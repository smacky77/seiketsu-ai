"""
User model for authentication and authorization
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from enum import Enum
from datetime import datetime
from typing import Optional, List

from .base import BaseModel, TenantMixin, AuditMixin


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(BaseModel, TenantMixin, AuditMixin):
    """User model with role-based access control"""
    __tablename__ = "users"
    
    # Basic information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255))
    email_verified_at = Column(DateTime)
    
    # Password reset
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    last_password_change = Column(DateTime, default=datetime.utcnow)
    
    # Role and permissions
    role = Column(SQLEnum(UserRole), default=UserRole.AGENT, nullable=False)
    permissions = Column(JSON, default=list)  # Additional specific permissions
    
    # Status and activity
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_VERIFICATION)
    last_login_at = Column(DateTime)
    last_activity_at = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Profile information
    phone = Column(String(50))
    avatar_url = Column(String(500))
    bio = Column(String(500))
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Preferences
    preferences = Column(JSON, default=dict)
    notification_settings = Column(JSON, default=dict)
    
    # Two-factor authentication
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(255))
    backup_codes = Column(JSON, default=list)
    
    # API access
    api_key = Column(String(255), unique=True, index=True)
    api_key_expires = Column(DateTime)
    
    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="users")
    
    # Activity relationships
    created_conversations = relationship(
        "Conversation", 
        foreign_keys="Conversation.created_by_user_id",
        back_populates="created_by_user"
    )
    assigned_conversations = relationship(
        "Conversation",
        foreign_keys="Conversation.assigned_to_user_id", 
        back_populates="assigned_to_user"
    )
    created_leads = relationship("Lead", back_populates="created_by_user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]
    
    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN
    
    @property
    def can_manage_organization(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]
    
    @property
    def can_manage_users(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER]
    
    @property
    def can_create_voice_agents(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER]
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if self.is_super_admin:
            return True
        
        permissions = self.permissions or []
        return permission in permissions
    
    def add_permission(self, permission: str):
        """Add permission to user"""
        permissions = self.permissions or []
        if permission not in permissions:
            permissions.append(permission)
            self.permissions = permissions
    
    def remove_permission(self, permission: str):
        """Remove permission from user"""
        permissions = self.permissions or []
        if permission in permissions:
            permissions.remove(permission)
            self.permissions = permissions
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
    
    def update_login_stats(self):
        """Update login statistics"""
        self.last_login_at = datetime.utcnow()
        self.login_count = (self.login_count or 0) + 1
        self.update_last_activity()
    
    def is_password_expired(self, max_age_days: int = 90) -> bool:
        """Check if password is expired"""
        if not self.last_password_change:
            return True
        
        from datetime import timedelta
        expiry_date = self.last_password_change + timedelta(days=max_age_days)
        return datetime.utcnow() > expiry_date