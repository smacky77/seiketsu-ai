# Blue-Green Deployment Module for Seiketsu AI
# Enables zero-downtime deployments with automated rollback capabilities

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  blue_environment  = "${var.name_prefix}-blue"
  green_environment = "${var.name_prefix}-green"
  
  # Determine active and inactive environments
  active_env   = var.current_environment == "blue" ? local.blue_environment : local.green_environment
  inactive_env = var.current_environment == "blue" ? local.green_environment : local.blue_environment
  
  # Target group names
  active_tg_name   = "${var.name_prefix}-${var.current_environment}-tg"
  inactive_tg_name = "${var.name_prefix}-${var.target_environment}-tg"
  
  common_tags = merge(var.tags, {
    Module = "blue-green-deployment"
  })
}

# Application Load Balancer for Blue-Green deployments
resource "aws_lb" "main" {
  name               = "${var.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets           = var.public_subnet_ids

  enable_deletion_protection = var.enable_deletion_protection
  
  access_logs {
    bucket  = var.access_logs_bucket
    prefix  = "alb-logs"
    enabled = var.enable_access_logs
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-alb"
  })
}

# Blue Target Group
resource "aws_lb_target_group" "blue" {
  name     = "${var.name_prefix}-blue-tg"
  port     = var.target_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = var.health_check_healthy_threshold
    interval            = var.health_check_interval
    matcher             = var.health_check_matcher
    path                = var.health_check_path
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = var.health_check_timeout
    unhealthy_threshold = var.health_check_unhealthy_threshold
  }

  # Blue-green deployment requires preserving connections during switch
  deregistration_delay = var.deregistration_delay

  tags = merge(local.common_tags, {
    Name        = "${var.name_prefix}-blue-tg"
    Environment = "blue"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Green Target Group
resource "aws_lb_target_group" "green" {
  name     = "${var.name_prefix}-green-tg"
  port     = var.target_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = var.health_check_healthy_threshold
    interval            = var.health_check_interval
    matcher             = var.health_check_matcher
    path                = var.health_check_path
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = var.health_check_timeout
    unhealthy_threshold = var.health_check_unhealthy_threshold
  }

  deregistration_delay = var.deregistration_delay

  tags = merge(local.common_tags, {
    Name        = "${var.name_prefix}-green-tg"
    Environment = "green"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Primary ALB Listener (active environment)
resource "aws_lb_listener" "primary" {
  load_balancer_arn = aws_lb.main.arn
  port              = var.listener_port
  protocol          = var.listener_protocol
  ssl_policy        = var.ssl_policy
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = var.current_environment == "blue" ? aws_lb_target_group.blue.arn : aws_lb_target_group.green.arn
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-primary-listener"
  })
}

# Test ALB Listener (inactive environment for testing)
resource "aws_lb_listener" "test" {
  load_balancer_arn = aws_lb.main.arn
  port              = var.test_listener_port
  protocol          = var.listener_protocol
  ssl_policy        = var.ssl_policy
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = var.current_environment == "blue" ? aws_lb_target_group.green.arn : aws_lb_target_group.blue.arn
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-test-listener"
  })
}

# CloudWatch Log Group for deployment events
resource "aws_cloudwatch_log_group" "deployment_logs" {
  name              = "/aws/lambda/${var.name_prefix}-blue-green-deployment"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-deployment-logs"
  })
}

# Lambda function for blue-green traffic switching
resource "aws_lambda_function" "traffic_switch" {
  filename         = data.archive_file.traffic_switch.output_path
  function_name    = "${var.name_prefix}-traffic-switch"
  role            = aws_iam_role.traffic_switch.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.traffic_switch.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      ALB_ARN                = aws_lb.main.arn
      PRIMARY_LISTENER_ARN   = aws_lb_listener.primary.arn
      BLUE_TARGET_GROUP_ARN  = aws_lb_target_group.blue.arn
      GREEN_TARGET_GROUP_ARN = aws_lb_target_group.green.arn
      LOG_GROUP_NAME         = aws_cloudwatch_log_group.deployment_logs.name
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-traffic-switch"
  })
}

# Lambda deployment package
data "archive_file" "traffic_switch" {
  type        = "zip"
  output_path = "/tmp/traffic_switch.zip"
  
  source {
    content = templatefile("${path.module}/lambda/traffic_switch.py", {
      blue_tg_arn  = aws_lb_target_group.blue.arn
      green_tg_arn = aws_lb_target_group.green.arn
    })
    filename = "index.py"
  }
}

# IAM role for traffic switching Lambda
resource "aws_iam_role" "traffic_switch" {
  name = "${var.name_prefix}-traffic-switch-role"

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
    Name = "${var.name_prefix}-traffic-switch-role"
  })
}

