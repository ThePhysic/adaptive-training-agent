mock_provider "aws" {
  override_during = plan
  mock_resource "aws_s3_bucket" {
    defaults = { id = "fata-offline-state", arn = "arn:aws:s3:::fata-offline-state" }
  }
}
variables { name = "fata-offline-state" }
run "state_retention" {
  command = plan
  variables { backup_retention = false }
  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].status == "Enabled" && one(aws_s3_bucket_server_side_encryption_configuration.this.rule).apply_server_side_encryption_by_default[0].sse_algorithm == "AES256"
    error_message = "Versioned encrypted storage required."
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.this.block_public_acls && aws_s3_bucket_public_access_block.this.block_public_policy && aws_s3_bucket_public_access_block.this.ignore_public_acls && aws_s3_bucket_public_access_block.this.restrict_public_buckets && !aws_s3_bucket.this.force_destroy && length(aws_s3_bucket_lifecycle_configuration.backup) == 0
    error_message = "No public state, forced deletion or automatic state expiry."
  }
}
run "backup_retention" {
  command = plan
  variables { backup_retention = true }
  assert {
    condition     = length(aws_s3_bucket_lifecycle_configuration.backup) == 1 && jsondecode(aws_s3_bucket_policy.tls.policy).Statement[0].Effect == "Deny"
    error_message = "Backup cleanup and TLS-only policy required."
  }
}
