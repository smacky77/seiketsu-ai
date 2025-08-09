"""
Voice AI endpoints for Seiketsu AI API
Real-time voice synthesis, conversation management, and call handling
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import base64

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.voice_service import VoiceService
from app.services.conversation_service import ConversationService
from app.services.websocket_service import WebSocketManager
from app.core.exceptions import VoiceProcessingException, ValidationException

router = APIRouter()
websocket_manager = WebSocketManager()


class VoiceSynthesisRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    voice_settings: Optional[Dict[str, Any]] = None
    output_format: Optional[str] = "mp3_44100_128"


class ConversationStartRequest(BaseModel):
    context: Optional[Dict[str, Any]] = None
    voice_config: Optional[Dict[str, Any]] = None
    caller_info: Optional[Dict[str, Any]] = None


class ConversationMessage(BaseModel):
    message: str
    message_type: str = "user"  # user, agent, system
    timestamp: Optional[datetime] = None


class VoiceCallRequest(BaseModel):
    phone_number: str
    script_template: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None


@router.post("/synthesize")
async def synthesize_voice(
    request: VoiceSynthesisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Synthesize text to speech using ElevenLabs
    """
    voice_service = VoiceService(db)
    
    try:
        # Generate audio
        audio_data = await voice_service.synthesize_text(
            text=request.text,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            voice_id=request.voice_id,
            voice_settings=request.voice_settings,
            output_format=request.output_format
        )
        
        # Return audio stream
        def audio_generator():
            yield audio_data
        
        media_type = "audio/mpeg" if "mp3" in request.output_format else "audio/wav"
        
        return StreamingResponse(
            audio_generator(),
            media_type=media_type,
            headers={
                "Content-Disposition": "attachment; filename=synthesis.mp3",
                "Content-Length": str(len(audio_data))
            }
        )
        
    except Exception as e:
        raise VoiceProcessingException(
            message=f"Voice synthesis failed: {str(e)}",
            operation="synthesis",
            provider="elevenlabs"
        )


