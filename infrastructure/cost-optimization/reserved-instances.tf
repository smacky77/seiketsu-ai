# Seiketsu AI - Reserved Instance Recommendations and Management
# Cost optimization through reserved capacity planning

# Data source to get current EC2 instance usage
data "aws_instances" "ecs_instances" {
  filter {
    name   = "tag:aws:autoscaling:groupName"
    values = [var.ecs_asg_name]
  }
  
  filter {
    name   = "instance-state-name"
    values = ["running"]
  }
}

# Lambda function for RI recommendations
resource "aws_lambda_function" "ri_analyzer" {
  filename         = "ri_analyzer.zip"
  function_name    = "${var.name_prefix}-ri-analyzer"
  role            = aws_iam_role.ri_analyzer_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      PROJECT_NAME     = var.name_prefix
      ENVIRONMENT      = var.environment
      SNS_TOPIC_ARN    = aws_sns_topic.cost_optimization.arn
      S3_BUCKET        = aws_s3_bucket.cost_reports.bucket
    }
  }

  tags = {
    Name        = "${var.name_prefix}-ri-analyzer"
    Component   = "cost-optimization"
    Environment = var.environment
  }

  depends_on = [data.archive_file.ri_analyzer_zip]
}

# RI Analyzer Lambda code
data "archive_file" "ri_analyzer_zip" {
  type        = "zip"
  output_path = "ri_analyzer.zip"
  source {
    content = file("${path.module}/lambda/ri_analyzer.py")
    filename = "index.py"
  }
}

# IAM role for RI analyzer Lambda
resource "aws_iam_role" "ri_analyzer_role" {
  name = "${var.name_prefix}-ri-analyzer-role"

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
    Name        = "${var.name_prefix}-ri-analyzer-role"
    Component   = "cost-optimization"
  }
}

resource "aws_iam_role_policy" "ri_analyzer_policy" {
  name = "${var.name_prefix}-ri-analyzer-policy"
  role = aws_iam_role.ri_analyzer_role.id

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
          "ec2:DescribeInstances",
          "ec2:DescribeReservedInstances",
          "ec2:DescribeReservedInstancesOfferings",
          "ec2:DescribeInstanceTypes",
          "autoscaling:DescribeAutoScalingGroups",
          "cloudwatch:GetMetricStatistics",
          "ce:GetUsageAndCosts",
          "ce:GetReservationCoverage",
          "ce:GetReservationPurchaseRecommendation",
          "ce:GetReservationUtilization"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.cost_reports.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.cost_optimization.arn
      }
    ]
  })
}

# CloudWatch Event Rule for scheduled RI analysis
resource "aws_cloudwatch_event_rule" "ri_analysis_schedule" {
  name                = "${var.name_prefix}-ri-analysis-schedule"
  description         = "Weekly RI recommendation analysis"
  schedule_expression = "cron(0 9 ? * MON *)"  # Every Monday at 9 AM UTC

  tags = {
    Name        = "${var.name_prefix}-ri-analysis-schedule"
    Component   = "cost-optimization"
  }
}

resource "aws_cloudwatch_event_target" "ri_analysis_target" {
  rule      = aws_cloudwatch_event_rule.ri_analysis_schedule.name
  target_id = "RIAnalysisTarget"
  arn       = aws_lambda_function.ri_analyzer.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_ri_analysis" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ri_analyzer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ri_analysis_schedule.arn
}

# RDS Reserved Instance Analyzer
resource "aws_lambda_function" "rds_ri_analyzer" {
  filename         = "rds_ri_analyzer.zip"
  function_name    = "${var.name_prefix}-rds-ri-analyzer"
  role            = aws_iam_role.rds_ri_analyzer_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      PROJECT_NAME      = var.name_prefix
      ENVIRONMENT       = var.environment
      SNS_TOPIC_ARN     = aws_sns_topic.cost_optimization.arn
      S3_BUCKET         = aws_s3_bucket.cost_reports.bucket
      RDS_CLUSTER_ID    = var.rds_cluster_identifier
    }
  }

  tags = {
    Name        = "${var.name_prefix}-rds-ri-analyzer"
    Component   = "cost-optimization"
    Environment = var.environment
  }

  depends_on = [data.archive_file.rds_ri_analyzer_zip]
}

