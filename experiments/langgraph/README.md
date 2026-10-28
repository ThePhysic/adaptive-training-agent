# Contained F2-03 LangGraph comparison

This separate environment is experimental infrastructure. The application does
not import it. Root dependency/source/evaluation provenance remains unchanged.
Only fixed synthetic scenarios may be persisted, under the ignored
`.cache/f203/` directory. No profile Save, candidate publication, approval,
history write, model SDK or hosted export is available to the graph.

## Design before installation

- Workflow: fixed synthetic context → provider reservation → fake model → bounded
  read-tool reservation/dispatch/result validation → optional synthetic interrupt
  → continuation → independent domain validation/one semantic repair → unpublished
  result. Reuse existing models, fake provider, budget/admission and read tools.
- Real local SQLite checkpoints use the official async saver. JSON-only state
  contains synthetic context, bounded messages/output, source versions, original
  deadline and accumulated budget, never real user input or application IDs.
  SQLite is an experiment file, not PostgreSQL business state or an app backend.
- Persist reservations before provider/tool calls. If a subsequent invocation finds
  a pending operation, charge its uncertainty and terminate rather than silently
  replaying it. A safe interrupted gate has no business effect before `interrupt`.
  Framework node retries are disabled; the graph alone owns one provider retry.
- Each active invocation uses existing process-wide admission and a deadline scope.
  Pausing releases admission; resumption reacquires it with the original deadline
  and counters. Downtime does not reset the 30-second allowance. Deadline expiry
  and stale source versions fail closed. Persist wall and monotonic start times,
  use the greater elapsed duration, and reject negative elapsed values. Same-machine,
  same-boot process restart only; no OS-reboot resumption claim. This is not an
  application resume API.
- One fixed thread per local experiment database; reject a second start. Completed
  reads are repeatable, but old checkpoint selection/time travel is not exposed.
  No general checkpoint upload/deserialization, arbitrary thread or graph input.
- Strict MessagePack deserialization, no pickle fallback; no credentials or raw
  checkpoint payloads in reports. Trusted local files only. Delete experiment files
  after tests/demos; no background retention worker. Counts and hashes may be
  recorded as review evidence. Files are bounded for this small fixed workflow,
  not a production retention/security mechanism.

## Dependencies checked 2026-10-24

Official PyPI lists stable LangGraph 1.2.17 (released October 24) and SQLite saver
3.1.2 (October 12), both requiring Python >=3.10. Resolution, `uv pip check`, 47
experimental tests and the restart demonstration passed with this project's
Python 3.14.9 and unchanged Pydantic 2.14.1. The separate `uv.lock` and `.venv`
contain 55 installed distributions, including transitive SDK/LangSmith packages;
no live adapter is supplied, tracing callbacks are disabled and invocation denies
network access. SQLite avoids another service and provides the required real
file-backed restart demonstration. Root lock/environment are unchanged.

Sources: [LangGraph package](https://pypi.org/project/langgraph/),
[SQLite saver package](https://pypi.org/project/langgraph-checkpoint-sqlite/),
[persistence](https://docs.langchain.com/oss/python/langgraph/persistence),
[interrupts and node restart rules](https://docs.langchain.com/oss/python/langgraph/interrupts).
An interrupt resumes using `Command(resume=...)`; its node starts again, so effects
before that call must be safe. The package documents strict MessagePack loading.

From repository root, after the separate frozen environment is acquired:

```powershell
experiments/langgraph/.venv/Scripts/python.exe -m pytest -c experiments/langgraph/pyproject.toml experiments/langgraph/tests -q
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py demo
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py compare
```

See the [runbook](../../docs/runbook.md#f2-03-isolated-langgraph-experiment) for
installation and explicit named cleanup. `demo`/`compare` remove their databases.
Manual checkpoints expire for execution after 30 seconds and require explicit
cleanup. No automatic deletion, secure erasure or arbitrary checkpoint upload.
The measured recommendation is to retain typed application orchestration.
Commands, raw evidence and tradeoffs: [F2-03 handoff](../../docs/implementation/f2-03-handoff.md).
No main-path adoption follows from this experiment; F2-04 remains separately authorized.
