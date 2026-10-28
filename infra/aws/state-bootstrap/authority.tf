# Proposals only: no IAM resource, attachment, trust change or active authority.
variable "bootstrap_principal_arn" {
  type = string
  validation {
    condition     = can(regex("^arn:aws:iam::${var.account_id}:(user|role)/[A-Za-z0-9+=,.@_/-]+$", var.bootstrap_principal_arn)) && !endswith(lower(var.bootstrap_principal_arn), "/future-f4-preflight")
    error_message = "Review an exact same-account bootstrap user/role; never grant writes to preflight."
  }
}
variable "state_principal_arn" {
  type = string
  validation {
    condition     = can(regex("^arn:aws:iam::${var.account_id}:(user|role)/[A-Za-z0-9+=,.@_/-]+$", var.state_principal_arn)) && !endswith(lower(var.state_principal_arn), "/future-f4-preflight")
    error_message = "Review an exact same-account state user/role; never grant writes to preflight."
  }
}
variable "permission_starts_at" {
  type = string
  validation {
    condition     = endswith(var.permission_starts_at, "Z") && can(formatdate("YYYY", var.permission_starts_at))
    error_message = "Specify an explicit UTC permission-window start."
  }
}
variable "permission_expires_at" {
  type = string
  validation {
    condition     = endswith(var.permission_expires_at, "Z") && try(timecmp(var.permission_starts_at, var.permission_expires_at) < 0 && timecmp(var.permission_expires_at, timeadd(var.permission_starts_at, "2h")) <= 0, false)
    error_message = "Permission window must be positive, UTC and no longer than two hours."
  }
}
locals {
  common_conditions = {
    DateGreaterThanEquals = { "aws:CurrentTime" = var.permission_starts_at }
    DateLessThan          = { "aws:CurrentTime" = var.permission_expires_at }
    StringEquals          = { "aws:PrincipalAccount" = var.account_id, "aws:RequestedRegion" = "us-east-1" }
    Bool                  = { "aws:SecureTransport" = "true" }
  }
  state_conditions     = merge(local.common_conditions, { ArnEquals = { "aws:PrincipalArn" = var.state_principal_arn } })
  bootstrap_conditions = merge(local.common_conditions, { ArnEquals = { "aws:PrincipalArn" = var.bootstrap_principal_arn } })
  bootstrap_policy = {
    Version = "2012-10-17"
    Statement = [{
      Sid       = "ReviewedStateBucketSetupAndRefreshOnly", Effect = "Allow"
      Resource  = local.state_bucket_arn
      Condition = local.bootstrap_conditions
      Action = [
        "s3:CreateBucket", "s3:TagResource", "s3:PutBucketTagging", "s3:PutBucketPublicAccessBlock",
        "s3:PutBucketOwnershipControls", "s3:PutBucketVersioning",
        "s3:PutEncryptionConfiguration", "s3:PutBucketPolicy",
        # Explicit ancillary reads used by the pinned bucket resource, even when
        # CORS/website/replication/lifecycle/object-lock are not configured here.
        "s3:ListBucket", "s3:GetBucketLocation", "s3:GetBucketTagging",
        "s3:GetBucketPublicAccessBlock", "s3:GetBucketOwnershipControls",
        "s3:GetEncryptionConfiguration", "s3:GetBucketPolicy", "s3:GetBucketAcl",
        "s3:GetBucketCORS", "s3:GetBucketWebsite", "s3:GetBucketVersioning",
        "s3:GetAccelerateConfiguration", "s3:GetBucketRequestPayment",
        "s3:GetBucketLogging", "s3:GetLifecycleConfiguration",
        "s3:GetReplicationConfiguration", "s3:GetBucketObjectLockConfiguration"
      ]
    }]
  }
}
