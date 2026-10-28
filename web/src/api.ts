import type { components } from "./api.generated.js";
import { consumeSSE, StreamError, planHash } from "./sse.js";
import {
  validateProfile,
  validateExercise,
  validateError,
  validateApproval,
  validateSavedPlan,
  validateSessionRecord,
  validateSubmission,
  validateSubmissionError,
} from "./validators.generated.js";
import type {
  ApiError,
  Candidate,
  CompletedStream,
  StreamEvent,
} from "./sse.js";

export type Preferences = components["schemas"]["ProfilePreferences"];
export type SavedProfile = components["schemas"]["SavedProfile"];
export type Exercise = components["schemas"]["CatalogRecord"];
export type Generate = components["schemas"]["GenerateRequest"];
export type Principal = "synthetic-a" | "synthetic-b";
export type Approval = components["schemas"]["ApprovalResult"];
export type ApprovalRequest = components["schemas"]["ApprovalRequest"];
export type SavedPlan = components["schemas"]["SavedPlan"];
export type SessionRecord = components["schemas"]["SessionRecord"];
export type SessionSubmission = components["schemas"]["SessionSubmission"];
export type SubmissionError = components["schemas"]["SubmissionError"];
export class SubmissionFailure extends Error {
  constructor(public readonly error: SubmissionError) {
    super(error.code);
  }
}
export class HttpFailure extends Error {
  constructor(public readonly error: ApiError) {
    super(error.code);
  }
}

export interface TrainingApi {
  completions(
    principal: Principal,
    plan: SavedPlan,
    signal: AbortSignal,
  ): Promise<SessionRecord[]>;
  submitSession(
    principal: Principal,
    plan: SavedPlan,
    day: number,
    body: SessionSubmission,
    signal: AbortSignal,
  ): Promise<SessionRecord>;
  profile(
    principal: Principal,
    signal: AbortSignal,
  ): Promise<SavedProfile | null>;
  catalog(principal: Principal, signal: AbortSignal): Promise<Exercise[]>;
  save(
    principal: Principal,
    preferences: Preferences,
    revision: number,
    signal: AbortSignal,
  ): Promise<SavedProfile>;
  generate(
    principal: Principal,
    request: Generate,
    signal: AbortSignal,
    onEvent: (event: StreamEvent) => void,
    revise?: Candidate,
  ): Promise<CompletedStream>;
  approve(
    principal: Principal,
    request: ApprovalRequest,
    signal: AbortSignal,
  ): Promise<Approval>;
  plan(
    principal: Principal,
    planId: string,
    signal: AbortSignal,
  ): Promise<SavedPlan>;
  history(
    principal: Principal,
    signal: AbortSignal,
    cursor?: string,
  ): Promise<SavedPlan[]>;
}

