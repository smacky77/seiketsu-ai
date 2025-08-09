"""
Client model for multi-tenant architecture
Handles client/tenant management and provisioning status
"""
import enum
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Boolean, Column, String, DateTime, Text, Integer,
    JSON, Enum, ForeignKey, Index, CheckConstraint,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

from .base import BaseModel


class ClientStatus(str, enum.Enum):
    """Client lifecycle status"""
    PENDING = "pending"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ERROR = "error"


class ProvisioningStep(str, enum.Enum):
    """Client provisioning pipeline steps"""
    VALIDATION = "validation"
    AWS_ACCOUNT_CREATION = "aws_account_creation"
    INFRASTRUCTURE_SETUP = "infrastructure_setup"
    DATABASE_PROVISIONING = "database_provisioning"
    SCHEMA_CREATION = "schema_creation"
    APPLICATION_DEPLOYMENT = "application_deployment"
    THIRD_PARTY_INTEGRATION = "third_party_integration"
    HEALTH_CHECK = "health_check"
    ACTIVATION = "activation"
    COMPLETED = "completed"


class ProvisioningStatus(str, enum.Enum):
    """Status of individual provisioning steps"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ClientTier(str, enum.Enum):
    """Client service tiers"""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class Client(BaseModel):
    """
    Client model for multi-tenant architecture
    Represents a client/tenant in the system with complete isolation
    """
    __tablename__ = "clients"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    
    # Contact information
    primary_contact_email = Column(String(255), nullable=False)
    primary_contact_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Business information
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)
    tax_id = Column(String(50), nullable=True)
    
    # Status and lifecycle
    status = Column(Enum(ClientStatus), nullable=False, default=ClientStatus.PENDING)
    tier = Column(Enum(ClientTier), nullable=False, default=ClientTier.STARTER)
    
    # AWS and infrastructure details
    aws_account_id = Column(String(12), unique=True, nullable=True)
    aws_region = Column(String(20), nullable=False, default="us-east-1")
    database_schema = Column(String(63), unique=True, nullable=False)
    vpc_id = Column(String(50), nullable=True)
    
    # Provisioning tracking
    provisioned_at = Column(DateTime(timezone=True), nullable=True)
    provisioning_started_at = Column(DateTime(timezone=True), nullable=True)
    last_provisioning_step = Column(
        Enum(ProvisioningStep), 
        nullable=True,
        default=ProvisioningStep.VALIDATION
    )
    
    # Configuration and features
    configuration = Column(JSONB, nullable=False, default=dict)
    features = Column(JSONB, nullable=False, default=dict)
    limits = Column(JSONB, nullable=False, default=dict)
    
    # Billing and subscription
    billing_email = Column(String(255), nullable=True)
    billing_address = Column(JSONB, nullable=True)
    subscription_id = Column(String(100), nullable=True)
    billing_customer_id = Column(String(100), nullable=True)
    
    # Security settings
    allowed_ips = Column(JSONB, nullable=True)  # IP whitelist
    security_settings = Column(JSONB, nullable=False, default=dict)
    compliance_requirements = Column(JSONB, nullable=False, default=list)
    
    # Operational metadata
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(20), nullable=False, default="unknown")
    health_check_url = Column(String(500), nullable=True)
    
    # Relationships
    provisioning_logs = relationship(
        "ClientProvisioningLog",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    third_party_accounts = relationship(
        "ClientThirdPartyAccount",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    usage_records = relationship(
        "ClientUsageRecord",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    audit_logs = relationship(
        "ClientAuditLog",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_client_status', 'status'),
        Index('idx_client_tier', 'tier'),
        Index('idx_client_aws_account', 'aws_account_id'),
        Index('idx_client_slug', 'slug'),
        Index('idx_client_provisioned_at', 'provisioned_at'),
        CheckConstraint('char_length(slug) >= 3', name='check_slug_min_length'),
        CheckConstraint('char_length(slug) <= 50', name='check_slug_max_length'),
        CheckConstraint("slug ~ '^[a-z0-9-]+$'", name='check_slug_format'),
        UniqueConstraint('database_schema', name='uq_database_schema'),
    )
    
    def __init__(self, **kwargs):
        # Auto-generate database schema name if not provided
        if 'database_schema' not in kwargs and 'slug' in kwargs:
            kwargs['database_schema'] = f"client_{kwargs['slug']}"
            
        # Set default limits based on tier
        if 'limits' not in kwargs and 'tier' in kwargs:
            kwargs['limits'] = self._get_default_limits(kwargs['tier'])
            
        # Set default features based on tier
        if 'features' not in kwargs and 'tier' in kwargs:
            kwargs['features'] = self._get_default_features(kwargs['tier'])
            
        super().__init__(**kwargs)
    
    @validates('slug')
    def validate_slug(self, key, slug):
        """Validate client slug format"""
        if not slug:
            raise ValueError("Client slug cannot be empty")
            
        if len(slug) < 3 or len(slug) > 50:
            raise ValueError("Client slug must be between 3 and 50 characters")
            
        # Only lowercase letters, numbers, and hyphens
        if not slug.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Client slug can only contain letters, numbers, and hyphens")
            
        return slug.lower()
    
    @validates('aws_account_id')
    def validate_aws_account_id(self, key, aws_account_id):
        """Validate AWS account ID format"""
        if aws_account_id and (len(aws_account_id) != 12 or not aws_account_id.isdigit()):
            raise ValueError("AWS account ID must be exactly 12 digits")
        return aws_account_id
    
    @hybrid_property
    def is_active(self) -> bool:
        """Check if client is active"""
        return self.status == ClientStatus.ACTIVE
    
    @hybrid_property
    def is_provisioned(self) -> bool:
        """Check if client is fully provisioned"""
        return (
            self.status == ClientStatus.ACTIVE and
            self.provisioned_at is not None and
            self.last_provisioning_step == ProvisioningStep.COMPLETED
        )
    
    @hybrid_property
    def provisioning_progress(self) -> float:
        """Calculate provisioning progress percentage"""
        if not self.last_provisioning_step:
            return 0.0
            
        steps = list(ProvisioningStep)
        current_index = steps.index(self.last_provisioning_step)
        return (current_index + 1) / len(steps) * 100
    
    def get_configuration(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback"""
        return self.configuration.get(key, default)
    
    def set_configuration(self, key: str, value: Any) -> None:
        """Set configuration value"""
        if self.configuration is None:
            self.configuration = {}
        self.configuration[key] = value
    
    def has_feature(self, feature: str) -> bool:
        """Check if client has specific feature enabled"""
        if not self.features:
            return False
        return self.features.get(feature, False)
    
    def get_limit(self, limit_name: str) -> Optional[int]:
        """Get specific limit value"""
        if not self.limits:
            return None
        return self.limits.get(limit_name)
    
    def is_within_limit(self, limit_name: str, current_value: int) -> bool:
        """Check if current value is within specified limit"""
        limit = self.get_limit(limit_name)
        if limit is None:
            return True  # No limit set
        return current_value <= limit
    
    def get_database_url(self, base_url: str) -> str:
        """Get tenant-specific database URL"""
        if not base_url or not self.database_schema:
            raise ValueError("Base URL and database schema required")
            
        # Replace database name in URL with tenant schema
        if self.aws_account_id:
            # Use dedicated database for enterprise clients
            return base_url.replace("/seiketsu_ai", f"/{self.database_schema}")
        else:
            # Use schema-based isolation for other clients
            return f"{base_url}?options=-csearch_path%3D{self.database_schema}"
    
    def can_access_ip(self, ip_address: str) -> bool:
        """Check if IP address is allowed for this client"""
        if not self.allowed_ips:
            return True  # No IP restrictions
            
        from ipaddress import ip_address, ip_network
        
        client_ip = ip_address(ip_address)
        for allowed in self.allowed_ips:
            try:
                if client_ip in ip_network(allowed, strict=False):
                    return True
            except Exception:
                # Invalid IP format, skip
                continue
                
        return False
    
    @staticmethod
    def _get_default_limits(tier: ClientTier) -> Dict[str, int]:
        """Get default limits based on client tier"""
        limits_by_tier = {
            ClientTier.STARTER: {
                "max_users": 5,
                "max_voice_agents": 2,
                "max_conversations_per_month": 1000,
                "max_properties": 100,
                "max_leads": 500,
                "max_api_calls_per_hour": 100,
                "max_storage_gb": 5,
                "max_concurrent_calls": 2
            },
            ClientTier.PROFESSIONAL: {
                "max_users": 25,
                "max_voice_agents": 10,
                "max_conversations_per_month": 10000,
                "max_properties": 1000,
                "max_leads": 5000,
                "max_api_calls_per_hour": 1000,
                "max_storage_gb": 50,
                "max_concurrent_calls": 10
            },
            ClientTier.ENTERPRISE: {
                "max_users": 100,
                "max_voice_agents": 50,
                "max_conversations_per_month": 100000,
                "max_properties": 10000,
                "max_leads": 50000,
                "max_api_calls_per_hour": 10000,
                "max_storage_gb": 500,
                "max_concurrent_calls": 50
            },
            ClientTier.CUSTOM: {
                # Custom limits set per client
            }
        }
        return limits_by_tier.get(tier, {})
    
    @staticmethod
    def _get_default_features(tier: ClientTier) -> Dict[str, bool]:
        """Get default features based on client tier"""
        features_by_tier = {
            ClientTier.STARTER: {
                "voice_synthesis": True,
                "basic_analytics": True,
                "lead_management": True,
                "property_search": True,
                "webhook_integration": False,
                "advanced_analytics": False,
                "custom_voice_models": False,
                "sso_integration": False,
                "advanced_reporting": False,
                "api_access": True,
                "white_labeling": False
            },
            ClientTier.PROFESSIONAL: {
                "voice_synthesis": True,
                "basic_analytics": True,
                "lead_management": True,
                "property_search": True,
                "webhook_integration": True,
                "advanced_analytics": True,
                "custom_voice_models": False,
                "sso_integration": True,
                "advanced_reporting": True,
                "api_access": True,
                "white_labeling": False
            },
            ClientTier.ENTERPRISE: {
                "voice_synthesis": True,
                "basic_analytics": True,
                "lead_management": True,
                "property_search": True,
                "webhook_integration": True,
                "advanced_analytics": True,
                "custom_voice_models": True,
                "sso_integration": True,
                "advanced_reporting": True,
                "api_access": True,
                "white_labeling": True
            },
            ClientTier.CUSTOM: {
                # Custom features set per client
            }
        }
        return features_by_tier.get(tier, {})
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert client to dictionary"""
        data = {
            "id": str(self.id),
            "slug": self.slug,
            "name": self.name,
            "display_name": self.display_name,
            "status": self.status.value,
            "tier": self.tier.value,
            "primary_contact_email": self.primary_contact_email,
            "phone": self.phone,
            "website": self.website,
            "industry": self.industry,
            "company_size": self.company_size,
            "aws_region": self.aws_region,
            "features": self.features,
            "limits": self.limits,
            "is_active": self.is_active,
            "is_provisioned": self.is_provisioned,
            "provisioning_progress": self.provisioning_progress,
            "health_status": self.health_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "provisioned_at": self.provisioned_at.isoformat() if self.provisioned_at else None,
        }
        
        if include_sensitive:
            data.update({
                "aws_account_id": self.aws_account_id,
                "database_schema": self.database_schema,
                "vpc_id": self.vpc_id,
                "configuration": self.configuration,
                "security_settings": self.security_settings,
                "allowed_ips": self.allowed_ips,
                "compliance_requirements": self.compliance_requirements,
                "billing_email": self.billing_email,
                "billing_address": self.billing_address,
                "subscription_id": self.subscription_id,
                "billing_customer_id": self.billing_customer_id,
            })
            
        return data
    
    def __repr__(self):
        return f"<Client(id='{self.id}', slug='{self.slug}', name='{self.name}', status='{self.status}')>"


class ClientProvisioningLog(BaseModel):
    """
    Tracks the client provisioning process step by step
    """
    __tablename__ = "client_provisioning_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # Provisioning step details
    step = Column(Enum(ProvisioningStep), nullable=False)
    status = Column(Enum(ProvisioningStatus), nullable=False)
    
    # Timing information
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Error handling
    error_details = Column(JSONB, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    
    # Metadata and context
    metadata = Column(JSONB, nullable=False, default=dict)
    performer_user_id = Column(UUID(as_uuid=True), nullable=True)  # Who triggered this step
    
    # Relationships
    client = relationship("Client", back_populates="provisioning_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_provisioning_client_step', 'client_id', 'step'),
        Index('idx_provisioning_status', 'status'),
        Index('idx_provisioning_started_at', 'started_at'),
    )
    
    @hybrid_property
    def is_completed(self) -> bool:
        """Check if step is completed"""
        return self.status == ProvisioningStatus.COMPLETED
    
    @hybrid_property
    def is_failed(self) -> bool:
        """Check if step failed"""
        return self.status == ProvisioningStatus.FAILED
    
    @hybrid_property
    def can_retry(self) -> bool:
        """Check if step can be retried"""
        return (
            self.status == ProvisioningStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def complete_step(self, metadata: Optional[Dict] = None) -> None:
        """Mark step as completed"""
        self.status = ProvisioningStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())
        
        if metadata:
            self.metadata.update(metadata)
    
    def fail_step(self, error: str, metadata: Optional[Dict] = None) -> None:
        """Mark step as failed with error details"""
        self.status = ProvisioningStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())
        
        self.error_details = {
            "error": error,
            "timestamp": self.completed_at.isoformat(),
            "retry_count": self.retry_count
        }
        
        if metadata:
            self.metadata.update(metadata)
    
    def __repr__(self):
        return f"<ClientProvisioningLog(client_id='{self.client_id}', step='{self.step}', status='{self.status}')>"