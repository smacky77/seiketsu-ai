"""
Third-party account management models
Handles integration accounts for voice services, MLS, CRM, etc.
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
from cryptography.fernet import Fernet
import uuid
import base64
import os

from .base import BaseModel


class ThirdPartyProvider(str, enum.Enum):
    """Supported third-party service providers"""
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AWS = "aws"
    GOOGLE_CLOUD = "google_cloud"
    AZURE = "azure"
    MLS = "mls"
    ZILLOW = "zillow"
    REALTOR_COM = "realtor_com"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZAPIER = "zapier"
    SLACK = "slack"
    MICROSOFT_TEAMS = "microsoft_teams"
    TWILIO = "twilio"
    SENDGRID = "sendgrid"
    STRIPE = "stripe"
    QUICKBOOKS = "quickbooks"
    CUSTOM = "custom"


class AccountStatus(str, enum.Enum):
    """Third-party account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    ERROR = "error"


class CredentialType(str, enum.Enum):
    """Types of credentials stored"""
    API_KEY = "api_key"
    OAUTH2_TOKEN = "oauth2_token"
    JWT_TOKEN = "jwt_token"
    BASIC_AUTH = "basic_auth"
    CERTIFICATE = "certificate"
    CONNECTION_STRING = "connection_string"
    CUSTOM = "custom"


class ClientThirdPartyAccount(BaseModel):
    """
    Manages third-party service accounts for clients
    Stores encrypted credentials and configuration
    """
    __tablename__ = "client_third_party_accounts"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # Provider information
    provider = Column(Enum(ThirdPartyProvider), nullable=False)
    provider_account_id = Column(String(255), nullable=True)  # External account ID
    provider_account_name = Column(String(255), nullable=True)
    
    # Account details
    name = Column(String(255), nullable=False)  # Internal name for this integration
    description = Column(Text, nullable=True)
    status = Column(Enum(AccountStatus), nullable=False, default=AccountStatus.PENDING_VERIFICATION)
    
    # Credentials (encrypted)
    credential_type = Column(Enum(CredentialType), nullable=False)
    encrypted_credentials = Column(Text, nullable=False)
    credential_metadata = Column(JSONB, nullable=False, default=dict)
    
    # Configuration and settings
    configuration = Column(JSONB, nullable=False, default=dict)
    rate_limits = Column(JSONB, nullable=True)
    usage_quotas = Column(JSONB, nullable=True)
    
    # Status tracking
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    last_error_message = Column(Text, nullable=True)
    
    # Expiration and rotation
    expires_at = Column(DateTime(timezone=True), nullable=True)
    rotation_required = Column(Boolean, nullable=False, default=False)
    auto_rotate = Column(Boolean, nullable=False, default=False)
    
    # Webhooks and callbacks
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    callback_configuration = Column(JSONB, nullable=True)
    
    # Usage tracking
    total_requests = Column(Integer, nullable=False, default=0)
    successful_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)
    last_request_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="third_party_accounts")
    usage_logs = relationship(
        "ThirdPartyUsageLog",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_third_party_client_provider', 'client_id', 'provider'),
        Index('idx_third_party_status', 'status'),
        Index('idx_third_party_provider', 'provider'),
        Index('idx_third_party_expires_at', 'expires_at'),
        UniqueConstraint('client_id', 'provider', 'name', name='uq_client_provider_name'),
    )
    
    def __init__(self, **kwargs):
        # Set up encryption if credentials provided
        if 'credentials' in kwargs and 'encrypted_credentials' not in kwargs:
            kwargs['encrypted_credentials'] = self._encrypt_credentials(kwargs.pop('credentials'))
        
        super().__init__(**kwargs)
    
    @validates('provider_account_id')
    def validate_provider_account_id(self, key, provider_account_id):
        """Validate provider account ID format"""
        if provider_account_id and len(provider_account_id) > 255:
            raise ValueError("Provider account ID too long")
        return provider_account_id
    
    @hybrid_property
    def is_active(self) -> bool:
        """Check if account is active and valid"""
        if self.status != AccountStatus.ACTIVE:
            return False
        
        # Check expiration
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return False
            
        return True
    
    @hybrid_property
    def is_expired(self) -> bool:
        """Check if account is expired"""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.now(timezone.utc)
    
    @hybrid_property
    def needs_rotation(self) -> bool:
        """Check if credentials need rotation"""
        if self.rotation_required:
            return True
            
        # Check if nearing expiration and auto-rotate is enabled
        if self.auto_rotate and self.expires_at:
            days_until_expiry = (self.expires_at - datetime.now(timezone.utc)).days
            return days_until_expiry <= 7  # Rotate 7 days before expiry
            
        return False
    
    @hybrid_property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_credentials(self) -> Dict[str, Any]:
        """Decrypt and return credentials"""
        if not self.encrypted_credentials:
            return {}
            
        return self._decrypt_credentials(self.encrypted_credentials)
    
    def set_credentials(self, credentials: Dict[str, Any]) -> None:
        """Encrypt and store credentials"""
        self.encrypted_credentials = self._encrypt_credentials(credentials)
        self.last_verified_at = None  # Force re-verification
    
    def get_configuration(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback"""
        return self.configuration.get(key, default)
    
    def set_configuration(self, key: str, value: Any) -> None:
        """Set configuration value"""
        if self.configuration is None:
            self.configuration = {}
        self.configuration[key] = value
    
    def verify_connection(self) -> bool:
        """Verify connection to third-party service"""
        # This would be implemented by service-specific verification logic
        # For now, return basic validation
        try:
            credentials = self.get_credentials()
            if not credentials:
                return False
                
            # Basic validation based on credential type
            if self.credential_type == CredentialType.API_KEY:
                return bool(credentials.get('api_key'))
            elif self.credential_type == CredentialType.OAUTH2_TOKEN:
                return bool(credentials.get('access_token'))
            elif self.credential_type == CredentialType.BASIC_AUTH:
                return bool(credentials.get('username') and credentials.get('password'))
                
            return True
            
        except Exception as e:
            self.last_error_at = datetime.now(timezone.utc)
            self.last_error_message = str(e)
            return False
    
    def record_usage(self, success: bool, metadata: Optional[Dict] = None) -> None:
        """Record API usage"""
        self.total_requests += 1
        self.last_request_at = datetime.now(timezone.utc)
        self.last_used_at = datetime.now(timezone.utc)
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def is_within_rate_limits(self) -> bool:
        """Check if account is within rate limits"""
        if not self.rate_limits:
            return True
            
        # Implementation would depend on specific rate limit logic
        # This is a placeholder for the actual rate limiting logic
        return True
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get provider-specific configuration"""
        provider_configs = {
            ThirdPartyProvider.ELEVENLABS: {
                "base_url": "https://api.elevenlabs.io/v1",
                "timeout": 30,
                "max_retries": 3,
                "required_credentials": ["api_key"]
            },
            ThirdPartyProvider.OPENAI: {
                "base_url": "https://api.openai.com/v1",
                "timeout": 60,
                "max_retries": 3,
                "required_credentials": ["api_key"]
            },
            ThirdPartyProvider.AWS: {
                "timeout": 30,
                "max_retries": 3,
                "required_credentials": ["access_key_id", "secret_access_key"]
            },
            ThirdPartyProvider.SALESFORCE: {
                "timeout": 30,
                "max_retries": 3,
                "required_credentials": ["access_token", "instance_url"]
            }
        }
        
        return provider_configs.get(self.provider, {})
    
    def _get_encryption_key(self) -> bytes:
        """Get encryption key for credentials"""
        # In production, this should come from a secure key management service
        key_env = os.getenv('ENCRYPTION_KEY')
        if not key_env:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
            
        # Ensure key is properly formatted for Fernet
        key_bytes = key_env.encode() if isinstance(key_env, str) else key_env
        if len(key_bytes) != 44:  # Fernet key should be 44 bytes when base64 encoded
            # Generate a proper key from the provided key
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            
            salt = b"seiketsu_ai_salt"  # In production, use a random salt per client
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
        else:
            key = key_bytes
            
        return key
    
    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials for storage"""
        if not credentials:
            return ""
            
        import json
        key = self._get_encryption_key()
        f = Fernet(key)
        
        credentials_json = json.dumps(credentials, sort_keys=True)
        encrypted = f.encrypt(credentials_json.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def _decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt credentials from storage"""
        if not encrypted_credentials:
            return {}
            
        import json
        key = self._get_encryption_key()
        f = Fernet(key)
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_credentials.encode())
            decrypted = f.decrypt(encrypted_bytes)
            return json.loads(decrypted.decode())
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {e}")
    
    def to_dict(self, include_credentials: bool = False) -> Dict[str, Any]:
        """Convert account to dictionary"""
        data = {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "provider": self.provider.value,
            "provider_account_id": self.provider_account_id,
            "provider_account_name": self.provider_account_name,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "credential_type": self.credential_type.value,
            "configuration": self.configuration,
            "rate_limits": self.rate_limits,
            "usage_quotas": self.usage_quotas,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "needs_rotation": self.needs_rotation,
            "success_rate": self.success_rate,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
            "last_error_message": self.last_error_message,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_credentials:
            try:
                data["credentials"] = self.get_credentials()
            except Exception:
                data["credentials"] = None
                
        return data
    
    def __repr__(self):
        return f"<ClientThirdPartyAccount(id='{self.id}', provider='{self.provider}', name='{self.name}')>"


class ThirdPartyUsageLog(BaseModel):
    """
    Logs third-party service usage for monitoring and billing
    """
    __tablename__ = "third_party_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("client_third_party_accounts.id"), nullable=False)
    
    # Request details
    operation = Column(String(255), nullable=False)
    method = Column(String(10), nullable=True)  # HTTP method
    endpoint = Column(String(500), nullable=True)
    
    # Response details
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False)
    
    # Usage metrics
    tokens_used = Column(Integer, nullable=True)  # For AI services
    data_transferred_bytes = Column(Integer, nullable=True)
    cost_estimate = Column(String(20), nullable=True)  # Decimal as string
    
    # Timing
    request_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    # Additional context
    metadata = Column(JSONB, nullable=False, default=dict)
    error_details = Column(Text, nullable=True)
    
    # Relationships
    account = relationship("ClientThirdPartyAccount", back_populates="usage_logs")
    
    # Indexes for performance and analytics
    __table_args__ = (
        Index('idx_usage_log_account_timestamp', 'account_id', 'request_timestamp'),
        Index('idx_usage_log_operation', 'operation'),
        Index('idx_usage_log_success', 'success'),
        Index('idx_usage_log_timestamp', 'request_timestamp'),
    )
    
    def __repr__(self):
        return f"<ThirdPartyUsageLog(account_id='{self.account_id}', operation='{self.operation}', success='{self.success}')>"


class ThirdPartyWebhook(BaseModel):
    """
    Manages webhooks from third-party services
    """
    __tablename__ = "third_party_webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # Webhook details
    provider = Column(Enum(ThirdPartyProvider), nullable=False)
    webhook_id = Column(String(255), nullable=True)  # External webhook ID
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=True)
    
    # Configuration
    events = Column(JSONB, nullable=False, default=list)  # List of subscribed events
    active = Column(Boolean, nullable=False, default=True)
    
    # Status tracking
    last_delivery_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    consecutive_failures = Column(Integer, nullable=False, default=0)
    
    # Statistics
    total_deliveries = Column(Integer, nullable=False, default=0)
    successful_deliveries = Column(Integer, nullable=False, default=0)
    failed_deliveries = Column(Integer, nullable=False, default=0)
    
    # Indexes
    __table_args__ = (
        Index('idx_webhook_client_provider', 'client_id', 'provider'),
        Index('idx_webhook_active', 'active'),
    )
    
    def __repr__(self):
        return f"<ThirdPartyWebhook(id='{self.id}', provider='{self.provider}', active='{self.active}')>"