# RDS RI Analyzer Lambda code
data "archive_file" "rds_ri_analyzer_zip" {
  type        = "zip"
  output_path = "rds_ri_analyzer.zip"
  source {
    content = file("${path.module}/lambda/rds_ri_analyzer.py")
    filename = "index.py"
  }
}

# IAM role for RDS RI analyzer Lambda
resource "aws_iam_role" "rds_ri_analyzer_role" {
  name = "${var.name_prefix}-rds-ri-analyzer-role"

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
    Name        = "${var.name_prefix}-rds-ri-analyzer-role"
    Component   = "cost-optimization"
  }
}

resource "aws_iam_role_policy" "rds_ri_analyzer_policy" {
  name = "${var.name_prefix}-rds-ri-analyzer-policy"
  role = aws_iam_role.rds_ri_analyzer_role.id

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
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "rds:DescribeReservedDBInstances",
          "rds:DescribeReservedDBInstancesOfferings",
          "cloudwatch:GetMetricStatistics",
          "ce:GetUsageAndCosts",
          "ce:GetReservationCoverage",
          "ce:GetReservationPurchaseRecommendation",
          "ce:GetReservationUtilization"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.cost_reports.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.cost_optimization.arn
      }
    ]
  })
}

# ElastiCache Reserved Instance Analyzer
resource "aws_lambda_function" "elasticache_ri_analyzer" {
  filename         = "elasticache_ri_analyzer.zip"
  function_name    = "${var.name_prefix}-elasticache-ri-analyzer"
  role            = aws_iam_role.elasticache_ri_analyzer_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      PROJECT_NAME       = var.name_prefix
      ENVIRONMENT        = var.environment
      SNS_TOPIC_ARN      = aws_sns_topic.cost_optimization.arn
      S3_BUCKET          = aws_s3_bucket.cost_reports.bucket
      REDIS_CLUSTER_ID   = var.redis_cluster_identifier
    }
  }

  tags = {
    Name        = "${var.name_prefix}-elasticache-ri-analyzer"
    Component   = "cost-optimization"
    Environment = var.environment
  }

  depends_on = [data.archive_file.elasticache_ri_analyzer_zip]
}

# ElastiCache RI Analyzer Lambda code
data "archive_file" "elasticache_ri_analyzer_zip" {
  type        = "zip"
  output_path = "elasticache_ri_analyzer.zip"
  source {
    content = file("${path.module}/lambda/elasticache_ri_analyzer.py")
    filename = "index.py"
  }
}

# IAM role for ElastiCache RI analyzer Lambda
resource "aws_iam_role" "elasticache_ri_analyzer_role" {
  name = "${var.name_prefix}-elasticache-ri-analyzer-role"

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
    Name        = "${var.name_prefix}-elasticache-ri-analyzer-role"
    Component   = "cost-optimization"
  }
}

resource "aws_iam_role_policy" "elasticache_ri_analyzer_policy" {
  name = "${var.name_prefix}-elasticache-ri-analyzer-policy"
  role = aws_iam_role.elasticache_ri_analyzer_role.id

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
          "elasticache:DescribeCacheClusters",
          "elasticache:DescribeReplicationGroups",
          "elasticache:DescribeReservedCacheNodes",
          "elasticache:DescribeReservedCacheNodesOfferings",
          "cloudwatch:GetMetricStatistics",
          "ce:GetUsageAndCosts",
          "ce:GetReservationCoverage",
          "ce:GetReservationPurchaseRecommendation",
          "ce:GetReservationUtilization"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.cost_reports.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.cost_optimization.arn
      }
    ]
  })
}

# Consolidated RI Recommendations Report Generator
resource "aws_lambda_function" "ri_report_generator" {
  filename         = "ri_report_generator.zip"
  function_name    = "${var.name_prefix}-ri-report-generator"
  role            = aws_iam_role.ri_report_generator_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 600
  memory_size     = 1024

  environment {
    variables = {
      PROJECT_NAME     = var.name_prefix
      ENVIRONMENT      = var.environment
      SNS_TOPIC_ARN    = aws_sns_topic.cost_optimization.arn
      S3_BUCKET        = aws_s3_bucket.cost_reports.bucket
      SLACK_WEBHOOK    = var.slack_webhook_url
    }
  }

  tags = {
    Name        = "${var.name_prefix}-ri-report-generator"
    Component   = "cost-optimization"
    Environment = var.environment
  }

  depends_on = [data.archive_file.ri_report_generator_zip]
}