async function boundedJSON(
  response: Response,
  maxBytes = 16384,
): Promise<unknown> {
  if (
    !response.body ||
    response.headers.get("content-type")?.split(";", 1)[0] !==
      "application/json"
  )
    throw new StreamError();
  const reader = response.body.getReader();
  let length = 0;
  const chunks: Uint8Array[] = [];
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > maxBytes) throw new StreamError();
      chunks.push(value);
    }
    const bytes = new Uint8Array(length);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export class BrowserApi implements TrainingApi {
  constructor(
    private fetcher: typeof fetch = globalThis.fetch.bind(globalThis),
  ) {}

  private async call(
    principal: Principal,
    path: string,
    signal: AbortSignal,
    body?: unknown,
  ): Promise<Response> {
    const response = await this.fetcher(path, {
      method: body === undefined ? "GET" : "POST",
      signal,
      credentials: "omit",
      cache: "no-store",
      redirect: "error",
      headers: {
        "X-Synthetic-Principal": principal,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    return response;
  }

  private async checkedJSON(
    response: Response,
    maxBytes = 16384,
  ): Promise<unknown> {
    const data = await boundedJSON(response, maxBytes);
    if (!response.ok) {
      if (validateError(data)) throw new HttpFailure(data);
      throw new StreamError();
    }
    return data;
  }

  private async sessionJSON(response: Response) {
    const data = await boundedJSON(response, 8192);
    if (!response.ok) {
      if (validateSubmissionError(data)) throw new SubmissionFailure(data);
      throw new StreamError();
    }
    return data;
  }

  private sessionMatches(
    data: unknown,
    plan: SavedPlan,
  ): data is SessionRecord {
    return (
      validateSessionRecord(data) &&
      data.plan_id === plan.approval.plan_id &&
      data.plan_revision === plan.approval.candidate.revision &&
      data.plan_content_hash === plan.approval.candidate.content_hash &&
      plan.plan.days.some((day) => day.day_index === data.day_index)
    );
  }

  async completions(
    principal: Principal,
    plan: SavedPlan,
    signal: AbortSignal,
  ) {
    const data = await this.sessionJSON(
      await this.call(
        principal,
        `/api/v1/plans/${encodeURIComponent(plan.approval.plan_id)}/completions`,
        signal,
      ),
    );
    if (
      !Array.isArray(data) ||
      data.length > 4 ||
      !data.every((item) => this.sessionMatches(item, plan))
    )
      throw new StreamError();
    const rows = data as SessionRecord[];
    if (
      rows.some(
        (row, index) => index > 0 && row.day_index <= rows[index - 1].day_index,
      ) ||
      new Set(rows.map((row) => row.record_id)).size !== rows.length
    )
      throw new StreamError();
    return rows;
  }

  async submitSession(
    principal: Principal,
    plan: SavedPlan,
    day: number,
    body: SessionSubmission,
    signal: AbortSignal,
  ) {
    if (
      !validateSubmission(body) ||
      body.plan_revision !== plan.approval.candidate.revision ||
      body.plan_content_hash !== plan.approval.candidate.content_hash ||
      !plan.plan.days.some((item) => item.day_index === day)
    )
      throw new StreamError();
    const data = await this.sessionJSON(
      await this.call(
        principal,
        `/api/v1/plans/${encodeURIComponent(plan.approval.plan_id)}/sessions/${day}/completion`,
        signal,
        body,
      ),
    );
    if (
      !this.sessionMatches(data, plan) ||
      data.day_index !== day ||
      data.status !== body.status ||
      (data.effort ?? null) !== (body.effort ?? null) ||
      (data.rating ?? null) !== (body.rating ?? null)
    )
      throw new StreamError();
    return data;
  }

  async profile(principal: Principal, signal: AbortSignal) {
    const response = await this.call(principal, "/api/v1/profile", signal);
    if (response.status === 404) {
      const error = await boundedJSON(response);
      if (validateError(error) && error.code === "not_found") return null;
      throw new StreamError();
    }
    const data = await this.checkedJSON(response);
    if (!validateProfile(data)) throw new StreamError();
    return data;
  }

  async catalog(principal: Principal, signal: AbortSignal) {
    const records: Exercise[] = [];
    let cursor = "";
    for (let page = 0; page < 2; page++) {
      const data = await this.checkedJSON(
        await this.call(
          principal,
          "/api/v1/exercises?limit=20" +
            (cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""),
          signal,
        ),
      );
      if (
        !Array.isArray(data) ||
        data.length > 20 ||
        !data.every((item) => validateExercise(item))
      )
        throw new StreamError();
      records.push(...(data as Exercise[]));
      if (data.length < 20) break;
      cursor = records.at(-1)!.exercise_id;
    }
    if (
      new Set(records.map((r) => r.exercise_id)).size !== records.length ||
      new Set(records.map((r) => r.catalog_revision)).size > 1
    )
      throw new StreamError();
    return records;
  }

  async save(
    principal: Principal,
    preferences: Preferences,
    revision: number,
    signal: AbortSignal,
  ) {
    const response = await this.fetcher("/api/v1/profile", {
      method: "PUT",
      signal,
      credentials: "omit",
      cache: "no-store",
      redirect: "error",
      headers: {
        "X-Synthetic-Principal": principal,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ expected_revision: revision, preferences }),
    });
    const data = await this.checkedJSON(response);
    if (!validateProfile(data)) throw new StreamError();
    return data;
  }

  async generate(
    principal: Principal,
    request: Generate,
    signal: AbortSignal,
    onEvent: (event: StreamEvent) => void,
    revise?: Candidate,
  ) {
    const path = revise
      ? `/api/v1/drafts/${encodeURIComponent(revise.candidate_id)}/revise/stream`
      : "/api/v1/drafts/stream";
    const response = await this.call(
      principal,
      path,
      signal,
      revise ? { ...request, candidate: revise } : request,
    );
    if (!response.ok) {
      await this.checkedJSON(response);
      throw new StreamError();
    }
    return consumeSSE(response, signal, onEvent, revise ? 2 : 1);
  }

  async approve(
    principal: Principal,
    request: ApprovalRequest,
    signal: AbortSignal,
  ) {
    const response = await this.call(
      principal,
      `/api/v1/drafts/${encodeURIComponent(request.candidate_id)}/approve`,
      signal,
      request,
    );
    const data = await this.checkedJSON(response);
    if (
      !validateApproval(data) ||
      data.candidate.candidate_id !== request.candidate_id ||
      data.candidate.revision !== request.revision ||
      data.candidate.content_hash !== request.content_hash
    )
      throw new StreamError();
    return data;
  }

  async plan(principal: Principal, planId: string, signal: AbortSignal) {
    const data = await this.checkedJSON(
      await this.call(
        principal,
        `/api/v1/plans/${encodeURIComponent(planId)}`,
        signal,
      ),
      69632,
    );
    if (
      !validateSavedPlan(data) ||
      data.approval.plan_id !== planId ||
      (await planHash(data.plan)) !== data.approval.candidate.content_hash
    )
      throw new StreamError();
    return data;
  }

  async history(principal: Principal, signal: AbortSignal, cursor?: string) {
    const data = await this.checkedJSON(
      await this.call(
        principal,
        "/api/v1/plans?limit=5" +
          (cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""),
        signal,
      ),
      69632 * 5,
    );
    if (
      !Array.isArray(data) ||
      data.length > 5 ||
      !data.every((row) => validateSavedPlan(row))
    )
      throw new StreamError();
    const rows = data as SavedPlan[];
    const ids = rows.map((row) => row.approval.plan_id);
    if (
      new Set(ids).size !== ids.length ||
      ids.some(
        (id, index) =>
          (cursor && id <= cursor) || (index > 0 && id <= ids[index - 1]),
      )
    )
      throw new StreamError();
    for (const row of rows)
      if ((await planHash(row.plan)) !== row.approval.candidate.content_hash)
        throw new StreamError();
    return rows;
  }
}
