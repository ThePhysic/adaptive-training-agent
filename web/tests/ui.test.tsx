import { beforeEach, afterEach, test, mock } from "node:test";
import assert from "node:assert/strict";
import { JSDOM } from "jsdom";
import { act } from "react";
import type { Root } from "react-dom/client";
import { App } from "../src/App.js";
import { HttpFailure } from "../src/api.js";
import type {
  TrainingApi,
  Principal,
  Preferences,
  ApprovalRequest,
  SavedPlan,
} from "../src/api.js";
import type { Candidate, CompletedStream, StreamEvent } from "../src/sse.js";
import { StreamError } from "../src/sse.js";
import {
  candidate,
  catalog,
  deferred,
  event,
  plan,
  profile,
} from "./fixtures.js";

let dom: JSDOM;
let root: Root;
beforeEach(async () => {
  dom = new JSDOM('<!doctype html><div id="root"></div>', {
    url: "http://127.0.0.1:8000",
  });
  Object.assign(globalThis, {
    window: dom.window,
    document: dom.window.document,
    HTMLElement: dom.window.HTMLElement,
    IS_REACT_ACT_ENVIRONMENT: true,
  });
  const { createRoot } = await import("react-dom/client");
  root = createRoot(document.getElementById("root")!);
  // Controlled crypto scheduling for DOM-only state tests. Real Web Crypto is
  // checked separately by the parser hash fixture and installed-browser journey.
  mock.method(
    crypto.subtle,
    "digest",
    async () =>
      Uint8Array.from(Buffer.from(candidate.content_hash, "hex")).buffer,
  );
});
afterEach(async () => {
  await act(() => root.unmount());
  dom.window.close();
  mock.restoreAll();
});

class FakeApi implements TrainingApi {
  async completions() {
    return [];
  }
  async submitSession(): Promise<never> {
    throw new Error("No implicit session writes");
  }
  approved: ApprovalRequest[] = [];
  rows: SavedPlan[] = [];
  loseApprovalOnce = false;
  loseReadbackOnce = false;
  saved: typeof profile | null = structuredClone(profile);
  saves: {
    principal: Principal;
    preferences: Preferences;
    revision: number;
  }[] = [];
  reads: Principal[] = [];
  calls: {
    principal: Principal;
    request: { profile_revision: number };
    signal: AbortSignal;
    onEvent: (event: StreamEvent) => void;
    revise?: Candidate;
    result: ReturnType<typeof deferred<CompletedStream>>;
  }[] = [];
  async profile(principal: Principal) {
    this.reads.push(principal);
    return structuredClone(this.saved);
  }
  async catalog() {
    return structuredClone(catalog);
  }
  async approve(
    _principal: Principal,
    request: ApprovalRequest,
    _signal?: AbortSignal,
  ) {
    this.approved.push(structuredClone(request));
    if (!this.rows.length)
      this.rows.push({
        approval: {
          plan_id: "saved-fixture",
          candidate: {
            candidate_id: request.candidate_id,
            revision: request.revision,
            content_hash: request.content_hash,
          },
        },
        plan: structuredClone(plan),
        versions: {
          profile_revision: 1,
          catalog_revision: "catalog-v1",
          validator_revision: "validator-v1",
        },
      });
    if (this.loseApprovalOnce) {
      this.loseApprovalOnce = false;
      throw new TypeError("Synthetic lost response");
    }
    return structuredClone(this.rows[0].approval);
  }
  async plan(_principal: Principal, planId: string) {
    if (this.loseReadbackOnce) {
      this.loseReadbackOnce = false;
      throw new TypeError("Synthetic readback failure");
    }
    const row = this.rows.find((row) => row.approval.plan_id === planId);
    if (!row) throw new HttpFailure({ code: "not_found", retryable: false });
    return structuredClone(row);
  }
  async history(principal: Principal, _signal?: AbortSignal, cursor?: string) {
    return principal === "synthetic-a"
      ? structuredClone(
          this.rows
            .filter((row) => !cursor || row.approval.plan_id > cursor)
            .sort((a, b) =>
              a.approval.plan_id.localeCompare(b.approval.plan_id),
            )
            .slice(0, 5),
        )
      : [];
  }
  async save(principal: Principal, preferences: Preferences, revision: number) {
    this.saves.push({ principal, preferences, revision });
    this.saved = {
      revision: revision + 1,
      preferences: structuredClone(preferences),
    };
    return this.saved;
  }
  generate(
    principal: Principal,
    request: { profile_revision: number },
    signal: AbortSignal,
    onEvent: (event: StreamEvent) => void,
    revise?: Candidate,
  ) {
    const result = deferred<CompletedStream>();
    this.calls.push({ principal, request, signal, onEvent, revise, result });
    return result.promise;
  }
}
function button(text: string) {
  const found = [...document.querySelectorAll("button")].find(
    (el) => el.textContent === text,
  );
  assert(found, `Button missing: ${text}`);
  return found;
}
function field(text: string) {
  const label = [...document.querySelectorAll("label")].find(
    (el) => el.firstChild?.textContent === text,
  );
  assert(label, `Field missing: ${text}`);
  return label.querySelector("select,input,textarea") as
    HTMLSelectElement | HTMLInputElement | HTMLTextAreaElement;
}
async function mount(api: FakeApi) {
  await act(async () => {
    root.render(<App api={api} />);
  });
}
async function click(text: string) {
  await act(async () => {
    button(text).click();
  });
}
async function select(text: string, value: string) {
  await act(async () => {
    const input = field(text);
    input.value = value;
    input.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
  });
}
async function finish(api: FakeApi, revision = 1) {
  await act(async () =>
    api.calls.at(-1)!.result.resolve({
      draft: plan,
      done: { outcome: "plan", candidate: { ...candidate, revision } },
    }),
  );
}

