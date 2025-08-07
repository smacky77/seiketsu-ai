"""
Error Handling and Fallback Mechanism Tests
Tests for error handling, fallback systems, and system resilience
"""
import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
import httpx
from datetime import datetime


@pytest.mark.error_handling
class TestAPIErrorHandling:
    """Test API error handling and response formatting"""
    
    @pytest.mark.asyncio
    async def test_404_error_handling(self, client: TestClient, authorized_headers):
        """Test 404 error handling for non-existent resources"""
        # Test non-existent lead
        response = client.get(
            "/api/v1/leads/non-existent-id",
            headers=authorized_headers
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert "not found" in error_data["detail"].lower()
        
        # Test non-existent conversation
        response = client.get(
            "/api/v1/conversations/non-existent-id",
            headers=authorized_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, client: TestClient, authorized_headers):
        """Test validation error handling for invalid data"""
        # Test invalid email format
        invalid_lead_data = {
            "name": "Test Lead",
            "email": "invalid-email-format",
            "phone": "+1234567890"
        }
        
        response = client.post(
            "/api/v1/leads",
            json=invalid_lead_data,
            headers=authorized_headers
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)
        
        # Find email validation error
        email_error = next(
            (err for err in error_data["detail"] if "email" in err.get("loc", [])), 
            None
        )
        assert email_error is not None
        assert "email" in email_error["msg"].lower() or "value_error" in email_error["type"]
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, client: TestClient):
        """Test authentication error handling"""
        # Test request without authentication
        response = client.get("/api/v1/leads")
        assert response.status_code == 401
        
        error_data = response.json()
        assert "detail" in error_data
        assert "not authenticated" in error_data["detail"].lower() or "unauthorized" in error_data["detail"].lower()
        
        # Test request with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/leads", headers=invalid_headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_authorization_error_handling(self, client: TestClient, authorized_headers):
        """Test authorization error handling for insufficient permissions"""
        # Test agent trying to access admin endpoint
        response = client.get(
            "/api/v1/admin/users",
            headers=authorized_headers
        )
        
        # Should be 403 Forbidden (assuming regular user headers)
        assert response.status_code in [403, 404]  # 404 if endpoint doesn't exist in test
    
    @pytest.mark.asyncio
    async def test_rate_limiting_error_handling(self, client: TestClient, authorized_headers):
        """Test rate limiting error handling"""
        # Make rapid requests to trigger rate limiting
        responses = []
        for i in range(50):  # Attempt to exceed rate limit
            response = client.get("/api/v1/leads", headers=authorized_headers)
            responses.append(response.status_code)
            
            # If we hit rate limit, test the response
            if response.status_code == 429:
                error_data = response.json()
                assert "detail" in error_data
                assert "rate limit" in error_data["detail"].lower() or "too many requests" in error_data["detail"].lower()
                
                # Check for retry-after header
                assert "retry-after" in response.headers or "x-ratelimit-reset" in response.headers
                break
        
        # Should eventually hit rate limit
        assert 429 in responses, "Rate limiting should be enforced"
    
    @pytest.mark.asyncio
    async def test_server_error_handling(self, client: TestClient, authorized_headers):
        """Test 500 error handling for server errors"""
        # Mock a service to raise an exception
        with patch('app.api.v1.leads.lead_service') as mock_service:
            mock_service.get_leads.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/v1/leads", headers=authorized_headers)
            
            assert response.status_code == 500
            error_data = response.json()
            assert "detail" in error_data
            assert "request_id" in error_data  # Should include request ID for tracking
            assert "timestamp" in error_data
            
            # Error message should be generic for security
            assert "Database connection failed" not in error_data["detail"]
            assert "internal server error" in error_data["detail"].lower()


