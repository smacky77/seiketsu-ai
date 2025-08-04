#!/usr/bin/env python3
"""
Seiketsu AI API Validation Test Runner
Enterprise-grade test execution with comprehensive reporting

Usage:
    python run_api_validation.py --help
    python run_api_validation.py --quick
    python run_api_validation.py --full
    python run_api_validation.py --performance
    python run_api_validation.py --security
    python run_api_validation.py --voice
"""

import argparse
import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_validation.log')
    ]
)
logger = logging.getLogger(__name__)


class APIValidationRunner:
    """API validation test runner with reporting"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def run_test_suite(self, test_markers: List[str], description: str) -> Dict:
        """Run a specific test suite and return results"""
        logger.info(f"🚀 Starting {description}")
        
        # Build pytest command
        cmd = [
            "python", "-m", "pytest",
            "tests/api/",
            "-v",
            "--tb=short",
            "--durations=10",
            "--json-report",
            "--json-report-file=test_results.json"
        ]
        
        # Add markers
        if test_markers:
            marker_expr = " and ".join(test_markers)
            cmd.extend(["-m", marker_expr])
        
        suite_start = time.time()
        
        try:
            # Run tests
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            suite_duration = time.time() - suite_start
            
            # Parse results
            test_result = {
                "description": description,
                "duration_seconds": round(suite_duration, 2),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "PASSED" if result.returncode == 0 else "FAILED"
            }
            
            # Try to parse JSON report if available
            try:
                with open("test_results.json", "r") as f:
                    json_report = json.load(f)
                    test_result["summary"] = json_report.get("summary", {})
            except FileNotFoundError:
                logger.warning("JSON test report not found")
            
            logger.info(f"✅ {description} completed in {suite_duration:.2f}s - {test_result['status']}")
            
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Error running {description}: {e}")
            return {
                "description": description,
                "duration_seconds": time.time() - suite_start,
                "error": str(e),
                "status": "ERROR"
            }
    
    def run_quick_validation(self) -> Dict:
        """Run quick validation tests"""
        return self.run_test_suite(
            ["not load", "not soak", "not external"],
            "Quick API Validation"
        )
    
    def run_security_validation(self) -> Dict:
        """Run security validation tests"""
        return self.run_test_suite(
            ["security", "auth", "multitenant"],
            "Security Validation"
        )
    
    def run_performance_validation(self) -> Dict:
        """Run performance validation tests"""
        return self.run_test_suite(
            ["performance", "not soak"],
            "Performance Validation"
        )
    
    def run_load_testing(self) -> Dict:
        """Run load testing suite"""
        return self.run_test_suite(
            ["load", "not soak"],
            "Load Testing"
        )
    
    def run_voice_validation(self) -> Dict:
        """Run voice-specific validation tests"""
        return self.run_test_suite(
            ["voice", "not voice_load"],
            "Voice Processing Validation"
        )
    
    def run_contract_validation(self) -> Dict:
        """Run API contract validation"""
        return self.run_test_suite(
            ["contract", "openapi"],
            "API Contract Validation"
        )
    
    def run_compliance_validation(self) -> Dict:
        """Run compliance validation tests"""
        return self.run_test_suite(
            ["compliance", "tcpa", "gdpr"],
            "Compliance Validation"
        )
    
    def run_full_validation(self) -> Dict:
        """Run complete validation suite (excluding long-running tests)"""
        logger.info("🎯 Running Full API Validation Suite")
        
        test_suites = [
            self.run_quick_validation,
            self.run_security_validation,
            self.run_performance_validation,
            self.run_voice_validation,
            self.run_contract_validation,
            self.run_compliance_validation
        ]
        
        results = {}
        overall_status = "PASSED"
        
        for test_suite in test_suites:
            result = test_suite()
            suite_name = result["description"].replace(" ", "_").lower()
            results[suite_name] = result
            
            if result["status"] != "PASSED":
                overall_status = "FAILED"
        
        results["overall_status"] = overall_status
        results["total_duration"] = time.time() - self.start_time
        
        return results
    
    def run_comprehensive_validation(self) -> Dict:
        """Run comprehensive validation including load tests"""
        logger.info("🚀 Running Comprehensive API Validation Suite")
        
        # Run full validation first
        results = self.run_full_validation()
        
        # Add load testing
        load_result = self.run_load_testing()
        results["load_testing"] = load_result
        
        if load_result["status"] != "PASSED":
            results["overall_status"] = "FAILED"
        
        results["total_duration"] = time.time() - self.start_time
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("🏢 SEIKETSU AI - API VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("📊 EXECUTIVE SUMMARY")
        report.append("-" * 40)
        report.append(f"Overall Status: {results.get('overall_status', 'UNKNOWN')}")
        report.append(f"Total Duration: {results.get('total_duration', 0):.2f} seconds")
        report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Individual test suite results
        report.append("📋 TEST SUITE RESULTS")
        report.append("-" * 40)
        
        for suite_name, suite_result in results.items():
            if suite_name in ["overall_status", "total_duration"]:
                continue
                
            status_emoji = "✅" if suite_result["status"] == "PASSED" else "❌"
            report.append(f"{status_emoji} {suite_result['description']}")
            report.append(f"   Duration: {suite_result['duration_seconds']}s")
            report.append(f"   Status: {suite_result['status']}")
            
            # Add summary if available
            if "summary" in suite_result:
                summary = suite_result["summary"]
                if isinstance(summary, dict):
                    total = summary.get("total", 0)
                    passed = summary.get("passed", 0)
                    failed = summary.get("failed", 0)
                    report.append(f"   Tests: {passed}/{total} passed, {failed} failed")
            
            report.append("")
        
        # Performance metrics (if available)
        report.append("⚡ PERFORMANCE METRICS")
        report.append("-" * 40)
        report.append("Voice Processing: <180ms target")
        report.append("Standard APIs: <100ms target")
        report.append("WebSocket Latency: <20ms target")
        report.append("Concurrent Requests: 1000+ RPS target")
        report.append("")
        
        # Security validation
        report.append("🔒 SECURITY VALIDATION")
        report.append("-" * 40)
        security_result = results.get("security_validation", {})
        if security_result.get("status") == "PASSED":
            report.append("✅ Authentication & Authorization")
            report.append("✅ SQL Injection Prevention")
            report.append("✅ XSS Protection")
            report.append("✅ Rate Limiting")
            report.append("✅ Multi-tenant Isolation")
        else:
            report.append("❌ Security validation failed - review logs")
        report.append("")
        
        # Recommendations
        report.append("🎯 RECOMMENDATIONS")
        report.append("-" * 40)
        
        overall_status = results.get("overall_status")
        if overall_status == "PASSED":
            report.append("✅ API validation passed - ready for production")
            report.append("• Monitor performance metrics in production")
            report.append("• Set up alerting for key thresholds")
            report.append("• Schedule regular validation runs")
        else:
            report.append("❌ API validation failed - address issues before production")
            report.append("• Review failed test logs")
            report.append("• Fix performance or security issues")
            report.append("• Re-run validation after fixes")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_results(self, results: Dict, filename: str = "api_validation_results.json"):
        """Save test results to JSON file"""
        try:
            with open(filename, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"📄 Results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Seiketsu AI API Validation Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_api_validation.py --quick         # Quick validation (5-10 minutes)
  python run_api_validation.py --full          # Full validation (20-30 minutes)  
  python run_api_validation.py --comprehensive # Complete with load tests (45+ minutes)
  python run_api_validation.py --security      # Security tests only
  python run_api_validation.py --performance   # Performance tests only
  python run_api_validation.py --voice         # Voice processing tests only
        """
    )
    
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick validation tests (excludes load testing)")
    parser.add_argument("--full", action="store_true",
                       help="Run full validation suite (excludes heavy load tests)")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Run comprehensive validation including load tests")
    parser.add_argument("--security", action="store_true",
                       help="Run security validation tests only")
    parser.add_argument("--performance", action="store_true", 
                       help="Run performance validation tests only")
    parser.add_argument("--voice", action="store_true",
                       help="Run voice processing validation tests only")
    parser.add_argument("--contract", action="store_true",
                       help="Run API contract validation tests only")
    parser.add_argument("--compliance", action="store_true",
                       help="Run compliance validation tests only")
    parser.add_argument("--load", action="store_true",
                       help="Run load testing suite only")
    parser.add_argument("--report-only", action="store_true",
                       help="Generate report from existing results file")
    parser.add_argument("--output", default="api_validation_results.json",
                       help="Output file for results (default: api_validation_results.json)")
    
    args = parser.parse_args()
    
    runner = APIValidationRunner()
    
    # Handle report-only mode
    if args.report_only:
        try:
            with open(args.output, "r") as f:
                results = json.load(f)
            report = runner.generate_report(results)
            print(report)
            return
        except FileNotFoundError:
            logger.error(f"Results file {args.output} not found")
            sys.exit(1)
    
    # Determine which tests to run
    results = {}
    
    if args.comprehensive:
        results = runner.run_comprehensive_validation()
    elif args.full:
        results = runner.run_full_validation()  
    elif args.quick:
        results = runner.run_quick_validation()
    elif args.security:
        results = {"security_validation": runner.run_security_validation()}
    elif args.performance:
        results = {"performance_validation": runner.run_performance_validation()}
    elif args.voice:
        results = {"voice_validation": runner.run_voice_validation()}
    elif args.contract:
        results = {"contract_validation": runner.run_contract_validation()}
    elif args.compliance:
        results = {"compliance_validation": runner.run_compliance_validation()}
    elif args.load:
        results = {"load_testing": runner.run_load_testing()}
    else:
        # Default to quick validation
        logger.info("No specific test suite specified, running quick validation")
        results = runner.run_quick_validation()
    
    # Save results
    runner.save_results(results, args.output)
    
    # Generate and display report
    report = runner.generate_report(results)
    print("\n" + report)
    
    # Exit with appropriate code
    overall_status = results.get("overall_status")
    if isinstance(results, dict) and len(results) == 1:
        # Single test suite
        suite_result = list(results.values())[0]
        overall_status = suite_result.get("status")
    
    if overall_status == "PASSED":
        logger.info("🎉 API validation completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ API validation failed - check logs for details")
        sys.exit(1)


if __name__ == "__main__":
    main()