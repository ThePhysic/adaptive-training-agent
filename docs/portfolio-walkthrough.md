# Four-minute technical walkthrough

This is a recording storyboard, not an existing video or a report of a human study.
Reuse the [verified screenshots](implementation/f5-d1-report.md#demonstrated-application)
and [local demonstration](local-demonstration.md). No new image or video was
generated for F5-D2; no manual usability session is claimed.

## Prepare the capture

Use only a fresh demo project with synthetic data, built from the reviewed source.
Follow the hands-on container section of the demonstration runbook; keep loopback
networking and one worker. Do not record a terminal containing private AWS files,
identity results, environment dumps, browser password UI or account tabs. Close
unrelated windows/notifications before recording. Use an already available screen
recorder; this task does not install or configure one. Store a draft locally for
owner review before any upload. Show the browser window, not the entire desktop.

No special slow-provider mode is needed. Fake generation is fast: explain the
streaming stages or show the existing SSE tests rather than fabricating a long
model response. Do not call it a real LLM. Keep the public synthetic practice
results visibly distinct from collected human judgments.

## Shot list

| Time | Show | Explain / verify |
| --- | --- | --- |
| 0:00–0:20 | Workspace and architecture | “This local synthetic demo focuses on safe orchestration and explicit approval. Real-model and independent-human evaluation remain deferred.” |
| 0:20–1:00 | Attest synthetic adult preferences, Save general strength/bodyweight/beginner/two days/20 minutes, Generate | Save is explicit and revisioned. FastAPI streams status and a validated terminal plan; a partial stream cannot authorize approval |
| 1:00–1:30 | Review plan and Revise once | Read tools are bounded; domain checks are independent of provider output. This is one supported revision, not an unconstrained chat trainer |
| 1:30–2:05 | Approve and open saved history | Approval is a separate PostgreSQL transaction, never a model tool. Snapshot, idempotency result and audit commit together |
| 2:05–2:35 | Change preferences to 30 minutes, open old 20-minute plan, refresh page | The old snapshot stays immutable. Refresh reads durable history; it does not replay generation or approval |
| 2:35–3:10 | F5-D1 lost-response test result or controlled failure screenshot and trace | The test intercepts a successful response and explicitly retries the same key. The mobile error screenshot is an injected Save failure, not an arbitrary production incident. Show no secrets or private IDs |
| 3:10–3:45 | E9/E10 numerical evidence | 2/2/4 and 3/3/6 counted replay; earlier repair rejection remains a hard failure. Unknown charges remain held. Blinded practice packets and scripted dummy imports yield no genuine quality score |
| 3:45–4:10 | Evidence map and limitations | Point to concrete tests/recovery artifacts, distinguish software correctness from model/fitness benefit, and state the next provider/privacy/human approval boundaries |

For the injected recovery shot, use the existing automated browser harness and its
result/screenshots. The ordinary hands-on app does not intentionally lose responses.
Never manufacture a retry by deleting idempotency state, resetting a claim or
changing the approval key. A scripted session rating of 4 is test data, not a
person's satisfaction report. Do not present the E10 dummy mean as human feedback.

## Recording acceptance checklist

- Label the opening and evaluation shots “offline synthetic demonstration.”
- Capture actual UI actions; any cut or screenshot insert is identified.
- Keep expected output, automated scores and variant labels out of any purported
  blinded reviewer view. Use the numerical operator report for this walkthrough.
- Show no credentials, genuine cases, custody records, private paths or account UI.
- Retain the exact source manifest/image identity and date with the local draft.
- Owner reviews the recording, captions, visible tabs, audio, frame edges and
  disclosure before separately approving publication.
- Stop only the owned project and retain its volume; follow the existing recovery
  instructions rather than pruning or clearing data.

The F5-D1 desktop/mobile/error screenshots are suitable public synthetic examples
subject to final owner publication approval. No claim of public release approval,
accessible video captions or manual multi-browser acceptance is made by this guide.
