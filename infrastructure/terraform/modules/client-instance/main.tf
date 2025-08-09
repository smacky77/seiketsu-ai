# Seiketsu AI Client Instance Terraform Module
# Complete isolated infrastructure for each client

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# Variables
variable "client_id" {
  description = "Unique client identifier"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.client_id))
    error_message = "Client ID must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "client_name" {
  description = "Client company name"
  type        = string
}

variable "client_email" {
  description = "Client contact email"
  type        = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.client_email))
    error_message = "Must be a valid email address."
  }
}

variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "instance_type" {
  description = "EC2 instance type for application"
  type        = string
  default     = "t3.micro"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "min_capacity" {
  description = "Minimum number of instances in ASG"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of instances in ASG"
  type        = number
  default     = 10
}

variable "desired_capacity" {
  description = "Desired number of instances in ASG"
  type        = number
  default     = 2
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
  upper   = true
  lower   = true
  numeric = true
}

resource "random_password" "redis_auth_token" {
  length  = 32
  special = false
  upper   = true
  lower   = true
  numeric = true
}

# VPC for complete client isolation
resource "aws_vpc" "client_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name         = "${var.client_id}-vpc"
    Environment  = var.environment
    Client       = var.client_id
    ClientName   = var.client_name
    ManagedBy    = "Terraform"
    Purpose      = "SeiketsuAI-ClientIsolation"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "client_igw" {
  vpc_id = aws_vpc.client_vpc.id
  
  tags = {
    Name = "${var.client_id}-igw"
    Client = var.client_id
  }
}

# Public Subnets (for ALB and NAT Gateways)
resource "aws_subnet" "client_public" {
  count             = 2
  vpc_id            = aws_vpc.client_vpc.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${var.client_id}-public-${count.index + 1}"
    Type = "Public"
    Client = var.client_id
  }
}

# Private Subnets (for application and database)
resource "aws_subnet" "client_private" {
  count             = 2
  vpc_id            = aws_vpc.client_vpc.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "${var.client_id}-private-${count.index + 1}"
    Type = "Private"
    Client = var.client_id
  }
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "client_nat_eip" {
  count  = 2
  domain = "vpc"
  
  depends_on = [aws_internet_gateway.client_igw]
  
  tags = {
    Name = "${var.client_id}-nat-eip-${count.index + 1}"
    Client = var.client_id
  }
}

# NAT Gateways for private subnet internet access
resource "aws_nat_gateway" "client_nat" {
  count         = 2
  allocation_id = aws_eip.client_nat_eip[count.index].id
  subnet_id     = aws_subnet.client_public[count.index].id
  
  depends_on = [aws_internet_gateway.client_igw]
  
  tags = {
    Name = "${var.client_id}-nat-${count.index + 1}"
    Client = var.client_id
  }
}

# Route Tables
resource "aws_route_table" "client_public_rt" {
  vpc_id = aws_vpc.client_vpc.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.client_igw.id
  }
  
  tags = {
    Name = "${var.client_id}-public-rt"
    Type = "Public"
    Client = var.client_id
  }
}

resource "aws_route_table" "client_private_rt" {
  count  = 2
  vpc_id = aws_vpc.client_vpc.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.client_nat[count.index].id
  }
  
  tags = {
    Name = "${var.client_id}-private-rt-${count.index + 1}"
    Type = "Private"
    Client = var.client_id
  }
}

# Route Table Associations
resource "aws_route_table_association" "client_public_rta" {
  count          = 2
  subnet_id      = aws_subnet.client_public[count.index].id
  route_table_id = aws_route_table.client_public_rt.id
}

resource "aws_route_table_association" "client_private_rta" {
  count          = 2
  subnet_id      = aws_subnet.client_private[count.index].id
  route_table_id = aws_route_table.client_private_rt[count.index].id
}

