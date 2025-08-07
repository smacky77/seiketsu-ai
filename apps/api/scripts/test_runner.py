#!/usr/bin/env python3
"""
Advanced Python test runner for Seiketsu AI API with comprehensive test management,
reporting, and CI/CD integration.
"""
import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
import logging

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test execution result"""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration: float
    coverage_percent: Optional[float] = None
    exit_code: int = 0


class TestRunner:
    """Advanced test runner with comprehensive features"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent.parent
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
    def setup_environment(self):
        """Set up test environment"""
        logger.info("Setting up test environment...")
        
        # Set environment variables for testing
        os.environ.update({
            'ENVIRONMENT': 'test',
            'PYTHONPATH': str(self.project_dir),
            'PYTEST_CURRENT_TEST': 'true'
        })
        
        # Change to project directory
        os.chdir(self.project_dir)
        
        logger.info("Test environment configured")
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        logger.info("Checking test dependencies...")
        
        required_packages = [
            'pytest',
            'pytest-asyncio',
            'pytest-cov',
            'pytest-xdist',
            'pytest-benchmark',
            'pytest-html'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {', '.join(missing_packages)}")
            logger.error("Install with: pip install -r requirements.txt")
            return False
        
        logger.info("All dependencies are installed")
        return True
    
    def clean_artifacts(self):
        """Clean test artifacts and cache files"""
        logger.info("Cleaning test artifacts...")
        
        # Directories to clean
        clean_dirs = [
            '.pytest_cache',
            'htmlcov',
            '__pycache__',
            '.coverage'
        ]
        
        # Files to clean
        clean_files = [
            'coverage.xml',
            'test-report.html',
            'test-report.xml',
            '.coverage'
        ]
        
        # Clean directories
        for dir_name in clean_dirs:
            dir_path = self.project_dir / dir_name
            if dir_path.exists():
                subprocess.run(['rm', '-rf', str(dir_path)], check=False)
        
        # Clean files
        for file_name in clean_files:
            file_path = self.project_dir / file_name
            if file_path.exists():
                file_path.unlink()
        
        # Clean Python cache files recursively
        for cache_dir in self.project_dir.rglob('__pycache__'):
            subprocess.run(['rm', '-rf', str(cache_dir)], check=False)
        
        for pyc_file in self.project_dir.rglob('*.pyc'):
            pyc_file.unlink()
        
        logger.info("Test artifacts cleaned")
    
    def build_pytest_command(self, test_type: str, **options) -> List[str]:
        """Build pytest command based on test type and options"""
        cmd = ['python', '-m', 'pytest']
        
        # Basic options
        cmd.extend(['--tb=short', '--strict-markers'])
        
        # Coverage options
        if options.get('coverage', True):
            cmd.extend([
                '--cov=app',
                '--cov-report=html',
                '--cov-report=term-missing',
                '--cov-report=xml',
                '--cov-fail-under=80'
            ])
        
        # Parallel execution
        if options.get('parallel', True):
            workers = options.get('workers', 'auto')
            cmd.extend(['-n', str(workers)])
        
        # Verbose output
        if options.get('verbose', False):
            cmd.append('-v')
        
        # Test markers based on type
        marker_map = {
            'unit': 'unit',
            'integration': 'integration', 
            'performance': 'performance and slow',
            'security': 'security',
            'ai': 'ai',
            'voice': 'voice',
            'database': 'database',
            'api': 'api',
            'websocket': 'websocket',
            'all': 'unit or integration or performance or security'
        }
        
        if test_type in marker_map:
            cmd.extend(['-m', marker_map[test_type]])
        
        # Additional options for specific test types
        if test_type in ['performance', 'all']:
            cmd.append('--runslow')
        
        if test_type in ['external', 'all']:
            cmd.append('--runexternal')
        
        # Timeout for long-running tests
        if test_type in ['performance', 'integration']:
            cmd.extend(['--timeout=300'])
        
        # Reporting options
        cmd.extend([
            '--html=test-report.html',
            '--self-contained-html',
            '--junit-xml=test-report.xml'
        ])
        
        # Benchmark options for performance tests
        if test_type == 'performance':
            cmd.extend([
                '--benchmark-only',
                '--benchmark-sort=mean',
                '--benchmark-json=benchmark-report.json'
            ])
        
        return cmd
    
    def run_test_suite(self, test_type: str, **options) -> TestResult:
        """Run a specific test suite"""
        logger.info(f"Running {test_type} tests...")
        
        start_time = time.time()
        cmd = self.build_pytest_command(test_type, **options)
        
        # Log the command being executed
        logger.info(f"Executing: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            
            duration = time.time() - start_time
            
            # Parse test results
            test_result = self.parse_test_results(test_type, result, duration)
            
            # Log results
            if test_result.exit_code == 0:
                logger.info(f"{test_type} tests completed successfully")
            else:
                logger.error(f"{test_type} tests failed with exit code {test_result.exit_code}")
            
            # Log test output if there are failures
            if result.returncode != 0 and options.get('verbose', False):
                logger.error("Test output:")
                logger.error(result.stdout)
                if result.stderr:
                    logger.error("Error output:")
                    logger.error(result.stderr)
            
            return test_result
            
        except Exception as e:
            logger.error(f"Failed to run {test_type} tests: {e}")
            return TestResult(
                suite_name=test_type,
                total_tests=0,
                passed=0,
                failed=0,
                errors=1,
                skipped=0,
                duration=time.time() - start_time,
                exit_code=1
            )
    
    def parse_test_results(self, suite_name: str, result: subprocess.CompletedProcess, duration: float) -> TestResult:
        """Parse test results from pytest output"""
        # Try to parse JUnit XML first
        junit_file = self.project_dir / 'test-report.xml'
        
        if junit_file.exists():
            try:
                tree = ET.parse(junit_file)
                root = tree.getroot()
                
                # Extract test counts from testsuite element
                testsuite = root.find('.//testsuite')
                if testsuite is not None:
                    total = int(testsuite.get('tests', 0))
                    failures = int(testsuite.get('failures', 0))
                    errors = int(testsuite.get('errors', 0))
                    skipped = int(testsuite.get('skipped', 0))
                    passed = total - failures - errors - skipped
                    
                    return TestResult(
                        suite_name=suite_name,
                        total_tests=total,
                        passed=passed,
                        failed=failures,
                        errors=errors,
                        skipped=skipped,
                        duration=duration,
                        coverage_percent=self.parse_coverage(),
                        exit_code=result.returncode
                    )
            except Exception as e:
                logger.warning(f"Could not parse JUnit XML: {e}")
        
        # Fallback to parsing stdout
        output = result.stdout
        
        # Look for pytest summary line
        summary_patterns = [
            r'(\d+) passed',
            r'(\d+) failed',
            r'(\d+) error',
            r'(\d+) skipped'
        ]
        
        counts = {'passed': 0, 'failed': 0, 'errors': 0, 'skipped': 0}
        
        for line in output.split('\n'):
            if 'passed' in line or 'failed' in line or 'error' in line:
                for pattern_name, pattern in zip(['passed', 'failed', 'errors', 'skipped'], summary_patterns):
                    import re
                    match = re.search(pattern, line)
                    if match:
                        counts[pattern_name] = int(match.group(1))
        
        total = sum(counts.values())
        
        return TestResult(
            suite_name=suite_name,
            total_tests=total,
            passed=counts['passed'],
            failed=counts['failed'],
            errors=counts['errors'],
            skipped=counts['skipped'],
            duration=duration,
            coverage_percent=self.parse_coverage(),
            exit_code=result.returncode
        )
    
    def parse_coverage(self) -> Optional[float]:
        """Parse coverage percentage from coverage report"""
        coverage_file = self.project_dir / 'coverage.xml'
        
        if coverage_file.exists():
            try:
                tree = ET.parse(coverage_file)
                root = tree.getroot()
                
                # Look for coverage element with line-rate attribute
                coverage_elem = root.find('.//coverage')
                if coverage_elem is not None:
                    line_rate = coverage_elem.get('line-rate')
                    if line_rate:
                        return float(line_rate) * 100
            except Exception as e:
                logger.warning(f"Could not parse coverage report: {e}")
        
        return None
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating test report...")
        
        total_duration = time.time() - self.start_time
        
        # Calculate overall statistics
        total_tests = sum(r.total_tests for r in self.results)
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration': total_duration,
            'summary': {
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'errors': total_errors,
                'skipped': total_skipped,
                'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0
            },
            'suites': [
                {
                    'name': r.suite_name,
                    'total': r.total_tests,
                    'passed': r.passed,
                    'failed': r.failed,
                    'errors': r.errors,
                    'skipped': r.skipped,
                    'duration': r.duration,
                    'coverage': r.coverage_percent,
                    'exit_code': r.exit_code
                }
                for r in self.results
            ]
        }
        
        # Save JSON report
        report_file = self.project_dir / 'test-summary.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary to console
        self.print_summary(report)
        
        return report
    
    def print_summary(self, report: Dict):
        """Print test summary to console"""
        print("\n" + "="*60)
        print("              SEIKETSU AI TEST SUMMARY")
        print("="*60)
        
        summary = report['summary']
        
        print(f"Total Duration:    {report['duration']:.2f} seconds")
        print(f"Total Tests:       {summary['total_tests']}")
        print(f"Passed:            {summary['passed']}")
        print(f"Failed:            {summary['failed']}")
        print(f"Errors:            {summary['errors']}")
        print(f"Skipped:           {summary['skipped']}")
        print(f"Success Rate:      {summary['success_rate']:.1f}%")
        
        print("\n" + "-"*60)
        print("SUITE BREAKDOWN")
        print("-"*60)
        
        for suite in report['suites']:
            status = "✓" if suite['exit_code'] == 0 else "✗"
            coverage = f"{suite['coverage']:.1f}%" if suite['coverage'] else "N/A"
            
            print(f"{status} {suite['name']:15} | "
                  f"Tests: {suite['total']:3} | "
                  f"Passed: {suite['passed']:3} | "
                  f"Failed: {suite['failed']:2} | "
                  f"Coverage: {coverage:6} | "
                  f"Duration: {suite['duration']:6.2f}s")
        
        print("-"*60)
        
        # Show report files
        report_files = []
        if (self.project_dir / 'htmlcov' / 'index.html').exists():
            report_files.append("Coverage Report: htmlcov/index.html")
        if (self.project_dir / 'test-report.html').exists():
            report_files.append("Test Report:     test-report.html")
        if (self.project_dir / 'test-summary.json').exists():
            report_files.append("JSON Summary:    test-summary.json")
        
        if report_files:
            print("REPORTS GENERATED:")
            for report_file in report_files:
                print(f"  {report_file}")
        
        print("="*60)
    
    def run_continuous_integration(self, **options) -> bool:
        """Run tests in CI/CD mode with comprehensive validation"""
        logger.info("Running in CI/CD mode...")
        
        # Set stricter options for CI
        ci_options = {
            'coverage': True,
            'parallel': True,
            'verbose': False,
            **options
        }
        
        # Run all test suites in CI mode
        test_suites = ['unit', 'integration', 'security']
        
        # Add performance tests if specifically requested
        if options.get('include_performance', False):
            test_suites.append('performance')
        
        all_passed = True
        
        for suite in test_suites:
            result = self.run_test_suite(suite, **ci_options)
            self.results.append(result)
            
            if result.exit_code != 0:
                all_passed = False
        
        # Generate report
        self.generate_report()
        
        # Validate coverage requirements
        if ci_options.get('coverage', True):
            coverage_threshold = options.get('coverage_threshold', 80)
            for result in self.results:
                if result.coverage_percent and result.coverage_percent < coverage_threshold:
                    logger.error(f"Coverage {result.coverage_percent:.1f}% below threshold {coverage_threshold}%")
                    all_passed = False
        
        return all_passed


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Advanced test runner for Seiketsu AI API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py --unit                 # Run unit tests only
  python test_runner.py --all                  # Run all test suites
  python test_runner.py --integration --verbose # Run integration tests with verbose output
  python test_runner.py --ci                   # Run in CI/CD mode
  python test_runner.py --performance --no-parallel # Run performance tests sequentially
        """
    )
    
    # Test suite selection
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--security', action='store_true', help='Run security tests')
    parser.add_argument('--ai', action='store_true', help='Run AI service tests')
    parser.add_argument('--voice', action='store_true', help='Run voice processing tests')
    parser.add_argument('--database', action='store_true', help='Run database tests')
    parser.add_argument('--api', action='store_true', help='Run API endpoint tests')
    parser.add_argument('--all', action='store_true', help='Run all test suites')
    
    # Execution options
    parser.add_argument('--no-coverage', action='store_true', help='Disable coverage reporting')
    parser.add_argument('--no-parallel', action='store_true', help='Disable parallel execution')
    parser.add_argument('--workers', type=str, default='auto', help='Number of parallel workers')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--clean', action='store_true', help='Clean artifacts before running')
    
    # CI/CD options
    parser.add_argument('--ci', action='store_true', help='Run in CI/CD mode')
    parser.add_argument('--coverage-threshold', type=float, default=80, help='Coverage threshold for CI')
    parser.add_argument('--include-performance', action='store_true', help='Include performance tests in CI')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner()
    
    try:
        # Setup
        runner.setup_environment()
        
        if not runner.check_dependencies():
            sys.exit(1)
        
        if args.clean:
            runner.clean_artifacts()
        
        # Determine what to run
        if args.ci:
            # CI/CD mode
            options = {
                'coverage': not args.no_coverage,
                'parallel': not args.no_parallel,
                'workers': args.workers,
                'verbose': args.verbose,
                'coverage_threshold': args.coverage_threshold,
                'include_performance': args.include_performance
            }
            
            success = runner.run_continuous_integration(**options)
            sys.exit(0 if success else 1)
        
        # Regular mode - determine test suites to run
        test_suites = []
        
        if args.all:
            test_suites = ['unit', 'integration', 'performance', 'security']
        else:
            if args.unit:
                test_suites.append('unit')
            if args.integration:
                test_suites.append('integration')
            if args.performance:
                test_suites.append('performance')
            if args.security:
                test_suites.append('security')
            if args.ai:
                test_suites.append('ai')
            if args.voice:
                test_suites.append('voice')
            if args.database:
                test_suites.append('database')
            if args.api:
                test_suites.append('api')
        
        # Default to unit tests if nothing specified
        if not test_suites:
            test_suites = ['unit']
        
        # Run test suites
        options = {
            'coverage': not args.no_coverage,
            'parallel': not args.no_parallel,
            'workers': args.workers,
            'verbose': args.verbose
        }
        
        all_passed = True
        
        for suite in test_suites:
            result = runner.run_test_suite(suite, **options)
            runner.results.append(result)
            
            if result.exit_code != 0:
                all_passed = False
        
        # Generate final report
        runner.generate_report()
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()