# Persistent ceiling proposal only. No managed IAM resource or attachment.
# Opt-in leaves existing bootstrap/state/plan policy outputs unchanged.
variable "include_state_operator_boundary" {
  type    = bool
  default = false
}
locals {
  state_operator_boundary_name = "future-f4-state-operator-boundary"
  boundary_login_actions       = ["signin:AuthorizeOAuth2Access", "signin:CreateOAuth2Token"]
  # Same public-client resource scope as SignInLocalDevelopmentAccess v3.
  # Do not copy S3 principal/region/MFA conditions into the pre-login flow.
  boundary_login_resource = "arn:aws:signin:*:*:oauth2/public-client/*"
  boundary_object_actions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
  boundary_s3_actions     = concat(["s3:ListBucket"], local.boundary_object_actions)
  boundary_state_arn      = "${local.state_bucket_arn}/${local.state_key}"
  boundary_lock_arn       = "${local.boundary_state_arn}.tflock"
  # Persistent restrictions, deliberately independent of temporary grant windows.
  boundary_s3_conditions = {
    ArnEquals    = { "aws:PrincipalArn" = var.state_principal_arn }
    StringEquals = { "aws:PrincipalAccount" = var.account_id, "aws:RequestedRegion" = "us-east-1" }
    Bool         = { "aws:SecureTransport" = "true" }
  }
  state_operator_boundary = {
    Version = "2012-10-17"
    Statement = [
      { Sid = "BrowserLogin", Effect = "Allow", Action = local.boundary_login_actions, Resource = local.boundary_login_resource },
      { Sid       = "WorkspaceDiscovery", Effect = "Allow", Action = ["s3:ListBucket"], Resource = local.state_bucket_arn,
        Condition = merge(local.boundary_s3_conditions, { StringEquals = merge(local.boundary_s3_conditions.StringEquals, { "s3:prefix" = ["env:/"] }) })
      },
      { Sid = "StateReadWrite", Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject"], Resource = local.boundary_state_arn,
      Condition = local.boundary_s3_conditions },
      { Sid = "LockLifecycle", Effect = "Allow", Action = local.boundary_object_actions, Resource = local.boundary_lock_arn,
      Condition = local.boundary_s3_conditions },
      # Implicit boundary denies alone do not limit same-account resource grants
      # directly to this user ARN. Explicit denies close the prohibited paths.
      { Sid = "DenyOtherActions", Effect = "Deny", NotAction = concat(local.boundary_login_actions, local.boundary_s3_actions), Resource = "*" },
      { Sid = "DenyOtherLoginResources", Effect = "Deny", Action = local.boundary_login_actions, NotResource = local.boundary_login_resource },
      { Sid = "DenyOtherBuckets", Effect = "Deny", Action = ["s3:ListBucket"], NotResource = local.state_bucket_arn },
      { Sid = "DenyOtherObjectKeys", Effect = "Deny", Action = local.boundary_object_actions, NotResource = [local.boundary_state_arn, local.boundary_lock_arn] },
      { Sid = "DenyStateDeletion", Effect = "Deny", Action = ["s3:DeleteObject"], Resource = local.boundary_state_arn },
      { Sid = "DenyOtherPrefixes", Effect = "Deny", Action = ["s3:ListBucket"], Resource = local.state_bucket_arn,
      Condition = { StringNotEquals = { "s3:prefix" = ["env:/"] } } },
      { Sid = "DenyWrongPrincipal", Effect = "Deny", Action = local.boundary_s3_actions, Resource = "*",
      Condition = { ArnNotEquals = { "aws:PrincipalArn" = var.state_principal_arn } } },
      { Sid = "DenyWrongAccount", Effect = "Deny", Action = local.boundary_s3_actions, Resource = "*",
      Condition = { StringNotEquals = { "aws:PrincipalAccount" = var.account_id } } },
      { Sid = "DenyWrongRegion", Effect = "Deny", Action = local.boundary_s3_actions, Resource = "*",
      Condition = { StringNotEquals = { "aws:RequestedRegion" = "us-east-1" } } },
      { Sid = "DenyInsecureOrMissingTransport", Effect = "Deny", Action = local.boundary_s3_actions, Resource = "*",
      Condition = { BoolIfExists = { "aws:SecureTransport" = "false" } } }
    ]
  }
}
output "state_operator_boundary_policy" {
  value     = var.include_state_operator_boundary ? jsonencode(local.state_operator_boundary) : null
  sensitive = true
  precondition {
    condition     = !var.include_state_operator_boundary || can(regex("^arn:aws:iam::${var.account_id}:user/([A-Za-z0-9+=,.@_-]+/)*future-f4-state-operator$", var.state_principal_arn))
    error_message = "Boundary is only for the exact same-account state operator user."
  }
  precondition {
    condition     = !var.include_state_operator_boundary || length(jsonencode(local.state_operator_boundary)) <= 6144
    error_message = "Boundary exceeds the customer-managed policy document quota."
  }
}
