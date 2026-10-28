// Test-only browser lifecycle/diagnostics. No page content, raw errors or URLs escape.
import { StringDecoder } from "node:string_decoder";
import { availableParallelism, freemem, totalmem } from "node:os";
import { readFileSync, statfsSync } from "node:fs";
import { lstat, mkdir, realpath } from "node:fs/promises";
import { isAbsolute, join, resolve } from "node:path";

// No environment path override: every run owns one exclusive ignored UUID leaf.
export async function createBrowserEvidence(root, runId) {
  if (
    typeof root !== "string" ||
    !isAbsolute(root) ||
    typeof runId !== "string" ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(
      runId,
    )
  )
    throw Error("browser_evidence_rejected");
  try {
    const check = async (path) => {
      const stat = await lstat(path);
      if (
        !stat.isDirectory() ||
        stat.isSymbolicLink() ||
        resolve(await realpath(path)) !== resolve(path)
      )
        throw Error("browser_evidence_rejected");
    };
    await check(root);
    let parent = root;
    for (const name of [".cache", "browser-evidence"]) {
      parent = join(parent, name);
      try {
        await mkdir(parent, { mode: 0o700 });
      } catch (error) {
        if (error.code !== "EEXIST") throw error;
      }
      await check(parent);
    }
    const directory = join(parent, runId);
    await mkdir(directory, { mode: 0o700 }); // Exclusive: collision never becomes reuse.
    await check(directory);
    return directory;
  } catch {
    throw Error("browser_evidence_rejected");
  }
}

export const browserBudgets = Object.freeze({
  startup: 30000,
  discovery: 6000,
  workflow: 30000,
  global: 80000,
  cleanup: 3000,
  shutdown: 3000,
});

export function resourceSnapshot() {
  const integer = (value) =>
    /^\d+$/.test(value ?? "") && Number.isSafeInteger(Number(value))
      ? Number(value)
      : null;
  const read = (path) => {
    try {
      return readFileSync(path, "utf8").slice(0, 4096);
    } catch {
      return "";
    }
  };
  const limits = process.platform === "linux" ? read("/proc/self/limits") : "";
  let sharedMemory = { totalMiB: null, availableMiB: null };
  try {
    const s = statfsSync("/dev/shm");
    sharedMemory = {
      totalMiB: Math.floor((s.bsize * s.blocks) / 1048576),
      availableMiB: Math.floor((s.bsize * s.bavail) / 1048576),
    };
  } catch {
    /* Unavailable on Windows; never report a host path or exception. */
  }
  const cgroup = (name) =>
    process.platform === "linux"
      ? integer(read("/sys/fs/cgroup/" + name).trim())
      : null;
  const available = integer(
    /^MemAvailable:\s+(\d+)/m.exec(read("/proc/meminfo"))?.[1],
  );
  const maximum = cgroup("memory.max"),
    current = cgroup("memory.current");
  return {
    availableCPUs: availableParallelism(),
    totalMemoryMiB: Math.floor(totalmem() / 1048576),
    freeMemoryMiB: Math.floor(freemem() / 1048576),
    availableMemoryMiB:
      available === null ? null : Math.floor(available / 1024),
    sharedMemory,
    processSoftLimit: integer(/^Max processes\s+(\S+)/m.exec(limits)?.[1]),
    filesSoftLimit: integer(/^Max open files\s+(\S+)/m.exec(limits)?.[1]),
    // These describe the mounted cgroup root, not an inferred per-user scope.
    rootCgroupMemoryMaxMiB:
      maximum === null ? null : Math.floor(maximum / 1048576),
    rootCgroupMemoryCurrentMiB:
      current === null ? null : Math.floor(current / 1048576),
    rootCgroupPidsMax: cgroup("pids.max"),
    rootCgroupPidsCurrent: cgroup("pids.current"),
  };
}

