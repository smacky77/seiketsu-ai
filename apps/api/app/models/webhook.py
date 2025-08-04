"""
Webhook model for external integrations
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from enum import Enum
from datetime import datetime
from typing import Dict, Any

from .base import BaseModel, TenantMixin, AuditMixin


class WebhookEvent(str, Enum):
    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_ENDED = "conversation.ended"
    LEAD_CREATED = "lead.created"
    LEAD_UPDATED = "lead.updated"
    APPOINTMENT_SCHEDULED = "appointment.scheduled"
    CALL_TRANSFERRED = "call.transferred"
    ALL = "*"


class WebhookStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    DISABLED = "disabled"


class Webhook(BaseModel, TenantMixin, AuditMixin):
    """Webhook configuration for external integrations"""
    __tablename__ = "webhooks"
    
    # Basic configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    url = Column(String(500), nullable=False)
    
    # Event configuration
    events = Column(JSON, default=list)  # List of WebhookEvent values
    
    # Security
    secret = Column(String(255))  # HMAC secret for signature verification
    headers = Column(JSON, default=dict)  # Additional headers to send
    
    # Status and monitoring
    status = Column(SQLEnum(WebhookStatus), default=WebhookStatus.ACTIVE)
    is_verified = Column(Boolean, default=False)
    last_ping = Column(DateTime)
    
    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=30)
    
    # Statistics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime)
    last_success_at = Column(DateTime)
    last_failure_at = Column(DateTime)
    
    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="webhooks")
    
    def __repr__(self):
        return f"<Webhook(id={self.id}, name={self.name}, url={self.url})>"
    
    @property
    def success_rate(self) -> float:
        if self.total_deliveries == 0:
            return 0.0
        return self.successful_deliveries / self.total_deliveries
    
    @property
    def is_healthy(self) -> bool:
        return (
            self.status == WebhookStatus.ACTIVE and
            self.success_rate >= 0.95 and
            (not self.last_failure_at or 
             (self.last_success_at and self.last_success_at > self.last_failure_at))
        )
    
    def supports_event(self, event: WebhookEvent) -> bool:
        """Check if webhook supports a specific event"""
        return WebhookEvent.ALL.value in self.events or event.value in self.events
    
    def record_delivery(self, success: bool):
        """Record webhook delivery attempt"""
        self.total_deliveries += 1
        self.last_delivery_at = datetime.utcnow()
        
        if success:
            self.successful_deliveries += 1
            self.last_success_at = datetime.utcnow()
            if self.status == WebhookStatus.FAILED:
                self.status = WebhookStatus.ACTIVE
        else:
            self.failed_deliveries += 1
            self.last_failure_at = datetime.utcnow()
            
            # Mark as failed if too many consecutive failures
            if self.failed_deliveries - self.successful_deliveries >= 10:
                self.status = WebhookStatus.FAILED


class Integration(BaseModel, TenantMixin, AuditMixin):
    """External service integration configuration"""
    __tablename__ = "integrations"
    
    # Integration details
    name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)  # "salesforce", "hubspot", "zapier"
    description = Column(Text)
    
    # Configuration
    config = Column(JSON, default=dict)  # Provider-specific configuration
    credentials = Column(JSON, default=dict)  # Encrypted credentials
    
    # Status
    is_enabled = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_sync = Column(DateTime)
    last_error = Column(Text)
    
    # Rate limiting
    rate_limit_per_hour = Column(Integer, default=1000)
    requests_this_hour = Column(Integer, default=0)
    rate_limit_reset = Column(DateTime)
    
    # Organization relationship  
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="integrations")
    
    def __repr__(self):
        return f"<Integration(id={self.id}, provider={self.provider}, name={self.name})>"
    
    @property
    def is_rate_limited(self) -> bool:
        if not self.rate_limit_reset or datetime.utcnow() > self.rate_limit_reset:
            return False
        return self.requests_this_hour >= self.rate_limit_per_hour
    
    def record_request(self):
        """Record API request for rate limiting"""
        now = datetime.utcnow()
        
        # Reset counter if hour has passed
        if not self.rate_limit_reset or now > self.rate_limit_reset:
            self.requests_this_hour = 0
            self.rate_limit_reset = now.replace(minute=0, second=0, microsecond=0)
            # Add one hour
            self.rate_limit_reset = self.rate_limit_reset.replace(hour=self.rate_limit_reset.hour + 1)
        
        self.requests_this_hour += 1


class AnalyticsEvent(BaseModel, TenantMixin):
    """Analytics and tracking events"""
    __tablename__ = "analytics_events"
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_name = Column(String(255), nullable=False)
    
    # Context
    session_id = Column(String(255), index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), index=True)
    voice_agent_id = Column(String, ForeignKey("voice_agents.id"), index=True)
    
    # Event data
    properties = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Technical details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    referrer = Column(String(500))
    
    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="analytics_events")
    
    def __repr__(self):
        return f"<AnalyticsEvent(event_type={self.event_type}, event_name={self.event_name})>"


class Subscription(BaseModel, TenantMixin, AuditMixin):
    """Subscription and billing information"""
    __tablename__ = "subscriptions"
    
    # Subscription details
    stripe_subscription_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_price_id = Column(String(255), nullable=False)
    
    # Status
    status = Column(String(50), nullable=False, index=True)  # Stripe status
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    
    # Billing
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), default="usd")
    interval = Column(String(20), nullable=False)  # "month", "year"
    
    # Trial
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    
    # Cancellation
    canceled_at = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    cancellation_reason = Column(Text)
    
    # Usage tracking
    usage_this_period = Column(JSON, default=dict)
    overage_charges = Column(Integer, default=0)  # In cents
    
    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, stripe_id={self.stripe_subscription_id}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        return self.status in ["active", "trialing"]
    
    @property
    def is_trial(self) -> bool:
        return self.status == "trialing"
    
    @property
    def amount_dollars(self) -> float:
        return self.amount / 100.0