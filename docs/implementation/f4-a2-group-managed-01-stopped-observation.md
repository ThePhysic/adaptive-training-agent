# F4-A2-group-managed-01 — Stopped observation

2026-10-27. Owner-attested evidence recorded offline. Codex did not execute or
reproduce the invocation, inspect private records, or contact AWS.

The owner reports one separately authorized, supervised initial-page
`iam:ListAttachedGroupPolicies` invocation: caller `future-f4-human-admin`, target
`FutureStateOperators`, region `us-east-1`, endpoint `https://iam.amazonaws.com`.

```json
{"checkpoint":"F4-A2-group-managed-01","result":"stopped","outcome_uncertain":true}
```

The owner's subsequent local presence check reported:

| Artifact | Owner-reported presence |
| --- | --- |
| `preparation.json` | Present |
| `preparation.sha256` | Present |
| `attempt.claim` | Present |
| `observed-policies.json` | Absent |
| `result.json` | Absent |

The claim exists; no verified observation or successful result was reported as
persisted. This is not proof that claim creation returned successfully, that the
native process started, or that an HTTP request reached AWS. The cause is unknown.
No authentication, authorization, policy count/type, or missing-policy conclusion
can be drawn. MFA, exact HTTP request count, native refresh behavior, and Windows
OS-level egress containment remain unverified or limited as previously recorded.

The original stopped result, preparation, digest, claim and associated evidence
remain unchanged. Codex did not inspect, copy, repair, reset or backfill them. No
new diagnostic artifact is generated for that historical invocation. The claim
must remain; a new directory is not a replay mechanism. There is no retry or
alternative AWS diagnostic request proposed or authorized by this record.

State-01's zero directly attached managed user policies and state-02's zero inline
user policies remain separate owner-attested findings. State-03 retained one group
membership without passing its allowlist. Group-inherited authority, managed/inline
policy classification, the permissions boundary and effective permissions remain
unverified. Historical NO-GO decisions and all approval boundaries are unchanged.

See the [failure-path analysis](f4-a2-group-managed-01-failure-analysis.md) and
[offline postmortem handoff](f4-a2-group-managed-01-postmortem-handoff.md).