const stages = new Set([
  "launch",
  "preflight",
  "devtools",
  "connect",
  "navigate",
  "initial_ui",
  "save",
  "generate",
  "revise",
  "approval_loss",
  "approval_retry",
  "sessions_ready",
  "completion_loss",
  "completion_retry",
  "profile_change",
  "readback",
  "mobile_completion",
  "refresh_history",
  "refresh_readback",
  "owner_switch",
  "owner_error",
  "owner_recovery",
  "assertions",
  "shutdown",
]);
const codes = new Set([
  "sandbox_unavailable",
  "profile_unavailable",
  "resource_exhausted",
  "debugging_policy",
  "stderr_other",
  "stderr_oversized",
  "spawn_error",
  "spawn_success",
  "startup_observing",
  "startup_timeout",
  "browser_exit",
  "devtools_ready",
  "devtools_http_refused",
  "devtools_http_timeout",
  "devtools_http_failed",
  "devtools_http_status",
  "devtools_invalid_json",
  "devtools_response_oversized",
  "devtools_malformed_target",
  "devtools_target_mismatch",
  "devtools_target_unavailable",
  "devtools_target_ready",
  "browser_exited_during_devtools",
  "TypeError",
  "ReferenceError",
  "SyntaxError",
  "Error",
  "console_error",
  "other",
  "net::ERR_CONNECTION_REFUSED",
  "net::ERR_CONNECTION_RESET",
  "net::ERR_FAILED",
  "net::ERR_ABORTED",
  "net::ERR_NAME_NOT_RESOLVED",
  "BlockedByClient",
]);

export function routeClass(url, base) {
  try {
    const parsed = new URL(url);
    if (parsed.origin !== base) return "external";
    const path = parsed.pathname;
    if (path === "/") return "document";
    if (path === "/health" || path === "/ready") return path.slice(1);
    if (path.startsWith("/assets/") || /\.(js|css|ico)$/.test(path))
      return "asset";
    if (path.endsWith("/approve")) return "approval";
    if (path.endsWith("/completion") || path.endsWith("/completions"))
      return "completion";
    if (path.endsWith("/revise/stream")) return "revision";
    if (path.includes("/profile")) return "profile";
    if (path.includes("/draft")) return "generation";
    if (path.includes("/plans")) return "plans";
    return "other_local";
  } catch {
    return "other";
  }
}

export function diagnostics(base) {
  const started = Date.now();
  const events = [];
  let stage = "launch";
  let truncated = false;
  const add = (kind, value = {}) => {
    if (events.length === 32) {
      events.shift();
      truncated = true;
    }
    events.push({
      kind: [
        "stage",
        "browser",
        "console",
        "page",
        "network",
        "response",
      ].includes(kind)
        ? kind
        : "other",
      stage,
      ms: Math.min(80000, Math.max(0, Date.now() - started)),
      ...(value.code
        ? { code: codes.has(value.code) ? value.code : "other" }
        : {}),
      ...(value.url ? { route: routeClass(value.url, base) } : {}),
      ...(Number.isInteger(value.status) &&
      value.status >= 0 &&
      value.status <= 599
        ? { status: value.status }
        : {}),
      ...(Number.isInteger(value.exitCode) &&
      value.exitCode >= -255 &&
      value.exitCode <= 255
        ? { exitCode: value.exitCode }
        : {}),
      ...(Number.isInteger(value.attempt) &&
      value.attempt >= 1 &&
      value.attempt <= 24
        ? { attempt: value.attempt }
        : {}),
      ...(value.signal
        ? {
            signal: [
              "SIGTERM",
              "SIGKILL",
              "SIGABRT",
              "SIGSEGV",
              "SIGTRAP",
              "SIGINT",
            ].includes(value.signal)
              ? value.signal
              : "other",
          }
        : {}),
    });
  };
  return {
    add,
    stage(value) {
      stage = stages.has(value) ? value : "other";
      add("stage");
    },
    snapshot() {
      return { stage, truncated, events: events.map((x) => ({ ...x })) };
    },
  };
}

function stderrClass(line) {
  if (
    /No usable sandbox|Running as root without --no-sandbox|Failed to move to new namespace/i.test(
      line,
    )
  )
    return "sandbox_unavailable";
  if (
    /Singleton|user data directory|cannot create.*directory|Permission denied/i.test(
      line,
    )
  )
    return "profile_unavailable";
  if (
    /pthread_create|Cannot allocate memory|No space left|out of memory/i.test(
      line,
    )
  )
    return "resource_exhausted";
  if (
    /remote debugging.*(disabled|not allowed)|RemoteDebuggingAllowed/i.test(
      line,
    )
  )
    return "debugging_policy";
  return "stderr_other";
}

