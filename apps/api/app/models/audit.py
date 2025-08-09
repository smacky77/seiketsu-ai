"""
Audit trail and compliance models
Comprehensive logging for security, compliance, and debugging
"""
import enum
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Boolean, Column, String, DateTime, Text, Integer,
    JSON, Enum, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

from .base import BaseModel


class AuditEventType(str, enum.Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    TOKEN_REFRESH = "token_refresh"
    ACCOUNT_LOCKED = "account_locked"
    
    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGE = "permission_change"
    ROLE_CHANGE = "role_change"
    
    # Data access events
    DATA_READ = "data_read"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    # Configuration events
    CONFIG_CHANGE = "config_change"
    FEATURE_TOGGLE = "feature_toggle"
    INTEGRATION_CHANGE = "integration_change"
    
    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    
    # Compliance events
    DATA_RETENTION = "data_retention"
    DATA_PURGE = "data_purge"
    COMPLIANCE_VIOLATION = "compliance_violation"
    AUDIT_LOG_ACCESS = "audit_log_access"
    
    # Security events
    SECURITY_ALERT = "security_alert"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IP_BLOCKED = "ip_blocked"
    
    # API events
    API_CALL = "api_call"
    API_ERROR = "api_error"
    WEBHOOK_SENT = "webhook_sent"
    WEBHOOK_FAILED = "webhook_failed"


class AuditSeverity(str, enum.Enum):
    """Severity levels for audit events"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceFramework(str, enum.Enum):
    """Supported compliance frameworks"""
    SOC2 = "soc2"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    CCPA = "ccpa"
    SOX = "sox"
    ISO_27001 = "iso_27001"
    NIST = "nist"


class ClientAuditLog(BaseModel):
    """
    Comprehensive audit logging for client activities
    Designed for security, compliance, and forensic analysis
    """
    __tablename__ = "client_audit_logs"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # Event classification
    event_type = Column(Enum(AuditEventType), nullable=False)
    event_category = Column(String(100), nullable=False)
    severity = Column(Enum(AuditSeverity), nullable=False, default=AuditSeverity.INFO)
    
    # Event details
    event_name = Column(String(255), nullable=False)
    event_description = Column(Text, nullable=True)
    event_outcome = Column(String(20), nullable=False)  # "success", "failure", "partial"
    
    # Actor information
    user_id = Column(UUID(as_uuid=True), nullable=True)
    username = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(100), nullable=True)
    service_account = Column(String(255), nullable=True)  # For system actions
    
    # Network and session context
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)
    
    # Resource information
    resource_type = Column(String(100), nullable=True)  # "user", "property", "conversation", etc.
    resource_id = Column(String(255), nullable=True)
    resource_name = Column(String(255), nullable=True)
    affected_resources = Column(JSONB, nullable=True)
    
    # API/Request details
    api_endpoint = Column(String(500), nullable=True)
    http_method = Column(String(10), nullable=True)
    http_status_code = Column(Integer, nullable=True)
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    
    # Data changes
    old_values = Column(JSONB, nullable=True)  # Before values for updates
    new_values = Column(JSONB, nullable=True)  # After values for updates
    field_changes = Column(JSONB, nullable=True)  # Specific field changes
    
    # Compliance and retention
    compliance_frameworks = Column(JSONB, nullable=False, default=list)
    retention_required_until = Column(DateTime(timezone=True), nullable=True)
    sensitive_data = Column(Boolean, nullable=False, default=False)
    
    # Error and security context
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    security_alert = Column(Boolean, nullable=False, default=False)
    risk_score = Column(Integer, nullable=True)  # 0-100 risk assessment
    
    # Event timing
    event_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    process_duration_ms = Column(Integer, nullable=True)
    
    # Additional context and metadata
    metadata = Column(JSONB, nullable=False, default=dict)
    tags = Column(JSONB, nullable=False, default=list)
    correlation_id = Column(String(255), nullable=True)  # For linking related events
    parent_event_id = Column(UUID(as_uuid=True), nullable=True)  # For event hierarchies
    
    # Data classification
    data_classification = Column(String(50), nullable=True)  # "public", "internal", "confidential", "restricted"
    geographic_location = Column(String(100), nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="audit_logs")
    
    # Indexes for performance and querying
    __table_args__ = (
        Index('idx_audit_client_timestamp', 'client_id', 'event_timestamp'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_severity', 'severity'),
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_ip_address', 'ip_address'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_security_alert', 'security_alert'),
        Index('idx_audit_compliance', 'compliance_frameworks'),
        Index('idx_audit_correlation', 'correlation_id'),
        Index('idx_audit_timestamp', 'event_timestamp'),
        Index('idx_audit_outcome', 'event_outcome'),
        Index('idx_audit_api_endpoint', 'api_endpoint'),
    )
    
    def __init__(self, **kwargs):
        # Auto-set event category based on event type
        if 'event_category' not in kwargs and 'event_type' in kwargs:
            kwargs['event_category'] = self._get_category_for_event_type(kwargs['event_type'])
        
        # Auto-set compliance frameworks based on client
        if 'compliance_frameworks' not in kwargs and 'client_id' in kwargs:
            # This would be set based on client requirements
            kwargs['compliance_frameworks'] = ['soc2']  # Default minimum
        
        super().__init__(**kwargs)
    
    @validates('risk_score')
    def validate_risk_score(self, key, risk_score):
        """Validate risk score is between 0-100"""
        if risk_score is not None and (risk_score < 0 or risk_score > 100):
            raise ValueError("Risk score must be between 0 and 100")
        return risk_score
    
    @validates('ip_address')
    def validate_ip_address(self, key, ip_address):
        """Validate IP address format"""
        if ip_address:
            from ipaddress import ip_address as validate_ip
            try:
                validate_ip(ip_address)
            except ValueError as e:
                raise ValueError(f"Invalid IP address: {e}")
        return ip_address
    
    @hybrid_property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event"""
        security_event_types = [
            AuditEventType.LOGIN_FAILED,
            AuditEventType.ACCOUNT_LOCKED,
            AuditEventType.ACCESS_DENIED,
            AuditEventType.SECURITY_ALERT,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.RATE_LIMIT_EXCEEDED,
            AuditEventType.IP_BLOCKED,
            AuditEventType.COMPLIANCE_VIOLATION
        ]
        return self.event_type in security_event_types or self.security_alert
    
    @hybrid_property
    def is_compliance_event(self) -> bool:
        """Check if this is a compliance-related event"""
        compliance_event_types = [
            AuditEventType.DATA_RETENTION,
            AuditEventType.DATA_PURGE,
            AuditEventType.COMPLIANCE_VIOLATION,
            AuditEventType.AUDIT_LOG_ACCESS,
            AuditEventType.DATA_EXPORT
        ]
        return self.event_type in compliance_event_types
    
    @hybrid_property
    def is_data_access_event(self) -> bool:
        """Check if this is a data access event"""
        data_event_types = [
            AuditEventType.DATA_READ,
            AuditEventType.DATA_CREATE,
            AuditEventType.DATA_UPDATE,
            AuditEventType.DATA_DELETE,
            AuditEventType.DATA_EXPORT,
            AuditEventType.DATA_IMPORT
        ]
        return self.event_type in data_event_types
    
    @hybrid_property
    def requires_retention(self) -> bool:
        """Check if event requires extended retention"""
        return (
            self.sensitive_data or
            self.is_security_event or
            self.is_compliance_event or
            self.severity in [AuditSeverity.CRITICAL, AuditSeverity.HIGH]
        )
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the event"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def set_correlation(self, correlation_id: str, parent_event_id: Optional[str] = None) -> None:
        """Set correlation ID and optional parent event"""
        self.correlation_id = correlation_id
        if parent_event_id:
            self.parent_event_id = uuid.UUID(parent_event_id)
    
    def mark_sensitive(self, data_classification: str = "confidential") -> None:
        """Mark event as containing sensitive data"""
        self.sensitive_data = True
        self.data_classification = data_classification
        
        # Extend retention period for sensitive data
        if not self.retention_required_until:
            from datetime import timedelta
            self.retention_required_until = datetime.now(timezone.utc) + timedelta(days=2555)  # 7 years
    
    def calculate_risk_score(self) -> int:
        """Calculate risk score based on event characteristics"""
        score = 0
        
        # Base score by event type
        high_risk_events = [
            AuditEventType.LOGIN_FAILED,
            AuditEventType.ACCESS_DENIED,
            AuditEventType.DATA_DELETE,
            AuditEventType.SECURITY_ALERT,
            AuditEventType.SUSPICIOUS_ACTIVITY
        ]
        
        if self.event_type in high_risk_events:
            score += 30
        elif self.event_outcome == "failure":
            score += 20
        elif self.is_security_event:
            score += 25
        
        # Severity modifier
        severity_scores = {
            AuditSeverity.CRITICAL: 40,
            AuditSeverity.HIGH: 30,
            AuditSeverity.MEDIUM: 15,
            AuditSeverity.LOW: 5,
            AuditSeverity.INFO: 0
        }
        score += severity_scores.get(self.severity, 0)
        
        # Sensitive data modifier
        if self.sensitive_data:
            score += 20
        
        # Multiple failures from same IP
        if self.ip_address and self.event_outcome == "failure":
            # This would require a query to count recent failures
            score += 10
        
        return min(100, max(0, score))
    
    def generate_alert(self) -> Optional[Dict[str, Any]]:
        """Generate security alert if conditions are met"""
        if not self.is_security_event and self.risk_score < 70:
            return None
        
        return {
            "alert_id": str(uuid.uuid4()),
            "client_id": str(self.client_id),
            "event_id": str(self.id),
            "alert_type": "security_event",
            "severity": self.severity.value,
            "title": f"Security Event: {self.event_name}",
            "description": self.event_description,
            "risk_score": self.risk_score,
            "timestamp": self.event_timestamp.isoformat(),
            "source_ip": str(self.ip_address) if self.ip_address else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "metadata": self.metadata
        }
    
    @staticmethod
    def _get_category_for_event_type(event_type: AuditEventType) -> str:
        """Get category for event type"""
        categories = {
            AuditEventType.LOGIN: "authentication",
            AuditEventType.LOGOUT: "authentication",
            AuditEventType.LOGIN_FAILED: "authentication",
            AuditEventType.PASSWORD_CHANGE: "authentication",
            AuditEventType.PASSWORD_RESET: "authentication",
            AuditEventType.TOKEN_REFRESH: "authentication",
            AuditEventType.ACCOUNT_LOCKED: "authentication",
            
            AuditEventType.ACCESS_GRANTED: "authorization",
            AuditEventType.ACCESS_DENIED: "authorization",
            AuditEventType.PERMISSION_CHANGE: "authorization",
            AuditEventType.ROLE_CHANGE: "authorization",
            
            AuditEventType.DATA_READ: "data_access",
            AuditEventType.DATA_CREATE: "data_access",
            AuditEventType.DATA_UPDATE: "data_access",
            AuditEventType.DATA_DELETE: "data_access",
            AuditEventType.DATA_EXPORT: "data_access",
            AuditEventType.DATA_IMPORT: "data_access",
            
            AuditEventType.CONFIG_CHANGE: "configuration",
            AuditEventType.FEATURE_TOGGLE: "configuration",
            AuditEventType.INTEGRATION_CHANGE: "configuration",
            
            AuditEventType.SYSTEM_START: "system",
            AuditEventType.SYSTEM_STOP: "system",
            AuditEventType.BACKUP_CREATE: "system",
            AuditEventType.BACKUP_RESTORE: "system",
            
            AuditEventType.DATA_RETENTION: "compliance",
            AuditEventType.DATA_PURGE: "compliance",
            AuditEventType.COMPLIANCE_VIOLATION: "compliance",
            AuditEventType.AUDIT_LOG_ACCESS: "compliance",
            
            AuditEventType.SECURITY_ALERT: "security",
            AuditEventType.SUSPICIOUS_ACTIVITY: "security",
            AuditEventType.RATE_LIMIT_EXCEEDED: "security",
            AuditEventType.IP_BLOCKED: "security",
            
            AuditEventType.API_CALL: "api",
            AuditEventType.API_ERROR: "api",
            AuditEventType.WEBHOOK_SENT: "api",
            AuditEventType.WEBHOOK_FAILED: "api",
        }
        
        return categories.get(event_type, "general")
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert audit log to dictionary"""
        data = {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "event_type": self.event_type.value,
            "event_category": self.event_category,
            "severity": self.severity.value,
            "event_name": self.event_name,
            "event_description": self.event_description,
            "event_outcome": self.event_outcome,
            "user_id": str(self.user_id) if self.user_id else None,
            "username": self.username,
            "user_email": self.user_email,
            "user_role": self.user_role,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "api_endpoint": self.api_endpoint,
            "http_method": self.http_method,
            "http_status_code": self.http_status_code,
            "event_timestamp": self.event_timestamp.isoformat(),
            "is_security_event": self.is_security_event,
            "is_compliance_event": self.is_compliance_event,
            "is_data_access_event": self.is_data_access_event,
            "risk_score": self.risk_score,
            "tags": self.tags,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_sensitive:
            data.update({
                "ip_address": str(self.ip_address) if self.ip_address else None,
                "user_agent": self.user_agent,
                "session_id": self.session_id,
                "request_id": self.request_id,
                "old_values": self.old_values,
                "new_values": self.new_values,
                "field_changes": self.field_changes,
                "metadata": self.metadata,
                "error_code": self.error_code,
                "error_message": self.error_message,
                "sensitive_data": self.sensitive_data,
                "data_classification": self.data_classification,
            })
        
        return data
    
    def __repr__(self):
        return f"<ClientAuditLog(id='{self.id}', event_type='{self.event_type}', severity='{self.severity}')>"


class ComplianceReport(BaseModel):
    """
    Compliance reporting and audit trail summaries
    """
    __tablename__ = "compliance_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # Report details
    report_type = Column(String(100), nullable=False)
    compliance_framework = Column(Enum(ComplianceFramework), nullable=False)
    reporting_period_start = Column(DateTime(timezone=True), nullable=False)
    reporting_period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Report content
    summary = Column(JSONB, nullable=False, default=dict)
    findings = Column(JSONB, nullable=False, default=list)
    recommendations = Column(JSONB, nullable=False, default=list)
    
    # Status
    status = Column(String(20), nullable=False, default="draft")
    generated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # External references
    external_report_id = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    
    # Relationships
    client = relationship("Client")
    
    __table_args__ = (
        Index('idx_compliance_client_framework', 'client_id', 'compliance_framework'),
        Index('idx_compliance_status', 'status'),
        Index('idx_compliance_period', 'reporting_period_start', 'reporting_period_end'),
    )
    
    def __repr__(self):
        return f"<ComplianceReport(id='{self.id}', framework='{self.compliance_framework}', status='{self.status}')>"