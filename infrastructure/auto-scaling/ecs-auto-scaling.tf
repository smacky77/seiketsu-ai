# Seiketsu AI - ECS Auto-scaling Configuration
# Comprehensive auto-scaling for application services

# Application Auto Scaling Target for ECS Service
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${var.cluster_name}/${var.service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
  
  tags = {
    Name        = "${var.name_prefix}-ecs-scaling-target"
    Component   = "auto-scaling"
    Environment = var.environment
  }
}

# CPU-based Auto Scaling Policy (Scale Up)
resource "aws_appautoscaling_policy" "ecs_scale_up_cpu" {
  name               = "${var.name_prefix}-ecs-scale-up-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    
    target_value       = 70.0
    scale_in_cooldown  = 300  # 5 minutes
    scale_out_cooldown = 180  # 3 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-ecs-cpu-scaling"
    Component   = "auto-scaling"
    MetricType  = "cpu"
  }
}

# Memory-based Auto Scaling Policy
resource "aws_appautoscaling_policy" "ecs_scale_up_memory" {
  name               = "${var.name_prefix}-ecs-scale-up-memory"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    
    target_value       = 80.0
    scale_in_cooldown  = 300  # 5 minutes
    scale_out_cooldown = 180  # 3 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-ecs-memory-scaling"
    Component   = "auto-scaling"
    MetricType  = "memory"
  }
}

# Custom Metric Auto Scaling - Voice Response Time
resource "aws_appautoscaling_policy" "ecs_scale_up_voice_latency" {
  name               = "${var.name_prefix}-ecs-scale-up-voice-latency"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "VoiceResponseTime"
      namespace   = "Seiketsu/Performance"
      statistic   = "Average"
    }
    
    target_value       = 1800.0  # Target 1.8s to stay under 2s SLA
    scale_in_cooldown  = 600     # 10 minutes - longer cooldown for performance metrics
    scale_out_cooldown = 120     # 2 minutes - faster scale out for performance
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-ecs-voice-latency-scaling"
    Component   = "auto-scaling"
    MetricType  = "performance"
  }
}

# Request Count-based Auto Scaling
resource "aws_appautoscaling_policy" "ecs_scale_up_requests" {
  name               = "${var.name_prefix}-ecs-scale-up-requests"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "RequestCount"
      namespace   = "AWS/ApplicationELB"
      statistic   = "Sum"
      
      dimensions = {
        LoadBalancer = var.alb_arn_suffix
      }
    }
    
    target_value       = 1000.0  # Target 1000 requests per 5 minutes per instance
    scale_in_cooldown  = 300     # 5 minutes
    scale_out_cooldown = 120     # 2 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-ecs-request-scaling"
    Component   = "auto-scaling"
    MetricType  = "requests"
  }
}

# Scheduled Scaling for Predictable Load Patterns
resource "aws_appautoscaling_scheduled_action" "scale_up_business_hours" {
  count              = var.enable_scheduled_scaling ? 1 : 0
  name               = "${var.name_prefix}-scale-up-business-hours"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  
  schedule = "cron(0 8 * * MON-FRI)"  # 8 AM Monday-Friday UTC
  
  scalable_target_action {
    min_capacity = var.min_capacity + 2
    max_capacity = var.max_capacity
  }
  
  tags = {
    Name        = "${var.name_prefix}-scheduled-scale-up"
    Component   = "auto-scaling"
    Type        = "scheduled"
  }
}

resource "aws_appautoscaling_scheduled_action" "scale_down_off_hours" {
  count              = var.enable_scheduled_scaling ? 1 : 0
  name               = "${var.name_prefix}-scale-down-off-hours"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  
  schedule = "cron(0 18 * * MON-FRI)"  # 6 PM Monday-Friday UTC
  
  scalable_target_action {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }
  
  tags = {
    Name        = "${var.name_prefix}-scheduled-scale-down"
    Component   = "auto-scaling"
    Type        = "scheduled"
  }
}

# Weekend scaling - minimal capacity
resource "aws_appautoscaling_scheduled_action" "scale_down_weekend" {
  count              = var.enable_scheduled_scaling ? 1 : 0
  name               = "${var.name_prefix}-scale-down-weekend"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  
  schedule = "cron(0 0 * * SAT)"  # Saturday midnight UTC
  
  scalable_target_action {
    min_capacity = max(1, var.min_capacity - 1)
    max_capacity = var.max_capacity
  }
  
  tags = {
    Name        = "${var.name_prefix}-scheduled-weekend-scale"
    Component   = "auto-scaling"
    Type        = "scheduled"
  }
}

