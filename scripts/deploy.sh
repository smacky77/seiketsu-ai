#!/bin/bash

# Seiketsu AI - Deployment Script
# Comprehensive deployment automation with rollback capabilities

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="staging"
DEPLOYMENT_TYPE="blue-green"
SKIP_TESTS="false"
DRY_RUN="false"
FORCE_DEPLOY="false"
ROLLBACK_ON_FAILURE="true"
HEALTH_CHECK_TIMEOUT="300"
SLACK_WEBHOOK_URL=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Seiketsu AI Deployment Script

OPTIONS:
    -e, --environment ENV       Target environment (staging, production) [default: staging]
    -t, --type TYPE            Deployment type (blue-green, canary, rolling) [default: blue-green]
    -s, --skip-tests           Skip running tests before deployment
    -d, --dry-run              Show what would be deployed without making changes
    -f, --force                Force deployment even if validation fails
    --no-rollback              Disable automatic rollback on failure
    --timeout SECONDS          Health check timeout in seconds [default: 300]
    --slack-webhook URL        Slack webhook URL for notifications
    -h, --help                 Show this help message

EXAMPLES:
    # Deploy to staging with blue-green deployment
    $0 --environment staging --type blue-green

    # Deploy to production with canary deployment
    $0 --environment production --type canary

    # Dry run for production deployment
    $0 --environment production --dry-run

    # Force deploy with custom timeout
    $0 --environment production --force --timeout 600
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -s|--skip-tests)
            SKIP_TESTS="true"
            shift
            ;;
        -d|--dry-run)
            DRY_RUN="true"
            shift
            ;;
        -f|--force)
            FORCE_DEPLOY="true"
            shift
            ;;
        --no-rollback)
            ROLLBACK_ON_FAILURE="false"
            shift
            ;;
        --timeout)
            HEALTH_CHECK_TIMEOUT="$2"
            shift 2
            ;;
        --slack-webhook)
            SLACK_WEBHOOK_URL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
    exit 1
fi

# Validate deployment type
if [[ ! "$DEPLOYMENT_TYPE" =~ ^(blue-green|canary|rolling)$ ]]; then
    print_error "Invalid deployment type: $DEPLOYMENT_TYPE. Must be 'blue-green', 'canary', or 'rolling'"
    exit 1
fi

# Set deployment variables
DEPLOYMENT_ID=$(date +%Y%m%d-%H%M%S)-$(git rev-parse --short HEAD)
DEPLOYMENT_START_TIME=$(date +%s)
AWS_REGION=${AWS_REGION:-us-east-1}
PROJECT_NAME="seiketsu-ai"

print_status "Starting $PROJECT_NAME deployment"
print_status "Environment: $ENVIRONMENT"
print_status "Deployment Type: $DEPLOYMENT_TYPE"
print_status "Deployment ID: $DEPLOYMENT_ID"

# Function to send Slack notification
send_slack_notification() {
    local message="$1"
    local color="$2"
    
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\",\"color\":\"$color\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("aws" "terraform" "docker" "git" "jq" "curl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            print_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check Git status
    if [[ $(git status --porcelain) ]]; then
        if [[ "$FORCE_DEPLOY" != "true" ]]; then
            print_error "Git working directory is not clean. Use --force to override."
            exit 1
        else
            print_warning "Git working directory is not clean, but force deploy enabled"
        fi
    fi
    
    print_success "Prerequisites check passed"
}

# Function to run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        print_warning "Skipping tests as requested"
        return 0
    fi
    
    print_status "Running tests..."
    
    # Frontend tests
    if [[ -f "apps/web/package.json" ]]; then
        print_status "Running frontend tests..."
        cd apps/web
        npm ci
        npm run test:ci
        npm run type-check
        cd ../..
    fi
    
    # Backend tests
    if [[ -f "apps/api/requirements.txt" ]]; then
        print_status "Running backend tests..."
        cd apps/api
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        python -m pytest --cov=. --cov-report=xml
        deactivate
        cd ../..
    fi
    
    # Infrastructure tests
    if [[ -d "infrastructure/terraform" ]]; then
        print_status "Validating Terraform configuration..."
        cd infrastructure/terraform
        terraform init -backend=false
        terraform validate
        terraform fmt -check -recursive .
        cd ../..
    fi
    
    print_success "All tests passed"
}

