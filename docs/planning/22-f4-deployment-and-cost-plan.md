# F4-01 AWS deployment and cost proposal

F4-02 implementation follow-up: [offline Terraform and operations](../portfolio-readiness.md) (curated release-readiness substitute; original infrastructure reference omitted)
and [cloud-execution checklist23](23-f4-03-cloud-execution-readiness.md) describe
the concrete retained-disk/ECR/state design and revised cost arithmetic. The
original F4-01 comparison below is preserved; neither grants cloud spending.

Prepared 2026-10-25. **Design only; authorized cloud spend $0. No Terraform apply,
AWS account operations or deployment performed.** F4-02 requires separate work-unit
authorization; provisioning additionally requires a numerical budget and execution
approval. This does not lift provider, counting, Langfuse or external-user gates.

## Requirements and fixed assumptions

Proposed region: **us-east-1, Northern Virginia**. One operator, synthetic adult
data, fake model, single process, at most two simultaneous generations. A demo
lasts 24 hours, with 1,000 API requests/day including 100 fake generations, 2 GB
gross internet response traffic and 0.1 GB metadata logs. Keep one conservatively
sized 1 GB image, 1 GB logical backup and 10 GB changed snapshot blocks for seven
days. No real model costs, hosted tracing or public participant access are in this
proposal. 730 hours/month is a comparison convention, not an AWS billing rule.

Proposed recovery objectives: quiesced daily backup, **RPO <=24 hours**, manual
restore **RTO <=1 hour** during an attended demo. These are future cloud acceptance
targets, not measured AWS guarantees. Local dump/restore command timings do not
measure cloud RTO. No availability SLA or multi-AZ failover claim.

## Two topology choices

| | A: short-lived single host (recommended) | B: Fargate/RDS/ALB (conditional future option) |
| --- | --- | --- |
| Compute | EC2 t3.small, Linux x86, 2 vCPU/2 GiB, standard CPU credits | One Linux x86 task, 0.5 vCPU/1 GiB |
| Application | Existing app and PostgreSQL containers, host loopback only | One task; different reviewed network/auth configuration required |
| Database | 40 GB encrypted gp3 host volume includes OS/database; logical S3 backup and EBS snapshot | RDS PostgreSQL db.t4g.micro, Single-AZ, 20 GB gp3, private DB |
| Access | SSM Session Manager port forwarding; no inbound security-group rules | HTTPS ALB across two AZs, non-exportable ACM certificate, existing owned domain |
| Network | One public IPv4 for outbound SSM/ECR; no NAT/ALB | Public task IPv4; task SG only from ALB, DB SG only from task; no NAT in base |
| State/release | One failure domain; stop old app before new; manual recovery | Desired count one, stop/start without task overlap; not HA |
| Educational value | IAM, VPC, ECR, SSM, EBS/S3 recovery, Terraform lifecycle and cost teardown | Adds ECS task/IAM split, ALB, RDS/TLS, subnets/SGs, DNS/ACM, more idle cost |

A preserves the synthetic identity boundary by forwarding to the host's
127.0.0.1 listener. SSM transport is encrypted; the browser still speaks HTTP to
its own loopback. This is **not end-to-end browser HTTPS**. Require an appropriately
scoped operator IAM session and bind the local forwarded port to loopback. There
is no SSH ingress, public UI, third-party enrollment or synthetic selector exposed
through a public reverse proxy. Future literal HTTPS/public access requires a
separately reviewed TLS and real identity design. An operator with host/root/SSM
access remains trusted and can read synthetic data; containers are not a boundary
against that operator.

B is an architecture comparison, **not deployable with the current unchanged
application**. An awsvpc task bound to loopback cannot serve an ALB; the database
DSN is also fixed to loopback. Changing bind, remote PostgreSQL credentials/TLS,
trusted origins/proxy handling and authentication requires explicit implementation
scope/security review. An ALB or OAuth component cannot simply make the current
developer identity selectors safe. Do not relax those guards in Terraform.
If later approved, use one running app task, minimumHealthyPercent=0 and
maximumPercent=100, accepting downtime; overlapping replicas would violate the
process-local candidate/concurrency assumptions. RDS and task remain single
instances. Two ALB AZs alone do not create application/database HA.

## Official price assumptions

Checked 2026-10-25 from public AWS documentation and unauthenticated AWS price
files; no signed/account AWS API calls. Prices are on-demand USD before taxes,
FX, support and credits. Requote before approval/apply. No free-tier or shared
100 GB transfer allowance is credited. These estimates are not billing caps.

