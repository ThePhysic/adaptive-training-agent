import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  SSEParser,
  consumeSSE,
  MAX_EVENTS,
  MAX_FRAME_BYTES,
  planHash,
} from "../src/sse.js";
import type { StreamEvent } from "../src/sse.js";
import {
  candidate,
  event,
  frame,
  plan,
  response,
  success,
} from "./fixtures.js";

test("Python canonical candidate hash matches browser hash", async () => {
  assert.equal(await planHash(plan), candidate.content_hash);
});

for (const newline of ["\n", "\r\n", "\r"])
  for (const multiline of [true, false]) {
    test(`every byte split supports ${JSON.stringify(newline)} and multiline=${multiline}`, () => {
      const text = frame(
        event("done", {
          outcome: "clarify",
          fields: ["equipment"],
          choices: ["Choose bodyweight · café 🏋"],
        }),
        newline,
        multiline,
      );
      const bytes = new TextEncoder().encode(text);
      for (let split = 0; split <= bytes.length; split++) {
        const parser = new SSEParser();
        parser.feed(bytes.slice(0, split));
        parser.feed(bytes.slice(split));
        assert.equal(parser.finish().done.outcome, "clarify");
      }
    });
  }

test("one-byte chunks and metadata-only comments", async () => {
  const parser = new SSEParser();
  for (const byte of new TextEncoder().encode(": heartbeat\n\n" + success()))
    parser.feed(new Uint8Array([byte]));
  assert.equal(parser.finish().done.outcome, "plan");
  assert.equal(
    (
      await consumeSSE(
        response(success()),
        new AbortController().signal,
        () => {},
        1,
      )
    ).draft?.days.length,
    2,
  );
});

for (const outcome of ["clarify", "abstain", "error"] as const) {
  test(`terminal ${outcome} and no approval identity`, async () => {
    const error = { code: "provider_failure", retryable: false } as const;
    const payload =
      outcome === "clarify"
        ? {
            outcome,
            fields: ["equipment"],
            choices: ["Choose a supported option"],
          }
        : outcome === "abstain"
          ? {
              outcome,
              reason: "unsupported_scope",
              next_step: "change_supported_preferences",
            }
          : { outcome, error };
    const text =
      (outcome === "error" ? frame(event("error", error)) : "") +
      frame(
        event(
          "done",
          payload as Extract<StreamEvent, { event_type: "done" }>["payload"],
          outcome === "error" ? 1 : 0,
        ),
      );
    const result = await consumeSSE(
      response(text),
      new AbortController().signal,
      () => {},
      1,
    );
    assert.equal(result.done.outcome, outcome);
    assert.equal(result.draft, null);
    assert.equal("candidate" in result.done, false);
  });
}

