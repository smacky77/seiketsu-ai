# Seiketsu AI - Production Environment Configuration

# Environment Settings
environment = "production"
project_name = "seiketsu-ai"
aws_region = "us-east-1"

# Domain Configuration
domain_name = "seiketsu-ai.com"

# Network Configuration
vpc_cidr = "10.0.0.0/16"

# Blue-Green Deployment Configuration
enable_blue_green = true
current_environment = "blue"
target_environment = "green"

# Database Configuration - Optimized for Production
db_instance_class = "db.r6g.2xlarge"
db_allocated_storage = 1000
db_max_allocated_storage = 10000
db_backup_retention_period = 30
db_backup_window = "03:00-04:00"
db_maintenance_window = "sun:04:00-sun:05:00"
enable_multi_az = true
enable_encryption = true
enable_performance_insights = true
performance_insights_retention = 30

# Read Replica Configuration
enable_read_replica = true
read_replica_count = 2
read_replica_instance_class = "db.r6g.xlarge"

# Cache Configuration - Redis Cluster
cache_node_type = "cache.r6g.xlarge"
cache_num_nodes = 3
cache_parameter_group = "default.redis7.cluster.on"
enable_cache_clustering = true

# ECS Configuration - High Availability
ecs_task_cpu = 2048
ecs_task_memory = 4096
ecs_desired_count = 5
ecs_min_capacity = 3
ecs_max_capacity = 40

# Auto Scaling Configuration
enable_auto_scaling = true
scale_up_threshold = 60
scale_down_threshold = 20
scale_up_cooldown = 300
scale_down_cooldown = 600

# Load Balancer Configuration
enable_sticky_sessions = true
health_check_path = "/health"
health_check_interval = 30
health_check_timeout = 5
healthy_threshold = 2
unhealthy_threshold = 3

# Monitoring Configuration
enable_detailed_monitoring = true
enable_container_insights = true
log_retention_days = 90
performance_insights_retention = 30

# Security Configuration
enable_waf = true
enable_shield_advanced = true
ssl_policy = "ELBSecurityPolicy-TLS-1-2-2017-01"
enable_access_logs = true

# CloudFront Configuration
cloudfront_price_class = "PriceClass_All"
cloudfront_ttl_default = 86400
cloudfront_ttl_max = 31536000
enable_compression = true

# Feature Flags for Production
feature_flags = {
  voice_ai = true
  analytics = true
  multi_tenant = true
  canary_deployments = true
  blue_green_deployments = true
  feature_flags = true
  advanced_monitoring = true
  premium_features = true
  enterprise_features = true
  compliance_mode = true
}

# Cost Optimization for Production
cost_optimization = {
  enable_spot_instances = false
  enable_scheduled_scaling = true
  enable_hibernation = false
  reserved_capacity_percentage = 60
}

# Backup Configuration
backup_retention_days = 90
enable_point_in_time_recovery = true
enable_cross_region_backup = true
backup_destination_region = "us-west-2"

# Disaster Recovery Configuration
enable_disaster_recovery = true
rto_minutes = 30
rpo_minutes = 15
dr_region = "us-west-2"

# Compliance Configuration
enable_config_rules = true
enable_cloudtrail = true
enable_guardduty = true
enable_security_hub = true
enable_inspector = true

# Multi-Tenant Configuration
max_tenants = 40
tenant_isolation_level = "strict"
enable_tenant_metrics = true

# Performance Configuration
api_gateway_throttling = {
  burst_limit = 5000
  rate_limit = 2000
}

voice_processing = {
  max_concurrent_sessions = 200
  response_time_sla_ms = 2000
  quality_threshold = 0.95
}

# Tags
tags = {
  Environment = "production"
  Project = "Seiketsu-AI"
  Owner = "DevOps"
  CostCenter = "Production"
  Purpose = "Customer-Facing"
  DataClassification = "Confidential"
  Compliance = "SOC2"
  BackupRequired = "true"
  MonitoringLevel = "Critical"
}