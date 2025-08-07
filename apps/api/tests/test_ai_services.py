"""
Comprehensive tests for AI services including voice processing, conversation AI,
and domain-specific intelligence services.
"""
import pytest
import asyncio
import json
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any
import io
import base64

from app.ai.voice.engine import VoiceEngine
from app.ai.voice.speech_to_text import SpeechToTextService
from app.ai.voice.text_to_speech import TextToSpeechService
from app.ai.voice.audio_processor import AudioProcessor
from app.ai.voice.voice_quality import VoiceQualityAnalyzer
from app.ai.voice.biometrics import VoiceBiometricsService

from app.ai.conversation.engine import ConversationEngine
from app.ai.conversation.context_manager import ContextManager
from app.ai.conversation.intent_recognition import IntentRecognizer
from app.ai.conversation.function_calling import FunctionCaller
from app.ai.conversation.flow_manager import FlowManager

from app.ai.domain.intelligence import DomainIntelligence
from app.ai.domain.lead_qualification import LeadQualifier
from app.ai.domain.property_recommendations import PropertyRecommender
from app.ai.domain.market_analysis import MarketAnalyzer
from app.ai.domain.scheduling import SchedulingService
from app.ai.domain.follow_up import FollowUpService

from app.ai.analytics.sentiment import SentimentAnalyzer
from app.ai.analytics.engagement import EngagementAnalyzer
from app.ai.analytics.performance import PerformanceAnalyzer
from app.ai.analytics.intelligence import IntelligenceAnalyzer