test("no implicit Save; adult attestation and explicit Save enable generation", async () => {
  const api = new FakeApi();
  api.saved = null;
  await mount(api);
  assert.equal(api.saves.length, 0);
  assert.equal(button("Save profile").disabled, true);
  assert.equal(button("Generate preview").disabled, true);
  const checkbox = document.querySelector(
    'input[type="checkbox"]',
  ) as HTMLInputElement;
  // The first checkbox in catalog details is an exclusion; choose attestation explicitly.
  assert(checkbox);
  const attestation = document.querySelector(
    ".attestation input",
  ) as HTMLInputElement;
  await act(() => attestation.click());
  await click("Save profile");
  assert.equal(api.saves.length, 1);
  assert.equal(api.saves[0].revision, 0);
  assert.equal(button("Generate preview").disabled, false);
  assert.match(document.body.textContent!, /Saved revision 1/);
});

test("unsaved changes invalidate review and require optimistic Save", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await finish(api);
  assert(document.querySelector('[data-complete="true"]'));
  await select("Session preset", "30");
  assert.equal(button("Generate preview").disabled, true);
  assert.equal(document.querySelector(".plan"), null);
  await click("Save profile");
  assert.equal(api.saves[0].revision, 1);
  assert.equal(api.saves[0].preferences.session_minutes, 30);
  assert.match(document.body.textContent!, /Saved revision 2/);
});

test("draft is incomplete; only complete review permits revision and approval", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await act(() => api.calls[0].onEvent(event("draft", plan)));
  assert(document.querySelector('[data-complete="false"]'));
  assert.equal(button("Revise once").disabled, true);
  assert.equal(button("Approve & save").disabled, true);
  await finish(api);
  assert(document.querySelector('[data-complete="true"]'));
  assert.match(document.body.textContent!, /1200 s/);
  assert.match(document.body.textContent!, /20.0 min estimated/);
  assert.match(document.body.textContent!, /Session 2/);
  await click("Revise once");
  assert.deepEqual(api.calls[1].revise, candidate);
  assert.equal(api.calls[1].request.profile_revision, 1);
  await finish(api, 2);
  assert.equal(button("Revise once").disabled, true);
  assert.equal(button("Approve & save").disabled, false);
});

