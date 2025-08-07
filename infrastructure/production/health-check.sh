#!/bin/bash
# Seiketsu AI - Production Health Check Script
# Comprehensive health monitoring for production infrastructure

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-prod}"
REGION="us-east-1"
PROJECT="seiketsu-ai"

# Health check results
PASSED=0
FAILED=0
WARNINGS=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

check_aws_connectivity() {
    log_info "Checking AWS connectivity..."
    
    if aws sts get-caller-identity >/dev/null 2>&1; then
        log_success "AWS connectivity verified"
    else
        log_error "AWS connectivity failed"
    fi
}

check_vpc_infrastructure() {
    log_info "Checking VPC infrastructure..."
    
    # Check VPC exists
    VPC_ID=$(aws ec2 describe-vpcs \
        --filters "Name=tag:Name,Values=${PROJECT}-${ENVIRONMENT}-vpc" \
        --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "None")
    
    if [[ "$VPC_ID" != "None" ]]; then
        log_success "VPC found: $VPC_ID"
        
        # Check subnets
        SUBNET_COUNT=$(aws ec2 describe-subnets \
            --filters "Name=vpc-id,Values=$VPC_ID" \
            --query 'length(Subnets)' --output text)
        
        if [[ $SUBNET_COUNT -ge 6 ]]; then
            log_success "Subnets configured: $SUBNET_COUNT"
        else
            log_warning "Insufficient subnets: $SUBNET_COUNT (expected ≥6)"
        fi
    else
        log_error "VPC not found"
    fi
}

check_ecs_cluster() {
    log_info "Checking ECS cluster..."
    
    CLUSTER_NAME="${PROJECT}-${ENVIRONMENT}-cluster"
    CLUSTER_STATUS=$(aws ecs describe-clusters \
        --clusters "$CLUSTER_NAME" \
        --query 'clusters[0].status' --output text 2>/dev/null || echo "MISSING")
    
    if [[ "$CLUSTER_STATUS" == "ACTIVE" ]]; then
        log_success "ECS cluster is active: $CLUSTER_NAME"
        
        # Check services
        SERVICE_COUNT=$(aws ecs list-services \
            --cluster "$CLUSTER_NAME" \
            --query 'length(serviceArns)' --output text)
        
        if [[ $SERVICE_COUNT -gt 0 ]]; then
            log_success "ECS services running: $SERVICE_COUNT"
            
            # Check service health
            aws ecs describe-services \
                --cluster "$CLUSTER_NAME" \
                --services $(aws ecs list-services --cluster "$CLUSTER_NAME" --query 'serviceArns' --output text) \
                --query 'services[].[serviceName,runningCount,desiredCount,deploymentStatus]' \
                --output table
        else
            log_warning "No ECS services found"
        fi
    else
        log_error "ECS cluster not active: $CLUSTER_STATUS"
    fi
}

check_database() {
    log_info "Checking RDS database..."
    
    DB_IDENTIFIER="${PROJECT}-${ENVIRONMENT}-db"
    DB_STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier "$DB_IDENTIFIER" \
        --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo "MISSING")
    
    if [[ "$DB_STATUS" == "available" ]]; then
        log_success "RDS database is available: $DB_IDENTIFIER"
        
        # Check backup retention
        BACKUP_RETENTION=$(aws rds describe-db-instances \
            --db-instance-identifier "$DB_IDENTIFIER" \
            --query 'DBInstances[0].BackupRetentionPeriod' --output text)
        
        if [[ $BACKUP_RETENTION -ge 7 ]]; then
            log_success "Backup retention configured: $BACKUP_RETENTION days"
        else
            log_warning "Backup retention too low: $BACKUP_RETENTION days"
        fi
    else
        log_error "RDS database not available: $DB_STATUS"
    fi
}

