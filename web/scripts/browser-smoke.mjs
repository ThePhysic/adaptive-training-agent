// Optional real-browser evidence against an isolated localhost test application.
// No browser download. All writes stay in this workspace; nonlocal page requests fail.
import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve, join } from "node:path";
import { randomUUID } from "node:crypto";
import assert from "node:assert/strict";
import {
  diagnostics,
  browserBudgets,
  devtoolsFailures,
  routeClass,
  resourceSnapshot,
  serverStatus,
  waitForDevTools,
  waitForPageTarget,
} from "./browser-support.mjs";

const [base, executable] = process.argv.slice(2);
assert(/^http:\/\/127\.0\.0\.1:\d+$/.test(base));
const root = resolve("..");
const evidenceStage = process.env.FATA_BROWSER_EVIDENCE_STAGE ?? "f1-07";
assert(
  [
    "f1-07",
    "f2-01",
    "f2-02",
    "f2-03",
    "f2-04",
    "f3-02",
    "f3-03a",
    "f3-03b",
    "f3-03d",
    "f3-04a",
    "f3-04b",
    "f3-04c",
    "f3-05a",
    "f4-01",
    "f4-03b-r5a-ci",
    "f4-03b-r5a-devtools",
    "f4-03b-r5a-startup",
    "f5-d1",
  ].includes(evidenceStage),
);
const profile = join(root, ".cache", "browser-f107-" + randomUUID());
const evidence = join(root, "docs", "implementation", "evidence");
// The Python owner establishes a process group/Windows Job before releasing us.
// This prevents Chrome escaping cleanup if Node is killed or crashes.
if (process.env.FATA_BROWSER_SUPERVISED === "1") {
  await new Promise((resolve, reject) => {
    let message = "",
      bytes = 0;
    const timer = setTimeout(
      () => reject(Error("browser_owner_not_ready")),
      5000,
    );
    process.stdin.on("data", (data) => {
      bytes += data.length;
      if (bytes <= 3) message += data.toString();
    });
    process.stdin.once("end", () => {
      clearTimeout(timer);
      bytes === 3 && message === "go\n"
        ? resolve()
        : reject(Error("browser_owner_not_ready"));
    });
  });
}
let browser, browserExited, ws, control;
const diagnostic = diagnostics(base);
const startup = {};
const version = process.env.FATA_BROWSER_VERSION ?? "";
const environment = {
  chromeVersion: /^\d{1,3}\.\d{1,4}\.\d{1,6}\.\d{1,6}$/.test(version)
    ? version
    : null,
  before: resourceSnapshot(),
};
const started = Date.now();
const globalDeadline = started + browserBudgets.global;
let scriptDeadline = globalDeadline;
const watchdog = setTimeout(() => {
  console.error(
    JSON.stringify({
      failure: "browser_global_timeout",
      browserSmokeFailure: diagnostic.snapshot(),
      startup,
      environment,
    }),
  );
  browser?.kill();
  process.exit(1); // Python's OS-level ownership still terminates the owned tree.
}, browserBudgets.global);
try {
  diagnostic.stage("preflight");
  await mkdir(profile, { recursive: true });
  await mkdir(evidence, { recursive: true });
  diagnostic.stage("launch");
  const spawnStarted = Date.now();
  try {
    browser = spawn(
      executable,
      [
        "--headless=new",
        "--no-first-run",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-sync",
        "--disable-breakpad",
        "--disable-default-apps",
        "--metrics-recording-only",
        "--no-proxy-server",
        "--disable-features=MediaRouter,OptimizationHints,AutofillServerCommunication",
        "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
        "--remote-debugging-port=0",
        "--remote-debugging-address=127.0.0.1",
        "--user-data-dir=" + profile,
        "about:blank",
      ],
      { windowsHide: true, stdio: ["ignore", "pipe", "pipe"] },
    );
  } catch {
    diagnostic.add("browser", { code: "spawn_error" });
    throw Error("browser_spawn_failed");
  }
  browserExited = new Promise((resolve) => {
    browser.once("exit", resolve);
    browser.once("error", resolve);
  });
  // Attach observation synchronously after spawn, before any awaited operation.
  const ready = waitForDevTools(browser, diagnostic, {
    timeout: browserBudgets.startup,
    evidence: startup,
  });
  async function until(read, timeout = 15000) {
    const end = Math.min(scriptDeadline, Date.now() + timeout);
    while (Date.now() < end) {
      const value = await read();
      if (value) return value;
      await new Promise((resolve) => setTimeout(resolve, 25));
    }
    throw Error("browser_condition_timeout");
  }
  const { port, browserSocket } = await ready;
  const readyMs = Date.now() - spawnStarted;
  diagnostic.stage("devtools");
  const { target, attempts } = await waitForPageTarget(
    browser,
    port,
    diagnostic,
    {
      deadline: Math.min(globalDeadline, Date.now() + browserBudgets.discovery),
    },
  );
  const targetMs = Date.now() - spawnStarted - readyMs;
  const workflowStarted = Date.now();
  scriptDeadline = Math.min(
    globalDeadline,
    workflowStarted + browserBudgets.workflow,
  );
  diagnostic.stage("connect");
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    const deadline = setTimeout(
      () => reject(Error("cdp_connect_timeout")),
      3000,
    );
    ws.addEventListener(
      "open",
      () => {
        clearTimeout(deadline);
        resolve();
      },
      { once: true },
    );
    ws.addEventListener(
      "error",
      () => {
        clearTimeout(deadline);
        reject(Error("cdp_connect_failed"));
      },
      { once: true },
    );
  });
  let id = 0;
  const pending = new Map();
  const errors = [];
  const blocked = [];
  const command = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const sequence = ++id;
      const deadline = setTimeout(
        () => {
          pending.delete(sequence);
          reject(Error("cdp_command_timeout"));
        },
        Math.max(1, Math.min(3000, scriptDeadline - Date.now())),
      );
      pending.set(sequence, { resolve, reject, deadline });
      ws.send(JSON.stringify({ id: sequence, method, params }));
    });
  ws.addEventListener("message", ({ data }) => {
    const message = JSON.parse(data);
    if (message.id) {
      const entry = pending.get(message.id);
      if (!entry) return;
      pending.delete(message.id);
      clearTimeout(entry.deadline);
      message.error
        ? entry.reject(Error("cdp_command_failed"))
        : entry.resolve(message.result);
    }
    if (message.method === "Runtime.exceptionThrown") {
      if (errors.length < 32) errors.push("page_exception");
      diagnostic.add("page", {
        code: message.params.exceptionDetails.exception?.className ?? "other",
      });
    }
    if (
      message.method === "Runtime.consoleAPICalled" &&
      message.params.type === "error"
    )
      diagnostic.add("console", { code: "console_error" });
    if (message.method === "Network.responseReceived")
      diagnostic.add("response", {
        url: message.params.response.url,
        status: message.params.response.status,
      });
    if (message.method === "Network.loadingFailed")
      diagnostic.add("network", { code: message.params.errorText });
    if (message.method === "Fetch.requestPaused") {
      const { requestId, request } = message.params;
      if (request.url.startsWith(base + "/"))
        void command("Fetch.continueRequest", { requestId }).catch(() =>
          diagnostic.add("network", { code: "other" }),
        );
      else {
        if (blocked.length < 32) blocked.push(routeClass(request.url, base));
        void command("Fetch.failRequest", {
          requestId,
          errorReason: "BlockedByClient",
        }).catch(() => diagnostic.add("network", { code: "other" }));
      }
    }
  });
  const evaluate = async (expression) => {
    const result = await command("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (result.exceptionDetails) throw Error("Browser evaluation failed");
    return result.result.value;
  };
  const wait = (stage, expression) => {
    diagnostic.stage(stage);
    return until(() =>
      evaluate(`(()=>{try{return !!(${expression})}catch{return false}})()`),
    );
  };
  async function screenshot(name) {
    const metrics = await command("Page.getLayoutMetrics");
    const { data } = await command("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: true,
      clip: {
        x: 0,
        y: 0,
        width: metrics.cssContentSize.width,
        height: metrics.cssContentSize.height,
        scale: 1,
      },
    });
    await writeFile(join(evidence, name), Buffer.from(data, "base64"));
  }
  const click = (text) =>
    evaluate(
      `[...document.querySelectorAll('button')].find(b=>b.textContent===${JSON.stringify(text)}).click()`,
    );
  await command("Runtime.enable");
  await command("Page.enable");
  await command("Network.enable");
  await command("Fetch.enable", { patterns: [{ urlPattern: "*" }] });
  await command("Page.addScriptToEvaluateOnNewDocument", {
    source: `
    window.__approvalKeys=[];
    window.__sessionAttempts=[];
    const originalFetch=window.fetch.bind(window);
    let loseFirstApproval=true;
    let loseFirstSession=true;
    window.fetch=async(input,options)=>{
      const path=typeof input==='string'?input:input.url;
      const approval=path.endsWith('/approve');
      const submission=path.endsWith('/completion') && options?.method==='POST';
      if(submission)window.__sessionAttempts.push(JSON.parse(options.body));
      if(approval)window.__approvalKeys.push(JSON.parse(options.body).idempotency_key);
      const response=await originalFetch(input,options);
      if(approval && response.ok && loseFirstApproval){
        loseFirstApproval=false;await response.text();
        throw new TypeError('Synthetic lost successful approval response');
      }
      if(submission && response.ok && loseFirstSession){
        loseFirstSession=false;await response.text();
        throw new TypeError('Synthetic lost successful session response');
      }
      return response;
    };
  `,
  });
  await command("Emulation.setDeviceMetricsOverride", {
    width: 1440,
    height: 1100,
    deviceScaleFactor: 1,
    mobile: false,
  });
  diagnostic.stage("navigate");
  await command("Page.navigate", { url: base + "/" });
  await wait(
    "initial_ui",
    "document.body.textContent.includes('Save to begin')",
  );
  await evaluate("document.querySelector('.attestation input').click()");
  await click("Save profile");
  await wait(
    "save",
    "document.body.textContent.includes('Preferences saved. Ready to generate.')",
  );
  await click("Generate preview");
  await wait(
    "generate",
    "!!document.querySelector('[data-complete=\"true\"]')",
  );
  assert.equal(
    await evaluate(
      "[...document.querySelectorAll('button')].find(b=>b.textContent==='Approve & save').disabled",
    ),
    false,
  );
  await click("Revise once");
  await wait(
    "revise",
    "!!document.querySelector('[data-complete=\"true\"]') && [...document.querySelectorAll('button')].find(b=>b.textContent==='Stop').disabled",
  );
  assert.equal(
    await evaluate(
      "[...document.querySelectorAll('button')].find(b=>b.textContent==='Revise once').disabled",
    ),
    true,
  );
  await click("Approve & save");
  await wait(
    "approval_loss",
    "[...document.querySelectorAll('button')].some(b=>b.textContent==='Retry approval' && !b.disabled)",
  );
  await click("Retry approval");
  await wait(
    "approval_retry",
    "!!document.querySelector('.saved') && [...document.querySelectorAll('button')].some(b=>b.textContent==='Open saved plan' && !b.disabled)",
  );
  assert.equal(
    await evaluate(
      "window.__approvalKeys.length===2 && window.__approvalKeys[0]===window.__approvalKeys[1]",
    ),
    true,
  );
  await wait(
    "sessions_ready",
    "!!document.querySelector('[aria-label=\"Session 1 status\"]') && !document.querySelector('[aria-label=\"Session 1 status\"]').disabled",
  );
  assert.equal(await evaluate("window.__sessionAttempts.length"), 0);
  assert.equal(
    await evaluate("document.querySelectorAll('[data-session-record]').length"),
    0,
  );
  for (const [label, value] of [
    ["Session 1 status", "completed"],
    ["Session 1 effort", "moderate"],
    ["Session 1 rating", "4"],
  ]) {
    await evaluate(
      `(()=>{const element=document.querySelector('[aria-label="${label}"]');element.value='${value}';element.dispatchEvent(new Event('change',{bubbles:true}));})()`,
    );
  }
  await click("Submit session 1 record");
  await wait(
    "completion_loss",
    "[...document.querySelectorAll('button')].some(b=>b.textContent==='Retry the same submission' && !b.disabled)",
  );
  assert.equal(
    await evaluate("document.querySelectorAll('[data-session-record]').length"),
    0,
  );
  await click("Retry the same submission");
  await wait(
    "completion_retry",
    "document.querySelector('[data-session-record=\"1\"]')?.textContent.includes('Submitted: completed')",
  );
  assert.equal(
    await evaluate(
      "window.__sessionAttempts.length===2 && JSON.stringify(window.__sessionAttempts[0])===JSON.stringify(window.__sessionAttempts[1])",
    ),
    true,
  );
  // Change current preferences, then read the independently stored old plan and record.
  await evaluate(
    "const preset=[...document.querySelectorAll('label')].find(l=>l.firstChild?.textContent==='Session preset').querySelector('select');preset.value='30';preset.dispatchEvent(new Event('change',{bubbles:true}));",
  );
  await click("Save profile");
  await wait(
    "profile_change",
    "document.body.textContent.includes('Saved revision 2')",
  );
  await click("Open saved plan");
  await wait(
    "readback",
    "!!document.querySelector('.saved') && document.querySelector('.plan').textContent.includes('Requested preset: 20 minutes')",
  );
  assert.equal(
    await evaluate(
      "[...document.querySelectorAll('button')].find(b=>b.textContent==='Approve & save').disabled",
    ),
    true,
  );
  await wait(
    "readback",
    "document.querySelector('[data-session-record=\"1\"]')?.textContent.includes('rating: 4')",
  );
  assert.equal(
    await evaluate("document.documentElement.scrollWidth > innerWidth"),
    false,
  );
  await screenshot(`${evidenceStage}-desktop.png`);
  await command("Emulation.setDeviceMetricsOverride", {
    width: 390,
    height: 844,
    deviceScaleFactor: 1,
    mobile: true,
  });
  await evaluate(
    "const status=document.querySelector('[aria-label=\"Session 2 status\"]');status.value='skipped';status.dispatchEvent(new Event('change',{bubbles:true}));",
  );
  assert.equal(
    await evaluate(
      "document.querySelector('[aria-label=\"Session 2 effort\"]').disabled && document.querySelector('[aria-label=\"Session 2 rating\"]').disabled",
    ),
    true,
  );
  await click("Submit session 2 record");
  await wait(
    "mobile_completion",
    "document.querySelector('[data-session-record=\"2\"]')?.textContent.includes('Submitted: skipped')",
  );
  assert.equal(
    await evaluate("document.documentElement.scrollWidth > innerWidth"),
    false,
  );
  await screenshot(`${evidenceStage}-mobile.png`);
  // A fresh page must recover only durable history, never a transient approval.
  await command("Page.reload", { ignoreCache: true });
  await wait(
    "refresh_history",
    "[...document.querySelectorAll('button')].some(b=>b.textContent==='Open saved plan' && !b.disabled)",
  );
  assert.equal(await evaluate("!!document.querySelector('.plan')"), false);
  await click("Open saved plan");
  await wait(
    "refresh_readback",
    "document.querySelector('[data-session-record=\"1\"]')?.textContent.includes('rating: 4') && document.querySelector('[data-session-record=\"2\"]')?.textContent.includes('Submitted: skipped')",
  );
  assert.equal(
    await evaluate(
      "[...document.querySelectorAll('button')].find(b=>b.textContent==='Approve & save').disabled",
    ),
    true,
  );
  await evaluate(
    "const select=document.querySelector('[aria-label=\"Synthetic profile\"]');select.value='synthetic-b';select.dispatchEvent(new Event('change',{bubbles:true}));",
  );
  await wait(
    "owner_switch",
    "document.body.textContent.includes('Save to begin') && !document.querySelector('.plan')",
  );
  assert.equal(
    await evaluate("document.body.textContent.includes('Open saved plan')"),
    false,
  );
  await evaluate("document.querySelector('.attestation input').click()");
  await click("Save profile");
  await wait(
    "owner_error",
    "document.querySelector('[role=status]').textContent.includes('The request could not be completed.')",
  );
  assert.equal(
    await evaluate(
      "[...document.querySelectorAll('button')].find(b=>b.textContent==='Generate preview').disabled",
    ),
    true,
  );
  await screenshot(`${evidenceStage}-mobile-error.png`);
  await click("Save profile");
  await wait(
    "owner_recovery",
    "document.body.textContent.includes('Preferences saved. Ready to generate.')",
  );
  diagnostic.stage("assertions");
  assert.deepEqual(errors, []);
  assert.deepEqual(blocked, []); // The local application requested no external resources.
  console.log(
    JSON.stringify({
      ui: "save -> generate -> revise -> lost approval response -> same-key retry -> durable readback -> profile change -> immutable history -> page refresh -> owner switch",
      sameKeyRetry: true,
      completionSameKeyRetry: true,
      sessionRecords: 2,
      mobileErrorRecovery: true,
      horizontalOverflow: false,
      approval: "enabled only for complete review; disabled for stored history",
      runtimeErrors: errors.length,
      externalPageRequests: blocked.length,
      startup,
      environment,
      budgets: browserBudgets,
      timing: {
        readyMs,
        targetMs,
        discoveryAttempts: attempts,
        workflowMs: Date.now() - workflowStarted,
        totalMs: Date.now() - started,
      },
      screenshots: [
        `${evidenceStage}-desktop.png`,
        `${evidenceStage}-mobile.png`,
        `${evidenceStage}-mobile-error.png`,
      ],
    }),
  );
  // Close through browser-level CDP so its renderer processes exit too.
  diagnostic.stage("shutdown");
  // The ready signal already validated this owned browser endpoint. Avoid a
  // second discovery HTTP dependency after completing the application workflow.
  control = new WebSocket(browserSocket);
  await new Promise((resolve, reject) => {
    const deadline = setTimeout(
      () => reject(Error("cdp_connect_timeout")),
      browserBudgets.shutdown,
    );
    control.addEventListener(
      "open",
      () => {
        clearTimeout(deadline);
        resolve();
      },
      { once: true },
    );
    control.addEventListener(
      "error",
      () => {
        clearTimeout(deadline);
        reject(Error("cdp_connect_failed"));
      },
      { once: true },
    );
  });
  control.send(JSON.stringify({ id: 1, method: "Browser.close" }));
  control.close();
} catch (error) {
  const allowed = new Set([
    ...devtoolsFailures,
    "devtools_readiness_timeout",
    "browser_spawn_failed",
    "browser_exited_before_ready",
    "browser_condition_timeout",
    "cdp_connect_timeout",
    "cdp_connect_failed",
    "cdp_command_timeout",
    "cdp_command_failed",
  ]);
  const failure =
    error?.code === "ERR_ASSERTION"
      ? "assertion_failed"
      : allowed.has(error?.message)
        ? error.message
        : "browser_step_failed";
  console.error(
    JSON.stringify({
      failure,
      browserSmokeFailure: diagnostic.snapshot(),
      startup,
      environment: { ...environment, atFailure: resourceSnapshot() },
      budgets: browserBudgets,
      server: await serverStatus(base),
    }),
  );
  process.exitCode = 1;
} finally {
  clearTimeout(watchdog);
  ws?.close();
  control?.close();
  if (
    browser?.pid &&
    browser.exitCode === null &&
    browser.signalCode === null
  ) {
    browser.kill();
    let deadline;
    await Promise.race([
      browserExited,
      new Promise((resolve) => {
        deadline = setTimeout(resolve, browserBudgets.cleanup / 2);
      }),
    ]);
    clearTimeout(deadline);
    if (browser.exitCode === null && browser.signalCode === null) {
      browser.kill("SIGKILL");
      await Promise.race([
        browserExited,
        new Promise((resolve) => {
          deadline = setTimeout(resolve, browserBudgets.cleanup / 2);
        }),
      ]);
      clearTimeout(deadline);
    }
  }
}
