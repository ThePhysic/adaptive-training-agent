# F4-A1b — Owner-attested completion

Recorded on 2026-10-26 from the owner's report in this conversation. Exact execution
timestamps, native CLI version and capture/cleanup evidence were not supplied.
**Owner-attested live result; not independently reproduced or audited by Codex.**

```json
{"checkpoint":"F4-A1b","result":"identity_matched","mfa_verified":false,"http_request_count_verified":false}
```

The owner reports this separately authorized sequence:

1. No authoritative saved state-operator UserId was located.
2. One read-only human-administrator `iam:GetUser` request targeted only
   `future-f4-state-operator`. The owner privately verified/saved the authoritative
   state Account, exact Arn and AWS-generated UserId.
3. The reviewed state-operator STS procedure was prepared.
4. One separately authorized `sts:GetCallerIdentity` invocation used
   `future-f4-state-operator`. All three identity fields matched the private
   expectations exactly. The reviewed procedure specifies us-east-1 and
   `https://sts.us-east-1.amazonaws.com`; this is the procedure's binding, not a
   fresh independent observation of the owner's transport/session.

No IAM modifications, S3 operations, Terraform operations or infrastructure
deployment were reported. The two named service operations do not establish the
underlying HTTP request count, including authentication/refresh exchanges.

MFA use remains unverified (`false` means unverified, not absent). Native credential
refresh and authentication-related traffic remain documented limitations; OS-enforced
egress containment was not established. No new independently measured claim is made
about identity source, native compatibility, attempt fences, process cleanup, output
privacy or the exact implementation used by the owner. An identity match does not
establish effective permissions, policy inventory, boundary attachment or deployment
readiness. The report does not provide a reusable authentication/containment exception
for later units.

Codex has not opened/corrected/copied the private identity record, inspected real
credentials/config/login caches, read raw AWS responses, repeated either operation
or issued a follow-up request. No private identifiers accompany this record.

**F4-A1b is recorded complete within that owner-attested scope. No subsequent AWS
permission or operation is authorized.** A2 metadata reads, A3 policy-body closure,
MFA/context checks, policy validation/installation, S3, Terraform, deployment,
spending and live automation each retain separate approval gates.

The [A1b offline handoff](f4-a1b-offline-preparation-handoff.md), its
[supervised proposal](f4-a1b-supervised-sts-procedure.md), and earlier A1a security
NO-GO records remain historical evidence of the conditions at their respective dates.
They have not been rewritten as successful automated/contained execution. Existing
live executors and fixed operation scopes are unchanged.

Next: [A2 offline inventory preparation](f4-a2-iam-inventory-preparation.md), followed
by independent review, not automatic AWS execution.