const invalid: [string, string][] = [
  [
    "missing explicit version",
    frame(event("status", { stage: "context" })).replace(
      '"schema_version":"1",',
      "",
    ),
  ],
  [
    "missing retryability",
    frame(
      event("error", { code: "provider_failure", retryable: false }),
    ).replace(',"retryable":false', ""),
  ],
  ["EOF before draft", frame(event("status", { stage: "drafting" }))],
  ["EOF after draft", frame(event("draft", plan))],
  [
    "unframed terminal",
    frame(
      event("done", {
        outcome: "abstain",
        reason: "unsupported_scope",
        next_step: "change_supported_preferences",
      }),
    ).slice(0, -1),
  ],
  [
    "plan done without preview",
    frame(event("done", { outcome: "plan", candidate })),
  ],
  [
    "duplicate draft",
    frame(event("draft", plan)) + frame(event("draft", plan, 1)),
  ],
  ["wrong sequence", frame(event("status", { stage: "drafting" }, 1))],
  [
    "wrong request id",
    frame(event("draft", plan)) +
      frame({
        ...event("done", { outcome: "plan", candidate }, 1),
        request_id: "other",
      }),
  ],
  [
    "unknown version",
    frame({
      ...event("status", { stage: "context" }),
      schema_version: "2",
    } as unknown as StreamEvent),
  ],
  [
    "extra field",
    frame({
      ...event("status", { stage: "context" }),
      owner_id: "synthetic-b",
    } as unknown as StreamEvent),
  ],
  ["unknown event", "event: invented\ndata: {}\n\n"],
  [
    "wrong event name",
    frame(event("status", { stage: "context" })).replace(
      "event: status",
      "event: done",
    ),
  ],
  ["malformed JSON", "event: done\ndata: {nope}\n\n"],
  [
    "identity in draft",
    frame(event("draft", { ...plan, candidate } as PlanWithExtra)),
  ],
  [
    "error missing before error done",
    frame(
      event("done", {
        outcome: "error",
        error: { code: "provider_failure", retryable: false },
      }),
    ),
  ],
  [
    "error then plan",
    frame(event("error", { code: "provider_failure", retryable: false })) +
      frame(event("done", { outcome: "plan", candidate }, 1)),
  ],
  [
    "different error",
    frame(event("error", { code: "provider_failure", retryable: false })) +
      frame(
        event(
          "done",
          {
            outcome: "error",
            error: { code: "internal_error", retryable: false },
          },
          1,
        ),
      ),
  ],
  [
    "clarification after draft",
    frame(event("draft", plan)) +
      frame(
        event(
          "done",
          { outcome: "clarify", fields: ["equipment"], choices: ["x"] },
          1,
        ),
      ),
  ],
  [
    "status after draft",
    frame(event("draft", plan)) +
      frame(event("status", { stage: "drafting" }, 1)),
  ],
  [
    "extra event after done",
    success() + frame(event("status", { stage: "drafting" }, 3)),
  ],
  [
    "duplicate done",
    success() + frame(event("done", { outcome: "plan", candidate }, 3)),
  ],
  ["id replay field", "id: old\n" + success()],
  ["retry field", "retry: 1000\n" + success()],
  [
    "oversized frame",
    "event: done\ndata: " + "x".repeat(MAX_FRAME_BYTES) + "\n\n",
  ],
  ["oversized unterminated line", "x".repeat(MAX_FRAME_BYTES + 1)],
  [
    "unsafe integer",
    frame(
      event("draft", {
        ...plan,
        days: [
          { ...plan.days[0], planned_seconds: Number.MAX_SAFE_INTEGER + 1 },
          plan.days[1],
        ],
      }),
    ),
  ],
];
type PlanWithExtra = typeof plan & { candidate: typeof candidate };
test("runtime framing limits are generated from the backend contract", () => {
  const contract = JSON.parse(
    readFileSync("../contracts/openapi.json", "utf8"),
  );
  const limits = contract.paths["/api/v1/drafts/stream"].post["x-sse-limits"];
  assert.equal(MAX_FRAME_BYTES, limits.maxFrameBytes);
  assert.equal(MAX_EVENTS, limits.maxEvents);
});
for (const [name, text] of invalid)
  test(`reject ${name}`, async () => {
    await assert.rejects(
      consumeSSE(response(text), new AbortController().signal, () => {}, 1),
    );
  });

test("wrong candidate hash or revision cannot become complete", async () => {
  for (const terminal of [
    { ...candidate, content_hash: "0".repeat(64) },
    { ...candidate, revision: 2 },
  ]) {
    const text =
      frame(event("draft", plan)) +
      frame(event("done", { outcome: "plan", candidate: terminal }, 1));
    await assert.rejects(
      consumeSSE(response(text), new AbortController().signal, () => {}, 1),
    );
  }
});

test("invalid and truncated UTF-8 fail closed", () => {
  for (const bytes of [new Uint8Array([255]), new Uint8Array([0xe2, 0x82])]) {
    const parser = new SSEParser();
    assert.throws(() => {
      parser.feed(bytes);
      parser.finish();
    });
  }
});

test("event and aggregate byte counts are bounded", () => {
  const parser = new SSEParser();
  assert.throws(() => {
    for (let i = 0; i <= MAX_EVENTS; i++)
      parser.feed(
        new TextEncoder().encode(
          frame(event("status", { stage: "drafting" }, i)),
        ),
      );
  });
  assert.throws(() =>
    new SSEParser().feed(new Uint8Array(MAX_FRAME_BYTES * MAX_EVENTS + 1)),
  );
});

test("Stop cancels and releases a hanging reader, including repeated Stop", async () => {
  let cancelled = false;
  const controller = new AbortController();
  const source = new ReadableStream<Uint8Array>({
    cancel() {
      cancelled = true;
    },
  });
  const task = consumeSSE(
    new Response(source, { headers: { "Content-Type": "text/event-stream" } }),
    controller.signal,
    () => {},
    1,
  );
  controller.abort();
  controller.abort();
  await assert.rejects(task);
  assert.equal(cancelled, true);
  assert.equal(source.locked, false);
});

test("malformed content cancels the reader, and wrong MIME/status is rejected", async () => {
  let cancelled = false;
  const source = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode("bad\n\n"));
    },
    cancel() {
      cancelled = true;
    },
  });
  await assert.rejects(
    consumeSSE(
      new Response(source, {
        headers: { "Content-Type": "text/event-stream" },
      }),
      new AbortController().signal,
      () => {},
      1,
    ),
  );
  assert.equal(cancelled, true);
  for (const response of [
    new Response("{}"),
    new Response("", { status: 503 }),
  ])
    await assert.rejects(
      consumeSSE(response, new AbortController().signal, () => {}, 1),
    );
});
