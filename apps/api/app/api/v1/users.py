"""
Users API endpoints
"""
from fastapi import APIRouter
from typing import Dict, Any
import logging

logger = logging.getLogger("seiketsu.users")
router = APIRouter()


@router.get("/profile")
async def get_user_profile() -> Dict[str, Any]:
    """Get user profile"""
    return {
        "id": "mock_user_id",
        "email": "user@example.com",
        "full_name": "Mock User",
        "role": "agent",
        "organization_id": "org_123"
    }


@router.put("/profile")
async def update_user_profile() -> Dict[str, Any]:
    """Update user profile"""
    return {"message": "Profile updated successfully"}


@router.post("/change-password")
async def change_password() -> Dict[str, str]:
    """Change user password"""
    return {"message": "Password updated successfully"}