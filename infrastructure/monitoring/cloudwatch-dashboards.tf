# Seiketsu AI - Enhanced CloudWatch Dashboards
# Comprehensive monitoring with performance optimization focus

# Main Infrastructure Dashboard
resource "aws_cloudwatch_dashboard" "infrastructure_overview" {
  dashboard_name = "${var.name_prefix}-infrastructure-overview"

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
            [".", "MemoryUtilization", ".", ".", ".", "."],
            [".", "RunningTaskCount", ".", ".", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ECS Service Performance"
          period  = 300
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "${var.name_prefix}-database"],
            [".", "DatabaseConnections", ".", "."],
            [".", "ReadLatency", ".", "."],
            [".", "WriteLatency", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "RDS Performance Metrics"
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
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "${var.name_prefix}-alb"],
            [".", "RequestCount", ".", "."],
            [".", "NewConnectionCount", ".", "."],
            [".", "ActiveConnectionCount", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Load Balancer Performance"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", "${var.name_prefix}-redis"],
            [".", "NetworkBytesIn", ".", "."],
            [".", "NetworkBytesOut", ".", "."],
            [".", "CurrConnections", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ElastiCache Performance"
          period  = 300
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-infrastructure-dashboard"
    Component   = "monitoring"
    Environment = var.environment
  }
}

# Voice Performance Dashboard
resource "aws_cloudwatch_dashboard" "voice_performance" {
  dashboard_name = "${var.name_prefix}-voice-performance"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 24
        height = 6
        properties = {
          metrics = [
            ["Seiketsu/Performance", "VoiceResponseTime"],
            [".", "VoiceProcessingLatency"],
            [".", "ElevenLabsAPILatency"],
            [".", "OpenAIAPILatency"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Voice Processing Performance (Target: <2s)"
          period  = 300
          annotations = {
            horizontal = [
              {
                label = "SLA Threshold (2000ms)"
                value = 2000
                fill  = "above"
              }
            ]
          }
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
            ["Seiketsu/Performance", "VoiceRequestsPerMinute"],
            [".", "ConcurrentVoiceRequests"],
            [".", "VoiceRequestSuccessRate"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Voice Request Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["Seiketsu/Performance", "VoiceErrorRate"],
            [".", "VoiceTimeouts"],
            [".", "VoiceRetries"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Voice Error Tracking"
          period  = 300
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-voice-performance-dashboard"
    Component   = "monitoring"
    Environment = var.environment
  }
}

# Cost Optimization Dashboard
resource "aws_cloudwatch_dashboard" "cost_optimization" {
  dashboard_name = "${var.name_prefix}-cost-optimization"

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
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD"],
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", "ServiceName", "AmazonEC2"],
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", "ServiceName", "AmazonRDS"],
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", "ServiceName", "AmazonS3"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "Estimated Costs by Service"
          period  = 86400
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization"],
            ["AWS/RDS", "CPUUtilization"],
            ["AWS/ElastiCache", "CPUUtilization"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Resource Utilization (Optimization Targets)"
          period  = 300
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-cost-dashboard"
    Component   = "monitoring"
    Environment = var.environment
  }
}

# Security Dashboard
resource "aws_cloudwatch_dashboard" "security_monitoring" {
  dashboard_name = "${var.name_prefix}-security-monitoring"

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
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", "${var.name_prefix}-alb"],
            [".", "HTTPCode_Target_5XX_Count", ".", "."],
            ["AWS/WAFv2", "BlockedRequests", "WebACL", "${var.name_prefix}-waf"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Security Metrics"
          period  = 300
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          query   = "SOURCE '/aws/waf/${var.name_prefix}' | fields @timestamp, httpRequest.clientIP, action\n| filter action = \"BLOCK\"\n| stats count() by httpRequest.clientIP\n| sort @timestamp desc\n| limit 20"
          region  = var.aws_region
          title   = "Blocked IP Addresses"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-security-dashboard"
    Component   = "monitoring"
    Environment = var.environment
  }
}

# Multi-tenant Usage Dashboard
resource "aws_cloudwatch_dashboard" "tenant_usage" {
  dashboard_name = "${var.name_prefix}-tenant-usage"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 24
        height = 6
        properties = {
          metrics = [
            ["Seiketsu/MultiTenant", "ActiveTenants"],
            [".", "TotalRequests"],
            [".", "RequestsPerTenant"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Multi-tenant Usage Metrics"
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
            ["Seiketsu/MultiTenant", "TenantResourceUsage"],
            [".", "TenantStorageUsage"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Tenant Resource Consumption"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["Seiketsu/MultiTenant", "TenantErrorRate"],
            [".", "TenantThrottling"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Tenant Error and Throttling"
          period  = 300
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-tenant-dashboard"
    Component   = "monitoring"
    Environment = var.environment
  }
}