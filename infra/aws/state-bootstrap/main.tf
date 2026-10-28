terraform {
  required_version = "= 1.17.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.70.0" }
  }
  # Deliberately local for separately approved state bootstrap, never self-hosted.
  backend "local" {}
}
variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Explicit approved account required."
  }
}
variable "bucket_name" {
  type = string
  validation {
    condition     = can(regex("^fata-[a-z0-9-]{3,45}-state$", var.bucket_name))
    error_message = "Use a dedicated fata-...-state bucket."
  }
}
provider "aws" {
  region              = "us-east-1"
  allowed_account_ids = [var.account_id]
  max_retries         = 1
  default_tags { tags = { Project = "fata-state", WorkUnit = "F4-02", Retention = "explicit-reviewed-deletion" } }
}
module "state" {
  source           = "../modules/protected-bucket"
  name             = var.bucket_name
  backup_retention = false
}
locals {
  state_key        = "ec2-demo/terraform.tfstate"
  state_bucket_arn = "arn:aws:s3:::${var.bucket_name}"
  backend = {
    bucket               = var.bucket_name, key = local.state_key, region = "us-east-1"
    encrypt              = true, use_lockfile = true, allowed_account_ids = [var.account_id]
    workspace_key_prefix = "env:", max_retries = 1, retry_mode = "standard"
  }
  state_policy = {
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:ListBucket"], Resource = local.state_bucket_arn,
      Condition = merge(local.state_conditions, { StringEquals = merge(local.state_conditions.StringEquals, { "s3:prefix" = ["env:/"] }) }) },
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject"], Resource = "${local.state_bucket_arn}/${local.state_key}", Condition = local.state_conditions },
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], Resource = "${local.state_bucket_arn}/${local.state_key}.tflock", Condition = local.state_conditions }
    ]
  }
  # First speculative plan needs state reads and lock writes, not permission to
  # persist managed deployment state. Derive it from the same exact conditions.
  plan_policy = merge(local.state_policy, {
    Statement = [for i, s in local.state_policy.Statement : i == 1 ? merge(s, { Action = ["s3:GetObject"] }) : s]
  })
}
output "backend_configuration" {
  value     = local.backend
  sensitive = true
}
output "state_operator_policy" {
  value     = jsonencode(local.state_policy)
  sensitive = true
}
output "bootstrap_operator_policy" {
  value     = jsonencode(local.bootstrap_policy)
  sensitive = true
}
output "plan_operator_policy" {
  value     = jsonencode(local.plan_policy)
  sensitive = true
}