test("repeated Stop clears draft and late terminal results cannot restore eligibility", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await act(() => api.calls[0].onEvent(event("draft", plan)));
  await click("Stop");
  await click("Stop");
  assert(api.calls[0].signal.aborted);
  await act(() => api.calls[0].onEvent(event("draft", plan)));
  await finish(api);
  assert.equal(document.querySelector(".plan"), null);
  assert.equal(button("Revise once").disabled, true);
  assert.equal(api.calls.length, 1);
  assert.match(document.body.textContent!, /Stopped/);
});

test("principal switch aborts old work and ignores its late response", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await select("Synthetic profile", "synthetic-b");
  assert(api.calls[0].signal.aborted);
  assert.equal(api.reads.at(-1), "synthetic-b");
  await finish(api);
  assert.equal(document.querySelector(".plan"), null);
  assert.equal(field("Synthetic profile").value, "synthetic-b");
  assert.equal(api.saves.length, 0);
});

test("clarification, abstention and typed errors are rendered as text without a plan", async () => {
  const api = new FakeApi();
  await mount(api);
  for (const done of [
    {
      outcome: "clarify",
      fields: ["equipment"],
      choices: ['Choose <img src=x onerror="throw 1"> bodyweight'],
    },
    {
      outcome: "abstain",
      reason: "medical_context",
      next_step: "seek_qualified_professional",
    },
    { outcome: "error", error: { code: "provider_failure", retryable: false } },
  ] as const) {
    await click("Generate preview");
    await act(async () =>
      api.calls.at(-1)!.result.resolve({
        draft: null,
        done: structuredClone(done) as CompletedStream["done"],
      }),
    );
    assert.equal(document.querySelector(".plan"), null);
    assert.equal(document.querySelector("img"), null);
    assert.equal(button("Revise once").disabled, true);
    assert.equal(button("Approve & save").disabled, true);
  }
});

test("EOF after draft removes preview and never automatically retries", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await act(() => api.calls[0].onEvent(event("draft", plan)));
  await act(async () => api.calls[0].result.reject(new StreamError()));
  assert.equal(document.querySelector(".plan"), null);
  assert.equal(api.calls.length, 1);
  assert.match(document.body.textContent!, /Stream incomplete or invalid/);
});

test("failed revision preserves a retry target without showing an incomplete plan", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await finish(api);
  await click("Revise once");
  await click("Stop");
  assert.equal(document.querySelector(".plan"), null);
  assert.equal(button("Revise once").disabled, false);
  await click("Revise once");
  assert.deepEqual(api.calls[2].revise, candidate);
  await finish(api, 2);
});

test("stale Save does not overwrite automatically; explicit reload reconciles", async () => {
  const api = new FakeApi();
  await mount(api);
  await select("Session preset", "30");
  api.save = async () => {
    throw new HttpFailure({ code: "stale_profile", retryable: false });
  };
  await click("Save profile");
  assert.match(document.body.textContent!, /Reload it/);
  assert.equal(api.reads.length, 1);
  api.saved = { ...profile, revision: 2 };
  await click("Reload saved profile");
  assert.equal(api.reads.length, 2);
  assert.equal(field("Session preset").value, "20");
});

test("explicit approval fetches durable readback and never saves on generation alone", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await finish(api);
  assert.equal(api.approved.length, 0);
  assert.equal(button("Approve & save").disabled, false);
  await click("Approve & save");
  assert.equal(api.approved.length, 1);
  assert.deepEqual(
    { ...api.approved[0], idempotency_key: undefined },
    { ...candidate, idempotency_key: undefined },
  );
  assert.match(api.approved[0].idempotency_key, /^[A-Za-z0-9_-]{1,128}$/);
  assert.match(document.body.textContent!, /Approved & saved/);
  assert.equal(button("Approve & save").disabled, true);
  assert.equal(button("Revise once").disabled, true);
  assert.equal(button("Open saved plan").disabled, false);
});

for (const phase of ["approval", "readback"])
  test(`lost ${phase} retains the exact approval key until explicit retry`, async () => {
    const api = new FakeApi();
    await mount(api);
    await click("Generate preview");
    await finish(api);
    if (phase === "approval") api.loseApprovalOnce = true;
    else api.loseReadbackOnce = true;
    await click("Approve & save");
    assert.equal(api.approved.length, 1);
    assert.equal(document.querySelector(".saved"), null);
    assert.equal(button("Generate preview").disabled, true);
    assert.match(
      document.body.textContent!,
      phase === "readback" ? /Approval committed/ : /outcome is not confirmed/,
    );
    await click("Retry approval");
    assert.equal(api.approved.length, 2);
    assert.deepEqual(api.approved[0], api.approved[1]);
    assert.equal(api.rows.length, 1);
    assert(document.querySelector(".saved"));
  });

