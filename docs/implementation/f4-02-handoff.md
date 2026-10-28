# F4-02 — Offline Terraform infrastructure and AWS deployment preparation

Date: 2026-10-25. **F4-02 only; ready for owner review, cloud execution NO-GO.**
F4-01 was accepted. No AWS account access, resource creation/change, account-
connected plan, remote-state initialization, Terraform apply/destroy, ECR push,
cloud spend, provider/count request, hosted telemetry, real-user data, commit or
push occurred. Completion does not authorize F4-03. Only public documentation,
CLI/provider acquisition and local offline validation were used.

## Implementation and files

| Paths | Result |
| --- | --- |
| `infra/aws/deployment/{versions,variables,main,iam}.tf` | us-east-1 t3.small, VPC/subnet/IGW/route, zero-inbound SG, outbound TLS, IMDS settings, standard credits, instance IAM/profile, encrypted storage, ECR mirrors and bounded SSM documents/policy |
| `infra/aws/deployment/bootstrap.sh.tftpl`, `infra/aws/host/host.py` | Compressed configuration bootstrap; reviewed tool attestation; explicit-volume mount; app-UID egress fence before Docker; fixed start/stop/verify/backup operations and expiry shutdown |
| `infra/aws/state-bootstrap/main.tf`, `infra/aws/modules/protected-bucket/main.tf` | Separate state bootstrap; reusable encrypted/versioned/public-blocked/TLS-only buckets; native S3 lock permissions and explicit deletion protection |
| Three `.terraform.lock.hcl` files | Exact AWS6.70.0 selection, authenticated archive hashes and Windows/Linux h1 checksums |
| Three `tests/safety.tftest.hcl` files | Seven mock-provider, explicit plan-only native tests; no apply even in the mock harness |
| `infra/aws/deployment/{backend.hcl,terraform.tfvars}.example` | Non-activating fake placeholders; no real account/AMI/image/window or credentials |
| `scripts/check_infrastructure.py`, `infra/aws/offline_container.py` | Static safety checks, sanitized environment, native validation/mock tests and independent Docker-network-none repetition |
| `tests/test_infrastructure.py` | 29 offline policy mutations, credential/environment, firewall, expiry, tool-version, disk and failure-cleanup cases |
| `.gitignore` | Ignore private Terraform state/plans/backend/tfvars/workdirs while retaining provider locks and AGENTS.md exclusion |
| `infra/aws/README.md` | Reviewed state, IAM, AMI/image, deployment, recovery, rollback and teardown specification |
| `docs/planning/23-f4-03-cloud-execution-readiness.md` | Exact remaining source/account/IAM/privacy/cost/access/recovery/deletion approval gates |
| Root `README.md`, `docs/{development,runbook,local-release}.md`, document22 pointer | Current status and navigation; original F4-01 comparison retained |
| `docs/implementation/evidence/f4-02-*.json`, this handoff | Versions/hashes, two-platform TF results, application checks, packaging and revised cost arithmetic |

Starting HEAD `036dfb35f0b5dd1a265015315fe78e279a821490`. Changes remain uncommitted.
**No application source, schemas, contracts, database migrations, provider/financial
gates, dependency locks, frontend code, existing release image/Compose, historical
acceptance records or evaluation assets were modified.** The original40 cases
and all150 model-suite dispositions remain unchanged. No new evaluation platform,
service, queue, cache, production LangGraph or live authority.

## Infrastructure decisions and limits

One deployment root and one separately initialized state-bootstrap root share a
small protected-bucket module. There are23 declared resource blocks; for the
configured deployment their count/for_each expansion includes24 resource instances,
plus6 for separate state bootstrap. No NAT, RDS, ECS, ALB, public application
listener, SSH key, hosted logging, secret, customer KMS key or scheduled snapshot.
One public IPv4 is for host outbound SSM/ECR/S3 HTTPS only. DNS uses VPC facilities;
the SG allows no public inbound traffic. Root t3 credits are standard, not unlimited.

The encrypted8GB root is disposable; the encrypted32GB data volume is independent
and protected against accidental destruction. Docker's data-root and PostgreSQL
volume reside there. Force detach is disabled, attachment removal stops the host,
and actual disk selection uses the specified Nitro volume ID/UUID. Blank disks
alone may be formatted; unknown signatures are rejected. Actual cloud device/
AMI behavior is not established by filesystem fakes.

IMDSv2/hop-one/disabled IPv6 metadata are supplemented by UID10001 owner firewall
rules: IPv4 permits loopback only and IPv6 is rejected. They run/check before
Docker, persist via ordered systemd units and are checked on start/verify. App
remains non-root/read-only/capability-free and receives no credential/host mount.
Host root and SSM administrator remain trusted. This is not production auth or
proof against a compromised host/database administrator.

The reviewed AMI must already contain compatible Docker/Compose/AWS CLI/SSM/
Python/system tools and no Docker state/credentials. Bootstrap installs no packages
or unpinned script. Exact tool-version stdout is checked against a mandatory
manifest SHA-256, with **SSM>=3.3.4851.0** additionally required. AMI source,
architecture, patching and provenance still need owner selection/review. There
is no fabricated active AMI ID. Bootstrap prepares the host, then the operator
must publish/verify both image digests and explicitly Start. It does not start
the app on infrastructure creation alone.

