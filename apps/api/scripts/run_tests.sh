#!/bin/bash
# Comprehensive test runner script for Seiketsu AI API

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DB_NAME="seiketsu_test"

# Default values
RUN_UNIT=true
RUN_INTEGRATION=false
RUN_PERFORMANCE=false
RUN_SECURITY=false
RUN_ALL=false
COVERAGE=true
PARALLEL=true
VERBOSE=false
CLEAN=false

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
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test runner for Seiketsu AI API with comprehensive test suite management.

OPTIONS:
    -u, --unit           Run unit tests only (default)
    -i, --integration    Run integration tests
    -p, --performance    Run performance tests
    -s, --security       Run security tests
    -a, --all            Run all test suites
    --no-coverage        Disable coverage reporting
    --no-parallel        Disable parallel test execution
    -v, --verbose        Verbose output
    -c, --clean          Clean test artifacts before running
    --setup-db           Set up test database
    --cleanup-db         Clean up test database
    -h, --help           Show this help message

EXAMPLES:
    $0                          # Run unit tests with coverage
    $0 --all                    # Run all test suites
    $0 -i -p                    # Run integration and performance tests
    $0 --unit --verbose         # Run unit tests with verbose output
    $0 --clean --all            # Clean and run all tests

ENVIRONMENT VARIABLES:
    TEST_DATABASE_URL           Test database connection string
    REDIS_URL                   Redis connection string for tests
    PYTEST_WORKERS             Number of parallel test workers (default: auto)

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--unit)
            RUN_UNIT=true
            RUN_INTEGRATION=false
            RUN_PERFORMANCE=false
            RUN_SECURITY=false
            shift
            ;;
        -i|--integration)
            RUN_INTEGRATION=true
            shift
            ;;
        -p|--performance)
            RUN_PERFORMANCE=true
            shift
            ;;
        -s|--security)
            RUN_SECURITY=true
            shift
            ;;
        -a|--all)
            RUN_ALL=true
            RUN_UNIT=true
            RUN_INTEGRATION=true
            RUN_PERFORMANCE=true
            RUN_SECURITY=true
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --no-parallel)
            PARALLEL=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        --setup-db)
            setup_test_database
            exit 0
            ;;
        --cleanup-db)
            cleanup_test_database
            exit 0
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_DIR/pytest.ini" ]]; then
        print_error "pytest.ini not found. Please run from the API directory."
        exit 1
    fi
    
    # Check Python installation
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check if virtual environment is activated
    if [[ -z "$VIRTUAL_ENV" ]] && [[ ! -f "$PROJECT_DIR/.venv/bin/activate" ]]; then
        print_warning "No virtual environment detected. Consider using a virtual environment."
    fi
    
    # Check required packages
    if ! python3 -c "import pytest" 2>/dev/null; then
        print_error "pytest is not installed. Run: pip install -r requirements.txt"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to set up test database
setup_test_database() {
    print_status "Setting up test database..."
    
    # Check if PostgreSQL is running
    if ! pg_isready &> /dev/null; then
        print_error "PostgreSQL is not running. Please start PostgreSQL service."
        exit 1
    fi
    
    # Create test database if it doesn't exist
    if ! psql -lqt | cut -d \| -f 1 | grep -qw "$TEST_DB_NAME"; then
        print_status "Creating test database: $TEST_DB_NAME"
        createdb "$TEST_DB_NAME" || {
            print_error "Failed to create test database"
            exit 1
        }
    fi
    
    print_success "Test database setup complete"
}

# Function to clean up test database
cleanup_test_database() {
    print_status "Cleaning up test database..."
    
    if psql -lqt | cut -d \| -f 1 | grep -qw "$TEST_DB_NAME"; then
        print_status "Dropping test database: $TEST_DB_NAME"
        dropdb "$TEST_DB_NAME" || print_warning "Could not drop test database"
    fi
    
    print_success "Test database cleanup complete"
}

# Function to start Redis if needed
start_redis() {
    if ! redis-cli ping &> /dev/null; then
        print_status "Starting Redis server..."
        if command -v redis-server &> /dev/null; then
            redis-server --daemonize yes --port 6379
            sleep 2
            if redis-cli ping &> /dev/null; then
                print_success "Redis started successfully"
            else
                print_warning "Redis may not have started properly"
            fi
        else
            print_warning "Redis not found. Some tests may fail."
        fi
    fi
}

# Function to clean test artifacts
clean_artifacts() {
    print_status "Cleaning test artifacts..."
    
    # Remove coverage files
    rm -rf "$PROJECT_DIR/htmlcov"
    rm -f "$PROJECT_DIR/.coverage"
    rm -f "$PROJECT_DIR/coverage.xml"
    
    # Remove pytest cache
    rm -rf "$PROJECT_DIR/.pytest_cache"
    
    # Remove test reports
    rm -f "$PROJECT_DIR/test-report.html"
    rm -f "$PROJECT_DIR/test-report.xml"
    
    # Remove temporary files
    find "$PROJECT_DIR" -name "*.pyc" -delete
    find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Test artifacts cleaned"
}

# Function to build pytest command
build_pytest_command() {
    local cmd="python -m pytest"
    
    # Add basic options
    cmd="$cmd --tb=short"
    
    # Add coverage options
    if [[ "$COVERAGE" == true ]]; then
        cmd="$cmd --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml"
    fi
    
    # Add parallel execution
    if [[ "$PARALLEL" == true ]]; then
        local workers="${PYTEST_WORKERS:-auto}"
        cmd="$cmd -n $workers"
    fi
    
    # Add verbose output
    if [[ "$VERBOSE" == true ]]; then
        cmd="$cmd -v"
    fi
    
    # Add test markers based on what to run
    local markers=""
    
    if [[ "$RUN_ALL" == true ]]; then
        markers="unit or integration or performance or security"
    else
        local marker_parts=()
        [[ "$RUN_UNIT" == true ]] && marker_parts+=("unit")
        [[ "$RUN_INTEGRATION" == true ]] && marker_parts+=("integration")
        [[ "$RUN_PERFORMANCE" == true ]] && marker_parts+=("performance")
        [[ "$RUN_SECURITY" == true ]] && marker_parts+=("security")
        
        if [[ ${#marker_parts[@]} -gt 0 ]]; then
            markers=$(IFS=" or "; echo "${marker_parts[*]}")
        fi
    fi
    
    if [[ -n "$markers" ]]; then
        cmd="$cmd -m \"$markers\""
    fi
    
    # Add slow test option for performance tests
    if [[ "$RUN_PERFORMANCE" == true ]] || [[ "$RUN_ALL" == true ]]; then
        cmd="$cmd --runslow"
    fi
    
    # Add HTML report
    cmd="$cmd --html=test-report.html --self-contained-html"
    
    # Add JUnit XML for CI
    cmd="$cmd --junit-xml=test-report.xml"
    
    echo "$cmd"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    cd "$PROJECT_DIR"
    
    # Build and execute pytest command
    local pytest_cmd=$(build_pytest_command)
    
    print_status "Executing: $pytest_cmd"
    
    # Run tests and capture exit code
    if eval "$pytest_cmd"; then
        print_success "Tests completed successfully"
        return 0
    else
        local exit_code=$?
        print_error "Tests failed with exit code: $exit_code"
        return $exit_code
    fi
}

# Function to generate test report summary
generate_summary() {
    print_status "Generating test summary..."
    
    local report_file="$PROJECT_DIR/test-report.xml"
    if [[ -f "$report_file" ]]; then
        # Parse JUnit XML for summary
        if command -v xmllint &> /dev/null; then
            local total=$(xmllint --xpath "string(//testsuite/@tests)" "$report_file" 2>/dev/null || echo "0")
            local failures=$(xmllint --xpath "string(//testsuite/@failures)" "$report_file" 2>/dev/null || echo "0")
            local errors=$(xmllint --xpath "string(//testsuite/@errors)" "$report_file" 2>/dev/null || echo "0")
            local skipped=$(xmllint --xpath "string(//testsuite/@skipped)" "$report_file" 2>/dev/null || echo "0")
            local passed=$((total - failures - errors - skipped))
            
            echo
            echo "=========================================="
            echo "           TEST SUMMARY"
            echo "=========================================="
            echo "Total Tests:   $total"
            echo "Passed:        $passed"
            echo "Failed:        $failures"
            echo "Errors:        $errors"
            echo "Skipped:       $skipped"
            echo "=========================================="
            
            if [[ -f "$PROJECT_DIR/htmlcov/index.html" ]]; then
                echo "Coverage Report: htmlcov/index.html"
            fi
            
            if [[ -f "$PROJECT_DIR/test-report.html" ]]; then
                echo "Test Report:     test-report.html"
            fi
            echo "=========================================="
        fi
    fi
}

# Function to display performance metrics
show_performance_metrics() {
    if [[ "$RUN_PERFORMANCE" == true ]] || [[ "$RUN_ALL" == true ]]; then
        print_status "Performance test metrics available in test reports"
        
        # Look for performance test results
        if [[ -f "$PROJECT_DIR/test-report.html" ]]; then
            print_status "Detailed performance metrics in test-report.html"
        fi
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "    Seiketsu AI API Test Runner"
    echo "=========================================="
    echo
    
    # Check prerequisites
    check_prerequisites
    
    # Clean artifacts if requested
    if [[ "$CLEAN" == true ]]; then
        clean_artifacts
    fi
    
    # Set up services
    setup_test_database
    start_redis
    
    # Run tests
    local exit_code=0
    if ! run_tests; then
        exit_code=1
    fi
    
    # Generate reports
    generate_summary
    show_performance_metrics
    
    # Final status
    echo
    if [[ $exit_code -eq 0 ]]; then
        print_success "All tests completed successfully!"
    else
        print_error "Some tests failed. Check the reports for details."
    fi
    
    echo "=========================================="
    
    exit $exit_code
}

# Run main function
main "$@"