# IAM policy for traffic switching Lambda
resource "aws_iam_role_policy" "traffic_switch" {
  name = "${var.name_prefix}-traffic-switch-policy"
  role = aws_iam_role.traffic_switch.id

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
        Resource = "${aws_cloudwatch_log_group.deployment_logs.arn}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:ModifyListener",
          "elasticloadbalancing:DescribeListeners",
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeTargetHealth"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:UpdateService"
        ]
        Resource = "*"
      }
    ]
  })
}

# Step Function for automated blue-green deployment
resource "aws_sfn_state_machine" "blue_green_deployment" {
  name     = "${var.name_prefix}-blue-green-deployment"
  role_arn = aws_iam_role.step_function.arn

  definition = templatefile("${path.module}/step-function/blue-green-deployment.json", {
    traffic_switch_function_arn = aws_lambda_function.traffic_switch.arn
    rollback_function_arn      = aws_lambda_function.rollback.arn
    health_check_function_arn  = aws_lambda_function.health_check.arn
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_function.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-blue-green-deployment"
  })
}

# CloudWatch Log Group for Step Function
resource "aws_cloudwatch_log_group" "step_function" {
  name              = "/aws/stepfunction/${var.name_prefix}-blue-green"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-step-function-logs"
  })
}

# IAM role for Step Function
resource "aws_iam_role" "step_function" {
  name = "${var.name_prefix}-step-function-role"

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
    Name = "${var.name_prefix}-step-function-role"
  })
}

# IAM policy for Step Function
resource "aws_iam_role_policy" "step_function" {
  name = "${var.name_prefix}-step-function-policy"
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
          aws_lambda_function.traffic_switch.arn,
          aws_lambda_function.rollback.arn,
          aws_lambda_function.health_check.arn
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

# Health check Lambda function
resource "aws_lambda_function" "health_check" {
  filename         = data.archive_file.health_check.output_path
  function_name    = "${var.name_prefix}-health-check"
  role            = aws_iam_role.health_check.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.health_check.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      ALB_DNS_NAME               = aws_lb.main.dns_name
      HEALTH_CHECK_PATH         = var.health_check_path
      HEALTH_CHECK_TIMEOUT      = var.health_check_timeout
      BLUE_TARGET_GROUP_ARN     = aws_lb_target_group.blue.arn
      GREEN_TARGET_GROUP_ARN    = aws_lb_target_group.green.arn
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-health-check"
  })
}

# Health check Lambda package
data "archive_file" "health_check" {
  type        = "zip"
  output_path = "/tmp/health_check.zip"
  
  source {
    content  = file("${path.module}/lambda/health_check.py")
    filename = "index.py"
  }
}

# IAM role for health check Lambda
resource "aws_iam_role" "health_check" {
  name = "${var.name_prefix}-health-check-role"

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
    Name = "${var.name_prefix}-health-check-role"
  })
}

# IAM policy for health check Lambda
resource "aws_iam_role_policy" "health_check" {
  name = "${var.name_prefix}-health-check-policy"
  role = aws_iam_role.health_check.id

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
          "elasticloadbalancing:DescribeTargetHealth",
          "elasticloadbalancing:DescribeTargetGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# Rollback Lambda function
resource "aws_lambda_function" "rollback" {
  filename         = data.archive_file.rollback.output_path
  function_name    = "${var.name_prefix}-rollback"
  role            = aws_iam_role.traffic_switch.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.rollback.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      ALB_ARN                = aws_lb.main.arn
      PRIMARY_LISTENER_ARN   = aws_lb_listener.primary.arn
      BLUE_TARGET_GROUP_ARN  = aws_lb_target_group.blue.arn
      GREEN_TARGET_GROUP_ARN = aws_lb_target_group.green.arn
      LOG_GROUP_NAME         = aws_cloudwatch_log_group.deployment_logs.name
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-rollback"
  })
}

# Rollback Lambda package
data "archive_file" "rollback" {
  type        = "zip"
  output_path = "/tmp/rollback.zip"
  
  source {
    content  = file("${path.module}/lambda/rollback.py")
    filename = "index.py"
  }
}

# CloudWatch alarms for monitoring deployment health
resource "aws_cloudwatch_metric_alarm" "blue_target_group_health" {
  alarm_name          = "${var.name_prefix}-blue-tg-unhealthy"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "Blue target group has unhealthy targets"
  alarm_actions       = var.sns_topic_arn != null ? [var.sns_topic_arn] : []

  dimensions = {
    TargetGroup  = aws_lb_target_group.blue.arn_suffix
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-blue-tg-health-alarm"
  })
}

resource "aws_cloudwatch_metric_alarm" "green_target_group_health" {
  alarm_name          = "${var.name_prefix}-green-tg-unhealthy"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "Green target group has unhealthy targets"
  alarm_actions       = var.sns_topic_arn != null ? [var.sns_topic_arn] : []

  dimensions = {
    TargetGroup  = aws_lb_target_group.green.arn_suffix
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-green-tg-health-alarm"
  })
}