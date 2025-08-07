# Seiketsu AI - Secrets Manager Module
# Centralized secrets management with rotation

# Database Password Secret
resource "aws_secretsmanager_secret" "database_password" {
  name                    = "${var.name_prefix}/database/password"
  description             = "Database password for ${var.name_prefix}"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-password"
    Type = "database-credential"
  })
}

resource "aws_secretsmanager_secret_version" "database_password" {
  secret_id     = aws_secretsmanager_secret.database_password.id
  secret_string = var.secrets.database_password
}

# Redis Auth Token Secret
resource "aws_secretsmanager_secret" "redis_auth" {
  name                    = "${var.name_prefix}/redis/auth-token"
  description             = "Redis auth token for ${var.name_prefix}"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis-auth"
    Type = "cache-credential"
  })
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id     = aws_secretsmanager_secret.redis_auth.id
  secret_string = var.secrets.redis_auth_token
}

# ElevenLabs API Key Secret
resource "aws_secretsmanager_secret" "elevenlabs_api_key" {
  name                    = "${var.name_prefix}/api-keys/elevenlabs"
  description             = "ElevenLabs API key for voice synthesis"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-elevenlabs-key"
    Type = "api-key"
  })
}

resource "aws_secretsmanager_secret_version" "elevenlabs_api_key" {
  secret_id     = aws_secretsmanager_secret.elevenlabs_api_key.id
  secret_string = var.secrets.elevenlabs_api_key
}

# OpenAI API Key Secret
resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${var.name_prefix}/api-keys/openai"
  description             = "OpenAI API key for AI processing"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-openai-key"
    Type = "api-key"
  })
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.secrets.openai_api_key
}

# JWT Secret
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${var.name_prefix}/auth/jwt-secret"
  description             = "JWT secret for authentication"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-jwt-secret"
    Type = "auth-credential"
  })
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.secrets.jwt_secret
}

# Supabase Key Secret
resource "aws_secretsmanager_secret" "supabase_key" {
  name                    = "${var.name_prefix}/api-keys/supabase"
  description             = "Supabase API key"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-supabase-key"
    Type = "api-key"
  })
}

resource "aws_secretsmanager_secret_version" "supabase_key" {
  secret_id     = aws_secretsmanager_secret.supabase_key.id
  secret_string = var.secrets.supabase_key
}

# Monitoring API Key Secret
resource "aws_secretsmanager_secret" "monitoring_api_key" {
  name                    = "${var.name_prefix}/api-keys/monitoring"
  description             = "21dev.ai monitoring API key"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-monitoring-key"
    Type = "api-key"
  })
}

resource "aws_secretsmanager_secret_version" "monitoring_api_key" {
  secret_id     = aws_secretsmanager_secret.monitoring_api_key.id
  secret_string = var.secrets.monitoring_api_key
}

# Database Connection String Secret
resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${var.name_prefix}/database/connection-string"
  description             = "Database connection string"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-connection"
    Type = "database-credential"
  })
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = aws_secretsmanager_secret.database_url.id
  secret_string = jsonencode({
    host     = var.database_host
    port     = var.database_port
    dbname   = var.database_name
    username = var.database_username
    password = var.secrets.database_password
    url      = "postgresql://${var.database_username}:${var.secrets.database_password}@${var.database_host}:${var.database_port}/${var.database_name}"
  })
}

# Redis Connection String Secret
resource "aws_secretsmanager_secret" "redis_url" {
  name                    = "${var.name_prefix}/redis/connection-string"
  description             = "Redis connection string"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis-connection"
    Type = "cache-credential"
  })
}

resource "aws_secretsmanager_secret_version" "redis_url" {
  secret_id = aws_secretsmanager_secret.redis_url.id
  secret_string = jsonencode({
    host     = var.redis_host
    port     = var.redis_port
    password = var.secrets.redis_auth_token
    url      = "redis://:${var.secrets.redis_auth_token}@${var.redis_host}:${var.redis_port}"
  })
}