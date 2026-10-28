# Offline Langfuse SDK exercise

Separate Python3.14 environment; application dependencies are unchanged. No
server, cloud account, real keys, provider or network exporter is required.
This process permanently seals sockets/DNS, inherited SDK/provider/OTel settings
and async SDK HTTP defaults. **Do not import it into the application or embed it
in a shared process.** It has no hosted activation option.

From this directory, after root dependencies are installed:

```powershell
uv sync --frozen --python ../../.venv/Scripts/python.exe
# From repository root first: .venv/Scripts/python.exe scripts/prepare_langfuse.py
$env:PYTHONPATH='../../src'
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe run.py
```

Use `.venv/bin/python` on Linux. Generated metadata and SDK capture stay under
ignored `.cache/f3-05a/`. The SDK score endpoint is a fixed MockTransport; spans
go to bounded memory. No UI/ingestion result or actual human/model judgment is
claimed. The SDK's private prompt-cache shutdown hook is intentionally pinned
and tested. Review any upgrade before running; never substitute a real exporter.

See [specification21](../../docs/planning/21-f3-langfuse-offline-integration.md)
and [handoff](../../docs/implementation/f3-05a-handoff.md) for privacy, bounds,
compatibility evidence and independent future hosted approvals.
