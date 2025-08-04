"""
Organization model for multi-tenant architecture
"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from enum import Enum
from typing import Optional, Dict, Any

from .base import BaseModel, AuditMixin


class PlanType(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class Organization(BaseModel, AuditMixin):
    """Organization model for multi-tenant support"""
    __tablename__ = "organizations"
    
    # Basic information
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, index=True)
    description = Column(Text)
    
    # Contact information
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="US")
    
    # Business information
    industry = Column(String(100))
    company_size = Column(String(50))
    timezone = Column(String(50), default="UTC")
    
    # Subscription and billing
    plan_type = Column(SQLEnum(PlanType), default=PlanType.STARTER)
    billing_email = Column(String(255))
    stripe_customer_id = Column(String(255), unique=True, index=True)
    
    # Features and limits
    max_users = Column(Integer, default=5)
    max_voice_agents = Column(Integer, default=1)
    max_conversations_per_month = Column(Integer, default=1000)
    max_storage_gb = Column(Integer, default=10)
    
    # Configuration
    settings = Column(JSON, default=dict)
    branding = Column(JSON, default=dict)  # Logo, colors, etc.
    integrations_config = Column(JSON, default=dict)
    
    # Status
    is_verified = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    suspension_reason = Column(Text)
    
    # Trial information
    trial_ends_at = Column(DateTime)
    is_trial = Column(Boolean, default=True)
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    voice_agents = relationship("VoiceAgent", back_populates="organization", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="organization", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="organization", cascade="all, delete-orphan")
    properties = relationship("Property", back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="organization", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="organization", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="organization", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, slug={self.slug})>"
    
    @property
    def is_enterprise(self) -> bool:
        return self.plan_type in [PlanType.ENTERPRISE, PlanType.CUSTOM]
    
    @property
    def is_on_trial(self) -> bool:
        if not self.trial_ends_at:
            return False
        from datetime import datetime
        return datetime.utcnow() < self.trial_ends_at
    
    def get_feature_limit(self, feature: str) -> Optional[int]:
        """Get feature limit for organization"""
        limits = {
            "users": self.max_users,
            "voice_agents": self.max_voice_agents,
            "conversations": self.max_conversations_per_month,
            "storage": self.max_storage_gb
        }
        return limits.get(feature)
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update organization settings"""
        current_settings = self.settings or {}
        current_settings.update(new_settings)
        self.settings = current_settings