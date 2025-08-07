"""
Enhanced Voice Processing API Endpoints
Additional endpoints for the complete voice API specification
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_organization
from app.models.user import User
from app.models.organization import Organization
from app.models.conversation import Conversation
from app.services.voice_service import VoiceService
from app.api.v1.voice import VoiceSessionRequest, manager

logger = logging.getLogger("seiketsu.voice_enhanced")
router = APIRouter()

# Initialize services
voice_service = VoiceService()

@router.post("/initiate", status_code=201)
async def initiate_voice_conversation(
    request: VoiceSessionRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Initiate a new voice conversation session"""
    try:
        from app.models.voice_agent import VoiceAgent
        
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
            "success": True,
            "conversation_id": conversation.id,
            "session_id": conversation.session_id,
            "status": conversation.status.value,
            "voice_agent": {
                "id": voice_agent.id,
                "name": voice_agent.name,
                "phone_number": voice_agent.phone_number,
                "voice_settings": voice_agent.voice_settings
            },
            "websocket_url": f"/api/v1/voice/ws/{conversation.session_id}",
            "started_at": conversation.started_at.isoformat(),
            "estimated_response_time_ms": voice_service.get_estimated_response_time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate voice conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate conversation")

@router.get("/status/{session_id}")
async def get_conversation_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get real-time status of voice conversation"""
    try:
        # Find conversation by session_id
        from sqlalchemy import select
        stmt = select(Conversation).where(
            Conversation.session_id == session_id,
            Conversation.organization_id == current_org.id
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get real-time metrics
        current_metrics = await voice_service.get_conversation_metrics(conversation.id)
        
        return {
            "session_id": session_id,
            "conversation_id": conversation.id,
            "status": conversation.status.value,
            "is_active": conversation.is_active,
            "duration_seconds": conversation.duration_seconds or 0,
            "started_at": conversation.started_at.isoformat(),
            "last_activity_at": conversation.updated_at.isoformat(),
            "voice_agent": {
                "id": conversation.voice_agent.id,
                "name": conversation.voice_agent.name,
                "status": conversation.voice_agent.status.value
            },
            "metrics": current_metrics,
            "lead_generated": bool(conversation.lead_id),
            "sentiment_score": conversation.sentiment_score,
            "transferred_to_human": conversation.transferred_to_human,
            "websocket_connected": session_id in manager.active_connections
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation status")