import { readFileSync } from "node:fs";
import type { Plan, Candidate, StreamEvent } from "../src/sse.js";
import type { Exercise, SavedProfile } from "../src/api.js";

const fixture = JSON.parse(readFileSync("tests/server-plan.json", "utf8"));
export const plan: Plan = fixture.plan;
export const candidate: Candidate = fixture.candidate;
export const profile: SavedProfile = { revision: 1, preferences: plan.profile };
export const catalog: Exercise[] = JSON.parse(
  readFileSync("../data/catalog/v1.json", "utf8"),
).records;
export function event<T extends StreamEvent["event_type"]>(
  event_type: T,
  payload: Extract<StreamEvent, { event_type: T }>["payload"],
  sequence = 0,
): StreamEvent {
  return {
    schema_version: "1",
    request_id: "fixture-request",
    sequence,
    event_type,
    payload,
  } as StreamEvent;
}
export function frame(value: StreamEvent, newline = "\n", multiline = false) {
  const json = JSON.stringify(
    value,
    multiline ? null : undefined,
    multiline ? 2 : undefined,
  );
  return `event: ${value.event_type}${newline}${json
    .split("\n")
    .map((line) => "data: " + line)
    .join(newline)}${newline}${newline}`;
}
export function success(revision = 1) {
  return (
    frame(event("status", { stage: "context" }, 0)) +
    frame(event("draft", plan, 1)) +
    frame(
      event(
        "done",
        { outcome: "plan", candidate: { ...candidate, revision } },
        2,
      ),
    )
  );
}
export function response(text: string) {
  return new Response(text, {
    status: 200,
    headers: { "Content-Type": "text/event-stream; charset=utf-8" },
  });
}
export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
