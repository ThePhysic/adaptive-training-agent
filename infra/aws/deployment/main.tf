locals {
  account_arn = "arn:aws:ec2:us-east-1:${var.account_id}"
  registry    = "${var.account_id}.dkr.ecr.us-east-1.amazonaws.com"
  bucket_name = "${var.name}-${var.account_id}-backups"
  config = {
    app_image      = "${local.registry}/${aws_ecr_repository.images["app"].name}@${var.app_digest}"
    postgres_image = "${local.registry}/${aws_ecr_repository.images["postgres"].name}@${var.postgres_digest}"
    registry       = local.registry, bucket = local.bucket_name
    volume_id      = aws_ebs_volume.data.id, host_tools_sha256 = var.host_tools_sha256
    starts_at      = var.starts_at, expires_at = var.expires_at
  }
  # Windows checkouts may use CRLF; cloud-init's shebang/shell must use LF.
  bootstrap = replace(templatefile("${path.module}/bootstrap.sh.tftpl", {
    config  = base64encode(jsonencode(local.config))
    host    = filebase64("${path.module}/../host/host.py")
    compose = filebase64("${path.module}/../../../compose.release.yaml")
  }), "\r\n", "\n")
}

resource "aws_vpc" "this" {
  cidr_block           = "10.77.0.0/24"
  enable_dns_support   = true
  enable_dns_hostnames = true
}
resource "aws_subnet" "this" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.77.0.0/26"
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = false
}
resource "aws_internet_gateway" "this" { vpc_id = aws_vpc.this.id }
resource "aws_route_table" "this" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
}
resource "aws_route_table_association" "this" {
  subnet_id      = aws_subnet.this.id
  route_table_id = aws_route_table.this.id
}
resource "aws_security_group" "host" {
  name_prefix = "${var.name}-"
  description = "No inbound rules; outbound TLS for attended SSM/ECR/S3 operations"
  vpc_id      = aws_vpc.this.id
  ingress     = []
  egress      = []
}
resource "aws_vpc_security_group_egress_rule" "https" {
  security_group_id = aws_security_group.host.id
  description       = "Host TLS only; app UID is separately loopback-fenced"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_ebs_volume" "data" {
  availability_zone = var.availability_zone
  type              = "gp3"
  size              = 32
  encrypted         = true
  tags              = { Name = "${var.name}-data", Retention = "explicit-reviewed-deletion" }
  lifecycle { prevent_destroy = true }
}
resource "aws_instance" "host" {
  ami                                  = var.ami_id
  instance_type                        = "t3.small"
  subnet_id                            = aws_subnet.this.id
  vpc_security_group_ids               = [aws_security_group.host.id]
  associate_public_ip_address          = true
  iam_instance_profile                 = aws_iam_instance_profile.host.name
  monitoring                           = false
  disable_api_termination              = true
  instance_initiated_shutdown_behavior = "stop"
  user_data_replace_on_change          = true
  user_data_base64                     = base64gzip(local.bootstrap)
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    http_protocol_ipv6          = "disabled"
    instance_metadata_tags      = "disabled"
  }
  credit_specification { cpu_credits = "standard" }
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 8
    encrypted             = true
    delete_on_termination = true
  }
  lifecycle {
    precondition {
      condition     = timecmp(var.starts_at, var.expires_at) < 0 && timecmp(var.expires_at, timeadd(var.starts_at, "24h")) <= 0
      error_message = "The attended window must be positive and no longer than 24 hours."
    }
  }
  depends_on = [aws_route_table_association.this]
}
resource "aws_volume_attachment" "data" {
  device_name                    = "/dev/sdf"
  volume_id                      = aws_ebs_volume.data.id
  instance_id                    = aws_instance.host.id
  force_detach                   = false
  stop_instance_before_detaching = true
}
resource "aws_ecr_repository" "images" {
  for_each             = toset(["app", "postgres"])
  name                 = "${var.name}/${each.key}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false
  encryption_configuration { encryption_type = "AES256" }
  lifecycle { prevent_destroy = true }
}
module "backups" {
  source           = "../modules/protected-bucket"
  name             = local.bucket_name
  backup_retention = true
}
