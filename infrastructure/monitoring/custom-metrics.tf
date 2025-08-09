# Seiketsu AI - Custom CloudWatch Metrics
# Performance and business metrics collection

# Voice Response Time Metrics
resource "aws_cloudwatch_log_metric_filter" "voice_response_time" {
  name           = "${var.name_prefix}-voice-response-time"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"VOICE_RESPONSE_TIME\", duration_ms=*]"

  metric_transformation {
    name      = "VoiceResponseTime"
    namespace = "Seiketsu/Performance"
    value     = "$duration_ms"
    unit      = "Milliseconds"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-voice-response-metric"
    Component   = "monitoring"
    MetricType  = "performance"
  }
}

# API Response Time Metrics
resource "aws_cloudwatch_log_metric_filter" "api_response_time" {
  name           = "${var.name_prefix}-api-response-time"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"API_RESPONSE_TIME\", duration_ms=*]"

  metric_transformation {
    name      = "APIResponseTime"
    namespace = "Seiketsu/Performance"
    value     = "$duration_ms"
    unit      = "Milliseconds"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-api-response-metric"
    Component   = "monitoring"
    MetricType  = "performance"
  }
}

# Database Query Performance
resource "aws_cloudwatch_log_metric_filter" "database_query_time" {
  name           = "${var.name_prefix}-database-query-time"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"DB_QUERY_TIME\", duration_ms=*]"

  metric_transformation {
    name      = "DatabaseQueryTime"
    namespace = "Seiketsu/Performance"
    value     = "$duration_ms"
    unit      = "Milliseconds"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-db-query-metric"
    Component   = "monitoring"
    MetricType  = "database"
  }
}

# Third-party API Latency (ElevenLabs)
resource "aws_cloudwatch_log_metric_filter" "elevenlabs_api_latency" {
  name           = "${var.name_prefix}-elevenlabs-latency"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"ELEVENLABS_API_TIME\", duration_ms=*]"

  metric_transformation {
    name      = "ElevenLabsAPILatency"
    namespace = "Seiketsu/Performance"
    value     = "$duration_ms"
    unit      = "Milliseconds"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-elevenlabs-metric"
    Component   = "monitoring"
    MetricType  = "third-party"
  }
}

# OpenAI API Latency
resource "aws_cloudwatch_log_metric_filter" "openai_api_latency" {
  name           = "${var.name_prefix}-openai-latency"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"OPENAI_API_TIME\", duration_ms=*]"

  metric_transformation {
    name      = "OpenAIAPILatency"
    namespace = "Seiketsu/Performance"
    value     = "$duration_ms"
    unit      = "Milliseconds"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-openai-metric"
    Component   = "monitoring"
    MetricType  = "third-party"
  }
}

# Tenant Request Metrics
resource "aws_cloudwatch_log_metric_filter" "tenant_requests" {
  name           = "${var.name_prefix}-tenant-requests"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"TENANT_REQUEST\", tenant_id=\"*\"]"

  metric_transformation {
    name      = "TenantRequests"
    namespace = "Seiketsu/MultiTenant"
    value     = "1"
    unit      = "Count"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-tenant-requests-metric"
    Component   = "monitoring"
    MetricType  = "business"
  }
}

# Voice Processing Success Rate
resource "aws_cloudwatch_log_metric_filter" "voice_success" {
  name           = "${var.name_prefix}-voice-success"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"VOICE_PROCESSING_SUCCESS\"]"

  metric_transformation {
    name      = "VoiceProcessingSuccess"
    namespace = "Seiketsu/Performance"
    value     = "1"
    unit      = "Count"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-voice-success-metric"
    Component   = "monitoring"
    MetricType  = "performance"
  }
}

# Voice Processing Errors
resource "aws_cloudwatch_log_metric_filter" "voice_errors" {
  name           = "${var.name_prefix}-voice-errors"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level=\"ERROR\", message=\"VOICE_PROCESSING_ERROR\"]"

  metric_transformation {
    name      = "VoiceProcessingErrors"
    namespace = "Seiketsu/Performance"
    value     = "1"
    unit      = "Count"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-voice-errors-metric"
    Component   = "monitoring"
    MetricType  = "errors"
  }
}

# Memory Usage Tracking
resource "aws_cloudwatch_log_metric_filter" "memory_usage" {
  name           = "${var.name_prefix}-memory-usage"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"MEMORY_USAGE\", memory_mb=*]"

  metric_transformation {
    name      = "ApplicationMemoryUsage"
    namespace = "Seiketsu/Performance"
    value     = "$memory_mb"
    unit      = "None"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-memory-usage-metric"
    Component   = "monitoring"
    MetricType  = "resource"
  }
}

# Concurrent Voice Requests
resource "aws_cloudwatch_log_metric_filter" "concurrent_voice_requests" {
  name           = "${var.name_prefix}-concurrent-voice"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"CONCURRENT_VOICE_REQUESTS\", count=*]"

  metric_transformation {
    name      = "ConcurrentVoiceRequests"
    namespace = "Seiketsu/Performance"
    value     = "$count"
    unit      = "Count"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-concurrent-voice-metric"
    Component   = "monitoring"
    MetricType  = "performance"
  }
}

# Business Metrics: Active Tenants
resource "aws_cloudwatch_log_metric_filter" "active_tenants" {
  name           = "${var.name_prefix}-active-tenants"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"ACTIVE_TENANTS\", count=*]"

  metric_transformation {
    name      = "ActiveTenants"
    namespace = "Seiketsu/MultiTenant"
    value     = "$count"
    unit      = "Count"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-active-tenants-metric"
    Component   = "monitoring"
    MetricType  = "business"
  }
}

# Cache Hit Rate
resource "aws_cloudwatch_log_metric_filter" "cache_hit_rate" {
  name           = "${var.name_prefix}-cache-hit-rate"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"CACHE_HIT\", hit=*]"

  metric_transformation {
    name      = "CacheHitRate"
    namespace = "Seiketsu/Performance"
    value     = "$hit"
    unit      = "Percent"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-cache-hit-metric"
    Component   = "monitoring"
    MetricType  = "performance"
  }
}

# Cost Tracking: API Call Costs
resource "aws_cloudwatch_log_metric_filter" "api_costs" {
  name           = "${var.name_prefix}-api-costs"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id=\"*\", level, message=\"API_COST\", cost_cents=*]"

  metric_transformation {
    name      = "APICosts"
    namespace = "Seiketsu/Cost"
    value     = "$cost_cents"
    unit      = "None"
    
    default_value = 0
  }

  tags = {
    Name        = "${var.name_prefix}-api-costs-metric"
    Component   = "monitoring"
    MetricType  = "cost"
  }
}