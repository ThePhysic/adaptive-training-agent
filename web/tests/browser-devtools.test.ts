import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import type { ChildProcess } from "node:child_process";
import { test } from "node:test";
import { diagnostics, waitForPageTarget } from "../scripts/browser-support.mjs";

const id = "A".repeat(32);
const target = {
  id,
  type: "page",
  url: "about:blank",
  webSocketDebuggerUrl: `ws://127.0.0.1:4321/devtools/page/${id}`,
};
function setup() {
  const child = Object.assign(new EventEmitter(), {
    exitCode: null,
    signalCode: null,
  });
  const d = diagnostics("http://127.0.0.1:8000");
  let clock = 0;
  const options = {
    deadline: 6000,
    now: () => clock,
    pause: async (ms: number) => {
      clock += ms;
    },
  };
  return {
    child,
    d,
    options,
    advance: (ms: number) => {
      clock += ms;
    },
    run: (request: typeof fetch, extra = {}) =>
      waitForPageTarget(child as unknown as ChildProcess, 4321, d, {
        ...options,
        request,
        ...extra,
      }),
  };
}
const json = (value: unknown) => new Response(JSON.stringify(value));

test("read-only discovery retries a timeout, refusal and absent target then selects the same owned blank page", async () => {
  const s = setup();
  let calls = 0;
  const result = await s.run(async (input, init) => {
    assert.equal(input, "http://127.0.0.1:4321/json/list");
    assert.equal(init?.method, "GET");
    assert.equal(init?.redirect, "error");
    if (++calls === 1)
      throw new DOMException("private-timeout-canary", "TimeoutError");
    if (calls === 2)
      throw new TypeError("private-refusal-canary", {
        cause: { code: "ECONNREFUSED" },
      });
    if (calls === 3) return json([]);
    return json([target]);
  });
  assert.equal(result.attempts, 4);
  assert.equal(result.target.webSocketDebuggerUrl, target.webSocketDebuggerUrl);
  assert.equal(s.child.listenerCount("exit"), 0);
  const report = JSON.stringify(s.d.snapshot());
  for (const code of [
    "devtools_http_timeout",
    "devtools_http_refused",
    "devtools_target_unavailable",
    "devtools_target_ready",
  ])
    assert.match(report, new RegExp(code));
  assert.doesNotMatch(report, /private-|4321|AAAAAAAA|ws:|http:/);
});

for (const [name, response, code] of [
  [
    "unexpected status",
    () => new Response("private-status-canary", { status: 503 }),
    "devtools_http_status",
  ],
  [
    "redirect",
    () =>
      new Response("private-redirect-canary", {
        status: 302,
        headers: { Location: "https://private.invalid" },
      }),
    "devtools_http_status",
  ],
  [
    "invalid JSON",
    () => new Response("private-json-canary"),
    "devtools_invalid_json",
  ],
  [
    "invalid UTF8",
    () => new Response(new Uint8Array([0xff])),
    "devtools_invalid_json",
  ],
  [
    "oversized body",
    () => new Response("x".repeat(65537)),
    "devtools_response_oversized",
  ],
  ["object instead of list", () => json(target), "devtools_malformed_target"],
  ["missing fields", () => json([{}]), "devtools_malformed_target"],
  [
    "too many targets",
    () => json(Array(17).fill(target)),
    "devtools_malformed_target",
  ],
  ["ambiguous page", () => json([target, target]), "devtools_target_mismatch"],
  [
    "wrong page URL",
    () => json([{ ...target, url: "https://private.invalid" }]),
    "devtools_target_mismatch",
  ],
  [
    "malformed type",
    () => json([{ ...target, type: 7 }]),
    "devtools_malformed_target",
  ],
  [
    "nonlocal destination",
    () =>
      json([
        {
          ...target,
          webSocketDebuggerUrl: target.webSocketDebuggerUrl.replace(
            "127.0.0.1",
            "private.invalid",
          ),
        },
      ]),
    "devtools_target_mismatch",
  ],
  [
    "wrong port",
    () =>
      json([
        {
          ...target,
          webSocketDebuggerUrl: target.webSocketDebuggerUrl.replace(
            ":4321",
            ":4322",
          ),
        },
      ]),
    "devtools_target_mismatch",
  ],
  [
    "wrong target identity",
    () => json([{ ...target, id: "B".repeat(32) }]),
    "devtools_target_mismatch",
  ],
  [
    "URL credentials",
    () =>
      json([
        {
          ...target,
          webSocketDebuggerUrl: target.webSocketDebuggerUrl.replace(
            "ws://",
            "ws://secret@",
          ),
        },
      ]),
    "devtools_target_mismatch",
  ],
  [
    "query suffix",
    () =>
      json([
        {
          ...target,
          webSocketDebuggerUrl: target.webSocketDebuggerUrl + "?secret=canary",
        },
      ]),
    "devtools_target_mismatch",
  ],
] as const)
  test(`${name} fails immediately without raw response or target disclosure`, async () => {
    const s = setup();
    let calls = 0;
    await assert.rejects(
      s.run(async () => {
        calls++;
        return response();
      }),
      new RegExp(code),
    );
    assert.equal(calls, 1);
    assert.equal(s.child.listenerCount("exit"), 0);
    assert.doesNotMatch(
      JSON.stringify(s.d.snapshot()),
      /private-|canary|secret|4321|AAAAAAAA/,
    );
  });

