import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { PassThrough } from "node:stream";
import type { ChildProcess } from "node:child_process";
import { test } from "node:test";
import { mkdtemp, mkdir, readFile, symlink, writeFile } from "node:fs/promises";
import { join, relative } from "node:path";
import { tmpdir } from "node:os";
import { randomUUID } from "node:crypto";
import {
  diagnostics,
  createBrowserEvidence,
  browserBudgets,
  resourceSnapshot,
  routeClass,
  serverStatus,
  waitForDevTools,
} from "../scripts/browser-support.mjs";

const base = "http://127.0.0.1:8000";
const ready =
  "DevTools listening on ws://127.0.0.1:4321/devtools/browser/00000000-0000-0000-0000-000000000000\n";
function fake() {
  return Object.assign(new EventEmitter(), {
    stderr: new PassThrough(),
    exitCode: null,
  });
}

test("slow successful startup has independent budget and records spawn without private PID", async () => {
  const child = Object.assign(fake(), {
    pid: 987654,
    stdout: new PassThrough(),
  });
  const d = diagnostics(base),
    clock = deadline();
  let now = 0;
  const evidence: Record<string, number | boolean> = {};
  const result = waitForDevTools(child as unknown as ChildProcess, d, {
    ...clock.options,
    now: () => now,
    evidence,
  });
  child.emit("spawn");
  now = 18000; // Beyond the old 15s budget; no actual sleep.
  child.stderr.write(ready);
  await result;
  assert.equal(browserBudgets.startup, 30000);
  assert.equal(browserBudgets.workflow, 30000);
  assert(
    browserBudgets.startup +
      browserBudgets.discovery +
      browserBudgets.workflow +
      browserBudgets.cleanup +
      browserBudgets.shutdown <
      browserBudgets.global,
  );
  assert.equal(evidence.elapsedMs, 18000);
  assert(evidence.spawnObserved && evidence.pidAssigned);
  now = 25000;
  child.emit("exit", 0);
  assert.equal(evidence.elapsedMs, 18000); // Startup timing survives later exit.
  assert.doesNotMatch(
    JSON.stringify({ evidence, diagnostic: d.snapshot() }),
    /987654|4321|00000000/,
  );
});

for (const mode of ["silent", "partial", "stdout only", "scheduler lag"]) {
  test(`permanently hung ${mode} startup produces bounded evidence`, async () => {
    const child = Object.assign(fake(), {
      pid: 123456,
      stdout: new PassThrough(),
    });
    const d = diagnostics(base),
      clock = deadline();
    let now = 0;
    const evidence: Record<string, number | boolean> = {};
    const result = waitForDevTools(child as unknown as ChildProcess, d, {
      ...clock.options,
      now: () => now,
      evidence,
    });
    child.emit("spawn");
    if (mode === "partial") child.stderr.write("private-partial-line-canary");
    if (mode === "stdout only") child.stdout.write(ready);
    now = mode === "scheduler lag" ? 34000 : 30000;
    clock.expire();
    await assert.rejects(result, /devtools_readiness_timeout/);
    assert.equal(evidence.partialLine, mode === "partial");
    assert.equal(evidence.stderrBytes, mode === "partial" ? 27 : 0);
    assert.equal(evidence.timerLagMs, mode === "scheduler lag" ? 4000 : 0);
    assert.equal(evidence.exitObserved, false);
    if (mode === "stdout only") assert(Number(evidence.stdoutBytes) > 0);
    assert.match(
      JSON.stringify(d.snapshot()),
      /spawn_success.*startup_timeout/,
    );
    assert.doesNotMatch(
      JSON.stringify({ evidence, diagnostic: d.snapshot() }),
      /private-|123456|4321/,
    );
    assert(clock.cleared());
  });
}

test("signaled early exit is observed and only allowlisted signals are reported", async () => {
  const child = fake(),
    d = diagnostics(base),
    clock = deadline();
  const evidence: Record<string, number | boolean> = {};
  const result = waitForDevTools(child as unknown as ChildProcess, d, {
    ...clock.options,
    evidence,
  });
  child.emit("exit", null, "SIGKILL");
  await assert.rejects(result, /browser_exited_before_ready/);
  assert(evidence.exitObserved);
  assert.match(JSON.stringify(d.snapshot()), /SIGKILL/);
  d.add("browser", { signal: "private-signal-canary" });
  assert.doesNotMatch(JSON.stringify(d.snapshot()), /private-signal/);
});

