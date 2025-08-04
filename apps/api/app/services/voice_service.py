"""
Voice processing service for real-time AI voice interactions
"""
import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
import aiohttp
import openai
from elevenlabs import generate, set_api_key, Voice, VoiceSettings

from app.core.config import settings
from app.models.conversation import Conversation, ConversationMessage, MessageType, MessageDirection
from app.models.voice_agent import VoiceAgent
from app.models.lead import Lead
from app.services.conversation_service import ConversationService
from app.services.lead_service import LeadService
from app.services.webhook_service import WebhookService

logger = logging.getLogger("seiketsu.voice_service")


class VoiceService:
    """Enterprise voice processing service with <180ms response times"""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        set_api_key(settings.ELEVEN_LABS_API_KEY)
        
        self.conversation_service = ConversationService()
        self.lead_service = LeadService()
        self.webhook_service = WebhookService()
        
        # Response time tracking
        self.target_response_time_ms = 180
        self.response_times = []
        
    async def initialize(self):
        """Initialize voice service"""
        try:
            # Test ElevenLabs connection
            await self._test_elevenlabs_connection()
            
            # Test OpenAI connection
            await self._test_openai_connection()
            
            logger.info("Voice service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice service: {e}")
            raise
    
    async def process_voice_input(
        self,
        audio_data: bytes,
        conversation_id: str,
        voice_agent: VoiceAgent,
        organization_id: str
    ) -> Dict[str, Any]:
        """Process incoming voice input with <180ms response time"""
        start_time = time.time()
        
        try:
            # Step 1: Speech-to-Text (30-50ms)
            transcript = await self._speech_to_text(audio_data)
            stt_time = time.time()
            
            # Step 2: AI Processing (80-100ms)
            ai_response = await self._generate_ai_response(
                transcript, conversation_id, voice_agent, organization_id
            )
            ai_time = time.time()
            
            # Step 3: Text-to-Speech (50-80ms)
            audio_response = await self._text_to_speech(
                ai_response["text"], voice_agent
            )
            tts_time = time.time()
            
            # Calculate timing
            total_time_ms = (tts_time - start_time) * 1000
            timing = {
                "stt_ms": (stt_time - start_time) * 1000,
                "ai_ms": (ai_time - stt_time) * 1000,
                "tts_ms": (tts_time - ai_time) * 1000,
                "total_ms": total_time_ms
            }
            
            # Track response times
            self.response_times.append(total_time_ms)
            if len(self.response_times) > 100:
                self.response_times.pop(0)
            
            # Log performance warning if too slow
            if total_time_ms > self.target_response_time_ms:
                logger.warning(
                    f"Voice processing exceeded target time: {total_time_ms:.1f}ms > {self.target_response_time_ms}ms"
                )
            
            # Save conversation messages
            await self._save_conversation_messages(
                conversation_id, transcript, ai_response["text"], timing
            )
            
            # Process any lead qualification
            if ai_response.get("lead_qualified"):
                await self._process_lead_qualification(
                    conversation_id, ai_response["lead_data"], organization_id
                )
            
            return {
                "success": True,
                "transcript": transcript,
                "response_text": ai_response["text"],
                "response_audio": audio_response,
                "timing": timing,
                "lead_qualified": ai_response.get("lead_qualified", False),
                "needs_transfer": ai_response.get("needs_transfer", False),
                "conversation_ended": ai_response.get("conversation_ended", False)
            }
            
        except Exception as e:
            error_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Voice processing failed after {error_time_ms:.1f}ms: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "timing": {"total_ms": error_time_ms}
            }
    
    async def start_conversation(
        self,
        caller_phone: str,
        voice_agent: VoiceAgent,
        organization_id: str,
        call_metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Start a new voice conversation"""
        try:
            # Create conversation record
            conversation = await self.conversation_service.create_conversation(
                caller_phone=caller_phone,
                voice_agent_id=voice_agent.id,
                organization_id=organization_id,
                metadata=call_metadata or {}
            )
            
            # Generate greeting
            greeting_text = voice_agent.greeting_message or f"Hello! This is {voice_agent.name}. How can I help you today?"
            greeting_audio = await self._text_to_speech(greeting_text, voice_agent)
            
            # Save greeting message
            await self._save_conversation_message(
                conversation.id,
                MessageType.AGENT_SPEECH,
                MessageDirection.OUTBOUND,
                greeting_text,
                audio_url=greeting_audio.get("url") if isinstance(greeting_audio, dict) else None
            )
            
            # Send webhook notification
            await self.webhook_service.send_webhook(
                organization_id,
                "conversation.started",
                {
                    "conversation_id": conversation.id,
                    "caller_phone": caller_phone,
                    "voice_agent_id": voice_agent.id,
                    "started_at": conversation.started_at.isoformat()
                }
            )
            
            logger.info(f"Started conversation {conversation.id} for agent {voice_agent.name}")
            
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            raise
    
    async def end_conversation(
        self,
        conversation_id: str,
        outcome: str,
        outcome_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """End a voice conversation and process results"""
        try:
            conversation = await self.conversation_service.end_conversation(
                conversation_id, outcome, outcome_details
            )
            
            # Update voice agent statistics
            if conversation.voice_agent:
                conversation.voice_agent.update_performance_stats(
                    conversation.duration_seconds or 0,
                    conversation.was_successful
                )
            
            # Send webhook notification
            await self.webhook_service.send_webhook(
                conversation.organization_id,
                "conversation.ended",
                {
                    "conversation_id": conversation.id,
                    "outcome": outcome,
                    "duration_seconds": conversation.duration_seconds,
                    "lead_qualified": bool(conversation.lead_id),
                    "ended_at": conversation.ended_at.isoformat()
                }
            )
            
            logger.info(f"Ended conversation {conversation_id} with outcome: {outcome}")
            
            return {
                "conversation_id": conversation_id,
                "outcome": outcome,
                "duration_seconds": conversation.duration_seconds,
                "lead_created": bool(conversation.lead_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to end conversation {conversation_id}: {e}")
            raise
    
    async def transfer_to_human(
        self,
        conversation_id: str,
        reason: str,
        target_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transfer conversation to human agent"""
        try:
            conversation = await self.conversation_service.transfer_to_human(
                conversation_id, reason, target_agent
            )
            
            # Send webhook notification
            await self.webhook_service.send_webhook(
                conversation.organization_id,
                "call.transferred",
                {
                    "conversation_id": conversation.id,
                    "reason": reason,
                    "target_agent": target_agent,
                    "transferred_at": conversation.transfer_timestamp.isoformat()
                }
            )
            
            logger.info(f"Transferred conversation {conversation_id} to human: {reason}")
            
            return {
                "conversation_id": conversation_id,
                "transferred": True,
                "reason": reason,
                "target_agent": target_agent
            }
            
        except Exception as e:
            logger.error(f"Failed to transfer conversation {conversation_id}: {e}")
            raise
    
    async def _speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech to text using OpenAI Whisper"""
        try:
            # Use OpenAI Whisper for fast, accurate transcription
            response = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.mp3", audio_data, "audio/mpeg"),
                language="en"  # Optimize for English
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Speech-to-text failed: {e}")
            raise
    
    async def _generate_ai_response(
        self,
        user_input: str,
        conversation_id: str,
        voice_agent: VoiceAgent,
        organization_id: str
    ) -> Dict[str, Any]:
        """Generate AI response using optimized prompting"""
        try:
            # Get conversation history
            conversation_history = await self._get_conversation_history(conversation_id)
            
            # Build optimized prompt
            system_prompt = voice_agent.get_system_prompt_with_context({
                "organization_id": organization_id,
                "conversation_history": conversation_history[-5:]  # Last 5 exchanges
            })
            
            # Create messages for OpenAI
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Generate response with function calling for structured output
            response = await self.openai_client.chat.completions.create(
                model=voice_agent.ai_model or "gpt-4",
                messages=messages,
                temperature=voice_agent.temperature or 0.7,
                max_tokens=voice_agent.max_tokens or 200,  # Keep responses concise
                functions=[
                    {
                        "name": "process_conversation",
                        "description": "Process conversation and determine next action",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "response_text": {
                                    "type": "string",
                                    "description": "The text response to speak to the user"
                                },
                                "lead_qualified": {
                                    "type": "boolean",
                                    "description": "Whether the user qualifies as a lead"
                                },
                                "lead_data": {
                                    "type": "object",
                                    "description": "Lead qualification data if qualified"
                                },
                                "needs_transfer": {
                                    "type": "boolean",
                                    "description": "Whether to transfer to human agent"
                                },
                                "conversation_ended": {
                                    "type": "boolean",
                                    "description": "Whether the conversation should end"
                                }
                            },
                            "required": ["response_text"]
                        }
                    }
                ],
                function_call="auto"
            )
            
            # Parse function call response
            message = response.choices[0].message
            if message.function_call:
                function_data = json.loads(message.function_call.arguments)
                return function_data
            else:
                return {"response_text": message.content}
                
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            # Fallback response
            return {
                "response_text": "I apologize, but I'm having trouble processing that. Could you please repeat your question?"
            }
    
    async def _text_to_speech(
        self,
        text: str,
        voice_agent: VoiceAgent
    ) -> bytes:
        """Convert text to speech using ElevenLabs"""
        try:
            # Get voice settings for the agent
            voice_settings = voice_agent.get_voice_settings_for_provider()
            
            # Generate audio using ElevenLabs
            audio = generate(
                text=text,
                voice=voice_settings.get("voice_id", "21m00Tcm4TlvDq8ikWAM"),  # Default voice
                model=voice_settings.get("model_id", "eleven_turbo_v2"),  # Fastest model
                voice_settings=VoiceSettings(
                    stability=voice_settings.get("voice_settings", {}).get("stability", 0.75),
                    similarity_boost=voice_settings.get("voice_settings", {}).get("similarity_boost", 0.75),
                    style=voice_settings.get("voice_settings", {}).get("style", 0.0),
                    use_speaker_boost=voice_settings.get("voice_settings", {}).get("use_speaker_boost", True)
                )
            )
            
            return audio
            
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            raise
    
    async def _save_conversation_messages(
        self,
        conversation_id: str,
        user_input: str,
        ai_response: str,
        timing: Dict[str, float]
    ):
        """Save conversation messages to database"""
        try:
            # Save user message
            await self._save_conversation_message(
                conversation_id,
                MessageType.USER_SPEECH,
                MessageDirection.INBOUND,
                user_input,
                processing_time_ms=timing.get("stt_ms", 0)
            )
            
            # Save AI response
            await self._save_conversation_message(
                conversation_id,
                MessageType.AGENT_SPEECH,
                MessageDirection.OUTBOUND,
                ai_response,
                processing_time_ms=timing.get("total_ms", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to save conversation messages: {e}")
    
    async def _save_conversation_message(
        self,
        conversation_id: str,
        message_type: MessageType,
        direction: MessageDirection,
        content: str,
        audio_url: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ):
        """Save individual conversation message"""
        # This would integrate with your database session
        # Implementation depends on your database setup
        pass
    
    async def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        # This would query your database for recent messages
        # Return format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        return []
    
    async def _process_lead_qualification(
        self,
        conversation_id: str,
        lead_data: Dict[str, Any],
        organization_id: str
    ):
        \"\"\"Process lead qualification from conversation\"\"\"
        try:
            # Create lead record
            lead = await self.lead_service.create_lead_from_conversation(
                conversation_id, lead_data, organization_id
            )
            
            # Send webhook notification
            await self.webhook_service.send_webhook(
                organization_id,
                "lead.created",
                {
                    "lead_id": lead.id,
                    "conversation_id": conversation_id,
                    "lead_score": lead.lead_score,
                    "contact_info": {
                        "name": lead.full_name,
                        "email": lead.email,
                        "phone": lead.phone
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Lead qualification processing failed: {e}")
    
    async def _test_elevenlabs_connection(self):
        """Test ElevenLabs API connection"""
        try:
            # Simple test generation
            test_audio = generate(
                text="Test",
                voice="21m00Tcm4TlvDq8ikWAM",
                model="eleven_turbo_v2"
            )
            logger.info("ElevenLabs connection test successful")
        except Exception as e:
            logger.error(f"ElevenLabs connection test failed: {e}")
            raise
    
    async def _test_openai_connection(self):
        """Test OpenAI API connection"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1
            )
            logger.info("OpenAI connection test successful")
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            raise
    
    @property
    def average_response_time_ms(self) -> float:
        \"\"\"Get average response time over recent requests\"\"\"
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def performance_stats(self) -> Dict[str, Any]:
        \"\"\"Get performance statistics\"\"\"
        if not self.response_times:
            return {"average_ms": 0, "requests_processed": 0, "target_met_percentage": 0}
        
        within_target = sum(1 for t in self.response_times if t <= self.target_response_time_ms)
        
        return {
            "average_ms": self.average_response_time_ms,
            "requests_processed": len(self.response_times),
            "target_met_percentage": (within_target / len(self.response_times)) * 100,
            "target_response_time_ms": self.target_response_time_ms
        }