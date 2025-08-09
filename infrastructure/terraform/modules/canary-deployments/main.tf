# Canary Deployment Module for Seiketsu AI
# Implements gradual traffic shifting for safe deployments

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  common_tags = merge(var.tags, {
    Module = "canary-deployments"
  })
  
  # Calculate weight distribution
  stable_weight = 100 - var.canary_weight
  canary_weight = var.canary_weight
}

# Application Load Balancer Listener Rule for Canary Deployments
resource "aws_lb_listener_rule" "canary" {
  count        = var.enable_canary ? 1 : 0
  listener_arn = var.listener_arn
  priority     = var.rule_priority

  action {
    type = "forward"
    
    forward {
      target_group {
        arn    = var.stable_target_group_arn
        weight = local.stable_weight
      }
      
      target_group {
        arn    = var.canary_target_group_arn
        weight = local.canary_weight
      }
      
      stickiness {
        enabled  = var.enable_stickiness
        duration = var.stickiness_duration
      }
    }
  }

  condition {
    path_pattern {
      values = var.canary_path_patterns
    }
  }

  dynamic "condition" {
    for_each = var.canary_headers
    content {
      http_header {
        http_header_name = condition.key
        values          = condition.value
      }
    }
  }

  dynamic "condition" {
    for_each = var.canary_query_strings
    content {
      query_string {
        key   = condition.key
        value = condition.value
      }
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-rule"
  })
}

# CodeDeploy Application
resource "aws_codedeploy_application" "main" {
  name             = "${var.name_prefix}-canary"
  compute_platform = "ECS"

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-app"
  })
}

# CodeDeploy Deployment Configuration for Canary
resource "aws_codedeploy_deployment_config" "canary" {
  deployment_config_name = "${var.name_prefix}-canary-config"
  compute_platform      = "ECS"

  traffic_routing_config {
    type = "TimeBasedCanary"
    
    time_based_canary {
      canary_percentage = var.canary_weight
      canary_interval   = var.canary_interval_minutes
    }
  }

  auto_rollback_configuration {
    enabled = var.enable_auto_rollback
    events  = var.auto_rollback_events
  }

  blue_green_deployment_config {
    deployment_ready_option {
      action_on_timeout = "CONTINUE_DEPLOYMENT"
    }

    green_fleet_provisioning_option {
      action = "COPY_AUTO_SCALING_GROUP"
    }

    terminate_blue_instances_on_deployment_success {
      action                         = "TERMINATE"
      termination_wait_time_in_minutes = var.termination_wait_time
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-config"
  })
}

# CodeDeploy Deployment Group
resource "aws_codedeploy_deployment_group" "main" {
  app_name               = aws_codedeploy_application.main.name
  deployment_group_name  = "${var.name_prefix}-canary-group"
  service_role_arn      = aws_iam_role.codedeploy.arn
  deployment_config_name = aws_codedeploy_deployment_config.canary.id

  auto_rollback_configuration {
    enabled = var.enable_auto_rollback
    events  = var.auto_rollback_events
  }

  blue_green_deployment_config {
    terminate_blue_instances_on_deployment_success {
      action                         = "TERMINATE"
      termination_wait_time_in_minutes = var.termination_wait_time
    }

    deployment_ready_option {
      action_on_timeout = "CONTINUE_DEPLOYMENT"
    }

    green_fleet_provisioning_option {
      action = "COPY_AUTO_SCALING_GROUP"
    }
  }

  ecs_service {
    cluster_name = var.ecs_cluster_name
    service_name = var.ecs_service_name
  }

  load_balancer_info {
    target_group_info {
      name = regex("([^/]+)$", var.stable_target_group_arn)[0]
    }
    
    target_group_info {
      name = regex("([^/]+)$", var.canary_target_group_arn)[0]
    }
  }

  alarm_configuration {
    enabled = var.enable_cloudwatch_alarms
    alarms  = var.cloudwatch_alarms
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-group"
  })
}

