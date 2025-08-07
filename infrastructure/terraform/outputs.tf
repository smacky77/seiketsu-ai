# Seiketsu AI - Terraform Outputs

# Networking Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = module.networking.vpc_cidr
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

# Database Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.database.rds_endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.database.rds_port
}

output "database_name" {
  description = "Database name"
  value       = module.database.database_name
}

# Cache Outputs
output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.cache.redis_endpoint
  sensitive   = true
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = module.cache.redis_port
}

# Container Orchestration Outputs
output "ecs_cluster_id" {
  description = "ECS cluster ID"
  value       = module.container_orchestration.ecs_cluster_id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.container_orchestration.ecs_cluster_name
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.container_orchestration.alb_dns_name
}

output "alb_zone_id" {
  description = "Application Load Balancer zone ID"
  value       = module.container_orchestration.alb_zone_id
}

# API Gateway Outputs
output "api_gateway_url" {
  description = "API Gateway URL"
  value       = module.api_gateway.api_gateway_url
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = module.api_gateway.api_gateway_id
}

# Frontend Hosting Outputs
output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.frontend_hosting.cloudfront_distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.frontend_hosting.cloudfront_domain_name
}

output "s3_bucket_name" {
  description = "S3 bucket name for frontend assets"
  value       = module.frontend_hosting.s3_bucket_name
}

# Security Outputs
output "security_group_ids" {
  description = "Security group IDs"
  value = {
    ecs      = module.security.ecs_security_group_id
    alb      = module.security.alb_security_group_id
    database = module.security.database_security_group_id
    cache    = module.security.cache_security_group_id
  }
}

# Secrets Manager Outputs
output "secrets_manager_arns" {
  description = "Secrets Manager ARNs"
  value       = module.secrets_manager.secret_arns
  sensitive   = true
}

# Monitoring Outputs
output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value       = module.monitoring.log_group_names
}

output "monitoring_dashboard_url" {
  description = "21dev.ai monitoring dashboard URL"
  value       = module.monitoring.dashboard_url
}

# Backup and Disaster Recovery Outputs
output "backup_vault_arn" {
  description = "AWS Backup vault ARN"
  value       = module.backup_disaster_recovery.backup_vault_arn
}

output "backup_plan_id" {
  description = "AWS Backup plan ID"
  value       = module.backup_disaster_recovery.backup_plan_id
}

# Multi-tenant Configuration Outputs
output "tenant_configuration" {
  description = "Multi-tenant configuration details"
  value = {
    max_tenants           = var.max_tenant_instances
    isolation_level       = var.tenant_isolation_level
    auto_scaling_enabled  = var.auto_scaling_enabled
    container_studio      = var.container_studio_enabled
  }
}

# Performance Configuration Outputs
output "performance_configuration" {
  description = "Performance configuration details"
  value = {
    voice_response_sla_ms = var.voice_response_sla_ms
    api_response_sla_ms   = var.api_response_sla_ms
    monitoring_provider   = var.monitoring_provider
  }
}

# Cost Optimization Outputs
output "cost_optimization_features" {
  description = "Enabled cost optimization features"
  value = {
    spot_instances       = var.use_spot_instances
    scheduled_scaling    = var.enable_scheduled_scaling
    cost_optimization    = var.enable_cost_optimization
  }
}

# Compliance Outputs
output "compliance_features" {
  description = "Enabled compliance features"
  value = {
    soc2_compliance           = var.soc2_compliance_enabled
    encryption_at_rest        = var.enable_encryption_at_rest
    encryption_in_transit     = var.enable_encryption_in_transit
    backup_retention_days     = var.db_backup_retention_period
    log_retention_days        = var.cloudwatch_log_retention_days
  }
}

# Environment Information
output "environment_info" {
  description = "Environment configuration details"
  value = {
    environment              = var.environment
    region                  = var.aws_region
    project_name            = var.project_name
    deployment_timestamp    = timestamp()
    terraform_workspace     = terraform.workspace
  }
}