output "database_password_arn" {
  description = "ARN of database password secret"
  value       = aws_secretsmanager_secret.database_password.arn
}

output "redis_auth_arn" {
  description = "ARN of Redis auth token secret"
  value       = aws_secretsmanager_secret.redis_auth.arn
}

output "elevenlabs_api_key_arn" {
  description = "ARN of ElevenLabs API key secret"
  value       = aws_secretsmanager_secret.elevenlabs_api_key.arn
}

output "openai_api_key_arn" {
  description = "ARN of OpenAI API key secret"
  value       = aws_secretsmanager_secret.openai_api_key.arn
}

output "jwt_secret_arn" {
  description = "ARN of JWT secret"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}

output "supabase_key_arn" {
  description = "ARN of Supabase key secret"
  value       = aws_secretsmanager_secret.supabase_key.arn
}

output "monitoring_api_key_arn" {
  description = "ARN of monitoring API key secret"
  value       = aws_secretsmanager_secret.monitoring_api_key.arn
}

output "database_url_arn" {
  description = "ARN of database connection string secret"
  value       = aws_secretsmanager_secret.database_url.arn
}

output "redis_url_arn" {
  description = "ARN of Redis connection string secret"
  value       = aws_secretsmanager_secret.redis_url.arn
}