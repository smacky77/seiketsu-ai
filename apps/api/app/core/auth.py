"""
Authentication and authorization for Seiketsu AI API
JWT-based authentication with role-based access control
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization

logger = logging.getLogger("seiketsu.auth")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handler
security = HTTPBearer()


class AuthService:
    """Authentication service for user management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    @staticmethod
    async def authenticate_user(
        email: str, 
        password: str, 
        db: AsyncSession
    ) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            # Get user by email
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Verify password
            if not AuthService.verify_password(password, user.hashed_password):
                return None
            
            # Check if user is active
            if not user.is_active or user.status not in ["active", "pending_verification"]:
                return None
            
            # Update login statistics
            user.update_login_stats()
            await db.commit()
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {e}")
            return None
    
    @staticmethod
    async def get_user_by_token(token: str, db: AsyncSession) -> Optional[User]:
        """Get user from JWT token"""
        payload = AuthService.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user and user.is_active:
                user.update_last_activity()
                await db.commit()
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by token: {e}")
            return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    
    user = await AuthService.get_user_by_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Get current user's organization"""
    try:
        stmt = select(Organization).where(Organization.id == current_user.organization_id)
        result = await db.execute(stmt)
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if organization.is_suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization is suspended"
            )
        
        return organization
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization"
        )


def require_role(*allowed_roles: UserRole):
    """Decorator to require specific user roles"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_checker


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )
        return current_user
    
    return permission_checker


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user if they are an admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_super_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user if they are a super admin"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


class TenantValidator:
    """Validate tenant access for multi-tenant resources"""
    
    @staticmethod
    def validate_tenant_access(
        resource_org_id: str,
        current_user: User,
        current_org: Organization
    ):
        """Validate user has access to resource in their tenant"""
        # Super admins can access any tenant
        if current_user.is_super_admin:
            return
        
        # Regular users can only access their own organization's resources
        if resource_org_id != current_org.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"  # Don't reveal it exists in another tenant
            )
    
    @staticmethod
    def get_tenant_filter(current_user: User, current_org: Organization) -> Optional[str]:
        """Get tenant filter for database queries"""
        # Super admins see all tenants
        if current_user.is_super_admin:
            return None
        
        # Regular users only see their organization
        return current_org.id


async def get_tenant_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization)
) -> Dict[str, Any]:
    """Get tenant context for request"""
    return {
        "user_id": current_user.id,
        "organization_id": current_org.id,
        "user_role": current_user.role,
        "is_admin": current_user.is_admin,
        "is_super_admin": current_user.is_super_admin,
        "tenant_slug": current_org.slug,
        "request_id": getattr(request.state, 'request_id', None)
    }


class APIKeyAuth:
    """API key authentication for external integrations"""
    
    @staticmethod
    async def validate_api_key(
        api_key: str,
        db: AsyncSession
    ) -> Optional[User]:
        """Validate API key and return associated user"""
        try:
            stmt = select(User).where(
                User.api_key == api_key,
                User.is_active == True
            )
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Check if API key is expired
            if user.api_key_expires and datetime.utcnow() > user.api_key_expires:
                return None
            
            # Update last activity
            user.update_last_activity()
            await db.commit()
            
            return user
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None


async def get_current_user_from_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from API key header"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    user = await APIKeyAuth.validate_api_key(api_key, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user


def create_auth_tokens(user: User) -> Dict[str, str]:
    """Create access and refresh tokens for user"""
    access_token_data = {
        "sub": user.id,
        "email": user.email,
        "org_id": user.organization_id,
        "role": user.role.value,
        "type": "access"
    }
    
    refresh_token_data = {
        "sub": user.id,
        "type": "refresh"
    }
    
    access_token = AuthService.create_access_token(access_token_data)
    refresh_token = AuthService.create_refresh_token(refresh_token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }