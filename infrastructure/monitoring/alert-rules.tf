# Seiketsu AI - CloudWatch Alert Rules
# Comprehensive alerting for performance, infrastructure, and business metrics

# Critical Performance Alerts
resource "aws_cloudwatch_metric_alarm" "voice_response_sla_breach" {
  alarm_name          = "${var.name_prefix}-voice-response-sla-breach"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "VoiceResponseTime"
  namespace           = "Seiketsu/Performance"
  period              = "300"
  statistic           = "Average"
  threshold           = "2000"
  alarm_description   = "Voice response time exceeds 2 second SLA"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  ok_actions          = [aws_sns_topic.critical_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.name_prefix}-voice-sla-alarm"
    Component   = "monitoring"
    Severity    = "critical"
    SLA         = "voice-response"
  }
}

resource "aws_cloudwatch_metric_alarm" "api_response_sla_breach" {
  alarm_name          = "${var.name_prefix}-api-response-sla-breach"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "APIResponseTime"
  namespace           = "Seiketsu/Performance"
  period              = "300"
  statistic           = "Average"
  threshold           = "500"
  alarm_description   = "API response time exceeds 500ms SLA"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]
  ok_actions          = [aws_sns_topic.performance_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.name_prefix}-api-sla-alarm"
    Component   = "monitoring"
    Severity    = "high"
    SLA         = "api-response"
  }
}

# Infrastructure Scaling Alerts
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  alarm_name          = "${var.name_prefix}-ecs-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "70"
  alarm_description   = "ECS CPU utilization is high - scaling trigger"
  alarm_actions       = [aws_sns_topic.infrastructure_alerts.arn]
  ok_actions          = [aws_sns_topic.infrastructure_alerts.arn]

  dimensions = {
    ServiceName = "${var.name_prefix}-api-service"
    ClusterName = "${var.name_prefix}-cluster"
  }

  tags = {
    Name        = "${var.name_prefix}-ecs-cpu-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "scaling"
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory_high" {
  alarm_name          = "${var.name_prefix}-ecs-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "ECS memory utilization is high - scaling trigger"
  alarm_actions       = [aws_sns_topic.infrastructure_alerts.arn]
  ok_actions          = [aws_sns_topic.infrastructure_alerts.arn]

  dimensions = {
    ServiceName = "${var.name_prefix}-api-service"
    ClusterName = "${var.name_prefix}-cluster"
  }

  tags = {
    Name        = "${var.name_prefix}-ecs-memory-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "scaling"
  }
}

# Database Performance Alerts
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${var.name_prefix}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "RDS CPU utilization is high"
  alarm_actions       = [aws_sns_topic.infrastructure_alerts.arn]

  dimensions = {
    DBInstanceIdentifier = "${var.name_prefix}-database"
  }

  tags = {
    Name        = "${var.name_prefix}-rds-cpu-alarm"
    Component   = "monitoring"
    Severity    = "high"
    Type        = "database"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  alarm_name          = "${var.name_prefix}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "RDS connection count is high (80% of max)"
  alarm_actions       = [aws_sns_topic.infrastructure_alerts.arn]

  dimensions = {
    DBInstanceIdentifier = "${var.name_prefix}-database"
  }

  tags = {
    Name        = "${var.name_prefix}-rds-connections-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "database"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_read_latency_high" {
  alarm_name          = "${var.name_prefix}-rds-read-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ReadLatency"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "0.1"
  alarm_description   = "RDS read latency is high (>100ms)"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]

  dimensions = {
    DBInstanceIdentifier = "${var.name_prefix}-database"
  }

  tags = {
    Name        = "${var.name_prefix}-rds-read-latency-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "performance"
  }
}

# Load Balancer Health Alerts
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_targets" {
  alarm_name          = "${var.name_prefix}-alb-unhealthy-targets"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "ALB has no healthy targets"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  treat_missing_data  = "breaching"

  tags = {
    Name        = "${var.name_prefix}-alb-health-alarm"
    Component   = "monitoring"
    Severity    = "critical"
    Type        = "availability"
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_response_time_high" {
  alarm_name          = "${var.name_prefix}-alb-response-time-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "1.0"
  alarm_description   = "ALB target response time is high (>1s)"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]

  tags = {
    Name        = "${var.name_prefix}-alb-response-time-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "performance"
  }
}