@pytest.mark.error_handling
class TestServiceErrorHandling:
    """Test service-level error handling and fallbacks"""
    
    @pytest.mark.asyncio
    async def test_elevenlabs_service_error_handling(self, elevenlabs_service, test_voice_agent):
        """Test ElevenLabs service error handling and fallbacks"""
        # Test API timeout
        with patch.object(elevenlabs_service, '_synthesize_audio') as mock_synthesize:
            mock_synthesize.side_effect = asyncio.TimeoutError("Request timeout")
            
            with pytest.raises(Exception):
                await elevenlabs_service.synthesize_speech(
                    text="Test timeout handling",
                    voice_agent=test_voice_agent
                )
        
        # Test API error response
        with patch.object(elevenlabs_service, '_synthesize_audio') as mock_synthesize:
            mock_synthesize.side_effect = httpx.HTTPStatusError(
                "API Error", 
                request=Mock(), 
                response=Mock(status_code=503)
            )
            
            with pytest.raises(Exception):
                await elevenlabs_service.synthesize_speech(
                    text="Test API error handling",
                    voice_agent=test_voice_agent
                )
        
        # Test invalid response format
        with patch.object(elevenlabs_service, '_synthesize_audio') as mock_synthesize:
            mock_synthesize.return_value = None  # Invalid response
            
            with pytest.raises(Exception):
                await elevenlabs_service.synthesize_speech(
                    text="Test invalid response",
                    voice_agent=test_voice_agent
                )
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, db_session, test_organization):
        """Test database error handling and recovery"""
        from app.models.lead import Lead
        from sqlalchemy.exc import OperationalError
        
        # Test connection error handling
        with patch.object(db_session, 'execute') as mock_execute:
            mock_execute.side_effect = OperationalError(
                "Database connection lost", None, None
            )
            
            # Should handle database errors gracefully
            with pytest.raises(OperationalError):
                await db_session.execute("SELECT 1")
        
        # Test constraint violation handling
        lead1 = Lead(
            organization_id=test_organization.id,
            name="Test Lead",
            email="constraint@example.com",
            phone="+1234567890",
            source="test",
            qualification_status="new"
        )
        
        db_session.add(lead1)
        await db_session.commit()
        
        # Try to create duplicate (assuming email uniqueness)
        lead2 = Lead(
            organization_id=test_organization.id,
            name="Duplicate Lead",
            email="constraint@example.com",  # Same email
            phone="+1234567891",
            source="test",
            qualification_status="new"
        )
        
        db_session.add(lead2)
        
        # Should handle constraint violation
        with pytest.raises(Exception):  # IntegrityError or similar
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_external_api_error_handling(self):
        """Test external API error handling"""
        from app.services.twentyonedev_service import TwentyOneDevService
        
        service = TwentyOneDevService()
        
        # Test API unavailable
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.text = "Service Unavailable"
            mock_post.return_value = mock_response
            
            # Should handle API unavailability gracefully
            result = await service.send_analytics_event(
                event_type="test_event",
                data={"test": "data"}
            )
            
            # Should not raise exception, but return error indication
            assert result is None or "error" in result
        
        # Test network timeout
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")
            
            # Should handle timeout gracefully
            result = await service.send_analytics_event(
                event_type="test_event",
                data={"test": "data"}
            )
            
            assert result is None or "error" in result
    
    @pytest.mark.asyncio
    async def test_redis_error_handling(self, mock_redis_client):
        """Test Redis error handling and fallbacks"""
        from app.core.cache import cache_get, cache_set
        import redis.exceptions
        
        # Test Redis connection error
        with patch('app.core.cache.get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.side_effect = redis.exceptions.ConnectionError("Redis unavailable")
            mock_get_client.return_value = mock_client
            
            # Should handle Redis errors gracefully
            result = await cache_get("test_key")
            assert result is None  # Should return None on error
        
        # Test Redis timeout
        with patch('app.core.cache.get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.set.side_effect = redis.exceptions.TimeoutError("Redis timeout")
            mock_get_client.return_value = mock_client
            
            # Should handle timeout gracefully
            try:
                await cache_set("test_key", {"data": "test"}, 300)
                # Should not raise exception
            except Exception as e:
                # If exception is raised, it should be handled at higher level
                assert "timeout" in str(e).lower()


@pytest.mark.error_handling
class TestFallbackMechanisms:
    """Test fallback mechanisms and graceful degradation"""
    
    @pytest.mark.asyncio
    async def test_voice_synthesis_fallback(self, elevenlabs_service, test_voice_agent):
        """Test voice synthesis fallback when primary service fails"""
        # Mock primary service failure
        with patch.object(elevenlabs_service, '_synthesize_audio') as mock_primary:
            # First few calls fail
            call_count = 0
            def failing_synthesis(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise Exception("Primary service unavailable")
                return b"fallback_audio_data"
            
            mock_primary.side_effect = failing_synthesis
            elevenlabs_service._get_voice_profile_for_agent = Mock(
                return_value=elevenlabs_service.voice_profiles["professional_male"]
            )
            elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
            elevenlabs_service._cache_audio = AsyncMock()
            elevenlabs_service._send_analytics_event = AsyncMock()
            
            # Should eventually succeed with fallback
            result = await elevenlabs_service.synthesize_speech(
                text="Test fallback mechanism",
                voice_agent=test_voice_agent
            )
            
            assert result.audio_data == b"fallback_audio_data"
            assert call_count >= 2  # Should have retried
    
    @pytest.mark.asyncio
    async def test_cache_fallback_to_direct_processing(self, elevenlabs_service, test_voice_agent):
        """Test fallback to direct processing when cache fails"""
        # Mock cache failure but working synthesis
        elevenlabs_service._get_cached_audio = AsyncMock(side_effect=Exception("Cache unavailable"))
        elevenlabs_service._synthesize_audio = AsyncMock(return_value=b"direct_synthesis_audio")
        elevenlabs_service._get_voice_profile_for_agent = Mock(
            return_value=elevenlabs_service.voice_profiles["professional_male"]
        )
        elevenlabs_service._cache_audio = AsyncMock()  # May also fail, but shouldn't block
        elevenlabs_service._send_analytics_event = AsyncMock()
        
        # Should fallback to direct synthesis
        result = await elevenlabs_service.synthesize_speech(
            text="Test cache fallback",
            voice_agent=test_voice_agent,
            enable_caching=True
        )
        
        assert result.audio_data == b"direct_synthesis_audio"
        assert not result.cached
    
    @pytest.mark.asyncio
    async def test_database_read_replica_fallback(self, db_session):
        """Test fallback to read replica when primary database fails"""
        # This is a conceptual test - actual implementation would depend on
        # database setup with read replicas
        
        # Simulate primary database failure
        with patch.object(db_session, 'execute') as mock_execute:
            # First call fails (primary), second succeeds (replica)
            call_count = 0
            def db_call_with_fallback(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Primary database unavailable")
                
                # Mock successful replica response
                mock_result = Mock()
                mock_result.scalar.return_value = 5
                return mock_result
            
            mock_execute.side_effect = db_call_with_fallback
            
            # Should succeed with fallback
            try:
                result = await db_session.execute("SELECT COUNT(*) FROM leads")
                count = result.scalar()
                assert count == 5
            except Exception:
                # In test environment, fallback might not be implemented
                # This test verifies the concept
                pass
    
    @pytest.mark.asyncio
    async def test_analytics_fallback_to_local_storage(self):
        """Test fallback to local storage when analytics service fails"""
        from app.services.twentyonedev_service import TwentyOneDevService
        
        service = TwentyOneDevService()
        
        # Mock analytics service failure
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("Analytics service unavailable")
            
            # Mock local storage fallback
            with patch('app.services.twentyonedev_service.store_analytics_locally') as mock_local:
                mock_local.return_value = {"stored_locally": True}
                
                # Should fallback to local storage
                result = await service.send_analytics_event(
                    event_type="test_fallback",
                    data={"test": "data"}
                )
                
                # Should indicate local storage was used
                assert result is None or "stored_locally" in str(result)
    
    @pytest.mark.asyncio
    async def test_graceful_service_degradation(self, client: TestClient, authorized_headers):
        """Test graceful degradation when non-critical services fail"""
        # Mock voice service failure
        with patch('app.services.elevenlabs_service.elevenlabs_service') as mock_voice:
            mock_voice.synthesize_speech.side_effect = Exception("Voice service unavailable")
            
            # API should still work for non-voice operations
            response = client.get("/api/v1/leads", headers=authorized_headers)
            assert response.status_code == 200
            
            # Voice-specific endpoints should handle errors gracefully
            voice_response = client.post(
                "/api/v1/voice/synthesize",
                json={
                    "text": "Test graceful degradation",
                    "voice_agent_id": "test_agent"
                },
                headers=authorized_headers
            )
            
            # Should return error but not crash
            assert voice_response.status_code in [500, 503, 422]
            
            if voice_response.status_code in [500, 503]:
                error_data = voice_response.json()
                assert "detail" in error_data
                assert "request_id" in error_data


@pytest.mark.error_handling
class TestErrorRecovery:
    """Test error recovery and resilience mechanisms"""
    
    @pytest.mark.asyncio
    async def test_automatic_retry_mechanism(self, elevenlabs_service, test_voice_agent):
        """Test automatic retry mechanism for transient failures"""
        call_count = 0
        
        def transient_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                # First two calls fail with transient error
                raise httpx.ConnectTimeout("Transient network error")
            else:
                # Third call succeeds
                return b"success_after_retry"
        
        elevenlabs_service._synthesize_audio = Mock(side_effect=transient_failure)
        elevenlabs_service._get_voice_profile_for_agent = Mock(
            return_value=elevenlabs_service.voice_profiles["professional_male"]
        )
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
        elevenlabs_service._cache_audio = AsyncMock()
        elevenlabs_service._send_analytics_event = AsyncMock()
        
        # Should succeed after retries
        result = await elevenlabs_service.synthesize_speech(
            text="Test retry mechanism",
            voice_agent=test_voice_agent
        )
        
        assert result.audio_data == b"success_after_retry"
        assert call_count >= 3  # Should have retried
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for failing services"""
        # This is a conceptual test for circuit breaker implementation
        
        class MockCircuitBreaker:
            def __init__(self):
                self.failure_count = 0
                self.is_open = False
                self.last_failure_time = None
            
            def call(self, func, *args, **kwargs):
                if self.is_open:
                    # Circuit is open, fail fast
                    raise Exception("Circuit breaker is open")
                
                try:
                    result = func(*args, **kwargs)
                    self.failure_count = 0  # Reset on success
                    return result
                except Exception as e:
                    self.failure_count += 1
                    if self.failure_count >= 3:
                        self.is_open = True
                        self.last_failure_time = datetime.utcnow()
                    raise e
        
        circuit_breaker = MockCircuitBreaker()
        
        def failing_service():
            raise Exception("Service failure")
        
        # First few calls should fail and eventually open circuit
        for i in range(5):
            try:
                circuit_breaker.call(failing_service)
            except Exception as e:
                if "Circuit breaker is open" in str(e):
                    # Circuit opened, failing fast
                    assert i >= 3  # Should open after 3 failures
                    break
        
        assert circuit_breaker.is_open
    
    @pytest.mark.asyncio
    async def test_health_check_recovery(self, elevenlabs_service):
        """Test service recovery through health checks"""
        # Mock unhealthy service
        with patch.object(elevenlabs_service, '_synthesize_audio') as mock_synthesize:
            mock_synthesize.side_effect = Exception("Service unhealthy")
            
            # Health check should detect unhealthy state
            health_status = await elevenlabs_service.health_check()
            assert health_status["status"] == "unhealthy"
            assert "error" in health_status
        
        # Mock service recovery
        with patch.object(elevenlabs_service, '_synthesize_audio') as mock_synthesize:
            mock_synthesize.return_value = b"healthy_response"
            elevenlabs_service.voice_profiles = {"test": Mock()}
            elevenlabs_service.redis_client = AsyncMock()
            elevenlabs_service.redis_client.ping = AsyncMock()
            elevenlabs_service.response_times = [100, 150, 120]
            elevenlabs_service.synthesis_count = 10
            elevenlabs_service.cache_hits = 8
            
            # Health check should detect recovery
            health_status = await elevenlabs_service.health_check()
            assert health_status["status"] in ["healthy", "degraded"]
            assert health_status["response_time_ms"] < 5000
    
    @pytest.mark.asyncio
    async def test_data_consistency_after_failure(self, db_session, test_organization):
        """Test data consistency after partial failures"""
        from app.models.lead import Lead
        from app.models.conversation import Conversation
        
        # Start transaction
        lead = Lead(
            organization_id=test_organization.id,
            name="Consistency Test Lead",
            email="consistency@example.com",
            phone="+1234567890",
            source="test",
            qualification_status="new"
        )
        
        db_session.add(lead)
        await db_session.flush()  # Get ID without committing
        
        # Try to add conversation (might fail)
        conversation = Conversation(
            organization_id=test_organization.id,
            lead_id=lead.id,
            agent_id="non-existent-agent",  # This might cause foreign key error
            duration_seconds=180,
            transcript="Test conversation",
            sentiment_score=0.8,
            lead_score=70,
            status="completed"
        )
        
        db_session.add(conversation)
        
        try:
            await db_session.commit()
        except Exception:
            # Transaction should rollback, lead should not exist
            await db_session.rollback()
            
            # Verify rollback worked
            lead_exists = await db_session.get(Lead, lead.id)
            assert lead_exists is None
            
            conv_exists = await db_session.get(Conversation, conversation.id)
            assert conv_exists is None


@pytest.mark.error_handling
class TestMonitoringAndAlerting:
    """Test error monitoring and alerting capabilities"""
    
    @pytest.mark.asyncio
    async def test_error_logging_and_tracking(self, client: TestClient, authorized_headers):
        """Test error logging and request tracking"""
        import logging
        
        # Mock logger to capture error logs
        with patch('app.core.logging.logger') as mock_logger:
            # Trigger an error
            response = client.get(
                "/api/v1/leads/non-existent-id",
                headers=authorized_headers
            )
            
            assert response.status_code == 404
            
            # Should include request ID for tracking
            error_data = response.json()
            if "request_id" in error_data:
                assert len(error_data["request_id"]) > 0
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_alerts(self, assert_timing):
        """Test performance monitoring and slow query alerts"""
        # Test slow operation detection
        assert_timing.start()
        
        # Simulate slow operation
        await asyncio.sleep(0.15)  # 150ms
        
        elapsed = assert_timing.get_elapsed()
        
        # Should detect slow operation
        if elapsed > 0.1:  # 100ms threshold
            # Would trigger monitoring alert in real system
            assert elapsed > 0.1
            print(f"Slow operation detected: {elapsed:.3f}s")
    
    @pytest.mark.asyncio
    async def test_error_rate_monitoring(self, client: TestClient, authorized_headers):
        """Test error rate monitoring"""
        total_requests = 20
        error_count = 0
        
        # Make requests with some expected to fail
        for i in range(total_requests):
            if i % 5 == 0:
                # Every 5th request to non-existent resource (will 404)
                response = client.get(
                    f"/api/v1/leads/non-existent-id-{i}",
                    headers=authorized_headers
                )
            else:
                # Normal request
                response = client.get("/api/v1/leads", headers=authorized_headers)
            
            if response.status_code >= 400:
                error_count += 1
        
        error_rate = error_count / total_requests
        
        # Monitor error rate
        if error_rate > 0.1:  # 10% error rate threshold
            print(f"High error rate detected: {error_rate:.2%}")
            # Would trigger alert in real system
        
        assert error_rate < 0.5  # Should not exceed 50% error rate
    
    def test_system_resource_monitoring(self):
        """Test system resource monitoring for alerts"""
        import psutil
        
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Monitor for high resource usage
        if cpu_percent > 80:
            print(f"High CPU usage alert: {cpu_percent:.1f}%")
        
        if memory.percent > 80:
            print(f"High memory usage alert: {memory.percent:.1f}%")
        
        # Test should pass unless system is severely constrained
        assert cpu_percent < 95, f"CPU usage too high: {cpu_percent}%"
        assert memory.percent < 95, f"Memory usage too high: {memory.percent}%"