# Seiketsu AI - Monitoring Module
# Comprehensive monitoring with 21dev.ai integration

# CloudWatch Dashboard for Infrastructure Overview
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.name_prefix}-infrastructure"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "${var.name_prefix}-api-service", "ClusterName", "${var.name_prefix}-cluster"],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "ECS Service Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "${var.name_prefix}-database"],
            [".", "DatabaseConnections", ".", "."],
            [".", "FreeStorageSpace", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "RDS Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "${var.name_prefix}-alb"],
            [".", "RequestCount", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "ALB Metrics"
          period  = 300
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-dashboard"
    Component = "monitoring"
  })
}

# Custom CloudWatch Metrics for Voice Response Time
resource "aws_cloudwatch_log_metric_filter" "voice_response_time" {
  name           = "${var.name_prefix}-voice-response-time"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id, voice_response_time_ms = *ms*]"

  metric_transformation {
    name      = "VoiceResponseTime"
    namespace = "Seiketsu/Performance"
    value     = "$voice_response_time_ms"
    unit      = "Milliseconds"
  }
}

# Custom CloudWatch Metrics for API Response Time
resource "aws_cloudwatch_log_metric_filter" "api_response_time" {
  name           = "${var.name_prefix}-api-response-time"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id, api_response_time_ms = *ms*]"

  metric_transformation {
    name      = "APIResponseTime"
    namespace = "Seiketsu/Performance"
    value     = "$api_response_time_ms"
    unit      = "Milliseconds"
  }
}

# Custom CloudWatch Metrics for Tenant Usage
resource "aws_cloudwatch_log_metric_filter" "tenant_requests" {
  name           = "${var.name_prefix}-tenant-requests"
  log_group_name = "/ecs/${var.name_prefix}/api"
  pattern        = "[timestamp, request_id, tenant_id, request_type]"

  metric_transformation {
    name      = "TenantRequests"
    namespace = "Seiketsu/MultiTenant"
    value     = "1"
    unit      = "Count"
  }
}

# CloudWatch Alarms for Performance SLA
resource "aws_cloudwatch_metric_alarm" "voice_response_sla" {
  alarm_name          = "${var.name_prefix}-voice-response-sla-breach"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "VoiceResponseTime"
  namespace           = "Seiketsu/Performance"
  period              = "300"
  statistic           = "Average"
  threshold           = var.performance_thresholds.voice_response_time
  alarm_description   = "Voice response time exceeds 2 second SLA"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]
  ok_actions          = [aws_sns_topic.performance_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-voice-sla-alarm"
    Component = "monitoring"
    SLA = "voice-response"
  })
}

resource "aws_cloudwatch_metric_alarm" "api_response_sla" {
  alarm_name          = "${var.name_prefix}-api-response-sla-breach"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "APIResponseTime"
  namespace           = "Seiketsu/Performance"
  period              = "300"
  statistic           = "Average"
  threshold           = var.performance_thresholds.api_response_time
  alarm_description   = "API response time exceeds 500ms SLA"
  alarm_actions       = [aws_sns_topic.performance_alerts.arn]
  ok_actions          = [aws_sns_topic.performance_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api-sla-alarm"
    Component = "monitoring"
    SLA = "api-response"
  })
}

# ECS Service Alarms
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  alarm_name          = "${var.name_prefix}-ecs-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "70"
  alarm_description   = "ECS CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.infrastructure_alerts.arn]

  dimensions = {
    ServiceName = "${var.name_prefix}-api-service"
    ClusterName = "${var.name_prefix}-cluster"
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory_high" {
  alarm_name          = "${var.name_prefix}-ecs-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "ECS memory utilization is too high"
  alarm_actions       = [aws_sns_topic.infrastructure_alerts.arn]

  dimensions = {
    ServiceName = "${var.name_prefix}-api-service"
    ClusterName = "${var.name_prefix}-cluster"
  }

  tags = var.tags
}

# ALB Target Health Alarm
resource "aws_cloudwatch_metric_alarm" "alb_healthy_targets" {
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

  dimensions = {
    TargetGroup  = aws_lb_target_group.api.arn_suffix
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = var.tags
}

# SNS Topics for Alerts
resource "aws_sns_topic" "critical_alerts" {
  name = "${var.name_prefix}-critical-alerts"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-critical-alerts"
    Component = "monitoring"
    Severity = "critical"
  })
}

resource "aws_sns_topic" "infrastructure_alerts" {
  name = "${var.name_prefix}-infrastructure-alerts"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-infrastructure-alerts"
    Component = "monitoring"
    Severity = "warning"
  })
}

resource "aws_sns_topic" "performance_alerts" {
  name = "${var.name_prefix}-performance-alerts"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-performance-alerts"
    Component = "monitoring"
    Severity = "performance"
  })
}

# 21dev.ai Integration via Lambda Function
resource "aws_lambda_function" "metrics_forwarder" {
  filename         = "metrics_forwarder.zip"
  function_name    = "${var.name_prefix}-metrics-forwarder"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 60

  environment {
    variables = {
      MONITORING_ENDPOINT = var.monitoring_config.metrics_endpoint
      API_KEY_SECRET_ARN  = aws_secretsmanager_secret.monitoring_api_key.arn
      PROJECT_NAME        = var.name_prefix
      ENVIRONMENT         = var.environment
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-metrics-forwarder"
    Component = "monitoring"
    Integration = "21dev-ai"
  })

  depends_on = [data.archive_file.lambda_zip]
}

# Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "metrics_forwarder.zip"
  source {
    content = file("${path.module}/lambda/metrics_forwarder.py")
    filename = "index.py"
  }
}

# Lambda IAM Role
resource "aws_iam_role" "lambda_role" {
  name = "${var.name_prefix}-lambda-metrics-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.name_prefix}-lambda-metrics-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.monitoring_api_key.arn
      }
    ]
  })
}

# CloudWatch Event Rule to trigger Lambda
resource "aws_cloudwatch_event_rule" "metrics_schedule" {
  name                = "${var.name_prefix}-metrics-schedule"
  description         = "Trigger metrics forwarder every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.metrics_schedule.name
  target_id = "MetricsForwarderTarget"
  arn       = aws_lambda_function.metrics_forwarder.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.metrics_forwarder.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.metrics_schedule.arn
}

# Secrets Manager for 21dev.ai API Key
resource "aws_secretsmanager_secret" "monitoring_api_key" {
  name        = "${var.name_prefix}/monitoring/api-key"
  description = "21dev.ai monitoring API key"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-monitoring-api-key"
    Component = "secrets"
  })
}

resource "aws_secretsmanager_secret_version" "monitoring_api_key" {
  secret_id     = aws_secretsmanager_secret.monitoring_api_key.id
  secret_string = var.monitoring_api_key
}

# X-Ray Tracing for Performance Analysis
resource "aws_xray_sampling_rule" "main" {
  rule_name      = "${var.name_prefix}-sampling-rule"
  priority       = 9000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.1
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-xray-sampling"
    Component = "tracing"
  })
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}