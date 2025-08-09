"""
API Key Management System
Handles API key generation, validation, and management for programmatic access
"""
import enum
import logging
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy import (
    Boolean, Column, String, DateTime, Text, Integer,
    JSON, Enum, ForeignKey, Index, select, and_
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.base import BaseModel
from app.models.client import Client
from app.models.audit import ClientAuditLog, AuditEventType, AuditSeverity
from app.core.cache import get_redis_client


logger = logging.getLogger(__name__)


class APIKeyScope(str, enum.Enum):
    """API key access scopes"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    VOICE_AGENT = "voice_agent"
    ANALYTICS = "analytics"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class APIKeyStatus(str, enum.Enum):
    """API key status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class APIKeyValidationResult:
    """Result of API key validation"""
    valid: bool
    key_id: Optional[str] = None
    client_id: Optional[str] = None
    scopes: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    rate_limit_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None


class APIKey(BaseModel):
    """
    API Key model for programmatic access
    """
    __tablename__ = "api_keys"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # Key details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    key_hash = Column(String(128), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    
    # Access control
    scopes = Column(JSONB, nullable=False, default=list)
    permissions = Column(JSONB, nullable=False, default=list)
    ip_whitelist = Column(JSONB, nullable=True)  # Allowed IP addresses
    
    # Status and lifecycle
    status = Column(Enum(APIKeyStatus), nullable=False, default=APIKeyStatus.ACTIVE)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    auto_rotate = Column(Boolean, nullable=False, default=False)
    rotation_interval_days = Column(Integer, nullable=True)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    total_requests = Column(Integer, nullable=False, default=0)
    rate_limit_per_hour = Column(Integer, nullable=True)
    rate_limit_per_day = Column(Integer, nullable=True)
    
    # Security
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=False, default=dict)
    
    # Relationships
    client = relationship("Client")
    usage_logs = relationship(
        "APIKeyUsageLog",
        back_populates="api_key",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_api_key_client_status', 'client_id', 'status'),
        Index('idx_api_key_expires_at', 'expires_at'),
        Index('idx_api_key_created_by', 'created_by_user_id'),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if API key is active"""
        return (
            self.status == APIKeyStatus.ACTIVE and
            (self.expires_at is None or self.expires_at > datetime.now(timezone.utc))
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        return (
            self.expires_at is not None and
            self.expires_at <= datetime.now(timezone.utc)
        )
    
    @property
    def needs_rotation(self) -> bool:
        """Check if API key needs rotation"""
        if not self.auto_rotate or not self.rotation_interval_days:
            return False
        
        rotation_date = self.created_at + timedelta(days=self.rotation_interval_days)
        return datetime.now(timezone.utc) >= rotation_date
    
    def can_access_from_ip(self, ip_address: str) -> bool:
        """Check if API key can be used from given IP"""
        if not self.ip_whitelist:
            return True
        
        from ipaddress import ip_address as ip_addr, ip_network
        
        try:
            client_ip = ip_addr(ip_address)
            for allowed in self.ip_whitelist:
                if client_ip in ip_network(allowed, strict=False):
                    return True
        except Exception:
            return False
        
        return False
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert API key to dictionary"""
        data = {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "name": self.name,
            "description": self.description,
            "key_prefix": self.key_prefix,
            "scopes": self.scopes,
            "permissions": self.permissions,
            "status": self.status.value,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "needs_rotation": self.needs_rotation,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "total_requests": self.total_requests,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "rate_limit_per_day": self.rate_limit_per_day,
            "auto_rotate": self.auto_rotate,
            "rotation_interval_days": self.rotation_interval_days,
            "metadata": self.metadata,
        }
        
        if include_sensitive:
            data.update({
                "ip_whitelist": self.ip_whitelist,
                "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
                "revocation_reason": self.revocation_reason,
            })
        
        return data


class APIKeyUsageLog(BaseModel):
    """
    API Key usage logging
    """
    __tablename__ = "api_key_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False)
    
    # Request details
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True)
    
    # Usage metrics
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    # Additional context
    metadata = Column(JSONB, nullable=False, default=dict)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_key_usage_key_timestamp', 'api_key_id', 'timestamp'),
        Index('idx_api_key_usage_endpoint', 'endpoint'),
        Index('idx_api_key_usage_status', 'status_code'),
        Index('idx_api_key_usage_timestamp', 'timestamp'),
    )