# Security Groups
resource "aws_security_group" "client_alb_sg" {
  name_prefix = "${var.client_id}-alb-sg"
  vpc_id      = aws_vpc.client_vpc.id
  description = "Security group for ${var.client_name} Application Load Balancer"
  
  # HTTPS ingress
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # HTTP ingress (redirect to HTTPS)
  ingress {
    description = "HTTP from internet (redirect to HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.client_id}-alb-sg"
    Client = var.client_id
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "client_app_sg" {
  name_prefix = "${var.client_id}-app-sg"
  vpc_id      = aws_vpc.client_vpc.id
  description = "Security group for ${var.client_name} application servers"
  
  # Application port from ALB
  ingress {
    description     = "Application port from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.client_alb_sg.id]
  }
  
  # SSH access (optional, for debugging)
  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] # Only from within VPC
  }
  
  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.client_id}-app-sg"
    Client = var.client_id
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "client_db_sg" {
  name_prefix = "${var.client_id}-db-sg"
  vpc_id      = aws_vpc.client_vpc.id
  description = "Security group for ${var.client_name} database"
  
  # PostgreSQL access from application
  ingress {
    description     = "PostgreSQL from application servers"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.client_app_sg.id]
  }
  
  tags = {
    Name = "${var.client_id}-db-sg"
    Client = var.client_id
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "client_redis_sg" {
  name_prefix = "${var.client_id}-redis-sg"
  vpc_id      = aws_vpc.client_vpc.id
  description = "Security group for ${var.client_name} Redis cache"
  
  # Redis access from application
  ingress {
    description     = "Redis from application servers"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.client_app_sg.id]
  }
  
  tags = {
    Name = "${var.client_id}-redis-sg"
    Client = var.client_id
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

# Database Subnet Group
resource "aws_db_subnet_group" "client_db_subnet" {
  name       = "${var.client_id}-db-subnet"
  subnet_ids = aws_subnet.client_private[*].id
  description = "Database subnet group for ${var.client_name}"
  
  tags = {
    Name = "${var.client_id}-db-subnet-group"
    Client = var.client_id
  }
}

# RDS Database Instance
resource "aws_db_instance" "client_db" {
  identifier = "${var.client_id}-db"
  
  # Engine configuration
  engine         = "postgres"
  engine_version = "14.10"
  instance_class = var.db_instance_class
  
  # Storage configuration
  allocated_storage     = 20
  max_allocated_storage = 1000
  storage_encrypted     = true
  storage_type          = "gp3"
  
  # Database configuration
  db_name  = replace("seiketsu_${var.client_id}", "-", "_")
  username = "seiketsu_admin"
  password = random_password.db_password.result
  port     = 5432
  
  # Network configuration
  vpc_security_group_ids = [aws_security_group.client_db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.client_db_subnet.name
  publicly_accessible    = false
  
  # Backup configuration
  backup_retention_period   = 7
  backup_window            = "03:00-04:00"
  maintenance_window       = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade = true
  
  # Security configuration
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "${var.client_id}-db-final-snapshot"
  
  # Performance Insights
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  
  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn
  
  tags = {
    Name = "${var.client_id}-database"
    Client = var.client_id
    ClientName = var.client_name
    Environment = var.environment
  }
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "client_redis_subnet" {
  name       = "${var.client_id}-redis-subnet"
  subnet_ids = aws_subnet.client_private[*].id
  description = "Redis subnet group for ${var.client_name}"
  
  tags = {
    Name = "${var.client_id}-redis-subnet-group"
    Client = var.client_id
  }
}

# ElastiCache Redis Cluster
resource "aws_elasticache_replication_group" "client_redis" {
  replication_group_id         = "${var.client_id}-redis"
  description                  = "Redis cache for ${var.client_name}"
  
  # Engine configuration
  engine               = "redis"
  engine_version       = "7.0"
  node_type           = "cache.t3.micro"
  port                = 6379
  parameter_group_name = "default.redis7"
  
  # Cluster configuration
  num_cache_clusters = 1
  
  # Network configuration
  subnet_group_name    = aws_elasticache_subnet_group.client_redis_subnet.name
  security_group_ids   = [aws_security_group.client_redis_sg.id]
  
  # Security configuration
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = random_password.redis_auth_token.result
  
  # Backup configuration
  automatic_failover_enabled = false
  snapshot_retention_limit   = 3
  snapshot_window           = "05:00-07:00"
  
  tags = {
    Name = "${var.client_id}-redis"
    Client = var.client_id
    ClientName = var.client_name
    Environment = var.environment
  }
}

# S3 Bucket for client data
resource "aws_s3_bucket" "client_bucket" {
  bucket = "seiketsu-${var.client_id}-data-${random_password.bucket_suffix.result}"
  
  tags = {
    Name = "${var.client_id}-data-bucket"
    Client = var.client_id
    ClientName = var.client_name
    Environment = var.environment
  }
}

resource "random_password" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Bucket Configuration
resource "aws_s3_bucket_versioning" "client_bucket_versioning" {
  bucket = aws_s3_bucket.client_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "client_bucket_encryption" {
  bucket = aws_s3_bucket.client_bucket.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "client_bucket_pab" {
  bucket = aws_s3_bucket.client_bucket.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "client_bucket_lifecycle" {
  bucket = aws_s3_bucket.client_bucket.id
  
  rule {
    id     = "client_data_lifecycle"
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
  }
}

# IAM Role for RDS Enhanced Monitoring
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "${var.client_id}-rds-monitoring-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name = "${var.client_id}-rds-monitoring-role"
    Client = var.client_id
  }
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Application Load Balancer
resource "aws_lb" "client_alb" {
  name               = "${var.client_id}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.client_alb_sg.id]
  subnets            = aws_subnet.client_public[*].id
  
  enable_deletion_protection = false # Set to true for production
  
  access_logs {
    bucket  = aws_s3_bucket.client_bucket.bucket
    prefix  = "alb-access-logs"
    enabled = true
  }
  
  tags = {
    Name = "${var.client_id}-alb"
    Client = var.client_id
    ClientName = var.client_name
    Environment = var.environment
  }
}

# ALB Target Group
resource "aws_lb_target_group" "client_tg" {
  name     = "${var.client_id}-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.client_vpc.id
  target_type = "instance"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }
  
  stickiness {
    enabled = false
    type    = "lb_cookie"
  }
  
  tags = {
    Name = "${var.client_id}-target-group"
    Client = var.client_id
  }
}

# SSL Certificate
resource "aws_acm_certificate" "client_cert" {
  domain_name       = "${var.client_id}.seiketsu.ai"
  validation_method = "DNS"
  
  subject_alternative_names = [
    "*.${var.client_id}.seiketsu.ai"
  ]
  
  tags = {
    Name = "${var.client_id}-ssl-cert"
    Client = var.client_id
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

# ALB Listeners
resource "aws_lb_listener" "client_https" {
  load_balancer_arn = aws_lb.client_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.client_cert.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.client_tg.arn
  }
  
  tags = {
    Name = "${var.client_id}-https-listener"
    Client = var.client_id
  }
}

resource "aws_lb_listener" "client_http_redirect" {
  load_balancer_arn = aws_lb.client_alb.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
  
  tags = {
    Name = "${var.client_id}-http-redirect"
    Client = var.client_id
  }
}

# Launch Template for Auto Scaling
resource "aws_launch_template" "client_lt" {
  name_prefix   = "${var.client_id}-lt"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  
  vpc_security_group_ids = [aws_security_group.client_app_sg.id]
  
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    client_id = var.client_id
    db_endpoint = aws_db_instance.client_db.endpoint
    db_name = aws_db_instance.client_db.db_name
    db_username = aws_db_instance.client_db.username
    redis_endpoint = aws_elasticache_replication_group.client_redis.primary_endpoint_address
    s3_bucket = aws_s3_bucket.client_bucket.bucket
  }))
  
  iam_instance_profile {
    name = aws_iam_instance_profile.client_instance_profile.name
  }
  
  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = 20
      volume_type = "gp3"
      encrypted   = true
      delete_on_termination = true
    }
  }
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.client_id}-app-instance"
      Client = var.client_id
      ClientName = var.client_name
      Environment = var.environment
    }
  }
  
  tags = {
    Name = "${var.client_id}-launch-template"
    Client = var.client_id
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "client_asg" {
  name                = "${var.client_id}-asg"
  vpc_zone_identifier = aws_subnet.client_private[*].id
  target_group_arns   = [aws_lb_target_group.client_tg.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300
  
  min_size         = var.min_capacity
  max_size         = var.max_capacity
  desired_capacity = var.desired_capacity
  
  launch_template {
    id      = aws_launch_template.client_lt.id
    version = "$Latest"
  }
  
  tag {
    key                 = "Name"
    value               = "${var.client_id}-asg"
    propagate_at_launch = false
  }
  
  tag {
    key                 = "Client"
    value               = var.client_id
    propagate_at_launch = true
  }
  
  tag {
    key                 = "ClientName"
    value               = var.client_name
    propagate_at_launch = true
  }
  
  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }
}

# Auto Scaling Policies
resource "aws_autoscaling_policy" "client_scale_up" {
  name                   = "${var.client_id}-scale-up"
  scaling_adjustment     = 2
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.client_asg.name
  policy_type           = "SimpleScaling"
}

resource "aws_autoscaling_policy" "client_scale_down" {
  name                   = "${var.client_id}-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.client_asg.name
  policy_type           = "SimpleScaling"
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "client_cpu_high" {
  alarm_name          = "${var.client_id}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "High CPU utilization for ${var.client_name}"
  alarm_actions       = [aws_autoscaling_policy.client_scale_up.arn]
  
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.client_asg.name
  }
  
  tags = {
    Name = "${var.client_id}-cpu-high-alarm"
    Client = var.client_id
  }
}

resource "aws_cloudwatch_metric_alarm" "client_cpu_low" {
  alarm_name          = "${var.client_id}-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "30"
  alarm_description   = "Low CPU utilization for ${var.client_name}"
  alarm_actions       = [aws_autoscaling_policy.client_scale_down.arn]
  
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.client_asg.name
  }
  
  tags = {
    Name = "${var.client_id}-cpu-low-alarm"
    Client = var.client_id
  }
}