# Function to build and push container images
build_and_push_images() {
    print_status "Building and pushing container images..."
    
    local ecr_registry="$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com"
    local image_tag="${DEPLOYMENT_ID}"
    
    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ecr_registry"
    
    # Build and push API image
    if [[ -f "apps/api/Dockerfile" ]]; then
        print_status "Building API image..."
        docker build -t "$ecr_registry/$PROJECT_NAME-api:$image_tag" apps/api/
        
        if [[ "$DRY_RUN" != "true" ]]; then
            docker push "$ecr_registry/$PROJECT_NAME-api:$image_tag"
            # Also tag as environment-latest
            docker tag "$ecr_registry/$PROJECT_NAME-api:$image_tag" "$ecr_registry/$PROJECT_NAME-api:$ENVIRONMENT-latest"
            docker push "$ecr_registry/$PROJECT_NAME-api:$ENVIRONMENT-latest"
        else
            print_status "DRY RUN: Would push $ecr_registry/$PROJECT_NAME-api:$image_tag"
        fi
    fi
    
    print_success "Container images built and pushed"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure..."
    
    cd infrastructure/terraform
    
    # Initialize Terraform
    terraform init
    
    # Select or create workspace
    terraform workspace select "$ENVIRONMENT" || terraform workspace new "$ENVIRONMENT"
    
    # Plan infrastructure changes
    local tf_var_file="environments/$ENVIRONMENT/terraform.tfvars"
    if [[ ! -f "$tf_var_file" ]]; then
        print_error "Terraform variables file not found: $tf_var_file"
        exit 1
    fi
    
    terraform plan -var-file="$tf_var_file" -out=tfplan -input=false
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Infrastructure plan created, skipping apply"
        cd ../..
        return 0
    fi
    
    # Apply infrastructure changes
    terraform apply -auto-approve tfplan
    
    # Get outputs
    terraform output -json > terraform-outputs.json
    
    cd ../..
    print_success "Infrastructure deployed successfully"
}

# Function to deploy application
deploy_application() {
    print_status "Deploying application using $DEPLOYMENT_TYPE deployment..."
    
    case "$DEPLOYMENT_TYPE" in
        "blue-green")
            deploy_blue_green
            ;;
        "canary")
            deploy_canary
            ;;
        "rolling")
            deploy_rolling
            ;;
    esac
}

# Function to deploy using blue-green strategy
deploy_blue_green() {
    print_status "Starting blue-green deployment..."
    
    # Get current environment state
    local current_env=$(aws elbv2 describe-listeners --listener-arns $(terraform output -raw primary_listener_arn) --query 'Listeners[0].DefaultActions[0].ForwardConfig.TargetGroups[0].TargetGroupArn' --output text)
    
    if [[ "$current_env" == *"blue"* ]]; then
        local target_env="green"
    else
        local target_env="blue"
    fi
    
    print_status "Current environment: $(echo $current_env | grep -o 'blue\|green')"
    print_status "Target environment: $target_env"
    
    # Update target environment with new image
    update_ecs_service "$target_env"
    
    # Wait for deployment to be healthy
    wait_for_healthy_deployment "$target_env"
    
    # Run smoke tests on target environment
    run_smoke_tests "$target_env"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        # Switch traffic to target environment
        switch_traffic "$target_env"
        
        # Final health check
        wait_for_healthy_deployment "$target_env"
    else
        print_status "DRY RUN: Would switch traffic to $target_env environment"
    fi
    
    print_success "Blue-green deployment completed successfully"
}

# Function to deploy using canary strategy
deploy_canary() {
    print_status "Starting canary deployment..."
    
    local canary_weight=${CANARY_WEIGHT:-10}
    local canary_duration=${CANARY_DURATION:-10}
    
    # Update canary environment
    update_ecs_service "canary"
    
    # Wait for canary to be healthy
    wait_for_healthy_deployment "canary"
    
    # Start canary traffic split
    if [[ "$DRY_RUN" != "true" ]]; then
        aws stepfunctions start-execution \
            --state-machine-arn $(terraform output -raw canary_step_function_arn) \
            --input "{\"canaryWeight\": $canary_weight, \"duration\": $canary_duration}" \
            --name "canary-$DEPLOYMENT_ID"
        
        print_status "Canary deployment started with $canary_weight% traffic for $canary_duration minutes"
        
        # Monitor canary metrics
        monitor_canary_deployment "$DEPLOYMENT_ID"
    else
        print_status "DRY RUN: Would start canary deployment with $canary_weight% traffic"
    fi
    
    print_success "Canary deployment completed successfully"
}

