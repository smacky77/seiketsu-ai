# Feature Flags Module for Seiketsu AI
# Implements dynamic feature toggling with AWS AppConfig

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
    Module = "feature-flags"
  })
}

# AppConfig Application
resource "aws_appconfig_application" "main" {
  name        = "${var.name_prefix}-feature-flags"
  description = "Feature flags for Seiketsu AI application"

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-feature-flags-app"
  })
}

# AppConfig Environment for each deployment environment
resource "aws_appconfig_environment" "main" {
  name           = var.environment
  description    = "Feature flags environment for ${var.environment}"
  application_id = aws_appconfig_application.main.id

  monitor {
    alarm_arn      = var.alarm_arn
    alarm_role_arn = aws_iam_role.appconfig_alarm.arn
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-${var.environment}-ff-env"
  })
}

# Configuration Profile for feature flags
resource "aws_appconfig_configuration_profile" "feature_flags" {
  application_id     = aws_appconfig_application.main.id
  name              = "feature-flags"
  description       = "JSON configuration for feature flags"
  location_uri      = "hosted"
  retrieval_role_arn = aws_iam_role.appconfig_retrieval.arn
  type              = "AWS.AppConfig.FeatureFlags"

  validator {
    content = jsonencode({
      "$schema" = "http://json-schema.org/draft-07/schema#"
      type      = "object"
      properties = {
        flags = {
          type = "object"
          patternProperties = {
            ".*" = {
              type = "object"
              properties = {
                enabled = { type = "boolean" }
                variants = {
                  type = "object"
                  properties = {
                    enabled = {
                      type = "object"
                      properties = {
                        value = { type = "boolean" }
                      }
                    }
                    disabled = {
                      type = "object"
                      properties = {
                        value = { type = "boolean" }
                      }
                    }
                  }
                }
              }
              required = ["enabled", "variants"]
            }
          }
        }
        values = {
          type = "object"
        }
        version = { type = "string" }
      }
      required = ["flags", "values", "version"]
    })
    type = "JSON_SCHEMA"
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-feature-flags-profile"
  })
}

# Initial feature flags configuration
resource "aws_appconfig_hosted_configuration_version" "feature_flags" {
  application_id          = aws_appconfig_application.main.id
  configuration_profile_id = aws_appconfig_configuration_profile.feature_flags.configuration_profile_id
  description             = "Initial feature flags configuration"
  content_type           = "application/json"

  content = jsonencode({
    flags = merge(
      {
        # Core features
        voice_ai = {
          enabled = var.feature_flags.voice_ai
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        analytics = {
          enabled = var.feature_flags.analytics
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        multi_tenant = {
          enabled = var.feature_flags.multi_tenant
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        
        # Deployment features
        canary_deployments = {
          enabled = var.feature_flags.canary_deployments
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        blue_green_deployments = {
          enabled = var.feature_flags.blue_green_deployments
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        
        # Monitoring features
        advanced_monitoring = {
          enabled = var.feature_flags.advanced_monitoring
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        
        # Premium features
        premium_features = {
          enabled = var.feature_flags.premium_features
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        enterprise_features = {
          enabled = var.feature_flags.enterprise_features
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        
        # Experimental features
        experimental_ai_models = {
          enabled = var.feature_flags.experimental_ai_models
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        new_ui_components = {
          enabled = var.feature_flags.new_ui_components
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        
        # Performance features
        edge_caching = {
          enabled = var.feature_flags.edge_caching
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
        lazy_loading = {
          enabled = var.feature_flags.lazy_loading
          variants = {
            enabled = { value = true }
            disabled = { value = false }
          }
        }
      },
      var.custom_feature_flags
    )
    values = {}
    version = "1.0.0"
  })
}

# Deployment Strategy
resource "aws_appconfig_deployment_strategy" "gradual" {
  name                           = "${var.name_prefix}-gradual-deployment"
  description                   = "Gradual deployment strategy for feature flags"
  deployment_duration_in_minutes = var.deployment_duration_minutes
  final_bake_time_in_minutes    = var.bake_time_minutes
  growth_factor                 = var.growth_factor
  growth_type                   = "LINEAR"
  replicate_to                  = "NONE"

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-gradual-deployment"
  })
}

# Deployment Strategy for immediate changes (emergency use)
resource "aws_appconfig_deployment_strategy" "immediate" {
  name                           = "${var.name_prefix}-immediate-deployment"
  description                   = "Immediate deployment strategy for emergency feature flag changes"
  deployment_duration_in_minutes = 0
  final_bake_time_in_minutes    = 0
  growth_factor                 = 100
  growth_type                   = "LINEAR"
  replicate_to                  = "NONE"

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-immediate-deployment"
  })
}

# IAM Role for AppConfig to access CloudWatch alarms
resource "aws_iam_role" "appconfig_alarm" {
  name = "${var.name_prefix}-appconfig-alarm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "appconfig.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-appconfig-alarm-role"
  })
}

# IAM Policy for AppConfig alarm role
resource "aws_iam_role_policy" "appconfig_alarm" {
  name = "${var.name_prefix}-appconfig-alarm-policy"
  role = aws_iam_role.appconfig_alarm.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:DescribeAlarms",
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Role for AppConfig configuration retrieval
resource "aws_iam_role" "appconfig_retrieval" {
  name = "${var.name_prefix}-appconfig-retrieval-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "appconfig.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-appconfig-retrieval-role"
  })
}

# CloudWatch Log Group for feature flag changes
resource "aws_cloudwatch_log_group" "feature_flags" {
  name              = "/aws/appconfig/${var.name_prefix}/feature-flags"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-feature-flags-logs"
  })
}

# EventBridge rule to capture feature flag deployment events
resource "aws_cloudwatch_event_rule" "feature_flag_deployments" {
  name        = "${var.name_prefix}-feature-flag-deployments"
  description = "Capture AppConfig deployment events for feature flags"

  event_pattern = jsonencode({
    source      = ["aws.appconfig"]
    detail-type = ["AppConfig Configuration Deployment Started", "AppConfig Configuration Deployment Completed"]
    detail = {
      application-id = [aws_appconfig_application.main.id]
    }
  })

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-feature-flag-events"
  })
}