# Error Rate Alerts
resource "aws_cloudwatch_metric_alarm" "voice_error_rate_high" {
  alarm_name          = "${var.name_prefix}-voice-error-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  
  metric_query {
    id = "e1"
    return_data = true
    
    metric {
      metric_name = "VoiceProcessingErrors"
      namespace   = "Seiketsu/Performance"
      period      = 300
      stat        = "Sum"
    }
  }
  
  metric_query {
    id = "m1"
    return_data = false
    
    metric {
      metric_name = "VoiceProcessingSuccess"
      namespace   = "Seiketsu/Performance"
      period      = 300
      stat        = "Sum"
    }
  }
  
  metric_query {
    id          = "error_rate"
    expression  = "e1 / (e1 + m1) * 100"
    label       = "Voice Error Rate"
    return_data = true
  }

  threshold           = "5"
  alarm_description   = "Voice processing error rate exceeds 5%"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.name_prefix}-voice-error-rate-alarm"
    Component   = "monitoring"
    Severity    = "high"
    Type        = "error-rate"
  }
}

# Cost Alerts
resource "aws_cloudwatch_metric_alarm" "estimated_charges_high" {
  alarm_name          = "${var.name_prefix}-estimated-charges-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = "86400"
  statistic           = "Maximum"
  threshold           = "1000"
  alarm_description   = "Estimated monthly charges exceed $1000"
  alarm_actions       = [aws_sns_topic.cost_alerts.arn]

  dimensions = {
    Currency = "USD"
  }

  tags = {
    Name        = "${var.name_prefix}-cost-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "cost"
  }
}

# Third-party API Alerts
resource "aws_cloudwatch_metric_alarm" "elevenlabs_api_slow" {
  alarm_name          = "${var.name_prefix}-elevenlabs-api-slow"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ElevenLabsAPILatency"
  namespace           = "Seiketsu/Performance"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000"
  alarm_description   = "ElevenLabs API response time is high (>5s)"
  alarm_actions       = [aws_sns_topic.third_party_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.name_prefix}-elevenlabs-slow-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "third-party"
  }
}

resource "aws_cloudwatch_metric_alarm" "openai_api_slow" {
  alarm_name          = "${var.name_prefix}-openai-api-slow"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "OpenAIAPILatency"
  namespace           = "Seiketsu/Performance"
  period              = "300"
  statistic           = "Average"
  threshold           = "10000"
  alarm_description   = "OpenAI API response time is high (>10s)"
  alarm_actions       = [aws_sns_topic.third_party_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.name_prefix}-openai-slow-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "third-party"
  }
}

# Multi-tenant Alerts
resource "aws_cloudwatch_metric_alarm" "tenant_capacity_warning" {
  alarm_name          = "${var.name_prefix}-tenant-capacity-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ActiveTenants"
  namespace           = "Seiketsu/MultiTenant"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "35"
  alarm_description   = "Active tenant count approaching capacity limit (35/40)"
  alarm_actions       = [aws_sns_topic.capacity_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.name_prefix}-tenant-capacity-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "capacity"
  }
}

# Cache Performance Alerts
resource "aws_cloudwatch_metric_alarm" "redis_cpu_high" {
  alarm_name          = "${var.name_prefix}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "75"
  alarm_description   = "Redis CPU utilization is high"
  alarm_actions       = [aws_sns_topic.infrastructure_alerts.arn]

  dimensions = {
    CacheClusterId = "${var.name_prefix}-redis"
  }

  tags = {
    Name        = "${var.name_prefix}-redis-cpu-alarm"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "cache"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory_high" {
  alarm_name          = "${var.name_prefix}-redis-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Redis memory usage is high"
  alarm_actions       = [aws_sns_topic.infrastructure_alerts.arn]

  dimensions = {
    CacheClusterId = "${var.name_prefix}-redis"
  }

  tags = {
    Name        = "${var.name_prefix}-redis-memory-alarm"
    Component   = "monitoring"
    Severity    = "high"
    Type        = "cache"
  }
}