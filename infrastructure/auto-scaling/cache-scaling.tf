# Seiketsu AI - ElastiCache Auto-scaling Configuration
# Redis cluster scaling for performance optimization

# ElastiCache Replication Group with Auto Scaling
resource "aws_elasticache_replication_group" "redis_cluster" {
  count                      = var.enable_elasticache_scaling ? 1 : 0
  replication_group_id      = "${var.name_prefix}-redis"
  description               = "Redis cluster for Seiketsu AI with auto-scaling"
  
  node_type                 = var.redis_node_type
  port                      = 6379
  parameter_group_name      = aws_elasticache_parameter_group.redis[0].name
  
  num_cache_clusters        = var.redis_initial_cache_clusters
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  subnet_group_name         = var.cache_subnet_group_name
  security_group_ids        = [var.cache_security_group_id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = var.redis_auth_token
  
  maintenance_window        = "sun:03:00-sun:04:00"
  snapshot_retention_limit  = 7
  snapshot_window          = "02:00-03:00"
  
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow_log[0].name
    destination_type = "cloudwatch-logs"
    log_format      = "text"
    log_type        = "slow-log"
  }
  
  tags = {
    Name        = "${var.name_prefix}-redis-cluster"
    Component   = "cache-scaling"
    Environment = var.environment
  }
}

# Redis Parameter Group for Optimization
resource "aws_elasticache_parameter_group" "redis" {
  count  = var.enable_elasticache_scaling ? 1 : 0
  family = "redis7.x"
  name   = "${var.name_prefix}-redis-params"
  
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
  
  parameter {
    name  = "timeout"
    value = "300"
  }
  
  parameter {
    name  = "tcp-keepalive"
    value = "300"
  }
  
  tags = {
    Name        = "${var.name_prefix}-redis-parameters"
    Component   = "cache-scaling"
  }
}

# CloudWatch Log Group for Redis Slow Log
resource "aws_cloudwatch_log_group" "redis_slow_log" {
  count             = var.enable_elasticache_scaling ? 1 : 0
  name              = "/aws/elasticache/redis/${var.name_prefix}/slow-log"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.name_prefix}-redis-slow-log"
    Component   = "cache-scaling"
  }
}

# Application Auto Scaling Target for ElastiCache
resource "aws_appautoscaling_target" "elasticache_target" {
  count              = var.enable_elasticache_scaling ? 1 : 0
  max_capacity       = var.redis_max_cache_clusters
  min_capacity       = var.redis_min_cache_clusters
  resource_id        = "replication-group/${aws_elasticache_replication_group.redis_cluster[0].id}"
  scalable_dimension = "elasticache:replication-group:Replicas"
  service_namespace  = "elasticache"
  
  tags = {
    Name        = "${var.name_prefix}-elasticache-scaling-target"
    Component   = "cache-scaling"
    Environment = var.environment
  }
}

# CPU-based Auto Scaling Policy for ElastiCache
resource "aws_appautoscaling_policy" "elasticache_scale_up_cpu" {
  count              = var.enable_elasticache_scaling ? 1 : 0
  name               = "${var.name_prefix}-elasticache-scale-up-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.elasticache_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.elasticache_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.elasticache_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ElastiCacheReplicationGroupCPUUtilization"
    }
    
    target_value       = 70.0
    scale_in_cooldown  = 300  # 5 minutes
    scale_out_cooldown = 300  # 5 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-elasticache-cpu-scaling"
    Component   = "cache-scaling"
    MetricType  = "cpu"
  }
}

# Memory-based Auto Scaling Policy for ElastiCache
resource "aws_appautoscaling_policy" "elasticache_scale_up_memory" {
  count              = var.enable_elasticache_scaling ? 1 : 0
  name               = "${var.name_prefix}-elasticache-scale-up-memory"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.elasticache_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.elasticache_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.elasticache_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "DatabaseMemoryUsagePercentage"
      namespace   = "AWS/ElastiCache"
      statistic   = "Average"
      
      dimensions = {
        CacheClusterId = "${var.name_prefix}-redis"
      }
    }
    
    target_value       = 75.0  # Target 75% memory utilization
    scale_in_cooldown  = 300   # 5 minutes
    scale_out_cooldown = 180   # 3 minutes - faster scale out for memory
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-elasticache-memory-scaling"
    Component   = "cache-scaling"
    MetricType  = "memory"
  }
}

