# Seiketsu AI - Database Auto-scaling Configuration
# RDS Aurora and Read Replica scaling for multi-tenant workloads

# Aurora Auto Scaling Target for Read Replicas
resource "aws_appautoscaling_target" "aurora_read_replica_target" {
  count              = var.enable_aurora_scaling ? 1 : 0
  max_capacity       = var.aurora_max_read_replicas
  min_capacity       = var.aurora_min_read_replicas
  resource_id        = "cluster:${var.aurora_cluster_identifier}"
  scalable_dimension = "rds:cluster:ReadReplicaCount"
  service_namespace  = "rds"
  
  tags = {
    Name        = "${var.name_prefix}-aurora-scaling-target"
    Component   = "database-scaling"
    Environment = var.environment
  }
}

# Aurora CPU-based Auto Scaling Policy
resource "aws_appautoscaling_policy" "aurora_scale_up_cpu" {
  count              = var.enable_aurora_scaling ? 1 : 0
  name               = "${var.name_prefix}-aurora-scale-up-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.aurora_read_replica_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.aurora_read_replica_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.aurora_read_replica_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "RDSReaderAverageCPUUtilization"
    }
    
    target_value       = 70.0
    scale_in_cooldown  = 300  # 5 minutes
    scale_out_cooldown = 300  # 5 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-aurora-cpu-scaling"
    Component   = "database-scaling"
    MetricType  = "cpu"
  }
}

# Aurora Connection-based Auto Scaling
resource "aws_appautoscaling_policy" "aurora_scale_up_connections" {
  count              = var.enable_aurora_scaling ? 1 : 0
  name               = "${var.name_prefix}-aurora-scale-up-connections"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.aurora_read_replica_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.aurora_read_replica_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.aurora_read_replica_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "RDSReaderAverageDatabaseConnections"
    }
    
    target_value       = 40.0  # Target 40 connections per read replica
    scale_in_cooldown  = 300   # 5 minutes
    scale_out_cooldown = 180   # 3 minutes - faster scale out for connections
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-aurora-connection-scaling"
    Component   = "database-scaling"
    MetricType  = "connections"
  }
}

# Custom Metric for Database Query Performance
resource "aws_appautoscaling_policy" "aurora_scale_by_query_performance" {
  count              = var.enable_aurora_scaling ? 1 : 0
  name               = "${var.name_prefix}-aurora-scale-by-query-performance"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.aurora_read_replica_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.aurora_read_replica_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.aurora_read_replica_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "DatabaseQueryTime"
      namespace   = "Seiketsu/Performance"
      statistic   = "Average"
    }
    
    target_value       = 80.0  # Target 80ms average query time
    scale_in_cooldown  = 600   # 10 minutes
    scale_out_cooldown = 300   # 5 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-aurora-query-performance-scaling"
    Component   = "database-scaling"
    MetricType  = "performance"
  }
}

# Scheduled Scaling for Database (Business Hours)
resource "aws_appautoscaling_scheduled_action" "aurora_scale_up_business_hours" {
  count              = var.enable_aurora_scaling && var.enable_scheduled_scaling ? 1 : 0
  name               = "${var.name_prefix}-aurora-scale-up-business-hours"
  service_namespace  = aws_appautoscaling_target.aurora_read_replica_target[0].service_namespace
  resource_id        = aws_appautoscaling_target.aurora_read_replica_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.aurora_read_replica_target[0].scalable_dimension
  
  schedule = "cron(0 7 * * MON-FRI)"  # 7 AM Monday-Friday UTC
  
  scalable_target_action {
    min_capacity = var.aurora_min_read_replicas + 1
    max_capacity = var.aurora_max_read_replicas
  }
  
  tags = {
    Name        = "${var.name_prefix}-aurora-scheduled-scale-up"
    Component   = "database-scaling"
    Type        = "scheduled"
  }
}

resource "aws_appautoscaling_scheduled_action" "aurora_scale_down_off_hours" {
  count              = var.enable_aurora_scaling && var.enable_scheduled_scaling ? 1 : 0
  name               = "${var.name_prefix}-aurora-scale-down-off-hours"
  service_namespace  = aws_appautoscaling_target.aurora_read_replica_target[0].service_namespace
  resource_id        = aws_appautoscaling_target.aurora_read_replica_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.aurora_read_replica_target[0].scalable_dimension
  
  schedule = "cron(0 19 * * MON-FRI)"  # 7 PM Monday-Friday UTC
  
  scalable_target_action {
    min_capacity = var.aurora_min_read_replicas
    max_capacity = var.aurora_max_read_replicas
  }
  
  tags = {
    Name        = "${var.name_prefix}-aurora-scheduled-scale-down"
    Component   = "database-scaling"
    Type        = "scheduled"
  }
}

