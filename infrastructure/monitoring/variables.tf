# Seiketsu AI - Monitoring Module Variables

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

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}

variable "alert_email_addresses" {
  description = "List of email addresses for alerts"
  type        = list(string)
  default     = []
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "pagerduty_endpoint" {
  description = "PagerDuty endpoint for critical alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "monitoring_api_key" {
  description = "21dev.ai monitoring API key"
  type        = string
  sensitive   = true
}

variable "monitoring_config" {
  description = "Monitoring configuration"
  type = object({
    provider           = string
    metrics_endpoint   = string
    alert_channels     = list(string)
    performance_sla    = string
  })
  default = {
    provider           = "21dev-ai"
    metrics_endpoint   = "https://api.21dev.ai/metrics"
    alert_channels     = ["slack", "email"]
    performance_sla    = "sub-2s-voice-response"
  }
}

variable "performance_thresholds" {
  description = "Performance monitoring thresholds"
  type = object({
    voice_response_time = number
    api_response_time   = number
    database_query_time = number
  })
  default = {
    voice_response_time = 2000  # 2 seconds
    api_response_time   = 500   # 500ms
    database_query_time = 100   # 100ms
  }
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for all resources"
  type        = bool
  default     = true
}

variable "enable_xray_tracing" {
  description = "Enable AWS X-Ray tracing"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}