export function waitForDevTools(
  child,
  diagnostic,
  {
    timeout = 30000,
    timer = setTimeout,
    clear = clearTimeout,
    now = Date.now,
    evidence = {},
  } = {},
) {
  // Chrome's documented ready event does not depend on a separately written file.
  const decoder = new StringDecoder("utf8");
  let line = "";
  let bytes = 0;
  let oversized = false;
  let settled = false;
  const started = now();
  Object.assign(evidence, {
    spawnObserved: false,
    pidAssigned: Boolean(child.pid),
    exitObserved: false,
    stderrBytes: 0,
    stderrChunks: 0,
    stdoutBytes: 0,
    partialLine: false,
    elapsedMs: 0,
    timerLagMs: 0,
  });
  diagnostic.add("browser", { code: "startup_observing" });
  return new Promise((resolve, reject) => {
    const finish = (error, value) => {
      if (settled) return;
      settled = true;
      clear(deadline);
      evidence.elapsedMs = Math.min(80000, Math.max(0, now() - started));
      evidence.partialLine = Boolean(line);
      error ? reject(Error(error)) : resolve(value);
    };
    const deadline = timer(() => {
      evidence.timerLagMs = Math.min(
        80000,
        Math.max(0, now() - started - timeout),
      );
      evidence.exitCodePresent = child.exitCode !== null;
      evidence.signalPresent = Boolean(child.signalCode);
      diagnostic.add("browser", { code: "startup_timeout" });
      finish("devtools_readiness_timeout");
    }, timeout);
    child.once("spawn", () => {
      evidence.spawnObserved = true;
      evidence.pidAssigned = Boolean(child.pid);
      diagnostic.add("browser", { code: "spawn_success" });
    });
    child.stdout?.on("data", (chunk) => {
      evidence.stdoutBytes = Math.min(
        65536,
        evidence.stdoutBytes + chunk.length,
      );
    });
    const consume = (chunk) => {
      bytes += chunk.length;
      evidence.stderrBytes = Math.min(65536, bytes);
      evidence.stderrChunks = Math.min(65536, evidence.stderrChunks + 1);
      if (bytes > 65536) {
        line = "";
        diagnostic.add("browser", { code: "stderr_oversized" });
        return;
      }
      for (const char of decoder.write(chunk)) {
        if (char !== "\n") {
          if (line.length < 4096) line += char;
          else oversized = true;
          continue;
        }
        const text = line.trim();
        line = "";
        if (oversized) {
          oversized = false;
          diagnostic.add("browser", { code: "stderr_oversized" });
          continue;
        }
        const ready =
          /^DevTools listening on (ws:\/\/127\.0\.0\.1:(\d{1,5})\/devtools\/browser\/[a-f0-9-]{36})$/.exec(
            text,
          );
        if (ready && Number(ready[2]) > 0 && Number(ready[2]) <= 65535) {
          diagnostic.add("browser", { code: "devtools_ready" });
          finish(null, { port: Number(ready[2]), browserSocket: ready[1] });
        } else if (text) diagnostic.add("browser", { code: stderrClass(text) });
      }
    };
    child.stderr.on("data", consume);
    child.once("error", () => {
      diagnostic.add("browser", { code: "spawn_error" });
      finish("browser_spawn_failed");
    });
    child.once("exit", (code, signal) => {
      evidence.exitObserved = true;
      if (!settled)
        evidence.elapsedMs = Math.min(80000, Math.max(0, now() - started));
      if (line) {
        diagnostic.add("browser", {
          code: oversized ? "stderr_oversized" : stderrClass(line),
        });
        line = "";
      }
      diagnostic.add("browser", {
        code: "browser_exit",
        exitCode: code,
        signal,
      });
      finish("browser_exited_before_ready");
    });
    if (child.exitCode !== null) finish("browser_exited_before_ready");
  });
}

export const devtoolsFailures = new Set([
  "devtools_http_refused",
  "devtools_http_timeout",
  "devtools_http_failed",
  "devtools_http_status",
  "devtools_invalid_json",
  "devtools_response_oversized",
  "devtools_malformed_target",
  "devtools_target_mismatch",
  "devtools_target_unavailable",
  "browser_exited_during_devtools",
]);

function blankTarget(items, port) {
  if (!Array.isArray(items) || items.length > 16)
    throw Error("devtools_malformed_target");
  if (!items.length) throw Error("devtools_target_unavailable");
  if (
    items.some(
      (item) =>
        !item || typeof item !== "object" || typeof item.type !== "string",
    )
  )
    throw Error("devtools_malformed_target");
  // Chrome may also expose built-in extension workers. Never attach to them.
  // The fresh owned profile must have exactly one page, the requested blank page.
  const pages = items.filter((item) => item.type === "page");
  if (!pages.length) throw Error("devtools_target_unavailable");
  if (pages.length !== 1) throw Error("devtools_target_mismatch");
  const target = pages[0];
  if (
    !target ||
    typeof target !== "object" ||
    typeof target.id !== "string" ||
    !/^[a-fA-F0-9]{32}$/.test(target.id) ||
    typeof target.webSocketDebuggerUrl !== "string"
  )
    throw Error("devtools_malformed_target");
  if (target.type !== "page" || target.url !== "about:blank")
    throw Error("devtools_target_mismatch");
  const expected = `ws://127.0.0.1:${port}/devtools/page/${target.id}`;
  if (target.webSocketDebuggerUrl !== expected)
    throw Error("devtools_target_mismatch");
  return target;
}