# Multi-tenant Database Scaling Based on Tenant Activity
resource "aws_appautoscaling_policy" "aurora_scale_by_tenant_activity" {
  count              = var.enable_aurora_scaling ? 1 : 0
  name               = "${var.name_prefix}-aurora-scale-by-tenant-activity"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.aurora_read_replica_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.aurora_read_replica_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.aurora_read_replica_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "ActiveTenants"
      namespace   = "Seiketsu/MultiTenant"
      statistic   = "Maximum"
    }
    
    target_value       = var.tenants_per_read_replica  # e.g., 10 tenants per read replica
    scale_in_cooldown  = 900     # 15 minutes - longer for tenant-based DB scaling
    scale_out_cooldown = 300     # 5 minutes
    
    disable_scale_in = false
  }
  
  tags = {
    Name        = "${var.name_prefix}-aurora-tenant-activity-scaling"
    Component   = "database-scaling"
    MetricType  = "business"
  }
}

# Aurora Serverless v2 Scaling (if using Aurora Serverless)
resource "aws_rds_cluster" "aurora_serverless_v2" {
  count               = var.enable_aurora_serverless ? 1 : 0
  cluster_identifier  = "${var.name_prefix}-aurora-serverless"
  engine             = "aurora-mysql"
  engine_mode        = "provisioned"
  engine_version     = var.aurora_engine_version
  database_name      = var.database_name
  master_username    = var.database_username
  master_password    = var.database_password
  
  serverlessv2_scaling_configuration {
    max_capacity = var.aurora_serverless_max_capacity
    min_capacity = var.aurora_serverless_min_capacity
  }
  
  vpc_security_group_ids = [var.database_security_group_id]
  db_subnet_group_name   = var.db_subnet_group_name
  
  backup_retention_period = var.backup_retention_period
  preferred_backup_window = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  
  storage_encrypted = true
  kms_key_id       = var.kms_key_id
  
  deletion_protection = var.enable_deletion_protection
  skip_final_snapshot = false
  final_snapshot_identifier = "${var.name_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]
  
  tags = {
    Name        = "${var.name_prefix}-aurora-serverless"
    Component   = "database"
    Environment = var.environment
    Scaling     = "serverless"
  }
  
  lifecycle {
    ignore_changes = [final_snapshot_identifier]
  }
}

# CloudWatch Alarms for Database Scaling Events
resource "aws_cloudwatch_metric_alarm" "aurora_read_replica_high_cpu" {
  count               = var.enable_aurora_scaling ? 1 : 0
  alarm_name          = "${var.name_prefix}-aurora-read-replica-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Aurora read replica CPU is high - may need scaling"
  alarm_actions       = [aws_sns_topic.database_scaling_alerts.arn]

  dimensions = {
    DBClusterIdentifier = var.aurora_cluster_identifier
  }

  tags = {
    Name        = "${var.name_prefix}-aurora-cpu-alarm"
    Component   = "database-scaling"
    Type        = "monitoring"
  }
}

resource "aws_cloudwatch_metric_alarm" "aurora_read_replica_high_connections" {
  count               = var.enable_aurora_scaling ? 1 : 0
  alarm_name          = "${var.name_prefix}-aurora-read-replica-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "50"
  alarm_description   = "Aurora read replica connections are high"
  alarm_actions       = [aws_sns_topic.database_scaling_alerts.arn]

  dimensions = {
    DBClusterIdentifier = var.aurora_cluster_identifier
  }

  tags = {
    Name        = "${var.name_prefix}-aurora-connections-alarm"
    Component   = "database-scaling"
    Type        = "monitoring"
  }
}

# SNS Topic for Database Scaling Notifications
resource "aws_sns_topic" "database_scaling_alerts" {
  name = "${var.name_prefix}-database-scaling-alerts"
  
  tags = {
    Name        = "${var.name_prefix}-database-scaling-alerts"
    Component   = "database-scaling"
    Environment = var.environment
  }
}

# Database Scaling Dashboard
resource "aws_cloudwatch_dashboard" "database_scaling" {
  dashboard_name = "${var.name_prefix}-database-scaling"

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
            ["AWS/RDS", "CPUUtilization", "DBClusterIdentifier", var.aurora_cluster_identifier],
            [".", "DatabaseConnections", ".", "."],
            [".", "ReadLatency", ".", "."],
            [".", "WriteLatency", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Aurora Cluster Performance"
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
            ["AWS/RDS", "AuroraReplicaLag", "DBClusterIdentifier", var.aurora_cluster_identifier],
            ["Seiketsu/Performance", "DatabaseQueryTime"],
            ["Seiketsu/MultiTenant", "ActiveTenants"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Database Scaling Triggers"
          period  = 300
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-database-scaling-dashboard"
    Component   = "database-scaling"
    Environment = var.environment
  }
}