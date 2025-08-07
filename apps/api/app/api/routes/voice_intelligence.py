"""
Voice Intelligence API Routes
Real-time voice processing and conversation intelligence endpoints
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.voice_intelligence_service import voice_intelligence_service, ConversationContext, EmotionState
from app.models.user import User
from app.models.voice_agent import VoiceAgent
from app.models.conversation import Conversation

logger = logging.getLogger("seiketsu.voice_intelligence_api")

router = APIRouter(prefix="/api/v1/voice-intelligence", tags=["voice-intelligence"])

class VoiceProcessingRequest(BaseModel):
    agent_id: str
    conversation_context: Dict[str, Any]
    audio_format: str = "wav"
    sample_rate: int = 16000

class ConversationAnalysisRequest(BaseModel):
    conversation_id: str
    include_recommendations: bool = True

class DemoScenarioRequest(BaseModel):
    scenario_type: str = Field(..., description="Type of demo scenario")
    duration_minutes: Optional[int] = 5
    customizations: Optional[Dict[str, Any]] = None

class VoiceMetricsResponse(BaseModel):
    agent_id: str
    response_time: Dict[str, float]
    conversation_quality: Dict[str, float]
    business_metrics: Dict[str, float]
    technical_metrics: Dict[str, Any]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.conversation_sessions: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.conversation_sessions[session_id] = {
            "websocket": websocket,
            "connected_at": datetime.utcnow(),
            "conversation_context": None
        }
        logger.info(f"Voice intelligence session {session_id} connected")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id in self.conversation_sessions:
            del self.conversation_sessions[session_id]
        logger.info(f"Voice intelligence session {session_id} disconnected")

    async def send_personal_message(self, message: Dict, session_id: str):
        if session_id in self.conversation_sessions:
            websocket = self.conversation_sessions[session_id]["websocket"]
            await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

@router.websocket("/stream/{session_id}")
async def voice_stream_endpoint(
    websocket: WebSocket,
    session_id: str,
    agent_id: str,
    db=Depends(get_db)
):
    """Real-time voice processing WebSocket endpoint"""
    
    await manager.connect(websocket, session_id)
    
    try:
        # Initialize conversation context
        conversation_context = ConversationContext(
            lead_profile={},
            property_preferences={},
            conversation_history=[],
            emotion_timeline=[],
            current_intent="general_inquiry",
            confidence_score=0.0,
            objections=[],
            pain_points=[],
            hot_buttons=[]
        )
        
        manager.conversation_sessions[session_id]["conversation_context"] = conversation_context
        
        # Send connection confirmation
        await manager.send_personal_message({
            "type": "connected",
            "session_id": session_id,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }, session_id)
        
        while True:
            # Receive audio data or text messages
            data = await websocket.receive_bytes()
            
            # Process audio data
            async for response in voice_intelligence_service.process_real_time_conversation(
                data, conversation_context, agent_id
            ):
                # Send streaming response
                await manager.send_personal_message(response, session_id)
                
                # Update conversation context based on response
                if response["type"] == "emotion_detected":
                    emotion_state = EmotionState(
                        emotion=response["emotion"],
                        confidence=response["confidence"],
                        valence=response["valence"],
                        arousal=response["arousal"],
                        timestamp=datetime.fromisoformat(response["timestamp"].replace('Z', '+00:00'))
                    )
                    conversation_context.emotion_timeline.append(emotion_state)
                
                elif response["type"] == "intent_classified":
                    conversation_context.current_intent = response["intent"]
                    conversation_context.confidence_score = response["confidence"]
                
                elif response["type"] == "objection_detected":
                    conversation_context.objections.extend(response["objections"])
                
                elif response["type"] == "response_generated":
                    # Add to conversation history
                    conversation_context.conversation_history.append({
                        "speaker": "agent",
                        "text": response["text"],
                        "timestamp": response["timestamp"],
                        "strategy": response["strategy"]
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        logger.info(f"Voice intelligence session {session_id} disconnected")
    
    except Exception as e:
        logger.error(f"Voice stream error for session {session_id}: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "An error occurred during voice processing",
            "timestamp": datetime.utcnow().isoformat()
        }, session_id)

@router.post("/process-audio")
async def process_audio_file(
    file: UploadFile = File(...),
    agent_id: str = "default",
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """Process uploaded audio file for conversation analysis"""
    
    try:
        # Read audio file
        audio_data = await file.read()
        
        # Create basic conversation context
        conversation_context = ConversationContext(
            lead_profile={},
            property_preferences={},
            conversation_history=[],
            emotion_timeline=[],
            current_intent="general_inquiry",
            confidence_score=0.0,
            objections=[],
            pain_points=[],
            hot_buttons=[]
        )
        
        # Process audio
        results = []
        async for response in voice_intelligence_service.process_real_time_conversation(
            audio_data, conversation_context, agent_id
        ):
            results.append(response)
        
        return {
            "status": "processed",
            "results": results,
            "processing_complete": True
        }
    
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")

@router.post("/analyze-conversation")
async def analyze_conversation_quality(
    request: ConversationAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """Analyze conversation quality and provide insights"""
    
    try:
        analysis = await voice_intelligence_service.analyze_conversation_quality(
            request.conversation_id
        )
        
        return {
            "conversation_id": request.conversation_id,
            "analysis": analysis,
            "analyzed_at": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"Conversation analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/performance-metrics/{agent_id}")
async def get_voice_performance_metrics(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
) -> VoiceMetricsResponse:
    """Get real-time performance metrics for voice agent"""
    
    try:
        metrics = await voice_intelligence_service.get_performance_metrics(agent_id)
        
        return VoiceMetricsResponse(
            agent_id=agent_id,
            **metrics
        )
    
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@router.post("/demo-scenario")
async def create_demo_scenario(
    request: DemoScenarioRequest,
    current_user: User = Depends(get_current_user)
):
    """Create demo scenario for client presentations"""
    
    try:
        scenario = await voice_intelligence_service.create_demo_scenario(
            request.scenario_type
        )
        
        if "error" in scenario:
            raise HTTPException(status_code=404, detail=scenario["error"])
        
        # Apply customizations if provided
        if request.customizations:
            scenario["customizations"] = request.customizations
        
        return {
            "scenario_type": request.scenario_type,
            "scenario": scenario,
            "duration_minutes": request.duration_minutes,
            "created_at": datetime.utcnow()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo scenario creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scenario creation failed: {str(e)}")

@router.get("/demo-scenarios")
async def list_demo_scenarios(
    current_user: User = Depends(get_current_user)
):
    """List available demo scenarios"""
    
    scenarios = [
        {
            "type": "first_time_buyer",
            "name": "First-Time Home Buyer",
            "description": "Young professional looking to buy their first home",
            "duration_minutes": 5,
            "key_features": ["objection_handling", "education", "guidance"]
        },
        {
            "type": "luxury_buyer",
            "name": "Luxury Property Buyer",
            "description": "High-net-worth client seeking exclusive properties",
            "duration_minutes": 7,
            "key_features": ["luxury_tone", "exclusive_inventory", "white_glove_service"]
        },
        {
            "type": "investor",
            "name": "Real Estate Investor",
            "description": "Experienced investor looking for cash-flow properties",
            "duration_minutes": 6,
            "key_features": ["market_analysis", "roi_focus", "data_driven"]
        },
        {
            "type": "downsizing_senior",
            "name": "Downsizing Senior",
            "description": "Older couple looking to downsize their home",
            "duration_minutes": 8,
            "key_features": ["empathy", "patience", "lifestyle_focus"]
        },
        {
            "type": "urgent_relocation",
            "name": "Urgent Corporate Relocation",
            "description": "Executive needing to relocate quickly for work",
            "duration_minutes": 4,
            "key_features": ["efficiency", "urgency", "full_service"]
        }
    ]
    
    return {
        "scenarios": scenarios,
        "total_count": len(scenarios)
    }

@router.post("/test-voice-response")
async def test_voice_response(
    text: str,
    agent_id: str = "default",
    tone: str = "professional",
    current_user: User = Depends(get_current_user)
):
    """Test voice response generation"""
    
    try:
        from app.services.voice_intelligence_service import ResponseStrategy
        
        strategy = ResponseStrategy(
            tone=tone,
            pace="normal",
            emphasis_words=[],
            emotional_alignment="neutral",
            objection_handling=None,
            next_question=None
        )
        
        response = await voice_intelligence_service._generate_voice_response(
            text, agent_id, strategy
        )
        
        return {
            "text": text,
            "agent_id": agent_id,
            "tone": tone,
            "audio_url": response.get("url"),
            "generated_at": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"Voice response test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice test failed: {str(e)}")

@router.get("/conversation-templates")
async def get_conversation_templates(
    intent: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get conversation templates for different intents"""
    
    templates = {
        "property_search": {
            "opening": "I'd love to help you find the perfect property! What type of home are you looking for?",
            "follow_up_questions": [
                "What's your preferred location or neighborhood?",
                "What's your budget range?",
                "How many bedrooms and bathrooms do you need?",
                "Any specific features that are must-haves?"
            ],
            "objection_responses": {
                "price_too_high": "I understand budget is important. Let me show you some properties that offer great value in your range.",
                "wrong_location": "Location is key! Let's explore some nearby areas that might offer what you're looking for."
            }
        },
        "schedule_viewing": {
            "opening": "I'd be happy to schedule a viewing! When would be the best time for you?",
            "follow_up_questions": [
                "Would you prefer a weekday or weekend?",
                "Morning or afternoon works better?",
                "Should I schedule multiple properties for the same day?"
            ],
            "confirmation": "Perfect! I'll send you a confirmation with all the details."
        },
        "budget_discussion": {
            "opening": "Let's talk about your budget. What price range are you comfortable with?",
            "guidance": [
                "Have you spoken with a lender about pre-approval?",
                "Are you planning to put 20% down?",
                "Should we factor in any specific financing needs?"
            ],
            "reassurance": "Don't worry, we'll find something perfect within your budget."
        }
    }
    
    if intent and intent in templates:
        return {
            "intent": intent,
            "template": templates[intent]
        }
    
    return {
        "templates": templates,
        "available_intents": list(templates.keys())
    }