test("resource evidence contains numerical availability only, no environment values or paths", () => {
  process.env.BROWSER_PRIVATE_CANARY = "credential-prompt-profile-canary";
  try {
    const report = resourceSnapshot();
    const numeric = (value: unknown): boolean =>
      value === null ||
      (typeof value === "number" && Number.isFinite(value) && value >= 0) ||
      (typeof value === "object" && Object.values(value!).every(numeric));
    assert(numeric(report));
    assert.doesNotMatch(
      JSON.stringify(report),
      /canary|http:|Users|\/proc|\/dev/,
    );
  } finally {
    delete process.env.BROWSER_PRIVATE_CANARY;
  }
});
function deadline() {
  let callback: () => void = () => {
    throw Error("timer not registered");
  };
  let cleared = false;
  return {
    options: {
      timer: ((fn: () => void) => {
        callback = fn;
        return 1;
      }) as unknown as typeof setTimeout,
      clear: (() => {
        cleared = true;
      }) as unknown as typeof clearTimeout,
    },
    expire: () => callback(),
    cleared: () => cleared,
  };
}

test("Chrome ready event handles split chunks without DevToolsActivePort or sleeps", async () => {
  const child = fake();
  const d = diagnostics(base);
  const clock = deadline();
  const result = waitForDevTools(
    child as unknown as ChildProcess,
    d,
    clock.options,
  );
  child.stderr.write("No usable sandbox private-secret-canary\n");
  child.stderr.write(ready.slice(0, 23));
  child.stderr.write(ready.slice(23));
  assert.equal((await result).port, 4321);
  assert(clock.cleared());
  assert.match(JSON.stringify(d.snapshot()), /sandbox_unavailable/);
  assert.doesNotMatch(
    JSON.stringify(d.snapshot()),
    /private-secret|00000000|4321/,
  );
});

test("early browser exit fails immediately and preserves classified stderr and exit", async () => {
  const child = fake();
  const d = diagnostics(base);
  const clock = deadline();
  const result = waitForDevTools(
    child as unknown as ChildProcess,
    d,
    clock.options,
  );
  child.stderr.write("No usable sandbox! private-profile-canary");
  child.emit("exit", 1);
  await assert.rejects(result, /browser_exited_before_ready/);
  assert(clock.cleared());
  assert.match(JSON.stringify(d.snapshot()), /sandbox_unavailable/);
  assert.match(JSON.stringify(d.snapshot()), /"exitCode":1/);
  assert.doesNotMatch(JSON.stringify(d.snapshot()), /private-profile/);
});

test("missing browser executable fails without echoing its private path", async () => {
  const child = fake();
  const d = diagnostics(base);
  const result = waitForDevTools(
    child as unknown as ChildProcess,
    d,
    deadline().options,
  );
  child.emit("error", Error("credential-path-canary"));
  await assert.rejects(result, /browser_spawn_failed/);
  assert.doesNotMatch(JSON.stringify(d.snapshot()), /credential-path/);
});

for (const message of [
  ready.replace("127.0.0.1", "private-credential.invalid"),
  ready.replace(":4321", ":0"),
  ready.replace("\n", "?private-canary\n"),
  ready.trimEnd() + " ".repeat(5000) + "\n",
  "unrelated-private-canary\n",
])
  test("missing, invalid or oversized readiness cannot pass", async () => {
    const child = fake();
    const d = diagnostics(base);
    const clock = deadline();
    const result = waitForDevTools(
      child as unknown as ChildProcess,
      d,
      clock.options,
    );
    child.stderr.write(message);
    clock.expire();
    await assert.rejects(result, /devtools_readiness_timeout/);
    assert.doesNotMatch(
      JSON.stringify(d.snapshot()),
      /private-canary|credential.invalid/,
    );
  });

