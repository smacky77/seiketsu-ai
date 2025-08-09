# Variables for Blue-Green Deployment Module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where resources will be created"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for the load balancer"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID for the Application Load Balancer"
  type        = string
}

variable "current_environment" {
  description = "Current active environment (blue or green)"
  type        = string
  default     = "blue"
  
  validation {
    condition     = contains(["blue", "green"], var.current_environment)
    error_message = "Current environment must be either 'blue' or 'green'."
  }
}

variable "target_environment" {
  description = "Target environment for deployment (blue or green)"
  type        = string
  default     = "green"
  
  validation {
    condition     = contains(["blue", "green"], var.target_environment)
    error_message = "Target environment must be either 'blue' or 'green'."
  }
}

variable "target_port" {
  description = "Port for the target group"
  type        = number
  default     = 8000
}

variable "listener_port" {
  description = "Port for the primary ALB listener"
  type        = number
  default     = 443
}

variable "test_listener_port" {
  description = "Port for the test ALB listener"
  type        = number
  default     = 8443
}

variable "listener_protocol" {
  description = "Protocol for ALB listeners"
  type        = string
  default     = "HTTPS"
}

variable "ssl_policy" {
  description = "SSL security policy for HTTPS listeners"
  type        = string
  default     = "ELBSecurityPolicy-TLS-1-2-2017-01"
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS listeners"
  type        = string
}

variable "health_check_path" {
  description = "Path for target group health checks"
  type        = string
  default     = "/health"
}

variable "health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 30
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
}

variable "health_check_healthy_threshold" {
  description = "Number of consecutive successful health checks required"
  type        = number
  default     = 2
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive failed health checks required"
  type        = number
  default     = 3
}

variable "health_check_matcher" {
  description = "HTTP response codes for successful health checks"
  type        = string
  default     = "200"
}

variable "deregistration_delay" {
  description = "Time to wait for connections to drain during deregistration"
  type        = number
  default     = 300
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for the load balancer"
  type        = bool
  default     = true
}

variable "enable_access_logs" {
  description = "Enable access logs for the load balancer"
  type        = bool
  default     = true
}

variable "access_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms"
  type        = string
  default     = null
}

variable "enable_stickiness" {
  description = "Enable session stickiness"
  type        = bool
  default     = false
}

variable "stickiness_duration" {
  description = "Duration for session stickiness in seconds"
  type        = number
  default     = 86400
}

variable "enable_http2" {
  description = "Enable HTTP/2 support"
  type        = bool
  default     = true
}

variable "enable_waf" {
  description = "Enable AWS WAF protection"
  type        = bool
  default     = true
}

variable "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  type        = string
  default     = ""
}

variable "deployment_timeout" {
  description = "Maximum time to wait for deployment completion in minutes"
  type        = number
  default     = 30
}

variable "rollback_timeout" {
  description = "Maximum time to wait for rollback completion in minutes"
  type        = number
  default     = 10
}

variable "canary_percentage" {
  description = "Percentage of traffic to route to new version during canary deployment"
  type        = number
  default     = 10
  
  validation {
    condition     = var.canary_percentage >= 0 && var.canary_percentage <= 100
    error_message = "Canary percentage must be between 0 and 100."
  }
}

variable "canary_duration" {
  description = "Duration to run canary deployment in minutes"
  type        = number
  default     = 10
}

variable "auto_rollback_enabled" {
  description = "Enable automatic rollback on deployment failure"
  type        = bool
  default     = true
}

variable "rollback_on_alarm" {
  description = "Enable rollback when CloudWatch alarms are triggered"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}