| Component | Gross assumption | Official evidence |
| --- | --- | --- |
| EC2 t3.small Linux | $0.0208/hour | [EC2 pricing](https://aws.amazon.com/ec2/pricing/on-demand/), [regional Linux price file](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/US%20East%20(N.%20Virginia)/Linux/index.json), publication 2026-10-23 |
| Fargate Linux x86 | $0.04048/vCPU-hour + $0.004445/GB-hour, derived from per-second rates | [Fargate pricing](https://aws.amazon.com/fargate/pricing/); first 20 GB ephemeral storage included |
| RDS PostgreSQL db.t4g.micro Single-AZ | $0.016/hour; gp3 $0.115/GB-month; additional backup $0.095/GB-month | [PostgreSQL pricing](https://aws.amazon.com/rds/postgresql/pricing/), [regional RDS offer](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/us-east-1/index.json), publication 2026-10-20 |
| EBS gp3 / snapshot | $0.08 / $0.05 per GB-month | [EBS pricing](https://aws.amazon.com/ebs/pricing/), [AWS EBS price file](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ebs.json), publication 2026-10-23 |
| ALB | $0.0225/hour + $0.008/LCU-hour; assume 0.1 average LCU | [ELB pricing](https://aws.amazon.com/elasticloadbalancing/pricing/), [regional offer](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/us-east-1/index.json), publication 2026-09-11 |
| Public IPv4 / NAT | $0.005/address-hour; optional NAT $0.045/hour + $0.045/GB processed | [VPC pricing](https://aws.amazon.com/vpc/pricing/), [regional VPC offer](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonVPC/current/us-east-1/index.json), publication 2026-10-16 |
| ECR | $0.10/GB-month; same-region image transfer $0 | [ECR pricing](https://aws.amazon.com/ecr/pricing/) |
| S3 Standard | $0.023/GB-month; PUT $0.005/1,000, GET $0.0004/1,000 | [S3 pricing](https://aws.amazon.com/s3/pricing/), [regional offer](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/us-east-1/index.json), publication 2026-10-15 |
| CloudWatch | $0.50/GB ingestion, $0.03/GB-month stored; standard alarm $0.10/month | [CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/) |
| Secrets Manager | $0.40/secret-month, $0.05/10,000 requests | [Secrets pricing](https://aws.amazon.com/secrets-manager/pricing/), [regional offer](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSSecretsManager/current/us-east-1/index.json), publication 2026-09-11 |
| Data transfer | $0.09/GB gross internet egress; same-AZ placement assumed | [EC2 transfer pricing](https://aws.amazon.com/ec2/pricing/on-demand/) |
| Operator access | EC2 Session Manager no additional service charge; underlying resources still billed | [Systems Manager pricing](https://aws.amazon.com/systems-manager/pricing/) |
| DNS / certificate | New hosted zone $0.50 first month; 1,000 non-alias queries $0.0004; integrated non-exportable public ACM certificate $0 | [Route 53 pricing](https://aws.amazon.com/route53/pricing/), [ACM pricing](https://aws.amazon.com/certificate-manager/pricing/) |

No customer KMS key, Route 53 health check, private CA, WAF, Container Insights,
custom metric, tracing export, VPC endpoint or NAT is included in the base. If
added, explicitly price it first. Use SSE-S3 state/backup encryption and AWS-managed
EBS/RDS encryption initially. Domain purchase is not included or authorized; B
assumes an already controlled domain. ALB DNS alias queries are free; the query
allowance above conservatively assumes non-alias lookups. T3 standard credits
avoid the separate $0.05/vCPU-hour unlimited surplus rate; throttling is possible.
RDS backup allowance is not credited: 10 GB charged retention is conservative,
especially for snapshots retained after instance deletion.

## Reproducible arithmetic and idle charges

Full component arithmetic is in
[f4-01-aws-costs.json](../implementation/evidence/f4-01-aws-costs.json). Storage
uses `GB * monthly_rate * hours / 730`; 24-hour compute/network costs use hours
directly. Seven-day artifact retention is 168 hours. Backup sizes are planning
allowances, not sizes inferred from one small local dump.

| 24-hour demo plus retained artifacts | A: EC2 | B: Fargate/RDS |
| --- | ---: | ---: |
| Compute | $0.49920 | $0.59244 task + $0.38400 DB |
| Active database/host storage | $0.10521 | $0.07562 |
| ALB and 0.1 LCU | $0 | $0.55920 |
| IPv4 (one / three) | $0.12000 | $0.36000 |
| Seven-day snapshot allowance | $0.11507 | $0.21863 |
| ECR + S3 backup + state + requests | $0.02891 | $0.02891 |
| Logs + secret + alarms | $0.07092 | $0.07749 |
| Gross 2 GB internet egress | $0.18000 | $0.18000 |
| New zone + query allowance | $0 | $0.50040 |
| **Estimated total** | **$1.11930** | **$2.97668** |

These are workload assumptions, not guaranteed maximum bills. Unused ALB, RDS,
public IPv4, storage, secrets, images, logs and snapshots keep accruing charges.
The 730-hour idle/no-request baseline is approximately **$23.26 A running** or
**$62.34 B running** with the stated retained storage. Stopping EC2 and releasing
its address still leaves about **$4.426/month** for the retained storage, secret
and alarms. RDS stop does not remove storage charges and
[automatically starts after seven days](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html).
ALB addresses and NAT also remain billed until removed. A private-task NAT
variant adds roughly `$0.045 * hours + $0.045 * GB` relative to the base (NAT
public IP replaces task IP), about $1.08/day before data. Multiple NATs increase
that. Cross-AZ traffic, higher LCUs, image churn, CPU surplus or retained resources
can exceed these figures. AWS Budgets alarms are delayed alerts, not hard caps.

## Recommendation and future Terraform scope

Choose A for an attended synthetic operational exercise, if separately approved.
It offers real infrastructure/IAM/state/restore/teardown practice while preserving
the existing one-process boundary. It trades availability and automated recovery
for simplicity. Local tests demonstrate app behavior, not AWS host hardening,
SSM connectivity, performance or availability. B's additional configuration and
idle cost are justified only by separately approved ALB/RDS learning requirements.

Proposed F4-02 design/implementation tasks (not begun here):

1. Pin Terraform/provider versions and AMI digest/ID at implementation time; commit
   reviewed lockfiles then. Inventory/tag owner, unit, expiry, region and cost
   center. Separate read-only planning from apply permissions and require plan
   review. No default auto-apply or credentials in repository.
2. Bootstrap state deliberately: dedicated S3 prefix/bucket with versioning,
   encryption, public-access block, TLS-only policy and locking (`use_lockfile`
   after supported-version verification). Scope IAM to that state/lock. Treat
   state as sensitive; never put database passwords/provider keys in TF values,
   outputs, user-data or state. Document separate state-bucket teardown, recovery
   and retention instead of destroying its own recovery history blindly.
3. A: minimal VPC/subnet/route/IGW, no ingress, t3.small standard credits, encrypted
   40 GB gp3, instance role scoped to SSM, selected ECR repository and backup
   prefix. IMDSv2 mandatory; constrain container access to instance credentials.
   Docker runtime gets no AWS credentials; host backup/pull process owns its
   narrower permissions. No SSH keys, wildcard S3 access or broad administrator
   role. Scope ECR token action separately from repository pull permissions.
4. Secret delivery via instance role to a root-owned temporary file/read-only
   mount, no command line or raw logs. A can retain loopback synthetic trust only
   for this operator demo after explicit risk acceptance; any networked database
   requires a separate app role, migration role, password rotation and verified
   TLS. B needs those application changes before infrastructure activation.
5. Freeze image by digest, local-only binding, OS patch level and one-process
   startup. Pull then stop/start app; health/readiness and owned durable readback
   gate release. Do not use Compose restart loops to hide migration failures.
6. Approve processor/region/retention for **all** cloud data, backups and logs.
   Default hosted app telemetry remains off; even metadata CloudWatch export needs
   a separate destination/privacy approval. Budgeted logs are a proposal only.
   Backup bucket encryption, owner-only IAM and seven-day lifecycle are required;
   test actual restore to a fresh target and measure RPO/RTO before claiming them.
7. HTTPS: A uses an encrypted SSM tunnel with loopback browser HTTP and no public
   endpoint. If literal HTTPS is an acceptance requirement, stop for a separately
   reviewed solution. B requires ACM/domain control, HTTPS-only ALB ingress,
   verified backend networking, real auth and cookie/CSRF/Origin review before
   participant access; synthetic auth must never be publicly forwarded.
8. Teardown within the attended window: final quiesced synthetic backup if approved,
   stop app, destroy task/host/ALB/RDS/NAT/interfaces/addresses, review retained
   EBS/RDS snapshots/ECR layers/S3 versions/state/log groups/secrets/zone. Verify
   inventory and later billing, with an explicit list/cost/expiry for anything
   retained. Secrets scheduled deletion and snapshot retention are not immediate
   absence of charges. No automated global delete/prune.

## Separate owner decisions before any cloud execution

- Authorize the exact next work unit and source-reviewed Terraform plan.
- Approve account/region/operator role, synthetic data destinations and retention.
- Approve topology A or B and its authentication/HTTPS limitations. B remains
  blocked on unimplemented identity/network requirements.
- Approve a numerical maximum, attended window and residual-resource allowance.
  A possible **future** request is $5 total for one 24-hour A exercise including
  seven-day artifacts; it is not currently granted and is not an AWS hard cap.
  Reprice and define manual shutdown thresholds before requesting approval.
- Approve outbound AWS resource/registry access, IAM/secret/state handling,
  backup/recovery target and teardown audit. App live-provider and telemetry
  access remain independent NO-GO decisions; do not piggyback them on AWS consent.

Current result: **local release/recovery measured; AWS planned, not operated**.
See [handoff](../implementation/f4-01-handoff.md) and
[local operator instructions](../local-release.md).
