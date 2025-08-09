# Seiketsu AI - Auto-scaling Module Variables

variable "name_prefix" {
  description = "Name prefix for all resources"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# ECS Auto-scaling Variables
variable "cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "service_name" {
  description = "ECS service name"
  type        = string
}

variable "min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 2
}

variable "max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 40
}

variable "enable_scheduled_scaling" {
  description = "Enable scheduled scaling policies"
  type        = bool
  default     = true
}

variable "enable_predictive_scaling" {
  description = "Enable predictive scaling (if supported in region)"
  type        = bool
  default     = false
}

variable "alb_arn_suffix" {
  description = "Application Load Balancer ARN suffix"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix"
  type        = string
}

variable "asg_name" {
  description = "Auto Scaling Group name for ECS cluster"
  type        = string
}

variable "tenants_per_instance" {
  description = "Target number of tenants per ECS instance"
  type        = number
  default     = 2
}

variable "max_concurrent_voice_requests" {
  description = "Maximum concurrent voice requests per instance"
  type        = number
  default     = 10
}

# Database Auto-scaling Variables
variable "enable_aurora_scaling" {
  description = "Enable Aurora auto-scaling"
  type        = bool
  default     = true
}

variable "aurora_cluster_identifier" {
  description = "Aurora cluster identifier"
  type        = string
}

variable "aurora_min_read_replicas" {
  description = "Minimum number of Aurora read replicas"
  type        = number
  default     = 1
}

variable "aurora_max_read_replicas" {
  description = "Maximum number of Aurora read replicas"
  type        = number
  default     = 5
}

variable "tenants_per_read_replica" {
  description = "Target number of tenants per read replica"
  type        = number
  default     = 10
}

variable "enable_aurora_serverless" {
  description = "Enable Aurora Serverless v2"
  type        = bool
  default     = false
}

variable "aurora_serverless_min_capacity" {
  description = "Aurora Serverless minimum capacity"
  type        = number
  default     = 0.5
}

variable "aurora_serverless_max_capacity" {
  description = "Aurora Serverless maximum capacity"
  type        = number
  default     = 16
}

variable "aurora_engine_version" {
  description = "Aurora engine version"
  type        = string
  default     = "8.0.mysql_aurora.3.02.0"
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "seiketsu"
}

variable "database_username" {
  description = "Database username"
  type        = string
  default     = "admin"
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "database_security_group_id" {
  description = "Database security group ID"
  type        = string
}

variable "db_subnet_group_name" {
  description = "DB subnet group name"
  type        = string
}

variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 30
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for Aurora cluster"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
  default     = ""
}

# ElastiCache Auto-scaling Variables
variable "enable_elasticache_scaling" {
  description = "Enable ElastiCache auto-scaling"
  type        = bool
  default     = true
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "redis_initial_cache_clusters" {
  description = "Initial number of Redis cache clusters"
  type        = number
  default     = 2
}

variable "redis_min_cache_clusters" {
  description = "Minimum number of Redis cache clusters"
  type        = number
  default     = 1
}

variable "redis_max_cache_clusters" {
  description = "Maximum number of Redis cache clusters"
  type        = number
  default     = 6
}

variable "redis_auth_token" {
  description = "Redis authentication token"
  type        = string
  sensitive   = true
}

variable "cache_subnet_group_name" {
  description = "Cache subnet group name"
  type        = string
}

variable "cache_security_group_id" {
  description = "Cache security group ID"
  type        = string
}

# Cost Optimization Variables
variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = true
}

variable "cost_optimization_schedule" {
  description = "Schedule for cost optimization tasks"
  type        = string
  default     = "cron(0 2 * * ? *)"
}

# Performance Thresholds
variable "cpu_scale_up_threshold" {
  description = "CPU utilization threshold for scaling up"
  type        = number
  default     = 70
}

variable "memory_scale_up_threshold" {
  description = "Memory utilization threshold for scaling up"
  type        = number
  default     = 80
}

variable "voice_response_time_threshold" {
  description = "Voice response time threshold for scaling (ms)"
  type        = number
  default     = 1800
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}