check_cache() {
    log_info "Checking ElastiCache Redis..."
    
    CACHE_ID="${PROJECT}-${ENVIRONMENT}-redis"
    CACHE_STATUS=$(aws elasticache describe-replication-groups \
        --replication-group-id "$CACHE_ID" \
        --query 'ReplicationGroups[0].Status' --output text 2>/dev/null || echo "MISSING")
    
    if [[ "$CACHE_STATUS" == "available" ]]; then
        log_success "ElastiCache Redis is available: $CACHE_ID"
        
        # Check cluster nodes
        NODE_COUNT=$(aws elasticache describe-replication-groups \
            --replication-group-id "$CACHE_ID" \
            --query 'ReplicationGroups[0].NumCacheClusters' --output text)
        
        if [[ $NODE_COUNT -ge 2 ]]; then
            log_success "Redis cluster nodes: $NODE_COUNT"
        else
            log_warning "Redis cluster has only $NODE_COUNT node(s)"
        fi
    else
        log_error "ElastiCache Redis not available: $CACHE_STATUS"
    fi
}

check_load_balancer() {
    log_info "Checking Application Load Balancer..."
    
    ALB_NAME="${PROJECT}-${ENVIRONMENT}-alb"
    ALB_STATE=$(aws elbv2 describe-load-balancers \
        --names "$ALB_NAME" \
        --query 'LoadBalancers[0].State.Code' --output text 2>/dev/null || echo "MISSING")
    
    if [[ "$ALB_STATE" == "active" ]]; then
        log_success "ALB is active: $ALB_NAME"
        
        # Check target groups
        ALB_ARN=$(aws elbv2 describe-load-balancers \
            --names "$ALB_NAME" \
            --query 'LoadBalancers[0].LoadBalancerArn' --output text)
        
        TARGET_GROUPS=$(aws elbv2 describe-target-groups \
            --load-balancer-arn "$ALB_ARN" \
            --query 'TargetGroups[].TargetGroupName' --output text)
        
        for TG in $TARGET_GROUPS; do
            HEALTHY_COUNT=$(aws elbv2 describe-target-health \
                --target-group-arn $(aws elbv2 describe-target-groups --names "$TG" --query 'TargetGroups[0].TargetGroupArn' --output text) \
                --query 'length(TargetHealthDescriptions[?TargetHealth.State==`healthy`])' --output text)
            
            if [[ $HEALTHY_COUNT -gt 0 ]]; then
                log_success "Target group $TG has $HEALTHY_COUNT healthy targets"
            else
                log_warning "Target group $TG has no healthy targets"
            fi
        done
    else
        log_error "ALB not active: $ALB_STATE"
    fi
}

check_cloudfront() {
    log_info "Checking CloudFront distribution..."
    
    DOMAIN="app.seiketsu.ai"
    DIST_STATUS=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?contains(Aliases.Items, '$DOMAIN')].Status" \
        --output text 2>/dev/null || echo "MISSING")
    
    if [[ "$DIST_STATUS" == "Deployed" ]]; then
        log_success "CloudFront distribution is deployed for $DOMAIN"
    else
        log_error "CloudFront distribution not deployed: $DIST_STATUS"
    fi
}

check_secrets() {
    log_info "Checking AWS Secrets Manager..."
    
    SECRETS=(
        "${PROJECT}-${ENVIRONMENT}/database/connection-string"
        "${PROJECT}-${ENVIRONMENT}/redis/connection-string"
        "${PROJECT}-${ENVIRONMENT}/api-keys/elevenlabs"
        "${PROJECT}-${ENVIRONMENT}/api-keys/openai"
    )
    
    for SECRET in "${SECRETS[@]}"; do
        if aws secretsmanager describe-secret --secret-id "$SECRET" >/dev/null 2>&1; then
            log_success "Secret exists: $SECRET"
        else
            log_error "Secret missing: $SECRET"
        fi
    done
}

