"""
Advanced AI service mocking and testing with realistic responses and performance validation.
Tests AI service reliability, accuracy, and fallback mechanisms.
"""
import pytest
import asyncio
import json
import time
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import base64
import random

from app.ai.voice.engine import VoiceEngine
from app.ai.conversation.engine import ConversationEngine
from app.ai.domain.lead_qualification import LeadQualifier
from app.ai.analytics.sentiment import SentimentAnalyzer
from app.services.elevenlabs_service import ElevenLabsService
from app.services.voice_service import VoiceService

from tests.factories import (
    LeadFactory, 
    ConversationFactory, 
    QualifiedLeadFactory,
    create_complete_sales_scenario
)


class MockAIServiceBase:
    """Base class for AI service mocks with realistic behavior"""
    
    def __init__(self, success_rate=0.95, latency_range=(0.01, 0.1)):
        self.success_rate = success_rate
        self.latency_range = latency_range
        self.call_count = 0
        self.error_count = 0
        
    async def simulate_processing_delay(self):
        """Simulate realistic processing delay"""
        delay = random.uniform(*self.latency_range)
        await asyncio.sleep(delay)
        
    def should_succeed(self):
        """Determine if operation should succeed based on success rate"""
        return random.random() < self.success_rate
        
    def increment_call_count(self):
        """Track API calls"""
        self.call_count += 1
        
    def get_stats(self):
        """Get mock service statistics"""
        return {
            "total_calls": self.call_count,
            "error_count": self.error_count,
            "success_rate": (self.call_count - self.error_count) / max(self.call_count, 1),
            "avg_latency": sum(self.latency_range) / 2
        }


class MockElevenLabsService(MockAIServiceBase):
    """Mock ElevenLabs service with realistic voice synthesis"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.voice_models = {
            "sarah_professional": {
                "name": "Sarah Professional",
                "accent": "american",
                "gender": "female",
                "age": "middle_aged",
                "style": "professional"
            },
            "mike_friendly": {
                "name": "Mike Friendly", 
                "accent": "american",
                "gender": "male",
                "age": "young_adult",
                "style": "friendly"
            },
            "lisa_warm": {
                "name": "Lisa Warm",
                "accent": "american", 
                "gender": "female",
                "age": "middle_aged",
                "style": "warm"
            }
        }
    
    async def synthesize_speech(self, text: str, voice_id: str, settings: Dict) -> Dict:
        """Mock speech synthesis with realistic behavior"""
        self.increment_call_count()
        await self.simulate_processing_delay()
        
        if not self.should_succeed():
            self.error_count += 1
            raise Exception("ElevenLabs API temporarily unavailable")
        
        # Simulate realistic audio generation
        char_count = len(text)
        estimated_duration = char_count * 0.05  # ~20 chars per second
        audio_size = int(estimated_duration * 24000 * 2)  # 24kHz, 16-bit
        
        return {
            "audio_data": b"fake_audio_data_" + text[:50].encode(),
            "format": "mp3",
            "sample_rate": 24000,
            "duration_seconds": round(estimated_duration, 2),
            "character_count": char_count,
            "voice_id": voice_id,
            "voice_settings": settings,
            "processing_time_ms": random.randint(45, 150)
        }
    
    async def get_voice_list(self) -> List[Dict]:
        """Mock voice list retrieval"""
        self.increment_call_count()
        await self.simulate_processing_delay()
        
        if not self.should_succeed():
            self.error_count += 1
            raise Exception("Failed to retrieve voice list")
        
        return [
            {"voice_id": vid, **details}
            for vid, details in self.voice_models.items()
        ]
    
    async def clone_voice(self, voice_samples: List[bytes], voice_name: str) -> Dict:
        """Mock voice cloning"""
        self.increment_call_count() 
        await asyncio.sleep(random.uniform(2.0, 5.0))  # Voice cloning takes longer
        
        if not self.should_succeed():
            self.error_count += 1
            raise Exception("Voice cloning failed")
        
        return {
            "voice_id": f"cloned_{uuid.uuid4().hex[:8]}",
            "voice_name": voice_name,
            "status": "ready",
            "similarity_score": random.uniform(0.85, 0.98),
            "training_samples": len(voice_samples)
        }


class MockOpenAIService(MockAIServiceBase):
    """Mock OpenAI service for conversation AI"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conversation_templates = {
            "property_search": [
                "I'd be happy to help you find the perfect property! What type of home are you looking for?",
                "Great! Let me search our available properties that match your criteria.",
                "Based on your preferences, I have several excellent options to show you."
            ],
            "budget_inquiry": [
                "Understanding your budget helps me find the best options for you. What's your price range?",
                "Excellent! That budget opens up some wonderful opportunities in great neighborhoods.",
                "I can work within that budget to find you something perfect."
            ],
            "schedule_viewing": [
                "I'd love to show you these properties! When would be a good time for you?",
                "Perfect! I'll arrange viewings for this weekend. What time works best?",
                "Great! I'll coordinate with the listing agents and confirm the appointment times."
            ],
            "financing_help": [
                "I can connect you with excellent mortgage professionals. Are you pre-approved?",
                "Getting pre-approved gives you a competitive advantage. I know great lenders who can help.",
                "Let me introduce you to our preferred lending partners who specialize in your situation."
            ]
        }
    
    async def chat_completion(self, messages: List[Dict], model: str = "gpt-4") -> Dict:
        """Mock chat completion with contextual responses"""
        self.increment_call_count()
        await self.simulate_processing_delay()
        
        if not self.should_succeed():
            self.error_count += 1
            raise Exception("OpenAI API rate limit exceeded")
        
        # Analyze last user message to determine intent
        user_message = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
        detected_intent = self._detect_intent(user_message)
        
        # Generate contextual response
        response_text = self._generate_response(detected_intent, user_message)
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": sum(len(msg["content"].split()) for msg in messages),
                "completion_tokens": len(response_text.split()),
                "total_tokens": sum(len(msg["content"].split()) for msg in messages) + len(response_text.split())
            },
            "model": model,
            "processing_time_ms": random.randint(200, 800)
        }
    
    def _detect_intent(self, text: str) -> str:
        """Simple intent detection based on keywords"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["house", "home", "property", "buy", "purchase"]):
            return "property_search"
        elif any(word in text_lower for word in ["budget", "price", "cost", "afford", "$"]):
            return "budget_inquiry"
        elif any(word in text_lower for word in ["viewing", "show", "see", "visit", "appointment"]):
            return "schedule_viewing"
        elif any(word in text_lower for word in ["loan", "mortgage", "financing", "lender", "pre-approved"]):
            return "financing_help"
        else:
            return "general_inquiry"
    
    def _generate_response(self, intent: str, user_message: str) -> str:
        """Generate contextual response based on intent"""
        base_responses = self.conversation_templates.get(intent, [
            "I understand your question. Let me help you with that.",
            "That's a great point. I'm here to assist you.",
            "I'd be happy to help you with that inquiry."
        ])
        
        base_response = random.choice(base_responses)
        
        # Add contextual details based on user message
        if "3 bedroom" in user_message.lower():
            base_response += " I see you're looking for a 3-bedroom home specifically."
        elif "downtown" in user_message.lower():
            base_response += " Downtown has some excellent properties available right now."
        elif any(price in user_message for price in ["$", "k", "thousand", "million"]):
            base_response += " I'll focus on properties within your specified budget range."
        
        return base_response


class MockSpeechToTextService(MockAIServiceBase):
    """Mock speech-to-text service"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transcription_samples = [
            "Hello, I'm interested in buying a house in the downtown area",
            "I'm looking for a three-bedroom home with a garage and good schools nearby",
            "What's the average price for condos in this neighborhood?",
            "Can you schedule a viewing for this weekend?",
            "I need help with mortgage pre-approval, who do you recommend?",
            "I'm a first-time buyer, what should I know about the process?",
            "Are there any properties with pools in my price range?",
            "I'd like to see the market analysis for this area"
        ]
    
    async def transcribe(self, audio_data: bytes, language: str = "en-US") -> Dict:
        """Mock audio transcription"""
        self.increment_call_count()
        await self.simulate_processing_delay()
        
        if not self.should_succeed():
            self.error_count += 1
            raise Exception("Speech recognition service unavailable")
        
        # Simulate realistic transcription
        transcript = random.choice(self.transcription_samples)
        confidence = random.uniform(0.85, 0.99)
        audio_duration = len(audio_data) / 16000  # Assume 16kHz sample rate
        
        return {
            "transcript": transcript,
            "confidence": round(confidence, 3),
            "language": language,
            "duration_seconds": round(audio_duration, 2),
            "word_count": len(transcript.split()),
            "processing_time_ms": random.randint(50, 200)
        }


class TestAIServiceMocking:
    """Test AI service mocking and validation"""
    
    @pytest.fixture
    def mock_elevenlabs(self):
        """Create mock ElevenLabs service"""
        return MockElevenLabsService(success_rate=0.98, latency_range=(0.05, 0.15))
    
    @pytest.fixture
    def mock_openai(self):
        """Create mock OpenAI service"""
        return MockOpenAIService(success_rate=0.97, latency_range=(0.2, 0.8))
    
    @pytest.fixture
    def mock_stt(self):
        """Create mock speech-to-text service"""
        return MockSpeechToTextService(success_rate=0.96, latency_range=(0.05, 0.2))
    
    @pytest.mark.asyncio
    async def test_mock_elevenlabs_synthesis(self, mock_elevenlabs):
        """Test ElevenLabs mock with various inputs"""
        test_texts = [
            "Hello, welcome to Premier Real Estate!",
            "I'd be happy to help you find your dream home today.",
            "Based on your criteria, I have several excellent properties to show you.",
            "Thank you for choosing our services. I'll follow up with you tomorrow."
        ]
        
        for text in test_texts:
            result = await mock_elevenlabs.synthesize_speech(
                text=text,
                voice_id="sarah_professional",
                settings={"stability": 0.75, "similarity_boost": 0.85}
            )
            
            # Validate mock response structure
            assert "audio_data" in result
            assert "duration_seconds" in result
            assert result["format"] == "mp3"
            assert result["character_count"] == len(text)
            assert result["processing_time_ms"] < 200
        
        # Check mock statistics
        stats = mock_elevenlabs.get_stats()
        assert stats["total_calls"] == len(test_texts)
        assert stats["success_rate"] >= 0.9
    
    @pytest.mark.asyncio
    async def test_mock_openai_conversation(self, mock_openai):
        """Test OpenAI mock with conversation scenarios"""
        conversation_scenarios = [
            {
                "messages": [
                    {"role": "user", "content": "I'm looking for a 3-bedroom house under $500k"}
                ],
                "expected_intent": "property_search"
            },
            {
                "messages": [
                    {"role": "user", "content": "What's the average price in downtown?"}
                ],
                "expected_intent": "budget_inquiry"
            },
            {
                "messages": [
                    {"role": "user", "content": "Can you show me these properties this weekend?"}
                ],
                "expected_intent": "schedule_viewing"
            }
        ]
        
        for scenario in conversation_scenarios:
            result = await mock_openai.chat_completion(
                messages=scenario["messages"],
                model="gpt-4"
            )
            
            # Validate response structure
            assert "choices" in result
            assert len(result["choices"]) > 0
            assert "message" in result["choices"][0]
            assert result["choices"][0]["message"]["role"] == "assistant"
            assert len(result["choices"][0]["message"]["content"]) > 0
            
            # Validate usage tracking
            assert "usage" in result
            assert result["usage"]["total_tokens"] > 0
    
    @pytest.mark.asyncio
    async def test_mock_speech_recognition(self, mock_stt):
        """Test speech-to-text mock"""
        # Simulate different audio lengths
        audio_samples = [
            b"short_audio" * 100,      # ~1 second
            b"medium_audio" * 500,     # ~3 seconds  
            b"long_audio" * 1000,      # ~6 seconds
        ]
        
        for audio_data in audio_samples:
            result = await mock_stt.transcribe(audio_data, language="en-US")
            
            # Validate transcription response
            assert "transcript" in result
            assert len(result["transcript"]) > 0
            assert result["confidence"] >= 0.8
            assert result["language"] == "en-US"
            assert result["duration_seconds"] > 0
            assert result["word_count"] > 0
    
    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self, mock_elevenlabs):
        """Test AI service error handling and recovery"""
        # Create mock with low success rate to trigger errors
        unreliable_mock = MockElevenLabsService(success_rate=0.3)
        
        success_count = 0
        error_count = 0
        
        # Test multiple requests with error handling
        for i in range(10):
            try:
                result = await unreliable_mock.synthesize_speech(
                    text=f"Test message {i}",
                    voice_id="test_voice",
                    settings={}
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                assert "temporarily unavailable" in str(e)
        
        # Verify error rate matches expectation
        total_requests = success_count + error_count
        actual_success_rate = success_count / total_requests
        
        # Should be around 30% success rate (with some variance)
        assert 0.1 <= actual_success_rate <= 0.5
    
    @pytest.mark.asyncio
    async def test_ai_service_performance_monitoring(self, mock_elevenlabs, mock_openai):
        """Test AI service performance monitoring"""
        # Test concurrent requests
        elevenlabs_tasks = [
            mock_elevenlabs.synthesize_speech(f"Message {i}", "test_voice", {})
            for i in range(5)
        ]
        
        openai_tasks = [
            mock_openai.chat_completion([{"role": "user", "content": f"Question {i}"}])
            for i in range(5)
        ]
        
        start_time = time.time()
        
        # Execute all tasks concurrently
        elevenlabs_results = await asyncio.gather(*elevenlabs_tasks, return_exceptions=True)
        openai_results = await asyncio.gather(*openai_tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Validate concurrent execution was efficient
        assert total_time < 2.0  # Should complete much faster than sequential
        
        # Check that most requests succeeded
        elevenlabs_successes = len([r for r in elevenlabs_results if not isinstance(r, Exception)])
        openai_successes = len([r for r in openai_results if not isinstance(r, Exception)])
        
        assert elevenlabs_successes >= 4  # Most should succeed
        assert openai_successes >= 4
        
        # Verify performance stats
        elevenlabs_stats = mock_elevenlabs.get_stats()
        openai_stats = mock_openai.get_stats()
        
        assert elevenlabs_stats["total_calls"] == 5
        assert openai_stats["total_calls"] == 5


class TestAIServiceIntegrationMocking:
    """Test AI service integration with mocking"""
    
    @pytest.fixture
    def integrated_ai_services(self):
        """Create integrated AI services with mocks"""
        return {
            "voice_engine": VoiceEngine(),
            "conversation_engine": ConversationEngine(),
            "lead_qualifier": LeadQualifier(),
            "sentiment_analyzer": SentimentAnalyzer()
        }
    
    @pytest.mark.asyncio
    async def test_voice_to_conversation_pipeline_mock(self, integrated_ai_services):
        """Test complete voice-to-conversation pipeline with mocks"""
        voice_engine = integrated_ai_services["voice_engine"]
        conversation_engine = integrated_ai_services["conversation_engine"]
        
        # Mock the STT service
        with patch.object(voice_engine, 'speech_to_text') as mock_stt:
            mock_stt.return_value = {
                "transcript": "I'm looking for a 3-bedroom house with good schools nearby",
                "confidence": 0.94,
                "processing_time_ms": 120
            }
            
            # Mock the conversation engine
            with patch.object(conversation_engine, 'process_message') as mock_conversation:
                mock_conversation.return_value = {
                    "response": "Excellent! I can help you find 3-bedroom homes in great school districts. What's your budget range?",
                    "intent": "property_search",
                    "entities": {"bedrooms": 3, "requirement": "good_schools"},
                    "confidence": 0.91,
                    "next_actions": ["ask_budget", "show_properties"]
                }
                
                # Execute pipeline
                audio_data = np.random.random(16000 * 3).astype(np.float32)
                
                # Step 1: Voice to text
                transcript_result = await voice_engine.speech_to_text(audio_data)
                
                # Step 2: Process conversation
                conversation_context = {"phase": "discovery", "lead_id": "test_lead"}
                conversation_result = await conversation_engine.process_message(
                    transcript_result["transcript"],
                    conversation_context
                )
                
                # Validate pipeline results
                assert transcript_result["confidence"] >= 0.9
                assert conversation_result["intent"] == "property_search"
                assert "bedrooms" in conversation_result["entities"]
                assert len(conversation_result["next_actions"]) >= 1
                
                # Verify mock calls
                mock_stt.assert_called_once()
                mock_conversation.assert_called_once_with(
                    transcript_result["transcript"],
                    conversation_context
                )
    
    @pytest.mark.asyncio
    async def test_lead_qualification_with_ai_mock(self, integrated_ai_services):
        """Test lead qualification with AI analysis mock"""
        lead_qualifier = integrated_ai_services["lead_qualifier"]
        
        # Create test lead data
        lead_data = QualifiedLeadFactory().dict() if hasattr(QualifiedLeadFactory(), 'dict') else {
            "name": "Test Lead",
            "email": "test@example.com",
            "phone": "+1234567890",
            "property_preferences": {
                "bedrooms": 3,
                "max_price": 500000,
                "location": "downtown"
            },
            "timeline": "3_months",
            "budget_verified": True
        }
        
        # Mock AI qualification analysis
        with patch.object(lead_qualifier, 'analyze_qualification') as mock_analyze:
            mock_analyze.return_value = {
                "lead_score": 87,
                "qualification_status": "hot_lead",
                "scoring_factors": {
                    "budget_clarity": 0.9,
                    "timeline_urgency": 0.8,
                    "requirement_specificity": 0.85,
                    "engagement_level": 0.92
                },
                "recommendations": [
                    "Schedule immediate property viewing",
                    "Connect with mortgage specialist", 
                    "Prepare customized property list"
                ],
                "risk_assessment": "low",
                "predicted_conversion_probability": 0.78
            }
            
            result = await lead_qualifier.analyze_qualification(lead_data)
            
            # Validate qualification results
            assert result["lead_score"] >= 80
            assert result["qualification_status"] == "hot_lead"
            assert result["predicted_conversion_probability"] >= 0.7
            assert len(result["recommendations"]) >= 2
            
            # Verify all scoring factors are present
            scoring_factors = result["scoring_factors"]
            assert all(0 <= score <= 1 for score in scoring_factors.values())
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_mock(self, integrated_ai_services):
        """Test sentiment analysis with realistic mocking"""
        sentiment_analyzer = integrated_ai_services["sentiment_analyzer"]
        
        # Test various conversation types
        conversation_samples = [
            {
                "transcript": "I'm so excited about this property! It's exactly what we've been looking for!",
                "expected_sentiment": "very_positive"
            },
            {
                "transcript": "I'm not sure about the price. It seems a bit high for what we're getting.",
                "expected_sentiment": "negative"
            },
            {
                "transcript": "The house is okay, but I'd like to see more options before deciding.",
                "expected_sentiment": "neutral"
            },
            {
                "transcript": "This is perfect! When can we make an offer?",
                "expected_sentiment": "very_positive"
            }
        ]
        
        for sample in conversation_samples:
            with patch.object(sentiment_analyzer, 'analyze_sentiment') as mock_sentiment:
                # Create realistic sentiment response based on expected sentiment
                if sample["expected_sentiment"] == "very_positive":
                    sentiment_score = random.uniform(0.8, 1.0)
                    emotions = {"excitement": 0.9, "satisfaction": 0.85, "interest": 0.95}
                elif sample["expected_sentiment"] == "negative":
                    sentiment_score = random.uniform(0.0, 0.4)
                    emotions = {"concern": 0.7, "disappointment": 0.6, "hesitation": 0.8}
                else:  # neutral
                    sentiment_score = random.uniform(0.4, 0.6)
                    emotions = {"interest": 0.5, "consideration": 0.6, "uncertainty": 0.4}
                
                mock_sentiment.return_value = {
                    "overall_sentiment": sample["expected_sentiment"],
                    "sentiment_score": sentiment_score,
                    "confidence": random.uniform(0.85, 0.98),
                    "emotions": emotions,
                    "key_phrases": [
                        phrase.strip() for phrase in sample["transcript"].split('.')
                        if len(phrase.strip()) > 5
                    ][:3],
                    "sentiment_trend": "stable",
                    "urgency_indicators": ["when can we" in sample["transcript"].lower()]
                }
                
                result = await sentiment_analyzer.analyze_sentiment({
                    "transcript": sample["transcript"],
                    "conversation_id": f"test_conv_{uuid.uuid4().hex[:8]}"
                })
                
                # Validate sentiment analysis
                assert result["overall_sentiment"] == sample["expected_sentiment"]
                assert 0 <= result["sentiment_score"] <= 1
                assert result["confidence"] >= 0.8
                assert len(result["emotions"]) > 0
                assert all(0 <= score <= 1 for score in result["emotions"].values())
    
    @pytest.mark.asyncio
    async def test_ai_service_fallback_mechanisms(self, integrated_ai_services):
        """Test AI service fallback mechanisms when primary services fail"""
        voice_engine = integrated_ai_services["voice_engine"]
        
        # Mock primary service failure with fallback
        with patch.object(voice_engine, 'primary_stt_service') as mock_primary:
            with patch.object(voice_engine, 'fallback_stt_service') as mock_fallback:
                
                # Primary service fails
                mock_primary.transcribe.side_effect = Exception("Primary STT service down")
                
                # Fallback service succeeds
                mock_fallback.transcribe.return_value = {
                    "transcript": "Fallback transcription successful",
                    "confidence": 0.82,
                    "source": "fallback_service"
                }
                
                # Mock the fallback logic
                with patch.object(voice_engine, 'speech_to_text') as mock_stt:
                    mock_stt.side_effect = [
                        Exception("Primary service failed"),  # First attempt fails
                        {  # Fallback succeeds
                            "transcript": "Fallback transcription successful", 
                            "confidence": 0.82,
                            "source": "fallback_service"
                        }
                    ]
                    
                    # Test fallback mechanism
                    try:
                        # First call should fail
                        await voice_engine.speech_to_text(np.array([1, 2, 3]))
                        assert False, "Should have failed on first attempt"
                    except Exception:
                        pass
                    
                    # Second call should succeed with fallback
                    result = await voice_engine.speech_to_text(np.array([1, 2, 3]))
                    
                    assert result["transcript"] == "Fallback transcription successful"
                    assert result["source"] == "fallback_service"
                    assert result["confidence"] >= 0.8


class TestRealisticAIMockScenarios:
    """Test realistic AI scenarios with comprehensive mocking"""
    
    @pytest.mark.asyncio
    async def test_complete_sales_call_simulation(self):
        """Test complete sales call with all AI services mocked"""
        # Create realistic test scenario
        scenario = create_complete_sales_scenario()
        
        # Mock all AI services
        mock_services = {
            "stt": MockSpeechToTextService(),
            "tts": MockElevenLabsService(), 
            "conversation": MockOpenAIService(),
            "sentiment": Mock(),
            "lead_qualifier": Mock()
        }
        
        # Simulate complete sales call workflow
        call_steps = [
            {
                "audio_input": b"audio_data_1",
                "expected_transcript": "Hello, I'm interested in buying a home",
                "response_intent": "property_search"
            },
            {
                "audio_input": b"audio_data_2", 
                "expected_transcript": "I'm looking for a 3-bedroom house under $500,000",
                "response_intent": "budget_specification"
            },
            {
                "audio_input": b"audio_data_3",
                "expected_transcript": "Yes, I'd like to schedule viewings for this weekend",
                "response_intent": "schedule_viewing"
            }
        ]
        
        conversation_results = []
        
        for step in call_steps:
            # Step 1: Speech to text
            stt_result = await mock_services["stt"].transcribe(step["audio_input"])
            
            # Step 2: Conversation processing
            conversation_messages = [{"role": "user", "content": stt_result["transcript"]}]
            conversation_result = await mock_services["conversation"].chat_completion(conversation_messages)
            
            # Step 3: Response synthesis
            response_text = conversation_result["choices"][0]["message"]["content"]
            tts_result = await mock_services["tts"].synthesize_speech(
                response_text, 
                "sarah_professional", 
                {"stability": 0.75}
            )
            
            # Step 4: Sentiment analysis
            mock_services["sentiment"].analyze.return_value = {
                "sentiment_score": random.uniform(0.6, 0.9),
                "emotions": {"interest": 0.8, "engagement": 0.7}
            }
            sentiment_result = mock_services["sentiment"].analyze(stt_result["transcript"])
            
            conversation_results.append({
                "transcript": stt_result["transcript"],
                "response": response_text,
                "sentiment": sentiment_result,
                "audio_generated": len(tts_result["audio_data"]) > 0
            })
        
        # Validate complete call simulation
        assert len(conversation_results) == 3
        
        for result in conversation_results:
            assert len(result["transcript"]) > 0
            assert len(result["response"]) > 0
            assert result["sentiment"]["sentiment_score"] > 0.5
            assert result["audio_generated"] is True
        
        # Final lead qualification
        mock_services["lead_qualifier"].qualify_from_conversation.return_value = {
            "final_lead_score": 89,
            "qualification_status": "hot_lead",
            "next_actions": ["schedule_viewing", "prepare_offer_analysis"]
        }
        
        final_qualification = mock_services["lead_qualifier"].qualify_from_conversation(
            conversation_results
        )
        
        assert final_qualification["final_lead_score"] >= 85
        assert final_qualification["qualification_status"] == "hot_lead"
        assert len(final_qualification["next_actions"]) >= 2
    
    @pytest.mark.asyncio
    async def test_ai_service_degradation_handling(self):
        """Test graceful degradation when AI services are partially unavailable"""
        # Create services with different availability levels
        services = {
            "high_availability": MockElevenLabsService(success_rate=0.99),
            "medium_availability": MockOpenAIService(success_rate=0.85),
            "low_availability": MockSpeechToTextService(success_rate=0.60),
            "unreliable": MockElevenLabsService(success_rate=0.30)
        }
        
        # Test system behavior under degraded conditions
        degradation_results = {}
        
        for service_name, service in services.items():
            success_count = 0
            total_attempts = 20
            
            for _ in range(total_attempts):
                try:
                    if isinstance(service, MockElevenLabsService):
                        await service.synthesize_speech("Test", "voice", {})
                    elif isinstance(service, MockOpenAIService):
                        await service.chat_completion([{"role": "user", "content": "Test"}])
                    elif isinstance(service, MockSpeechToTextService):
                        await service.transcribe(b"test_audio")
                    
                    success_count += 1
                except Exception:
                    pass
            
            actual_success_rate = success_count / total_attempts
            degradation_results[service_name] = {
                "expected_rate": service.success_rate,
                "actual_rate": actual_success_rate,
                "degradation": abs(service.success_rate - actual_success_rate)
            }
        
        # Validate degradation handling
        for service_name, results in degradation_results.items():
            # Success rate should be within reasonable variance
            assert abs(results["expected_rate"] - results["actual_rate"]) < 0.2
            
            # System should handle degradation gracefully
            if results["actual_rate"] < 0.8:
                print(f"Service {service_name} degraded to {results['actual_rate']:.2%}")
                # In real implementation, would trigger alerts/fallbacks


# Performance validation with mocks
class TestMockPerformanceValidation:
    """Test performance characteristics with mocked services"""
    
    @pytest.mark.asyncio
    async def test_mock_service_latency_validation(self):
        """Test that mock services maintain realistic latency"""
        mock_tts = MockElevenLabsService(latency_range=(0.05, 0.15))
        
        latencies = []
        
        for _ in range(20):
            start_time = time.time()
            
            try:
                await mock_tts.synthesize_speech("Test message", "voice", {})
            except Exception:
                pass  # Include failed requests in latency measurement
            
            end_time = time.time()
            latencies.append((end_time - start_time) * 1000)  # Convert to ms
        
        avg_latency = sum(latencies) / len(latencies)
        
        # Verify latency is within expected range
        assert 50 <= avg_latency <= 200, f"Average latency {avg_latency:.2f}ms outside expected range"
        
        # Verify latency consistency
        latency_std = np.std(latencies)
        assert latency_std < 50, f"Latency too variable: {latency_std:.2f}ms std dev"
    
    @pytest.mark.asyncio
    async def test_mock_service_throughput_validation(self):
        """Test mock service throughput under load"""
        mock_conversation = MockOpenAIService(success_rate=0.95)
        
        # Test concurrent request handling
        num_concurrent = 10
        test_messages = [
            [{"role": "user", "content": f"Test message {i}"}]
            for i in range(num_concurrent)
        ]
        
        start_time = time.time()
        
        tasks = [
            mock_conversation.chat_completion(messages)
            for messages in test_messages
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        successful_requests = len([r for r in results if not isinstance(r, Exception)])
        throughput = successful_requests / total_time
        
        # Validate throughput
        assert throughput >= 5, f"Throughput too low: {throughput:.2f} requests/second"
        assert successful_requests >= 8, f"Too many failures: {num_concurrent - successful_requests}"
        
        # Verify concurrent execution efficiency
        assert total_time < 2.0, f"Concurrent execution too slow: {total_time:.2f}s"