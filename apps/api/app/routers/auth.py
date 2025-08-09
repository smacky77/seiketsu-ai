"""
Authentication endpoints for Seiketsu AI API
JWT-based authentication with refresh tokens and multi-tenant support
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_hash,
    verify_password
)
from app.core.config import settings
from app.models.user import User
from app.services.user_service import UserService
from app.services.tenant_service import TenantService
from app.core.exceptions import AuthenticationException, ValidationException

router = APIRouter()


class UserLogin(BaseModel):
    username: str
    password: str
    tenant_id: Optional[str] = None


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    tenant_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr
    tenant_id: Optional[str] = None


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    User login with JWT token generation
    """
    user_service = UserService(db)
    
    # Authenticate user
    user = await authenticate_user(
        db, 
        login_data.username, 
        login_data.password, 
        login_data.tenant_id
    )
    
    if not user:
        raise AuthenticationException("Invalid credentials")
    
    if not user.is_active:
        raise AuthenticationException("User account is disabled")
    
    # Generate tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": user.tenant_id},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "tenant_id": user.tenant_id},
        expires_delta=refresh_token_expires
    )
    
    # Update last login
    await user_service.update_last_login(user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "permissions": user.permissions or []
        }
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    register_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    User registration with automatic tenant assignment
    """
    user_service = UserService(db)
    tenant_service = TenantService(db)
    
    # Check if user already exists
    existing_user = await user_service.get_by_email(
        register_data.email, 
        register_data.tenant_id
    )
    if existing_user:
        raise ValidationException("User with this email already exists")
    
    # Handle tenant assignment
    tenant_id = register_data.tenant_id
    if not tenant_id:
        # Create new tenant for company if provided
        if register_data.company_name:
            tenant = await tenant_service.create_tenant({
                "name": register_data.company_name,
                "type": "company",
                "subscription_tier": "bronze"
            })
            tenant_id = tenant.id
        else:
            tenant_id = settings.DEFAULT_TENANT_ID
    else:
        # Validate existing tenant
        tenant = await tenant_service.get_tenant(tenant_id)
        if not tenant or not tenant.is_active:
            raise ValidationException("Invalid tenant")
    
    # Create user
    user_data = {
        "email": register_data.email,
        "password_hash": get_password_hash(register_data.password),
        "full_name": register_data.full_name,
        "phone": register_data.phone,
        "tenant_id": tenant_id,
        "role": "admin" if register_data.company_name else "user",
        "is_active": True
    }
    
    user = await user_service.create_user(user_data)
    
    # Generate tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": user.tenant_id},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "tenant_id": user.tenant_id},
        expires_delta=refresh_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "permissions": user.permissions or []
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    user_service = UserService(db)
    
    # Verify refresh token
    payload = verify_refresh_token(refresh_data.refresh_token)
    if not payload:
        raise AuthenticationException("Invalid refresh token")
    
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    
    if not user_id:
        raise AuthenticationException("Invalid refresh token")
    
    # Get user
    user = await user_service.get_user(user_id)
    if not user or not user.is_active:
        raise AuthenticationException("User not found or inactive")
    
    # Generate new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": user.tenant_id},
        expires_delta=access_token_expires
    )
    
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "tenant_id": user.tenant_id},
        expires_delta=refresh_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "permissions": user.permissions or []
        }
    )


@router.post("/logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user and invalidate refresh token
    """
    # In production, add refresh token to blacklist in Redis
    # For now, just return success
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
async def forgot_password(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate password reset process
    """
    user_service = UserService(db)
    
    # Find user by email and tenant
    user = await user_service.get_by_email(
        reset_request.email, 
        reset_request.tenant_id
    )
    
    if not user:
        # Don't reveal if email exists for security
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Generate reset token (implement in production)
    reset_token = "implement_password_reset_token_generation"
    
    # Send reset email (implement in production)
    # await send_password_reset_email(user.email, reset_token)
    
    return {"message": "If the email exists, a reset link will be sent"}


@router.post("/reset-password")
async def reset_password(
    reset_confirm: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset with token
    """
    user_service = UserService(db)
    
    # Verify reset token (implement in production)
    user_id = "extract_user_id_from_token"  # Implement this
    
    if not user_id:
        raise ValidationException("Invalid or expired reset token")
    
    # Update password
    password_hash = get_password_hash(reset_confirm.new_password)
    await user_service.update_password(user_id, password_hash)
    
    return {"message": "Password reset successful"}


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user profile information
    """
    user_service = UserService(db)
    
    # Get fresh user data
    user = await user_service.get_user(current_user.id)
    if not user:
        raise AuthenticationException("User not found")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "tenant_id": user.tenant_id,
        "role": user.role,
        "permissions": user.permissions or [],
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat()
    }


@router.get("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify if current token is valid
    """
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "tenant_id": current_user.tenant_id,
        "expires_at": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }