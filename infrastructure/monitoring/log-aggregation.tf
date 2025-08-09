# Seiketsu AI - Log Aggregation Configuration
# Centralized logging with structured log processing

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/ecs/${var.name_prefix}/api"
  retention_in_days = var.log_retention_days
  
  tags = {
    Name        = "${var.name_prefix}-api-logs"
    Component   = "logging"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "frontend_logs" {
  name              = "/cloudfront/${var.name_prefix}/frontend"
  retention_in_days = var.log_retention_days
  
  tags = {
    Name        = "${var.name_prefix}-frontend-logs"
    Component   = "logging"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "alb_logs" {
  name              = "/aws/applicationloadbalancer/${var.name_prefix}"
  retention_in_days = var.log_retention_days
  
  tags = {
    Name        = "${var.name_prefix}-alb-logs"
    Component   = "logging"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "waf_logs" {
  name              = "/aws/wafv2/${var.name_prefix}"
  retention_in_days = var.log_retention_days
  
  tags = {
    Name        = "${var.name_prefix}-waf-logs"
    Component   = "logging"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.name_prefix}-metrics-forwarder"
  retention_in_days = var.log_retention_days
  
  tags = {
    Name        = "${var.name_prefix}-lambda-logs"
    Component   = "logging"
    Environment = var.environment
  }
}

# Log Insights Queries for Performance Analysis
resource "aws_cloudwatch_query_definition" "voice_performance_analysis" {
  name = "${var.name_prefix}-voice-performance-analysis"
  
  log_group_names = [
    aws_cloudwatch_log_group.api_logs.name
  ]
  
  query_string = <<-EOT
    fields @timestamp, @message, @requestId
    | filter @message like /VOICE_RESPONSE_TIME/
    | parse @message /VOICE_RESPONSE_TIME duration_ms=(?<duration>\d+)/
    | stats avg(duration), max(duration), min(duration), count() by bin(5m)
    | sort @timestamp desc
  EOT
}

resource "aws_cloudwatch_query_definition" "api_error_analysis" {
  name = "${var.name_prefix}-api-error-analysis"
  
  log_group_names = [
    aws_cloudwatch_log_group.api_logs.name
  ]
  
  query_string = <<-EOT
    fields @timestamp, @message, @requestId, level
    | filter level = "ERROR"
    | stats count() by @message
    | sort count desc
    | limit 50
  EOT
}

resource "aws_cloudwatch_query_definition" "tenant_usage_analysis" {
  name = "${var.name_prefix}-tenant-usage-analysis"
  
  log_group_names = [
    aws_cloudwatch_log_group.api_logs.name
  ]
  
  query_string = <<-EOT
    fields @timestamp, @message, @requestId
    | filter @message like /TENANT_REQUEST/
    | parse @message /tenant_id="(?<tenant_id>[^"]+)"/
    | stats count() by tenant_id
    | sort count desc
  EOT
}

resource "aws_cloudwatch_query_definition" "third_party_api_latency" {
  name = "${var.name_prefix}-third-party-api-latency"
  
  log_group_names = [
    aws_cloudwatch_log_group.api_logs.name
  ]
  
  query_string = <<-EOT
    fields @timestamp, @message, @requestId
    | filter @message like /ELEVENLABS_API_TIME/ or @message like /OPENAI_API_TIME/
    | parse @message /(?<api_type>ELEVENLABS|OPENAI)_API_TIME duration_ms=(?<duration>\d+)/
    | stats avg(duration), max(duration), count() by api_type, bin(5m)
    | sort @timestamp desc
  EOT
}

resource "aws_cloudwatch_query_definition" "security_events" {
  name = "${var.name_prefix}-security-events"
  
  log_group_names = [
    aws_cloudwatch_log_group.waf_logs.name,
    aws_cloudwatch_log_group.alb_logs.name
  ]
  
  query_string = <<-EOT
    fields @timestamp, @message
    | filter @message like /BLOCK/ or @message like /403/ or @message like /401/
    | parse @message /"clientIp":"(?<client_ip>[^"]+)"/
    | stats count() by client_ip
    | sort count desc
    | limit 20
  EOT
}

# CloudWatch Log Subscription Filters for Real-time Processing
resource "aws_cloudwatch_log_subscription_filter" "api_errors_to_lambda" {
  name            = "${var.name_prefix}-api-errors-processor"
  log_group_name  = aws_cloudwatch_log_group.api_logs.name
  filter_pattern  = "[timestamp, request_id, level=\"ERROR\", ...]"
  destination_arn = aws_lambda_function.error_processor.arn

  depends_on = [aws_lambda_permission.allow_cloudwatch_logs]
}

# Lambda function for error processing
resource "aws_lambda_function" "error_processor" {
  filename         = "error_processor.zip"
  function_name    = "${var.name_prefix}-error-processor"
  role            = aws_iam_role.error_processor_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 60

  environment {
    variables = {
      SNS_TOPIC_ARN   = aws_sns_topic.critical_alerts.arn
      ENVIRONMENT     = var.environment
      PROJECT_NAME    = var.name_prefix
    }
  }

  tags = {
    Name        = "${var.name_prefix}-error-processor"
    Component   = "monitoring"
    Environment = var.environment
  }

  depends_on = [data.archive_file.error_processor_zip]
}

# Error processor Lambda code
data "archive_file" "error_processor_zip" {
  type        = "zip"
  output_path = "error_processor.zip"
  source {
    content = file("${path.module}/lambda/error_processor.py")
    filename = "index.py"
  }
}

# IAM role for error processor Lambda
resource "aws_iam_role" "error_processor_role" {
  name = "${var.name_prefix}-error-processor-role"

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
    Name        = "${var.name_prefix}-error-processor-role"
    Component   = "monitoring"
  }
}

