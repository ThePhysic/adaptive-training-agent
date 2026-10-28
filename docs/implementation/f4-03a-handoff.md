# F4-03A — Final offline cloud preflight and targeted readiness corrections

2026-10-25. **F4-03A only; ready for review, cloud execution still NO-GO.**
F4-02 was accepted offline. No AWS account access, account-connected plan,
backend initialization, apply/destroy, provisioning, cloud spend, live provider/
count request, hosted telemetry, external deployment/user data, positive financial
authority, commit or push occurred. F4-03B is not authorized by this report.

Starting HEAD: `f58eb5d5f7e6bf018030d4cb95b65f49a21a3493`. Local changes remain
unstaged/uncommitted. The [operator checklist](../planning/23-f4-03-cloud-execution-readiness.md)
is prepared for review; its unchecked decisions are not approved.

## Findings and corrections

| Item | Finding | Offline result / remaining gate |
| --- | --- | --- |
| SSM termination | Exact caller/target system tags agree with the documented tag shape. The published caller-prefix wildcard can also match another caller sharing that prefix. | Exact ownership retained, with14 structural context cases and explicit compatibility limitations. Actual AWS tag shape/effective IAM still unverified. |
| PostgreSQL IMDS | Host-network PG UID999 had no egress fence; app UID10001's rule did not cover it. Hop-one/IMDSv2 do not isolate a process in the same network namespace. | Fence both UIDs; force cloud PG to999 without capabilities/no-new-privileges. Native Linux/PG fixture demonstrates the old gap and corrected denial while SQL remains usable. |
| Bootstrap/EBS | One inline wait could outlast attachment; preparation was not restartable/idempotent. No persistent early daemon inhibition, complete-bundle marker or live pre-start volume check. | Persistent masks, atomic bundle/config, bounded boot preparation/recovery, format intent, exact mount checks and daemon pre-start gate. Deterministic faults/restarts pass. Actual EC2/cloud-init/systemd execution remains unverified. |

### SSM review: preserve ownership rather than broaden it