test("bounded diagnostic ring never includes URLs, page text, private errors or identifiers", () => {
  const d = diagnostics(base);
  d.stage("private-stage-canary");
  for (let i = 0; i < 100; i++)
    d.add("network", {
      url: base + "/api/v1/drafts/private-id/approve?token=secret",
      code: "private-response-canary",
      status: 503,
    });
  const result = d.snapshot();
  assert.equal(result.events.length, 32);
  assert(result.truncated);
  assert.doesNotMatch(JSON.stringify(result), /private-|token|secret|http:/);
  assert.equal(
    routeClass(base + "/api/v1/drafts/id/approve", base),
    "approval",
  );
  assert.equal(
    routeClass(base + "/api/v1/drafts/private-id/revise/stream", base),
    "revision",
  );
  assert.equal(
    routeClass("https://credential.invalid/secret", base),
    "external",
  );
});

test("server diagnostics retain only status codes and cancel private bodies", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (input) =>
    new Response("private-server-body-canary", {
      status: String(input).endsWith("/health") ? 200 : 503,
    });
  try {
    assert.deepEqual(await serverStatus(base), { health: 200, ready: 503 });
  } finally {
    globalThis.fetch = original;
  }
});

test("server diagnostics reject nonlocal destinations before fetching", async () => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    throw Error("Must not fetch");
  };
  try {
    await assert.rejects(
      serverStatus("https://private-credential.invalid"),
      /local_server_only/,
    );
    assert.equal(calls, 0);
  } finally {
    globalThis.fetch = original;
  }
});

// Every directory below is newly test-owned; never touch accepted screenshot evidence.
test("browser evidence is exclusive, ignored and cannot overwrite historical screenshots", async () => {
  const root = await mkdtemp(join(tmpdir(), "fata-browser-evidence-"));
  const historical = join(root, "docs", "implementation", "evidence");
  await mkdir(historical, { recursive: true });
  const original = join(historical, "f1-07-desktop.png");
  await writeFile(original, "accepted-historical-bytes", { flag: "wx" });
  const id = randomUUID();
  const first = await createBrowserEvidence(root, id);
  assert.equal(
    relative(root, first).replaceAll("\\", "/"),
    `.cache/browser-evidence/${id}`,
  );
  const screenshot = join(first, "f1-07-desktop.png");
  await writeFile(screenshot, "fresh-evidence", { flag: "wx" });
  await assert.rejects(
    createBrowserEvidence(root, id),
    /browser_evidence_rejected/,
  );
  await assert.rejects(writeFile(screenshot, "replacement", { flag: "wx" }), {
    code: "EEXIST",
  });
  assert.equal(await readFile(original, "utf8"), "accepted-historical-bytes");
  assert.equal(await readFile(screenshot, "utf8"), "fresh-evidence");
  assert.notEqual(await createBrowserEvidence(root, randomUUID()), first);
});

for (const value of [
  "../docs/implementation/evidence",
  "C:/private",
  "",
  "a".repeat(500),
  "../" + randomUUID(),
]) {
  test(
    "browser evidence rejects unsafe run identity " +
      JSON.stringify(value.slice(0, 40)),
    async () => {
      const root = await mkdtemp(join(tmpdir(), "fata-browser-reject-"));
      await assert.rejects(
        createBrowserEvidence(root, value),
        /^Error: browser_evidence_rejected$/,
      );
      await assert.rejects(readFile(join(root, ".cache")), { code: "ENOENT" });
    },
  );
}

test("browser evidence rejects linked cache parents without writing through them", async () => {
  const root = await mkdtemp(join(tmpdir(), "fata-browser-link-"));
  const outside = await mkdtemp(join(tmpdir(), "fata-browser-outside-"));
  await symlink(
    outside,
    join(root, ".cache"),
    process.platform === "win32" ? "junction" : "dir",
  );
  await assert.rejects(
    createBrowserEvidence(root, randomUUID()),
    /^Error: browser_evidence_rejected$/,
  );
  await assert.rejects(readFile(join(outside, "browser-evidence")), {
    code: "ENOENT",
  });
});
