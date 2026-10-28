resource "aws_iam_role" "host" {
  name = "${var.name}-host"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}
resource "aws_iam_instance_profile" "host" {
  name = "${var.name}-host"
  role = aws_iam_role.host.name
}
locals {
  host_policy = {
    Version = "2012-10-17"
    Statement = [
      { Sid = "InstanceHeartbeat", Effect = "Allow", Resource = aws_instance.host.arn, Action = ["ssm:UpdateInstanceInformation"] },
      { Sid = "MinimumSSMAgent", Effect = "Allow", Resource = "*", Action = [
        "ssmmessages:CreateControlChannel", "ssmmessages:CreateDataChannel",
        "ssmmessages:OpenControlChannel", "ssmmessages:OpenDataChannel"
      ] },
      { Sid = "ECRLogin", Effect = "Allow", Resource = "*", Action = ["ecr:GetAuthorizationToken"] },
      { Sid = "PinnedRepositories", Effect = "Allow", Resource = [for r in aws_ecr_repository.images : r.arn], Action = [
        "ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"
      ] },
      { Sid = "BackupLocation", Effect = "Allow", Resource = module.backups.arn, Action = ["s3:GetBucketLocation"] },
      { Sid = "BackupList", Effect = "Allow", Resource = module.backups.arn, Action = ["s3:ListBucket"],
      Condition = { StringLike = { "s3:prefix" = ["backups/*"] } } },
      { Sid = "BackupReadWrite", Effect = "Allow", Resource = "${module.backups.arn}/backups/*", Action = ["s3:PutObject", "s3:GetObject", "s3:GetObjectVersion"] }
    ]
  }
}
resource "aws_iam_role_policy" "host" {
  name   = "bounded-host"
  role   = aws_iam_role.host.id
  policy = jsonencode(local.host_policy)
}

resource "aws_ssm_document" "port" {
  name            = "${var.name}-loopback-8000"
  document_type   = "Session"
  document_format = "JSON"
  content = jsonencode({
    schemaVersion = "1.0", sessionType = "Port"
    description   = "Fixed local application port; no shell or remote host"
    properties    = { portNumber = "8000", localPortNumber = "8000" }
  })
}
resource "aws_ssm_document" "operate" {
  name            = "${var.name}-operate"
  document_type   = "Session"
  document_format = "JSON"
  content = jsonencode({
    schemaVersion = "1.0", sessionType = "InteractiveCommands"
    description   = "Fixed operational commands only; no arbitrary shell input"
    parameters = {
      Operation = { type = "String", allowedValues = ["prepare", "start", "stop", "verify", "backup"] }
    }
    properties = {
      linux = { commands = "/usr/bin/python3 /opt/fata/host.py {{ Operation }}", runAsElevated = true }
    }
  })
}
locals {
  operator_policy = {
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["ssm:StartSession"], Resource = [aws_instance.host.arn, aws_ssm_document.port.arn, aws_ssm_document.operate.arn],
      Condition = { Bool = { "ssm:SessionDocumentAccessCheck" = "true" } } },
      { Effect = "Allow", Action = ["ssm:GetDocument"], Resource = [aws_ssm_document.port.arn, aws_ssm_document.operate.arn] },
      { Effect = "Allow", Action = ["ssm:TerminateSession"], Resource = "arn:aws:ssm:us-east-1:${var.account_id}:session/*",
        # The documented tag is role-id:role-session-name. A trailing caller '*'
        # also matches another caller with a shared prefix; retain exact ownership.
        # If account evidence reveals another tag shape, stop for source review.
        Condition = { StringEquals = {
          "ssm:resourceTag/aws:ssmmessages:session-id" = "$${aws:userid}"
          "ssm:resourceTag/aws:ssmmessages:target-id"  = aws_instance.host.id
      } } },
      { Effect = "Allow", Action = ["ssmmessages:OpenDataChannel"], Resource = "*",
      Condition = { StringEquals = { "aws:RequestedRegion" = "us-east-1" } } }
    ]
  }
}
output "operator_policy" { value = jsonencode(local.operator_policy) }
output "instance_id" { value = aws_instance.host.id }
output "data_volume_id" { value = aws_ebs_volume.data.id }
output "backup_bucket" { value = module.backups.name }
