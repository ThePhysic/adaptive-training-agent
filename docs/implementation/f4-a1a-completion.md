# F4-A1a — Owner-attested completion

Recorded on 2026-10-26 from the owner's report in this conversation. Exact execution
timestamps were not supplied. **Owner-attested live success, not independently
reproduced or audited Codex execution.**

```json
{"checkpoint":"F4-A1a","result":"identity_matched","mfa_verified":false,"http_request_count_verified":false}
```

The owner reports the following separately authorized operations in a local VS Code
PowerShell terminal (terminal/CLI versions were not supplied for this execution):

1. One read-only `iam:GetUser` operation targeting `future-f4-human-admin`, to obtain
   the AWS-generated UserId. The owner privately verified/saved the expected Account,
   Arn and UserId. This was a separate reference read, not an implied STS permission.
2. One separately authorized `sts:GetCallerIdentity` invocation using the
   `future-f4-human-admin` profile, us-east-1, and
   `https://sts.us-east-1.amazonaws.com`, after preparing the isolated CLI
   configuration/environment described by the owner.
3. Strict, case-sensitive comparisons of all three returned identity fields against
   those private expectations, producing the sanitized result above.

Codex has not opened the private expected-identity file, read credentials/cache,
copied identifiers or raw responses, inspected their storage/ACLs, or repeated either
operation. No private identifiers, tokens or credential material accompany this record.
The reported environment preparation is **not OS-enforced network containment**.

## Evidence limits and scope

- MFA use was not independently verified. `mfa_verified:false` means unverified,
  not that MFA was absent.
- Underlying HTTP request count was not established. The two named operations above
  are not an audit of service/authentication handshakes or retry counts.
- OS-enforced egress containment was unavailable. Native CLI credential refresh and
  authentication-related traffic remain documented limitations of the accepted
  supervised A1a approach.
- Identity matching does not prove least privilege, current effective policies,
  a boundary attachment, Terraform/backend compatibility or deployment readiness.
- No IAM modifications, S3 mutations, Terraform operations or infrastructure
  deployment were reported by the owner for this checkpoint.

**F4-A1a is recorded complete within that owner-attested scope. No subsequent AWS
permissions or operations were authorized.** A1b, extra IAM reads, login, policy
validation/creation/attachment, S3 reads/writes, remote init/locking, plans, apply,
deployment and spending each still require their own explicit approval.

The earlier [supervised proposal](f4-a1a-supervised-sts-procedure.md),
[native-containment NO-GO](f4-a1a-native-containment-handoff.md) and
[Home assessment](f4-a1a-native-containment-handoff.md) (curated replacement; original historical reference omitted) remain accurate
historical records of their authorization and evidence at the time. They are not
rewritten as successful isolated-executor evidence. Automated live executors remain
disabled; the A1a manual-risk exception does not automatically extend to A1b.

Next planning/evidence handoff: [A1b preparation](f4-a1b-preparation-handoff.md).
