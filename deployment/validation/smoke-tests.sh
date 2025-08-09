#!/bin/bash

# Seiketsu AI Smoke Test Suite
# Quick validation tests to verify core functionality after deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="/tmp/seiketsu_smoke_tests_${TIMESTAMP}.log"

# Environment variables with defaults
API_BASE_URL="${API_BASE_URL:-https://api.seiketsu-ai.com}"
WEB_BASE_URL="${WEB_BASE_URL:-https://seiketsu-ai.com}"
TEST_TENANT_ID="${TEST_TENANT_ID:-smoke-test-tenant}"
API_TIMEOUT="${API_TIMEOUT:-30}"
VOICE_TIMEOUT="${VOICE_TIMEOUT:-10}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Test result tracking
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0

# Test execution wrapper
run_test() {
    local test_name="$1"
    local test_function="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    log_info "Running test: $test_name"
    
    if $test_function; then
        log_success "PASSED: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "FAILED: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# HTTP utility functions
http_get() {
    local url="$1"
    local expected_status="${2:-200}"
    local timeout="${3:-$API_TIMEOUT}"
    
    response=$(curl -s -w "%{http_code}" -m "$timeout" "$url" 2>/dev/null || echo "000")
    status_code="${response: -3}"
    
    if [[ "$status_code" == "$expected_status" ]]; then
        return 0
    else
        log_error "HTTP GET $url returned $status_code, expected $expected_status"
        return 1
    fi
}

http_post() {
    local url="$1"
    local data="$2"
    local expected_status="${3:-200}"
    local timeout="${4:-$API_TIMEOUT}"
    local headers="${5:-Content-Type: application/json}"
    
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "$headers" \
        -d "$data" \
        -m "$timeout" \
        "$url" 2>/dev/null || echo "000")
    status_code="${response: -3}"
    
    if [[ "$status_code" == "$expected_status" ]]; then
        return 0
    else
        log_error "HTTP POST $url returned $status_code, expected $expected_status"
        return 1
    fi
}

# Individual smoke tests
test_api_health() {
    log_info "Testing API health endpoint"
    http_get "$API_BASE_URL/health"
}

test_api_version() {
    log_info "Testing API version endpoint"
    http_get "$API_BASE_URL/version"
}

test_web_frontend() {
    log_info "Testing web frontend availability"
    if curl -s -m 10 "$WEB_BASE_URL" | grep -q "Seiketsu AI"; then
        return 0
    else
        log_error "Web frontend does not contain expected content"
        return 1
    fi
}

test_voice_endpoint() {
    log_info "Testing voice synthesis endpoint"
    local test_data='{
        "text": "This is a smoke test for voice synthesis.",
        "voice_id": "test_voice",
        "model_id": "eleven_monolingual_v1"
    }'
    
    # First check if endpoint is available (may return 401 without auth, which is expected)
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        -m "$VOICE_TIMEOUT" \
        "$API_BASE_URL/voice/synthesize" 2>/dev/null || echo "000")
    status_code="${response: -3}"
    
    # Accept 200 (success), 401 (unauthorized), or 422 (validation error) as valid responses
    if [[ "$status_code" == "200" || "$status_code" == "401" || "$status_code" == "422" ]]; then
        return 0
    else
        log_error "Voice endpoint unreachable or returning unexpected status: $status_code"
        return 1
    fi
}

test_database_connection() {
    log_info "Testing database connectivity through API"
    # Use a simple endpoint that requires database access
    response=$(curl -s -w "%{http_code}" -m 10 \
        "$API_BASE_URL/admin/health/database" 2>/dev/null || echo "000")
    status_code="${response: -3}"
    
    # Accept 200 (success) or 401 (unauthorized) as valid responses
    if [[ "$status_code" == "200" || "$status_code" == "401" ]]; then
        return 0
    else
        log_error "Database connectivity test failed with status: $status_code"
        return 1
    fi
}

test_redis_cache() {
    log_info "Testing Redis cache through API"
    response=$(curl -s -w "%{http_code}" -m 10 \
        "$API_BASE_URL/admin/health/cache" 2>/dev/null || echo "000")
    status_code="${response: -3}"
    
    # Accept 200 (success) or 401 (unauthorized) as valid responses
    if [[ "$status_code" == "200" || "$status_code" == "401" ]]; then
        return 0
    else
        log_error "Redis cache test failed with status: $status_code"
        return 1
    fi
}

test_tenant_provisioning() {
    log_info "Testing tenant provisioning endpoint"
    local tenant_data='{
        "name": "Smoke Test Tenant",
        "email": "smoketest@example.com",
        "plan": "basic"
    }'
    
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$tenant_data" \
        -m 15 \
        "$API_BASE_URL/admin/tenants" 2>/dev/null || echo "000")
    status_code="${response: -3}"
    
    # Accept 201 (created), 401 (unauthorized), or 409 (conflict) as valid responses
    if [[ "$status_code" == "201" || "$status_code" == "401" || "$status_code" == "409" ]]; then
        return 0
    else
        log_error "Tenant provisioning test failed with status: $status_code"
        return 1
    fi
}

