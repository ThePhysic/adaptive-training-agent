import { afterEach, beforeEach, test } from "node:test";
import assert from "node:assert/strict";
import { JSDOM } from "jsdom";
import { act } from "react";
import type { Root } from "react-dom/client";
import { CompletionPanel } from "../src/CompletionPanel.js";
import { BrowserApi, SubmissionFailure } from "../src/api.js";
import type {
  TrainingApi,
  SavedPlan,
  SessionSubmission,
  SessionRecord,
} from "../src/api.js";
import { candidate, plan, deferred } from "./fixtures.js";

const saved: SavedPlan = {
  approval: { plan_id: "saved-plan", candidate },
  plan,
  versions: {
    profile_revision: 1,
    catalog_revision: "catalog-v1",
    validator_revision: "validator-v1",
  },
};
const body: SessionSubmission = {
  expected_revision: 0,
  plan_revision: candidate.revision,
  plan_content_hash: candidate.content_hash,
  status: "completed",
  effort: null,
  rating: null,
  idempotency_key: "record-key",
};
function record(overrides: Partial<SessionRecord> = {}): SessionRecord {
  return {
    record_id: "record-one",
    plan_id: "saved-plan",
    day_index: 1,
    revision: 1,
    plan_revision: candidate.revision,
    plan_content_hash: candidate.content_hash,
    status: "completed",
    effort: null,
    rating: null,
    ...overrides,
  };
}
function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
const signal = new AbortController().signal;

test("session client sends explicit owned POST and bounded GET without automatic retry", async () => {
  const requests: { path: string; options?: RequestInit }[] = [];
  const api = new BrowserApi(async (path, options) => {
    requests.push({ path: String(path), options });
    return json(options?.method === "POST" ? record() : [record()]);
  });
  await api.completions("synthetic-b", saved, signal);
  await api.submitSession("synthetic-b", saved, 1, body, signal);
  assert.equal(requests[0].options?.method, "GET");
  assert.equal(requests[1].options?.method, "POST");
  assert.equal(
    requests[1].path,
    "/api/v1/plans/saved-plan/sessions/1/completion",
  );
  assert.deepEqual(JSON.parse(String(requests[1].options?.body)), body);
  assert(
    requests.every(
      (r) =>
        (r.options?.headers as Record<string, string>)[
          "X-Synthetic-Principal"
        ] === "synthetic-b",
    ),
  );
  assert(
    requests.every(
      (r) =>
        r.options?.cache === "no-store" && r.options.credentials === "omit",
    ),
  );
  let calls = 0;
  const lost = new BrowserApi(async () => {
    calls++;
    throw new TypeError("synthetic lost response");
  });
  await assert.rejects(
    lost.submitSession("synthetic-a", saved, 1, body, signal),
  );
  assert.equal(calls, 1);
});

for (const bad of [
  [record(), record()],
  [record({ day_index: 2 }), record()],
  [record({ day_index: 4 })],
  [record({ plan_id: "other" })],
  [record({ plan_content_hash: "b".repeat(64) })],
  [record({ status: "skipped", rating: 4 })],
  [record({ rating: true as unknown as number })],
  [record(), record(), record(), record(), record()],
])
  test(
    "session client rejects malformed or mismatched readback " +
      JSON.stringify(bad).slice(0, 70),
    async () => {
      const api = new BrowserApi(async () => json(bad));
      await assert.rejects(api.completions("synthetic-a", saved, signal));
    },
  );

test("session client rejects mismatched POST receipt and classifies conflicts", async () => {
  await assert.rejects(
    new BrowserApi(async () => json(record({ rating: 5 }))).submitSession(
      "synthetic-a",
      saved,
      1,
      body,
      signal,
    ),
  );
  const api = new BrowserApi(async () =>
    json({ code: "session_already_recorded", retryable: false }, 409),
  );
  await assert.rejects(
    api.submitSession("synthetic-a", saved, 1, body, signal),
    SubmissionFailure,
  );
});

let dom: JSDOM, root: Root;
beforeEach(async () => {
  dom = new JSDOM('<!doctype html><div id="root"></div>', {
    url: "http://127.0.0.1",
  });
  Object.assign(globalThis, {
    window: dom.window,
    document: dom.window.document,
    HTMLElement: dom.window.HTMLElement,
    IS_REACT_ACT_ENVIRONMENT: true,
  });
  const { createRoot } = await import("react-dom/client");
  root = createRoot(document.getElementById("root")!);
});
afterEach(async () => {
  await act(async () => {
    root.unmount();
  });
  dom.window.close();
});