@router.post("/conversations")
async def start_conversation(
    request: ConversationStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new voice conversation session
    """
    conversation_service = ConversationService(db)
    
    conversation = await conversation_service.create_conversation(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        context=request.context or {},
        voice_config=request.voice_config or {},
        caller_info=request.caller_info
    )
    
    return {
        "conversation_id": str(conversation.id),
        "session_id": conversation.session_id,
        "status": conversation.status,
        "created_at": conversation.created_at.isoformat(),
        "websocket_url": f"/api/v1/voice/conversations/{conversation.id}/ws",
        "context": conversation.context
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation details and history
    """
    conversation_service = ConversationService(db)
    
    conversation = await conversation_service.get_conversation(
        conversation_id, 
        current_user.tenant_id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get conversation messages
    messages = await conversation_service.get_conversation_messages(conversation_id)
    
    return {
        "conversation_id": str(conversation.id),
        "session_id": conversation.session_id,
        "status": conversation.status,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "context": conversation.context,
        "caller_info": conversation.caller_info,
        "messages": [
            {
                "id": str(msg.id),
                "message": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.created_at.isoformat(),
                "metadata": msg.metadata
            }
            for msg in messages
        ],
        "analytics": {
            "duration": conversation.duration_seconds,
            "message_count": len(messages),
            "sentiment_score": conversation.sentiment_score,
            "lead_score": conversation.lead_score
        }
    }


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    message: ConversationMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message in a conversation
    """
    conversation_service = ConversationService(db)
    voice_service = VoiceService(db)
    
    # Verify conversation exists and user has access
    conversation = await conversation_service.get_conversation(
        conversation_id, 
        current_user.tenant_id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.status != "active":
        raise ValidationException("Conversation is not active")
    
    # Process user message
    user_message = await conversation_service.add_message(
        conversation_id=conversation_id,
        content=message.message,
        message_type=message.message_type,
        sender_id=current_user.id if message.message_type == "user" else None
    )
    
    # Generate AI response
    if message.message_type == "user":
        ai_response = await voice_service.generate_response(
            conversation_id=conversation_id,
            user_message=message.message,
            context=conversation.context
        )
        
        # Save AI response
        ai_message = await conversation_service.add_message(
            conversation_id=conversation_id,
            content=ai_response["text"],
            message_type="agent",
            metadata={
                "confidence": ai_response.get("confidence"),
                "intent": ai_response.get("intent"),
                "entities": ai_response.get("entities")
            }
        )
        
        # Synthesize response to audio if needed
        if conversation.voice_config.get("auto_synthesize", True):
            audio_data = await voice_service.synthesize_text(
                text=ai_response["text"],
                user_id=current_user.id,
                tenant_id=current_user.tenant_id,
                voice_id=conversation.voice_config.get("voice_id")
            )
            
            # Encode audio as base64 for JSON response
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        else:
            audio_base64 = None
        
        return {
            "user_message": {
                "id": str(user_message.id),
                "content": user_message.content,
                "timestamp": user_message.created_at.isoformat()
            },
            "ai_response": {
                "id": str(ai_message.id),
                "content": ai_message.content,
                "timestamp": ai_message.created_at.isoformat(),
                "metadata": ai_message.metadata,
                "audio": audio_base64
            }
        }
    
    return {
        "message": {
            "id": str(user_message.id),
            "content": user_message.content,
            "timestamp": user_message.created_at.isoformat()
        }
    }


@router.post("/conversations/{conversation_id}/end")
async def end_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    End a conversation and generate analytics
    """
    conversation_service = ConversationService(db)
    
    conversation = await conversation_service.end_conversation(
        conversation_id, 
        current_user.tenant_id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Generate conversation analytics
    analytics = await conversation_service.generate_analytics(conversation_id)
    
    return {
        "conversation_id": str(conversation.id),
        "status": conversation.status,
        "ended_at": conversation.updated_at.isoformat(),
        "analytics": analytics
    }


@router.websocket("/conversations/{conversation_id}/ws")
async def conversation_websocket(
    websocket: WebSocket,
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time conversation
    """
    await websocket.accept()
    
    try:
        # Add connection to manager
        await websocket_manager.connect(websocket, conversation_id)
        
        # Handle WebSocket messages
        while True:
            try:
                # Wait for message from client
                data = await websocket.receive_json()
                
                # Process message based on type
                if data.get("type") == "message":
                    # Handle text message
                    message_content = data.get("content")
                    if message_content:
                        # Process through conversation service
                        response = await process_websocket_message(
                            conversation_id, message_content, db
                        )
                        
                        # Send response back to client
                        await websocket.send_json({
                            "type": "response",
                            "content": response["text"],
                            "metadata": response.get("metadata", {}),
                            "audio": response.get("audio")  # Base64 encoded audio
                        })
                
                elif data.get("type") == "audio":
                    # Handle audio input
                    audio_data = data.get("data")  # Base64 encoded audio
                    if audio_data:
                        # Process audio input
                        response = await process_websocket_audio(
                            conversation_id, audio_data, db
                        )
                        
                        await websocket.send_json({
                            "type": "response",
                            "content": response["text"],
                            "metadata": response.get("metadata", {}),
                            "audio": response.get("audio")
                        })
                
                elif data.get("type") == "ping":
                    # Handle ping for connection keep-alive
                    await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        pass
    finally:
        # Clean up connection
        websocket_manager.disconnect(websocket)


@router.post("/calls/initiate")
async def initiate_voice_call(
    request: VoiceCallRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate an outbound voice call
    """
    voice_service = VoiceService(db)
    
    try:
        call_result = await voice_service.initiate_call(
            phone_number=request.phone_number,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            script_template=request.script_template,
            context=request.context or {},
            callback_url=request.callback_url
        )
        
        return {
            "call_id": call_result["call_id"],
            "status": call_result["status"],
            "phone_number": request.phone_number,
            "initiated_at": datetime.utcnow().isoformat(),
            "estimated_duration": call_result.get("estimated_duration"),
            "callback_url": request.callback_url
        }
        
    except Exception as e:
        raise VoiceProcessingException(
            message=f"Call initiation failed: {str(e)}",
            operation="call_initiation",
            provider="twilio"
        )


@router.get("/calls/{call_id}")
async def get_call_status(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status and details of a voice call
    """
    voice_service = VoiceService(db)
    
    call = await voice_service.get_call_status(call_id, current_user.tenant_id)
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return {
        "call_id": call_id,
        "status": call["status"],
        "duration": call.get("duration"),
        "cost": call.get("cost"),
        "recording_url": call.get("recording_url"),
        "transcript": call.get("transcript"),
        "analytics": call.get("analytics"),
        "created_at": call["created_at"],
        "updated_at": call["updated_at"]
    }


@router.get("/voices")
async def list_available_voices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List available voices for synthesis
    """
    voice_service = VoiceService(db)
    
    voices = await voice_service.get_available_voices(current_user.tenant_id)
    
    return {
        "voices": voices,
        "default_voice": voices[0] if voices else None,
        "total": len(voices)
    }


@router.post("/audio/upload")
async def upload_audio_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process audio file for transcription
    """
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise ValidationException("File must be an audio file")
    
    voice_service = VoiceService(db)
    
    try:
        # Read file content
        audio_content = await file.read()
        
        # Process audio file
        result = await voice_service.process_audio_file(
            audio_content=audio_content,
            filename=file.filename,
            content_type=file.content_type,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        
        return {
            "file_id": result["file_id"],
            "transcription": result.get("transcription"),
            "duration": result.get("duration"),
            "language": result.get("language"),
            "confidence": result.get("confidence"),
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise VoiceProcessingException(
            message=f"Audio processing failed: {str(e)}",
            operation="audio_upload"
        )


async def process_websocket_message(
    conversation_id: str, 
    message: str, 
    db: AsyncSession
) -> Dict[str, Any]:
    """Process WebSocket text message"""
    conversation_service = ConversationService(db)
    voice_service = VoiceService(db)
    
    # Add user message
    await conversation_service.add_message(
        conversation_id=conversation_id,
        content=message,
        message_type="user"
    )
    
    # Generate AI response
    response = await voice_service.generate_response(
        conversation_id=conversation_id,
        user_message=message,
        context={}
    )
    
    # Add AI response message
    await conversation_service.add_message(
        conversation_id=conversation_id,
        content=response["text"],
        message_type="agent",
        metadata=response.get("metadata", {})
    )
    
    return response


async def process_websocket_audio(
    conversation_id: str, 
    audio_data: str, 
    db: AsyncSession
) -> Dict[str, Any]:
    """Process WebSocket audio message"""
    voice_service = VoiceService(db)
    
    # Decode base64 audio
    audio_bytes = base64.b64decode(audio_data)
    
    # Transcribe audio to text
    transcription = await voice_service.transcribe_audio(audio_bytes)
    
    # Process as text message
    response = await process_websocket_message(
        conversation_id, transcription["text"], db
    )
    
    # Synthesize response to audio
    audio_response = await voice_service.synthesize_text(
        text=response["text"],
        user_id=None,  # WebSocket context
        tenant_id=None,  # Will be extracted from conversation
    )
    
    # Encode response audio as base64
    response["audio"] = base64.b64encode(audio_response).decode('utf-8')
    
    return response