# IAM role for CodeDeploy
resource "aws_iam_role" "codedeploy" {
  name = "${var.name_prefix}-codedeploy-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codedeploy.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-codedeploy-role"
  })
}

# Attach AWS managed policy for CodeDeploy ECS
resource "aws_iam_role_policy_attachment" "codedeploy_ecs" {
  policy_arn = "arn:aws:iam::aws:policy/AWSCodeDeployRoleForECS"
  role       = aws_iam_role.codedeploy.name
}

# Custom policy for additional permissions
resource "aws_iam_role_policy" "codedeploy_custom" {
  name = "${var.name_prefix}-codedeploy-custom-policy"
  role = aws_iam_role.codedeploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeListeners",
          "elasticloadbalancing:ModifyListener",
          "elasticloadbalancing:DescribeRules",
          "elasticloadbalancing:ModifyRule",
          "lambda:InvokeFunction",
          "cloudwatch:DescribeAlarms",
          "sns:Publish"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda function for canary analysis
resource "aws_lambda_function" "canary_analysis" {
  filename         = data.archive_file.canary_analysis.output_path
  function_name    = "${var.name_prefix}-canary-analysis"
  role            = aws_iam_role.canary_lambda.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.canary_analysis.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      STABLE_TARGET_GROUP_ARN = var.stable_target_group_arn
      CANARY_TARGET_GROUP_ARN = var.canary_target_group_arn
      CLOUDWATCH_NAMESPACE    = var.cloudwatch_namespace
      ERROR_RATE_THRESHOLD    = var.error_rate_threshold
      LATENCY_THRESHOLD       = var.latency_threshold
      MIN_REQUESTS_THRESHOLD  = var.min_requests_threshold
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-analysis"
  })
}

# Canary analysis Lambda package
data "archive_file" "canary_analysis" {
  type        = "zip"
  output_path = "/tmp/canary_analysis.zip"
  
  source {
    content = templatefile("${path.module}/lambda/canary_analysis.py", {
      stable_tg_arn = var.stable_target_group_arn
      canary_tg_arn = var.canary_target_group_arn
    })
    filename = "index.py"
  }
}

# IAM role for canary Lambda
resource "aws_iam_role" "canary_lambda" {
  name = "${var.name_prefix}-canary-lambda-role"

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

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-lambda-role"
  })
}

# IAM policy for canary Lambda
resource "aws_iam_role_policy" "canary_lambda" {
  name = "${var.name_prefix}-canary-lambda-policy"
  role = aws_iam_role.canary_lambda.id

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
          "cloudwatch:PutMetricData",
          "elasticloadbalancing:DescribeTargetHealth",
          "elasticloadbalancing:DescribeTargetGroups",
          "codedeploy:StopDeployment",
          "codedeploy:GetDeployment"
        ]
        Resource = "*"
      }
    ]
  })
}

# Step Function for canary deployment orchestration
resource "aws_sfn_state_machine" "canary_deployment" {
  name     = "${var.name_prefix}-canary-deployment"
  role_arn = aws_iam_role.step_function.arn

  definition = templatefile("${path.module}/step-function/canary-deployment.json", {
    canary_analysis_function_arn = aws_lambda_function.canary_analysis.arn
    rollback_function_arn       = aws_lambda_function.rollback.arn
    promotion_function_arn      = aws_lambda_function.promotion.arn
    canary_duration_minutes     = var.canary_duration_minutes
    analysis_interval_minutes   = var.analysis_interval_minutes
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_function.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-deployment"
  })
}

# CloudWatch Log Group for Step Function
resource "aws_cloudwatch_log_group" "step_function" {
  name              = "/aws/stepfunction/${var.name_prefix}-canary"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-step-function-logs"
  })
}

# IAM role for Step Function
resource "aws_iam_role" "step_function" {
  name = "${var.name_prefix}-canary-step-function-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-step-function-role"
  })
}