check_monitoring() {
    log_info "Checking CloudWatch monitoring..."
    
    # Check log groups
    LOG_GROUPS=(
        "/ecs/${PROJECT}-${ENVIRONMENT}/api"
        "/aws/vpc/flowlogs/${PROJECT}-${ENVIRONMENT}"
    )
    
    for LOG_GROUP in "${LOG_GROUPS[@]}"; do
        if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --query 'logGroups[0]' >/dev/null 2>&1; then
            log_success "Log group exists: $LOG_GROUP"
        else
            log_warning "Log group missing: $LOG_GROUP"
        fi
    done
    
    # Check CloudWatch dashboards
    DASHBOARD_COUNT=$(aws cloudwatch list-dashboards \
        --query "length(DashboardEntries[?contains(DashboardName, '${PROJECT}')])"
        --output text)
    
    if [[ $DASHBOARD_COUNT -gt 0 ]]; then
        log_success "CloudWatch dashboards configured: $DASHBOARD_COUNT"
    else
        log_warning "No CloudWatch dashboards found"
    fi
}

check_backups() {
    log_info "Checking backup configuration..."
    
    BACKUP_VAULT="${PROJECT}-${ENVIRONMENT}-backup-vault"
    if aws backup describe-backup-vault --backup-vault-name "$BACKUP_VAULT" >/dev/null 2>&1; then
        log_success "Backup vault exists: $BACKUP_VAULT"
        
        # Check backup plans
        PLAN_COUNT=$(aws backup list-backup-plans \
            --query "length(BackupPlansList[?contains(BackupPlanName, '${PROJECT}')])" \
            --output text)
        
        if [[ $PLAN_COUNT -gt 0 ]]; then
            log_success "Backup plans configured: $PLAN_COUNT"
        else
            log_warning "No backup plans found"
        fi
    else
        log_error "Backup vault missing: $BACKUP_VAULT"
    fi
}

check_api_endpoints() {
    log_info "Checking API endpoint health..."
    
    API_ENDPOINT="https://api.seiketsu.ai/health"
    
    if curl -sf "$API_ENDPOINT" >/dev/null 2>&1; then
        log_success "API health endpoint responding: $API_ENDPOINT"
    else
        log_warning "API health endpoint not responding: $API_ENDPOINT"
    fi
}

check_ssl_certificates() {
    log_info "Checking SSL certificates..."
    
    DOMAINS=("app.seiketsu.ai" "api.seiketsu.ai")
    
    for DOMAIN in "${DOMAINS[@]}"; do
        CERT_STATUS=$(aws acm list-certificates \
            --query "CertificateSummaryList[?DomainName=='$DOMAIN'].Status" \
            --output text 2>/dev/null || echo "MISSING")
        
        if [[ "$CERT_STATUS" == "ISSUED" ]]; then
            log_success "SSL certificate issued for $DOMAIN"
        else
            log_warning "SSL certificate not issued for $DOMAIN: $CERT_STATUS"
        fi
    done
}

generate_report() {
    echo -e "\n${BLUE}=== SEIKETSU AI HEALTH CHECK REPORT ===${NC}"
    echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
    echo -e "Region: ${YELLOW}$REGION${NC}"
    echo -e "Timestamp: ${YELLOW}$(date)${NC}\n"
    
    echo -e "${GREEN}✅ Passed: $PASSED${NC}"
    echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
    echo -e "${RED}❌ Failed: $FAILED${NC}\n"
    
    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}🎉 Infrastructure is healthy and ready for production!${NC}"
        exit 0
    elif [[ $FAILED -le 2 ]]; then
        echo -e "${YELLOW}⚠️  Infrastructure has minor issues but may be usable${NC}"
        exit 1
    else
        echo -e "${RED}🚨 Infrastructure has critical issues requiring attention${NC}"
        exit 2
    fi
}

# Main execution
main() {
    echo -e "${GREEN}Seiketsu AI Production Health Check${NC}\n"
    
    check_aws_connectivity
    check_vpc_infrastructure
    check_ecs_cluster
    check_database
    check_cache
    check_load_balancer
    check_cloudfront
    check_secrets
    check_monitoring
    check_backups
    check_ssl_certificates
    check_api_endpoints
    
    generate_report
}

main "$@"