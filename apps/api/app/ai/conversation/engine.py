"""
Conversation AI Engine
Core conversational AI system with GPT-4 integration and function calling
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum

from openai import AsyncOpenAI
import openai

from .context_manager import ConversationContextManager
from .intent_recognition import IntentRecognizer
from .function_calling import FunctionCallHandler
from .flow_manager import ConversationFlowManager
from ..config import ai_settings, MODEL_CONFIGS
from ...core.cache import get_redis_client

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Conversation states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    WAITING_FOR_INPUT = "waiting_for_input"
    PROCESSING = "processing"
    FUNCTION_CALLING = "function_calling"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ConversationMessage:
    """Single conversation message"""
    role: str  # "user", "assistant", "system", "function"
    content: str
    function_call: Optional[Dict[str, Any]] = None
    function_name: Optional[str] = None
    timestamp: float = 0.0
    message_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ConversationTurn:
    """Complete conversation turn with response"""
    user_message: ConversationMessage
    assistant_response: ConversationMessage
    function_calls: List[Dict[str, Any]] = None
    processing_time_ms: int = 0
    tokens_used: int = 0
    cost: float = 0.0
    confidence: float = 1.0
    intent: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class ConversationAI:
    """
    Advanced Conversation AI Engine
    Handles natural conversations with function calling and context management
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=ai_settings.OPENAI_API_KEY,
            organization=ai_settings.OPENAI_ORG_ID,
            base_url=ai_settings.OPENAI_BASE_URL,
            timeout=ai_settings.OPENAI_TIMEOUT,
            max_retries=ai_settings.OPENAI_MAX_RETRIES
        )
        
        # Initialize components
        self.context_manager = ConversationContextManager()
        self.intent_recognizer = IntentRecognizer()
        self.function_handler = FunctionCallHandler()
        self.flow_manager = ConversationFlowManager()
        
        # Configuration
        self.model_config = MODEL_CONFIGS["gpt-4-conversation"]
        self.max_context_turns = ai_settings.CONVERSATION_MEMORY_TURNS
        self.function_calling_enabled = ai_settings.ENABLE_FUNCTION_CALLING
        self.max_function_calls = ai_settings.MAX_FUNCTION_CALLS
        
        # Performance tracking
        self._conversation_times = []
        self._token_usage = []
        self._function_call_success_rate = 0.0
        
        logger.info("Conversation AI engine initialized")
    
    async def initialize(self):
        """Initialize all components"""
        await self.context_manager.initialize()
        await self.intent_recognizer.initialize()
        await self.function_handler.initialize()
        await self.flow_manager.initialize()
        logger.info("Conversation AI components initialized")
    
    async def process_conversation_turn(
        self,
        user_input: str,
        conversation_id: str,
        user_id: str,
        tenant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> ConversationTurn:
        """
        Process a complete conversation turn
        
        Args:
            user_input: User's message
            conversation_id: Unique conversation identifier
            user_id: User identifier
            tenant_id: Tenant identifier for multi-tenancy
            context: Additional context for the conversation
            system_prompt: Custom system prompt
            
        Returns:
            Complete conversation turn with response
        """
        start_time = time.time()
        
        try:
            # Create user message
            user_message = ConversationMessage(
                role="user",
                content=user_input,
                timestamp=time.time(),
                message_id=self._generate_message_id(),
                metadata={"user_id": user_id, "tenant_id": tenant_id}
            )
            
            # Get conversation context
            conversation_context = await self.context_manager.get_context(
                conversation_id, user_id, tenant_id
            )
            
            # Recognize intent
            intent_result = await self.intent_recognizer.recognize_intent(
                user_input, conversation_context, context
            )
            
            # Build conversation messages
            messages = await self._build_conversation_messages(
                conversation_context, user_message, system_prompt, context
            )
            
            # Determine if function calling is needed
            functions = None
            if self.function_calling_enabled and intent_result.requires_function_call:
                functions = await self.function_handler.get_available_functions(
                    user_id, tenant_id, intent_result.intent
                )
            
            # Generate response
            assistant_response, function_calls, token_usage = await self._generate_response(
                messages, functions, conversation_id, user_id, tenant_id
            )
            
            # Update conversation context
            await self.context_manager.add_turn(
                conversation_id, user_message, assistant_response, user_id, tenant_id
            )
            
            # Update flow state
            await self.flow_manager.update_flow_state(
                conversation_id, intent_result.intent, assistant_response.content,
                user_id, tenant_id
            )
            
            # Calculate costs
            cost = self._calculate_cost(token_usage)
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create conversation turn
            turn = ConversationTurn(
                user_message=user_message,
                assistant_response=assistant_response,
                function_calls=function_calls,
                processing_time_ms=processing_time_ms,
                tokens_used=token_usage.get("total_tokens", 0),
                cost=cost,
                confidence=intent_result.confidence,
                intent=intent_result.intent,
                success=True
            )
            
            # Track performance
            self._track_performance(processing_time_ms, token_usage, len(function_calls or []))
            
            logger.info(f"Conversation turn completed in {processing_time_ms}ms: {intent_result.intent}")
            
            return turn
            
        except Exception as e:
            logger.error(f"Conversation turn failed: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create error response
            error_message = ConversationMessage(
                role="assistant",
                content="I apologize, but I encountered an error processing your request. Please try again.",
                timestamp=time.time(),
                message_id=self._generate_message_id()
            )
            
            return ConversationTurn(
                user_message=ConversationMessage(role="user", content=user_input, timestamp=time.time()),
                assistant_response=error_message,
                processing_time_ms=processing_time_ms,
                success=False,
                error=str(e)
            )
    
    async def stream_conversation_response(
        self,
        user_input: str,
        conversation_id: str,
        user_id: str,
        tenant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream conversation response for real-time interaction
        Yields response tokens as they're generated
        """
        try:
            # Get context and build messages
            conversation_context = await self.context_manager.get_context(
                conversation_id, user_id, tenant_id
            )
            
            user_message = ConversationMessage(
                role="user",
                content=user_input,
                timestamp=time.time()
            )
            
            messages = await self._build_conversation_messages(
                conversation_context, user_message, None, context
            )
            
            # Stream response
            response_content = ""
            async for chunk in self._stream_openai_response(messages):
                if chunk:
                    response_content += chunk
                    yield chunk
            
            # Save complete response to context
            assistant_response = ConversationMessage(
                role="assistant",
                content=response_content,
                timestamp=time.time()
            )
            
            await self.context_manager.add_turn(
                conversation_id, user_message, assistant_response, user_id, tenant_id
            )
            
        except Exception as e:
            logger.error(f"Streaming conversation failed: {e}")
            yield f"Error: {str(e)}"
    
    async def _generate_response(
        self,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, Any]]],
        conversation_id: str,
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> tuple[ConversationMessage, List[Dict[str, Any]], Dict[str, int]]:
        """Generate response using OpenAI API with function calling"""
        
        function_calls = []
        total_tokens = 0
        
        # Prepare request parameters
        request_params = {
            "model": self.model_config.model_id,
            "messages": messages,
            "max_tokens": self.model_config.max_tokens,
            "temperature": self.model_config.temperature,
            "timeout": self.model_config.timeout
        }
        
        if functions:
            request_params["functions"] = functions
            request_params["function_call"] = "auto"
        
        # Initial response
        response = await self.client.chat.completions.create(**request_params)
        message = response.choices[0].message
        total_tokens += response.usage.total_tokens
        
        # Handle function calls
        if message.function_call and len(function_calls) < self.max_function_calls:
            # Execute function call
            function_result = await self.function_handler.execute_function(
                message.function_call.name,
                json.loads(message.function_call.arguments),
                user_id,
                tenant_id
            )
            
            function_calls.append({
                "name": message.function_call.name,
                "arguments": message.function_call.arguments,
                "result": function_result
            })
            
            # Add function result to conversation
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": message.function_call.name,
                    "arguments": message.function_call.arguments
                }
            })
            
            messages.append({
                "role": "function",
                "name": message.function_call.name,
                "content": json.dumps(function_result)
            })
            
            # Get final response
            final_response = await self.client.chat.completions.create(**request_params)
            final_message = final_response.choices[0].message
            total_tokens += final_response.usage.total_tokens
            
            # Create assistant message
            assistant_response = ConversationMessage(
                role="assistant",
                content=final_message.content,
                timestamp=time.time(),
                message_id=self._generate_message_id(),
                function_call=message.function_call.__dict__ if message.function_call else None
            )
        else:
            # Create assistant message without function calls
            assistant_response = ConversationMessage(
                role="assistant",
                content=message.content,
                timestamp=time.time(),
                message_id=self._generate_message_id()
            )
        
        token_usage = {
            "total_tokens": total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }
        
        return assistant_response, function_calls, token_usage
    
    async def _stream_openai_response(
        self, 
        messages: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI API"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_config.model_id,
                messages=messages,
                max_tokens=self.model_config.max_tokens,
                temperature=self.model_config.temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            yield ""
    
    async def _build_conversation_messages(
        self,
        context: Dict[str, Any],
        user_message: ConversationMessage,
        system_prompt: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Build message list for OpenAI API"""
        
        messages = []
        
        # System message
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({
                "role": "system", 
                "content": self._get_default_system_prompt(additional_context)
            })
        
        # Previous conversation history
        conversation_history = context.get("messages", [])
        for msg in conversation_history[-self.max_context_turns:]:
            message_dict = {"role": msg["role"], "content": msg["content"]}
            if msg.get("function_call"):
                message_dict["function_call"] = msg["function_call"]
            if msg.get("function_name"):
                message_dict["name"] = msg["function_name"]
            messages.append(message_dict)
        
        # Current user message
        messages.append({"role": user_message.role, "content": user_message.content})
        
        return messages
    
    def _get_default_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Get default system prompt for real estate assistant"""
        base_prompt = """You are JARVIS, an advanced AI voice assistant for Seiketsu AI's real estate platform. You are professional, knowledgeable, and helpful.

Your capabilities include:
- Answering real estate questions
- Helping with property searches
- Scheduling appointments
- Providing market insights
- Lead qualification
- CRM management

Guidelines:
- Be conversational and natural
- Ask clarifying questions when needed
- Use function calls for specific actions
- Keep responses concise but informative
- Maintain professional tone
- Focus on providing value to real estate professionals

Current conversation context: Real estate voice assistant interaction."""
        
        if context:
            # Add context-specific information
            if context.get("user_type") == "agent":
                base_prompt += "\n\nUser is a real estate agent. Focus on agent-specific features and tools."
            elif context.get("user_type") == "client":
                base_prompt += "\n\nUser is a potential property buyer/seller. Focus on client-facing services."
        
        return base_prompt
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _calculate_cost(self, token_usage: Dict[str, int]) -> float:
        """Calculate conversation cost based on token usage"""
        try:
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
            
            # GPT-4 pricing (approximate)
            prompt_cost = prompt_tokens * 0.00003
            completion_cost = completion_tokens * 0.00006
            
            return prompt_cost + completion_cost
            
        except Exception as e:
            logger.error(f"Cost calculation failed: {e}")
            return 0.0
    
    def _track_performance(
        self, 
        processing_time_ms: int, 
        token_usage: Dict[str, int], 
        function_calls_count: int
    ):
        """Track performance metrics"""
        self._conversation_times.append(processing_time_ms)
        self._token_usage.append(token_usage.get("total_tokens", 0))
        
        # Update function call success rate
        if function_calls_count > 0:
            # In production, track actual success/failure
            self._function_call_success_rate = 0.95  # Placeholder
        
        # Keep recent metrics only
        if len(self._conversation_times) > 100:
            self._conversation_times = self._conversation_times[-100:]
            self._token_usage = self._token_usage[-100:]
    
    async def get_conversation_summary(
        self,
        conversation_id: str,
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate conversation summary and insights"""
        try:
            context = await self.context_manager.get_context(
                conversation_id, user_id, tenant_id
            )
            
            messages = context.get("messages", [])
            
            if not messages:
                return {"summary": "No conversation history", "insights": []}
            
            # Generate summary using GPT
            summary_prompt = f"""Summarize this conversation between a user and a real estate AI assistant. Focus on:
1. Key topics discussed
2. Actions taken or requested
3. Important decisions or preferences
4. Next steps or follow-ups needed

Conversation:
{json.dumps(messages[-20:], indent=2)}

Provide a concise summary and actionable insights."""
            
            summary_response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = summary_response.choices[0].message.content
            
            # Extract insights
            insights = await self._extract_conversation_insights(messages)
            
            return {
                "summary": summary,
                "insights": insights,
                "message_count": len(messages),
                "duration_minutes": (messages[-1]["timestamp"] - messages[0]["timestamp"]) / 60 if messages else 0,
                "generated_at": time.time()
            }
            
        except Exception as e:
            logger.error(f"Conversation summary generation failed: {e}")
            return {"error": str(e)}
    
    async def _extract_conversation_insights(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract actionable insights from conversation"""
        insights = []
        
        try:
            # Analyze conversation patterns
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            
            if len(user_messages) > 5:
                insights.append("Extended conversation - high engagement")
            
            # Look for specific keywords/patterns
            all_content = " ".join([msg["content"] for msg in user_messages]).lower()
            
            if "price" in all_content or "budget" in all_content:
                insights.append("Price/budget discussion - potential qualified lead")
            
            if "schedule" in all_content or "appointment" in all_content:
                insights.append("Scheduling request - follow up needed")
            
            if "property" in all_content or "house" in all_content:
                insights.append("Property-specific interest - provide property details")
            
            return insights
            
        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get conversation AI performance metrics"""
        if not self._conversation_times:
            return {"status": "no_data"}
        
        return {
            "avg_response_time_ms": sum(self._conversation_times) / len(self._conversation_times),
            "max_response_time_ms": max(self._conversation_times),
            "min_response_time_ms": min(self._conversation_times),
            "avg_tokens_per_conversation": sum(self._token_usage) / len(self._token_usage) if self._token_usage else 0,
            "total_conversations": len(self._conversation_times),
            "function_call_success_rate": self._function_call_success_rate,
            "model_config": self.model_config.__dict__,
            "target_response_time_ms": 500
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for conversation AI engine"""
        health_status = {
            "status": "healthy",
            "service": "conversation_ai",
            "model": self.model_config.model_id,
            "function_calling_enabled": self.function_calling_enabled,
            "performance": self.get_performance_metrics(),
            "components": {},
            "timestamp": time.time()
        }
        
        # Check components
        components = [
            ("context_manager", self.context_manager),
            ("intent_recognizer", self.intent_recognizer),
            ("function_handler", self.function_handler),
            ("flow_manager", self.flow_manager)
        ]
        
        for name, component in components:
            try:
                component_health = await component.health_check()
                health_status["components"][name] = component_health
            except Exception as e:
                health_status["components"][name] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
        
        # Test OpenAI API connectivity
        try:
            test_response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                ),
                timeout=5.0
            )
            health_status["api_connectivity"] = "ok"
        except Exception as e:
            health_status["api_connectivity"] = "error"
            health_status["api_error"] = str(e)
            health_status["status"] = "degraded"
        
        return health_status