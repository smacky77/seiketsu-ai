"""
Admin API endpoints
"""
from fastapi import APIRouter
from typing import Dict, Any
import logging

logger = logging.getLogger("seiketsu.admin")
router = APIRouter()

@router.get("/users")
async def list_organization_users() -> Dict[str, Any]:
    return {"users": [], "total": 0}

@router.get("/system/status")
async def get_system_status() -> Dict[str, Any]:
    return {
        "status": "operational",
        "active_users": 0,
        "system_load": 0.1,
        "database_status": "healthy"
    }