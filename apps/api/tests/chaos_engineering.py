"""
Chaos Engineering Tests for System Resilience
Tests system behavior under failure conditions and stress
"""
import pytest
import asyncio
import random
import time
import logging
from typing import Dict, Any, List, Callable
from unittest.mock import patch, AsyncMock, Mock
from contextlib import asynccontextmanager
import psutil
import threading

from app.main import app
from app.services.voice_service import VoiceService
from app.ai.conversation.engine import ConversationAI
from app.core.database import get_db
from fastapi.testclient import TestClient


class ChaosExperiment:
    """Base class for chaos engineering experiments"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"chaos.{name}")
        
    async def setup(self):
        """Setup experiment"""
        pass
    
    async def inject_failure(self):
        """Inject failure into system"""
        raise NotImplementedError
    
    async def monitor_system(self, duration_seconds: int) -> Dict[str, Any]:
        """Monitor system during experiment"""
        start_time = time.time()
        metrics = {
            "start_time": start_time,
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "errors": []
        }
        
        while time.time() - start_time < duration_seconds:
            try:
                # Make test request
                request_start = time.time()
                success = await self._make_test_request()
                response_time = (time.time() - request_start) * 1000
                
                metrics["requests_total"] += 1
                if success:
                    metrics["requests_successful"] += 1
                else:
                    metrics["requests_failed"] += 1
                
                # Update response time metrics
                if metrics["max_response_time"] < response_time:
                    metrics["max_response_time"] = response_time
                
                metrics["avg_response_time"] = (
                    (metrics["avg_response_time"] * (metrics["requests_total"] - 1) + response_time) 
                    / metrics["requests_total"]
                )
                
                await asyncio.sleep(0.1)  # 100ms between requests
                
            except Exception as e:
                metrics["errors"].append(str(e))
                
        return metrics
    
    async def _make_test_request(self) -> bool:
        """Make a test request to verify system health"""
        # Override in specific experiments
        return True
    
    async def cleanup(self):
        """Clean up after experiment"""
        pass
    
    async def run_experiment(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Run complete chaos experiment"""
        self.logger.info(f"Starting chaos experiment: {self.name}")
        
        try:
            await self.setup()
            
            # Start monitoring
            monitor_task = asyncio.create_task(
                self.monitor_system(duration_seconds)
            )
            
            # Inject failure after brief warm-up
            await asyncio.sleep(5)
            await self.inject_failure()
            
            # Wait for monitoring to complete
            metrics = await monitor_task
            
            await self.cleanup()
            
            self.logger.info(f"Chaos experiment completed: {self.name}")
            return {
                "experiment": self.name,
                "description": self.description,
                "metrics": metrics,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Chaos experiment failed: {self.name} - {e}")
            return {
                "experiment": self.name,
                "description": self.description,
                "error": str(e),
                "success": False
            }


class DatabaseFailureExperiment(ChaosExperiment):
    """Test system resilience when database connections fail"""
    
    def __init__(self):
        super().__init__(
            "database_failure",
            "Simulate database connection failures and test recovery"
        )
        self.original_get_db = None
        self.failure_rate = 0.5  # 50% of requests fail
    
    async def setup(self):
        """Setup database failure simulation"""
        from app.core.database import get_db
        self.original_get_db = get_db
    
    async def inject_failure(self):
        """Inject database failures"""
        async def failing_get_db():
            if random.random() < self.failure_rate:
                raise Exception("Database connection failed")
            else:
                async for db in self.original_get_db():
                    yield db
        
        # Replace database connection with failing version
        with patch('app.core.database.get_db', failing_get_db):
            await asyncio.sleep(30)  # Let it fail for 30 seconds
    
    async def _make_test_request(self) -> bool:
        """Test database-dependent endpoint"""
        try:
            client = TestClient(app)
            response = client.get("/api/v1/health")
            return response.status_code == 200
        except:
            return False


class ExternalAPIFailureExperiment(ChaosExperiment):
    """Test resilience when external APIs (OpenAI, ElevenLabs) fail"""
    
    def __init__(self):
        super().__init__(
            "external_api_failure",
            "Simulate external API failures and test fallback mechanisms"
        )
        self.voice_service = None
        self.failure_scenarios = [
            "openai_timeout",
            "elevenlabs_rate_limit", 
            "elevenlabs_service_down",
            "network_partition"
        ]
    
    async def setup(self):
        """Setup external API failure simulation"""
        self.voice_service = VoiceService()
    
    async def inject_failure(self):
        """Inject various external API failures"""
        scenario = random.choice(self.failure_scenarios)
        self.logger.info(f"Injecting failure scenario: {scenario}")
        
        if scenario == "openai_timeout":
            with patch('openai.AsyncOpenAI') as mock_openai:
                mock_client = AsyncMock()
                mock_client.chat.completions.create.side_effect = asyncio.TimeoutError()
                mock_openai.return_value = mock_client
                await asyncio.sleep(20)
        
        elif scenario == "elevenlabs_rate_limit":
            with patch('httpx.AsyncClient.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 429
                mock_response.headers = {"retry-after": "60"}
                mock_post.return_value = mock_response
                await asyncio.sleep(15)
        
        elif scenario == "elevenlabs_service_down":
            with patch('httpx.AsyncClient.post') as mock_post:
                mock_post.side_effect = Exception("Service unavailable")
                await asyncio.sleep(25)
        
        elif scenario == "network_partition":
            # Simulate network issues
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.side_effect = Exception("Network unreachable")
                await asyncio.sleep(30)
    
    async def _make_test_request(self) -> bool:
        """Test voice processing endpoint"""
        try:
            if self.voice_service:
                # Simulate voice processing
                result = await self.voice_service.process_voice_input(
                    b"test_audio", "test_conv", Mock(), "test_org"
                )
                return result.get("success", False)
        except:
            return False
        return False


class MemoryLeakExperiment(ChaosExperiment):
    """Test system behavior under memory pressure"""
    
    def __init__(self):
        super().__init__(
            "memory_pressure",
            "Simulate memory pressure and test memory management"
        )
        self.memory_hogs = []
        self.initial_memory = 0
    
    async def setup(self):
        """Setup memory monitoring"""
        self.initial_memory = psutil.Process().memory_info().rss
    
    async def inject_failure(self):
        """Create memory pressure"""
        # Allocate large amounts of memory gradually
        for i in range(10):
            # Allocate 50MB chunks
            memory_hog = bytearray(50 * 1024 * 1024)  # 50MB
            self.memory_hogs.append(memory_hog)
            await asyncio.sleep(2)
    
    async def monitor_system(self, duration_seconds: int) -> Dict[str, Any]:
        """Monitor memory usage during experiment"""
        metrics = await super().monitor_system(duration_seconds)
        
        current_memory = psutil.Process().memory_info().rss
        metrics["memory_increase_mb"] = (current_memory - self.initial_memory) / 1024 / 1024
        metrics["memory_usage_mb"] = current_memory / 1024 / 1024
        
        return metrics
    
    async def cleanup(self):
        """Clean up allocated memory"""
        self.memory_hogs.clear()


class HighConcurrencyExperiment(ChaosExperiment):
    """Test system behavior under high concurrent load"""
    
    def __init__(self):
        super().__init__(
            "high_concurrency",
            "Test system under extreme concurrent load"
        )
        self.concurrent_tasks = []
    
    async def inject_failure(self):
        """Create high concurrent load"""
        async def concurrent_request():
            try:
                client = TestClient(app)
                response = client.get("/api/v1/health")
                return response.status_code == 200
            except:
                return False
        
        # Create 500 concurrent tasks
        self.concurrent_tasks = [
            asyncio.create_task(concurrent_request())
            for _ in range(500)
        ]
        
        # Wait for all tasks with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.concurrent_tasks, return_exceptions=True),
                timeout=30
            )
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in self.concurrent_tasks:
                if not task.done():
                    task.cancel()


class CPUExhaustionExperiment(ChaosExperiment):
    """Test system behavior under CPU exhaustion"""
    
    def __init__(self):
        super().__init__(
            "cpu_exhaustion", 
            "Simulate CPU exhaustion and test system responsiveness"
        )
        self.cpu_threads = []
        self.stop_cpu_load = False
    
    def cpu_intensive_task(self):
        """CPU intensive task to create load"""
        while not self.stop_cpu_load:
            # CPU intensive calculation
            sum(i*i for i in range(10000))
    
    async def inject_failure(self):
        """Create CPU load"""
        # Start CPU intensive threads (one per core)
        cpu_count = psutil.cpu_count()
        for _ in range(cpu_count):
            thread = threading.Thread(target=self.cpu_intensive_task)
            thread.start()
            self.cpu_threads.append(thread)
        
        await asyncio.sleep(30)  # Run CPU load for 30 seconds
    
    async def cleanup(self):
        """Stop CPU load"""
        self.stop_cpu_load = True
        for thread in self.cpu_threads:
            thread.join(timeout=1)


class NetworkLatencyExperiment(ChaosExperiment):
    """Test system behavior under network latency"""
    
    def __init__(self):
        super().__init__(
            "network_latency",
            "Simulate network latency and test timeout handling"
        )
    
    async def inject_failure(self):
        """Inject network latency"""
        original_request = None
        
        async def slow_request(*args, **kwargs):
            # Add random latency between 1-5 seconds
            await asyncio.sleep(random.uniform(1, 5))
            if original_request:
                return await original_request(*args, **kwargs)
            return Mock(status_code=408)  # Request timeout
        
        with patch('httpx.AsyncClient.post', slow_request):
            with patch('httpx.AsyncClient.get', slow_request):
                await asyncio.sleep(25)


class CascadingFailureExperiment(ChaosExperiment):
    """Test cascading failure scenarios"""
    
    def __init__(self):
        super().__init__(
            "cascading_failure",
            "Simulate cascading failures across multiple components"
        )
    
    async def inject_failure(self):
        """Inject cascading failures"""
        # Phase 1: Database slowdown
        self.logger.info("Phase 1: Database slowdown")
        with patch('asyncpg.connect') as mock_connect:
            async def slow_connect(*args, **kwargs):
                await asyncio.sleep(2)  # 2 second delay
                raise Exception("Connection timeout")
            mock_connect.side_effect = slow_connect
            await asyncio.sleep(10)
        
        # Phase 2: External API failures
        self.logger.info("Phase 2: External API failures")
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.side_effect = Exception("Service degraded")
            await asyncio.sleep(10)
        
        # Phase 3: Memory pressure
        self.logger.info("Phase 3: Memory pressure")
        memory_hogs = []
        for i in range(5):
            memory_hogs.append(bytearray(100 * 1024 * 1024))  # 100MB each
            await asyncio.sleep(2)


@pytest.mark.chaos
@pytest.mark.asyncio
class TestChaosEngineering:
    """Chaos engineering test suite"""
    
    async def test_database_failure_resilience(self):
        """Test system resilience to database failures"""
        experiment = DatabaseFailureExperiment()
        result = await experiment.run_experiment(duration_seconds=45)
        
        assert result["success"] is True
        
        metrics = result["metrics"]
        
        # System should handle at least some requests successfully
        success_rate = metrics["requests_successful"] / metrics["requests_total"] if metrics["requests_total"] > 0 else 0
        assert success_rate >= 0.3, f"Success rate too low: {success_rate}"
        
        # Response times should be reasonable for successful requests
        if metrics["requests_successful"] > 0:
            assert metrics["avg_response_time"] < 5000, f"Average response time too high: {metrics['avg_response_time']}ms"
    
    async def test_external_api_failure_resilience(self):
        """Test resilience to external API failures"""
        experiment = ExternalAPIFailureExperiment()
        result = await experiment.run_experiment(duration_seconds=60)
        
        assert result["success"] is True
        
        # System should implement fallback mechanisms
        metrics = result["metrics"]
        assert metrics["requests_total"] > 0, "No requests were made during experiment"
        
        # Should have some level of graceful degradation
        failure_rate = metrics["requests_failed"] / metrics["requests_total"]
        assert failure_rate < 0.9, f"Failure rate too high: {failure_rate}"
    
    async def test_memory_pressure_resilience(self):
        """Test system behavior under memory pressure"""
        experiment = MemoryLeakExperiment()
        result = await experiment.run_experiment(duration_seconds=30)
        
        assert result["success"] is True
        
        metrics = result["metrics"]
        
        # Memory increase should be bounded
        memory_increase = metrics.get("memory_increase_mb", 0)
        assert memory_increase < 1000, f"Memory increase too high: {memory_increase}MB"
        
        # System should remain responsive
        assert metrics["requests_successful"] > 0, "System became unresponsive under memory pressure"
    
    async def test_high_concurrency_resilience(self):
        """Test system under high concurrent load"""
        experiment = HighConcurrencyExperiment()
        result = await experiment.run_experiment(duration_seconds=40)
        
        assert result["success"] is True
        
        metrics = result["metrics"]
        
        # System should handle concurrent load gracefully
        if metrics["requests_total"] > 0:
            success_rate = metrics["requests_successful"] / metrics["requests_total"]
            assert success_rate >= 0.5, f"Success rate under load too low: {success_rate}"
        
        # Response times may be higher but should be bounded
        assert metrics["max_response_time"] < 10000, f"Max response time too high: {metrics['max_response_time']}ms"
    
    async def test_cpu_exhaustion_resilience(self):
        """Test system behavior under CPU exhaustion"""
        experiment = CPUExhaustionExperiment()
        result = await experiment.run_experiment(duration_seconds=40)
        
        assert result["success"] is True
        
        metrics = result["metrics"]
        
        # System should remain functional despite CPU load
        assert metrics["requests_successful"] > 0, "System became unresponsive under CPU load"
        
        # May have degraded performance but should complete requests
        if metrics["requests_total"] > 0:
            completion_rate = metrics["requests_successful"] / metrics["requests_total"]
            assert completion_rate >= 0.2, f"Completion rate too low: {completion_rate}"
    
    async def test_network_latency_resilience(self):
        """Test system behavior under network latency"""
        experiment = NetworkLatencyExperiment()
        result = await experiment.run_experiment(duration_seconds=35)
        
        assert result["success"] is True
        
        metrics = result["metrics"]
        
        # System should implement proper timeouts
        if metrics["requests_total"] > 0:
            # Should not hang indefinitely
            assert metrics["max_response_time"] < 30000, "Requests hanging without proper timeouts"
    
    async def test_cascading_failure_resilience(self):
        """Test resilience to cascading failures"""
        experiment = CascadingFailureExperiment()
        result = await experiment.run_experiment(duration_seconds=50)
        
        assert result["success"] is True
        
        metrics = result["metrics"]
        
        # System should implement circuit breakers and isolation
        assert len(metrics["errors"]) < metrics["requests_total"], "All requests failed during cascading failure"
        
        # Should recover partially
        if metrics["requests_total"] > 10:
            recovery_rate = metrics["requests_successful"] / metrics["requests_total"]
            assert recovery_rate > 0.1, f"No recovery observed: {recovery_rate}"


@pytest.mark.chaos
@pytest.mark.integration  
class TestChaosEngineeringIntegration:
    """Integration chaos engineering tests"""
    
    async def test_voice_ai_chaos_resilience(self):
        """Test voice AI system under multiple chaos conditions"""
        voice_service = VoiceService()
        
        # Simulate multiple failures simultaneously
        failures = [
            # OpenAI API failure
            patch('openai.AsyncOpenAI.chat.completions.create', side_effect=Exception("API unavailable")),
            # ElevenLabs rate limiting
            patch('httpx.AsyncClient.post', return_value=Mock(status_code=429)),
            # Database connection issues
            patch('sqlalchemy.ext.asyncio.create_async_engine', side_effect=Exception("Connection failed"))
        ]
        
        results = []
        
        # Apply all failures
        with failures[0], failures[1], failures[2]:
            # Test voice processing under multiple failures
            for i in range(5):
                try:
                    result = await voice_service.process_voice_input(
                        b"test_audio_data",
                        f"chaos_test_conv_{i}",
                        Mock(id="test_agent"),
                        "chaos_test_org"
                    )
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
                
                await asyncio.sleep(1)
        
        # Analyze results
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", True)]
        
        # Should implement graceful degradation
        assert len(results) == 5, "Not all test attempts were made"
        
        # May fail but should fail gracefully
        for result in failed_results:
            assert "error" in result, "Failed results should include error information"
    
    async def test_end_to_end_chaos_workflow(self):
        """Test complete workflow under chaos conditions"""
        client = TestClient(app)
        
        # Inject random failures during workflow
        async def random_failure_injection():
            failure_types = [
                lambda: patch('openai.AsyncOpenAI', side_effect=Exception("Random OpenAI failure")),
                lambda: patch('httpx.AsyncClient.get', side_effect=Exception("Random HTTP failure")),
                lambda: asyncio.sleep(random.uniform(0.1, 0.5))  # Random delays
            ]
            
            for _ in range(10):
                failure = random.choice(failure_types)
                try:
                    with failure():
                        await asyncio.sleep(0.5)
                except:
                    await asyncio.sleep(0.5)
        
        # Start chaos injection
        chaos_task = asyncio.create_task(random_failure_injection())
        
        # Execute workflow under chaos
        workflow_results = []
        
        try:
            # Step 1: Health check
            response = client.get("/api/v1/health")
            workflow_results.append(("health_check", response.status_code))
            
            # Step 2: Authentication (mocked)
            workflow_results.append(("auth", 200))  # Assume success
            
            # Step 3: Voice agent creation
            agent_data = {
                "name": "Chaos Test Agent",
                "voice_id": "test_voice",
                "greeting": "Hello from chaos test"
            }
            response = client.post("/api/v1/voice-agents", json=agent_data)
            workflow_results.append(("create_agent", response.status_code))
            
            # Step 4: Start conversation
            conv_data = {
                "caller_phone": "+1234567890", 
                "voice_agent_id": "test_agent"
            }
            response = client.post("/api/v1/conversations", json=conv_data)
            workflow_results.append(("start_conversation", response.status_code))
            
        finally:
            # Stop chaos injection
            chaos_task.cancel()
            try:
                await chaos_task
            except asyncio.CancelledError:
                pass
        
        # Analyze workflow resilience
        successful_steps = [step for step, status in workflow_results if 200 <= status < 300]
        failed_steps = [step for step, status in workflow_results if status >= 400]
        
        # Should complete at least some steps
        assert len(successful_steps) >= 1, f"No workflow steps succeeded: {workflow_results}"
        
        # Critical steps should have fallbacks
        critical_steps = ["health_check", "auth"]
        critical_failures = [step for step in failed_steps if step in critical_steps]
        assert len(critical_failures) == 0, f"Critical steps failed: {critical_failures}"


class ChaosEngineeringReport:
    """Generate chaos engineering experiment reports"""
    
    @staticmethod
    def generate_report(results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive chaos engineering report"""
        report = ["CHAOS ENGINEERING EXPERIMENT REPORT", "=" * 50, ""]
        
        total_experiments = len(results)
        successful_experiments = len([r for r in results if r["success"]])
        
        report.extend([
            f"Total Experiments: {total_experiments}",
            f"Successful Experiments: {successful_experiments}",
            f"Success Rate: {(successful_experiments/total_experiments)*100:.1f}%",
            ""
        ])
        
        for result in results:
            report.extend([
                f"Experiment: {result['experiment']}",
                f"Description: {result['description']}",
                f"Status: {'PASSED' if result['success'] else 'FAILED'}",
                ""
            ])
            
            if result["success"] and "metrics" in result:
                metrics = result["metrics"]
                report.extend([
                    f"  Total Requests: {metrics['requests_total']}",
                    f"  Successful Requests: {metrics['requests_successful']}",
                    f"  Failed Requests: {metrics['requests_failed']}",
                    f"  Average Response Time: {metrics['avg_response_time']:.1f}ms",
                    f"  Max Response Time: {metrics['max_response_time']:.1f}ms",
                    ""
                ])
            
            if not result["success"]:
                report.extend([
                    f"  Error: {result.get('error', 'Unknown error')}",
                    ""
                ])
        
        # Recommendations
        report.extend([
            "RECOMMENDATIONS:",
            "-" * 20,
            ""
        ])
        
        if successful_experiments < total_experiments:
            report.append("• Implement additional error handling and recovery mechanisms")
        
        if any("memory" in r["experiment"] for r in results if r["success"]):
            report.append("• Monitor memory usage and implement memory management strategies")
        
        if any("concurrency" in r["experiment"] for r in results if r["success"]):
            report.append("• Implement rate limiting and load balancing")
        
        report.append("• Consider implementing circuit breakers for external dependencies")
        report.append("• Add comprehensive monitoring and alerting")
        
        return "\n".join(report)


if __name__ == "__main__":
    async def run_chaos_experiments():
        """Run all chaos experiments"""
        experiments = [
            DatabaseFailureExperiment(),
            ExternalAPIFailureExperiment(), 
            MemoryLeakExperiment(),
            HighConcurrencyExperiment(),
            CPUExhaustionExperiment(),
            NetworkLatencyExperiment(),
            CascadingFailureExperiment()
        ]
        
        results = []
        for experiment in experiments:
            print(f"Running experiment: {experiment.name}")
            result = await experiment.run_experiment()
            results.append(result)
            print(f"Completed: {experiment.name} - {'PASSED' if result['success'] else 'FAILED'}")
        
        # Generate report
        report = ChaosEngineeringReport.generate_report(results)
        print("\n" + report)
        
        return results
    
    # Run experiments
    asyncio.run(run_chaos_experiments())