# Connection-based Auto Scaling Policy
resource "aws_appautoscaling_policy" "elasticache_scale_up_connections" {
  count              = var.enable_elasticache_scaling ? 1 : 0
  name               = "${var.name_prefix}-elasticache-scale-up-connections"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.elasticache_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.elasticache_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.elasticache_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "CurrConnections"
      namespace   = "AWS/ElastiCache"
      statistic   = "Average"
      
      dimensions = {
        CacheClusterId = "${var.name_prefix}-redis"
      }
    }
    
    target_value       = 100.0  # Target 100 connections per cache node
    scale_in_cooldown  = 300    # 5 minutes
    scale_out_cooldown = 180    # 3 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-elasticache-connection-scaling"
    Component   = "cache-scaling"
    MetricType  = "connections"
  }
}

# Cache Hit Rate Based Scaling (Scale out when hit rate is low)
resource "aws_appautoscaling_policy" "elasticache_scale_by_hit_rate" {
  count              = var.enable_elasticache_scaling ? 1 : 0
  name               = "${var.name_prefix}-elasticache-scale-by-hit-rate"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.elasticache_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.elasticache_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.elasticache_target[0].service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown               = 300
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = 1
    }
  }
  
  tags = {
    Name        = "${var.name_prefix}-elasticache-hit-rate-scaling"
    Component   = "cache-scaling"
    MetricType  = "hit-rate"
  }
}

# CloudWatch Alarm for Low Cache Hit Rate
resource "aws_cloudwatch_metric_alarm" "cache_hit_rate_low" {
  count               = var.enable_elasticache_scaling ? 1 : 0
  alarm_name          = "${var.name_prefix}-cache-hit-rate-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  
  metric_query {
    id = "hit_rate"
    return_data = true
    
    metric {
      metric_name = "CacheHits"
      namespace   = "AWS/ElastiCache"
      period      = 300
      stat        = "Sum"
      
      dimensions = {
        CacheClusterId = "${var.name_prefix}-redis"
      }
    }
  }
  
  metric_query {
    id = "miss_rate"
    return_data = false
    
    metric {
      metric_name = "CacheMisses"
      namespace   = "AWS/ElastiCache"
      period      = 300
      stat        = "Sum"
      
      dimensions = {
        CacheClusterId = "${var.name_prefix}-redis"
      }
    }
  }
  
  metric_query {
    id          = "hit_rate_percentage"
    expression  = "hit_rate / (hit_rate + miss_rate) * 100"
    label       = "Cache Hit Rate Percentage"
    return_data = true
  }

  threshold           = "80"
  alarm_description   = "Cache hit rate is below 80%"
  alarm_actions       = [aws_appautoscaling_policy.elasticache_scale_by_hit_rate[0].arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.name_prefix}-cache-hit-rate-alarm"
    Component   = "cache-scaling"
    Type        = "performance"
  }
}

# Network I/O Based Scaling
resource "aws_appautoscaling_policy" "elasticache_scale_by_network_io" {
  count              = var.enable_elasticache_scaling ? 1 : 0
  name               = "${var.name_prefix}-elasticache-scale-by-network-io"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.elasticache_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.elasticache_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.elasticache_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "NetworkBytesOut"
      namespace   = "AWS/ElastiCache"
      statistic   = "Average"
      
      dimensions = {
        CacheClusterId = "${var.name_prefix}-redis"
      }
    }
    
    target_value       = 5000000.0  # 5MB/s target network output
    scale_in_cooldown  = 300        # 5 minutes
    scale_out_cooldown = 180        # 3 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-elasticache-network-io-scaling"
    Component   = "cache-scaling"
    MetricType  = "network"
  }
}