export async function waitForPageTarget(
  child,
  port,
  diagnostic,
  {
    deadline = Date.now() + 6000,
    now = Date.now,
    request = globalThis.fetch,
    timer = setTimeout,
    clear = clearTimeout,
    pause = (ms, signal) =>
      new Promise((resolve, reject) => {
        const abort = () => {
          clearTimeout(handle);
          reject(Error("browser_exited_during_devtools"));
        };
        const handle = setTimeout(() => {
          signal.removeEventListener("abort", abort);
          resolve();
        }, ms);
        signal.addEventListener("abort", abort, { once: true });
        if (signal.aborted) abort();
      }),
  } = {},
) {
  if (!Number.isInteger(port) || port < 1 || port > 65535)
    throw Error("devtools_target_mismatch");
  const lifetime = new AbortController();
  const exited = () => lifetime.abort();
  child.once("exit", exited);
  child.once("error", exited);
  let last = "devtools_target_unavailable";
  try {
    for (let attempt = 1; attempt <= 24 && now() < deadline; attempt++) {
      if (
        child.exitCode !== null ||
        child.signalCode ||
        lifetime.signal.aborted
      )
        throw Error("browser_exited_during_devtools");
      const timeout = new AbortController();
      const handle = timer(
        () => timeout.abort(),
        Math.min(2000, deadline - now()),
      );
      const signal = AbortSignal.any([lifetime.signal, timeout.signal]);
      try {
        // Discovery is read-only and retry-safe; /json/new creates a page and is
        // deliberately never retried (or used). No application request is replayed.
        const response = await request(`http://127.0.0.1:${port}/json/list`, {
          method: "GET",
          redirect: "error",
          signal,
        });
        if (response.status !== 200) {
          diagnostic.add("browser", {
            code: "devtools_http_status",
            status: response.status,
            attempt,
          });
          await response.body?.cancel().catch(() => {});
          throw Error("devtools_http_status");
        }
        const reader = response.body?.getReader();
        let text = "";
        let bytes = 0;
        const decoder = new TextDecoder("utf-8", { fatal: true });
        if (!reader) throw Error("devtools_invalid_json");
        try {
          for (;;) {
            const { done, value } = await reader.read();
            if (done) break;
            bytes += value.byteLength;
            if (bytes > 65536) throw Error("devtools_response_oversized");
            text += decoder.decode(value, { stream: true });
          }
          text += decoder.decode();
        } finally {
          await reader.cancel().catch(() => {});
          reader.releaseLock();
        }
        let items;
        try {
          items = JSON.parse(text);
        } catch {
          throw Error("devtools_invalid_json");
        }
        const target = blankTarget(items, port);
        if (signal.aborted) throw Error("devtools_http_timeout");
        diagnostic.add("browser", { code: "devtools_target_ready", attempt });
        return { target, attempts: attempt };
      } catch (error) {
        last = lifetime.signal.aborted
          ? "browser_exited_during_devtools"
          : timeout.signal.aborted || error?.name === "TimeoutError"
            ? "devtools_http_timeout"
            : devtoolsFailures.has(error?.message)
              ? error.message
              : error?.cause?.code === "ECONNREFUSED"
                ? "devtools_http_refused"
                : error instanceof TypeError &&
                    error.code === "ERR_ENCODING_INVALID_ENCODED_DATA"
                  ? "devtools_invalid_json"
                  : "devtools_http_failed";
        diagnostic.add("browser", { code: last, attempt });
        if (
          !new Set([
            "devtools_http_refused",
            "devtools_http_timeout",
            "devtools_http_failed",
            "devtools_target_unavailable",
          ]).has(last)
        )
          throw Error(last);
      } finally {
        clear(handle);
      }
      if (now() < deadline)
        await pause(Math.min(250, deadline - now()), lifetime.signal);
    }
    throw Error(last);
  } finally {
    child.removeListener("exit", exited);
    child.removeListener("error", exited);
  }
}

export async function serverStatus(base) {
  if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(base))
    throw Error("local_server_only");
  const status = {};
  for (const path of ["/health", "/ready"]) {
    try {
      const response = await fetch(base + path, {
        redirect: "error",
        signal: AbortSignal.timeout(750),
      });
      status[path.slice(1)] = response.status;
      await response.body?.cancel();
    } catch {
      status[path.slice(1)] = 0;
    }
  }
  return status;
}
