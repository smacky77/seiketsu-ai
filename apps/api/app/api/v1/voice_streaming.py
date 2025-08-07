"""
Enhanced Voice Streaming API Endpoints for Real-time Voice Processing
Supports WebSocket streaming, multi-language synthesis, and performance monitoring
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List, AsyncGenerator
from pydantic import BaseModel, Field
import logging
import json
import asyncio
import time
from datetime import datetime
import io

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_organization
from app.models.user import User
from app.models.organization import Organization
from app.models.voice_agent import VoiceAgent
from app.services.elevenlabs_service import elevenlabs_service, Language, AudioFormat
from app.services.voice_service import VoiceService
from app.tasks.voice_generation_tasks import pregenerate_agent_voices, voice_quality_analysis
from app.services.twentyonedev_service import analytics_service

logger = logging.getLogger("seiketsu.voice_streaming")
router = APIRouter()

# Initialize voice service
voice_service = VoiceService()

# WebSocket connection manager for streaming
class StreamingConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, voice_agent: VoiceAgent):
        await websocket.accept()
        self.active_connections[session_id] = {
            "websocket": websocket,
            "voice_agent": voice_agent,
            "connected_at": datetime.utcnow(),
            "messages_processed": 0,
            "total_processing_time": 0.0
        }
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            connection_info = self.active_connections[session_id]
            duration = (datetime.utcnow() - connection_info["connected_at"]).total_seconds()
            
            # Log session metrics
            logger.info(f"WebSocket session {session_id} ended: "
                       f"{connection_info['messages_processed']} messages, "
                       f"{duration:.1f}s duration")
            
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]["websocket"]
            await websocket.send_text(json.dumps(message))
    
    def get_connection_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.active_connections.get(session_id)
    
    def update_stats(self, session_id: str, processing_time_ms: float):
        if session_id in self.active_connections:
            conn = self.active_connections[session_id]
            conn["messages_processed"] += 1
            conn["total_processing_time"] += processing_time_ms

streaming_manager = StreamingConnectionManager()

# Request/Response Models
class StreamingSynthesisRequest(BaseModel):
    text: str = Field(..., max_length=5000)
    voice_agent_id: str
    language: str = Field(default="en", regex="^(en|es|zh)$")
    format: str = Field(default="mp3", regex="^(mp3|wav|ogg)$")
    optimize_for_speed: bool = True
    enable_caching: bool = True

class BulkSynthesisRequest(BaseModel):
    texts: List[str] = Field(..., max_items=50)
    voice_agent_id: str
    language: str = Field(default="en", regex="^(en|es|zh)$")
    background_processing: bool = False

class VoiceQualityRequest(BaseModel):
    text: str
    voice_agent_id: str
    quality_threshold: float = Field(default=0.8, ge=0.0, le=1.0)

class PregenerationRequest(BaseModel):
    voice_agent_id: str
    language: str = Field(default="en", regex="^(en|es|zh)$")
    custom_responses: Optional[List[str]] = None

@router.websocket("/stream/{session_id}")
async def voice_streaming_websocket(
    websocket: WebSocket,
    session_id: str,
    voice_agent_id: str,
    language: str = "en",
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time voice streaming with sub-second latency
    Supports bidirectional audio streaming and real-time synthesis
    """
    voice_agent = None
    
    try:
        # Get and validate voice agent
        voice_agent = await db.get(VoiceAgent, voice_agent_id)
        if not voice_agent or not voice_agent.is_active:
            await websocket.close(code=4004, reason="Voice agent not found or inactive")
            return
        
        # Connect to streaming manager
        await streaming_manager.connect(websocket, session_id, voice_agent)
        
        # Send initial connection confirmation
        await streaming_manager.send_message(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "voice_agent": {
                "id": voice_agent.id,
                "name": voice_agent.name,
                "language": language
            },
            "capabilities": {
                "streaming": True,
                "caching": True,
                "multi_language": True,
                "quality_monitoring": True
            }
        })
        
        # Main streaming loop
        while True:
            try:
                # Receive message from client
                raw_message = await websocket.receive_text()
                message = json.loads(raw_message)
                
                message_type = message.get("type")
                
                if message_type == "synthesize":
                    await handle_synthesis_message(session_id, message, voice_agent, language)
                elif message_type == "ping":
                    await streaming_manager.send_message(session_id, {"type": "pong"})
                elif message_type == "get_stats":
                    await handle_stats_request(session_id)
                else:
                    await streaming_manager.send_message(session_id, {
                        "type": "error",
                        "error": f"Unknown message type: {message_type}"
                    })
                    
            except json.JSONDecodeError:
                await streaming_manager.send_message(session_id, {
                    "type": "error",
                    "error": "Invalid JSON message"
                })
            except Exception as e:
                logger.error(f"Error processing message in session {session_id}: {e}")
                await streaming_manager.send_message(session_id, {
                    "type": "error",
                    "error": f"Processing error: {str(e)}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        streaming_manager.disconnect(session_id)

async def handle_synthesis_message(session_id: str, message: Dict[str, Any], voice_agent: VoiceAgent, language: str):
    """Handle voice synthesis message via WebSocket"""
    try:
        start_time = time.time()
        text = message.get("text", "")
        
        if not text or len(text.strip()) == 0:
            await streaming_manager.send_message(session_id, {
                "type": "error",
                "error": "Empty text provided"
            })
            return
        
        # Map language
        lang_map = {
            "en": Language.ENGLISH,
            "es": Language.SPANISH,
            "zh": Language.MANDARIN
        }
        
        # Synthesize speech
        synthesis_result = await elevenlabs_service.synthesize_speech(
            text=text,
            voice_agent=voice_agent,
            language=lang_map.get(language, Language.ENGLISH),
            optimize_for_speed=True,
            enable_caching=True
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Update connection stats
        streaming_manager.update_stats(session_id, processing_time_ms)
        
        # Send audio response
        await streaming_manager.send_message(session_id, {
            "type": "audio_response",
            "audio_data": synthesis_result.audio_data.hex(),  # Send as hex string
            "metadata": {
                "text": text,
                "voice_id": synthesis_result.voice_id,
                "duration_ms": synthesis_result.duration_ms,
                "processing_time_ms": processing_time_ms,
                "cached": synthesis_result.cached,
                "quality_score": synthesis_result.quality_score
            }
        })
        
        # Send analytics event
        await analytics_service.track_event("voice_streaming_synthesis", {
            "session_id": session_id,
            "voice_agent_id": voice_agent.id,
            "text_length": len(text),
            "processing_time_ms": processing_time_ms,
            "cached": synthesis_result.cached,
            "language": language
        })
        
    except Exception as e:
        logger.error(f"Synthesis failed for session {session_id}: {e}")
        await streaming_manager.send_message(session_id, {
            "type": "error",
            "error": f"Synthesis failed: {str(e)}"
        })

async def handle_stats_request(session_id: str):
    """Handle stats request via WebSocket"""
    try:
        connection_info = streaming_manager.get_connection_info(session_id)
        if connection_info:
            duration = (datetime.utcnow() - connection_info["connected_at"]).total_seconds()
            avg_processing_time = (connection_info["total_processing_time"] / 
                                 max(connection_info["messages_processed"], 1))
            
            await streaming_manager.send_message(session_id, {
                "type": "session_stats",
                "stats": {
                    "session_duration_seconds": duration,
                    "messages_processed": connection_info["messages_processed"],
                    "average_processing_time_ms": avg_processing_time,
                    "connected_at": connection_info["connected_at"].isoformat()
                }
            })
        
    except Exception as e:
        logger.error(f"Failed to get stats for session {session_id}: {e}")

@router.post("/synthesize/streaming")
async def streaming_synthesis(
    request: StreamingSynthesisRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Streaming voice synthesis endpoint - returns audio stream for large texts
    """
    try:
        # Get and validate voice agent
        voice_agent = await db.get(VoiceAgent, request.voice_agent_id)
        if not voice_agent or voice_agent.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Voice agent not found")
        
        # Map language and format
        lang_map = {
            "en": Language.ENGLISH,
            "es": Language.SPANISH,
            "zh": Language.MANDARIN
        }
        
        format_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg"
        }
        
        async def generate_audio_stream():
            """Generate streaming audio response"""
            try:
                async for chunk in elevenlabs_service.synthesize_streaming(
                    text=request.text,
                    voice_agent=voice_agent,
                    language=lang_map.get(request.language, Language.ENGLISH)
                ):
                    yield chunk
                    
            except Exception as e:
                logger.error(f"Streaming synthesis failed: {e}")
                # Send error as part of stream (client should handle)
                yield b""
        
        return StreamingResponse(
            generate_audio_stream(),
            media_type=format_map.get(request.format, "audio/mpeg"),
            headers={
                "X-Voice-Agent-ID": voice_agent.id,
                "X-Language": request.language,
                "X-Streaming": "true"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming synthesis endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synthesize/bulk")
async def bulk_synthesis(
    request: BulkSynthesisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk voice synthesis with optional background processing
    """
    try:
        # Get and validate voice agent
        voice_agent = await db.get(VoiceAgent, request.voice_agent_id)
        if not voice_agent or voice_agent.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Voice agent not found")
        
        if request.background_processing:
            # Process in background using Celery
            task = pregenerate_agent_voices.delay(
                agent_id=request.voice_agent_id,
                language=request.language
            )
            
            return {
                "status": "processing",
                "task_id": task.id,
                "texts_count": len(request.texts),
                "estimated_completion_seconds": len(request.texts) * 2  # Rough estimate
            }
        else:
            # Process synchronously
            lang_map = {
                "en": Language.ENGLISH,
                "es": Language.SPANISH,
                "zh": Language.MANDARIN
            }
            
            start_time = time.time()
            
            results = await elevenlabs_service.bulk_synthesize(
                texts=request.texts,
                voice_agent=voice_agent,
                language=lang_map.get(request.language, Language.ENGLISH)
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Schedule quality analysis in background
            synthesis_data = [
                {
                    "processing_time_ms": result.processing_time_ms,
                    "cached": result.cached,
                    "quality_score": result.quality_score
                }
                for result in results
            ]
            background_tasks.add_task(voice_quality_analysis.delay, synthesis_data)
            
            return {
                "status": "completed",
                "results_count": len(results),
                "processing_time_ms": processing_time_ms,
                "cache_hit_rate": sum(1 for r in results if r.cached) / len(results) * 100,
                "average_quality_score": sum(r.quality_score for r in results) / len(results)
            }
        
    except Exception as e:
        logger.error(f"Bulk synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quality/analyze")
async def analyze_voice_quality(
    request: VoiceQualityRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze voice synthesis quality and provide recommendations
    """
    try:
        # Get and validate voice agent
        voice_agent = await db.get(VoiceAgent, request.voice_agent_id)
        if not voice_agent or voice_agent.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Voice agent not found")
        
        # Synthesize and analyze quality
        synthesis_result = await elevenlabs_service.synthesize_speech(
            text=request.text,
            voice_agent=voice_agent,
            enable_caching=False  # Force fresh synthesis for quality analysis
        )
        
        # Get quality score
        quality_score = await elevenlabs_service.get_voice_quality_score(
            text=request.text,
            voice_agent=voice_agent,
            audio_data=synthesis_result.audio_data
        )
        
        # Generate recommendations
        recommendations = []
        if quality_score < request.quality_threshold:
            recommendations.append("Consider adjusting voice stability settings")
            if synthesis_result.processing_time_ms > 2000:
                recommendations.append("Processing time is high - check network connectivity")
            if len(synthesis_result.audio_data) < len(request.text) * 50:
                recommendations.append("Audio output seems compressed - verify voice settings")
        
        # Provide voice profile suggestions
        current_profile = elevenlabs_service._get_voice_profile_for_agent(voice_agent)
        profile_suggestions = []
        
        if quality_score < 0.7:
            for profile_name, profile in elevenlabs_service.voice_profiles.items():
                if profile.voice_id != current_profile.voice_id:
                    profile_suggestions.append({
                        "profile_name": profile_name,
                        "voice_id": profile.voice_id,
                        "persona": profile.persona
                    })
        
        return {
            "quality_score": quality_score,
            "meets_threshold": quality_score >= request.quality_threshold,
            "synthesis_metrics": {
                "processing_time_ms": synthesis_result.processing_time_ms,
                "audio_size_bytes": len(synthesis_result.audio_data),
                "duration_ms": synthesis_result.duration_ms,
                "voice_id": synthesis_result.voice_id
            },
            "recommendations": recommendations,
            "alternative_profiles": profile_suggestions[:3],  # Top 3 alternatives
            "current_profile": {
                "voice_id": current_profile.voice_id,
                "persona": current_profile.persona,
                "stability": current_profile.stability,
                "similarity_boost": current_profile.similarity_boost
            }
        }
        
    except Exception as e:
        logger.error(f"Voice quality analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pregenerate")
async def trigger_pregeneration(
    request: PregenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger pre-generation of common voice responses for an agent
    """
    try:
        # Get and validate voice agent
        voice_agent = await db.get(VoiceAgent, request.voice_agent_id)
        if not voice_agent or voice_agent.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Voice agent not found")
        
        # Start background pregeneration task
        task = pregenerate_agent_voices.delay(
            agent_id=request.voice_agent_id,
            language=request.language
        )
        
        return {
            "status": "initiated",
            "task_id": task.id,
            "voice_agent_id": request.voice_agent_id,
            "language": request.language,
            "estimated_completion_minutes": 5
        }
        
    except Exception as e:
        logger.error(f"Pregeneration trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/detailed")
async def get_detailed_voice_health(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization)
):
    """
    Get detailed voice service health and performance metrics
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get comprehensive health status
        health_status = await voice_service.get_voice_service_health()
        
        # Get active streaming connections
        active_connections = len(streaming_manager.active_connections)
        
        # Get ElevenLabs service metrics
        elevenlabs_health = await elevenlabs_service.health_check()
        
        return {
            "overall_health": health_status,
            "streaming_connections": {
                "active_count": active_connections,
                "connections": [
                    {
                        "session_id": sid,
                        "voice_agent_id": info["voice_agent"].id,
                        "messages_processed": info["messages_processed"],
                        "duration_seconds": (datetime.utcnow() - info["connected_at"]).total_seconds()
                    }
                    for sid, info in streaming_manager.active_connections.items()
                ]
            },
            "elevenlabs_service": elevenlabs_health,
            "performance_summary": {
                "target_response_time_ms": voice_service.target_response_time_ms,
                "average_response_time_ms": voice_service.average_response_time_ms,
                "requests_processed": len(voice_service.response_times),
                "cache_hit_rate": elevenlabs_health.get("cache_hit_rate_percent", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))