# IAM policy for Step Function
resource "aws_iam_role_policy" "step_function" {
  name = "${var.name_prefix}-canary-step-function-policy"
  role = aws_iam_role.step_function.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.canary_analysis.arn,
          aws_lambda_function.rollback.arn,
          aws_lambda_function.promotion.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda function for rollback
resource "aws_lambda_function" "rollback" {
  filename         = data.archive_file.rollback.output_path
  function_name    = "${var.name_prefix}-canary-rollback"
  role            = aws_iam_role.canary_lambda.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.rollback.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      LISTENER_ARN            = var.listener_arn
      STABLE_TARGET_GROUP_ARN = var.stable_target_group_arn
      CANARY_TARGET_GROUP_ARN = var.canary_target_group_arn
      CODEDEPLOY_APP_NAME     = aws_codedeploy_application.main.name
      CODEDEPLOY_GROUP_NAME   = aws_codedeploy_deployment_group.main.deployment_group_name
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-rollback"
  })
}

# Rollback Lambda package
data "archive_file" "rollback" {
  type        = "zip"
  output_path = "/tmp/canary_rollback.zip"
  
  source {
    content  = file("${path.module}/lambda/canary_rollback.py")
    filename = "index.py"
  }
}

# Lambda function for promotion
resource "aws_lambda_function" "promotion" {
  filename         = data.archive_file.promotion.output_path
  function_name    = "${var.name_prefix}-canary-promotion"
  role            = aws_iam_role.canary_lambda.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.promotion.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      LISTENER_ARN            = var.listener_arn
      STABLE_TARGET_GROUP_ARN = var.stable_target_group_arn
      CANARY_TARGET_GROUP_ARN = var.canary_target_group_arn
      CODEDEPLOY_APP_NAME     = aws_codedeploy_application.main.name
      CODEDEPLOY_GROUP_NAME   = aws_codedeploy_deployment_group.main.deployment_group_name
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-promotion"
  })
}

# Promotion Lambda package
data "archive_file" "promotion" {
  type        = "zip"
  output_path = "/tmp/canary_promotion.zip"
  
  source {
    content  = file("${path.module}/lambda/canary_promotion.py")
    filename = "index.py"
  }
}

# CloudWatch Dashboard for canary metrics
resource "aws_cloudwatch_dashboard" "canary" {
  dashboard_name = "${var.name_prefix}-canary-dashboard"

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
            ["AWS/ApplicationELB", "RequestCount", "TargetGroup", regex("([^/]+)$", var.stable_target_group_arn)[0]],
            [".", ".", ".", regex("([^/]+)$", var.canary_target_group_arn)[0]]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Request Count - Stable vs Canary"
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
            ["AWS/ApplicationELB", "TargetResponseTime", "TargetGroup", regex("([^/]+)$", var.stable_target_group_arn)[0]],
            [".", ".", ".", regex("([^/]+)$", var.canary_target_group_arn)[0]]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Response Time - Stable vs Canary"
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
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "TargetGroup", regex("([^/]+)$", var.stable_target_group_arn)[0]],
            [".", ".", ".", regex("([^/]+)$", var.canary_target_group_arn)[0]]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Error Count - Stable vs Canary"
          period  = 300
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-dashboard"
  })
}

# CloudWatch Alarms for canary monitoring
resource "aws_cloudwatch_metric_alarm" "canary_error_rate" {
  alarm_name          = "${var.name_prefix}-canary-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.error_rate_threshold
  alarm_description   = "Canary deployment error rate is too high"
  alarm_actions       = var.alarm_actions

  dimensions = {
    TargetGroup = regex("([^/]+)$", var.canary_target_group_arn)[0]
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-error-alarm"
  })
}

resource "aws_cloudwatch_metric_alarm" "canary_latency" {
  alarm_name          = "${var.name_prefix}-canary-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = var.latency_threshold
  alarm_description   = "Canary deployment latency is too high"
  alarm_actions       = var.alarm_actions

  dimensions = {
    TargetGroup = regex("([^/]+)$", var.canary_target_group_arn)[0]
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-canary-latency-alarm"
  })
}

# Data source for current AWS region
data "aws_region" "current" {}