# Scheduled Scaling for ElastiCache (Business Hours)
resource "aws_appautoscaling_scheduled_action" "elasticache_scale_up_business_hours" {
  count              = var.enable_elasticache_scaling && var.enable_scheduled_scaling ? 1 : 0
  name               = "${var.name_prefix}-elasticache-scale-up-business-hours"
  service_namespace  = aws_appautoscaling_target.elasticache_target[0].service_namespace
  resource_id        = aws_appautoscaling_target.elasticache_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.elasticache_target[0].scalable_dimension
  
  schedule = "cron(0 7 * * MON-FRI)"  # 7 AM Monday-Friday UTC
  
  scalable_target_action {
    min_capacity = var.redis_min_cache_clusters + 1
    max_capacity = var.redis_max_cache_clusters
  }
  
  tags = {
    Name        = "${var.name_prefix}-elasticache-scheduled-scale-up"
    Component   = "cache-scaling"
    Type        = "scheduled"
  }
}

resource "aws_appautoscaling_scheduled_action" "elasticache_scale_down_off_hours" {
  count              = var.enable_elasticache_scaling && var.enable_scheduled_scaling ? 1 : 0
  name               = "${var.name_prefix}-elasticache-scale-down-off-hours"
  service_namespace  = aws_appautoscaling_target.elasticache_target[0].service_namespace
  resource_id        = aws_appautoscaling_target.elasticache_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.elasticache_target[0].scalable_dimension
  
  schedule = "cron(0 19 * * MON-FRI)"  # 7 PM Monday-Friday UTC
  
  scalable_target_action {
    min_capacity = var.redis_min_cache_clusters
    max_capacity = var.redis_max_cache_clusters
  }
  
  tags = {
    Name        = "${var.name_prefix}-elasticache-scheduled-scale-down"
    Component   = "cache-scaling"
    Type        = "scheduled"
  }
}

# Cache Performance Alarms
resource "aws_cloudwatch_metric_alarm" "redis_cpu_high" {
  count               = var.enable_elasticache_scaling ? 1 : 0
  alarm_name          = "${var.name_prefix}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Redis CPU utilization is high"
  alarm_actions       = [aws_sns_topic.cache_scaling_alerts.arn]

  dimensions = {
    CacheClusterId = "${var.name_prefix}-redis"
  }

  tags = {
    Name        = "${var.name_prefix}-redis-cpu-alarm"
    Component   = "cache-scaling"
    Type        = "monitoring"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory_high" {
  count               = var.enable_elasticache_scaling ? 1 : 0
  alarm_name          = "${var.name_prefix}-redis-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "Redis memory usage is high"
  alarm_actions       = [aws_sns_topic.cache_scaling_alerts.arn]

  dimensions = {
    CacheClusterId = "${var.name_prefix}-redis"
  }

  tags = {
    Name        = "${var.name_prefix}-redis-memory-alarm"
    Component   = "cache-scaling"
    Type        = "monitoring"
  }
}

# SNS Topic for Cache Scaling Notifications
resource "aws_sns_topic" "cache_scaling_alerts" {
  name = "${var.name_prefix}-cache-scaling-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-cache-scaling-alerts"
    Component   = "cache-scaling"
    Environment = var.environment
  }
}

# Cache Scaling Dashboard
resource "aws_cloudwatch_dashboard" "cache_scaling" {
  dashboard_name = "${var.name_prefix}-cache-scaling"

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
            ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", "${var.name_prefix}-redis"],
            [".", "DatabaseMemoryUsagePercentage", ".", "."],
            [".", "CurrConnections", ".", "."],
            [".", "NetworkBytesIn", ".", "."],
            [".", "NetworkBytesOut", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ElastiCache Performance Metrics"
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
            ["AWS/ElastiCache", "CacheHits", "CacheClusterId", "${var.name_prefix}-redis"],
            [".", "CacheMisses", ".", "."],
            ["Seiketsu/Performance", "CacheHitRate"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Cache Hit/Miss Metrics"
          period  = 300
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-cache-scaling-dashboard"
    Component   = "cache-scaling"
    Environment = var.environment
  }
}