"""
Enterprise Voice Processing API Endpoints
Real-time voice interactions with <180ms response times
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging
import json
import asyncio
from datetime import datetime
import io

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_organization
from app.models.user import User
from app.models.organization import Organization
from app.models.voice_agent import VoiceAgent
from app.models.conversation import Conversation, ConversationStatus
from app.services.voice_service import VoiceService
from app.services.conversation_service import ConversationService
from app.services.elevenlabs_service import elevenlabs_service, Language, AudioFormat
from app.api.v1.voice_streaming import router as streaming_router

logger = logging.getLogger("seiketsu.voice")
router = APIRouter()

# Initialize services
voice_service = VoiceService()
conversation_service = ConversationService()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
    
    def disconnect(self, conversation_id: str):
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]
    
    async def send_personal_message(self, message: dict, conversation_id: str):
        if conversation_id in self.active_connections:
            websocket = self.active_connections[conversation_id]
            await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

# Request/Response Models
class VoiceProcessingRequest(BaseModel):
    conversation_id: str
    voice_agent_id: str
    caller_phone: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class VoiceSessionRequest(BaseModel):
    voice_agent_id: str
    caller_phone: str
    caller_name: Optional[str] = None
    caller_email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class TextToSpeechRequest(BaseModel):
    text: str = Field(..., max_length=2000)
    voice_agent_id: str
    format: str = Field(default="mp3", regex="^(mp3|wav|ogg)$")
    language: str = Field(default="en", regex="^(en|es|zh)$")
    optimize_for_speed: bool = True
    enable_caching: bool = True

class SpeechToTextResponse(BaseModel):
    transcript: str
    confidence: float
    duration_seconds: float
    processing_time_ms: float

class VoiceProcessingResponse(BaseModel):
    success: bool
    transcript: Optional[str] = None
    response_text: Optional[str] = None
    timing: Dict[str, float]
    lead_qualified: bool = False
    needs_transfer: bool = False
    conversation_ended: bool = False
    error: Optional[str] = None

@router.websocket("/ws/{session_id}")
async def voice_stream_websocket(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time voice streaming with sub-2s response time"""
    await manager.connect(websocket, session_id)
    
    try:
        # Get conversation and validate access
        conversation = await conversation_service.get_conversation(conversation_id, db)
        if not conversation:
            await websocket.send_text(json.dumps({
                "error": "Conversation not found",
                "type": "error"
            }))
            return
        
        voice_agent = conversation.voice_agent
        if not voice_agent or not voice_agent.is_active:
            await websocket.send_text(json.dumps({
                "error": "Voice agent not available", 
                "type": "error"
            }))
            return
        
        logger.info(f"WebSocket connection established for conversation {conversation_id}")
        
        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            
            # Process voice input
            result = await voice_service.process_voice_input(
                audio_data=data,
                conversation_id=conversation_id,
                voice_agent=voice_agent,
                organization_id=conversation.organization_id
            )
            
            # Send response back
            await websocket.send_text(json.dumps({
                "type": "voice_response",
                "data": result
            }))
            
            # Handle conversation state changes
            if result.get("conversation_ended"):
                await websocket.send_text(json.dumps({
                    "type": "conversation_ended",
                    "data": {"conversation_id": conversation_id}
                }))
                break
            
            if result.get("needs_transfer"):
                await websocket.send_text(json.dumps({
                    "type": "transfer_requested",
                    "data": {"conversation_id": conversation_id}
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error for conversation {conversation_id}: {e}")
        await websocket.send_text(json.dumps({
            "error": str(e),
            "type": "error"
        }))
    finally:
        manager.disconnect(conversation_id)

@router.post("/process", response_model=VoiceProcessingResponse)
async def process_voice_input(
    request: VoiceProcessingRequest,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Process voice input with AI response generation"""
    try:
        # Validate conversation access
        conversation = await conversation_service.get_conversation(request.conversation_id, db)
        if not conversation or conversation.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if not conversation.is_active:
            raise HTTPException(status_code=400, detail="Conversation is not active")
        
        # Read audio data
        audio_data = await audio.read()
        if len(audio_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="Audio file too large")
        
        # Process voice input
        result = await voice_service.process_voice_input(
            audio_data=audio_data,
            conversation_id=request.conversation_id,
            voice_agent=conversation.voice_agent,
            organization_id=current_org.id
        )
        
        return VoiceProcessingResponse(**result)
        
    except Exception as e:
        logger.error(f"Voice processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions", status_code=201)
async def create_voice_session(
    request: VoiceSessionRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create new voice conversation session"""
    try:
        # Get voice agent
        voice_agent = await db.get(VoiceAgent, request.voice_agent_id)
        if not voice_agent or voice_agent.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Voice agent not found")
        
        if not voice_agent.is_active:
            raise HTTPException(status_code=400, detail="Voice agent is not active")
        
        # Start conversation
        conversation = await voice_service.start_conversation(
            caller_phone=request.caller_phone,
            voice_agent=voice_agent,
            organization_id=current_org.id,
            call_metadata={
                "caller_name": request.caller_name,
                "caller_email": request.caller_email,
                "created_by_user_id": current_user.id,
                **request.metadata
            }
        )
        
        return {
            "conversation_id": conversation.id,
            "session_id": conversation.session_id,
            "status": conversation.status.value,
            "voice_agent": {
                "id": voice_agent.id,
                "name": voice_agent.name,
                "phone_number": voice_agent.phone_number
            },
            "websocket_url": f"/api/v1/voice/stream/{conversation.id}",
            "started_at": conversation.started_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{conversation_id}/end")
async def end_voice_session(
    conversation_id: str,
    outcome: str,
    outcome_details: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """End voice conversation session"""
    try:
        # Validate conversation access
        conversation = await conversation_service.get_conversation(conversation_id, db)
        if not conversation or conversation.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # End conversation
        result = await voice_service.end_conversation(
            conversation_id, outcome, outcome_details
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to end voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{conversation_id}/transfer")
async def transfer_to_human(
    conversation_id: str,
    reason: str,
    target_agent: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Transfer conversation to human agent"""
    try:
        # Validate conversation access
        conversation = await conversation_service.get_conversation(conversation_id, db)
        if not conversation or conversation.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Transfer conversation
        result = await voice_service.transfer_to_human(
            conversation_id, reason, target_agent
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to transfer conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synthesize")
async def synthesize_speech(
    request: TextToSpeechRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Response:
    """Convert text to speech using voice agent settings"""
    try:
        # Get voice agent
        voice_agent = await db.get(VoiceAgent, request.voice_agent_id)
        if not voice_agent or voice_agent.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Voice agent not found")
        
        # Generate speech using enhanced ElevenLabs service
        lang_map = {"en": Language.ENGLISH, "es": Language.SPANISH, "zh": Language.MANDARIN}
        format_map = {"mp3": AudioFormat.MP3, "wav": AudioFormat.WAV, "ogg": AudioFormat.OGG}
        
        synthesis_result = await elevenlabs_service.synthesize_speech(
            text=request.text,
            voice_agent=voice_agent,
            format=format_map.get(request.format, AudioFormat.MP3),
            language=lang_map.get(getattr(request, 'language', 'en'), Language.ENGLISH),
            optimize_for_speed=True
        )
        
        audio_data = synthesis_result.audio_data
        
        # Determine content type
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav", 
            "ogg": "audio/ogg"
        }
        content_type = content_type_map.get(request.format, "audio/mpeg")
        
        return Response(
            content=audio_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=speech.{request.format}",
                "X-Audio-Duration": str(synthesis_result.duration_ms / 1000),
                "X-Voice-Agent-ID": voice_agent.id,
                "X-Processing-Time-MS": str(synthesis_result.processing_time_ms),
                "X-Cached": str(synthesis_result.cached),
                "X-Quality-Score": str(synthesis_result.quality_score)
            }
        )
        
    except Exception as e:
        logger.error(f"Text-to-speech failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe", response_model=SpeechToTextResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization)
) -> SpeechToTextResponse:
    """Convert speech to text using Whisper"""
    try:
        # Validate audio file
        if audio.content_type not in ["audio/mpeg", "audio/wav", "audio/mp3", "audio/ogg"]:
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        audio_data = await audio.read()
        if len(audio_data) > 25 * 1024 * 1024:  # 25MB limit for Whisper
            raise HTTPException(status_code=413, detail="Audio file too large")
        
        # Transcribe audio
        import time
        start_time = time.time()
        
        transcript = await voice_service._speech_to_text(audio_data)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return SpeechToTextResponse(
            transcript=transcript,
            confidence=0.95,  # Whisper doesn't provide confidence scores
            duration_seconds=len(audio_data) / 16000,  # Approximate
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        logger.error(f"Speech-to-text failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_voice_performance(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization)
) -> Dict[str, Any]:
    """Get voice processing performance metrics"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        performance_stats = voice_service.performance_stats
        
        # Get enhanced health status including ElevenLabs service
        enhanced_health = await voice_service.get_voice_service_health()
        
        return {
            "performance": performance_stats,
            "service_status": enhanced_health["overall_status"],
            "elevenlabs_status": enhanced_health["elevenlabs_service"]["status"],
            "cache_hit_rate": enhanced_health["elevenlabs_service"].get("cache_hit_rate_percent", 0),
            "organization_id": current_org.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_voice_agents(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List available voice agents for organization"""
    try:
        # Query voice agents
        from sqlalchemy import select
        
        stmt = select(VoiceAgent).where(
            VoiceAgent.organization_id == current_org.id,
            VoiceAgent.is_active == True
        )
        result = await db.execute(stmt)
        agents = result.scalars().all()
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "type": agent.type.value,
                "status": agent.status.value,
                "phone_number": agent.phone_number,
                "total_conversations": agent.total_conversations,
                "success_rate": agent.success_rate,
                "can_handle_call": agent.can_handle_call()
            }
            for agent in agents
        ]

# Include streaming endpoints
router.include_router(streaming_router, prefix="/streaming", tags=["voice-streaming"])
        
    except Exception as e:
        logger.error(f"Failed to list voice agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))