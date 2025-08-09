# Terraform Backend Configuration for Remote State Management
# This file configures remote state storage in S3 with DynamoDB locking

terraform {
  backend "s3" {
    # S3 bucket for state storage
    bucket = "seiketsu-ai-terraform-state"
    region = "us-east-1"
    
    # DynamoDB table for state locking
    dynamodb_table = "seiketsu-ai-terraform-locks"
    
    # Encryption and versioning
    encrypt        = true
    versioning     = true
    
    # State file path (will be overridden by environment-specific configs)
    key = "default/terraform.tfstate"
    
    # Access control
    acl = "bucket-owner-full-control"
    
    # Server-side encryption
    server_side_encryption_configuration {
      rule {
        apply_server_side_encryption_by_default {
          kms_master_key_id = "alias/seiketsu-ai-terraform-state"
          sse_algorithm     = "aws:kms"
        }
      }
    }
  }
}

# Data source to check if backend resources exist
data "aws_s3_bucket" "terraform_state" {
  count  = var.create_backend_resources ? 0 : 1
  bucket = "seiketsu-ai-terraform-state"
}

data "aws_dynamodb_table" "terraform_locks" {
  count = var.create_backend_resources ? 0 : 1
  name  = "seiketsu-ai-terraform-locks"
}

# S3 bucket for Terraform state
resource "aws_s3_bucket" "terraform_state" {
  count  = var.create_backend_resources ? 1 : 0
  bucket = "seiketsu-ai-terraform-state"

  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "Seiketsu AI Terraform State"
    Purpose     = "Terraform State Storage"
    Environment = "global"
    Project     = "Seiketsu-AI"
  }
}

# Enable versioning for the S3 bucket
resource "aws_s3_bucket_versioning" "terraform_state_versioning" {
  count  = var.create_backend_resources ? 1 : 0
  bucket = aws_s3_bucket.terraform_state[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption for the S3 bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state_encryption" {
  count  = var.create_backend_resources ? 1 : 0
  bucket = aws_s3_bucket.terraform_state[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.terraform_state[0].arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# Block public access to the S3 bucket
resource "aws_s3_bucket_public_access_block" "terraform_state_pab" {
  count  = var.create_backend_resources ? 1 : 0
  bucket = aws_s3_bucket.terraform_state[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle configuration for the S3 bucket
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state_lifecycle" {
  count  = var.create_backend_resources ? 1 : 0
  bucket = aws_s3_bucket.terraform_state[0].id

  rule {
    id     = "delete_old_versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  rule {
    id     = "delete_incomplete_multipart_uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# KMS key for encrypting Terraform state
resource "aws_kms_key" "terraform_state" {
  count                   = var.create_backend_resources ? 1 : 0
  description             = "KMS key for Seiketsu AI Terraform state encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Terraform State Access"
        Effect = "Allow"
        Principal = {
          AWS = [
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/TerraformExecutionRole",
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/GithubActionsRole"
          ]
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "Seiketsu AI Terraform State KMS Key"
    Purpose     = "Terraform State Encryption"
    Environment = "global"
    Project     = "Seiketsu-AI"
  }
}

# KMS alias for the Terraform state key
resource "aws_kms_alias" "terraform_state" {
  count         = var.create_backend_resources ? 1 : 0
  name          = "alias/seiketsu-ai-terraform-state"
  target_key_id = aws_kms_key.terraform_state[0].key_id
}

# DynamoDB table for Terraform state locking
resource "aws_dynamodb_table" "terraform_locks" {
  count          = var.create_backend_resources ? 1 : 0
  name           = "seiketsu-ai-terraform-locks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.terraform_state[0].arn
  }

  tags = {
    Name        = "Seiketsu AI Terraform Locks"
    Purpose     = "Terraform State Locking"
    Environment = "global"
    Project     = "Seiketsu-AI"
  }
}

# IAM role for GitHub Actions to access Terraform state
resource "aws_iam_role" "github_actions" {
  count = var.create_backend_resources ? 1 : 0
  name  = "GithubActionsRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:seiketsu-ai/*:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "GitHub Actions Role"
    Purpose     = "CI/CD Pipeline Access"
    Environment = "global"
    Project     = "Seiketsu-AI"
  }
}

# IAM policy for GitHub Actions role
resource "aws_iam_role_policy" "github_actions_terraform" {
  count = var.create_backend_resources ? 1 : 0
  name  = "TerraformStateAccess"
  role  = aws_iam_role.github_actions[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.terraform_state[0].arn,
          "${aws_s3_bucket.terraform_state[0].arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.terraform_locks[0].arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.terraform_state[0].arn
      }
    ]
  })
}

# Output the backend configuration
output "terraform_backend_config" {
  value = {
    bucket         = var.create_backend_resources ? aws_s3_bucket.terraform_state[0].id : "seiketsu-ai-terraform-state"
    region         = var.aws_region
    dynamodb_table = var.create_backend_resources ? aws_dynamodb_table.terraform_locks[0].name : "seiketsu-ai-terraform-locks"
    encrypt        = true
    kms_key_id     = var.create_backend_resources ? aws_kms_key.terraform_state[0].arn : null
  }
  description = "Terraform backend configuration details"
}