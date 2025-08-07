# Seiketsu AI - Terraform Variables

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (prod, staging, dev)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "Environment must be prod, staging, or dev."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "seiketsu-ai"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "app.seiketsu.ai"
}

# API Keys and Secrets
variable "elevenlabs_api_key" {
  description = "ElevenLabs API key for voice synthesis"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key for AI processing"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT secret for authentication"
  type        = string
  sensitive   = true
}

variable "supabase_key" {
  description = "Supabase API key"
  type        = string
  sensitive   = true
}

variable "monitoring_api_key" {
  description = "21dev.ai monitoring API key"
  type        = string
  sensitive   = true
}

variable "monitoring_endpoint" {
  description = "21dev.ai monitoring endpoint URL"
  type        = string
  default     = "https://api.21dev.ai/metrics"
}

# Multi-tenant Configuration
variable "max_tenant_instances" {
  description = "Maximum number of tenant instances"
  type        = number
  default     = 40
}

variable "tenant_isolation_level" {
  description = "Level of tenant isolation (shared, dedicated, hybrid)"
  type        = string
  default     = "hybrid"
  
  validation {
    condition     = contains(["shared", "dedicated", "hybrid"], var.tenant_isolation_level)
    error_message = "Tenant isolation level must be shared, dedicated, or hybrid."
  }
}

# Performance Configuration
variable "voice_response_sla_ms" {
  description = "Voice response SLA in milliseconds"
  type        = number
  default     = 2000
}

variable "api_response_sla_ms" {
  description = "API response SLA in milliseconds"
  type        = number
  default     = 500
}

# Scaling Configuration
variable "auto_scaling_enabled" {
  description = "Enable auto-scaling for ECS services"
  type        = bool
  default     = true
}

variable "min_capacity" {
  description = "Minimum capacity for auto-scaling"
  type        = number
  default     = 2
}

variable "max_capacity" {
  description = "Maximum capacity for auto-scaling"
  type        = number
  default     = 40
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.2xlarge"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 1000
}

variable "db_backup_retention_period" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 30
}

# Cache Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.xlarge"
}

variable "redis_num_cache_clusters" {
  description = "Number of ElastiCache Redis clusters"
  type        = number
  default     = 3
}

# Security Configuration
variable "enable_encryption_at_rest" {
  description = "Enable encryption at rest for all resources"
  type        = bool
  default     = true
}

variable "enable_encryption_in_transit" {
  description = "Enable encryption in transit for all resources"
  type        = bool
  default     = true
}

variable "soc2_compliance_enabled" {
  description = "Enable SOC 2 compliance features"
  type        = bool
  default     = true
}

# Monitoring Configuration
variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for all resources"
  type        = bool
  default     = true
}

# Container Studio Configuration
variable "container_studio_enabled" {
  description = "Enable Container Studio integration"
  type        = bool
  default     = true
}

variable "container_orchestration_engine" {
  description = "Container orchestration engine (ecs, eks)"
  type        = string
  default     = "ecs"
  
  validation {
    condition     = contains(["ecs", "eks"], var.container_orchestration_engine)
    error_message = "Container orchestration engine must be ecs or eks."
  }
}

# 21dev.ai Integration
variable "monitoring_provider" {
  description = "Monitoring provider (21dev-ai, datadog, newrelic)"
  type        = string
  default     = "21dev-ai"
}

variable "alert_channels" {
  description = "Alert notification channels"
  type        = list(string)
  default     = ["slack", "email", "pagerduty"]
}

# Cost Optimization
variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = true
}

variable "use_spot_instances" {
  description = "Use spot instances for non-critical workloads"
  type        = bool  
  default     = true
}

variable "enable_scheduled_scaling" {
  description = "Enable scheduled scaling based on usage patterns"
  type        = bool
  default     = true
}