test("built-in worker targets are never attached; only the unique blank page is accepted", async () => {
  const s = setup();
  const value = await s.run(async () =>
    json([
      { type: "service_worker", url: "private-worker-canary" },
      target,
      { type: "background_page", webSocketDebuggerUrl: "ws://private.invalid" },
    ]),
  );
  assert.equal(value.target.id, target.id);
  assert.equal(value.attempts, 1);
  assert.doesNotMatch(JSON.stringify(s.d.snapshot()), /private|AAAAAAAA/);
});

for (const reason of [
  "absent",
  "workers only",
  "refused",
  "timeout",
  "connection reset",
])
  test(`permanently ${reason} target is bounded by the deadline and attempt cap`, async () => {
    const s = setup();
    let calls = 0;
    await assert.rejects(
      s.run(async () => {
        calls++;
        if (reason === "absent") return json([]);
        if (reason === "workers only")
          return json([{ type: "service_worker" }]);
        if (reason === "refused")
          throw new TypeError("private", { cause: { code: "ECONNREFUSED" } });
        if (reason === "timeout") {
          s.advance(2000);
          throw new DOMException("private", "TimeoutError");
        }
        throw new TypeError("private", { cause: { code: "ECONNRESET" } });
      }),
      /devtools_(target_unavailable|http_refused|http_timeout|http_failed)/,
    );
    assert(calls > 1 && calls <= 24);
    assert.equal(s.child.listenerCount("exit"), 0);
    assert(s.d.snapshot().events.length <= 32);
  });

test("hung response body times out, cancels its reader, then recovers", async () => {
  const s = setup();
  let expire = () => {};
  let calls = 0;
  let cancelled = false;
  let released = false;
  const result = await s.run(
    async (_, init) => {
      if (++calls > 1) return json([target]);
      const response = new Response(
        new ReadableStream({
          start(controller) {
            init!.signal!.addEventListener(
              "abort",
              () => controller.error(new DOMException("private", "AbortError")),
              { once: true },
            );
            queueMicrotask(() => expire());
          },
        }),
      );
      const reader = response.body!.getReader();
      Object.defineProperty(response.body, "getReader", {
        value: () => ({
          read: () => reader.read(),
          cancel: () => {
            cancelled = true;
            return reader.cancel();
          },
          releaseLock: () => {
            released = true;
            reader.releaseLock();
          },
        }),
      });
      return response;
    },
    {
      timer: ((fn: () => void, ms: number) => {
        assert.equal(ms, 2000);
        expire = fn;
        return 1;
      }) as unknown as typeof setTimeout,
      clear: (() => {}) as unknown as typeof clearTimeout,
    },
  );
  assert(cancelled && released);
  assert.equal(result.attempts, 2);
  assert.match(JSON.stringify(s.d.snapshot()), /devtools_http_timeout/);
});

test("browser exit aborts an in-flight HTTP request immediately without retry", async () => {
  const s = setup();
  let calls = 0;
  await assert.rejects(
    s.run(async (_, init) => {
      calls++;
      return await new Promise<Response>((_, reject) => {
        init!.signal!.addEventListener(
          "abort",
          () => reject(Error("private-exit-canary")),
          { once: true },
        );
        s.child.emit("exit", 1);
      });
    }),
    /browser_exited_during_devtools/,
  );
  assert.equal(calls, 1);
  assert.equal(s.child.listenerCount("exit"), 0);
});

test("browser exit between discovery attempts prevents another request", async () => {
  const s = setup();
  let calls = 0;
  await assert.rejects(
    s.run(
      async () => {
        calls++;
        return json([]);
      },
      {
        pause: async () => {
          s.child.emit("exit", 1);
        },
      },
    ),
    /browser_exited_during_devtools/,
  );
  assert.equal(calls, 1);
});

test("already exited browser, expired deadline and invalid port never fetch", async () => {
  const s = setup();
  const request = async () => {
    assert.fail("Must not fetch");
  };
  Object.assign(s.child, { exitCode: 1 });
  await assert.rejects(s.run(request), /browser_exited_during_devtools/);
  Object.assign(s.child, { exitCode: null });
  await assert.rejects(
    s.run(request, { deadline: 0 }),
    /devtools_target_unavailable/,
  );
  await assert.rejects(
    waitForPageTarget(s.child as unknown as ChildProcess, 0, s.d, { request }),
    /devtools_target_mismatch/,
  );
});

test("an almost exhausted overall deadline caps the per-attempt timer", async () => {
  const s = setup();
  let limit = 0;
  await s.run(async () => json([target]), {
    deadline: 75,
    timer: ((_: () => void, ms: number) => {
      limit = ms;
      return 1;
    }) as unknown as typeof setTimeout,
    clear: (() => {}) as unknown as typeof clearTimeout,
  });
  assert.equal(limit, 75);
});
