terraform {
  required_version = "= 1.17.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.70.0" }
  }
  backend "s3" {}
}
provider "aws" {
  region              = "us-east-1"
  allowed_account_ids = [var.account_id]
  default_tags {
    tags = {
      Project = var.name, WorkUnit = "F4-02", Data = "synthetic-only"
      Owner   = var.owner, ExpiresAt = var.expires_at
    }
  }
}
