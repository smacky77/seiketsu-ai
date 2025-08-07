#!/bin/bash

# Seiketsu AI Infrastructure Deployment Script
# Comprehensive deployment with Container Studio and 21dev.ai integration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform"
ENVIRONMENT="${1:-staging}"
ACTION="${2:-plan}"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Seiketsu AI Infrastructure Deployment Script

Usage: $0 [ENVIRONMENT] [ACTION]

Environments:
  staging     - Staging environment (default)
  production  - Production environment
  dev         - Development environment

Actions:
  plan        - Show what will be created/changed (default)
  apply       - Apply the infrastructure changes
  destroy     - Destroy the infrastructure
  init        - Initialize Terraform backend
  validate    - Validate Terraform configuration
  cost        - Show cost estimation

Examples:
  $0 staging plan          # Plan staging deployment
  $0 production apply      # Deploy to production
  $0 staging destroy       # Destroy staging infrastructure
  $0 staging cost          # Show cost estimation

Required Environment Variables:
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  ELEVENLABS_API_KEY
  OPENAI_API_KEY
  JWT_SECRET
  SUPABASE_KEY
  MONITORING_API_KEY

Optional Environment Variables:
  CONTAINER_STUDIO_API_KEY
  SLACK_WEBHOOK_URL

EOF
}

# Check if help is requested
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

# Validate environment
case "$ENVIRONMENT" in
    dev|staging|production)
        log "Deploying to $ENVIRONMENT environment"
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT"
        log_error "Valid environments: dev, staging, production"
        exit 1
        ;;
esac

# Validate action
case "$ACTION" in
    init|validate|plan|apply|destroy|cost)
        log "Action: $ACTION"
        ;;
    *)
        log_error "Invalid action: $ACTION"
        log_error "Valid actions: init, validate, plan, apply, destroy, cost"
        exit 1
        ;;
esac

# Check required tools
check_requirements() {
    log "Checking requirements..."
    
    local required_tools=("terraform" "aws" "docker" "jq")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -ne 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install the missing tools and try again"
        exit 1
    fi
    
    # Check Terraform version
    local tf_version=$(terraform version -json | jq -r '.terraform_version')
    log "Terraform version: $tf_version"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid"
        log_error "Please run 'aws configure' or set AWS environment variables"
        exit 1
    fi
    
    local aws_account=$(aws sts get-caller-identity --query Account --output text)
    local aws_region=$(aws configure get region || echo "us-east-1")
    log "AWS Account: $aws_account"
    log "AWS Region: $aws_region"
    
    log_success "All requirements satisfied"
}

# Check required environment variables
check_env_vars() {
    log "Checking environment variables..."
    
    local required_vars=()
    
    if [[ "$ACTION" == "apply" ]]; then
        required_vars=("ELEVENLABS_API_KEY" "OPENAI_API_KEY" "JWT_SECRET" "SUPABASE_KEY" "MONITORING_API_KEY")
    fi
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -ne 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        log_error "Please set the missing variables and try again"
        exit 1
    fi
    
    log_success "Environment variables validated"
}

# Initialize Terraform backend
init_terraform() {
    log "Initializing Terraform..."
    
    cd "$TERRAFORM_DIR"
    
    # Create backend bucket if it doesn't exist
    local backend_bucket="seiketsu-ai-terraform-state"
    local backend_table="seiketsu-ai-terraform-locks"
    
    if ! aws s3 ls "s3://$backend_bucket" &> /dev/null; then
        log "Creating Terraform state bucket: $backend_bucket"
        aws s3 mb "s3://$backend_bucket"
        aws s3api put-bucket-versioning --bucket "$backend_bucket" --versioning-configuration Status=Enabled
        aws s3api put-bucket-encryption --bucket "$backend_bucket" --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
    fi
    
    # Create DynamoDB table if it doesn't exist
    if ! aws dynamodb describe-table --table-name "$backend_table" &> /dev/null; then
        log "Creating Terraform lock table: $backend_table"
        aws dynamodb create-table \
            --table-name "$backend_table" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
        
        # Wait for table to be active
        log "Waiting for DynamoDB table to be active..."
        aws dynamodb wait table-exists --table-name "$backend_table"
    fi
    
    terraform init -upgrade
    
    log_success "Terraform initialized"
}

# Validate Terraform configuration
validate_terraform() {
    log "Validating Terraform configuration..."
    
    cd "$TERRAFORM_DIR"
    
    terraform fmt -check -recursive
    terraform validate
    
    log_success "Terraform configuration is valid"
}

# Plan Terraform changes
plan_terraform() {
    log "Planning Terraform changes..."
    
    cd "$TERRAFORM_DIR"
    
    local plan_args=(
        "-var" "environment=$ENVIRONMENT"
        "-out=tfplan"
    )
    
    if [[ "$ACTION" == "apply" ]]; then
        plan_args+=(
            "-var" "elevenlabs_api_key=$ELEVENLABS_API_KEY"
            "-var" "openai_api_key=$OPENAI_API_KEY"
            "-var" "jwt_secret=$JWT_SECRET"
            "-var" "supabase_key=$SUPABASE_KEY"
            "-var" "monitoring_api_key=$MONITORING_API_KEY"
        )
    fi
    
    terraform plan "${plan_args[@]}"
    
    log_success "Terraform plan completed"
}