# IAM Role for EC2 instances
resource "aws_iam_role" "client_instance_role" {
  name = "${var.client_id}-instance-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name = "${var.client_id}-instance-role"
    Client = var.client_id
  }
}

resource "aws_iam_role_policy" "client_instance_policy" {
  name = "${var.client_id}-instance-policy"
  role = aws_iam_role.client_instance_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.client_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.client_bucket.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "${aws_cloudwatch_log_group.client_logs.arn}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "client_instance_profile" {
  name = "${var.client_id}-instance-profile"
  role = aws_iam_role.client_instance_role.name
  
  tags = {
    Name = "${var.client_id}-instance-profile"
    Client = var.client_id
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "client_logs" {
  name              = "/aws/seiketsu/${var.client_id}"
  retention_in_days = 30
  
  tags = {
    Name = "${var.client_id}-logs"
    Client = var.client_id
    ClientName = var.client_name
    Environment = var.environment
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "client_dashboard" {
  dashboard_name = "${var.client_id}-dashboard"
  
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
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.client_alb.arn_suffix],
            [".", "TargetResponseTime", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.region
          title   = "ALB Metrics"
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
            ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", aws_autoscaling_group.client_asg.name],
            [".", "NetworkIn", ".", "."],
            [".", "NetworkOut", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.region
          title   = "EC2 Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.client_db.id],
            [".", "DatabaseConnections", ".", "."],
            [".", "ReadLatency", ".", "."],
            [".", "WriteLatency", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.region
          title   = "RDS Metrics"
          period  = 300
        }
      }
    ]
  })
  
  tags = {
    Name = "${var.client_id}-dashboard"
    Client = var.client_id
  }
}

# Outputs
output "client_vpc_id" {
  description = "VPC ID for client infrastructure"
  value       = aws_vpc.client_vpc.id
}

output "client_db_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.client_db.endpoint
}

