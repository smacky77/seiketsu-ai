"""
Comprehensive unit tests for VoiceService
Tests voice processing, AI integration, and performance requirements
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from app.services.voice_service import VoiceService
from app.models.voice_agent import VoiceAgent
from app.models.conversation import Conversation
from app.models.lead import Lead


@pytest.mark.asyncio
@pytest.mark.voice
@pytest.mark.unit
class TestVoiceService:
    """Test suite for VoiceService functionality"""

    @pytest.fixture
    async def voice_service(self):
        """Create VoiceService instance with mocked dependencies"""
        with patch('app.services.voice_service.openai') as mock_openai, \
             patch('app.services.voice_service.elevenlabs_service') as mock_elevenlabs, \
             patch('app.services.voice_service.ConversationService') as mock_conv_service, \
             patch('app.services.voice_service.LeadService') as mock_lead_service, \
             patch('app.services.voice_service.WebhookService') as mock_webhook_service:
            
            # Setup mocks
            mock_openai.AsyncOpenAI.return_value = AsyncMock()
            mock_elevenlabs.initialize = AsyncMock()
            mock_conv_service.return_value = AsyncMock()
            mock_lead_service.return_value = AsyncMock()
            mock_webhook_service.return_value = AsyncMock()
            
            service = VoiceService()
            await service.initialize()
            
            yield service

    @pytest.fixture
    def sample_voice_agent(self, test_organization):
        """Create sample voice agent for testing"""
        return VoiceAgent(
            id="test_agent_id",
            organization_id=test_organization.id,
            name="Test Agent",
            voice_id="elevenlabs_test_voice",
            greeting_message="Hello, how can I help you?",
            ai_model="gpt-4",
            temperature=0.7,
            max_tokens=200
        )

    @pytest.fixture
    def sample_audio_data(self):
        """Sample audio data for testing"""
        return b"fake_audio_data_for_testing"

    async def test_initialize_success(self, voice_service):
        """Test successful voice service initialization"""
        # Should initialize without errors
        assert voice_service.openai_client is not None
        assert voice_service.elevenlabs_service is not None
        assert voice_service.target_response_time_ms == 180

    async def test_process_voice_input_success(self, voice_service, sample_voice_agent, sample_audio_data):
        """Test successful voice input processing within target time"""
        conversation_id = "test_conversation_id"
        organization_id = "test_org_id"
        
        # Mock responses
        with patch.object(voice_service, '_speech_to_text', return_value="Hello, I want to buy a house") as mock_stt, \
             patch.object(voice_service, '_generate_ai_response', return_value={
                 "text": "Great! I'd love to help you find a house. What's your budget?",
                 "lead_qualified": False,
                 "needs_transfer": False,
                 "conversation_ended": False
             }) as mock_ai, \
             patch.object(voice_service.elevenlabs_service, 'synthesize_speech', return_value=Mock(
                 audio_data=b"synthesized_audio_response"
             )) as mock_tts, \
             patch.object(voice_service, '_save_conversation_messages') as mock_save:
            
            start_time = time.time()
            result = await voice_service.process_voice_input(
                sample_audio_data, conversation_id, sample_voice_agent, organization_id
            )
            processing_time = (time.time() - start_time) * 1000
            
            # Verify result structure
            assert result["success"] is True
            assert result["transcript"] == "Hello, I want to buy a house"
            assert result["response_text"] == "Great! I'd love to help you find a house. What's your budget?"
            assert result["response_audio"] == b"synthesized_audio_response"
            assert "timing" in result
            assert result["lead_qualified"] is False
            
            # Verify performance
            assert result["timing"]["total_ms"] <= voice_service.target_response_time_ms
            
            # Verify all pipeline steps were called
            mock_stt.assert_called_once_with(sample_audio_data)
            mock_ai.assert_called_once()
            mock_tts.assert_called_once()
            mock_save.assert_called_once()

    async def test_process_voice_input_performance_warning(self, voice_service, sample_voice_agent, sample_audio_data):
        """Test performance warning when processing exceeds target time"""
        with patch.object(voice_service, '_speech_to_text', return_value="test"), \
             patch.object(voice_service, '_generate_ai_response', return_value={"text": "response"}), \
             patch.object(voice_service.elevenlabs_service, 'synthesize_speech', return_value=Mock(audio_data=b"audio")), \
             patch.object(voice_service, '_save_conversation_messages'), \
             patch('time.sleep', return_value=None):  # Simulate slow processing
            
            # Mock slow processing
            async def slow_tts(*args, **kwargs):
                await asyncio.sleep(0.2)  # 200ms delay
                return Mock(audio_data=b"slow_audio")
            
            voice_service.elevenlabs_service.synthesize_speech = slow_tts
            
            with patch('app.services.voice_service.logger.warning') as mock_logger:
                result = await voice_service.process_voice_input(
                    sample_audio_data, "conv_id", sample_voice_agent, "org_id"
                )
                
                # Should log warning if over target time
                if result["timing"]["total_ms"] > voice_service.target_response_time_ms:
                    mock_logger.assert_called()

    async def test_process_voice_input_with_lead_qualification(self, voice_service, sample_voice_agent, sample_audio_data):
        """Test voice processing with lead qualification"""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "budget_min": 300000,
            "budget_max": 500000
        }
        
        with patch.object(voice_service, '_speech_to_text', return_value="I'm looking for a house under $500k"), \
             patch.object(voice_service, '_generate_ai_response', return_value={
                 "text": "Perfect! I found some great options for you.",
                 "lead_qualified": True,
                 "lead_data": lead_data
             }), \
             patch.object(voice_service.elevenlabs_service, 'synthesize_speech', return_value=Mock(audio_data=b"audio")), \
             patch.object(voice_service, '_save_conversation_messages'), \
             patch.object(voice_service, '_process_lead_qualification') as mock_lead_processing:
            
            result = await voice_service.process_voice_input(
                sample_audio_data, "conv_id", sample_voice_agent, "org_id"
            )
            
            assert result["success"] is True
            assert result["lead_qualified"] is True
            mock_lead_processing.assert_called_once_with(
                "conv_id", lead_data, "org_id"
            )

    async def test_process_voice_input_error_handling(self, voice_service, sample_voice_agent, sample_audio_data):
        """Test error handling in voice processing"""
        with patch.object(voice_service, '_speech_to_text', side_effect=Exception("STT failed")):
            result = await voice_service.process_voice_input(
                sample_audio_data, "conv_id", sample_voice_agent, "org_id"
            )
            
            assert result["success"] is False
            assert "error" in result
            assert "STT failed" in result["error"]
            assert "timing" in result

    async def test_start_conversation_success(self, voice_service, sample_voice_agent):
        """Test successful conversation start"""
        caller_phone = "+1234567890"
        organization_id = "test_org_id"
        
        mock_conversation = Mock()
        mock_conversation.id = "new_conv_id"
        mock_conversation.started_at = Mock()
        
        with patch.object(voice_service.conversation_service, 'create_conversation', return_value=mock_conversation), \
             patch.object(voice_service.elevenlabs_service, 'synthesize_speech', return_value=Mock(
                 audio_data=b"greeting_audio"
             )), \
             patch.object(voice_service, '_save_conversation_message'), \
             patch.object(voice_service.webhook_service, 'send_webhook') as mock_webhook:
            
            result = await voice_service.start_conversation(
                caller_phone, sample_voice_agent, organization_id
            )
            
            assert result == mock_conversation
            mock_webhook.assert_called_once()

    async def test_end_conversation_success(self, voice_service):
        """Test successful conversation ending"""
        conversation_id = "test_conv_id"
        outcome = "lead_qualified"
        outcome_details = {"lead_score": 85, "next_action": "schedule_appointment"}
        
        mock_conversation = Mock()
        mock_conversation.id = conversation_id
        mock_conversation.organization_id = "org_id"
        mock_conversation.duration_seconds = 180
        mock_conversation.was_successful = True
        mock_conversation.voice_agent = Mock()
        mock_conversation.lead_id = "lead_id"
        mock_conversation.ended_at = Mock()
        
        with patch.object(voice_service.conversation_service, 'end_conversation', return_value=mock_conversation), \
             patch.object(voice_service.webhook_service, 'send_webhook') as mock_webhook:
            
            result = await voice_service.end_conversation(
                conversation_id, outcome, outcome_details
            )
            
            assert result["conversation_id"] == conversation_id
            assert result["outcome"] == outcome
            assert result["lead_created"] is True
            mock_webhook.assert_called_once()

    async def test_transfer_to_human_success(self, voice_service):
        """Test successful transfer to human agent"""
        conversation_id = "test_conv_id"
        reason = "complex_financial_question"
        target_agent = "senior_agent_id"
        
        mock_conversation = Mock()
        mock_conversation.id = conversation_id
        mock_conversation.organization_id = "org_id"
        mock_conversation.transfer_timestamp = Mock()
        
        with patch.object(voice_service.conversation_service, 'transfer_to_human', return_value=mock_conversation), \
             patch.object(voice_service.webhook_service, 'send_webhook') as mock_webhook:
            
            result = await voice_service.transfer_to_human(
                conversation_id, reason, target_agent
            )
            
            assert result["conversation_id"] == conversation_id
            assert result["transferred"] is True
            assert result["reason"] == reason
            assert result["target_agent"] == target_agent
            mock_webhook.assert_called_once()

    async def test_speech_to_text_success(self, voice_service, sample_audio_data):
        """Test successful speech-to-text conversion"""
        expected_transcript = "Hello, I need help finding a house"
        
        mock_response = Mock()
        mock_response.text = expected_transcript
        
        voice_service.openai_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)
        
        result = await voice_service._speech_to_text(sample_audio_data)
        
        assert result == expected_transcript
        voice_service.openai_client.audio.transcriptions.create.assert_called_once()

    async def test_speech_to_text_error(self, voice_service, sample_audio_data):
        """Test speech-to-text error handling"""
        voice_service.openai_client.audio.transcriptions.create = AsyncMock(
            side_effect=Exception("OpenAI API error")
        )
        
        with pytest.raises(Exception):
            await voice_service._speech_to_text(sample_audio_data)

    async def test_generate_ai_response_success(self, voice_service, sample_voice_agent):
        """Test successful AI response generation"""
        user_input = "I want to buy a $400k house with 3 bedrooms"
        conversation_id = "conv_id"
        organization_id = "org_id"
        
        # Mock conversation history
        with patch.object(voice_service, '_get_conversation_history', return_value=[]):
            # Mock OpenAI response
            mock_message = Mock()
            mock_message.function_call = Mock()
            mock_message.function_call.arguments = '{"response_text": "Great! I can help you find a 3-bedroom house in your budget.", "lead_qualified": true}'
            
            mock_choice = Mock()
            mock_choice.message = mock_message
            
            mock_response = Mock()
            mock_response.choices = [mock_choice]
            
            voice_service.openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            result = await voice_service._generate_ai_response(
                user_input, conversation_id, sample_voice_agent, organization_id
            )
            
            assert result["response_text"] == "Great! I can help you find a 3-bedroom house in your budget."
            assert result["lead_qualified"] is True

    async def test_generate_ai_response_fallback(self, voice_service, sample_voice_agent):
        """Test AI response fallback on error"""
        voice_service.openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API error")
        )
        
        with patch.object(voice_service, '_get_conversation_history', return_value=[]):
            result = await voice_service._generate_ai_response(
                "test input", "conv_id", sample_voice_agent, "org_id"
            )
            
            assert "response_text" in result
            assert "trouble processing" in result["response_text"].lower()

    async def test_streaming_synthesis(self, voice_service, sample_voice_agent):
        """Test streaming voice synthesis"""
        text = "This is a test response for streaming"
        
        # Mock streaming response
        async def mock_stream():
            chunks = [b"chunk1", b"chunk2", b"chunk3"]
            for chunk in chunks:
                yield chunk
        
        voice_service.elevenlabs_service.synthesize_streaming = AsyncMock(return_value=mock_stream())
        
        result_chunks = []
        async for chunk in voice_service.synthesize_speech_streaming(text, sample_voice_agent):
            result_chunks.append(chunk)
        
        assert len(result_chunks) == 3
        assert result_chunks == [b"chunk1", b"chunk2", b"chunk3"]

    async def test_pregenerate_responses(self, voice_service, sample_voice_agent):
        """Test pre-generating common responses"""
        common_responses = [
            "Hello, how can I help you today?",
            "Thank you for your interest in our properties.",
            "I'd be happy to schedule a viewing for you."
        ]
        
        voice_service.elevenlabs_service.pregenerate_responses = AsyncMock()
        
        await voice_service.pregenerate_agent_responses(
            sample_voice_agent, common_responses
        )
        
        voice_service.elevenlabs_service.pregenerate_responses.assert_called_once()

    async def test_performance_stats(self, voice_service):
        """Test performance statistics tracking"""
        # Simulate some processing times
        voice_service.response_times = [150, 160, 170, 180, 200]
        
        stats = voice_service.performance_stats
        
        assert stats["average_ms"] == 172.0
        assert stats["requests_processed"] == 5
        assert stats["target_met_percentage"] == 80.0  # 4 out of 5 under 180ms
        assert stats["target_response_time_ms"] == 180

    async def test_average_response_time(self, voice_service):
        """Test average response time calculation"""
        voice_service.response_times = [100, 150, 200]
        
        avg_time = voice_service.average_response_time_ms
        assert avg_time == 150.0
        
        # Test empty response times
        voice_service.response_times = []
        avg_time = voice_service.average_response_time_ms
        assert avg_time == 0.0

    async def test_health_check(self, voice_service):
        """Test voice service health check"""
        # Mock ElevenLabs health check
        voice_service.elevenlabs_service.health_check = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 45
        })
        
        # Add some performance data
        voice_service.response_times = [120, 140, 160]
        
        health = await voice_service.get_voice_service_health()
        
        assert health["overall_status"] == "healthy"
        assert "voice_processing" in health
        assert "elevenlabs_service" in health
        assert health["target_response_time_ms"] == 180
        assert "timestamp" in health

    async def test_health_check_degraded(self, voice_service):
        """Test health check with degraded performance"""
        # Mock slow performance
        voice_service.response_times = [250, 300, 350]  # All over target
        
        voice_service.elevenlabs_service.health_check = AsyncMock(return_value={
            "status": "healthy"
        })
        
        health = await voice_service.get_voice_service_health()
        
        assert health["overall_status"] == "degraded"

    async def test_health_check_error(self, voice_service):
        """Test health check error handling"""
        voice_service.elevenlabs_service.health_check = AsyncMock(
            side_effect=Exception("Service unavailable")
        )
        
        health = await voice_service.get_voice_service_health()
        
        assert health["overall_status"] == "unhealthy"
        assert "error" in health
        assert "Service unavailable" in health["error"]

    @pytest.mark.performance
    async def test_voice_processing_performance_benchmark(self, voice_service, sample_voice_agent, sample_audio_data):
        """Performance benchmark test for voice processing pipeline"""
        # Setup mocks for fast responses
        with patch.object(voice_service, '_speech_to_text', return_value="Quick test"), \
             patch.object(voice_service, '_generate_ai_response', return_value={"text": "Quick response"}), \
             patch.object(voice_service.elevenlabs_service, 'synthesize_speech', return_value=Mock(audio_data=b"audio")), \
             patch.object(voice_service, '_save_conversation_messages'):
            
            # Run multiple iterations to get average performance
            times = []
            for _ in range(10):
                start_time = time.time()
                result = await voice_service.process_voice_input(
                    sample_audio_data, "conv_id", sample_voice_agent, "org_id"
                )
                processing_time = (time.time() - start_time) * 1000
                times.append(processing_time)
                
                assert result["success"] is True
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            # Performance assertions
            assert avg_time < voice_service.target_response_time_ms, f"Average time {avg_time}ms exceeds target"
            assert max_time < voice_service.target_response_time_ms * 1.5, f"Max time {max_time}ms too high"

    @pytest.mark.performance
    async def test_concurrent_voice_processing(self, voice_service, sample_voice_agent, sample_audio_data):
        """Test concurrent voice processing performance"""
        with patch.object(voice_service, '_speech_to_text', return_value="Concurrent test"), \
             patch.object(voice_service, '_generate_ai_response', return_value={"text": "Concurrent response"}), \
             patch.object(voice_service.elevenlabs_service, 'synthesize_speech', return_value=Mock(audio_data=b"audio")), \
             patch.object(voice_service, '_save_conversation_messages'):
            
            # Create concurrent tasks
            tasks = []
            num_concurrent = 5
            
            start_time = time.time()
            for i in range(num_concurrent):
                task = voice_service.process_voice_input(
                    sample_audio_data, f"conv_{i}", sample_voice_agent, "org_id"
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)
            total_time = (time.time() - start_time) * 1000
            
            # Verify all succeeded
            for result in results:
                assert result["success"] is True
            
            # Should complete faster than sequential processing
            expected_sequential_time = num_concurrent * voice_service.target_response_time_ms
            assert total_time < expected_sequential_time * 0.8, "Concurrent processing not efficient enough"


@pytest.mark.asyncio
@pytest.mark.voice
@pytest.mark.integration
class TestVoiceServiceIntegration:
    """Integration tests for VoiceService with real dependencies"""
    
    @pytest.fixture
    async def voice_service_real(self):
        """VoiceService with real dependencies (mocked external APIs)"""
        with patch('app.services.voice_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test_key"
            
            service = VoiceService()
            # Mock external API calls but keep internal logic
            with patch.object(service, '_test_openai_connection'), \
                 patch.object(service.elevenlabs_service, 'initialize'):
                await service.initialize()
            
            yield service

    async def test_full_voice_pipeline_integration(self, voice_service_real, sample_voice_agent, sample_audio_data, db_session):
        """Test full voice processing pipeline with database integration"""
        conversation_id = "integration_test_conv"
        organization_id = "integration_test_org"
        
        with patch.object(voice_service_real, '_speech_to_text', return_value="I want to buy a house for $400k"), \
             patch.object(voice_service_real.openai_client.chat.completions, 'create') as mock_openai, \
             patch.object(voice_service_real.elevenlabs_service, 'synthesize_speech', return_value=Mock(
                 audio_data=b"integration_test_audio"
             )):
            
            # Mock OpenAI response
            mock_response = Mock()
            mock_message = Mock()
            mock_message.function_call = Mock()
            mock_message.function_call.arguments = '{
                "response_text": "Great! I can help you find a house in your budget. What area are you looking in?",
                "lead_qualified": true,
                "lead_data": {
                    "budget_max": 400000,
                    "property_type": "house"
                }
            }'
            mock_response.choices = [Mock(message=mock_message)]
            mock_openai.return_value = mock_response
            
            result = await voice_service_real.process_voice_input(
                sample_audio_data, conversation_id, sample_voice_agent, organization_id
            )
            
            # Verify integration result
            assert result["success"] is True
            assert result["lead_qualified"] is True
            assert "$400k" in result["transcript"] or "400k" in result["transcript"]
            assert "budget" in result["response_text"].lower()

    async def test_error_recovery_integration(self, voice_service_real, sample_voice_agent, sample_audio_data):
        """Test error recovery in integrated environment"""
        # Simulate OpenAI API failure
        with patch.object(voice_service_real, '_speech_to_text', return_value="test input"), \
             patch.object(voice_service_real, '_generate_ai_response', side_effect=Exception("API timeout")), \
             patch.object(voice_service_real.elevenlabs_service, 'synthesize_speech', return_value=Mock(audio_data=b"error_audio")):
            
            result = await voice_service_real.process_voice_input(
                sample_audio_data, "conv_id", sample_voice_agent, "org_id"
            )
            
            # Should handle error gracefully
            assert result["success"] is False
            assert "error" in result
            assert "timing" in result  # Should still track timing