Instance role permits heartbeat on its exact generated EC2 ARN, four minimum
message-gateway actions, ECR login plus pull on two exact repositories, and S3
read/write confined to this backup prefix. Message gateway and ECR authorization
token actions require wildcard resources; no IAM/admin/cloud-delete permissions.
Heartbeat policy follows instance creation, avoiding a dependency cycle; initial
SSM registration/IAM propagation remains a future compatibility check.

Operator policy is an **unattached output**, not an account modification. It
allows StartSession on only this instance/two documents, requires document-access
checking, reads those documents and terminates sessions using exact AWS system
caller/target tags (federated-safe). Regional OpenDataChannel is the narrowly
named required exception with resource `*`, because AWS message gateway exposes
no resource ARN scoping. No shell/remote-host forwarding/SendCommand/ResumeSession/
IAM/PassRole is granted. Real effective permissions and negative authorization
checks remain prerequisites; offline tests cannot emulate AWS IAM evaluation.

The custom Port document fixes both ends to8000; the command document permits
only start/stop/verify/backup. No prompts, owner input or command fragments are
passed to a generic shell. Routine operations cannot restore or delete data;
a separately reviewed recovery/deletion identity/procedure is required.

State uses SSE-S3/versioning/TLS/public blocks and the native `.tflock` mechanism,
not DynamoDB. State writer can read/write only the selected key and delete only
its lock. Dedicated bucket listing is permitted; version recovery/deletion is
separate. Bootstrap state remains local on encrypted operator storage until its
separately approved lifecycle is established. Backend initialization was disabled
for every validation; no state bucket was created or contacted.

## Versions, sources and acquisition

Local Windows11, Python3.14.9, existing Node24.22.1/npm11.19.1/Ruff0.17.2; Linux
repeat in accepted F4-01 image on Docker29.9.1/Compose5.6.0. No root application
SDK/package install or lock change.

