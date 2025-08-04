"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import logging

logger = logging.getLogger("seiketsu.auth")

router = APIRouter()
security = HTTPBearer()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "agent"
    organization_id: str = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    refresh_token: str


@router.post("/register", status_code=201)
async def register_user(user_data: UserRegister) -> Dict[str, Any]:
    """Register a new user"""
    # Mock implementation for server startup
    return {
        "id": "mock_user_id",
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": user_data.role,
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_type": "bearer"
    }


@router.post("/login")
async def login_user(login_data: UserLogin) -> Dict[str, Any]:
    """Login user"""
    # Mock implementation for server startup
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_type": "bearer",
        "expires_in": 1800
    }


@router.post("/refresh")
async def refresh_token(token_data: TokenRefresh) -> Dict[str, Any]:
    """Refresh access token"""
    # Mock implementation for server startup
    return {
        "access_token": "new_mock_access_token",
        "refresh_token": "new_mock_refresh_token",
        "token_type": "bearer",
        "expires_in": 1800
    }


@router.post("/logout")
async def logout_user() -> Dict[str, str]:
    """Logout user"""
    # Mock implementation for server startup
    return {"message": "Successfully logged out"}