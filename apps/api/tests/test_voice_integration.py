"""
Comprehensive ElevenLabs Voice Integration Tests
Tests for voice synthesis, streaming, caching, and performance validation
"""
import pytest
import asyncio
import time
import json
import base64
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
import websockets
import httpx

from app.services.elevenlabs_service import (
    ElevenLabsService, 
    VoiceProfile, 
    SynthesisRequest, 
    AudioFormat, 
    Language,
    VoiceModel
)


@pytest.mark.voice
class TestElevenLabsService:
    """Test ElevenLabs service functionality"""
    
    @pytest.fixture
    async def elevenlabs_service(self, mock_elevenlabs_api, mock_redis_client):
        """Create ElevenLabs service instance for testing"""
        service = ElevenLabsService()
        service.redis_client = Mock()
        service.http_client = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_voice_profile(self):
        """Sample voice profile for testing"""
        return VoiceProfile(
            voice_id="test_voice_id",
            name="Test Voice",
            persona="professional",
            stability=0.75,
            similarity_boost=0.75,
            model=VoiceModel.TURBO_V2
        )
    
    @pytest.mark.asyncio
    async def test_voice_synthesis_performance(self, elevenlabs_service, test_voice_agent, sample_voice_profile, assert_timing):
        """Test voice synthesis meets sub-2s performance requirement"""
        test_text = "Hello, thank you for your interest in our properties. How can I help you today?"
        
        # Mock successful API response
        elevenlabs_service._synthesize_audio = AsyncMock(return_value=b"fake_audio_data")
        elevenlabs_service._get_voice_profile_for_agent = Mock(return_value=sample_voice_profile)
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
        elevenlabs_service._cache_audio = AsyncMock()
        elevenlabs_service._send_analytics_event = AsyncMock()
        
        # Test synthesis timing
        assert_timing.start()
        result = await elevenlabs_service.synthesize_speech(
            text=test_text,
            voice_agent=test_voice_agent,
            enable_caching=False
        )
        assert_timing.assert_under(2.0, "Voice synthesis must complete under 2 seconds")
        
        # Validate result
        assert result.audio_data == b"fake_audio_data"
        assert result.processing_time_ms < 2000
        assert not result.cached
        assert result.voice_id == sample_voice_profile.voice_id
    
    @pytest.mark.asyncio
    async def test_voice_caching_functionality(self, elevenlabs_service, test_voice_agent, sample_voice_profile):
        """Test voice caching improves performance"""
        test_text = "Welcome to our real estate platform"
        
        # Mock cached response
        cached_result = {
            "audio_data": base64.b64encode(b"cached_audio_data").decode(),
            "duration_ms": 2500,
            "voice_id": "test_voice_id"
        }
        
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
        elevenlabs_service._synthesize_audio = AsyncMock(return_value=b"fresh_audio_data")
        elevenlabs_service._cache_audio = AsyncMock()
        elevenlabs_service._get_voice_profile_for_agent = Mock(return_value=sample_voice_profile)
        elevenlabs_service._send_analytics_event = AsyncMock()
        
        # First synthesis - not cached
        start_time = time.time()
        result1 = await elevenlabs_service.synthesize_speech(
            text=test_text,
            voice_agent=test_voice_agent,
            enable_caching=True
        )
        first_synthesis_time = time.time() - start_time
        
        assert not result1.cached
        assert result1.audio_data == b"fresh_audio_data"
        elevenlabs_service._cache_audio.assert_called_once()
        
        # Simulate cached response for second call
        from app.services.elevenlabs_service import SynthesisResult
        cached_synthesis_result = SynthesisResult(
            audio_data=b"cached_audio_data",
            duration_ms=2500,
            processing_time_ms=10,  # Very fast cache retrieval
            voice_id="test_voice_id",
            text_hash="test_hash",
            cached=True
        )
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=cached_synthesis_result)
        
        # Second synthesis - should be cached
        start_time = time.time()
        result2 = await elevenlabs_service.synthesize_speech(
            text=test_text,
            voice_agent=test_voice_agent,
            enable_caching=True
        )
        second_synthesis_time = time.time() - start_time
        
        assert result2.cached
        assert result2.audio_data == b"cached_audio_data"
        assert second_synthesis_time < first_synthesis_time * 0.1  # Cache should be 10x faster
    
    @pytest.mark.asyncio
    async def test_voice_streaming(self, elevenlabs_service, test_voice_agent, sample_voice_profile):
        """Test real-time voice streaming functionality"""
        test_text = "This is a streaming test message that should be delivered in real-time chunks."
        
        # Mock streaming response
        mock_chunks = [b"chunk1", b"chunk2", b"chunk3", b"final_chunk"]
        
        class MockStreamResponse:
            def __init__(self):
                self.status_code = 200
                self.chunks = iter(mock_chunks)
            
            async def aiter_bytes(self, chunk_size=1024):
                for chunk in self.chunks:
                    yield chunk
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
        
        elevenlabs_service._get_voice_profile_for_agent = Mock(return_value=sample_voice_profile)
        elevenlabs_service.http_client.stream = AsyncMock(return_value=MockStreamResponse())
        
        # Test streaming
        received_chunks = []
        async for chunk in elevenlabs_service.synthesize_streaming(
            text=test_text,
            voice_agent=test_voice_agent
        ):
            received_chunks.append(chunk)
        
        assert received_chunks == mock_chunks
        elevenlabs_service.http_client.stream.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_synthesis(self, elevenlabs_service, test_voice_agent, sample_voice_profile):
        """Test bulk synthesis with concurrency control"""
        texts = [
            "Welcome to our platform",
            "How can I help you today?",
            "Let me check available properties",
            "I'll schedule a viewing for you",
            "Thank you for your interest"
        ]
        
        elevenlabs_service._get_voice_profile_for_agent = Mock(return_value=sample_voice_profile)
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
        elevenlabs_service._synthesize_audio = AsyncMock(return_value=b"bulk_audio_data")
        elevenlabs_service._cache_audio = AsyncMock()
        elevenlabs_service._send_analytics_event = AsyncMock()
        
        # Test bulk synthesis
        start_time = time.time()
        results = await elevenlabs_service.bulk_synthesize(
            texts=texts,
            voice_agent=test_voice_agent,
            max_concurrent=3
        )
        total_time = time.time() - start_time
        
        assert len(results) == len(texts)
        assert all(result.audio_data == b"bulk_audio_data" for result in results)
        assert total_time < len(texts) * 2  # Should be faster than sequential
    
    @pytest.mark.asyncio
    async def test_voice_quality_assessment(self, elevenlabs_service, test_voice_agent):
        """Test voice quality scoring"""
        # Test high quality audio
        good_audio = b"a" * 10000  # Reasonable size
        quality_score = await elevenlabs_service.get_voice_quality_score(
            text="This is a test message",
            voice_agent=test_voice_agent,
            audio_data=good_audio
        )
        assert quality_score >= 0.8
        
        # Test poor quality audio (too small)
        poor_audio = b"a" * 100  # Too small
        poor_quality_score = await elevenlabs_service.get_voice_quality_score(
            text="This is a test message",
            voice_agent=test_voice_agent,
            audio_data=poor_audio
        )
        assert poor_quality_score < quality_score
    
    @pytest.mark.asyncio
    async def test_voice_profile_selection(self, elevenlabs_service, test_voice_agent):
        """Test voice profile selection based on agent configuration"""
        # Test default profile selection
        profile = elevenlabs_service._get_voice_profile_for_agent(test_voice_agent)
        assert profile.voice_id is not None
        assert profile.persona is not None
        
        # Test custom voice settings
        test_voice_agent.voice_settings = json.dumps({
            "profile": "friendly_female",
            "stability": 0.9,
            "similarity_boost": 0.8
        })
        
        custom_profile = elevenlabs_service._get_voice_profile_for_agent(test_voice_agent)
        assert custom_profile.stability == 0.9
        assert custom_profile.similarity_boost == 0.8
    
    @pytest.mark.asyncio
    async def test_health_check(self, elevenlabs_service, sample_voice_profile):
        """Test service health check functionality"""
        # Mock successful health check
        elevenlabs_service._synthesize_audio = AsyncMock(return_value=b"health_check_audio")
        elevenlabs_service.voice_profiles = {"test": sample_voice_profile}
        elevenlabs_service.redis_client.ping = AsyncMock()
        elevenlabs_service.response_times = [100, 150, 120, 180, 90]  # Mock response times
        elevenlabs_service.synthesis_count = 100
        elevenlabs_service.cache_hits = 80
        
        health_status = await elevenlabs_service.health_check()
        
        assert health_status["status"] in ["healthy", "degraded"]
        assert "response_time_ms" in health_status
        assert "cache_hit_rate_percent" in health_status
        assert health_status["cache_hit_rate_percent"] == 80.0
        assert health_status["total_syntheses"] == 100
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self, elevenlabs_service, test_voice_agent, sample_voice_profile):
        """Test error handling and fallback mechanisms"""
        elevenlabs_service._get_voice_profile_for_agent = Mock(return_value=sample_voice_profile)
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
        elevenlabs_service._cache_audio = AsyncMock()
        
        # Simulate API failure
        elevenlabs_service._synthesize_audio = AsyncMock(side_effect=Exception("API Error"))
        
        # Test that error is properly handled
        with pytest.raises(Exception, match="API Error"):
            await elevenlabs_service.synthesize_speech(
                text="Test error handling",
                voice_agent=test_voice_agent
            )


