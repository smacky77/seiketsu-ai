"""
Comprehensive unit tests for Conversation AI Engine
Tests conversation processing, function calling, and AI interactions
"""
import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from app.ai.conversation.engine import (
    ConversationAI, ConversationState, ConversationMessage, 
    ConversationTurn
)


@pytest.mark.asyncio
@pytest.mark.ai
@pytest.mark.unit
class TestConversationAI:
    """Test suite for ConversationAI functionality"""

    @pytest.fixture
    async def conversation_ai(self):
        """Create ConversationAI instance with mocked dependencies"""
        with patch('app.ai.conversation.engine.AsyncOpenAI') as mock_openai, \
             patch('app.ai.conversation.engine.ConversationContextManager') as mock_context, \
             patch('app.ai.conversation.engine.IntentRecognizer') as mock_intent, \
             patch('app.ai.conversation.engine.FunctionCallHandler') as mock_function, \
             patch('app.ai.conversation.engine.ConversationFlowManager') as mock_flow:
            
            # Setup mocks
            mock_openai.return_value = AsyncMock()
            mock_context.return_value = AsyncMock()
            mock_intent.return_value = AsyncMock()
            mock_function.return_value = AsyncMock()
            mock_flow.return_value = AsyncMock()
            
            ai = ConversationAI()
            await ai.initialize()
            
            yield ai

    @pytest.fixture
    def sample_conversation_context(self):
        """Sample conversation context for testing"""
        return {
            "conversation_id": "test_conv_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": time.time()},
                {"role": "assistant", "content": "Hi! How can I help?", "timestamp": time.time()}
            ],
            "session_data": {
                "properties_viewed": [],
                "budget_discussed": False,
                "contact_captured": False
            }
        }

    @pytest.fixture
    def mock_intent_result(self):
        """Mock intent recognition result"""
        return Mock(
            intent="property_search",
            confidence=0.85,
            requires_function_call=True,
            entities={
                "property_type": "house",
                "budget": "400k",
                "bedrooms": "3"
            }
        )

    async def test_initialize_success(self, conversation_ai):
        """Test successful ConversationAI initialization"""
        assert conversation_ai.client is not None
        assert conversation_ai.context_manager is not None
        assert conversation_ai.intent_recognizer is not None
        assert conversation_ai.function_handler is not None
        assert conversation_ai.flow_manager is not None
        assert conversation_ai.max_context_turns > 0
        assert conversation_ai.function_calling_enabled is not None

    async def test_process_conversation_turn_success(self, conversation_ai, sample_conversation_context, mock_intent_result):
        """Test successful conversation turn processing"""
        user_input = "I'm looking for a 3-bedroom house under $400k"
        conversation_id = "test_conv_123"
        user_id = "user_456"
        tenant_id = "tenant_789"
        
        # Mock component responses
        conversation_ai.context_manager.get_context.return_value = sample_conversation_context
        conversation_ai.intent_recognizer.recognize_intent.return_value = mock_intent_result
        conversation_ai.function_handler.get_available_functions.return_value = [
            {
                "name": "search_properties",
                "description": "Search for properties",
                "parameters": {}
            }
        ]
        
        # Mock OpenAI response
        mock_message = Mock()
        mock_message.content = "I found several 3-bedroom houses in your budget. Would you like to see them?"
        mock_message.function_call = None
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = Mock(total_tokens=150, prompt_tokens=100, completion_tokens=50)
        
        conversation_ai.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Process conversation turn
        start_time = time.time()
        result = await conversation_ai.process_conversation_turn(
            user_input, conversation_id, user_id, tenant_id
        )
        processing_time = (time.time() - start_time) * 1000
        
        # Verify result structure
        assert isinstance(result, ConversationTurn)
        assert result.success is True
        assert result.user_message.content == user_input
        assert result.user_message.role == "user"
        assert result.assistant_response.content == mock_message.content
        assert result.assistant_response.role == "assistant"
        assert result.intent == "property_search"
        assert result.confidence == 0.85
        assert result.processing_time_ms <= processing_time + 100  # Some tolerance
        assert result.tokens_used == 150
        
        # Verify component interactions
        conversation_ai.context_manager.get_context.assert_called_once_with(
            conversation_id, user_id, tenant_id
        )
        conversation_ai.intent_recognizer.recognize_intent.assert_called_once()
        conversation_ai.context_manager.add_turn.assert_called_once()
        conversation_ai.flow_manager.update_flow_state.assert_called_once()

    async def test_process_conversation_turn_with_function_call(self, conversation_ai, sample_conversation_context, mock_intent_result):
        """Test conversation turn with function calling"""
        user_input = "Show me houses in downtown area"
        
        # Mock function call scenario
        mock_function_call = Mock()
        mock_function_call.name = "search_properties"
        mock_function_call.arguments = '{"location": "downtown", "property_type": "house"}'
        
        # Mock initial OpenAI response with function call
        mock_initial_message = Mock()
        mock_initial_message.content = None
        mock_initial_message.function_call = mock_function_call
        
        mock_initial_response = Mock()
        mock_initial_response.choices = [Mock(message=mock_initial_message)]
        mock_initial_response.usage = Mock(total_tokens=100, prompt_tokens=80, completion_tokens=20)
        
        # Mock final OpenAI response after function execution
        mock_final_message = Mock()
        mock_final_message.content = "I found 5 houses in downtown. Here are the top matches..."
        mock_final_message.function_call = None
        
        mock_final_response = Mock()
        mock_final_response.choices = [Mock(message=mock_final_message)]
        mock_final_response.usage = Mock(total_tokens=75, prompt_tokens=50, completion_tokens=25)
        
        # Setup mocks
        conversation_ai.context_manager.get_context.return_value = sample_conversation_context
        conversation_ai.intent_recognizer.recognize_intent.return_value = mock_intent_result
        conversation_ai.function_handler.get_available_functions.return_value = [{"name": "search_properties"}]
        conversation_ai.function_handler.execute_function.return_value = {
            "properties": [{"id": "prop1", "address": "123 Main St"}],
            "count": 5
        }
        
        # Mock OpenAI calls (initial with function call, then final response)
        conversation_ai.client.chat.completions.create = AsyncMock(
            side_effect=[mock_initial_response, mock_final_response]
        )
        
        result = await conversation_ai.process_conversation_turn(
            user_input, "conv_id", "user_id", "tenant_id"
        )
        
        # Verify function calling
        assert result.success is True
        assert len(result.function_calls) == 1
        assert result.function_calls[0]["name"] == "search_properties"
        assert "downtown" in result.function_calls[0]["arguments"]
        assert result.assistant_response.content == mock_final_message.content
        assert result.tokens_used == 175  # Sum of both requests
        
        # Verify function execution
        conversation_ai.function_handler.execute_function.assert_called_once_with(
            "search_properties",
            {"location": "downtown", "property_type": "house"},
            "user_id",
            "tenant_id"
        )

    async def test_process_conversation_turn_error_handling(self, conversation_ai, sample_conversation_context):
        """Test error handling in conversation processing"""
        user_input = "Test error handling"
        
        # Mock error in intent recognition
        conversation_ai.context_manager.get_context.return_value = sample_conversation_context
        conversation_ai.intent_recognizer.recognize_intent.side_effect = Exception("Intent recognition failed")
        
        result = await conversation_ai.process_conversation_turn(
            user_input, "conv_id", "user_id", "tenant_id"
        )
        
        # Verify error handling
        assert result.success is False
        assert result.error == "Intent recognition failed"
        assert result.assistant_response.content.startswith("I apologize")
        assert result.processing_time_ms > 0

    async def test_stream_conversation_response(self, conversation_ai, sample_conversation_context):
        """Test streaming conversation response"""
        user_input = "Tell me about available properties"
        
        # Mock streaming response
        async def mock_stream():
            chunks = ["I", " found", " several", " properties", " for", " you."]
            for chunk in chunks:
                yield Mock(choices=[Mock(delta=Mock(content=chunk))])
        
        conversation_ai.context_manager.get_context.return_value = sample_conversation_context
        conversation_ai.client.chat.completions.create = AsyncMock(return_value=mock_stream())
        
        response_chunks = []
        async for chunk in conversation_ai.stream_conversation_response(
            user_input, "conv_id", "user_id", "tenant_id"
        ):
            response_chunks.append(chunk)
        
        # Verify streaming
        full_response = "".join(response_chunks)
        assert "found several properties" in full_response
        assert len(response_chunks) >= 6
        
        # Verify context was updated
        conversation_ai.context_manager.add_turn.assert_called_once()

    async def test_stream_conversation_error_handling(self, conversation_ai, sample_conversation_context):
        """Test error handling in streaming response"""
        conversation_ai.context_manager.get_context.return_value = sample_conversation_context
        conversation_ai.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Streaming failed")
        )
        
        response_chunks = []
        async for chunk in conversation_ai.stream_conversation_response(
            "test input", "conv_id", "user_id", "tenant_id"
        ):
            response_chunks.append(chunk)
        
        # Should yield error message
        full_response = "".join(response_chunks)
        assert "Error" in full_response
        assert "Streaming failed" in full_response

    async def test_generate_response_without_functions(self, conversation_ai):
        """Test response generation without function calling"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        
        # Mock OpenAI response
        mock_message = Mock()
        mock_message.content = "Hello! How can I help you today?"
        mock_message.function_call = None
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]
        mock_response.usage = Mock(total_tokens=50, prompt_tokens=30, completion_tokens=20)
        
        conversation_ai.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        assistant_response, function_calls, token_usage = await conversation_ai._generate_response(
            messages, None, "conv_id", "user_id", "tenant_id"
        )
        
        # Verify response without functions
        assert assistant_response.content == "Hello! How can I help you today?"
        assert assistant_response.role == "assistant"
        assert assistant_response.function_call is None
        assert len(function_calls) == 0
        assert token_usage["total_tokens"] == 50

    async def test_build_conversation_messages(self, conversation_ai, sample_conversation_context):
        """Test conversation message building"""
        user_message = ConversationMessage(
            role="user",
            content="Show me 3-bedroom houses",
            timestamp=time.time()
        )
        
        system_prompt = "You are a real estate assistant."
        additional_context = {"user_type": "agent"}
        
        messages = await conversation_ai._build_conversation_messages(
            sample_conversation_context, user_message, system_prompt, additional_context
        )
        
        # Verify message structure
        assert len(messages) >= 3  # System + history + current user message
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == system_prompt
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "Show me 3-bedroom houses"
        
        # Should include conversation history
        history_messages = [msg for msg in messages[1:-1] if msg["role"] in ["user", "assistant"]]
        assert len(history_messages) >= 0

    async def test_default_system_prompt(self, conversation_ai):
        """Test default system prompt generation"""
        # Test without context
        prompt = conversation_ai._get_default_system_prompt()
        assert "JARVIS" in prompt
        assert "real estate" in prompt.lower()
        assert "professional" in prompt.lower()
        
        # Test with agent context
        agent_context = {"user_type": "agent"}
        agent_prompt = conversation_ai._get_default_system_prompt(agent_context)
        assert "agent-specific" in agent_prompt.lower()
        
        # Test with client context
        client_context = {"user_type": "client"}
        client_prompt = conversation_ai._get_default_system_prompt(client_context)
        assert "client-facing" in client_prompt.lower()

    async def test_calculate_cost(self, conversation_ai):
        """Test conversation cost calculation"""
        token_usage = {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500
        }
        
        cost = conversation_ai._calculate_cost(token_usage)
        
        # Verify cost calculation (approximate GPT-4 pricing)
        expected_cost = (1000 * 0.00003) + (500 * 0.00006)
        assert abs(cost - expected_cost) < 0.001
        assert cost > 0

    async def test_calculate_cost_error_handling(self, conversation_ai):
        """Test cost calculation error handling"""
        # Test with missing keys
        invalid_usage = {"invalid_key": 100}
        cost = conversation_ai._calculate_cost(invalid_usage)
        assert cost == 0.0
        
        # Test with None input
        cost = conversation_ai._calculate_cost(None)
        assert cost == 0.0

    async def test_track_performance(self, conversation_ai):
        """Test performance tracking"""
        # Track some metrics
        conversation_ai._track_performance(150, {"total_tokens": 100}, 1)
        conversation_ai._track_performance(200, {"total_tokens": 120}, 0)
        conversation_ai._track_performance(180, {"total_tokens": 110}, 2)
        
        # Verify tracking
        assert len(conversation_ai._conversation_times) == 3
        assert len(conversation_ai._token_usage) == 3
        assert conversation_ai._conversation_times == [150, 200, 180]
        assert conversation_ai._token_usage == [100, 120, 110]
        assert conversation_ai._function_call_success_rate > 0

    async def test_performance_tracking_limits(self, conversation_ai):
        """Test performance tracking with limits"""
        # Add more than 100 entries to test limit
        for i in range(105):
            conversation_ai._track_performance(i, {"total_tokens": i}, 0)
        
        # Should keep only last 100
        assert len(conversation_ai._conversation_times) == 100
        assert len(conversation_ai._token_usage) == 100
        assert conversation_ai._conversation_times[0] == 5  # First 5 should be dropped
        assert conversation_ai._conversation_times[-1] == 104  # Last one should be 104

    async def test_get_conversation_summary(self, conversation_ai, sample_conversation_context):
        """Test conversation summary generation"""
        conversation_id = "test_conv_123"
        user_id = "user_456"
        
        # Mock context with messages
        context_with_messages = {
            **sample_conversation_context,
            "messages": [
                {"role": "user", "content": "I want to buy a house", "timestamp": 1000},
                {"role": "assistant", "content": "Great! What's your budget?", "timestamp": 1001},
                {"role": "user", "content": "Around $400k", "timestamp": 1002},
                {"role": "assistant", "content": "Perfect! I can show you some options", "timestamp": 1003}
            ]
        }
        
        conversation_ai.context_manager.get_context.return_value = context_with_messages
        
        # Mock GPT summary response
        mock_summary_response = Mock()
        mock_summary_response.choices = [Mock(message=Mock(
            content="User is looking to buy a house with a $400k budget. Agent offered to show property options. Next step: schedule property viewings."
        ))]
        
        conversation_ai.client.chat.completions.create = AsyncMock(return_value=mock_summary_response)
        
        summary = await conversation_ai.get_conversation_summary(
            conversation_id, user_id
        )
        
        # Verify summary structure
        assert "summary" in summary
        assert "insights" in summary
        assert "message_count" in summary
        assert "duration_minutes" in summary
        assert "generated_at" in summary
        
        assert summary["message_count"] == 4
        assert "$400k budget" in summary["summary"]
        assert isinstance(summary["insights"], list)

    async def test_extract_conversation_insights(self, conversation_ai):
        """Test conversation insights extraction"""
        messages = [
            {"role": "user", "content": "I want to buy a house for $500k"},
            {"role": "assistant", "content": "Great! Let me help you find one."},
            {"role": "user", "content": "Can we schedule a viewing for this weekend?"},
            {"role": "assistant", "content": "Absolutely! I'll arrange that."},
            {"role": "user", "content": "I really like that property we discussed"}
        ]
        
        insights = await conversation_ai._extract_conversation_insights(messages)
        
        # Verify insights detection
        insight_text = " ".join(insights).lower()
        assert "price" in insight_text or "budget" in insight_text
        assert "schedule" in insight_text or "appointment" in insight_text
        assert "property" in insight_text
        assert "engagement" in insight_text  # Should detect extended conversation

    async def test_get_performance_metrics(self, conversation_ai):
        """Test performance metrics retrieval"""
        # Add some performance data
        conversation_ai._conversation_times = [100, 150, 200, 120, 180]
        conversation_ai._token_usage = [50, 75, 100, 60, 85]
        conversation_ai._function_call_success_rate = 0.92
        
        metrics = conversation_ai.get_performance_metrics()
        
        # Verify metrics
        assert metrics["avg_response_time_ms"] == 150.0  # (100+150+200+120+180)/5
        assert metrics["max_response_time_ms"] == 200
        assert metrics["min_response_time_ms"] == 100
        assert metrics["avg_tokens_per_conversation"] == 74.0  # (50+75+100+60+85)/5
        assert metrics["total_conversations"] == 5
        assert metrics["function_call_success_rate"] == 0.92
        assert "model_config" in metrics
        assert metrics["target_response_time_ms"] == 500

    async def test_get_performance_metrics_no_data(self, conversation_ai):
        """Test performance metrics with no data"""
        metrics = conversation_ai.get_performance_metrics()
        assert metrics["status"] == "no_data"

    async def test_health_check_success(self, conversation_ai):
        """Test successful health check"""
        # Mock component health checks
        conversation_ai.context_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        conversation_ai.intent_recognizer.health_check = AsyncMock(return_value={"status": "healthy"})
        conversation_ai.function_handler.health_check = AsyncMock(return_value={"status": "healthy"})
        conversation_ai.flow_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Mock OpenAI API test
        mock_test_response = Mock()
        conversation_ai.client.chat.completions.create = AsyncMock(return_value=mock_test_response)
        
        # Add some performance data
        conversation_ai._conversation_times = [100, 150, 120]
        
        health = await conversation_ai.health_check()
        
        # Verify health check
        assert health["status"] == "healthy"
        assert health["service"] == "conversation_ai"
        assert health["function_calling_enabled"] is not None
        assert "performance" in health
        assert "components" in health
        assert health["api_connectivity"] == "ok"
        assert "timestamp" in health
        
        # Verify all components checked
        assert "context_manager" in health["components"]
        assert "intent_recognizer" in health["components"]
        assert "function_handler" in health["components"]
        assert "flow_manager" in health["components"]

    async def test_health_check_degraded(self, conversation_ai):
        """Test health check with degraded status"""
        # Mock component failure
        conversation_ai.context_manager.health_check = AsyncMock(
            side_effect=Exception("Context manager failed")
        )
        conversation_ai.intent_recognizer.health_check = AsyncMock(return_value={"status": "healthy"})
        conversation_ai.function_handler.health_check = AsyncMock(return_value={"status": "healthy"})
        conversation_ai.flow_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Mock successful API test
        conversation_ai.client.chat.completions.create = AsyncMock(return_value=Mock())
        
        health = await conversation_ai.health_check()
        
        # Should be degraded due to component failure
        assert health["status"] == "degraded"
        assert health["components"]["context_manager"]["status"] == "error"
        assert "Context manager failed" in health["components"]["context_manager"]["error"]

    async def test_health_check_api_failure(self, conversation_ai):
        """Test health check with API connectivity failure"""
        # Mock successful component checks
        conversation_ai.context_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        conversation_ai.intent_recognizer.health_check = AsyncMock(return_value={"status": "healthy"})
        conversation_ai.function_handler.health_check = AsyncMock(return_value={"status": "healthy"})
        conversation_ai.flow_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Mock API failure
        conversation_ai.client.chat.completions.create = AsyncMock(
            side_effect=Exception("API timeout")
        )
        
        health = await conversation_ai.health_check()
        
        # Should be degraded due to API failure
        assert health["status"] == "degraded"
        assert health["api_connectivity"] == "error"
        assert "API timeout" in health["api_error"]

    @pytest.mark.performance
    async def test_conversation_processing_performance(self, conversation_ai, sample_conversation_context, mock_intent_result):
        """Performance test for conversation processing"""
        # Setup fast mocks
        conversation_ai.context_manager.get_context.return_value = sample_conversation_context
        conversation_ai.intent_recognizer.recognize_intent.return_value = mock_intent_result
        conversation_ai.function_handler.get_available_functions.return_value = []
        
        # Mock fast OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Quick response", function_call=None))]
        mock_response.usage = Mock(total_tokens=50, prompt_tokens=30, completion_tokens=20)
        
        conversation_ai.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Test performance over multiple runs
        times = []
        for i in range(10):
            start_time = time.time()
            result = await conversation_ai.process_conversation_turn(
                f"Test input {i}", "conv_id", "user_id", "tenant_id"
            )
            processing_time = (time.time() - start_time) * 1000
            times.append(processing_time)
            
            assert result.success is True
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Performance assertions
        assert avg_time < 500, f"Average processing time too high: {avg_time}ms"
        assert max_time < 1000, f"Max processing time too high: {max_time}ms"
        assert all(t < 2000 for t in times), "Some processing times exceeded 2 seconds"

    @pytest.mark.performance
    async def test_concurrent_conversation_processing(self, conversation_ai, sample_conversation_context, mock_intent_result):
        """Test concurrent conversation processing performance"""
        # Setup mocks for concurrent processing
        conversation_ai.context_manager.get_context.return_value = sample_conversation_context
        conversation_ai.intent_recognizer.recognize_intent.return_value = mock_intent_result
        conversation_ai.function_handler.get_available_functions.return_value = []
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Concurrent response", function_call=None))]
        mock_response.usage = Mock(total_tokens=50, prompt_tokens=30, completion_tokens=20)
        
        conversation_ai.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Create concurrent tasks
        num_concurrent = 5
        tasks = []
        
        start_time = time.time()
        for i in range(num_concurrent):
            task = conversation_ai.process_conversation_turn(
                f"Concurrent input {i}", f"conv_{i}", f"user_{i}", "tenant_id"
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        # Verify all succeeded
        for result in results:
            assert result.success is True
        
        # Should complete much faster than sequential processing
        expected_sequential_time = num_concurrent * 500  # 500ms per request
        assert total_time < expected_sequential_time * 0.5, "Concurrent processing not efficient enough"
