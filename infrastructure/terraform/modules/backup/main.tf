# Seiketsu AI - Backup and Disaster Recovery Module
# Automated backups for RDS, S3, and EFS

# AWS Backup Vault
resource "aws_backup_vault" "main" {
  name        = "${var.name_prefix}-backup-vault"
  kms_key_arn = aws_kms_key.backup.arn

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-backup-vault"
    Component = "backup"
  })
}

# KMS Key for Backup Encryption
resource "aws_kms_key" "backup" {
  description             = "KMS key for ${var.name_prefix} backups"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-backup-key"
    Component = "encryption"
  })
}

resource "aws_kms_alias" "backup" {
  name          = "alias/${var.name_prefix}-backup"
  target_key_id = aws_kms_key.backup.key_id
}

# IAM Role for AWS Backup
resource "aws_iam_role" "backup" {
  name = "${var.name_prefix}-backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Attach AWS managed backup policy
resource "aws_iam_role_policy_attachment" "backup" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "backup_restore" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

# Daily Backup Plan
resource "aws_backup_plan" "daily" {
  name = "${var.name_prefix}-daily-backup"

  rule {
    rule_name         = "daily_backup_rule"
    target_vault_name = aws_backup_vault.main.name
    schedule          = var.backup_schedule
    start_window      = 120  # 2 hours
    completion_window = 300  # 5 hours

    lifecycle {
      cold_storage_after = 30
      delete_after       = 365
    }

    recovery_point_tags = merge(var.tags, {
      BackupType = "daily"
    })
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-daily-backup-plan"
    Component = "backup"
  })
}

# Weekly Backup Plan
resource "aws_backup_plan" "weekly" {
  name = "${var.name_prefix}-weekly-backup"

  rule {
    rule_name         = "weekly_backup_rule"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 3 ? * SUN *)"
    start_window      = 120
    completion_window = 480  # 8 hours for weekly

    lifecycle {
      cold_storage_after = 30
      delete_after       = 730  # 2 years
    }

    recovery_point_tags = merge(var.tags, {
      BackupType = "weekly"
    })
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-weekly-backup-plan"
    Component = "backup"
  })
}

# Backup Selection for RDS
resource "aws_backup_selection" "rds" {
  iam_role_arn = aws_iam_role.backup.arn
  name         = "${var.name_prefix}-rds-backup-selection"
  plan_id      = aws_backup_plan.daily.id

  resources = [
    var.rds_instance_arn
  ]

  condition {
    string_equals {
      key   = "aws:ResourceTag/BackupEnabled"
      value = "true"
    }
  }
}

# Backup Selection for S3
resource "aws_backup_selection" "s3" {
  iam_role_arn = aws_iam_role.backup.arn
  name         = "${var.name_prefix}-s3-backup-selection"
  plan_id      = aws_backup_plan.weekly.id

  resources = [
    var.s3_bucket_arn
  ]

  condition {
    string_equals {
      key   = "aws:ResourceTag/BackupEnabled"
      value = "true"
    }
  }
}

# Cross-Region Backup for Disaster Recovery
resource "aws_backup_vault" "dr" {
  count       = var.enable_cross_region_backup ? 1 : 0
  name        = "${var.name_prefix}-dr-backup-vault"
  kms_key_arn = aws_kms_key.backup.arn
  
  provider = aws.disaster_recovery

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-dr-backup-vault"
    Component = "disaster-recovery"
  })
}

# Backup Plan for Cross-Region Disaster Recovery
resource "aws_backup_plan" "disaster_recovery" {
  count = var.enable_cross_region_backup ? 1 : 0
  name  = "${var.name_prefix}-dr-backup"
  
  provider = aws.disaster_recovery

  rule {
    rule_name         = "disaster_recovery_rule"
    target_vault_name = aws_backup_vault.dr[0].name
    schedule          = "cron(0 6 ? * SUN *)"
    start_window      = 120
    completion_window = 480

    copy_action {
      destination_vault_arn = aws_backup_vault.dr[0].arn
      
      lifecycle {
        cold_storage_after = 30
        delete_after       = 365
      }
    }

    lifecycle {
      delete_after = 30  # Keep local copies for 30 days
    }

    recovery_point_tags = merge(var.tags, {
      BackupType = "disaster-recovery"
    })
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-dr-backup-plan"
    Component = "disaster-recovery"
  })
}

# CloudWatch Alarm for Backup Failures
resource "aws_cloudwatch_metric_alarm" "backup_failure" {
  alarm_name          = "${var.name_prefix}-backup-failure"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "NumberOfBackupJobsFailed"
  namespace           = "AWS/Backup"
  period              = "86400"  # 24 hours
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors backup job failures"
  alarm_actions       = [aws_sns_topic.backup_alerts.arn]

  dimensions = {
    BackupVaultName = aws_backup_vault.main.name
  }

  tags = var.tags
}

# SNS Topic for Backup Alerts
resource "aws_sns_topic" "backup_alerts" {
  name = "${var.name_prefix}-backup-alerts"

  tags = var.tags
}

# SNS Topic Subscription for Email Alerts
resource "aws_sns_topic_subscription" "backup_email" {
  count     = var.backup_notification_email != null ? 1 : 0
  topic_arn = aws_sns_topic.backup_alerts.arn
  protocol  = "email"
  endpoint  = var.backup_notification_email
}

# S3 Bucket for Backup Exports (for compliance)
resource "aws_s3_bucket" "backup_exports" {
  bucket = "${var.name_prefix}-backup-exports-${random_string.backup_suffix.result}"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-backup-exports"
    Component = "backup-export"
  })
}

resource "random_string" "backup_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_versioning" "backup_exports" {
  bucket = aws_s3_bucket.backup_exports.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backup_exports" {
  bucket = aws_s3_bucket.backup_exports.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.backup.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "backup_exports" {
  bucket = aws_s3_bucket.backup_exports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for backup exports
resource "aws_s3_bucket_lifecycle_configuration" "backup_exports" {
  bucket = aws_s3_bucket.backup_exports.id

  rule {
    id     = "backup_exports_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555  # 7 years for compliance
    }
  }
}