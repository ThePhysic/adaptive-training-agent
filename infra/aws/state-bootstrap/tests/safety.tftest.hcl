mock_provider "aws" {
  override_during = plan
  mock_resource "aws_s3_bucket" {
    defaults = { id = "fata-offline-state", arn = "arn:aws:s3:::fata-offline-state" }
  }
}
variables {
  account_id              = "000000000000"
  bucket_name             = "fata-offline-state"
  bootstrap_principal_arn = "arn:aws:iam::000000000000:role/synthetic-bootstrap"
  state_principal_arn     = "arn:aws:iam::000000000000:role/synthetic-state"
  permission_starts_at    = "2030-01-01T00:00:00Z"
  permission_expires_at   = "2030-01-01T01:00:00Z"
}
run "state_is_locked_and_scoped" {
  command = plan
  assert {
    condition     = output.backend_configuration.encrypt && output.backend_configuration.use_lockfile && output.backend_configuration.key == "ec2-demo/terraform.tfstate"
    error_message = "Encrypted state and native S3 locking required."
  }
  assert {
    condition     = jsondecode(output.state_operator_policy).Statement[2].Resource == "arn:aws:s3:::fata-offline-state/ec2-demo/terraform.tfstate.tflock" && !contains(jsondecode(output.state_operator_policy).Statement[1].Action, "s3:DeleteObject")
    error_message = "Delete permission must be confined to the lock object."
  }
  assert {
    condition     = tolist(jsondecode(output.state_operator_policy).Statement[0].Condition.StringEquals["s3:prefix"]) == tolist(["env:/"]) && output.backend_configuration.workspace_key_prefix == "env:" && output.backend_configuration.max_retries == 1
    error_message = "Only the observed default-workspace discovery prefix and bounded retry setting are permitted."
  }
  assert {
    condition     = alltrue([for s in jsondecode(output.state_operator_policy).Statement : s.Condition.DateLessThan["aws:CurrentTime"] == var.permission_expires_at && s.Condition.ArnEquals["aws:PrincipalArn"] == var.state_principal_arn]) && jsondecode(output.bootstrap_operator_policy).Statement[0].Condition.ArnEquals["aws:PrincipalArn"] == var.bootstrap_principal_arn
    error_message = "Every proposed grant must expire and bind the exact separate principal."
  }
  assert {
    condition     = jsondecode(output.bootstrap_operator_policy).Statement[0].Resource == "arn:aws:s3:::fata-offline-state" && contains(jsondecode(output.bootstrap_operator_policy).Statement[0].Action, "s3:TagResource") && alltrue([for a in jsondecode(output.bootstrap_operator_policy).Statement[0].Action : !strcontains(a, "*") && !strcontains(a, "Delete") && startswith(a, "s3:")])
    error_message = "Bootstrap may only set up/read its exact bucket, never delete or grant wildcard service actions."
  }
  assert {
    condition     = toset(jsondecode(output.plan_operator_policy).Statement[1].Action) == toset(["s3:GetObject"]) && toset(jsondecode(output.plan_operator_policy).Statement[2].Action) == toset(["s3:GetObject", "s3:PutObject", "s3:DeleteObject"])
    error_message = "First-plan grant must deny state writes while retaining exact lock lifecycle actions."
  }
  assert {
    condition     = jsondecode(output.plan_operator_policy).Statement[0] == jsondecode(output.state_operator_policy).Statement[0] && jsondecode(output.plan_operator_policy).Statement[1].Condition == jsondecode(output.state_operator_policy).Statement[1].Condition && jsondecode(output.plan_operator_policy).Statement[2] == jsondecode(output.state_operator_policy).Statement[2]
    error_message = "The derived plan policy must retain every principal/time/TLS/prefix and lock boundary unchanged."
  }
  assert {
    condition     = alltrue([for s in concat(jsondecode(output.bootstrap_operator_policy).Statement, jsondecode(output.state_operator_policy).Statement) : s.Condition.DateGreaterThanEquals["aws:CurrentTime"] == var.permission_starts_at && s.Condition.Bool["aws:SecureTransport"] == "true" && s.Condition.StringEquals["aws:PrincipalAccount"] == var.account_id && s.Condition.StringEquals["aws:RequestedRegion"] == "us-east-1"])
    error_message = "No unbound, non-TLS, cross-account/region or early authority."
  }
}
run "reject_preflight_bootstrap_writes" {
  command = plan
  variables { bootstrap_principal_arn = "arn:aws:iam::000000000000:user/future-f4-preflight" }
  expect_failures = [var.bootstrap_principal_arn]
}
run "reject_preflight_state_writes" {
  command = plan
  variables { state_principal_arn = "arn:aws:iam::000000000000:user/path/future-f4-preflight" }
  expect_failures = [var.state_principal_arn]
}
run "reject_overlong_authority" {
  command = plan
  variables { permission_expires_at = "2030-01-01T02:00:01Z" }
  expect_failures = [var.permission_expires_at]
}
run "reject_cross_account_principal" {
  command = plan
  variables { state_principal_arn = "arn:aws:iam::111111111111:role/synthetic-state" }
  expect_failures = [var.state_principal_arn]
}
run "reject_zero_permission_window" {
  command = plan
  variables { permission_expires_at = "2030-01-01T00:00:00Z" }
  expect_failures = [var.permission_expires_at]
}
run "accept_exact_two_hour_boundary" {
  command = plan
  variables { permission_expires_at = "2030-01-01T02:00:00Z" }
}
run "bind_established_operator_user" {
  command = plan
  variables {
    bootstrap_principal_arn = "arn:aws:iam::000000000000:user/future-f4-state-operator"
    state_principal_arn     = "arn:aws:iam::000000000000:user/future-f4-state-operator"
  }
  assert {
    condition     = jsondecode(output.bootstrap_operator_policy).Statement[0].Condition.ArnEquals["aws:PrincipalArn"] == var.bootstrap_principal_arn && alltrue([for s in jsondecode(output.plan_operator_policy).Statement : s.Condition.ArnEquals["aws:PrincipalArn"] == var.state_principal_arn])
    error_message = "Both proposals must bind the selected operator user; preflight stays read-only."
  }
}
run "boundary_is_opt_in" {
  command = plan
  assert {
    condition     = output.state_operator_boundary_policy == null
    error_message = "Existing grant-generation workflows must not implicitly enable a boundary."
  }
}
run "boundary_exact_ceiling" {
  command = plan
  variables {
    include_state_operator_boundary = true
    bootstrap_principal_arn         = "arn:aws:iam::000000000000:user/future-f4-human-admin"
    state_principal_arn             = "arn:aws:iam::000000000000:user/future-f4-state-operator"
  }
  assert {
    condition     = length(jsondecode(output.state_operator_boundary_policy).Statement) == 14 && length([for s in jsondecode(output.state_operator_boundary_policy).Statement : s if s.Effect == "Allow"]) == 4
    error_message = "Only the four reviewed capability allows and ten explicit deny guards are permitted."
  }
  assert {
    condition     = alltrue([for s in jsondecode(output.state_operator_boundary_policy).Statement : !can(s.Condition.DateLessThan) && !can(s.Condition.DateGreaterThanEquals)])
    error_message = "Persistent ceiling must never inherit the temporary grant window."
  }
  assert {
    condition     = alltrue([for s in jsondecode(output.state_operator_boundary_policy).Statement : s.Sid != "BrowserLogin" || (toset(s.Action) == toset(["signin:AuthorizeOAuth2Access", "signin:CreateOAuth2Token"]) && s.Resource == "arn:aws:signin:*:*:oauth2/public-client/*" && !can(s.Condition))])
    error_message = "Documented pre-login public-client authorization must survive without S3-only conditions."
  }
  assert {
    condition     = alltrue([for s in jsondecode(output.state_operator_boundary_policy).Statement : s.Sid != "StateReadWrite" || (s.Resource == "arn:aws:s3:::fata-offline-state/ec2-demo/terraform.tfstate" && toset(s.Action) == toset(["s3:GetObject", "s3:PutObject"]))])
    error_message = "State content maximum is exact-key read/write, never deletion."
  }
  assert {
    condition     = alltrue([for s in jsondecode(output.state_operator_boundary_policy).Statement : s.Sid != "LockLifecycle" || (s.Resource == "arn:aws:s3:::fata-offline-state/ec2-demo/terraform.tfstate.tflock" && toset(s.Action) == toset(["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]))])
    error_message = "Only the exact native lock receives read/write/delete."
  }
  assert {
    condition     = alltrue([for s in jsondecode(output.state_operator_boundary_policy).Statement : s.Effect != "Allow" || s.Sid == "BrowserLogin" || (s.Condition.ArnEquals["aws:PrincipalArn"] == var.state_principal_arn && s.Condition.StringEquals["aws:PrincipalAccount"] == var.account_id && s.Condition.StringEquals["aws:RequestedRegion"] == "us-east-1" && s.Condition.Bool["aws:SecureTransport"] == "true")])
    error_message = "S3 allows retain persistent principal, account, region and HTTPS restrictions."
  }
  assert {
    condition     = alltrue([for s in jsondecode(output.state_operator_boundary_policy).Statement : s.Sid != "WorkspaceDiscovery" || (s.Resource == "arn:aws:s3:::fata-offline-state" && tolist(s.Condition.StringEquals["s3:prefix"]) == tolist(["env:/"]))])
    error_message = "Keep the observed discovery prefix; no arbitrary listing expansion."
  }
}
run "boundary_survives_grant_window_change" {
  command = plan
  variables {
    include_state_operator_boundary = true
    bootstrap_principal_arn         = "arn:aws:iam::000000000000:user/future-f4-human-admin"
    state_principal_arn             = "arn:aws:iam::000000000000:user/future-f4-state-operator"
    permission_expires_at           = "2030-01-01T02:00:00Z"
  }
  assert {
    condition     = output.state_operator_boundary_policy == run.boundary_exact_ceiling.state_operator_boundary_policy && jsondecode(output.plan_operator_policy).Statement[1].Condition.DateLessThan["aws:CurrentTime"] == var.permission_expires_at
    error_message = "Grant windows change independently from the persistent boundary."
  }
}
run "boundary_accepts_actual_operator_path" {
  command = plan
  variables {
    include_state_operator_boundary = true
    state_principal_arn             = "arn:aws:iam::000000000000:user/path/future-f4-state-operator"
  }
}
run "boundary_rejects_role" {
  command = plan
  variables { include_state_operator_boundary = true }
  expect_failures = [output.state_operator_boundary_policy]
}
run "boundary_rejects_other_user" {
  command = plan
  variables {
    include_state_operator_boundary = true
    state_principal_arn             = "arn:aws:iam::000000000000:user/future-f4-human-admin"
  }
  expect_failures = [output.state_operator_boundary_policy]
}
