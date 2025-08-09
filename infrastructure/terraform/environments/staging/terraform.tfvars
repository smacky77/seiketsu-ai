# Seiketsu AI - Staging Environment Configuration

# Environment Settings
environment = "staging"
project_name = "seiketsu-ai"
aws_region = "us-east-1"

# Domain Configuration
domain_name = "staging.seiketsu-ai.com"

# Network Configuration
vpc_cidr = "10.1.0.0/16"

# Blue-Green Deployment Configuration
enable_blue_green = true
current_environment = "blue"
target_environment = "green"

# Database Configuration
db_instance_class = "db.t3.medium"
db_allocated_storage = 100
db_max_allocated_storage = 500
db_backup_retention_period = 7
db_backup_window = "03:00-04:00"
db_maintenance_window = "sun:04:00-sun:05:00"
enable_multi_az = false
enable_encryption = true

# Cache Configuration
cache_node_type = "cache.t3.medium"
cache_num_nodes = 2
cache_parameter_group = "default.redis7"

# ECS Configuration
ecs_task_cpu = 512
ecs_task_memory = 1024
ecs_desired_count = 2
ecs_min_capacity = 1
ecs_max_capacity = 5

# Auto Scaling Configuration
enable_auto_scaling = true
scale_up_threshold = 70
scale_down_threshold = 30
scale_up_cooldown = 300
scale_down_cooldown = 300

# Monitoring Configuration
enable_detailed_monitoring = true
log_retention_days = 14
performance_insights_retention = 7

# Security Configuration
enable_waf = true
enable_shield_advanced = false
ssl_policy = "ELBSecurityPolicy-TLS-1-2-2017-01"

# Feature Flags for Staging
feature_flags = {
  voice_ai = true
  analytics = true
  multi_tenant = true
  canary_deployments = true
  blue_green_deployments = true
  feature_flags = true
  advanced_monitoring = false
  premium_features = false
}

# Cost Optimization for Staging
cost_optimization = {
  enable_spot_instances = true
  enable_scheduled_scaling = true
  enable_hibernation = true
  reserved_capacity_percentage = 0
}

# Backup Configuration
backup_retention_days = 7
enable_point_in_time_recovery = true
enable_cross_region_backup = false

# Tags
tags = {
  Environment = "staging"
  Project = "Seiketsu-AI"
  Owner = "DevOps"
  CostCenter = "Engineering"
  Purpose = "Development"
  DataClassification = "Internal"
  Compliance = "Development"
}