class TestVoiceEngine:
    """Test voice processing engine"""
    
    @pytest.fixture
    def voice_engine(self):
        """Create voice engine instance"""
        return VoiceEngine()
    
    @pytest.fixture
    def sample_audio_data(self):
        """Generate sample audio data for testing"""
        # Generate 3 seconds of sample audio at 16kHz
        duration = 3.0
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Generate a simple sine wave
        frequency = 440  # A4 note
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
        return audio_data.astype(np.float32)
    
    @pytest.mark.asyncio
    async def test_voice_engine_initialization(self, voice_engine):
        """Test voice engine initialization"""
        await voice_engine.initialize()
        assert voice_engine.is_initialized
        assert voice_engine.stt_service is not None
        assert voice_engine.tts_service is not None
        assert voice_engine.audio_processor is not None
    
    @pytest.mark.asyncio
    async def test_speech_to_text_processing(self, voice_engine, sample_audio_data):
        """Test speech-to-text processing"""
        await voice_engine.initialize()
        
        # Mock the STT service response
        with patch.object(voice_engine.stt_service, 'transcribe') as mock_transcribe:
            mock_transcribe.return_value = {
                "transcript": "Hello, I'm interested in buying a house",
                "confidence": 0.95,
                "language": "en-US",
                "duration_seconds": 3.0
            }
            
            result = await voice_engine.speech_to_text(sample_audio_data)
            
            assert result["transcript"] == "Hello, I'm interested in buying a house"
            assert result["confidence"] >= 0.9
            assert result["duration_seconds"] == 3.0
            mock_transcribe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_text_to_speech_synthesis(self, voice_engine):
        """Test text-to-speech synthesis"""
        await voice_engine.initialize()
        
        text = "Thank you for your interest. I can help you find the perfect home."
        voice_settings = {
            "voice_id": "sarah_professional",
            "pitch": 1.0,
            "speed": 1.0,
            "stability": 0.75
        }
        
        with patch.object(voice_engine.tts_service, 'synthesize') as mock_synthesize:
            mock_audio_data = b"fake_audio_bytes"
            mock_synthesize.return_value = {
                "audio_data": mock_audio_data,
                "format": "mp3",
                "sample_rate": 24000,
                "duration_seconds": 4.2
            }
            
            result = await voice_engine.text_to_speech(text, voice_settings)
            
            assert result["audio_data"] == mock_audio_data
            assert result["format"] == "mp3"
            assert result["duration_seconds"] > 0
            mock_synthesize.assert_called_once_with(text, voice_settings)
    
    @pytest.mark.asyncio
    async def test_real_time_voice_processing(self, voice_engine, sample_audio_data):
        """Test real-time voice processing pipeline"""
        await voice_engine.initialize()
        
        # Mock real-time processing
        with patch.object(voice_engine, 'process_audio_stream') as mock_process:
            mock_process.return_value = {
                "status": "processing",
                "detected_speech": True,
                "silence_duration": 0.5,
                "audio_quality": "good"
            }
            
            result = await voice_engine.process_audio_stream(sample_audio_data)
            
            assert result["status"] == "processing"
            assert result["detected_speech"] is True
            assert "audio_quality" in result
    
    @pytest.mark.asyncio
    async def test_voice_quality_analysis(self, voice_engine, sample_audio_data):
        """Test voice quality analysis"""
        await voice_engine.initialize()
        
        quality_analyzer = VoiceQualityAnalyzer()
        
        with patch.object(quality_analyzer, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                "overall_score": 8.5,
                "noise_level": "low",
                "clarity": "excellent",
                "volume": "optimal",
                "frequency_response": "balanced",
                "recommendations": []
            }
            
            result = await quality_analyzer.analyze(sample_audio_data)
            
            assert result["overall_score"] >= 8.0
            assert result["noise_level"] == "low"
            assert result["clarity"] == "excellent"
    
    @pytest.mark.asyncio
    async def test_voice_biometrics(self, voice_engine, sample_audio_data):
        """Test voice biometrics and speaker identification"""
        biometrics_service = VoiceBiometricsService()
        
        with patch.object(biometrics_service, 'extract_features') as mock_extract:
            mock_extract.return_value = {
                "voice_print": "voice_print_hash_123",
                "speaker_confidence": 0.92,
                "emotion": "neutral",
                "stress_level": "low",
                "gender": "female",
                "age_estimate": "25-35"
            }
            
            result = await biometrics_service.extract_features(sample_audio_data)
            
            assert result["speaker_confidence"] >= 0.9
            assert result["emotion"] in ["neutral", "positive", "negative"]
            assert result["stress_level"] in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, voice_engine, sample_audio_data):
        """Test voice processing performance benchmarks"""
        await voice_engine.initialize()
        
        # Test latency requirements
        start_time = datetime.utcnow()
        
        with patch.object(voice_engine.stt_service, 'transcribe') as mock_transcribe:
            mock_transcribe.return_value = {
                "transcript": "Test transcript",
                "confidence": 0.95,
                "duration_seconds": 3.0
            }
            
            result = await voice_engine.speech_to_text(sample_audio_data)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Voice processing should complete within 180ms
            assert processing_time < 0.18
            assert result["transcript"] is not None