# EventBridge target to send events to CloudWatch Logs
resource "aws_cloudwatch_event_target" "feature_flag_logs" {
  rule      = aws_cloudwatch_event_rule.feature_flag_deployments.name
  target_id = "FeatureFlagLogTarget"
  arn       = aws_cloudwatch_log_group.feature_flags.arn
}

# Lambda function for feature flag management
resource "aws_lambda_function" "feature_flag_manager" {
  filename         = data.archive_file.feature_flag_manager.output_path
  function_name    = "${var.name_prefix}-feature-flag-manager"
  role            = aws_iam_role.feature_flag_lambda.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.feature_flag_manager.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      APPCONFIG_APPLICATION_ID = aws_appconfig_application.main.id
      APPCONFIG_ENVIRONMENT_ID = aws_appconfig_environment.main.environment_id
      APPCONFIG_PROFILE_ID     = aws_appconfig_configuration_profile.feature_flags.configuration_profile_id
      GRADUAL_STRATEGY_ID      = aws_appconfig_deployment_strategy.gradual.id
      IMMEDIATE_STRATEGY_ID    = aws_appconfig_deployment_strategy.immediate.id
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-feature-flag-manager"
  })
}

# Lambda deployment package for feature flag manager
data "archive_file" "feature_flag_manager" {
  type        = "zip"
  output_path = "/tmp/feature_flag_manager.zip"
  
  source {
    content = templatefile("${path.module}/lambda/feature_flag_manager.py", {
      application_id = aws_appconfig_application.main.id
      environment_id = aws_appconfig_environment.main.environment_id
    })
    filename = "index.py"
  }
}

# IAM role for feature flag Lambda
resource "aws_iam_role" "feature_flag_lambda" {
  name = "${var.name_prefix}-feature-flag-lambda-role"

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
    Name = "${var.name_prefix}-feature-flag-lambda-role"
  })
}

# IAM policy for feature flag Lambda
resource "aws_iam_role_policy" "feature_flag_lambda" {
  name = "${var.name_prefix}-feature-flag-lambda-policy"
  role = aws_iam_role.feature_flag_lambda.id

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
          "appconfig:CreateHostedConfigurationVersion",
          "appconfig:StartDeployment",
          "appconfig:GetConfiguration",
          "appconfig:StopDeployment"
        ]
        Resource = "*"
      }
    ]
  })
}

# API Gateway for feature flag management API
resource "aws_api_gateway_rest_api" "feature_flags" {
  name        = "${var.name_prefix}-feature-flags-api"
  description = "API for managing feature flags"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-feature-flags-api"
  })
}

# API Gateway resource for feature flags
resource "aws_api_gateway_resource" "flags" {
  rest_api_id = aws_api_gateway_rest_api.feature_flags.id
  parent_id   = aws_api_gateway_rest_api.feature_flags.root_resource_id
  path_part   = "flags"
}

# API Gateway method for getting feature flags
resource "aws_api_gateway_method" "get_flags" {
  rest_api_id   = aws_api_gateway_rest_api.feature_flags.id
  resource_id   = aws_api_gateway_resource.flags.id
  http_method   = "GET"
  authorization = "AWS_IAM"
}

# API Gateway method for updating feature flags
resource "aws_api_gateway_method" "update_flags" {
  rest_api_id   = aws_api_gateway_rest_api.feature_flags.id
  resource_id   = aws_api_gateway_resource.flags.id
  http_method   = "PUT"
  authorization = "AWS_IAM"
}

# API Gateway integration for GET method
resource "aws_api_gateway_integration" "get_flags" {
  rest_api_id = aws_api_gateway_rest_api.feature_flags.id
  resource_id = aws_api_gateway_resource.flags.id
  http_method = aws_api_gateway_method.get_flags.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.feature_flag_manager.invoke_arn
}

# API Gateway integration for PUT method
resource "aws_api_gateway_integration" "update_flags" {
  rest_api_id = aws_api_gateway_rest_api.feature_flags.id
  resource_id = aws_api_gateway_resource.flags.id
  http_method = aws_api_gateway_method.update_flags.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.feature_flag_manager.invoke_arn
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.feature_flag_manager.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.feature_flags.execution_arn}/*/*"
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "feature_flags" {
  depends_on = [
    aws_api_gateway_integration.get_flags,
    aws_api_gateway_integration.update_flags,
  ]

  rest_api_id = aws_api_gateway_rest_api.feature_flags.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.flags.id,
      aws_api_gateway_method.get_flags.id,
      aws_api_gateway_method.update_flags.id,
      aws_api_gateway_integration.get_flags.id,
      aws_api_gateway_integration.update_flags.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway stage
resource "aws_api_gateway_stage" "feature_flags" {
  deployment_id = aws_api_gateway_deployment.feature_flags.id
  rest_api_id   = aws_api_gateway_rest_api.feature_flags.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-feature-flags-stage"
  })
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.name_prefix}/feature-flags"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-api-gateway-logs"
  })
}