# Function to deploy using rolling strategy
deploy_rolling() {
    print_status "Starting rolling deployment..."
    
    # Update ECS service with rolling deployment
    update_ecs_service "main"
    
    # Wait for deployment to complete
    wait_for_healthy_deployment "main"
    
    print_success "Rolling deployment completed successfully"
}

# Function to update ECS service
update_ecs_service() {
    local environment_suffix="$1"
    local cluster_name="$PROJECT_NAME-$ENVIRONMENT-cluster"
    local service_name="$PROJECT_NAME-$ENVIRONMENT-$environment_suffix-service"
    
    print_status "Updating ECS service: $service_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Would update ECS service $service_name"
        return 0
    fi
    
    # Get current task definition
    local task_def_arn=$(aws ecs describe-services \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --query 'services[0].taskDefinition' --output text)
    
    # Update task definition with new image
    local new_task_def=$(aws ecs describe-task-definition --task-definition "$task_def_arn" --query taskDefinition)
    local ecr_registry="$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com"
    local new_image="$ecr_registry/$PROJECT_NAME-api:$DEPLOYMENT_ID"
    
    # Register new task definition
    local new_task_def_arn=$(echo "$new_task_def" | \
        jq --arg IMAGE "$new_image" '.containerDefinitions[0].image = $IMAGE | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy)' | \
        aws ecs register-task-definition --cli-input-json file:///dev/stdin --query taskDefinition.taskDefinitionArn --output text)
    
    # Update ECS service
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "$service_name" \
        --task-definition "$new_task_def_arn" \
        > /dev/null
    
    print_status "ECS service update initiated"
}

# Function to wait for healthy deployment
wait_for_healthy_deployment() {
    local environment_suffix="$1"
    local cluster_name="$PROJECT_NAME-$ENVIRONMENT-cluster"
    local service_name="$PROJECT_NAME-$ENVIRONMENT-$environment_suffix-service"
    
    print_status "Waiting for healthy deployment of $service_name..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Would wait for healthy deployment"
        return 0
    fi
    
    local timeout=$HEALTH_CHECK_TIMEOUT
    local elapsed=0
    local check_interval=30
    
    while [ $elapsed -lt $timeout ]; do
        local service_status=$(aws ecs describe-services \
            --cluster "$cluster_name" \
            --services "$service_name" \
            --query 'services[0].deployments[0].status' --output text)
        
        local running_count=$(aws ecs describe-services \
            --cluster "$cluster_name" \
            --services "$service_name" \
            --query 'services[0].runningCount' --output text)
        
        local desired_count=$(aws ecs describe-services \
            --cluster "$cluster_name" \
            --services "$service_name" \
            --query 'services[0].desiredCount' --output text)
        
        if [[ "$service_status" == "PRIMARY" && "$running_count" -eq "$desired_count" ]]; then
            print_success "Service is healthy (${running_count}/${desired_count} tasks running)"
            return 0
        fi
        
        print_status "Service status: $service_status, Tasks: ${running_count}/${desired_count}, elapsed: ${elapsed}s"
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    print_error "Deployment health check timed out after ${timeout}s"
    return 1
}

# Function to run smoke tests
run_smoke_tests() {
    local environment_suffix="$1"
    
    print_status "Running smoke tests for $environment_suffix environment..."
    
    # Get ALB DNS name
    local alb_dns=$(terraform output -raw alb_dns_name)
    local test_port="443"
    
    if [[ "$environment_suffix" == "green" || "$environment_suffix" == "canary" ]]; then
        test_port="8443"  # Test listener port
    fi
    
    # Basic health check
    local health_url="https://$alb_dns:$test_port/health"
    
    print_status "Testing health endpoint: $health_url"
    
    local max_retries=10
    local retry_delay=10
    
    for ((i=1; i<=max_retries; i++)); do
        if curl -f -s -m 10 "$health_url" > /dev/null; then
            print_success "Health check passed"
            break
        elif [[ $i -eq $max_retries ]]; then
            print_error "Health check failed after $max_retries retries"
            return 1
        else
            print_status "Health check failed, retry $i/$max_retries in ${retry_delay}s..."
            sleep $retry_delay
        fi
    done
    
    # Additional API tests
    local api_tests=(
        "/api/v1/status"
        "/api/v1/voice/status"
    )
    
    for endpoint in "${api_tests[@]}"; do
        local test_url="https://$alb_dns:$test_port$endpoint"
        print_status "Testing endpoint: $test_url"
        
        if curl -f -s -m 10 "$test_url" > /dev/null; then
            print_success "Endpoint test passed: $endpoint"
        else
            print_warning "Endpoint test failed: $endpoint (non-critical)"
        fi
    done
    
    print_success "Smoke tests completed"
}

# Function to switch traffic in blue-green deployment
switch_traffic() {
    local target_env="$1"
    
    print_status "Switching traffic to $target_env environment..."
    
    # Execute traffic switch using Step Function
    aws stepfunctions start-execution \
        --state-machine-arn $(terraform output -raw blue_green_step_function_arn) \
        --input "{\"action\": \"switch\", \"target\": \"$target_env\"}" \
        --name "traffic-switch-$DEPLOYMENT_ID" \
        > /dev/null
    
    print_success "Traffic switched to $target_env environment"
}

# Function to monitor canary deployment
monitor_canary_deployment() {
    local deployment_id="$1"
    
    print_status "Monitoring canary deployment..."
    
    # Wait for Step Function execution to complete
    local execution_arn="arn:aws:states:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):execution:$PROJECT_NAME-$ENVIRONMENT-canary-deployment:canary-$deployment_id"
    
    while true; do
        local status=$(aws stepfunctions describe-execution --execution-arn "$execution_arn" --query 'status' --output text)
        
        case "$status" in
            "SUCCEEDED")
                print_success "Canary deployment succeeded"
                break
                ;;
            "FAILED"|"TIMED_OUT"|"ABORTED")
                print_error "Canary deployment failed with status: $status"
                return 1
                ;;
            "RUNNING")
                print_status "Canary deployment in progress..."
                sleep 30
                ;;
        esac
    done
}