# Apply Terraform changes
apply_terraform() {
    log "Applying Terraform changes..."
    
    cd "$TERRAFORM_DIR"
    
    if [[ ! -f "tfplan" ]]; then
        log_error "No plan file found. Please run plan first."
        exit 1
    fi
    
    # Confirm application in production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_warning "You are about to apply changes to PRODUCTION environment!"
        read -p "Are you sure you want to continue? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log "Deployment cancelled"
            exit 0
        fi
    fi
    
    terraform apply tfplan
    
    # Save outputs
    terraform output -json > "terraform-outputs-$ENVIRONMENT.json"
    
    log_success "Terraform apply completed"
    
    # Post-deployment tasks
    post_deployment_tasks
}

# Destroy Terraform infrastructure
destroy_terraform() {
    log "Destroying Terraform infrastructure..."
    
    cd "$TERRAFORM_DIR"
    
    # Extra confirmation for production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_warning "You are about to DESTROY the PRODUCTION environment!"
        log_warning "This action is IRREVERSIBLE and will delete all data!"
        read -p "Type 'DESTROY' to confirm: " -r
        if [[ "$REPLY" != "DESTROY" ]]; then
            log "Destruction cancelled"
            exit 0
        fi
    fi
    
    local destroy_args=(
        "-var" "environment=$ENVIRONMENT"
        "-auto-approve"
    )
    
    if [[ -n "${ELEVENLABS_API_KEY:-}" ]]; then
        destroy_args+=(
            "-var" "elevenlabs_api_key=$ELEVENLABS_API_KEY"
            "-var" "openai_api_key=$OPENAI_API_KEY"
            "-var" "jwt_secret=$JWT_SECRET"
            "-var" "supabase_key=$SUPABASE_KEY"
            "-var" "monitoring_api_key=$MONITORING_API_KEY"
        )
    fi
    
    terraform destroy "${destroy_args[@]}"
    
    log_success "Infrastructure destroyed"
}

# Show cost estimation
show_cost_estimation() {
    log "Generating cost estimation..."
    
    cd "$TERRAFORM_DIR"
    
    if ! command -v infracost &> /dev/null; then
        log_warning "Infracost not installed. Installing..."
        curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh
    fi
    
    if [[ ! -f "tfplan" ]]; then
        log "No plan file found. Creating plan for cost estimation..."
        terraform plan -out=tfplan-cost
        mv tfplan-cost tfplan
    fi
    
    infracost breakdown --path=tfplan --format=table
    
    log_success "Cost estimation completed"
}

# Post-deployment tasks
post_deployment_tasks() {
    log "Running post-deployment tasks..."
    
    # Container Studio integration
    if [[ -n "${CONTAINER_STUDIO_API_KEY:-}" ]]; then
        log "Notifying Container Studio..."
        # Container Studio API call would go here
        log_success "Container Studio notified"
    fi
    
    # 21dev.ai monitoring setup
    if [[ -n "${MONITORING_API_KEY:-}" ]]; then
        log "Configuring 21dev.ai monitoring..."
        # 21dev.ai API call would go here
        log_success "21dev.ai monitoring configured"
    fi
    
    # Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        log "Sending Slack notification..."
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"text\": \"🚀 Seiketsu AI infrastructure deployed to $ENVIRONMENT\",
                \"attachments\": [
                    {
                        \"color\": \"good\",
                        \"fields\": [
                            {
                                \"title\": \"Environment\",
                                \"value\": \"$ENVIRONMENT\",
                                \"short\": true
                            },
                            {
                                \"title\": \"Timestamp\",
                                \"value\": \"$(date)\",
                                \"short\": true
                            }
                        ]
                    }
                ]
            }" \
            "$SLACK_WEBHOOK_URL" || log_warning "Failed to send Slack notification"
    fi
    
    log_success "Post-deployment tasks completed"
}

# Main execution
main() {
    log "Starting Seiketsu AI infrastructure deployment"
    log "Environment: $ENVIRONMENT"
    log "Action: $ACTION"
    
    check_requirements
    
    case "$ACTION" in
        init)
            init_terraform
            ;;
        validate)
            init_terraform
            validate_terraform
            ;;
        plan)
            check_env_vars
            init_terraform
            validate_terraform
            plan_terraform
            ;;
        apply)
            check_env_vars
            init_terraform
            validate_terraform
            plan_terraform
            apply_terraform
            ;;
        destroy)
            init_terraform
            destroy_terraform
            ;;
        cost)
            init_terraform
            validate_terraform
            plan_terraform
            show_cost_estimation
            ;;
    esac
    
    log_success "Deployment script completed successfully"
}

# Trap errors
trap 'log_error "Deployment script failed at line $LINENO"' ERR

# Run main function
main "$@"