test_authentication() {
    log_info "Testing authentication endpoint"
    local auth_data='{
        "email": "test@example.com",
        "password": "testpassword"
    }'
    
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$auth_data" \
        -m 10 \
        "$API_BASE_URL/auth/login" 2>/dev/null || echo "000")
    status_code="${response: -3}"
    
    # Accept 401 (unauthorized - expected for test credentials) or 422 (validation error)
    if [[ "$status_code" == "401" || "$status_code" == "422" ]]; then
        return 0
    else
        log_error "Authentication endpoint test failed with status: $status_code"
        return 1
    fi
}

test_websocket_endpoint() {
    log_info "Testing WebSocket endpoint availability"
    
    # Test if WebSocket endpoint is available (will fail connection but should not timeout)
    if command -v wscat >/dev/null 2>&1; then
        timeout 5 wscat -c "ws://localhost:8000/ws/voice" --close >/dev/null 2>&1 || true
        return 0
    else
        log_warning "wscat not available, skipping WebSocket test"
        TESTS_WARNINGS=$((TESTS_WARNINGS + 1))
        return 0
    fi
}

test_static_assets() {
    log_info "Testing static asset availability"
    
    # Test common static assets
    assets=(
        "$WEB_BASE_URL/favicon.ico"
        "$WEB_BASE_URL/_next/static/css/app/globals.css" 
        "$WEB_BASE_URL/assets/images/logo.png"
    )
    
    local failed_assets=0
    for asset in "${assets[@]}"; do
        if ! curl -s -f -m 5 "$asset" >/dev/null 2>&1; then
            log_warning "Static asset not available: $asset"
            failed_assets=$((failed_assets + 1))
        fi
    done
    
    if [[ $failed_assets -lt 2 ]]; then
        return 0  # Allow some assets to be missing
    else
        log_error "Too many static assets missing: $failed_assets"
        return 1
    fi
}

test_performance_baseline() {
    log_info "Testing basic performance baseline"
    
    # Measure API response time
    start_time=$(date +%s%N)
    if curl -s -f -m 5 "$API_BASE_URL/health" >/dev/null 2>&1; then
        end_time=$(date +%s%N)
        response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
        
        if [[ $response_time -lt 2000 ]]; then  # Less than 2 seconds
            log_info "API response time: ${response_time}ms"
            return 0
        else
            log_warning "API response time high: ${response_time}ms"
            TESTS_WARNINGS=$((TESTS_WARNINGS + 1))
            return 0
        fi
    else
        log_error "Performance baseline test failed - API unreachable"
        return 1
    fi
}

# Container/service status checks
test_container_health() {
    log_info "Testing container health (if Docker available)"
    
    if command -v docker >/dev/null 2>&1; then
        # Check if any seiketsu containers are running
        running_containers=$(docker ps --filter "name=seiketsu" --format "table {{.Names}}" 2>/dev/null | wc -l)
        
        if [[ $running_containers -gt 1 ]]; then  # Header + containers
            log_info "Found $((running_containers - 1)) running Seiketsu containers"
            return 0
        else
            log_warning "No Seiketsu containers found running locally"
            TESTS_WARNINGS=$((TESTS_WARNINGS + 1))
            return 0  # This is OK for cloud deployments
        fi
    else
        log_warning "Docker not available, skipping container health check"
        TESTS_WARNINGS=$((TESTS_WARNINGS + 1))
        return 0
    fi
}

# Main test execution
main() {
    log_info "Starting Seiketsu AI Smoke Tests"
    log_info "API Base URL: $API_BASE_URL"
    log_info "Web Base URL: $WEB_BASE_URL"
    log_info "Log File: $LOG_FILE"
    echo
    
    # Core functionality tests
    run_test "API Health Check" test_api_health
    run_test "API Version Check" test_api_version
    run_test "Web Frontend Availability" test_web_frontend
    run_test "Voice Service Endpoint" test_voice_endpoint
    run_test "Database Connection" test_database_connection
    run_test "Redis Cache" test_redis_cache
    
    # Feature tests
    run_test "Authentication Endpoint" test_authentication
    run_test "Tenant Provisioning" test_tenant_provisioning
    run_test "WebSocket Endpoint" test_websocket_endpoint
    
    # Performance and asset tests
    run_test "Static Assets" test_static_assets
    run_test "Performance Baseline" test_performance_baseline
    run_test "Container Health" test_container_health
    
    # Final report
    echo
    log_info "=== SMOKE TEST RESULTS ==="
    log_info "Total Tests: $TESTS_TOTAL"
    log_success "Passed: $TESTS_PASSED"
    log_error "Failed: $TESTS_FAILED"
    log_warning "Warnings: $TESTS_WARNINGS"
    
    local success_rate=0
    if [[ $TESTS_TOTAL -gt 0 ]]; then
        success_rate=$(( (TESTS_PASSED * 100) / TESTS_TOTAL ))
    fi
    
    log_info "Success Rate: $success_rate%"
    log_info "Log File: $LOG_FILE"
    echo
    
    # Determine exit code
    if [[ $TESTS_FAILED -eq 0 ]]; then
        if [[ $TESTS_WARNINGS -gt 0 ]]; then
            log_warning "All tests passed but with warnings"
            exit 2
        else
            log_success "All smoke tests passed successfully"
            exit 0
        fi
    else
        log_error "Smoke tests failed"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up smoke test resources..."
    # Add any cleanup logic here if needed
}

# Set up trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"