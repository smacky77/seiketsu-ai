"""
Voice Agents API endpoints
"""
from fastapi import APIRouter
from typing import Dict, Any
import logging

logger = logging.getLogger("seiketsu.voice_agents")
router = APIRouter()

@router.get("")
async def list_voice_agents() -> Dict[str, Any]:
    return {"agents": []}

@router.post("", status_code=201)
async def create_voice_agent() -> Dict[str, Any]:
    return {"id": "agent_123", "name": "Mock Agent", "created_at": "2024-01-01T00:00:00Z"}

@router.get("/{agent_id}")
async def get_voice_agent(agent_id: str) -> Dict[str, Any]:
    return {"id": agent_id, "name": "Mock Agent"}

@router.patch("/{agent_id}")
async def update_voice_agent(agent_id: str) -> Dict[str, Any]:
    return {"id": agent_id, "updated_at": "2024-01-01T00:00:00Z"}

@router.delete("/{agent_id}", status_code=204)
async def delete_voice_agent(agent_id: str):
    return None