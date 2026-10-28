mock_provider "aws" {
  override_during = plan
  mock_resource "aws_ecr_repository" {
    defaults = { arn = "arn:aws:ecr:us-east-1:000000000000:repository/fata-offline/app" }
  }
  mock_resource "aws_instance" {
    defaults = { id = "i-00000000000000000", arn = "arn:aws:ec2:us-east-1:000000000000:instance/i-00000000000000000" }
  }
  mock_resource "aws_s3_bucket" {
    defaults = { id = "fata-offline-000000000000-backups", arn = "arn:aws:s3:::fata-offline-000000000000-backups" }
  }
  mock_resource "aws_ebs_volume" { defaults = { id = "vol-00000000000000000" } }
}
variables {
  account_id        = "000000000000"
  name              = "fata-offline"
  owner             = "synthetic-operator"
  availability_zone = "us-east-1a"
  ami_id            = "ami-00000000000000000"
  host_tools_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
  app_digest        = "sha256:1111111111111111111111111111111111111111111111111111111111111111"
  postgres_digest   = "sha256:2222222222222222222222222222222222222222222222222222222222222222"
  starts_at         = "2030-01-01T00:00:00Z"
  expires_at        = "2030-01-02T00:00:00Z"
}
run "bounded_network_storage_identity" {
  command = plan
  assert {
    condition     = length(aws_security_group.host.ingress) == 0 && length(aws_security_group.host.egress) == 0 && aws_vpc_security_group_egress_rule.https.to_port == 443
    error_message = "No public application, SSH or database ingress is permitted."
  }
  assert {
    condition     = aws_instance.host.instance_type == "t3.small" && aws_instance.host.metadata_options[0].http_tokens == "required" && aws_instance.host.metadata_options[0].http_put_response_hop_limit == 1 && aws_instance.host.metadata_options[0].http_protocol_ipv6 == "disabled"
    error_message = "Fixed instance type and IMDS safeguards required."
  }
  assert {
    condition     = aws_ebs_volume.data.encrypted && aws_ebs_volume.data.size == 32 && aws_instance.host.root_block_device[0].encrypted && aws_instance.host.root_block_device[0].volume_size == 8 && !aws_volume_attachment.data.force_detach
    error_message = "Encrypted 40 GB total and safe detach required."
  }
  assert {
    condition     = aws_instance.host.credit_specification[0].cpu_credits == "standard" && aws_instance.host.disable_api_termination && aws_instance.host.instance_initiated_shutdown_behavior == "stop"
    error_message = "Bounded credits and operator-controlled teardown required."
  }
  assert {
    condition     = jsondecode(aws_ssm_document.port.content).properties.portNumber == "8000" && jsondecode(aws_ssm_document.port.content).sessionType == "Port"
    error_message = "Only fixed local port forwarding is permitted."
  }
  assert {
    condition     = toset(jsondecode(aws_ssm_document.operate.content).parameters.Operation.allowedValues) == toset(["prepare", "start", "stop", "verify", "backup"])
    error_message = "Recovery must use the fixed preparation operation, never an arbitrary shell."
  }
  assert {
    condition     = length([for s in local.host_policy.Statement : s if s.Resource == "*"]) == 2 && !strcontains(jsonencode(local.host_policy), "DeleteObject") && !strcontains(jsonencode(local.host_policy), "secretsmanager")
    error_message = "Only documented resource-less SSM/ECR actions can use wildcard resources."
  }
  assert {
    condition = toset(flatten([for s in local.host_policy.Statement : s.Action])) == toset([
      "ssm:UpdateInstanceInformation", "ssmmessages:CreateControlChannel", "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel", "ssmmessages:OpenDataChannel", "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage",
      "s3:GetBucketLocation", "s3:ListBucket", "s3:PutObject", "s3:GetObject", "s3:GetObjectVersion"
    ])
    error_message = "No IAM, administrator, deletion or unrelated service authority is permitted."
  }
  assert {
    condition     = toset(flatten([for s in local.operator_policy.Statement : s.Action])) == toset(["ssm:StartSession", "ssm:GetDocument", "ssm:TerminateSession", "ssmmessages:OpenDataChannel"])
    error_message = "Operator cannot use arbitrary shell documents or pass roles."
  }
  assert {
    condition     = local.operator_policy.Statement[0].Condition.Bool["ssm:SessionDocumentAccessCheck"] == "true" && local.operator_policy.Statement[2].Condition.StringEquals["ssm:resourceTag/aws:ssmmessages:session-id"] == "$${aws:userid}" && local.operator_policy.Statement[2].Condition.StringEquals["ssm:resourceTag/aws:ssmmessages:target-id"] == aws_instance.host.id
    error_message = "Require document access and caller/target-bound session termination for federated operators."
  }
  assert {
    condition     = length(aws_instance.host.user_data_base64) * 3 / 4 <= 16384
    error_message = "Compressed bootstrap must fit the EC2 user data limit."
  }
  assert {
    condition     = startswith(local.bootstrap, "#!/bin/bash\n") && !strcontains(local.bootstrap, "\r")
    error_message = "Cloud-init shell must be LF-normalized even from a Windows checkout."
  }
}
run "mutable_image_rejected" {
  command = plan
  variables { app_digest = "latest" }
  expect_failures = [var.app_digest]
}
run "federated_termination_structural_cases" {
  command = plan
  # Only this statement's resource/action/string constraints, not AWS IAM evaluation.
  assert {
    condition = alltrue([for c in jsondecode(file("${path.module}/tests/termination-cases.json")) : (
      contains(local.operator_policy.Statement[2].Action, c.action) &&
      can(regex("^${replace(local.operator_policy.Statement[2].Resource, "*", "[^/]+")}$", c.resource)) &&
      c.tag == replace(local.operator_policy.Statement[2].Condition.StringEquals["ssm:resourceTag/aws:ssmmessages:session-id"], "$${aws:userid}", c.caller) &&
      c.target == local.operator_policy.Statement[2].Condition.StringEquals["ssm:resourceTag/aws:ssmmessages:target-id"]
    ) == c.allowed])
    error_message = "Exact federated owner, instance, region, account and action boundaries must hold."
  }
}
run "wrong_region_rejected" {
  command = plan
  variables { availability_zone = "us-west-2a" }
  expect_failures = [var.availability_zone]
}
run "overlong_window_rejected" {
  command = plan
  variables { expires_at = "2030-01-03T00:00:00Z" }
  expect_failures = [aws_instance.host]
}
