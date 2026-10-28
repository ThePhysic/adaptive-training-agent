variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "An explicitly approved account ID is required."
  }
}
variable "name" {
  type = string
  validation {
    condition     = can(regex("^fata-[a-z0-9-]{3,24}$", var.name))
    error_message = "Use a short fata- prefixed synthetic deployment name."
  }
}
variable "owner" {
  type = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{1,32}$", var.owner))
    error_message = "Use an opaque operator label, not PII."
  }
}
variable "availability_zone" {
  type = string
  validation {
    condition     = can(regex("^us-east-1[a-f]$", var.availability_zone))
    error_message = "Select an approved us-east-1 AZ."
  }
}
variable "ami_id" {
  type = string
  validation {
    condition     = can(regex("^ami-[0-9a-f]{17}$", var.ami_id))
    error_message = "Pin a reviewed Linux x86_64 AMI; no latest lookup."
  }
}
variable "host_tools_sha256" {
  type = string
  validation {
    condition     = can(regex("^[0-9a-f]{64}$", var.host_tools_sha256))
    error_message = "Pin the reviewed host tools manifest hash."
  }
}
variable "app_digest" {
  type = string
  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.app_digest))
    error_message = "Application must be pinned by ECR digest, never a mutable tag."
  }
}
variable "postgres_digest" {
  type = string
  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.postgres_digest))
    error_message = "Pin the separately verified PostgreSQL 18.6 mirror digest."
  }
}
variable "starts_at" {
  type = string
  validation {
    condition     = can(regex("Z$", var.starts_at)) && can(formatdate("YYYY", var.starts_at))
    error_message = "An explicit UTC execution window is required."
  }
}
variable "expires_at" {
  type = string
  validation {
    condition     = can(regex("Z$", var.expires_at)) && can(formatdate("YYYY", var.expires_at))
    error_message = "An explicit UTC expiration is required."
  }
}