for (const code of ["stale_profile", "idempotency_mismatch"] as const)
  test(`${code} clears eligibility instead of choosing a new key`, async () => {
    const api = new FakeApi();
    await mount(api);
    await click("Generate preview");
    await finish(api);
    api.approve = async (_owner, request) => {
      api.approved.push(request);
      throw new HttpFailure({ code, retryable: false });
    };
    await click("Approve & save");
    assert.equal(api.approved.length, 1);
    assert.equal(button("Approve & save").disabled, true);
    assert.equal(document.querySelector(".plan"), null);
    assert.equal(api.rows.length, 0);
  });

test("reconciliation pending permits only a same-key approval retry", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await finish(api);
  const original = api.approve.bind(api);
  let pending = true;
  api.approve = async (owner, request, signal) => {
    if (pending) {
      api.approved.push(request);
      throw new HttpFailure({
        code: "reconciliation_pending",
        retryable: true,
      });
    }
    return original(owner, request, signal);
  };
  await click("Approve & save");
  assert.match(document.body.textContent!, /still being reconciled/);
  pending = false;
  await click("Retry approval");
  assert.deepEqual(api.approved[0], api.approved[1]);
  assert(document.querySelector(".saved"));
});

test("mismatched reviewed hash cannot send an approval", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await act(async () =>
    api.calls[0].result.resolve({
      draft: plan,
      done: {
        outcome: "plan",
        candidate: { ...candidate, content_hash: "0".repeat(64) },
      },
    }),
  );
  await click("Approve & save");
  assert.equal(api.approved.length, 0);
  assert.equal(button("Approve & save").disabled, true);
  assert.match(document.body.textContent!, /no longer matches/);
});

test("owner switch ignores a late approval response", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await finish(api);
  const pending = deferred<Awaited<ReturnType<TrainingApi["approve"]>>>();
  let signal: AbortSignal | undefined;
  api.approve = async (_owner, request, sig) => {
    api.approved.push(request);
    signal = sig;
    return pending.promise;
  };
  await click("Approve & save");
  await select("Synthetic profile", "synthetic-b");
  assert(signal?.aborted);
  await act(async () =>
    pending.resolve({ plan_id: "saved-fixture", candidate }),
  );
  assert.equal(document.querySelector(".saved"), null);
  assert.equal(document.querySelector(".plan"), null);
  assert.equal(button("Approve & save").disabled, true);
});

test("saved history opens the original snapshot after a profile change", async () => {
  const api = new FakeApi();
  await mount(api);
  await click("Generate preview");
  await finish(api);
  await click("Approve & save");
  await select("Session preset", "30");
  await click("Save profile");
  await click("Open saved plan");
  assert.equal(field("Session preset").value, "30");
  assert.match(
    document.querySelector(".plan")!.textContent!,
    /Requested preset: 20 minutes/,
  );
  assert.match(
    document.querySelector(".saved")!.textContent!,
    /profile revision 1/,
  );
  assert.equal(button("Approve & save").disabled, true);
});

test("history pagination reads successive bounded pages without enabling approval", async () => {
  const api = new FakeApi();
  api.rows = Array.from({ length: 6 }, (_, i) => ({
    approval: {
      plan_id: `plan-${i}`,
      candidate: { ...candidate, candidate_id: `history-candidate-${i}` },
    },
    plan: structuredClone(plan),
    versions: {
      profile_revision: 1,
      catalog_revision: "catalog-v1",
      validator_revision: "validator-v1",
    },
  }));
  await mount(api);
  assert.equal(document.querySelectorAll(".history li").length, 5);
  await click("Load more saved plans");
  assert.equal(document.querySelectorAll(".history li").length, 6);
  assert.equal(button("Approve & save").disabled, true);
});
