import {
  validateEvent,
  MAX_FRAME_BYTES,
  MAX_EVENTS,
} from "./validators.generated.js";
export { MAX_FRAME_BYTES, MAX_EVENTS } from "./validators.generated.js";
import type { components } from "./api.generated.js";

export type StreamEvent = components["schemas"]["StreamEvent"];
export type Plan = components["schemas"]["PlanProposal"];
export type Candidate = components["schemas"]["CandidateIdentity"];
export type Terminal = components["schemas"]["DoneEvent"]["payload"];
export type ApiError = components["schemas"]["ApiError"];
const MAX_STREAM_BYTES = MAX_FRAME_BYTES * MAX_EVENTS;
const encoder = new TextEncoder();

export class StreamError extends Error {
  constructor() {
    super("Stream incomplete or invalid. Generate again.");
  }
}

function safeNumbers(value: unknown): boolean {
  if (typeof value === "number") return Number.isSafeInteger(value);
  if (value !== null && typeof value === "object")
    return Object.values(value).every(safeNumbers);
  return true;
}

export interface CompletedStream {
  draft: Plan | null;
  done: Terminal;
}

export class SSEParser {
  private decoder = new TextDecoder("utf-8", { fatal: true });
  private buffer = "";
  private frameBytes = 0;
  private totalBytes = 0;
  private name: string | null = null;
  private data: string[] = [];
  private count = 0;
  private requestId: string | null = null;
  private draft: Plan | null = null;
  private error: ApiError | null = null;
  private done: Terminal | null = null;

  constructor(private onEvent: (event: StreamEvent) => void = () => {}) {}

  feed(chunk: Uint8Array): void {
    try {
      this.totalBytes += chunk.byteLength;
      if (this.totalBytes > MAX_STREAM_BYTES) throw new StreamError();
      this.buffer += this.decoder.decode(chunk, { stream: true });
      this.drain(false);
    } catch {
      throw new StreamError();
    }
  }

  private drain(final: boolean): void {
    while (true) {
      const match = /\r\n|\r|\n/.exec(this.buffer);
      if (!match) break;
      if (!final && match[0] === "\r" && match.index === this.buffer.length - 1)
        break;
      const line = this.buffer.slice(0, match.index);
      this.buffer = this.buffer.slice(match.index + match[0].length);
      this.frameBytes += encoder.encode(line + match[0]).byteLength;
      if (this.frameBytes > MAX_FRAME_BYTES) throw new StreamError();
      if (!line) {
        if (this.name !== null || this.data.length) this.dispatch();
        this.frameBytes = 0;
        this.name = null;
        this.data = [];
      } else if (!line.startsWith(":")) {
        const index = line.indexOf(":");
        if (index < 0) throw new StreamError();
        const field = line.slice(0, index);
        let value = line.slice(index + 1);
        if (value.startsWith(" ")) value = value.slice(1);
        if (field === "event" && this.name === null) this.name = value;
        else if (field === "data") this.data.push(value);
        else throw new StreamError(); // No id/retry/replay or ambiguous duplicate event field.
      }
    }
    if (
      this.frameBytes + encoder.encode(this.buffer).byteLength >
      MAX_FRAME_BYTES
    )
      throw new StreamError();
  }

  private dispatch(): void {
    if (
      !this.name ||
      !this.data.length ||
      this.done ||
      this.count >= MAX_EVENTS
    )
      throw new StreamError();
    const value: unknown = JSON.parse(this.data.join("\n"));
    if (!safeNumbers(value) || !validateEvent(value)) throw new StreamError();
    const event = value;
    if (
      event.schema_version !== "1" ||
      event.event_type !== this.name ||
      event.sequence !== this.count ||
      (this.requestId !== null && event.request_id !== this.requestId)
    )
      throw new StreamError();
    this.requestId = event.request_id;
    this.count++;
    if (event.event_type === "status") {
      if (this.draft || this.error) throw new StreamError();
    } else if (event.event_type === "draft") {
      if (this.draft || this.error) throw new StreamError();
      this.draft = event.payload;
    } else if (event.event_type === "error") {
      if (this.error || typeof event.payload.retryable !== "boolean")
        throw new StreamError();
      this.error = event.payload;
    } else {
      const outcome = event.payload;
      if (outcome.outcome === "plan") {
        if (!this.draft || this.error) throw new StreamError();
      } else if (outcome.outcome === "error") {
        if (
          !this.error ||
          this.error.code !== outcome.error.code ||
          this.error.retryable !== outcome.error.retryable
        )
          throw new StreamError();
      } else if (this.draft || this.error) throw new StreamError();
      this.done = outcome;
    }
    this.onEvent(event);
  }

  finish(): CompletedStream {
    try {
      this.buffer += this.decoder.decode();
      this.drain(true);
      if (this.buffer || this.name || this.data.length || !this.done)
        throw new StreamError();
      return { draft: this.draft, done: this.done };
    } catch {
      throw new StreamError();
    }
  }
}

export function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value !== null && typeof value === "object") {
    return `{${Object.entries(value)
      .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
      .map(([key, item]) => `${JSON.stringify(key)}:${canonical(item)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

export async function planHash(plan: Plan): Promise<string> {
  const hash = await crypto.subtle.digest(
    "SHA-256",
    encoder.encode(canonical(plan)),
  );
  return Array.from(new Uint8Array(hash), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

export async function consumeSSE(
  response: Response,
  signal: AbortSignal,
  onEvent: (event: StreamEvent) => void,
  expectedRevision: 1 | 2,
): Promise<CompletedStream> {
  if (
    response.status !== 200 ||
    response.headers.get("content-type")?.split(";", 1)[0] !==
      "text/event-stream" ||
    !response.body
  )
    throw new StreamError();
  const reader = response.body.getReader();
  const abort = () => {
    void reader.cancel().catch(() => {});
  };
  signal.addEventListener("abort", abort, { once: true });
  const parser = new SSEParser(onEvent);
  try {
    while (true) {
      signal.throwIfAborted();
      const { value, done } = await reader.read();
      signal.throwIfAborted();
      if (done) break;
      parser.feed(value);
    }
    const result = parser.finish();
    if (result.done.outcome === "plan") {
      if (
        result.done.candidate.revision !== expectedRevision ||
        (await planHash(result.draft!)) !== result.done.candidate.content_hash
      )
        throw new StreamError();
    }
    signal.throwIfAborted();
    return result;
  } finally {
    signal.removeEventListener("abort", abort);
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