Official sources reviewed2026-10-25:
[AWS session ownership examples](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-restrict-access-examples.html),
[service authorization keys](https://docs.aws.amazon.com/service-authorization/latest/reference/list_ssm.html),
[IMDS process isolation guidance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-metadata-limiting-access.html).

AWS documents a system owner tag in `role-id:caller-specified-role-name` form and
illustrates `${aws:userid}*`. That prefix also accepts `operator-a-other` when
the caller is `operator-a`. Adopting it would weaken owner isolation. The existing
`StringEquals` condition is intentionally retained for the documented exact tag,
together with exact target ID and region/account-scoped session ARN. No claim is
made that every federation/configuration variant has been verified.

The new14-case fixture covers exact assumed-role and IAM-user IDs, another role
with the same session name, another session in the same role, two prefix collisions,
an undocumented suffix, absent/case-different tags, wrong target, account, region
and action. Native Terraform assertions bind those cases to the actual statement's
resource/action/condition expressions. A separate Python regression demonstrates
the wildcard collision. These are **structural/string-constraint tests, not an AWS
IAM evaluator, IAM simulation API or actual authorization outcome**.

Only the documented exact owner-tag shape is supported. A real suffix/transformed
tag must fail closed and trigger source review; it must not silently grant prefix
access. The future operator must privately verify actual tags and have a separately
approved recovery identity able to terminate the exact returned session ARN if
routine termination fails. This compatibility gate remains before cloud closure.
No username-derived session ARN or fabricated real-session evidence is used.

The two SSM documents, resource scopes, required document-access check, regional
message-gateway exception and denial of arbitrary shell/remote-host forwarding
remain. The fixed operate document adds only `prepare`, alongside start/stop/
verify/backup. It accepts no command fragments. No restore/delete authority added.

### PostgreSQL and process isolation

The cached approved PostgreSQL18.6 bookworm image reports postgres UID/GID999.
Both999 and10001 now have IPv4 non-loopback rejection and IPv6 rejection. The
existing app fence is preserved, with no flush/delete. Cloud-only Compose overrides
force PG999 even during initialization, drop every capability and set
no-new-privileges, preventing a database child from switching to an unfenced UID.
Verification checks both container configurations. The accepted local Compose and
application image are unchanged. A different image/volume ownership fails startup
rather than reverting to root initialization.

Launch/backup also reject a daemon with an unexpected data-root, rootless mode or
user-namespace remapping: the tested kernel UID mapping must hold. The approved
AMI must have Docker/service socket already masked before cloud-init; user-data
cannot retrospectively prevent a daemon that the AMI started earlier. Host root/
SSM administrators remain trusted. Real AMI/UID/kernel behavior needs the future
account drill; this is not host-compromise protection or production authentication.

The actual fixture shares an isolated Docker `--network none` namespace between
a control process and PostgreSQL. Fake link-local IPv4/IPv6 listeners substitute
for IMDS. Its SQL `COPY TO PROGRAM` is a **test-only** superuser probe, never an
application/LLM tool. No actual EC2 endpoint, token or role credential is contacted.

| Probe | Prior app-only fence | Corrected fence |
| --- | --- | --- |
| UID10001 → synthetic IPv4/IPv6 metadata | Denied / denied | Denied / denied |
| UID999 → synthetic IPv4/IPv6 metadata | Reachable / reachable | Denied / denied |
| Actual PG backend/program → synthetic metadata | TCP connected | Connection rejected |
| UID0 control → both metadata listeners | Reachable | Reachable |
| IPv4 loopback HTTP for all3 UIDs | Passed | Passed |
| PG backend UID and loopback SQL |999 / passed |999 / passed |

[Native evidence](evidence/f4-03a-network.json). The fixture also uses two child
processes and actual Linux flock: the second first proves nonblocking acquisition
is rejected, then enters only after the first releases the host preparation lock.
Children are awaited/cleaned up; no timing-based race assertion. Host firewall and
development database were never touched. Fixture PG data exists only in tmpfs;
the script removes only its uniquely named containers.

### Preparation, interruptions and recovery

- Bootstrap masks/stops and disables Docker/service socket before file writes.
  Helper/config/Compose replacements are atomic; a bundle manifest is committed
  last. Partial/mismatched bundles cannot prepare, launch or verify storage.
- `fata-prepare.service` is an enabled,240-second oneshot with no restart loop.
  It makes one bounded attempt at boot and can be explicitly restarted through
  the fixed `prepare` operation. It waits180 seconds for the exact Nitro volume ID.
  No queue, worker or automatic application start is added.
- Preparation is serialized by flock and requires an inactive Docker daemon.
  The recovery operation first stops the owned release/daemon/socket, masks them
  and restarts the same service. Preparation keeps Docker masked on failure.
- Only a writable whole disk with no recognized signatures may be initialized.
  A format-intent record is written before non-forced mkfs, whose stdin is closed.
  Recognized ext4 is always reused; unknown signatures are rejected. After an
  interrupted format, a complete ext4 result can be reused. An ambiguous still-blank
  result cannot be formatted again automatically: retain it for inspection or
  explicitly approve a fresh volume. The intent is never blindly cleared.
- Exact mount source, UUID, filesystem and configured volume ID are checked.
  Repeated preparation recognizes the existing mount and preserves one fstab
  entry. `nofail`/device timeout allow host recovery without granting Docker a root-
  directory fallback. Config/storage records are atomic and reused on restart.
- Docker depends on guard/preparation/mount and has an independent `ExecStartPre`
  mount check. Launch, backup and verification repeat the check; no pull/daemon
  use is allowed by launch on an unverified mount. Unmasking happens only at the
  end of successful preparation, without starting Docker or the app.
- The rendered shell is normalized to LF even from Windows checkouts. Terraform
  checks its shebang/newlines and compressed16KiB bound. Tool versions, SSM patch
  floor, Terraform/provider versions and image pinning remain unchanged.

Tests inject delayed attachment, timeout then fresh runtime, blank/ext4/GPT disks,
process exit before/after mkfs, failures at three atomic write stages, partial
bundles, repeated preparation, already-mounted storage, wrong source/UUID/volume,
lost mount and active daemon. They simulate system commands/filesystems and clocks;
**they do not execute systemd, cloud-init, real EBS formatting or EC2 restart**.
File fsync/rename and initialization intent are not an arbitrary power-loss or
damaged-filesystem recovery guarantee. Incomplete unit installation needs the exact
reviewed bootstrap repaired by an approved recovery identity, or instance
replacement retaining data. No authorization guard is relaxed for recovery.

## Files changed

| Files | Change |
| --- | --- |
| `infra/aws/host/host.py` | Both UID fences, atomic bundle/storage preparation, safe retry/format intent, mount/daemon checks, fixed recovery operation and PG inspection |
| `infra/aws/deployment/{bootstrap.sh.tftpl,main.tf}` | Early masks, atomic complete bundle, boot preparation unit, LF-normalized gzip shell |
| `infra/aws/deployment/iam.tf` | Explain strict owner matching; add only fixed preparation operation |
| `infra/aws/deployment/tests/{safety.tftest.hcl,termination-cases.json}` |14 ownership contexts, exact allowed operations and bootstrap assertions |
| `tests/{test_infrastructure,test_host_preflight}.py` | Update previous3 storage cases for new model;53 combined deterministic host/security cases |
| `infra/aws/fixtures/{Dockerfile.network,network_probe.py}`, `scripts/check_host_network.py` | Opt-in isolated Linux firewall/PG/flock proof; no host-network test mutation |
| `infra/aws/README.md`, checklist23, root README/development/runbook status | Current recovery procedure, evidence boundaries and F4-03B decisions |
| `docs/implementation/evidence/f4-03a-*.json`, this report | Commands/results, native network proof, fixture versions and unchanged-cost inventory |

No migrations or resource kinds/allocations were added. Application source,
domain/catalog/validator, APIs/SSE, immutable approvals/completions, financial/live
provider barriers, original40/150 evaluation results, frontend, main/experimental
locks, local Docker image/Compose and historical handoffs remain unchanged.

## Commands, versions and observed outcomes

Windows11, Python3.14.9, Node24.22.1/npm11.19.1/Ruff0.17.2; existing Docker29.9.1,
Terraform1.17.0/hashicorp-aws6.70.0 and unchanged signed Windows/Linux locks.
Only a test image's public Debian packages were acquired: iptables1.8.9-2 and
iproute2 6.1.0-3. The pinned Python base, fixture image ID and syntax result are in
[fixture evidence](evidence/f4-03a-fixture.json). No main dependency installation.

Executed from repository root:

```powershell
docker build --provenance=false --sbom=false -f infra/aws/fixtures/Dockerfile.network -t fata-f403a-network .
.venv/Scripts/python.exe scripts/check_host_network.py
.tools/terraform/terraform.exe fmt -recursive infra/aws
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe
.venv/Scripts/python.exe -m pytest tests/test_infrastructure.py tests/test_host_preflight.py -q --basetemp=.cache/pytest-f403a-preflight-final
.venv/Scripts/python.exe scripts/check.py
.venv/Scripts/ruff.exe check src scripts tests infra/aws --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests infra/aws
```

The final network-none Terraform repetition reused the F4-02 read-only Linux
CLI/provider mirror, accepted local release image and `infra/aws/offline_container.py`;
exact Docker flags are in the infra README, with only the owned container name
and `.cache/f4-03a/` result destination changed. No backend initialization or
real plan/apply was used. The bootstrap template also passed cached PostgreSQL
image `bash -n` with networking disabled. Early target runs preceded the four
daemon-option cases; the final full suite includes all53 target cases.

Initial cloud-preflight checks, before the subsequently authorized CI correction:

| Check | Observed result |
| --- | --- |
| Terraform format/security/schema | Passed; all3 roots valid; unchanged23 resource blocks |
| Windows native mock plans | **8/8 passed**, zero failed/errored/skipped, including the14 structural ownership contexts |
| Linux network-none repeat | Same3 roots and **8/8 passed**, cached providers only |
| Offline application sequence | **20/20 commands exit0;1,038 routine Python cases passed**, zero failures/skips;257 integration deselected |
| Target host/security population | **53** cases included in that routine total; deterministic command/file fault simulations |
| Frontend | **85 tests**, type/format/generated checks and build pass; no UI change |
| Strict contracts/provider/count/model assets | All checks passed; original provider safeguards remain |
| Frozen40 | **24/24 development +16/16 held-out**, no changed corpus/results |
| Offline model suite |150 safe dispositions unchanged; template hard50/50, fake/replay44/50 each; deliberate failures remain visible |
| Native Linux fixture | Both protocols/UIDs, preserved loopback SQL and real flock barrier passed; owned containers removed |
| Source/lock/financial/privacy integrity | Protected files and existing evidence unchanged; ordinary host output remains classified metadata; no credentials or payloads in shared measurements |

[Windows TF](evidence/f4-03a-terraform-windows.json),
[Linux TF](evidence/f4-03a-terraform-linux.json),
[application commands/timings](evidence/f4-03a-application-checks.json).
Eight scenarios repeated on two platforms are not16 independent AWS trials.
Fourteen IAM contexts are not real authorization calls. Native network/PG proof
is separate from the command simulations. At this stage, full257 application
integration/browser, historical release/restore/load and isolated SDK/graph suites
were not rerun: their implementations are untouched. The later CI addendum below
records the additional release/restore run. No new hosted CI or AWS runtime claim.

Early checks exposed a Windows-only path expectation in a daemon test; comparing
POSIX paths corrected it. Initial shell inspection had native Windows quoting
limitations; the substantive fixture uses structured subprocess argument arrays.
Final checks pass. No permission escalation remains unresolved and no host firewall
rule or cloud operation was attempted.

## Costs, remaining assumptions and handoff

[Inventory recheck](evidence/f4-03a-cost-verification.json) confirms23 resource
blocks before/after, no extra service/allocated storage/networking, unchanged
estimated **$1.55866** under F4-02 assumptions, and authorized cloud spend **$0**.
New units execute on the same proposed host; the fixture exists only locally.
Failed preparation or expiry is not a billing cap; an attended operator must stop
the instance and audit retained volumes/images/state/backups. No actual bill exists.

Remaining account gates: approved account/role/MFA and effective IAM/SCP checks;
real session tags/emergency exact-session termination; masked, patched, reviewed
AMI/tool manifest and UID mapping; image provenance/digests; exact region/AZ/window;
real plan inventory and numerical budget; state locking/recovery; actual cloud-init/
systemd/EBS timing; mount/firewall/reboot/expiry proof; synthetic S3 restore and
private retention/deletion; emergency stop and explicit teardown inventory.

The [F4-03B checklist](../planning/23-f4-03-cloud-execution-readiness.md) contains
these owner decisions and the unchanged backup/rollback requirements. F4-03A
does not approve any of them. Live OpenAI/counting, hosted Langfuse, real-user data
and provider financial authority remain independently blocked. Stop for review.

## Additional authorization: hosted-CI release-drill correction

The owner additionally authorized this narrow correction within F4-03A. No hosted
run was triggered, code committed/pushed, or AWS/provider access enabled.

### Investigation and evidence limits

Read-only `gh run list` and `gh run view --log` inspected the two actual failures:

| Run | Successful integration/cleanup | Subsequent failure |
| --- | --- | --- |
| [F4-02:40245078312](https://github.com/ThePhysic/future-adaptive-training-agent/actions/runs/40245078312) |257 integration cases; PG reported Stopped at23:32:56.150 UTC | EADDRINUSE98 at23:33:07.894,11.744 seconds later |
| [F4-01:40241677865](https://github.com/ThePhysic/future-adaptive-training-agent/actions/runs/40241677865) |257 integration cases; PG reported Stopped at22:48:10.505 UTC | EADDRINUSE98 at22:48:21.823,11.318 seconds later |

Both are2026-10-25. Their images finished building before the failure. The old
loop logged neither its current port nor socket/process/container diagnostics.
**The historical hosted conflicting port and PID cannot be proven from these
logs.** The likely conflict is55432: development Compose publishes that port to
the integration database, and successful listener shutdown does not remove Linux
TCP close-state sockets. There is no evidence that Docker left a live proxy or
that an unrelated process should be killed.8000 remains a separately checked
possible conflict. [Bounded hosted-log summary](evidence/f4-03a-ci-hosted-log-review.json).

The native Linux reproduction establishes the actual conflicting port locally.
It runs the accepted PG18.6 image and a control process in one isolated network-
none namespace, using tmpfs data and **no host ports, volumes or firewall changes**.
The normal PostgreSQL wire protocol explicitly waits for server FIN after
Terminate, giving a reproducible server-side close. After Docker reports the
PG container stopped, `ss` reports only:

```text
TIME-WAIT 0 0 127.0.0.1:55432 127.0.0.1:45408
```

`/proc/net/tcp` confirms TIME_WAIT06 and no LISTEN0A. The original strict bind
accepts8000 but fails on55432 with errno98. Before stopping, Docker process
inspection identifies actual PostgreSQL processes and `ss` identifies the55432
listener; afterward this is a kernel TIME_WAIT socket with no live owner PID.
The corrected check waits **59.115 seconds**, then both strict binds succeed.
A second negative test installs a real8000 listener, verifies refusal at the
deadline and proves that listener remains listening. This is a local explanation
consistent with the hosted timing, not retrospective proof of the hosted owner.
[Native socket/process evidence](evidence/f4-03a-ci-port-handoff.json).

### Minimal correction and safety

- `scripts/check_release.py`: bounded75-second monotonic wait for the same plain
  exclusive bind checks. Retry only EADDRINUSE, report each conflicting port,
  retain both probes until the pair passes, release partial probes before waiting,
  and fail with the exact port at the deadline. Other errors fail immediately.
  No SO_REUSEADDR/SO_REUSEPORT, occupied-port bypass, process termination or
  filesystem/container cleanup occurs in this preflight. The later Docker bind
  still fails if a process wins the unavoidable bind handoff.
- `.github/workflows/offline.yml`: keep `if: always()` cleanup; explicitly stop
  only the workflow project's `postgres` with30-second timeout, then
  `docker compose rm --force postgres` removes that **stopped service container**.
  Here `--force` skips the removal prompt; no `--stop`, volume flag, prune or
  unrelated container removal is used. Log filtered `ss` and Compose status before/
  after cleanup, and filtered sockets/container ports if the release drill fails.
- `tests/test_release.py`: five new cases cover delayed release of either port,
  persistent occupation of either port, immediate permission failure, exact error
  metadata, released probe descriptors and no address reuse/owner cleanup.
- `scripts/check_release_port_handoff.py`: opt-in real Linux regression above,
  using only acknowledged, uniquely named fixture containers and cached images.
  Cached fixture prerequisites are built by the command earlier in this report.
- `docs/local-release.md`: bounded wait, Linux diagnostics and owned-service-only
  recovery guidance. No application, image, schema, dependency or CI job change.

The same stop/remove commands were exercised against an actual uniquely scoped
development Compose project with the real127.0.0.1:55432 binding. Its container
was removed, its named volume remains, and no unrelated container was touched.
The network was then removed with scoped `compose down`, without `--volumes`.
[Cleanup evidence](evidence/f4-03a-ci-cleanup.json). This retention test and the
isolated Linux close-state test are separate evidence, not a hosted runner trial.

Linux close-state reference: [socket(7)](https://man7.org/linux/man-pages/man7/socket.7.html)
and [Python socket guidance](https://docs.python.org/3.14/library/socket.html#example).
Address reuse from that guidance was deliberately not adopted: the strict bind
precondition remains. A kernel/owner retaining a port beyond75 seconds still
fails closed; this wait is not a universal guarantee of port availability.

### Commands and final observed results

```powershell
gh run list --repo ThePhysic/future-adaptive-training-agent --limit 5 --json databaseId,conclusion,headSha,createdAt,url,name
gh run view 40245078312 --repo ThePhysic/future-adaptive-training-agent --log
gh run view 40241677865 --repo ThePhysic/future-adaptive-training-agent --log
.venv/Scripts/python.exe scripts/check_release_port_handoff.py
.venv/Scripts/python.exe .cache/f4-03a/check_ci_cleanup.py
.venv/Scripts/python.exe -m pytest tests/test_release.py -q --basetemp=.cache/pytest-f403a-ci-port
.venv/Scripts/python.exe scripts/check_release.py
.venv/Scripts/python.exe scripts/check.py
.venv/Scripts/ruff.exe check src scripts tests infra/aws --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests infra/aws --no-cache
git diff --check
```

The ignored cleanup helper runs structured subprocess arguments for exactly
`docker compose -f compose.yaml -p fata-ci-cleanup-<nonce> up -d --wait --pull never postgres`,
`stop --timeout 30 postgres`, `rm --force postgres`, `ps --all --quiet`, volume
inspection, then scoped `down`. It asserts an empty service list and the same
existing volume. No volume deletion. Native fixture source is reproducible above;
raw downloaded hosted logs and private backup/state remain ignored.

| Final correction check | Observed outcome |
| --- | --- |
| Native Linux/PG socket handoff | Original55432 errno98 reproduced; corrected strict binds pass after59.115s; live8000 listener refused and preserved |
| Compose cleanup | Owned stopped container removed; `fata-ci-cleanup-0ba98042_training_pg` retained |
| Target release tests | **10/10 passed**; five new cases are also included in the total below |
| Final shared offline sequence | **20/20 commands exit0;1,043 Python cases passed**, zero failures/errors/skips;257 integration cases deselected |
| Frontend/contracts/evaluation |85 frontend tests, build/type/format/generated checks pass; frozen40/40 and150 model-suite dispositions unchanged |
| Full local Docker release/restore drill | Exit0 with existing accepted images; real HTTP/SQL and120 fake generations, zero load errors; restart, database interruption/recovery, restore, immutable readback and key retries pass |
| Release migration/rollback | Nine migrations; changed checksum rejected; same-schema rollback/forward and one row each in plan/approval-key/audit/session/completion-key verified |
| Ruff/format/diff | Passed;142 Python files formatted; protected application/contracts/data/migrations/web/locks unchanged |
| Hosted corrected workflow | **Not run**; requires a future owner-controlled GitHub Actions run after separately authorized source publication |

[Final20-command results](evidence/f4-03a-ci-application-checks.json),
[bounded release/fault measurements](evidence/f4-03a-ci-release-drill.json).
Full release run: `fata-f401-345fd061-{source,restore}`; its containers were
stopped/removed, volumes and synthetic binary backup retained for review. The
120 fake-only load requests used4 warm-ups and concurrency1/2 (60 requests each):
p50/p95 **48.28/93.85ms** and **67.92/117.20ms**, respectively. These are local
operational observations, with no real-model or AWS performance implication.

The first sandboxed shared check stopped at frontend esbuild `spawn EPERM`.
The permitted outside-sandbox run completed all20 commands; PowerShell treated
esbuild's normal stderr build summary as a wrapper error. The final run captures
combined child output directly and confirms process exit0. The recorded final
results belong to that completed run. No tests were weakened to accommodate it.

No new image builds or dependencies were needed for this correction. No native
AWS tests, full257-case integration/browser repetition or hosted Actions execution
is claimed. The real local Docker drill supplies additional PostgreSQL/recovery
evidence independently. Original cloud-preflight8/8 mock plans on both platforms
remain applicable; no Terraform changes were introduced by this addendum.
Costs and every cloud/provider restriction above remain unchanged. **Stop for
F4-03A review; cloud execution and all subsequent work units remain unauthorized.**
