# Seiketsu AI - SNS Topics for Alert Management
# Hierarchical alerting system with multiple notification channels

# Critical Alerts (Immediate action required)
resource "aws_sns_topic" "critical_alerts" {
  name = "${var.name_prefix}-critical-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-critical-alerts"
    Component   = "monitoring"
    Severity    = "critical"
    Environment = var.environment
  }
}

# Performance Alerts (SLA breaches)
resource "aws_sns_topic" "performance_alerts" {
  name = "${var.name_prefix}-performance-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-performance-alerts"
    Component   = "monitoring"
    Severity    = "high"
    Environment = var.environment
  }
}

# Infrastructure Alerts (Scaling and capacity)
resource "aws_sns_topic" "infrastructure_alerts" {
  name = "${var.name_prefix}-infrastructure-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-infrastructure-alerts"
    Component   = "monitoring"
    Severity    = "warning"
    Environment = var.environment
  }
}

# Cost Alerts (Budget monitoring)
resource "aws_sns_topic" "cost_alerts" {
  name = "${var.name_prefix}-cost-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-cost-alerts"
    Component   = "monitoring"
    Severity    = "medium"
    Type        = "cost"
    Environment = var.environment
  }
}

# Third-party API Alerts
resource "aws_sns_topic" "third_party_alerts" {
  name = "${var.name_prefix}-third-party-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-third-party-alerts"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "third-party"
    Environment = var.environment
  }
}

# Capacity Alerts (Multi-tenant scaling)
resource "aws_sns_topic" "capacity_alerts" {
  name = "${var.name_prefix}-capacity-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-capacity-alerts"
    Component   = "monitoring"
    Severity    = "warning"
    Type        = "capacity"
    Environment = var.environment
  }
}

# Security Alerts
resource "aws_sns_topic" "security_alerts" {
  name = "${var.name_prefix}-security-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-security-alerts"
    Component   = "monitoring"
    Severity    = "high"
    Type        = "security"
    Environment = var.environment
  }
}

# Backup and Recovery Alerts
resource "aws_sns_topic" "backup_alerts" {
  name = "${var.name_prefix}-backup-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-backup-alerts"
    Component   = "monitoring"
    Severity    = "medium"
    Type        = "backup"
    Environment = var.environment
  }
}

# Email Subscriptions for Critical Alerts
resource "aws_sns_topic_subscription" "critical_email" {
  count     = length(var.alert_email_addresses)
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_addresses[count.index]
}

# Slack Integration for Critical Alerts
resource "aws_sns_topic_subscription" "critical_slack" {
  count     = var.slack_webhook_url != "" ? 1 : 0
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}

# PagerDuty Integration for Critical Alerts
resource "aws_sns_topic_subscription" "critical_pagerduty" {
  count     = var.pagerduty_endpoint != "" ? 1 : 0
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "https"
  endpoint  = var.pagerduty_endpoint
}

# Lambda function for alert enrichment and routing
resource "aws_lambda_function" "alert_processor" {
  filename         = "alert_processor.zip"
  function_name    = "${var.name_prefix}-alert-processor"
  role            = aws_iam_role.alert_processor_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 30

  environment {
    variables = {
      SLACK_WEBHOOK_URL     = var.slack_webhook_url
      PAGERDUTY_ENDPOINT    = var.pagerduty_endpoint
      ENVIRONMENT          = var.environment
      PROJECT_NAME         = var.name_prefix
      ENABLE_ALERT_ROUTING = "true"
    }
  }

  tags = {
    Name        = "${var.name_prefix}-alert-processor"
    Component   = "monitoring"
    Environment = var.environment
  }

  depends_on = [data.archive_file.alert_processor_zip]
}

# Alert processor Lambda code
data "archive_file" "alert_processor_zip" {
  type        = "zip"
  output_path = "alert_processor.zip"
  source {
    content = file("${path.module}/lambda/alert_processor.py")
    filename = "index.py"
  }
}

# IAM role for alert processor Lambda
resource "aws_iam_role" "alert_processor_role" {
  name = "${var.name_prefix}-alert-processor-role"

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

  tags = {
    Name        = "${var.name_prefix}-alert-processor-role"
    Component   = "monitoring"
  }
}

resource "aws_iam_role_policy" "alert_processor_policy" {
  name = "${var.name_prefix}-alert-processor-policy"
  role = aws_iam_role.alert_processor_role.id

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
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.critical_alerts.arn,
          aws_sns_topic.performance_alerts.arn,
          aws_sns_topic.infrastructure_alerts.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      }
    ]
  })
}

# SNS Topic Subscriptions for Alert Processor
resource "aws_sns_topic_subscription" "alert_processor_critical" {
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.alert_processor.arn
}

resource "aws_sns_topic_subscription" "alert_processor_performance" {
  topic_arn = aws_sns_topic.performance_alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.alert_processor.arn
}

# Lambda permissions for SNS
resource "aws_lambda_permission" "allow_sns_critical" {
  statement_id  = "AllowExecutionFromSNSCritical"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.alert_processor.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.critical_alerts.arn
}

resource "aws_lambda_permission" "allow_sns_performance" {
  statement_id  = "AllowExecutionFromSNSPerformance"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.alert_processor.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.performance_alerts.arn
}

# Dead Letter Queue for failed alert processing
resource "aws_sqs_queue" "alert_dlq" {
  name = "${var.name_prefix}-alert-dlq"
  
  message_retention_seconds = 1209600  # 14 days
  
  tags = {
    Name        = "${var.name_prefix}-alert-dlq"
    Component   = "monitoring"
    Environment = var.environment
  }
}

# CloudWatch Alarm for DLQ messages
resource "aws_cloudwatch_metric_alarm" "alert_dlq_messages" {
  alarm_name          = "${var.name_prefix}-alert-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfVisibleMessages"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "Messages in alert processing DLQ"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]

  dimensions = {
    QueueName = aws_sqs_queue.alert_dlq.name
  }

  tags = {
    Name        = "${var.name_prefix}-alert-dlq-alarm"
    Component   = "monitoring"
    Type        = "system"
  }
}

# SNS Topic Policy for cross-account access (if needed)
data "aws_iam_policy_document" "sns_topic_policy" {
  statement {
    effect = "Allow"
    
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    
    actions = [
      "sns:GetTopicAttributes",
      "sns:SetTopicAttributes",
      "sns:AddPermission",
      "sns:RemovePermission",
      "sns:DeleteTopic",
      "sns:Subscribe",
      "sns:ListSubscriptionsByTopic",
      "sns:Publish",
      "sns:Receive"
    ]
    
    resources = [
      aws_sns_topic.critical_alerts.arn,
      aws_sns_topic.performance_alerts.arn,
      aws_sns_topic.infrastructure_alerts.arn
    ]
    
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceOwner"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "critical_alerts" {
  arn    = aws_sns_topic.critical_alerts.arn
  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

resource "aws_sns_topic_policy" "performance_alerts" {
  arn    = aws_sns_topic.performance_alerts.arn
  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

resource "aws_sns_topic_policy" "infrastructure_alerts" {
  arn    = aws_sns_topic.infrastructure_alerts.arn
  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

# Data sources
data "aws_caller_identity" "current" {}