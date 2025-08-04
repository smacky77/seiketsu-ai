"""
BMAD Method Phase 2: Backend Integration
Enhanced with @21st-extension/toolbar development workflow
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uvicorn

# Import your existing models and database
from app.core.database import get_db
from app.models import User, VoiceAgent, Property, Lead
from app.services.voice_service import VoiceService
from app.services.property_service import PropertyService
from app.services.leads_service import LeadsService
from app.services.market_service import MarketService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Seiketsu AI Voice Agent Platform",
    description="BMAD Method Phase 2: Backend Integration with @21st-extension/toolbar",
    version="2.0.0"
)

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, channel: str, user_id: str = None):
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        
        self.active_connections[channel].append(websocket)
        
        if user_id:
            self.user_connections[user_id] = websocket
        
        logger.info(f"WebSocket connected to channel: {channel}")
    
    def disconnect(self, websocket: WebSocket, channel: str, user_id: str = None):
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)
        
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected from channel: {channel}")
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_text(message)
    
    async def broadcast_to_channel(self, message: str, channel: str):
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove dead connections
                    self.active_connections[channel].remove(connection)

manager = ConnectionManager()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    # Implement your JWT token validation here
    # For now, returning a mock user
    user = db.query(User).first()  # Replace with actual token validation
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# Voice Agent Endpoints
@app.post("/api/voice/agents")
async def create_voice_agent(agent_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new voice agent with ElevenLabs integration"""
    voice_service = VoiceService(db)
    agent = await voice_service.create_agent(agent_data, current_user.id)
    
    # Broadcast update to connected clients
    await manager.broadcast_to_channel(
        json.dumps({
            "type": "agent_created",
            "payload": {"agent_id": agent.id, "name": agent.name}
        }),
        "voice"
    )
    
    return agent

@app.get("/api/voice/agents")
async def get_voice_agents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all voice agents for the current tenant"""
    voice_service = VoiceService(db)
    agents = await voice_service.get_agents_by_tenant(current_user.tenant_id)
    return {"agents": agents}

@app.post("/api/voice/synthesis")
async def synthesize_speech(synthesis_request: dict, current_user: User = Depends(get_current_user)):
    """Synthesize speech using ElevenLabs"""
    voice_service = VoiceService()
    result = await voice_service.synthesize_speech(
        text=synthesis_request["text"],
        voice_id=synthesis_request["voiceId"],
        settings=synthesis_request.get("settings", {})
    )
    return result

@app.post("/api/voice/recognition")
async def recognize_speech(audio_data: bytes, current_user: User = Depends(get_current_user)):
    """Recognize speech from audio data"""
    voice_service = VoiceService()
    result = await voice_service.recognize_speech(audio_data)
    return result

# Real Estate Property Endpoints
@app.get("/api/properties/search")
async def search_properties(
    location: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    property_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search properties with advanced filters"""
    property_service = PropertyService(db)
    
    search_params = {
        "location": location,
        "min_price": min_price,
        "max_price": max_price,
        "property_type": property_type,
        "tenant_id": current_user.tenant_id
    }
    
    properties = await property_service.search_properties(search_params)
    return {"properties": properties, "total": len(properties)}

@app.post("/api/properties/mls/sync")
async def sync_mls_data(sync_params: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Sync property data with MLS"""
    property_service = PropertyService(db)
    
    # Start background sync job
    job_id = await property_service.start_mls_sync(
        region=sync_params.get("region"),
        tenant_id=current_user.tenant_id
    )
    
    return {"status": "started", "jobId": job_id, "estimated": 300}

# Lead Management Endpoints
@app.get("/api/leads")
async def get_leads(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get leads with filtering and pagination"""
    leads_service = LeadsService(db)
    
    leads = await leads_service.get_leads(
        tenant_id=current_user.tenant_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    total = await leads_service.count_leads(current_user.tenant_id, status)
    
    return {
        "leads": leads,
        "total": total,
        "pagination": {
            "page": offset // limit + 1,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit
        }
    }

@app.post("/api/leads/{lead_id}/qualify")
async def qualify_lead(lead_id: str, qualification_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Qualify a lead using AI algorithms"""
    leads_service = LeadsService(db)
    
    result = await leads_service.qualify_lead(
        lead_id=lead_id,
        data=qualification_data,
        user_id=current_user.id
    )
    
    # Broadcast lead qualification update
    await manager.broadcast_to_channel(
        json.dumps({
            "type": "lead_qualified",
            "payload": {"lead_id": lead_id, "score": result["score"], "status": result["status"]}
        }),
        "leads"
    )
    
    return result

# Market Intelligence Endpoints
@app.get("/api/market/trends")
async def get_market_trends(
    location: Optional[str] = None,
    period: str = "3_months",
    current_user: User = Depends(get_current_user)
):
    """Get market trends and analytics"""
    market_service = MarketService()
    
    trends = await market_service.get_market_trends(
        location=location,
        period=period,
        tenant_id=current_user.tenant_id
    )
    
    return trends

@app.get("/api/market/insights")
async def get_market_insights(
    location: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered market insights"""
    market_service = MarketService()
    
    insights = await market_service.get_market_insights(
        location=location,
        tenant_id=current_user.tenant_id
    )
    
    return {"insights": insights, "total": len(insights)}

# WebSocket Endpoints for Real-time Features
@app.websocket("/ws/voice/{agent_id}")
async def voice_websocket_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time voice processing"""
    await manager.connect(websocket, f"voice_{agent_id}")
    
    try:
        while True:
            # Receive audio data or text messages
            data = await websocket.receive_bytes()
            
            # Process audio data with voice agent
            voice_service = VoiceService()
            response = await voice_service.process_real_time_audio(agent_id, data)
            
            # Send response back to client
            await websocket.send_json({
                "type": "voice_response",
                "payload": response
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"voice_{agent_id}")

@app.websocket("/ws/notifications")
async def notifications_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications"""
    await manager.connect(websocket, "notifications")
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket.send_json({
                "type": "ping",
                "payload": {"timestamp": datetime.now().isoformat()}
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "notifications")

@app.websocket("/ws/analytics")
async def analytics_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time analytics updates"""
    await manager.connect(websocket, "analytics")
    
    try:
        while True:
            # Send periodic analytics updates
            await asyncio.sleep(60)
            
            # Get latest analytics data
            analytics_data = {
                "leads": {"new": 5, "qualified": 12, "converted": 3},
                "properties": {"new_listings": 15, "price_changes": 8},
                "voice": {"conversations": 45, "success_rate": 0.78}
            }
            
            await websocket.send_json({
                "type": "analytics_update",
                "payload": analytics_data
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "analytics")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "phase": "BMAD Phase 2 - Backend Integration"
    }

# @21st-extension/toolbar integration endpoint
@app.get("/api/toolbar/status")
async def toolbar_status():
    """Status endpoint for @21st-extension/toolbar integration"""
    return {
        "toolbar_enabled": True,
        "features": {
            "voice_processing": True,
            "real_estate_data": True,
            "lead_qualification": True,
            "market_intelligence": True
        },
        "websocket_channels": list(manager.active_connections.keys()),
        "active_connections": sum(len(conns) for conns in manager.active_connections.values())
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "bmad_integration:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )