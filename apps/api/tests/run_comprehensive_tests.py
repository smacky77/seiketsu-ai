#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Seiketsu AI Platform
Runs all tests and generates detailed report for production readiness validation
"""
import sys
import os
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_test_category(category: str, test_files: List[str], markers: List[str] = None) -> Dict[str, Any]:
    """
    Run a category of tests and return results
    """
    print(f"\n{'='*60}")
    print(f"Running {category} Tests")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
    
    # Add markers if specified
    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])
    
    # Add test files
    cmd.extend(test_files)
    
    # Add JSON report
    json_report_file = f"test_results_{category.lower().replace(' ', '_')}.json"
    cmd.extend(["--json-report", f"--json-report-file={json_report_file}"])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Parse results
        passed = result.stdout.count(" PASSED")
        failed = result.stdout.count(" FAILED")
        skipped = result.stdout.count(" SKIPPED")
        errors = result.stdout.count(" ERROR")
        
        # Try to load JSON report if available
        json_data = None
        if os.path.exists(json_report_file):
            try:
                with open(json_report_file, 'r') as f:
                    json_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not parse JSON report: {e}")
        
        return {
            "category": category,
            "duration": duration,
            "return_code": result.returncode,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "total": passed + failed + skipped + errors,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "json_data": json_data
        }
        
    except subprocess.TimeoutExpired:
        return {
            "category": category,
            "duration": 1800,
            "return_code": -1,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 1,
            "total": 1,
            "stdout": "",
            "stderr": "Test execution timed out after 30 minutes",
            "json_data": None
        }
    except Exception as e:
        return {
            "category": category,
            "duration": time.time() - start_time,
            "return_code": -2,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 1,
            "total": 1,
            "stdout": "",
            "stderr": f"Test execution failed: {str(e)}",
            "json_data": None
        }

def generate_report(test_results: List[Dict[str, Any]]) -> str:
    """
    Generate comprehensive test report
    """
    total_duration = sum(r["duration"] for r in test_results)
    total_passed = sum(r["passed"] for r in test_results)
    total_failed = sum(r["failed"] for r in test_results)
    total_skipped = sum(r["skipped"] for r in test_results)
    total_errors = sum(r["errors"] for r in test_results)
    total_tests = sum(r["total"] for r in test_results)
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    report = f"""
{'='*80}
SEIKETSU AI PLATFORM - COMPREHENSIVE TEST REPORT
{'='*80}

Test Execution Summary:
{'-'*40}
Total Test Duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)
Total Tests Run: {total_tests}
Passed: {total_passed}
Failed: {total_failed}
Skipped: {total_skipped}
Errors: {total_errors}
Success Rate: {success_rate:.2f}%

Production Readiness Assessment:
{'-'*40}
"""
    
    # Assess production readiness
    if success_rate >= 95 and total_failed == 0 and total_errors == 0:
        report += "✅ PRODUCTION READY - All critical tests passing\n"
    elif success_rate >= 90 and total_failed <= 2:
        report += "⚠️  PRODUCTION READY WITH MINOR ISSUES - Review failed tests\n"
    elif success_rate >= 80:
        report += "❌ NOT PRODUCTION READY - Significant issues found\n"
    else:
        report += "🚨 CRITICAL ISSUES - Major system problems detected\n"
    
    report += f"\nDetailed Results by Category:\n{'-'*40}\n"
    
    for result in test_results:
        status = "✅ PASS" if result["return_code"] == 0 else "❌ FAIL"
        report += f"""
{result['category']}:
  Status: {status}
  Duration: {result['duration']:.2f}s
  Tests: {result['total']} (Passed: {result['passed']}, Failed: {result['failed']}, Skipped: {result['skipped']}, Errors: {result['errors']})
  Success Rate: {(result['passed'] / result['total'] * 100) if result['total'] > 0 else 0:.1f}%
"""
        
        if result["failed"] > 0 or result["errors"] > 0:
            report += f"  Issues Found: {result['failed']} failures, {result['errors']} errors\n"
            if result["stderr"]:
                report += f"  Error Details: {result['stderr'][:200]}...\n"
    
    report += f"\n{'='*80}\n"
    
    return report

def main():
    """
    Main test execution function
    """
    print("Starting Seiketsu AI Platform Comprehensive Test Suite")
    print(f"Test execution started at: {datetime.utcnow().isoformat()}")
    
    # Change to tests directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)
    
    # Define test categories and files
    test_categories = [
        {
            "name": "Authentication & Security",
            "files": ["test_auth.py", "test_api_comprehensive.py"],
            "markers": ["security"]
        },
        {
            "name": "Voice Integration",
            "files": ["test_voice_integration.py"],
            "markers": ["voice"]
        },
        {
            "name": "API Endpoints",
            "files": ["test_api_comprehensive.py"],
            "markers": ["api"]
        },
        {
            "name": "Database Integration",
            "files": ["test_database_integration.py"],
            "markers": ["database"]
        },
        {
            "name": "Redis Caching",
            "files": ["test_redis_caching.py"],
            "markers": ["redis"]
        },
        {
            "name": "Celery Background Tasks",
            "files": ["test_celery_tasks.py"],
            "markers": ["celery"]
        },
        {
            "name": "Error Handling",
            "files": ["test_error_handling.py"],
            "markers": ["error_handling"]
        },
        {
            "name": "21dev.ai Integration",
            "files": ["test_twentyonedev_integration.py"],
            "markers": ["twentyonedev"]
        },
        {
            "name": "Performance & Load Testing",
            "files": ["test_performance_load.py"],
            "markers": ["performance"]
        }
    ]
    
    # Run tests
    all_results = []
    
    for category in test_categories:
        # Check if test files exist
        existing_files = []
        for test_file in category["files"]:
            if os.path.exists(test_file):
                existing_files.append(test_file)
            else:
                print(f"Warning: Test file {test_file} not found, skipping...")
        
        if existing_files:
            result = run_test_category(
                category["name"],
                existing_files,
                category.get("markers")
            )
            all_results.append(result)
        else:
            print(f"Warning: No test files found for category {category['name']}")
    
    # Generate and display report
    report = generate_report(all_results)
    print(report)
    
    # Save report to file
    report_file = f"test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nDetailed test report saved to: {report_file}")
    
    # Return appropriate exit code
    total_failed = sum(r["failed"] for r in all_results)
    total_errors = sum(r["errors"] for r in all_results)
    
    if total_failed > 0 or total_errors > 0:
        print("\n❌ Tests completed with failures")
        return 1
    else:
        print("\n✅ All tests passed successfully")
        return 0

if __name__ == "__main__":
    sys.exit(main())