# Predictive Scaling (if supported in region)
resource "aws_appautoscaling_policy" "ecs_predictive_scaling" {
  count              = var.enable_predictive_scaling ? 1 : 0
  name               = "${var.name_prefix}-ecs-predictive-scaling"
  policy_type        = "PredictiveScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  predictive_scaling_policy_configuration {
    metric_specification {
      target_value = 70.0
      predefined_metric_pair_specification {
        predefined_metric_type = "ECSServiceAverageCPUUtilization"
      }
    }
    
    mode                         = "ForecastOnly"  # Start with forecast only
    scheduling_buffer_time       = 300            # 5 minutes buffer
    max_capacity_breach_behavior = "IncreaseMaxCapacity"
    max_capacity_buffer          = 10
  }
  
  tags = {
    Name        = "${var.name_prefix}-predictive-scaling"
    Component   = "auto-scaling"
    Type        = "predictive"
  }
}

# Step Scaling Policy for Emergency Scale Out
resource "aws_appautoscaling_policy" "ecs_emergency_scale_out" {
  name               = "${var.name_prefix}-ecs-emergency-scale-out"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown               = 60   # 1 minute for emergency scaling
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = 50
      scaling_adjustment          = 2
    }

    step_adjustment {
      metric_interval_lower_bound = 50
      scaling_adjustment          = 5
    }
  }
  
  tags = {
    Name        = "${var.name_prefix}-emergency-scale-out"
    Component   = "auto-scaling"
    Type        = "emergency"
  }
}

# CloudWatch Alarms to trigger emergency scaling
resource "aws_cloudwatch_metric_alarm" "emergency_cpu_alarm" {
  alarm_name          = "${var.name_prefix}-emergency-cpu-scaling"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"  # Immediate response
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"  # 1 minute periods
  statistic           = "Average"
  threshold           = "90"
  alarm_description   = "Emergency CPU-based scaling"
  alarm_actions       = [aws_appautoscaling_policy.ecs_emergency_scale_out.arn]

  dimensions = {
    ServiceName = var.service_name
    ClusterName = var.cluster_name
  }

  tags = {
    Name        = "${var.name_prefix}-emergency-cpu-alarm"
    Component   = "auto-scaling"
    Type        = "emergency"
  }
}

# Multi-tenant Scaling Based on Active Tenants
resource "aws_appautoscaling_policy" "ecs_scale_by_tenants" {
  name               = "${var.name_prefix}-ecs-scale-by-tenants"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "ActiveTenants"
      namespace   = "Seiketsu/MultiTenant"
      statistic   = "Maximum"
    }
    
    target_value       = var.tenants_per_instance  # e.g., 2 tenants per instance
    scale_in_cooldown  = 900     # 15 minutes - longer for tenant-based scaling
    scale_out_cooldown = 300     # 5 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-tenant-based-scaling"
    Component   = "auto-scaling"
    MetricType  = "business"
  }
}

# Voice Processing Queue Depth Scaling
resource "aws_appautoscaling_policy" "ecs_scale_by_queue_depth" {
  name               = "${var.name_prefix}-ecs-scale-by-queue-depth"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "ConcurrentVoiceRequests"
      namespace   = "Seiketsu/Performance"
      statistic   = "Maximum"
    }
    
    target_value       = var.max_concurrent_voice_requests  # e.g., 10 concurrent requests per instance
    scale_in_cooldown  = 300     # 5 minutes
    scale_out_cooldown = 60      # 1 minute - fast response for voice processing
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-queue-depth-scaling"
    Component   = "auto-scaling"
    MetricType  = "queue"
  }
}

# Auto Scaling Notifications
resource "aws_sns_topic" "autoscaling_notifications" {
  name = "${var.name_prefix}-autoscaling-notifications"
  
  tags = {
    Name        = "${var.name_prefix}-autoscaling-notifications"
    Component   = "auto-scaling"
    Environment = var.environment
  }
}

# Auto Scaling Event Notifications
resource "aws_autoscaling_notification" "scaling_notifications" {
  group_names = [var.asg_name]
  
  notifications = [
    "autoscaling:EC2_INSTANCE_LAUNCH",
    "autoscaling:EC2_INSTANCE_TERMINATE",
    "autoscaling:EC2_INSTANCE_LAUNCH_ERROR",
    "autoscaling:EC2_INSTANCE_TERMINATE_ERROR",
  ]
  
  topic_arn = aws_sns_topic.autoscaling_notifications.arn
}

# CloudWatch Dashboard for Auto Scaling Metrics
resource "aws_cloudwatch_dashboard" "autoscaling_dashboard" {
  dashboard_name = "${var.name_prefix}-autoscaling-metrics"

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
            ["AWS/ECS", "RunningTaskCount", "ServiceName", var.service_name, "ClusterName", var.cluster_name],
            ["AWS/ApplicationELB", "TargetGroupHealthyHostCount", "TargetGroup", var.target_group_arn_suffix]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Service Scaling Metrics"
          period  = 300
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
            ["Seiketsu/Performance", "VoiceResponseTime"],
            ["Seiketsu/MultiTenant", "ActiveTenants"],
            ["Seiketsu/Performance", "ConcurrentVoiceRequests"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Business Scaling Triggers"
          period  = 300
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-autoscaling-dashboard"
    Component   = "auto-scaling"
    Environment = var.environment
  }
}