function fake() {
  const rows: SessionRecord[] = [];
  const calls: SessionSubmission[] = [];
  let lost = true;
  const api = {
    async completions() {
      return structuredClone(rows);
    },
    async submitSession(
      _principal: unknown,
      _plan: unknown,
      day: number,
      value: SessionSubmission,
    ) {
      calls.push(structuredClone(value));
      if (!rows.length)
        rows.push(
          record({
            day_index: day,
            status: value.status,
            effort: value.effort,
            rating: value.rating,
          }),
        );
      if (lost) {
        lost = false;
        throw new TypeError("lost");
      }
      return structuredClone(rows[0]);
    },
  } as unknown as TrainingApi;
  return { api, rows, calls };
}
async function mount(
  api: TrainingApi,
  principal: "synthetic-a" | "synthetic-b" = "synthetic-a",
) {
  await act(async () => {
    root.render(
      <CompletionPanel
        key={principal}
        api={api}
        principal={principal}
        plan={saved}
      />,
    );
  });
}
async function select(label: string, value: string) {
  await act(async () => {
    const element = document.querySelector(
      `[aria-label="${label}"]`,
    ) as HTMLSelectElement;
    element.value = value;
    element.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
  });
}
async function click(label: string) {
  const button = [...document.querySelectorAll("button")].find(
    (b) => b.textContent === label,
  )!;
  await act(async () => {
    button.click();
  });
}

test("approval and selecting feedback never submit; explicit uncertain retry uses unchanged key/body", async () => {
  const f = fake();
  await mount(f.api);
  assert.equal(f.calls.length, 0);
  assert.equal(
    (
      document.querySelector(
        '[aria-label="Session 1 status"]',
      ) as HTMLSelectElement
    ).value,
    "",
  );
  await select("Session 1 status", "completed");
  await select("Session 1 effort", "moderate");
  await select("Session 1 rating", "5");
  assert.equal(f.calls.length, 0);
  await click("Submit session 1 record");
  assert.equal(f.calls.length, 1);
  assert.equal(document.querySelectorAll("[data-session-record]").length, 0);
  assert([...document.querySelectorAll("select")].every((e) => e.disabled));
  await click("Retry the same submission");
  assert.deepEqual(f.calls[0], f.calls[1]);
  assert.equal(f.calls[0].rating, 5);
  assert.equal(f.calls[0].effort, "moderate");
  assert(
    document
      .querySelector('[data-session-record="1"]')
      ?.textContent?.includes("Submitted: completed"),
  );
  assert(document.body.textContent?.includes("approved plan is unchanged"));
});

test("skipped clears optional feedback and only submits nulls", async () => {
  const f = fake();
  await mount(f.api);
  await select("Session 1 status", "partial");
  await select("Session 1 effort", "hard");
  await select("Session 1 rating", "2");
  await select("Session 1 status", "skipped");
  assert(
    (
      document.querySelector(
        '[aria-label="Session 1 effort"]',
      ) as HTMLSelectElement
    ).disabled,
  );
  await click("Submit session 1 record");
  assert.equal(f.calls[0].status, "skipped");
  assert.equal(f.calls[0].rating, null);
  assert.equal(f.calls[0].effort, null);
});

test("failed initial read prevents submit until explicit reload", async () => {
  const f = fake();
  let fail = true;
  f.api.completions = async () => {
    if (fail) throw new TypeError("unavailable");
    return [];
  };
  await mount(f.api);
  assert([...document.querySelectorAll("select")].every((e) => e.disabled));
  assert.equal(f.calls.length, 0);
  fail = false;
  await click("Reload session records");
  assert(
    !(
      document.querySelector(
        '[aria-label="Session 1 status"]',
      ) as HTMLSelectElement
    ).disabled,
  );
});

test("definite conflict requires owned reload; does not choose a fresh key automatically", async () => {
  const f = fake();
  f.api.submitSession = async () => {
    throw new SubmissionFailure({
      code: "session_already_recorded",
      retryable: false,
    });
  };
  await mount(f.api);
  await select("Session 1 status", "completed");
  await click("Submit session 1 record");
  assert([...document.querySelectorAll("select")].every((e) => e.disabled));
  f.rows.push(record());
  await click("Reload session records");
  assert(document.querySelector('[data-session-record="1"]'));
});

test("readback loss preserves the exact submission for an explicit retry", async () => {
  const f = fake();
  let reads = 0;
  f.api.completions = async () => {
    if (++reads === 2) throw new TypeError("lost readback");
    return structuredClone(f.rows);
  };
  // First POST succeeds, so the failure occurs only on its following GET.
  f.api.submitSession = async (_p, _s, day, value) => {
    f.calls.push(structuredClone(value));
    if (!f.rows.length) f.rows.push(record({ day_index: day }));
    return f.rows[0];
  };
  await mount(f.api);
  await select("Session 1 status", "completed");
  await click("Submit session 1 record");
  assert(document.body.textContent?.includes("not confirmed"));
  await click("Retry the same submission");
  assert.deepEqual(f.calls[0], f.calls[1]);
  assert(document.querySelector('[data-session-record="1"]'));
});

test("owner switch aborts pending submit and discards late result", async () => {
  const f = fake(),
    late = deferred<SessionRecord>();
  let oldSignal: AbortSignal | undefined;
  f.api.submitSession = async (_p, _s, _d, _b, s) => {
    oldSignal = s;
    return late.promise;
  };
  await mount(f.api);
  await select("Session 1 status", "completed");
  await click("Submit session 1 record");
  await mount(f.api, "synthetic-b");
  assert(oldSignal?.aborted);
  await act(async () => {
    late.resolve(record());
  });
  assert.equal(document.querySelectorAll("[data-session-record]").length, 0);
  assert(!document.body.textContent?.includes("record saved and read back"));
});
