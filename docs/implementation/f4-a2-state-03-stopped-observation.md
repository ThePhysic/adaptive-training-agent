# F4-A2-state-03 — Stopped owner-attested observation

Recorded on 2026-10-26 from the owner's report. **Owner-attested live/private local
inspection evidence, not independently reproduced or inspected by Codex.**

Original sanitized result, retained unchanged:

```json
{"checkpoint":"F4-A2-state-03","result":"stopped","outcome_uncertain":true}
```

The owner authorized one supervised ListGroupsForUser invocation: caller
`future-f4-human-admin`, target `future-f4-state-operator`, us-east-1,
`https://iam.amazonaws.com`. Subsequent owner-supervised **local** inspection reported:

| Artifact | Owner-reported status |
| --- | --- |
| preparation.json | Present |
| preparation.sha256 | Present |
| attempt.claim | Present; retained |
| observed-groups.json | Present; privately retained |
| result.json | Absent |

The owner reports that the observation passed existing structural checks and contains
exactly **one group**, recognized as `FutureStateOperators`. The approved group
allowlist was empty, so that nonempty observation could not pass. This explains the
stop; it is **not successful state-03 allowlist validation** or retrospective approval.
The original stopped/uncertain result and claim remain unchanged. Do not rerun state-03.

The owner reports that the group's only member is `future-f4-state-operator` and
that a policy named `SignInLocalDevelopmentAccess` was assigned during original setup.
Those are owner setup recollections, not verified membership enumeration, policy
classification, ARN, contents or effective-permission evidence. Managed versus inline
is unknown; no policy ARN is manufactured or policy body inferred from the name.

State-01 separately reported zero direct managed user attachments; state-02 reported
zero inline user policies. This group **may provide inherited permissions**. The
boundary and effective permissions remain unverified. MFA, exact underlying HTTP
count, native refresh/authentication and Windows OS-egress-containment limitations
remain. Raw records/identifiers, binary/source pins, timestamps and capture/cleanup
were not independently verified by Codex. The generic uncertainty flag is not rewritten.

Codex has not opened/copied the private group observation, identities, credentials,
AWS configuration, login caches or raw responses; no AWS request or mutation was
performed in this task. No claim deletion, result replacement, retry or old allowlist
change occurs. Historical [state-03 handoff](f4-a2-state-03-handoff.md),
[procedure](f4-a2-state-03-supervised-procedure.md) and NO-GO records remain unchanged.

Future group-policy metadata queries need **new prospective private group approval**
and independent policy expectations, fresh source/window/digest review and separate
live authorizations. That is not retroactive state-03 approval. Neither a returned
policy nor this observation is its own preapproved expectation. Current work prepares
two independent procedures offline only; no further AWS authority is requested/granted.