Checked official sources2026-10-25: [Terraform1.17.0 release](https://releases.hashicorp.com/terraform/1.17.0/),
[AWS6.70.0 registry](https://registry.terraform.io/providers/hashicorp/aws/6.70.0),
[S3 backend and lock IAM](https://developer.hashicorp.com/terraform/language/backend/s3),
[mock provider semantics](https://developer.hashicorp.com/terraform/language/tests/mocking),
[AWS session schemas](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-schema.html),
[SSM minimal instance role](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-create-iam-instance-profile.html),
[session caller/target policies](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-restrict-access-examples.html),
[message-gateway resource restrictions](https://docs.aws.amazon.com/service-authorization/latest/reference/list_ssmmessages.html),
[IMDS firewall](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-metadata-limiting-access.html)
and [SSM security bulletin2026-107](https://aws.amazon.com/security/security-bulletins/2026-107-aws/).
AWS provider6.70.0 was published2026-10-22T01:11:12Z. No third-party module/service.

CLI archives were SHA-256 checked against the official published sums: Windows
`2948dd7f77dec0f562ec29000103e0441d915be5e5f1a02c1ce23681951cfb19`, Linux
`c168cab7c637a8769fdb90089ddd19de701bc6ff8aca64dc2e2185fe46f59f67`.
Provider acquisition reported **signed by HashiCorp**. Linux checksum was added
using `providers lock -platform=linux_amd64` and the exact generated selection
copied to identical-requirement roots; no provider hash was hand-invented.
[Dependency evidence](evidence/f4-02-dependencies.json) captures lock hashes.

## Exact checks and observed results

PowerShell from root, acquired CLI under `.tools/terraform`:

```powershell
$env:CHECKPOINT_DISABLE='1'
$env:AWS_EC2_METADATA_DISABLED='true'
.tools/terraform/terraform.exe -chdir=infra/aws/deployment init -backend=false -input=false
.tools/terraform/terraform.exe -chdir=infra/aws/state-bootstrap init -backend=false -input=false
.tools/terraform/terraform.exe -chdir=infra/aws/modules/protected-bucket init -backend=false -input=false
.tools/terraform/terraform.exe -chdir=infra/aws/deployment providers mirror -platform=linux_amd64 ../../../.cache/f4-02/provider-mirror
.tools/terraform/terraform.exe -chdir=infra/aws/deployment providers lock -platform=linux_amd64
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe
.venv/Scripts/python.exe scripts/check.py
.venv/Scripts/ruff.exe check src scripts tests infra/aws --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests infra/aws
```

The checker clears inherited AWS credentials/config, TF_VAR/CLI argument injection
and TF_LOG values, disables checkpoint/metadata access and permits no install or
real plan command. Acquisition was a separate public-registry operation. Exact
network-none Docker invocation is in [operations spec](../portfolio-readiness.md) (curated release-readiness substitute; original infrastructure reference omitted).

| Population/check | Observed outcome |
| --- | --- |
| Terraform recursive format | Passed |
| Windows3 native validate roots |3/3 valid, no warnings/errors |
| Windows native mock tests | **7/7 passed**, no skipped/failed/errored;4 deployment,1 state,2 bucket |
| Linux network-none validation/mock repetition | Same3 roots and **7/7 passed**; read-only source/mirror, disposable executable tmpfs, no network interface to AWS |
| Static guard |6 HCL sources/23 resource blocks/3 test files; no remote data/module/provisioner or credential inputs |
| Python offline application checker | **20/20 commands exit0**, **1,014 routine tests passed**,257 integration deselected, no skipped/errors |
| New host/security tests | **29** included in that routine denominator; no real systemd/disk/firewall/AWS command |
| Frontend | **85 tests passed**, TypeScript/generated contracts/format/build pass; no UI code change |
| Schema/provider/count/evaluation contract checks | All passed; OpenAPI/generated TS/Responses/count fixtures unchanged |
| Frozen baseline | **24/24 development +16/16 held-out**, no modified corpus/results |
| Offline model suite | All150 safe dispositions unchanged; template hard50/50, fake/replay44/50 each; deliberate failures visible, no real-model/human claims |
| Existing async comparison |5 sequential +5 concurrent fake trials correct,3 reads/trial, zero retries; not a new cloud performance measurement |
| Packaging | Existing reviewed image unchanged; unchanged Compose and digest override resolve to host networking/loopback, non-root/read-only/no ports/credential mounts |
| Whitespace/protected-file/ignore audit | No app/SQL/contracts/locks/frozen evidence drift; AGENTS.md ignored, no active state/plan inputs tracked |

[Windows Terraform](evidence/f4-02-terraform-windows.json),
[Linux network-none](evidence/f4-02-terraform-linux.json),
[application commands/timings](evidence/f4-02-application-checks.json),
[packaging evidence](evidence/f4-02-packaging.json). Seven scenarios repeated on
two platforms are not14 independent AWS tests. Application tests include the
existing reference models; these do not become native SQL evidence.

No application/SQL/frontend behavior changed. Native PostgreSQL257, browser,
isolated Langfuse16/LangGraph47 and full restore/load drill were **not rerun** in
F4-02; their accepted F4-01/F3/F2 evidence remains historical. No new PostgreSQL
correctness, AWS performance, actual IAM or hosted CI claim. Existing GitHub
workflow was not triggered or changed; the infra check is explicitly opt-in so
routine app tests do not install a Terraform/provider dependency.

Initial test corrections: mock-plan assertions used set/object-safe expressions
and explicit computed IDs; no mock apply was substituted. Windows temp permissions
required normal local execution. A fake Linux-path remapping bug was corrected
before29/29 passed. The first container attempt used slow Windows-backed work
storage and was stopped after verifying task ownership; tmpfs required `exec` for
test binaries. Missing Linux h1 then failed checksum verification; adding the
authenticated cross-platform lock resolved it. These failures did not bypass
checks or contact AWS. Automatic review rejected an earlier unverified hard-coded
PowerShell stop; the stalled pytest was instead identified by its exact command
line before stopping. No permission request remains unresolved.

## Recovery, costs and readiness

Backup uses app quiescence, full binary PostgreSQL dump, max1GiB accepted archive,
SSE-S3/checksum upload under a unique prefix and a private local receipt. No raw
content, credentials, exceptions or receipt IDs are printed into normal logs.
It leaves app stopped on failure; no automatic replay/restart/deletion. Existing
F4-01 fresh-target restore verification is the reference; cloud restore is not
performed. There is no automatic scheduler/PITR or clinical/production guarantee.

Current backups expire after7 days and noncurrent versions7 days later; lifecycle
is asynchronous. State has no automatic expiry. Data/ECR/buckets have explicit
deletion guards. Safe teardown requires exact resource/version inventory and
reviewed release of guards, not force_destroy/state removal. Instance expiration
is an OS stop attempt, not a guaranteed financial cap; retained storage keeps
accruing charges. SSM encrypted forwarding is not end-to-end browser HTTPS.

Using the same dated official rates/workload as document22, actual design
allowance is **$1.55866** (24h plus stated retained artifacts), versus F4-01's
$1.11930 comparison assumption. Retained32GB data, mirrored PG image, potential
14-day backup window and AMI prerequisite are accounted for; unused hosted
logs/secrets/alarms/snapshot resources are excluded. No cloud cost was incurred.
[Arithmetic](evidence/f4-02-costs.json) and [checklist23](../planning/23-f4-03-cloud-execution-readiness.md)
explain idle/teardown costs, privacy/retention and separate numerical approval.

Offline scope is ready for review. Actual account IAM/SCPs, AMI/tool/image
selection/publication, SSM document/data-channel behavior, heartbeat propagation,
root/volume boot compatibility, firewall/reboot/expiry, state lock/recovery and
cloud backup/restore/teardown remain **unverified**. Before any real operation,
the owner must authorize its work unit, account/roles/region, exact reviewed source
and plan, privacy/data destinations, numerical spending/window/stop conditions and
retention/deletion. No active provider grant or live-access gate changed. Stop
after F4-02; no F4-03, live model, hosted Langfuse or cloud execution is authorized.