resource "aws_iam_role_policy" "error_processor_policy" {
  name = "${var.name_prefix}-error-processor-policy"
  role = aws_iam_role.error_processor_role.id

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
        Resource = aws_sns_topic.critical_alerts.arn
      }
    ]
  })
}

# Lambda permission for CloudWatch Logs
resource "aws_lambda_permission" "allow_cloudwatch_logs" {
  statement_id  = "AllowExecutionFromCloudWatchLogs"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.error_processor.function_name
  principal     = "logs.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.api_logs.arn}:*"
}

# Kinesis Data Firehose for log archival
resource "aws_kinesis_firehose_delivery_stream" "log_archival" {
  name        = "${var.name_prefix}-log-archival"
  destination = "s3"

  s3_configuration {
    role_arn   = aws_iam_role.firehose_role.arn
    bucket_arn = aws_s3_bucket.log_archive.arn
    prefix     = "logs/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    
    buffer_size     = 5
    buffer_interval = 300
    
    compression_format = "GZIP"
    
    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = "/aws/kinesisfirehose/${var.name_prefix}-log-archival"
      log_stream_name = "S3Delivery"
    }
  }

  tags = {
    Name        = "${var.name_prefix}-log-archival-stream"
    Component   = "logging"
    Environment = var.environment
  }
}

# S3 bucket for log archival
resource "aws_s3_bucket" "log_archive" {
  bucket = "${var.name_prefix}-log-archive-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "${var.name_prefix}-log-archive"
    Component   = "logging"
    Environment = var.environment
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "log_archive" {
  bucket = aws_s3_bucket.log_archive.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "log_archive" {
  bucket = aws_s3_bucket.log_archive.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "log_archive" {
  bucket = aws_s3_bucket.log_archive.id

  rule {
    id     = "log_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555  # 7 years for compliance
    }
  }
}

# IAM role for Kinesis Firehose
resource "aws_iam_role" "firehose_role" {
  name = "${var.name_prefix}-firehose-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "firehose.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-firehose-role"
    Component   = "logging"
  }
}

resource "aws_iam_role_policy" "firehose_policy" {
  name = "${var.name_prefix}-firehose-policy"
  role = aws_iam_role.firehose_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ]
        Resource = [
          aws_s3_bucket.log_archive.arn,
          "${aws_s3_bucket.log_archive.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}