@pytest.mark.voice
@pytest.mark.api
class TestVoiceAPIEndpoints:
    """Test voice API endpoints"""
    
    @pytest.mark.asyncio
    async def test_voice_synthesis_endpoint(self, client: TestClient, authorized_headers, test_voice_agent):
        """Test voice synthesis API endpoint"""
        synthesis_data = {
            "text": "Hello, how can I help you with your property search today?",
            "voice_agent_id": test_voice_agent.id,
            "language": "en",
            "format": "mp3",
            "enable_caching": True
        }
        
        with patch('app.services.elevenlabs_service.elevenlabs_service') as mock_service:
            mock_result = Mock()
            mock_result.audio_data = b"mock_audio_data"
            mock_result.duration_ms = 2500
            mock_result.processing_time_ms = 850
            mock_result.cached = False
            mock_service.synthesize_speech.return_value = mock_result
            
            response = client.post(
                "/api/v1/voice/synthesize",
                json=synthesis_data,
                headers=authorized_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "audio_url" in result
            assert result["duration_ms"] == 2500
            assert result["processing_time_ms"] == 850
            assert result["cached"] == False
    
    @pytest.mark.asyncio
    async def test_voice_streaming_endpoint(self, client: TestClient, authorized_headers, test_voice_agent):
        """Test voice streaming WebSocket endpoint"""
        # This would typically require WebSocket testing
        # For now, test the HTTP streaming endpoint
        streaming_data = {
            "text": "This is a streaming test message for real-time voice synthesis.",
            "voice_agent_id": test_voice_agent.id,
            "language": "en"
        }
        
        with patch('app.services.elevenlabs_service.elevenlabs_service') as mock_service:
            # Mock streaming generator
            async def mock_streaming_generator():
                yield b"chunk1"
                yield b"chunk2"
                yield b"chunk3"
            
            mock_service.synthesize_streaming.return_value = mock_streaming_generator()
            
            response = client.post(
                "/api/v1/voice/stream",
                json=streaming_data,
                headers=authorized_headers
            )
            
            # For streaming endpoints, we'd typically test WebSocket connection
            # This is a simplified test for the endpoint existence
            assert response.status_code in [200, 101]  # 101 for WebSocket upgrade
    
    @pytest.mark.asyncio
    async def test_voice_agent_configuration(self, client: TestClient, authorized_headers, test_organization):
        """Test voice agent configuration endpoint"""
        agent_config = {
            "name": "Sales Assistant",
            "voice_settings": {
                "profile": "professional_male",
                "stability": 0.8,
                "similarity_boost": 0.75,
                "voice_id": "custom_voice_id"
            },
            "personality": "professional",
            "language": "en-US",
            "script_template": "real_estate_qualifier"
        }
        
        response = client.post(
            "/api/v1/voice-agents",
            json=agent_config,
            headers=authorized_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Sales Assistant"
        assert result["voice_settings"]["stability"] == 0.8
        assert result["is_active"] == True
    
    @pytest.mark.asyncio
    async def test_voice_analytics_endpoint(self, client: TestClient, authorized_headers, test_organization):
        """Test voice analytics and performance metrics"""
        response = client.get(
            "/api/v1/voice/analytics",
            headers=authorized_headers,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        )
        
        assert response.status_code == 200
        analytics = response.json()
        assert "total_syntheses" in analytics
        assert "average_processing_time_ms" in analytics
        assert "cache_hit_rate" in analytics
        assert "quality_score" in analytics
        assert "performance_metrics" in analytics


@pytest.mark.voice
@pytest.mark.websocket
class TestVoiceWebSocketStreaming:
    """Test WebSocket voice streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_voice_streaming(self, test_voice_agent):
        """Test WebSocket streaming for real-time voice"""
        # This is a conceptual test - actual WebSocket testing would require
        # more complex setup with a running server
        
        streaming_message = {
            "type": "voice_stream_request",
            "text": "Hello, this is a real-time voice streaming test.",
            "voice_agent_id": test_voice_agent.id,
            "language": "en",
            "session_id": "test_session_123"
        }
        
        # Simulate WebSocket connection
        with patch('app.api.v1.voice_streaming.websocket_manager') as mock_manager:
            mock_manager.send_audio_chunk = AsyncMock()
            
            # This would test the WebSocket handler logic
            # In a real implementation, you'd use pytest-asyncio with actual WebSocket connections
            assert streaming_message["type"] == "voice_stream_request"
            assert len(streaming_message["text"]) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_websocket_connections(self):
        """Test handling multiple concurrent WebSocket connections"""
        # Test would verify that the system can handle 1000+ concurrent connections
        max_concurrent_connections = 1000
        
        # Mock concurrent connection handling
        with patch('app.api.v1.voice_streaming.websocket_manager') as mock_manager:
            mock_manager.active_connections = {}
            mock_manager.max_connections = max_concurrent_connections
            
            # Simulate connection management
            for i in range(max_concurrent_connections):
                connection_id = f"conn_{i}"
                mock_manager.active_connections[connection_id] = Mock()
            
            assert len(mock_manager.active_connections) == max_concurrent_connections


@pytest.mark.voice
@pytest.mark.performance
class TestVoicePerformance:
    """Test voice processing performance requirements"""
    
    @pytest.mark.asyncio
    async def test_sub_2_second_response_time(self, elevenlabs_service, test_voice_agent, sample_voice_profile, performance_monitor):
        """Test that voice synthesis consistently meets sub-2s requirement"""
        test_texts = [
            "Hello, welcome to our real estate platform.",
            "I'd be happy to help you find your perfect home.",
            "What type of property are you looking for today?",
            "Let me check our available listings in your area.",
            "Would you like to schedule a viewing?"
        ]
        
        elevenlabs_service._get_voice_profile_for_agent = Mock(return_value=sample_voice_profile)
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
        elevenlabs_service._synthesize_audio = AsyncMock(return_value=b"performance_test_audio")
        elevenlabs_service._cache_audio = AsyncMock()
        elevenlabs_service._send_analytics_event = AsyncMock()
        
        response_times = []
        
        for text in test_texts:
            performance_monitor.start()
            
            result = await elevenlabs_service.synthesize_speech(
                text=text,
                voice_agent=test_voice_agent,
                enable_caching=False,  # Test fresh synthesis
                optimize_for_speed=True
            )
            
            metrics = performance_monitor.get_metrics()
            response_times.append(metrics["elapsed_time"])
            
            # Each individual synthesis must be under 2 seconds
            assert metrics["elapsed_time"] < 2.0, f"Synthesis took {metrics['elapsed_time']:.3f}s for text: {text[:30]}..."
        
        # Average response time should be well under 2 seconds
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 1.5, f"Average response time {avg_response_time:.3f}s exceeds target"
        
        # 95th percentile should still be under 2 seconds
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        assert p95_response_time < 2.0, f"95th percentile response time {p95_response_time:.3f}s exceeds target"
    
    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self, elevenlabs_service, test_voice_agent, sample_voice_profile):
        """Test that caching provides significant performance improvement"""
        test_text = "Cache performance test message"
        
        elevenlabs_service._get_voice_profile_for_agent = Mock(return_value=sample_voice_profile)
        elevenlabs_service._send_analytics_event = AsyncMock()
        
        # First call - not cached (simulate slow synthesis)
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
        elevenlabs_service._synthesize_audio = AsyncMock(side_effect=lambda req: asyncio.sleep(0.5) or b"fresh_audio")
        elevenlabs_service._cache_audio = AsyncMock()
        
        start_time = time.time()
        result1 = await elevenlabs_service.synthesize_speech(
            text=test_text,
            voice_agent=test_voice_agent,
            enable_caching=True
        )
        uncached_time = time.time() - start_time
        
        # Second call - cached (simulate fast retrieval)
        from app.services.elevenlabs_service import SynthesisResult
        cached_result = SynthesisResult(
            audio_data=b"cached_audio",
            duration_ms=2500,
            processing_time_ms=10,
            voice_id="test_voice",
            text_hash="test_hash",
            cached=True
        )
        elevenlabs_service._get_cached_audio = AsyncMock(return_value=cached_result)
        
        start_time = time.time()
        result2 = await elevenlabs_service.synthesize_speech(
            text=test_text,
            voice_agent=test_voice_agent,
            enable_caching=True
        )
        cached_time = time.time() - start_time
        
        # Cached version should be at least 5x faster
        performance_improvement = uncached_time / cached_time
        assert performance_improvement >= 5.0, f"Cache only improved performance by {performance_improvement:.1f}x"
        assert result2.cached == True
        assert cached_time < 0.1  # Cached response should be very fast


@pytest.mark.voice
@pytest.mark.integration
class TestVoiceIntegrationWithDatabase:
    """Test voice service integration with database"""
    
    @pytest.mark.asyncio
    async def test_voice_agent_database_integration(self, db_session, test_organization, elevenlabs_service):
        """Test voice agent creation and configuration storage"""
        from app.models.voice_agent import VoiceAgent
        
        # Create voice agent
        voice_agent = VoiceAgent(
            organization_id=test_organization.id,
            name="Integration Test Agent",
            voice_settings=json.dumps({
                "profile": "professional_male",
                "stability": 0.8,
                "similarity_boost": 0.75
            }),
            personality="professional",
            language="en-US",
            is_active=True
        )
        
        db_session.add(voice_agent)
        await db_session.commit()
        await db_session.refresh(voice_agent)
        
        # Test that voice profile is correctly retrieved
        profile = elevenlabs_service._get_voice_profile_for_agent(voice_agent)
        assert profile.stability == 0.8
        assert profile.similarity_boost == 0.75
        assert profile.persona == "professional"
    
    @pytest.mark.asyncio
    async def test_conversation_voice_recording_storage(self, db_session, test_organization, test_lead, test_user):
        """Test that voice recordings are properly linked to conversations"""
        from app.models.conversation import Conversation
        
        # Create conversation with voice recording
        conversation = Conversation(
            organization_id=test_organization.id,
            lead_id=test_lead.id,
            agent_id=test_user.id,
            duration_seconds=180,
            transcript="Test conversation with voice recording",
            recording_url="https://storage.example.com/recordings/test_recording.mp3",
            voice_agent_used="test_voice_agent_id",
            voice_synthesis_time_ms=850,
            voice_quality_score=0.92
        )
        
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)
        
        # Verify voice-related fields are stored
        assert conversation.recording_url is not None
        assert conversation.voice_agent_used == "test_voice_agent_id"
        assert conversation.voice_synthesis_time_ms == 850
        assert conversation.voice_quality_score == 0.92