# RI Report Generator Lambda code
data "archive_file" "ri_report_generator_zip" {
  type        = "zip"
  output_path = "ri_report_generator.zip"
  source {
    content = file("${path.module}/lambda/ri_report_generator.py")
    filename = "index.py"
  }
}

# IAM role for RI report generator Lambda
resource "aws_iam_role" "ri_report_generator_role" {
  name = "${var.name_prefix}-ri-report-generator-role"

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
    Name        = "${var.name_prefix}-ri-report-generator-role"
    Component   = "cost-optimization"
  }
}

resource "aws_iam_role_policy" "ri_report_generator_policy" {
  name = "${var.name_prefix}-ri-report-generator-policy"
  role = aws_iam_role.ri_report_generator_role.id

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
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.cost_reports.arn,
          "${aws_s3_bucket.cost_reports.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.cost_optimization.arn
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.ri_analyzer.arn,
          aws_lambda_function.rds_ri_analyzer.arn,
          aws_lambda_function.elasticache_ri_analyzer.arn
        ]
      }
    ]
  })
}

# CloudWatch Event Rule for monthly RI report generation
resource "aws_cloudwatch_event_rule" "monthly_ri_report" {
  name                = "${var.name_prefix}-monthly-ri-report"
  description         = "Monthly RI recommendations report"
  schedule_expression = "cron(0 10 1 * ? *)";  # 1st of every month at 10 AM UTC

  tags = {
    Name        = "${var.name_prefix}-monthly-ri-report"
    Component   = "cost-optimization"
  }
}

resource "aws_cloudwatch_event_target" "monthly_ri_report_target" {
  rule      = aws_cloudwatch_event_rule.monthly_ri_report.name
  target_id = "MonthlyRIReportTarget"
  arn       = aws_lambda_function.ri_report_generator.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_monthly_ri_report" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ri_report_generator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monthly_ri_report.arn
}

# Budget Alert for RI Utilization
resource "aws_budgets_budget" "ri_utilization_budget" {
  name         = "${var.name_prefix}-ri-utilization"
  budget_type  = "RI_UTILIZATION"
  limit_amount = "80"  # Alert if RI utilization drops below 80%
  limit_unit   = "PERCENTAGE"
  time_unit    = "MONTHLY"
  
  cost_filters = {
    Service = ["Amazon Elastic Compute Cloud - Compute"]
  }

  notification {
    comparison_operator        = "LESS_THAN"
    threshold                 = 80
    threshold_type           = "PERCENTAGE"
    notification_type        = "ACTUAL"
    subscriber_email_addresses = var.cost_alert_emails
    subscriber_sns_topic_arns = [aws_sns_topic.cost_optimization.arn]
  }
  
  tags = {
    Name        = "${var.name_prefix}-ri-utilization-budget"
    Component   = "cost-optimization"
    Type        = "ri-monitoring"
  }
}

# SNS Topic for Cost Optimization Alerts
resource "aws_sns_topic" "cost_optimization" {
  name = "${var.name_prefix}-cost-optimization"
  
  tags = {
    Name        = "${var.name_prefix}-cost-optimization"
    Component   = "cost-optimization"
    Environment = var.environment
  }
}

# S3 Bucket for Cost Reports
resource "aws_s3_bucket" "cost_reports" {
  bucket = "${var.name_prefix}-cost-reports-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "${var.name_prefix}-cost-reports"
    Component   = "cost-optimization"
    Environment = var.environment
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 bucket versioning for cost reports
resource "aws_s3_bucket_versioning" "cost_reports" {
  bucket = aws_s3_bucket.cost_reports.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket encryption for cost reports
resource "aws_s3_bucket_server_side_encryption_configuration" "cost_reports" {
  bucket = aws_s3_bucket.cost_reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket lifecycle for cost reports
resource "aws_s3_bucket_lifecycle_configuration" "cost_reports" {
  bucket = aws_s3_bucket.cost_reports.id

  rule {
    id     = "cost_reports_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 2555  # 7 years retention
    }
  }
}