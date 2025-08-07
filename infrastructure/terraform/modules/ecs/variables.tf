# ECS Module Variables

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where resources will be created"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for load balancer"
  type        = list(string)
}

variable "ecs_security_group" {
  description = "Security group ID for ECS tasks"
  type        = string
}

variable "alb_security_group" {
  description = "Security group ID for Application Load Balancer"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "container_studio_config" {
  description = "Container Studio configuration"
  type = object({
    orchestration_engine = string
    service_mesh        = string
    auto_scaling       = string
    health_checks      = string
  })
  default = {
    orchestration_engine = "ecs"
    service_mesh        = "enabled"
    auto_scaling       = "enabled"
    health_checks      = "comprehensive"
  }
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

variable "api_cpu" {
  description = "CPU units for API task"
  type        = number
  default     = 1024
}

variable "api_memory" {
  description = "Memory for API task"
  type        = number
  default     = 2048
}

variable "api_image_uri" {
  description = "Docker image URI for API"
  type        = string
  default     = "nginx:latest"  # Placeholder
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for HTTPS"
  type        = string
  default     = ""
}

variable "database_secret_arn" {
  description = "ARN of database secret"
  type        = string
}

variable "redis_secret_arn" {
  description = "ARN of Redis secret"
  type        = string
}

variable "openai_secret_arn" {
  description = "ARN of OpenAI API key secret"
  type        = string
}

variable "elevenlabs_secret_arn" {
  description = "ARN of ElevenLabs API key secret"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}