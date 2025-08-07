# Seiketsu AI - AWS Infrastructure Configuration
# Multi-tenant Real Estate Voice Agent Platform

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }

  backend "s3" {
    bucket         = "seiketsu-ai-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "seiketsu-ai-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project           = "Seiketsu-AI"
      Environment       = var.environment
      Owner             = "DevOps"
      CostCenter        = "Engineering"
      Compliance        = "SOC2"
      ManagedBy         = "Terraform"
      ContainerStudio   = "enabled"
      MonitoringSystem  = "21dev-ai"
    }
  }
}

# Random password for RDS
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# Local values for consistency
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Terraform   = "true"
  }

  # Multi-tenant configuration
  max_tenants = 40
  
  # Container Studio integration
  container_studio_config = {
    orchestration_engine = "ecs"
    service_mesh        = "enabled"
    auto_scaling       = "enabled"
    health_checks      = "comprehensive"
  }

  # 21dev.ai monitoring integration
  monitoring_config = {
    provider           = "21dev-ai"
    metrics_endpoint   = var.monitoring_endpoint
    alert_channels     = ["slack", "email", "pagerduty"]
    performance_sla    = "sub-2s-voice-response"
  }
}

# Include modules
module "networking" {
  source = "./modules/networking"

  name_prefix         = local.name_prefix
  vpc_cidr            = var.vpc_cidr
  availability_zones  = data.aws_availability_zones.available.names
  enable_nat_gateway  = true
  enable_vpn_gateway  = false
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = local.common_tags
}

module "security" {
  source = "./modules/security"

  name_prefix = local.name_prefix
  vpc_id      = module.networking.vpc_id
  vpc_cidr    = var.vpc_cidr
  
  tags = local.common_tags
}

module "database" {
  source = "./modules/database"

  name_prefix             = local.name_prefix
  vpc_id                  = module.networking.vpc_id
  private_subnet_ids      = module.networking.private_subnet_ids
  database_security_group = module.security.database_security_group_id
  
  db_password = random_password.db_password.result
  
  # Multi-tenant database configuration
  instance_class          = "db.r6g.2xlarge"  # Optimized for 40 tenants
  allocated_storage       = 1000
  max_allocated_storage   = 10000
  backup_retention_period = 30
  
  tags = local.common_tags
}

module "cache" {
  source = "./modules/cache"

  name_prefix           = local.name_prefix
  vpc_id                = module.networking.vpc_id
  private_subnet_ids    = module.networking.private_subnet_ids
  cache_security_group  = module.security.cache_security_group_id
  
  # Redis cluster for multi-tenant caching
  node_type             = "cache.r6g.xlarge"
  num_cache_clusters    = 3
  
  tags = local.common_tags
}

module "container_orchestration" {
  source = "./modules/ecs"

  name_prefix                = local.name_prefix
  vpc_id                     = module.networking.vpc_id
  private_subnet_ids         = module.networking.private_subnet_ids
  public_subnet_ids          = module.networking.public_subnet_ids
  ecs_security_group         = module.security.ecs_security_group_id
  alb_security_group         = module.security.alb_security_group_id
  
  # Container Studio configuration
  container_studio_config = local.container_studio_config
  
  # Multi-tenant scaling configuration
  min_capacity = 2
  max_capacity = 40  # Support for 40 client instances
  
  tags = local.common_tags
}

module "api_gateway" {
  source = "./modules/api_gateway"

  name_prefix        = local.name_prefix
  environment        = var.environment
  vpc_id            = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  alb_security_group = module.security.alb_security_group_id
  domain_name       = var.domain_name
  
  tags = local.common_tags
}

module "frontend_hosting" {
  source = "./modules/cloudfront"

  name_prefix        = local.name_prefix
  domain_name        = var.domain_name
  api_domain_name    = "api.${var.domain_name}"
  ssl_certificate_arn = aws_acm_certificate.frontend.arn
  waf_web_acl_arn    = module.api_gateway.waf_web_acl_arn
  
  # S3 bucket for Next.js static assets
  create_s3_bucket = true
  
  # CloudFront configuration for global performance
  price_class = "PriceClass_All"
  
  tags = local.common_tags
}

# SSL Certificate for Frontend
resource "aws_acm_certificate" "frontend" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-cert"
  })
}

module "secrets_manager" {
  source = "./modules/secrets"

  name_prefix = local.name_prefix
  
  secrets = {
    database_password   = random_password.db_password.result
    redis_auth_token   = random_password.redis_auth.result
    elevenlabs_api_key = var.elevenlabs_api_key
    openai_api_key     = var.openai_api_key
    jwt_secret         = var.jwt_secret
    supabase_key       = var.supabase_key
    monitoring_api_key = var.monitoring_api_key
  }
  
  # Database connection details
  database_host     = module.database.rds_endpoint
  database_port     = module.database.rds_port
  database_name     = module.database.rds_db_name
  database_username = module.database.rds_username
  
  # Redis connection details
  redis_host = module.cache.redis_endpoint
  redis_port = module.cache.redis_port
  
  tags = local.common_tags
}

# Random password for Redis auth
resource "random_password" "redis_auth" {
  length  = 32
  special = false
}

module "monitoring" {
  source = "./modules/monitoring"

  name_prefix = local.name_prefix
  
  # CloudWatch configuration
  log_retention_days = 30
  
  # 21dev.ai integration
  monitoring_config = local.monitoring_config
  
  # Performance monitoring for sub-2s voice response
  performance_thresholds = {
    voice_response_time = 2000  # 2 seconds in milliseconds
    api_response_time   = 500   # 500ms for API calls
    database_query_time = 100   # 100ms for DB queries
  }
  
  tags = local.common_tags
}

module "backup_disaster_recovery" {
  source = "./modules/backup"

  name_prefix = local.name_prefix
  
  # RDS backup configuration
  rds_instance_arn = module.database.rds_instance_arn
  
  # S3 backup configuration
  s3_bucket_arn = module.frontend_hosting.s3_bucket_arn
  
  # Backup schedule for SOC 2 compliance
  backup_schedule = "cron(0 2 * * ? *)"
  
  # Cross-region backup for disaster recovery
  enable_cross_region_backup = true
  disaster_recovery_region   = "us-west-2"
  
  tags = local.common_tags
  
  providers = {
    aws.disaster_recovery = aws.disaster_recovery
  }
}

# Provider for disaster recovery region
provider "aws" {
  alias  = "disaster_recovery"
  region = "us-west-2"

  default_tags {
    tags = local.common_tags
  }
}