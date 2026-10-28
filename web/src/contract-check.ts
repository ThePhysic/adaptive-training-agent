// Type-level smoke checks only: no client, UI, event parser or network request.
import type { components, paths } from "./api.generated.js";

type Approval = components["schemas"]["ApprovalRequest"];
const approval: Approval = {
  candidate_id: "synthetic-candidate", revision: 1,
  content_hash: "a".repeat(64), idempotency_key: "synthetic-key"
};
// @ts-expect-error owner is server-derived, never an approval field
approval.owner_id = "other";
type Done = components["schemas"]["DoneEvent"]["payload"];
const clarify: Done = { outcome: "clarify", fields: ["excluded_ids"], choices: ["Change exclusions"] };
// @ts-expect-error streaming completion is not an approval outcome
const invalid: Done = { outcome: "approved" };
type ApproveEndpoint = paths["/api/v1/drafts/{candidate_id}/approve"]["post"];
const request: ApproveEndpoint["requestBody"]["content"]["application/json"] = approval;
void [clarify, invalid, request];
