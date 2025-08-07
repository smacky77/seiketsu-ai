variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "rds_instance_arn" {
  description = "ARN of RDS instance to backup"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of S3 bucket to backup"
  type        = string
}

variable "backup_schedule" {
  description = "Cron expression for backup schedule"
  type        = string
  default     = "cron(0 2 * * ? *)"
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup for disaster recovery"
  type        = bool
  default     = true
}

variable "disaster_recovery_region" {
  description = "AWS region for disaster recovery backups"
  type        = string
  default     = "us-west-2"
}

variable "backup_notification_email" {
  description = "Email address for backup notifications"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}