@router.get("/emotion-responses")
async def get_emotion_response_guide(
    current_user: User = Depends(get_current_user)
):
    """Get guide for responding to different emotions"""
    
    emotion_guide = {
        "anger": {
            "approach": "Stay calm, acknowledge concerns, focus on solutions",
            "tone": "empathetic",
            "pace": "slow",
            "phrases": [
                "I understand your frustration",
                "Let me help resolve this",
                "Your concerns are completely valid"
            ]
        },
        "fear": {
            "approach": "Provide reassurance, share expertise, offer support",
            "tone": "reassuring",
            "pace": "slow",
            "phrases": [
                "That's a common concern",
                "Let me walk you through this",
                "I'm here to guide you every step of the way"
            ]
        },
        "excitement": {
            "approach": "Match energy, maintain momentum, channel enthusiasm",
            "tone": "enthusiastic",
            "pace": "normal",
            "phrases": [
                "I love your excitement!",
                "This is going to be great",
                "Let's make this happen"
            ]
        },
        "confusion": {
            "approach": "Clarify, simplify, break down complex topics",
            "tone": "patient",
            "pace": "slow",
            "phrases": [
                "Let me explain that differently",
                "That's a great question",
                "I'll break this down step by step"
            ]
        },
        "skepticism": {
            "approach": "Provide evidence, share testimonials, be transparent",
            "tone": "authoritative",
            "pace": "normal",
            "phrases": [
                "I understand your hesitation",
                "Let me show you the data",
                "Here's what other clients have experienced"
            ]
        }
    }
    
    return {
        "emotion_response_guide": emotion_guide,
        "general_tips": [
            "Always validate the client's emotions",
            "Match appropriate energy levels",
            "Use specific examples and evidence",
            "Focus on solutions and next steps",
            "Maintain professional boundaries while being empathetic"
        ]
    }