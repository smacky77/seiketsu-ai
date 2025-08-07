output "backup_vault_arn" {
  description = "ARN of the backup vault"
  value       = aws_backup_vault.main.arn
}

output "backup_vault_name" {
  description = "Name of the backup vault"
  value       = aws_backup_vault.main.name
}

output "backup_kms_key_arn" {
  description = "ARN of the backup KMS key"
  value       = aws_kms_key.backup.arn
}

output "daily_backup_plan_arn" {
  description = "ARN of the daily backup plan"
  value       = aws_backup_plan.daily.arn
}

output "weekly_backup_plan_arn" {
  description = "ARN of the weekly backup plan"
  value       = aws_backup_plan.weekly.arn
}

output "backup_exports_bucket_name" {
  description = "Name of the backup exports S3 bucket"
  value       = aws_s3_bucket.backup_exports.bucket
}

output "backup_alerts_topic_arn" {
  description = "ARN of the backup alerts SNS topic"
  value       = aws_sns_topic.backup_alerts.arn
}