# Function to rollback deployment
rollback_deployment() {
    print_error "Rolling back deployment..."
    
    send_slack_notification "🔄 Rolling back Seiketsu AI deployment in $ENVIRONMENT" "warning"
    
    case "$DEPLOYMENT_TYPE" in
        "blue-green")
            # Switch back to previous environment
            aws stepfunctions start-execution \
                --state-machine-arn $(terraform output -raw blue_green_step_function_arn) \
                --input '{"action": "rollback"}' \
                --name "rollback-$DEPLOYMENT_ID" \
                > /dev/null
            ;;
        "canary")
            # Stop canary deployment and revert traffic
            aws stepfunctions stop-execution \
                --execution-arn "arn:aws:states:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):execution:$PROJECT_NAME-$ENVIRONMENT-canary-deployment:canary-$DEPLOYMENT_ID" \
                > /dev/null
            ;;
        "rolling")
            # Revert to previous task definition
            print_warning "Rolling deployments require manual rollback"
            ;;
    esac
    
    print_warning "Rollback initiated. Please verify system status."
}

# Function to cleanup on exit
cleanup() {
    local exit_code=$?
    
    if [[ $exit_code -ne 0 && "$ROLLBACK_ON_FAILURE" == "true" && "$DRY_RUN" != "true" ]]; then
        rollback_deployment
    fi
    
    # Calculate deployment duration
    local deployment_end_time=$(date +%s)
    local duration=$((deployment_end_time - DEPLOYMENT_START_TIME))
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Deployment completed successfully in ${duration}s"
        send_slack_notification "✅ Seiketsu AI deployment to $ENVIRONMENT completed successfully (${duration}s)" "good"
    else
        print_error "Deployment failed after ${duration}s"
        send_slack_notification "❌ Seiketsu AI deployment to $ENVIRONMENT failed after ${duration}s" "danger"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Main deployment flow
main() {
    send_slack_notification "🚀 Starting Seiketsu AI deployment to $ENVIRONMENT (Type: $DEPLOYMENT_TYPE)" "good"
    
    check_prerequisites
    run_tests
    build_and_push_images
    deploy_infrastructure
    deploy_application
    
    print_success "Deployment completed successfully!"
}

# Run main function
main "$@"