output "client_db_password" {
  description = "RDS database password"
  value       = random_password.db_password.result
  sensitive   = true
}

output "client_redis_endpoint" {
  description = "Redis cache endpoint"
  value       = aws_elasticache_replication_group.client_redis.primary_endpoint_address
}

output "client_redis_auth_token" {
  description = "Redis authentication token"
  value       = random_password.redis_auth_token.result
  sensitive   = true
}

output "client_bucket_name" {
  description = "S3 bucket name for client data"
  value       = aws_s3_bucket.client_bucket.bucket
}

output "client_alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.client_alb.dns_name
}

output "client_alb_zone_id" {
  description = "Application Load Balancer hosted zone ID"
  value       = aws_lb.client_alb.zone_id
}

output "client_certificate_arn" {
  description = "SSL certificate ARN"
  value       = aws_acm_certificate.client_cert.arn
}

output "client_certificate_domain_validation_options" {
  description = "Certificate domain validation options"
  value       = aws_acm_certificate.client_cert.domain_validation_options
}

output "client_cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.client_logs.name
}

output "client_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${var.region}.console.aws.amazon.com/cloudwatch/home?region=${var.region}#dashboards:name=${aws_cloudwatch_dashboard.client_dashboard.dashboard_name}"
}

output "client_infrastructure_summary" {
  description = "Complete infrastructure summary"
  value = {
    client_id     = var.client_id
    client_name   = var.client_name
    vpc_id        = aws_vpc.client_vpc.id
    database      = {
      endpoint = aws_db_instance.client_db.endpoint
      name     = aws_db_instance.client_db.db_name
    }
    cache         = {
      endpoint = aws_elasticache_replication_group.client_redis.primary_endpoint_address
    }
    storage       = {
      bucket = aws_s3_bucket.client_bucket.bucket
    }
    load_balancer = {
      dns_name = aws_lb.client_alb.dns_name
      url      = "https://${var.client_id}.seiketsu.ai"
    }
    monitoring    = {
      log_group = aws_cloudwatch_log_group.client_logs.name
      dashboard = aws_cloudwatch_dashboard.client_dashboard.dashboard_name
    }
  }
}