class APIKeyManager:
    """
    API Key Management Service
    """
    
    def __init__(self):
        self.key_length = 64  # Length of generated API keys
        self.prefix_length = 8  # Length of key prefix for identification
        self.default_rate_limit_per_hour = 1000
        self.default_rate_limit_per_day = 10000
        
        # Scope-based permissions mapping
        self.scope_permissions = {
            APIKeyScope.READ_ONLY: [
                "user:read", "org:read", "voice_agent:read",
                "conversation:read", "property:read", "lead:read",
                "analytics:read", "api:read"
            ],
            APIKeyScope.READ_WRITE: [
                "user:read", "org:read", "voice_agent:read", "voice_agent:update",
                "conversation:read", "conversation:update",
                "property:read", "property:create", "property:update",
                "lead:read", "lead:create", "lead:update",
                "analytics:read", "api:read", "api:write"
            ],
            APIKeyScope.ADMIN: [
                "user:*", "org:*", "voice_agent:*",
                "conversation:*", "property:*", "lead:*",
                "analytics:*", "api:*", "webhook:*"
            ],
            APIKeyScope.VOICE_AGENT: [
                "voice_agent:read", "voice_agent:update", "voice_agent:deploy",
                "conversation:read", "conversation:create", "conversation:update",
                "api:read", "api:write"
            ],
            APIKeyScope.ANALYTICS: [
                "analytics:read", "analytics:export",
                "conversation:read", "property:read", "lead:read",
                "api:read"
            ],
            APIKeyScope.WEBHOOK: [
                "webhook:read", "webhook:test",
                "conversation:read", "lead:read",
                "api:read"
            ]
        }
    
    async def create_api_key(
        self,
        session: AsyncSession,
        client_id: str,
        name: str,
        scopes: List[str],
        created_by_user_id: Optional[str] = None,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        ip_whitelist: Optional[List[str]] = None,
        rate_limit_per_hour: Optional[int] = None,
        rate_limit_per_day: Optional[int] = None,
        auto_rotate: bool = False,
        rotation_interval_days: Optional[int] = None,
        custom_permissions: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Create a new API key
        
        Returns:
            (success, api_key, key_info)
        """
        
        try:
            # Validate client
            client = await session.get(Client, client_id)
            if not client:
                return False, None, {"error": "Client not found"}
            
            # Validate scopes
            invalid_scopes = [s for s in scopes if s not in [scope.value for scope in APIKeyScope]]
            if invalid_scopes:
                return False, None, {"error": f"Invalid scopes: {invalid_scopes}"}
            
            # Generate API key
            raw_key = self._generate_api_key()
            key_hash = self._hash_api_key(raw_key)
            key_prefix = raw_key[:self.prefix_length]
            
            # Calculate permissions from scopes
            permissions = set()
            for scope in scopes:
                scope_enum = APIKeyScope(scope)
                scope_perms = self.scope_permissions.get(scope_enum, [])
                permissions.update(scope_perms)
            
            # Add custom permissions
            if custom_permissions:
                permissions.update(custom_permissions)
            
            # Create API key record
            api_key = APIKey(
                client_id=client_id,
                name=name,
                description=description,
                key_hash=key_hash,
                key_prefix=key_prefix,
                scopes=scopes,
                permissions=list(permissions),
                ip_whitelist=ip_whitelist,
                created_by_user_id=created_by_user_id,
                expires_at=expires_at,
                rate_limit_per_hour=rate_limit_per_hour or self.default_rate_limit_per_hour,
                rate_limit_per_day=rate_limit_per_day or self.default_rate_limit_per_day,
                auto_rotate=auto_rotate,
                rotation_interval_days=rotation_interval_days
            )
            
            session.add(api_key)
            await session.commit()
            
            # Log creation
            await self._log_key_event(
                session, str(api_key.id), client_id,
                AuditEventType.DATA_CREATE,
                f"API key '{name}' created",
                created_by_user_id
            )
            
            key_info = {
                "id": str(api_key.id),
                "name": name,
                "scopes": scopes,
                "permissions": list(permissions),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "created_at": api_key.created_at.isoformat()
            }
            
            return True, raw_key, key_info
            
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            await session.rollback()
            return False, None, {"error": str(e)}
    
    async def validate_api_key(
        self,
        session: AsyncSession,
        raw_key: str,
        ip_address: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> APIKeyValidationResult:
        """
        Validate API key and return permissions
        """
        
        try:
            key_hash = self._hash_api_key(raw_key)
            
            # Find API key
            query = select(APIKey).where(
                and_(
                    APIKey.key_hash == key_hash,
                    APIKey.status == APIKeyStatus.ACTIVE
                )
            )
            result = await session.execute(query)
            api_key = result.scalar_one_or_none()
            
            if not api_key:
                return APIKeyValidationResult(
                    valid=False,
                    error_message="Invalid API key"
                )
            
            # Check expiration
            if api_key.is_expired:
                api_key.status = APIKeyStatus.EXPIRED
                await session.commit()
                
                return APIKeyValidationResult(
                    valid=False,
                    error_message="API key has expired"
                )
            
            # Check IP restrictions
            if ip_address and not api_key.can_access_from_ip(ip_address):
                await self._log_security_event(
                    session, str(api_key.id), api_key.client_id,
                    f"API key access denied from IP {ip_address}"
                )
                
                return APIKeyValidationResult(
                    valid=False,
                    error_message="Access from this IP address is not permitted"
                )
            
            # Check rate limits
            rate_limit_info = await self._check_rate_limits(api_key)
            if not rate_limit_info["allowed"]:
                return APIKeyValidationResult(
                    valid=False,
                    error_message="Rate limit exceeded",
                    rate_limit_info=rate_limit_info
                )
            
            # Update usage
            api_key.last_used_at = datetime.now(timezone.utc)
            api_key.total_requests += 1
            
            return APIKeyValidationResult(
                valid=True,
                key_id=str(api_key.id),
                client_id=str(api_key.client_id),
                scopes=api_key.scopes,
                permissions=api_key.permissions,
                rate_limit_info=rate_limit_info,
                expires_at=api_key.expires_at
            )
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return APIKeyValidationResult(
                valid=False,
                error_message="API key validation failed"
            )
    
    async def revoke_api_key(
        self,
        session: AsyncSession,
        key_id: str,
        revoked_by_user_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Revoke an API key
        """
        
        try:
            api_key = await session.get(APIKey, key_id)
            if not api_key:
                return False
            
            api_key.status = APIKeyStatus.REVOKED
            api_key.revoked_at = datetime.now(timezone.utc)
            api_key.revoked_by_user_id = revoked_by_user_id
            api_key.revocation_reason = reason
            
            await session.commit()
            
            # Log revocation
            await self._log_key_event(
                session, key_id, str(api_key.client_id),
                AuditEventType.DATA_DELETE,
                f"API key '{api_key.name}' revoked: {reason or 'No reason provided'}",
                revoked_by_user_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            await session.rollback()
            return False
    
    async def rotate_api_key(
        self,
        session: AsyncSession,
        key_id: str,
        rotated_by_user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Rotate an API key (generate new key, keep same permissions)
        """
        
        try:
            api_key = await session.get(APIKey, key_id)
            if not api_key:
                return False, None
            
            # Generate new key
            new_raw_key = self._generate_api_key()
            new_key_hash = self._hash_api_key(new_raw_key)
            new_key_prefix = new_raw_key[:self.prefix_length]
            
            # Update key
            api_key.key_hash = new_key_hash
            api_key.key_prefix = new_key_prefix
            api_key.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
            
            # Log rotation
            await self._log_key_event(
                session, key_id, str(api_key.client_id),
                AuditEventType.DATA_UPDATE,
                f"API key '{api_key.name}' rotated",
                rotated_by_user_id
            )
            
            return True, new_raw_key
            
        except Exception as e:
            logger.error(f"Error rotating API key: {e}")
            await session.rollback()
            return False, None
    
    async def get_client_api_keys(
        self,
        session: AsyncSession,
        client_id: str,
        include_revoked: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all API keys for a client
        """
        
        try:
            query = select(APIKey).where(APIKey.client_id == client_id)
            
            if not include_revoked:
                query = query.where(APIKey.status != APIKeyStatus.REVOKED)
            
            result = await session.execute(query.order_by(APIKey.created_at.desc()))
            api_keys = result.scalars().all()
            
            return [key.to_dict() for key in api_keys]
            
        except Exception as e:
            logger.error(f"Error getting client API keys: {e}")
            return []
    
    async def log_api_key_usage(
        self,
        session: AsyncSession,
        api_key_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log API key usage for monitoring and billing
        """
        
        try:
            usage_log = APIKeyUsageLog(
                api_key_id=api_key_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                request_size_bytes=request_size_bytes,
                response_size_bytes=response_size_bytes,
                metadata=metadata or {}
            )
            
            session.add(usage_log)
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error logging API key usage: {e}")
    
    # Private helper methods
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        
        # Generate random bytes and encode as base64-like string
        random_bytes = secrets.token_bytes(48)  # 48 bytes = 64 chars when base64 encoded
        
        # Create API key with prefix
        key = secrets.token_urlsafe(48)
        
        return f"sk-{key}"
    
    def _hash_api_key(self, raw_key: str) -> str:
        """Hash API key for storage"""
        
        # Use SHA-256 for hashing
        return hashlib.sha256(raw_key.encode()).hexdigest()
    
    async def _check_rate_limits(self, api_key: APIKey) -> Dict[str, Any]:
        """Check API key rate limits"""
        
        redis_client = await get_redis_client()
        if not redis_client:
            # If Redis not available, allow request
            return {"allowed": True}
        
        try:
            now = datetime.now(timezone.utc)
            hour_key = f"api_rate_limit:hour:{api_key.id}:{now.strftime('%Y%m%d%H')}"
            day_key = f"api_rate_limit:day:{api_key.id}:{now.strftime('%Y%m%d')}"
            
            # Check hourly limit
            if api_key.rate_limit_per_hour:
                hour_count = await redis_client.get(hour_key) or 0
                if int(hour_count) >= api_key.rate_limit_per_hour:
                    return {
                        "allowed": False,
                        "limit_type": "hourly",
                        "limit": api_key.rate_limit_per_hour,
                        "current": int(hour_count)
                    }
            
            # Check daily limit
            if api_key.rate_limit_per_day:
                day_count = await redis_client.get(day_key) or 0
                if int(day_count) >= api_key.rate_limit_per_day:
                    return {
                        "allowed": False,
                        "limit_type": "daily",
                        "limit": api_key.rate_limit_per_day,
                        "current": int(day_count)
                    }
            
            # Increment counters
            pipe = redis_client.pipeline()
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)  # 1 hour
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)  # 1 day
            await pipe.execute()
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            return {"allowed": True}  # Allow on error
    
    async def _log_key_event(
        self,
        session: AsyncSession,
        key_id: str,
        client_id: str,
        event_type: AuditEventType,
        description: str,
        user_id: Optional[str] = None
    ):
        """Log API key related events"""
        
        try:
            audit_log = ClientAuditLog(
                client_id=client_id,
                event_type=event_type,
                event_name="API Key Management",
                event_description=description,
                event_outcome="success",
                user_id=user_id,
                resource_type="api_key",
                resource_id=key_id,
                metadata={"api_key_id": key_id}
            )
            
            session.add(audit_log)
            await session.flush()
            
        except Exception as e:
            logger.error(f"Error logging key event: {e}")
    
    async def _log_security_event(
        self,
        session: AsyncSession,
        key_id: str,
        client_id: str,
        description: str,
        severity: AuditSeverity = AuditSeverity.MEDIUM
    ):
        """Log security-related events"""
        
        try:
            audit_log = ClientAuditLog(
                client_id=client_id,
                event_type=AuditEventType.SECURITY_ALERT,
                event_name="API Key Security Event",
                event_description=description,
                event_outcome="failure",
                severity=severity,
                security_alert=True,
                resource_type="api_key",
                resource_id=key_id,
                metadata={"api_key_id": key_id}
            )
            
            session.add(audit_log)
            await session.flush()
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")