class TestConversationEngine:
    """Test conversation AI engine"""
    
    @pytest.fixture
    def conversation_engine(self):
        """Create conversation engine instance"""
        return ConversationEngine()
    
    @pytest.fixture
    def sample_conversation_context(self):
        """Sample conversation context for testing"""
        return {
            "lead_id": "lead_123",
            "organization_id": "org_456",
            "conversation_history": [
                {"role": "assistant", "content": "Hello! How can I help you find your dream home today?"},
                {"role": "user", "content": "I'm looking for a 3-bedroom house in downtown"}
            ],
            "lead_preferences": {
                "bedrooms": 3,
                "location": "downtown",
                "budget_min": 300000,
                "budget_max": 500000
            },
            "current_phase": "discovery"
        }
    
    @pytest.mark.asyncio
    async def test_conversation_engine_initialization(self, conversation_engine):
        """Test conversation engine initialization"""
        await conversation_engine.initialize()
        assert conversation_engine.is_initialized
        assert conversation_engine.intent_recognizer is not None
        assert conversation_engine.context_manager is not None
        assert conversation_engine.function_caller is not None
    
    @pytest.mark.asyncio
    async def test_intent_recognition(self, conversation_engine):
        """Test intent recognition from user input"""
        await conversation_engine.initialize()
        
        test_messages = [
            {
                "text": "I want to buy a house with 3 bedrooms",
                "expected_intent": "property_search",
                "expected_entities": {"bedrooms": 3}
            },
            {
                "text": "Can you schedule a viewing for tomorrow?",
                "expected_intent": "schedule_viewing",
                "expected_entities": {"date": "tomorrow"}
            },
            {
                "text": "What's my budget options?",
                "expected_intent": "budget_inquiry",
                "expected_entities": {}
            }
        ]
        
        for message in test_messages:
            with patch.object(conversation_engine.intent_recognizer, 'recognize') as mock_recognize:
                mock_recognize.return_value = {
                    "intent": message["expected_intent"],
                    "confidence": 0.95,
                    "entities": message["expected_entities"]
                }
                
                result = await conversation_engine.intent_recognizer.recognize(message["text"])
                
                assert result["intent"] == message["expected_intent"]
                assert result["confidence"] >= 0.9
                assert result["entities"] == message["expected_entities"]
    
    @pytest.mark.asyncio
    async def test_context_management(self, conversation_engine, sample_conversation_context):
        """Test conversation context management"""
        context_manager = ContextManager()
        
        # Test context storage and retrieval
        await context_manager.save_context("conv_123", sample_conversation_context)
        retrieved_context = await context_manager.get_context("conv_123")
        
        assert retrieved_context["lead_id"] == sample_conversation_context["lead_id"]
        assert retrieved_context["current_phase"] == "discovery"
        assert len(retrieved_context["conversation_history"]) == 2
    
    @pytest.mark.asyncio
    async def test_conversation_flow_management(self, conversation_engine, sample_conversation_context):
        """Test conversation flow management"""
        flow_manager = FlowManager()
        
        with patch.object(flow_manager, 'determine_next_action') as mock_determine:
            mock_determine.return_value = {
                "action": "ask_budget",
                "response": "What's your budget range for this property?",
                "next_phase": "qualification",
                "data_needed": ["budget_min", "budget_max"]
            }
            
            result = await flow_manager.determine_next_action(sample_conversation_context)
            
            assert result["action"] == "ask_budget"
            assert result["next_phase"] == "qualification"
            assert "budget_min" in result["data_needed"]
    
    @pytest.mark.asyncio
    async def test_function_calling(self, conversation_engine):
        """Test AI function calling capabilities"""
        function_caller = FunctionCaller()
        
        # Mock available functions
        available_functions = {
            "search_properties": {
                "description": "Search for properties matching criteria",
                "parameters": {
                    "bedrooms": {"type": "integer"},
                    "location": {"type": "string"},
                    "max_price": {"type": "integer"}
                }
            },
            "schedule_viewing": {
                "description": "Schedule a property viewing",
                "parameters": {
                    "property_id": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"}
                }
            }
        }
        
        with patch.object(function_caller, 'call_function') as mock_call:
            mock_call.return_value = {
                "function_name": "search_properties",
                "parameters": {"bedrooms": 3, "location": "downtown", "max_price": 500000},
                "result": {
                    "properties": [
                        {"id": "prop_1", "address": "123 Main St", "price": 425000},
                        {"id": "prop_2", "address": "456 Oak Ave", "price": 475000}
                    ],
                    "total_found": 2
                }
            }
            
            result = await function_caller.call_function(
                "search_properties",
                {"bedrooms": 3, "location": "downtown", "max_price": 500000}
            )
            
            assert result["function_name"] == "search_properties"
            assert len(result["result"]["properties"]) == 2
    
    @pytest.mark.asyncio
    async def test_conversation_response_generation(self, conversation_engine, sample_conversation_context):
        """Test AI response generation"""
        await conversation_engine.initialize()
        
        user_input = "I'm interested in a 3-bedroom house with a budget of $400,000"
        
        with patch.object(conversation_engine, 'generate_response') as mock_generate:
            mock_generate.return_value = {
                "response": "Perfect! I can help you find a 3-bedroom home within your $400,000 budget. Let me search our available properties in your preferred area. Are you looking for any specific neighborhood or features?",
                "intent": "property_search",
                "next_questions": ["neighborhood_preference", "special_features"],
                "context_updates": {
                    "budget_max": 400000,
                    "bedrooms": 3
                },
                "suggested_actions": ["search_properties", "ask_preferences"]
            }
            
            result = await conversation_engine.generate_response(user_input, sample_conversation_context)
            
            assert "Perfect!" in result["response"]
            assert result["intent"] == "property_search"
            assert "search_properties" in result["suggested_actions"]
    
    @pytest.mark.asyncio
    async def test_conversation_performance(self, conversation_engine, sample_conversation_context):
        """Test conversation processing performance"""
        await conversation_engine.initialize()
        
        start_time = datetime.utcnow()
        
        with patch.object(conversation_engine, 'process_message') as mock_process:
            mock_process.return_value = {
                "response": "Thank you for your interest!",
                "processing_time_ms": 45
            }
            
            result = await conversation_engine.process_message(
                "I need help finding a home",
                sample_conversation_context
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Conversation processing should be under 100ms
            assert processing_time < 0.1
            assert result["processing_time_ms"] < 50


class TestDomainIntelligence:
    """Test real estate domain-specific AI services"""
    
    @pytest.fixture
    def lead_qualifier(self):
        """Create lead qualifier instance"""
        return LeadQualifier()
    
    @pytest.fixture
    def property_recommender(self):
        """Create property recommender instance"""
        return PropertyRecommender()
    
    @pytest.fixture
    def market_analyzer(self):
        """Create market analyzer instance"""
        return MarketAnalyzer()
    
    @pytest.fixture
    def sample_lead_data(self):
        """Sample lead data for qualification testing"""
        return {
            "id": "lead_123",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "property_preferences": {
                "type": "single_family",
                "bedrooms": 3,
                "bathrooms": 2,
                "min_price": 300000,
                "max_price": 500000,
                "location": "downtown"
            },
            "timeline": "3_months",
            "pre_approved": False,
            "first_time_buyer": True,
            "current_situation": "renting"
        }
    
    @pytest.mark.asyncio
    async def test_lead_qualification_scoring(self, lead_qualifier, sample_lead_data):
        """Test lead qualification and scoring"""
        with patch.object(lead_qualifier, 'qualify_lead') as mock_qualify:
            mock_qualify.return_value = {
                "lead_score": 78,
                "qualification_status": "qualified",
                "qualification_factors": {
                    "budget_confirmed": True,
                    "timeline_defined": True,
                    "needs_clear": True,
                    "contact_responsive": True,
                    "pre_approved": False
                },
                "next_steps": [
                    "connect_with_lender",
                    "schedule_property_viewing",
                    "discuss_neighborhoods"
                ],
                "risk_factors": ["first_time_buyer", "not_pre_approved"],
                "opportunity_score": 85
            }
            
            result = await lead_qualifier.qualify_lead(sample_lead_data)
            
            assert result["lead_score"] >= 70  # Qualified threshold
            assert result["qualification_status"] == "qualified"
            assert len(result["next_steps"]) >= 2
            assert result["opportunity_score"] >= 80
    
    @pytest.mark.asyncio
    async def test_property_recommendations(self, property_recommender, sample_lead_data):
        """Test property recommendation engine"""
        available_properties = [
            {
                "id": "prop_1",
                "address": "123 Main St",
                "price": 425000,
                "bedrooms": 3,
                "bathrooms": 2,
                "square_feet": 2200,
                "location": "downtown",
                "features": ["garage", "updated_kitchen"]
            },
            {
                "id": "prop_2", 
                "address": "456 Oak Ave",
                "price": 375000,
                "bedrooms": 3,
                "bathrooms": 2,
                "square_feet": 1900,
                "location": "downtown",
                "features": ["pool", "large_yard"]
            }
        ]
        
        with patch.object(property_recommender, 'recommend') as mock_recommend:
            mock_recommend.return_value = {
                "recommended_properties": [
                    {
                        "property": available_properties[0],
                        "match_score": 92,
                        "match_reasons": [
                            "Exact bedroom match",
                            "Within budget range",
                            "Preferred location",
                            "Updated kitchen feature"
                        ]
                    },
                    {
                        "property": available_properties[1],
                        "match_score": 87,
                        "match_reasons": [
                            "Exact bedroom match",
                            "Within budget range",
                            "Preferred location"
                        ]
                    }
                ],
                "recommendation_strategy": "preference_based",
                "total_matches": 2
            }
            
            result = await property_recommender.recommend(
                sample_lead_data["property_preferences"],
                available_properties
            )
            
            assert len(result["recommended_properties"]) == 2
            assert result["recommended_properties"][0]["match_score"] >= 90
            assert "Exact bedroom match" in result["recommended_properties"][0]["match_reasons"]
    
    @pytest.mark.asyncio
    async def test_market_analysis(self, market_analyzer):
        """Test market analysis and insights"""
        market_request = {
            "location": "downtown",
            "property_type": "single_family",
            "bedrooms": 3,
            "analysis_type": "comprehensive"
        }
        
        with patch.object(market_analyzer, 'analyze_market') as mock_analyze:
            mock_analyze.return_value = {
                "market_summary": {
                    "average_price": 445000,
                    "median_price": 425000,
                    "price_per_sqft": 202,
                    "days_on_market": 28,
                    "inventory_level": "balanced"
                },
                "price_trends": {
                    "3_month_change": 2.3,
                    "6_month_change": 5.7,
                    "year_over_year": 8.2,
                    "trend_direction": "increasing"
                },
                "comparable_sales": [
                    {"address": "789 Pine St", "price": 435000, "date_sold": "2024-01-15"},
                    {"address": "321 Elm Ave", "price": 455000, "date_sold": "2024-01-22"}
                ],
                "market_insights": [
                    "Strong seller's market conditions",
                    "Low inventory driving competition",
                    "Prices trending upward"
                ],
                "investment_rating": "good"
            }
            
            result = await market_analyzer.analyze_market(market_request)
            
            assert result["market_summary"]["average_price"] > 0
            assert result["price_trends"]["trend_direction"] in ["increasing", "decreasing", "stable"]
            assert len(result["comparable_sales"]) >= 2
            assert result["investment_rating"] in ["excellent", "good", "fair", "poor"]
    
    @pytest.mark.asyncio
    async def test_scheduling_service(self):
        """Test appointment scheduling intelligence"""
        scheduling_service = SchedulingService()
        
        request = {
            "lead_id": "lead_123",
            "property_id": "prop_456",
            "preferred_times": ["weekday_morning", "weekend_afternoon"],
            "duration_minutes": 60,
            "type": "property_viewing"
        }
        
        with patch.object(scheduling_service, 'find_available_slots') as mock_find:
            mock_find.return_value = {
                "available_slots": [
                    {"date": "2024-01-15", "time": "10:00", "agent_id": "agent_1"},
                    {"date": "2024-01-15", "time": "14:00", "agent_id": "agent_2"},
                    {"date": "2024-01-16", "time": "09:00", "agent_id": "agent_1"}
                ],
                "recommended_slot": {
                    "date": "2024-01-15",
                    "time": "10:00",
                    "agent_id": "agent_1",
                    "match_score": 95
                },
                "scheduling_notes": "Morning slot matches lead preference"
            }
            
            result = await scheduling_service.find_available_slots(request)
            
            assert len(result["available_slots"]) >= 2
            assert result["recommended_slot"]["match_score"] >= 90
            assert "agent_id" in result["recommended_slot"]
    
    @pytest.mark.asyncio
    async def test_follow_up_automation(self):
        """Test intelligent follow-up service"""
        follow_up_service = FollowUpService()
        
        lead_context = {
            "lead_id": "lead_123",
            "last_contact": "2024-01-10T10:00:00Z",
            "conversation_history": [
                {"date": "2024-01-10", "type": "initial_call", "outcome": "interested"},
                {"date": "2024-01-08", "type": "email", "outcome": "opened"}
            ],
            "current_stage": "nurturing",
            "lead_score": 75,
            "preferences": {"contact_method": "phone", "best_time": "morning"}
        }
        
        with patch.object(follow_up_service, 'generate_follow_up_plan') as mock_plan:
            mock_plan.return_value = {
                "next_contact_date": "2024-01-12T10:00:00Z",
                "contact_method": "phone",
                "message_template": "follow_up_interested_lead",
                "priority": "high",
                "follow_up_sequence": [
                    {"days": 2, "method": "phone", "template": "follow_up_interested_lead"},
                    {"days": 5, "method": "email", "template": "property_updates"},
                    {"days": 10, "method": "text", "template": "check_in_brief"}
                ],
                "automation_triggers": ["property_match", "price_change", "open_house"]
            }
            
            result = await follow_up_service.generate_follow_up_plan(lead_context)
            
            assert result["priority"] in ["high", "medium", "low"]
            assert result["contact_method"] in ["phone", "email", "text"]
            assert len(result["follow_up_sequence"]) >= 2


class TestAnalyticsServices:
    """Test analytics and intelligence services"""
    
    @pytest.fixture
    def sentiment_analyzer(self):
        """Create sentiment analyzer instance"""
        return SentimentAnalyzer()
    
    @pytest.fixture
    def engagement_analyzer(self):
        """Create engagement analyzer instance"""
        return EngagementAnalyzer()
    
    @pytest.fixture
    def performance_analyzer(self):
        """Create performance analyzer instance"""
        return PerformanceAnalyzer()
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, sentiment_analyzer):
        """Test conversation sentiment analysis"""
        conversation_data = {
            "transcript": "I'm really excited about this property! It seems perfect for my family. Can we schedule a viewing soon?",
            "conversation_id": "conv_123",
            "duration_seconds": 180
        }
        
        with patch.object(sentiment_analyzer, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                "overall_sentiment": "positive",
                "sentiment_score": 0.85,
                "emotion_breakdown": {
                    "excitement": 0.7,
                    "interest": 0.9,
                    "satisfaction": 0.6,
                    "urgency": 0.4
                },
                "key_phrases": ["really excited", "perfect for my family", "schedule a viewing"],
                "sentiment_progression": [
                    {"timeframe": "0-60s", "sentiment": 0.8},
                    {"timeframe": "60-120s", "sentiment": 0.9},
                    {"timeframe": "120-180s", "sentiment": 0.85}
                ]
            }
            
            result = await sentiment_analyzer.analyze(conversation_data)
            
            assert result["overall_sentiment"] == "positive"
            assert result["sentiment_score"] >= 0.8
            assert len(result["key_phrases"]) >= 2
            assert result["emotion_breakdown"]["interest"] >= 0.8
    
    @pytest.mark.asyncio
    async def test_engagement_analysis(self, engagement_analyzer):
        """Test conversation engagement analysis"""
        conversation_metrics = {
            "conversation_id": "conv_123",
            "duration_seconds": 420,
            "turn_count": 12,
            "lead_talk_time": 240,
            "agent_talk_time": 180,
            "interruptions": 2,
            "questions_asked": 8,
            "questions_answered": 6
        }
        
        with patch.object(engagement_analyzer, 'analyze_engagement') as mock_analyze:
            mock_analyze.return_value = {
                "engagement_score": 8.2,
                "engagement_level": "high",
                "talk_ratio": 0.57,  # Lead talked 57% of the time
                "interaction_quality": {
                    "responsiveness": 0.9,
                    "question_engagement": 0.8,
                    "conversation_flow": 0.85
                },
                "engagement_indicators": [
                    "Active participation",
                    "Asking detailed questions",
                    "Providing specific preferences"
                ],
                "areas_for_improvement": [
                    "Reduce agent talk time slightly"
                ]
            }
            
            result = await engagement_analyzer.analyze_engagement(conversation_metrics)
            
            assert result["engagement_score"] >= 8.0
            assert result["engagement_level"] == "high"
            assert 0.5 <= result["talk_ratio"] <= 0.7  # Healthy balance
            assert len(result["engagement_indicators"]) >= 2
    
    @pytest.mark.asyncio
    async def test_performance_analysis(self, performance_analyzer):
        """Test agent and system performance analysis"""
        performance_data = {
            "agent_id": "agent_123",
            "time_period": "2024-01-01 to 2024-01-31",
            "conversations": [
                {"id": "conv_1", "duration": 300, "outcome": "qualified", "lead_score": 85},
                {"id": "conv_2", "duration": 180, "outcome": "interested", "lead_score": 70},
                {"id": "conv_3", "duration": 450, "outcome": "qualified", "lead_score": 90}
            ]
        }
        
        with patch.object(performance_analyzer, 'analyze_agent_performance') as mock_analyze:
            mock_analyze.return_value = {
                "overall_rating": 9.1,
                "total_conversations": 3,
                "qualification_rate": 0.67,
                "average_call_duration": 310,
                "average_lead_score": 81.67,
                "performance_metrics": {
                    "conversion_rate": 0.67,
                    "engagement_score": 8.5,
                    "customer_satisfaction": 9.2,
                    "response_time_avg": 0.12
                },
                "strengths": [
                    "High lead qualification rate",
                    "Excellent customer satisfaction",
                    "Fast response times"
                ],
                "improvement_areas": [
                    "Optimize call duration for efficiency"
                ],
                "benchmark_comparison": {
                    "vs_team_average": "+15%",
                    "vs_industry_standard": "+22%"
                }
            }
            
            result = await performance_analyzer.analyze_agent_performance(performance_data)
            
            assert result["overall_rating"] >= 9.0
            assert result["qualification_rate"] >= 0.6
            assert result["average_lead_score"] >= 80
            assert len(result["strengths"]) >= 2
    
    @pytest.mark.asyncio
    async def test_intelligence_insights(self):
        """Test AI-powered business intelligence"""
        intelligence_analyzer = IntelligenceAnalyzer()
        
        business_data = {
            "organization_id": "org_123",
            "time_period": "Q1_2024",
            "metrics": {
                "total_leads": 150,
                "qualified_leads": 95,
                "conversations": 220,
                "appointments_scheduled": 45,
                "deals_closed": 12
            }
        }
        
        with patch.object(intelligence_analyzer, 'generate_insights') as mock_insights:
            mock_insights.return_value = {
                "key_insights": [
                    "Lead qualification rate improved 15% this quarter",
                    "Voice AI conversations show 23% higher engagement",
                    "Peak calling times: 10-11 AM and 2-3 PM"
                ],
                "actionable_recommendations": [
                    "Increase calling capacity during peak hours",
                    "Focus on follow-up automation for qualified leads",
                    "Implement advanced lead scoring model"
                ],
                "performance_trends": {
                    "lead_volume": "increasing",
                    "qualification_rate": "stable_high",
                    "conversion_rate": "improving"
                },
                "predictive_insights": {
                    "next_month_leads": 175,
                    "expected_qualifications": 110,
                    "projected_closings": 15
                },
                "roi_analysis": {
                    "voice_ai_roi": 340,
                    "cost_per_qualified_lead": 85,
                    "revenue_per_conversation": 450
                }
            }
            
            result = await intelligence_analyzer.generate_insights(business_data)
            
            assert len(result["key_insights"]) >= 3
            assert len(result["actionable_recommendations"]) >= 3
            assert result["roi_analysis"]["voice_ai_roi"] > 300
            assert result["predictive_insights"]["next_month_leads"] > 0


class TestAIServiceIntegration:
    """Test integration between AI services"""
    
    @pytest.mark.asyncio
    async def test_voice_to_conversation_pipeline(self):
        """Test complete voice-to-conversation processing pipeline"""
        voice_engine = VoiceEngine()
        conversation_engine = ConversationEngine()
        
        await voice_engine.initialize()
        await conversation_engine.initialize()
        
        # Mock audio input
        audio_data = np.random.random(16000 * 3).astype(np.float32)  # 3 seconds
        
        # Mock voice processing
        with patch.object(voice_engine, 'speech_to_text') as mock_stt:
            mock_stt.return_value = {
                "transcript": "I'm looking for a family home with good schools nearby",
                "confidence": 0.94
            }
            
            # Mock conversation processing
            with patch.object(conversation_engine, 'process_message') as mock_process:
                mock_process.return_value = {
                    "response": "I'd be happy to help you find a family-friendly home near excellent schools. What's your preferred budget range?",
                    "intent": "property_search",
                    "next_phase": "budget_qualification"
                }
                
                # Process voice input
                transcript_result = await voice_engine.speech_to_text(audio_data)
                
                # Process conversation
                conversation_result = await conversation_engine.process_message(
                    transcript_result["transcript"],
                    {"phase": "discovery"}
                )
                
                assert transcript_result["confidence"] >= 0.9
                assert conversation_result["intent"] == "property_search"
                assert "budget" in conversation_result["response"].lower()
    
    @pytest.mark.asyncio
    async def test_end_to_end_ai_workflow(self):
        """Test complete end-to-end AI workflow"""
        # Initialize all services
        voice_engine = VoiceEngine()
        conversation_engine = ConversationEngine()
        lead_qualifier = LeadQualifier()
        sentiment_analyzer = SentimentAnalyzer()
        
        await voice_engine.initialize()
        await conversation_engine.initialize()
        
        # Simulate complete conversation workflow
        conversation_data = {
            "audio_input": np.random.random(16000 * 5).astype(np.float32),
            "lead_context": {
                "id": "lead_123",
                "preferences": {"bedrooms": 3, "budget_max": 500000}
            }
        }
        
        # Mock the entire pipeline
        with patch.object(voice_engine, 'speech_to_text') as mock_stt, \
             patch.object(conversation_engine, 'generate_response') as mock_conversation, \
             patch.object(lead_qualifier, 'update_qualification') as mock_qualify, \
             patch.object(sentiment_analyzer, 'analyze') as mock_sentiment:
            
            # Voice processing
            mock_stt.return_value = {
                "transcript": "Yes, I'm pre-approved for up to $450,000 and ready to buy within 60 days",
                "confidence": 0.96
            }
            
            # Conversation processing
            mock_conversation.return_value = {
                "response": "Excellent! Being pre-approved puts you in a strong position. Let me find properties in your price range.",
                "intent": "budget_confirmation",
                "context_updates": {"pre_approved": True, "timeline": "60_days"}
            }
            
            # Lead qualification update
            mock_qualify.return_value = {
                "lead_score": 92,
                "qualification_status": "hot_lead",
                "priority": "high"
            }
            
            # Sentiment analysis
            mock_sentiment.return_value = {
                "sentiment_score": 0.88,
                "engagement_level": "high"
            }
            
            # Execute workflow
            transcript = await voice_engine.speech_to_text(conversation_data["audio_input"])
            response = await conversation_engine.generate_response(
                transcript["transcript"],
                conversation_data["lead_context"]
            )
            qualification = await lead_qualifier.update_qualification(
                conversation_data["lead_context"]["id"],
                response["context_updates"]
            )
            sentiment = await sentiment_analyzer.analyze({
                "transcript": transcript["transcript"]
            })
            
            # Verify complete workflow
            assert transcript["confidence"] >= 0.95
            assert response["intent"] == "budget_confirmation"
            assert qualification["lead_score"] >= 90
            assert sentiment["sentiment_score"] >= 0.85
            assert qualification["qualification_status"] == "hot_lead"
    
    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self):
        """Test error handling across AI services"""
        voice_engine = VoiceEngine()
        
        # Test graceful handling of service failures
        with patch.object(voice_engine, 'speech_to_text') as mock_stt:
            mock_stt.side_effect = Exception("Service temporarily unavailable")
            
            try:
                await voice_engine.speech_to_text(np.array([]))
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Service temporarily unavailable" in str(e)
    
    @pytest.mark.asyncio
    async def test_ai_service_performance_monitoring(self):
        """Test AI service performance monitoring"""
        voice_engine = VoiceEngine()
        await voice_engine.initialize()
        
        # Monitor performance metrics
        with patch.object(voice_engine, 'get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "average_processing_time": 0.045,  # 45ms
                "success_rate": 0.998,
                "throughput_per_minute": 75,
                "error_rate": 0.002,
                "service_health": "excellent"
            }
            
            metrics = await voice_engine.get_performance_metrics()
            
            assert metrics["average_processing_time"] < 0.18  # Under 180ms requirement
            assert metrics["success_rate"] >= 0.99
            assert metrics["error_rate"] < 0.01
            assert metrics["service_health"] == "excellent"