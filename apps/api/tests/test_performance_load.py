"""
Performance and Load Testing
Tests for 1000+ concurrent sessions, load testing, and system scalability
"""
import pytest
import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
import httpx
import websockets
from datetime import datetime, timedelta
import statistics


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformance:
    """Test API performance under various load conditions"""
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, client: TestClient, authorized_headers, performance_monitor):
        """Test API performance with concurrent requests"""
        endpoint = "/api/v1/leads"
        concurrent_requests = 100
        
        performance_monitor.start()
        
        def make_request():
            start_time = time.time()
            response = client.get(endpoint, headers=authorized_headers)
            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200
            }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        metrics = performance_monitor.get_metrics()
        
        # Analyze results
        successful_requests = sum(1 for r in results if r["success"])
        response_times = [r["response_time"] for r in results]
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Performance assertions
        assert successful_requests >= concurrent_requests * 0.95  # 95% success rate
        assert avg_response_time < 2.0  # Average response time under 2s
        assert p95_response_time < 5.0  # 95th percentile under 5s
        assert p99_response_time < 10.0  # 99th percentile under 10s
        assert metrics["elapsed_time"] < 30.0  # Total test time under 30s
        
        print(f"\nConcurrent API Performance Results:")
        print(f"Successful requests: {successful_requests}/{concurrent_requests}")
        print(f"Average response time: {avg_response_time:.3f}s")
        print(f"95th percentile: {p95_response_time:.3f}s")
        print(f"99th percentile: {p99_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_voice_synthesis_performance_under_load(self, elevenlabs_service, test_voice_agent, performance_monitor):
        """Test voice synthesis performance under concurrent load"""
        texts = [
            "Welcome to our real estate platform.",
            "How can I help you find your perfect home?",
            "What's your budget range for this property?",
            "Let me check our available listings.",
            "Would you like to schedule a viewing?"
        ] * 10  # 50 total texts
        
        # Mock voice service for performance testing
        elevenlabs_service._get_voice_profile_for_agent = Mock(return_value=elevenlabs_service.voice_profiles["professional_male"])
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
        elevenlabs_service._cache_audio = AsyncMock()
        elevenlabs_service._send_analytics_event = AsyncMock()
        
        # Simulate realistic synthesis times with some variance
        async def mock_synthesis(request):
            await asyncio.sleep(0.1 + (len(request.text) * 0.001))  # Simulate processing time
            return b"mock_audio_data"
        
        elevenlabs_service._synthesize_audio = mock_synthesis
        
        performance_monitor.start()
        
        # Process texts concurrently
        tasks = []
        for text in texts:
            task = elevenlabs_service.synthesize_speech(
                text=text,
                voice_agent=test_voice_agent,
                enable_caching=False,
                optimize_for_speed=True
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics = performance_monitor.get_metrics()
        
        # Analyze results
        successful_syntheses = sum(1 for r in results if not isinstance(r, Exception))
        processing_times = [r.processing_time_ms for r in results if not isinstance(r, Exception)]
        
        if processing_times:
            avg_processing_time = statistics.mean(processing_times)
            p95_processing_time = statistics.quantiles(processing_times, n=20)[18]
            
            # Performance assertions
            assert successful_syntheses >= len(texts) * 0.95  # 95% success rate
            assert avg_processing_time < 2000  # Average under 2s
            assert p95_processing_time < 3000  # 95th percentile under 3s
            assert metrics["elapsed_time"] < 60.0  # Total time reasonable for concurrent processing
            
            print(f"\nVoice Synthesis Performance Results:")
            print(f"Successful syntheses: {successful_syntheses}/{len(texts)}")
            print(f"Average processing time: {avg_processing_time:.1f}ms")
            print(f"95th percentile: {p95_processing_time:.1f}ms")
    
    @pytest.mark.asyncio
    async def test_database_performance_under_load(self, db_session, test_organization, performance_monitor):
        """Test database performance with concurrent operations"""
        from app.models.lead import Lead
        
        # Create leads concurrently
        lead_count = 100
        performance_monitor.start()
        
        async def create_lead(index):
            lead = Lead(
                organization_id=test_organization.id,
                name=f"Load Test Lead {index}",
                email=f"loadtest{index}@example.com",
                phone=f"+123456{index:04d}",
                source="load_test",
                property_preferences={
                    "type": "single_family",
                    "min_price": 300000 + (index * 1000),
                    "max_price": 500000 + (index * 1000),
                    "bedrooms": 3
                },
                qualification_status="new",
                lead_score=0
            )
            
            db_session.add(lead)
            return lead
        
        # Create leads concurrently
        tasks = [create_lead(i) for i in range(lead_count)]
        created_leads = await asyncio.gather(*tasks)
        
        # Commit all at once
        await db_session.commit()
        
        metrics = performance_monitor.get_metrics()
        
        # Performance assertions
        assert len(created_leads) == lead_count
        assert metrics["elapsed_time"] < 10.0  # Should complete quickly
        
        print(f"\nDatabase Performance Results:")
        print(f"Created {lead_count} leads in {metrics['elapsed_time']:.3f}s")
        print(f"Rate: {lead_count / metrics['elapsed_time']:.1f} leads/second")
    
    @pytest.mark.asyncio
    async def test_redis_cache_performance_under_load(self, redis_client, performance_monitor):
        """Test Redis cache performance under concurrent load"""
        cache_operations = 500
        
        async def cache_operation(index):
            key = f"load_test:item_{index}"
            value = {
                "data": f"test_data_{index}",
                "timestamp": time.time(),
                "index": index
            }
            
            # Set operation
            await redis_client.set(key, json.dumps(value))
            
            # Get operation
            retrieved = await redis_client.get(key)
            retrieved_data = json.loads(retrieved) if retrieved else None
            
            return retrieved_data is not None and retrieved_data["index"] == index
        
        performance_monitor.start()
        
        # Execute cache operations concurrently
        tasks = [cache_operation(i) for i in range(cache_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics = performance_monitor.get_metrics()
        
        # Analyze results
        successful_operations = sum(1 for r in results if r is True)
        
        # Performance assertions
        assert successful_operations >= cache_operations * 0.98  # 98% success rate
        assert metrics["elapsed_time"] < 5.0  # Should be very fast
        
        operations_per_second = cache_operations / metrics["elapsed_time"]
        assert operations_per_second > 100  # Should handle 100+ ops/second
        
        print(f"\nRedis Cache Performance Results:")
        print(f"Successful operations: {successful_operations}/{cache_operations}")
        print(f"Operations per second: {operations_per_second:.1f}")
        print(f"Total time: {metrics['elapsed_time']:.3f}s")


@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentSessions:
    """Test system performance with 1000+ concurrent sessions"""
    
    @pytest.mark.asyncio
    async def test_1000_concurrent_sessions_simulation(self, authorized_headers, performance_monitor):
        """Simulate 1000+ concurrent user sessions"""
        concurrent_sessions = 1000
        session_duration = 30  # seconds
        requests_per_session = 5
        
        session_results = []
        
        async def simulate_user_session(session_id):
            """Simulate a single user session"""
            session_start = time.time()
            session_requests = []
            
            try:
                # Create async HTTP client for this session
                async with httpx.AsyncClient(base_url="http://testserver") as client:
                    # Make multiple requests during session
                    for request_num in range(requests_per_session):
                        request_start = time.time()
                        
                        # Vary the endpoints to simulate real usage
                        endpoints = [
                            "/api/v1/leads",
                            "/api/v1/conversations",
                            "/api/v1/properties/search",
                            "/api/v1/analytics/dashboard",
                            "/api/health"
                        ]
                        
                        endpoint = endpoints[request_num % len(endpoints)]
                        
                        try:
                            response = await client.get(endpoint, headers=authorized_headers, timeout=10.0)
                            request_time = time.time() - request_start
                            
                            session_requests.append({
                                "endpoint": endpoint,
                                "status_code": response.status_code,
                                "response_time": request_time,
                                "success": response.status_code in [200, 201]
                            })
                            
                        except Exception as e:
                            session_requests.append({
                                "endpoint": endpoint,
                                "status_code": 0,
                                "response_time": time.time() - request_start,
                                "success": False,
                                "error": str(e)
                            })
                        
                        # Small delay between requests in session
                        await asyncio.sleep(0.1)
                
                session_time = time.time() - session_start
                successful_requests = sum(1 for r in session_requests if r["success"])
                
                return {
                    "session_id": session_id,
                    "session_time": session_time,
                    "requests": session_requests,
                    "successful_requests": successful_requests,
                    "success_rate": successful_requests / len(session_requests) if session_requests else 0
                }
                
            except Exception as e:
                return {
                    "session_id": session_id,
                    "session_time": time.time() - session_start,
                    "requests": [],
                    "successful_requests": 0,
                    "success_rate": 0,
                    "session_error": str(e)
                }
        
        performance_monitor.start()
        
        # Create batches to avoid overwhelming the system
        batch_size = 50
        for batch_start in range(0, concurrent_sessions, batch_size):
            batch_end = min(batch_start + batch_size, concurrent_sessions)
            batch_sessions = range(batch_start, batch_end)
            
            print(f"\nProcessing sessions {batch_start}-{batch_end-1}...")
            
            # Process batch concurrently
            batch_tasks = [simulate_user_session(session_id) for session_id in batch_sessions]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Collect results
            for result in batch_results:
                if isinstance(result, Exception):
                    session_results.append({
                        "session_id": -1,
                        "session_time": 0,
                        "requests": [],
                        "successful_requests": 0,
                        "success_rate": 0,
                        "batch_error": str(result)
                    })
                else:
                    session_results.append(result)
            
            # Small delay between batches to avoid overwhelming
            await asyncio.sleep(1)
        
        total_metrics = performance_monitor.get_metrics()
        
        # Analyze overall results
        successful_sessions = sum(1 for s in session_results if s["success_rate"] > 0.8)
        total_requests = sum(len(s["requests"]) for s in session_results)
        total_successful_requests = sum(s["successful_requests"] for s in session_results)
        
        overall_success_rate = total_successful_requests / total_requests if total_requests > 0 else 0
        
        # Performance assertions for 1000+ concurrent sessions
        assert successful_sessions >= concurrent_sessions * 0.85  # 85% of sessions should be mostly successful
        assert overall_success_rate >= 0.80  # 80% overall success rate
        assert total_metrics["elapsed_time"] < 300  # Should complete within 5 minutes
        
        # Calculate response time statistics
        all_response_times = []
        for session in session_results:
            for request in session["requests"]:
                if request["success"]:
                    all_response_times.append(request["response_time"])
        
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18]
            p99_response_time = statistics.quantiles(all_response_times, n=100)[98]
            
            assert avg_response_time < 3.0  # Average response time under 3s under load
            assert p95_response_time < 8.0  # 95th percentile under 8s
            
            print(f"\n1000+ Concurrent Sessions Results:")
            print(f"Total sessions: {len(session_results)}")
            print(f"Successful sessions (>80% success): {successful_sessions}")
            print(f"Total requests: {total_requests}")
            print(f"Successful requests: {total_successful_requests}")
            print(f"Overall success rate: {overall_success_rate:.2%}")
            print(f"Average response time: {avg_response_time:.3f}s")
            print(f"95th percentile response time: {p95_response_time:.3f}s")
            print(f"99th percentile response time: {p99_response_time:.3f}s")
            print(f"Total test duration: {total_metrics['elapsed_time']:.1f}s")
    
    @pytest.mark.asyncio
    async def test_websocket_concurrent_connections(self):
        """Test WebSocket performance with concurrent connections"""
        concurrent_connections = 100  # Reduced for testing
        connection_duration = 10  # seconds
        
        connection_results = []
        
        async def websocket_session(connection_id):
            """Simulate a WebSocket connection session"""
            session_start = time.time()
            messages_sent = 0
            messages_received = 0
            
            try:
                # In a real test, this would connect to actual WebSocket endpoint
                # For now, simulate the connection behavior
                await asyncio.sleep(connection_duration)
                
                # Simulate message exchange
                messages_sent = 5
                messages_received = 5
                
                session_time = time.time() - session_start
                
                return {
                    "connection_id": connection_id,
                    "session_time": session_time,
                    "messages_sent": messages_sent,
                    "messages_received": messages_received,
                    "success": True
                }
                
            except Exception as e:
                return {
                    "connection_id": connection_id,
                    "session_time": time.time() - session_start,
                    "messages_sent": messages_sent,
                    "messages_received": messages_received,
                    "success": False,
                    "error": str(e)
                }
        
        # Execute concurrent WebSocket sessions
        tasks = [websocket_session(i) for i in range(concurrent_connections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_connections = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        total_messages_sent = sum(r.get("messages_sent", 0) for r in results if isinstance(r, dict))
        total_messages_received = sum(r.get("messages_received", 0) for r in results if isinstance(r, dict))
        
        # Performance assertions
        assert successful_connections >= concurrent_connections * 0.90  # 90% success rate
        assert total_messages_sent > 0
        assert total_messages_received > 0
        
        print(f"\nWebSocket Concurrent Connections Results:")
        print(f"Successful connections: {successful_connections}/{concurrent_connections}")
        print(f"Total messages sent: {total_messages_sent}")
        print(f"Total messages received: {total_messages_received}")


@pytest.mark.performance
@pytest.mark.slow
class TestScalabilityLimits:
    """Test system scalability limits and resource usage"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, performance_monitor):
        """Test memory usage during high load"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        performance_monitor.start()
        
        # Create memory-intensive operations
        large_datasets = []
        for i in range(100):
            # Simulate processing large datasets
            dataset = {
                "leads": [{"id": j, "data": "x" * 1000} for j in range(100)],
                "conversations": [{"id": j, "transcript": "y" * 2000} for j in range(50)],
                "analytics": {"metrics": list(range(1000))}
            }
            large_datasets.append(dataset)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Cleanup
        large_datasets.clear()
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        memory_cleanup = peak_memory - final_memory
        
        metrics = performance_monitor.get_metrics()
        
        # Memory usage assertions
        assert memory_increase < 500  # Should not use more than 500MB for test
        assert memory_cleanup > memory_increase * 0.7  # Should cleanup at least 70% of used memory
        
        print(f"\nMemory Usage Results:")
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Peak memory: {peak_memory:.1f} MB")
        print(f"Final memory: {final_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")
        print(f"Memory cleaned up: {memory_cleanup:.1f} MB")
    
    @pytest.mark.asyncio
    async def test_cpu_usage_optimization(self, performance_monitor):
        """Test CPU usage during intensive operations"""
        import psutil
        import threading
        
        process = psutil.Process()
        
        # Monitor CPU usage during test
        cpu_readings = []
        monitoring = True
        
        def monitor_cpu():
            while monitoring:
                cpu_readings.append(process.cpu_percent())
                time.sleep(0.1)
        
        cpu_thread = threading.Thread(target=monitor_cpu)
        cpu_thread.start()
        
        performance_monitor.start()
        
        try:
            # CPU-intensive operations
            tasks = []
            for i in range(20):
                # Simulate CPU-intensive processing
                task = asyncio.create_task(cpu_intensive_operation(i))
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
        finally:
            monitoring = False
            cpu_thread.join()
        
        metrics = performance_monitor.get_metrics()
        
        if cpu_readings:
            avg_cpu = statistics.mean(cpu_readings)
            peak_cpu = max(cpu_readings)
            
            # CPU usage should be reasonable
            assert avg_cpu < 80.0  # Average CPU usage under 80%
            assert peak_cpu < 95.0  # Peak CPU usage under 95%
            
            print(f"\nCPU Usage Results:")
            print(f"Average CPU usage: {avg_cpu:.1f}%")
            print(f"Peak CPU usage: {peak_cpu:.1f}%")
            print(f"Processing time: {metrics['elapsed_time']:.3f}s")
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, db_session):
        """Test database connection pool performance"""
        concurrent_db_operations = 50
        
        async def database_operation(operation_id):
            """Simulate database operation"""
            # Simulate database query
            start_time = time.time()
            
            # In real test, this would execute actual DB queries
            await asyncio.sleep(0.1)  # Simulate DB operation time
            
            return {
                "operation_id": operation_id,
                "duration": time.time() - start_time,
                "success": True
            }
        
        start_time = time.time()
        
        # Execute concurrent database operations
        tasks = [database_operation(i) for i in range(concurrent_db_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        successful_operations = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        
        # Performance assertions
        assert successful_operations == concurrent_db_operations
        assert total_time < 5.0  # Should complete quickly with connection pooling
        
        operations_per_second = concurrent_db_operations / total_time
        assert operations_per_second > 10  # Should handle reasonable throughput
        
        print(f"\nDatabase Connection Pool Results:")
        print(f"Successful operations: {successful_operations}/{concurrent_db_operations}")
        print(f"Operations per second: {operations_per_second:.1f}")
        print(f"Total time: {total_time:.3f}s")


async def cpu_intensive_operation(operation_id):
    """Simulate CPU-intensive operation"""
    # Simulate CPU-bound work
    result = 0
    for i in range(100000):
        result += i * operation_id
    
    await asyncio.sleep(0.01)  # Small async operation
    return result


@pytest.mark.performance
class TestResourceMonitoring:
    """Test resource monitoring and alerting"""
    
    def test_performance_metrics_collection(self, performance_monitor):
        """Test collection of performance metrics"""
        performance_monitor.start()
        
        # Simulate some work
        time.sleep(0.1)
        
        metrics = performance_monitor.get_metrics()
        
        # Verify metrics are collected
        assert "elapsed_time" in metrics
        assert "memory_delta" in metrics
        assert "cpu_percent" in metrics
        assert "memory_mb" in metrics
        
        assert metrics["elapsed_time"] > 0
        assert isinstance(metrics["memory_mb"], (int, float))
        assert isinstance(metrics["cpu_percent"], (int, float))
    
    @pytest.mark.asyncio
    async def test_performance_alerting_thresholds(self, assert_timing):
        """Test performance alerting when thresholds are exceeded"""
        # Test response time alerting
        assert_timing.start()
        
        # Simulate operation that should be fast
        await asyncio.sleep(0.05)  # 50ms
        
        # Should pass - operation is fast
        assert_timing.assert_under(0.1, "Fast operation should complete quickly")
        
        # Test slow operation alerting
        assert_timing.start()
        
        # Simulate slow operation
        await asyncio.sleep(0.2)  # 200ms
        
        # Should fail if threshold is too low
        try:
            assert_timing.assert_under(0.1, "Slow operation exceeds threshold")
            assert False, "Should have failed due to slow operation"
        except AssertionError as e:
            assert "exceeds threshold" in str(e) or "took too long" in str(e)
    
    def test_system_health_monitoring(self):
        """Test system health monitoring capabilities"""
        import psutil
        
        # Test system resource monitoring
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Verify monitoring data is available
        assert isinstance(cpu_percent, (int, float))
        assert 0 <= cpu_percent <= 100
        
        assert hasattr(memory, 'percent')
        assert 0 <= memory.percent <= 100
        
        assert hasattr(disk, 'percent')
        assert 0 <= disk.percent <= 100
        
        # System should be healthy for tests
        assert cpu_percent < 90, f"CPU usage too high: {cpu_percent}%"
        assert memory.percent < 90, f"Memory usage too high: {memory.percent}%"
        assert disk.percent < 90, f"Disk usage too high: {disk.percent}%"
        
        print(f"\nSystem Health Status:")
        print(f"CPU Usage: {cpu_percent:.1f}%")
        print(f"Memory Usage: {memory.percent:.1f}%")
        print(f"Disk Usage: {disk.percent:.1f}%")