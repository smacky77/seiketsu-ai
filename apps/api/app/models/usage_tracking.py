"""
Usage tracking and billing models
Handles client usage metrics, billing records, and subscription management
"""
import enum
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Boolean, Column, String, DateTime, Date, Text, Integer,
    Numeric, JSON, Enum, ForeignKey, Index, CheckConstraint,
    UniqueConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
import uuid

from .base import BaseModel


class UsageMetricType(str, enum.Enum):
    """Types of usage metrics tracked"""
    API_CALLS = "api_calls"
    VOICE_SYNTHESIS = "voice_synthesis"
    VOICE_MINUTES = "voice_minutes"
    CONVERSATION_COUNT = "conversation_count"
    STORAGE_BYTES = "storage_bytes"
    BANDWIDTH_BYTES = "bandwidth_bytes"
    USER_COUNT = "user_count"
    PROPERTY_COUNT = "property_count"
    LEAD_COUNT = "lead_count"
    WEBHOOK_DELIVERIES = "webhook_deliveries"
    AI_TOKENS = "ai_tokens"
    CUSTOM_METRIC = "custom_metric"


class BillingPeriod(str, enum.Enum):
    """Billing period types"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    USAGE_BASED = "usage_based"
    ONE_TIME = "one_time"


class PaymentStatus(str, enum.Enum):
    """Payment status for billing records"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class InvoiceStatus(str, enum.Enum):
    """Invoice status"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ClientUsageRecord(BaseModel):
    """
    Tracks detailed usage metrics per client
    Aggregated at different time intervals
    """
    __tablename__ = "client_usage_records"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # Metric identification
    metric_type = Column(Enum(UsageMetricType), nullable=False)
    metric_name = Column(String(255), nullable=False)  # Human readable name
    metric_unit = Column(String(50), nullable=False)  # e.g., "calls", "bytes", "minutes"
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # "hour", "day", "month", "year"
    
    # Usage data
    usage_count = Column(BigInteger, nullable=False, default=0)
    usage_limit = Column(BigInteger, nullable=True)  # Null = unlimited
    
    # Cost calculation
    unit_cost = Column(Numeric(10, 4), nullable=True)  # Cost per unit
    total_cost = Column(Numeric(12, 4), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Metadata and context
    metadata = Column(JSONB, nullable=False, default=dict)
    source_data = Column(JSONB, nullable=True)  # Raw data used for calculation
    
    # Relationships
    client = relationship("Client", back_populates="usage_records")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_usage_client_period', 'client_id', 'period_start', 'period_end'),
        Index('idx_usage_metric_type', 'metric_type'),
        Index('idx_usage_period_start', 'period_start'),
        Index('idx_usage_total_cost', 'total_cost'),
        UniqueConstraint(
            'client_id', 'metric_type', 'period_start', 'period_end',
            name='uq_client_metric_period'
        ),
    )
    
    @validates('usage_count')
    def validate_usage_count(self, key, usage_count):
        """Validate usage count is not negative"""
        if usage_count < 0:
            raise ValueError("Usage count cannot be negative")
        return usage_count
    
    @validates('currency')
    def validate_currency(self, key, currency):
        """Validate currency code"""
        if currency and len(currency) != 3:
            raise ValueError("Currency must be 3-character ISO code")
        return currency.upper() if currency else currency
    
    @hybrid_property
    def is_over_limit(self) -> bool:
        """Check if usage exceeds limit"""
        if self.usage_limit is None:
            return False
        return self.usage_count > self.usage_limit
    
    @hybrid_property
    def usage_percentage(self) -> float:
        """Calculate usage as percentage of limit"""
        if self.usage_limit is None or self.usage_limit == 0:
            return 0.0
        return min(100.0, (self.usage_count / self.usage_limit) * 100.0)
    
    @hybrid_property
    def overage_amount(self) -> int:
        """Calculate overage amount if over limit"""
        if not self.is_over_limit:
            return 0
        return self.usage_count - self.usage_limit
    
    def calculate_cost(self, rate_card: Dict[str, Any] = None) -> Decimal:
        """Calculate cost based on usage and rate card"""
        if not self.unit_cost:
            return Decimal('0.00')
            
        base_cost = Decimal(str(self.usage_count)) * Decimal(str(self.unit_cost))
        
        # Apply overage rates if applicable
        if rate_card and self.is_over_limit:
            overage_rate = rate_card.get('overage_multiplier', 1.5)
            overage_cost = Decimal(str(self.overage_amount)) * Decimal(str(self.unit_cost)) * Decimal(str(overage_rate))
            limit_cost = Decimal(str(self.usage_limit)) * Decimal(str(self.unit_cost))
            base_cost = limit_cost + overage_cost
            
        return base_cost.quantize(Decimal('0.0001'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert usage record to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "metric_type": self.metric_type.value,
            "metric_name": self.metric_name,
            "metric_unit": self.metric_unit,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "period_type": self.period_type,
            "usage_count": self.usage_count,
            "usage_limit": self.usage_limit,
            "unit_cost": float(self.unit_cost) if self.unit_cost else None,
            "total_cost": float(self.total_cost),
            "currency": self.currency,
            "is_over_limit": self.is_over_limit,
            "usage_percentage": self.usage_percentage,
            "overage_amount": self.overage_amount,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<ClientUsageRecord(client_id='{self.client_id}', metric='{self.metric_type}', usage={self.usage_count})>"


class ClientBillingRecord(BaseModel):
    """
    Billing records for client subscriptions and usage charges
    """
    __tablename__ = "client_billing_records"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # Billing details
    billing_period = Column(Enum(BillingPeriod), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Invoice information
    invoice_number = Column(String(100), unique=True, nullable=False)
    invoice_status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT)
    
    # Financial details
    subtotal_amount = Column(Numeric(12, 4), nullable=False, default=0)
    tax_amount = Column(Numeric(12, 4), nullable=False, default=0)
    discount_amount = Column(Numeric(12, 4), nullable=False, default=0)
    total_amount = Column(Numeric(12, 4), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Payment tracking
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(255), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Due dates
    due_date = Column(Date, nullable=False)
    overdue_at = Column(DateTime(timezone=True), nullable=True)
    
    # Line items and breakdown
    line_items = Column(JSONB, nullable=False, default=list)
    usage_breakdown = Column(JSONB, nullable=True)
    
    # External references
    stripe_invoice_id = Column(String(255), nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=False, default=dict)
    
    # Relationships
    client = relationship("Client")
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_client_period', 'client_id', 'period_start', 'period_end'),
        Index('idx_billing_invoice_status', 'invoice_status'),
        Index('idx_billing_payment_status', 'payment_status'),
        Index('idx_billing_due_date', 'due_date'),
        Index('idx_billing_invoice_number', 'invoice_number'),
    )
    
    def __init__(self, **kwargs):
        # Auto-generate invoice number if not provided
        if 'invoice_number' not in kwargs:
            kwargs['invoice_number'] = self._generate_invoice_number()
        super().__init__(**kwargs)
    
    @validates('total_amount')
    def validate_total_amount(self, key, total_amount):
        """Validate total amount is not negative"""
        if total_amount < 0:
            raise ValueError("Total amount cannot be negative")
        return total_amount
    
    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        if self.payment_status == PaymentStatus.PAID:
            return False
        return date.today() > self.due_date
    
    @hybrid_property
    def days_overdue(self) -> int:
        """Calculate days overdue"""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    @hybrid_property
    def net_amount(self) -> Decimal:
        """Calculate net amount after discounts"""
        return Decimal(str(self.subtotal_amount)) - Decimal(str(self.discount_amount))
    
    def add_line_item(self, description: str, quantity: int, unit_price: Decimal, 
                     metadata: Optional[Dict] = None) -> None:
        """Add a line item to the invoice"""
        if self.line_items is None:
            self.line_items = []
            
        line_item = {
            "id": str(uuid.uuid4()),
            "description": description,
            "quantity": quantity,
            "unit_price": float(unit_price),
            "total_price": float(quantity * unit_price),
            "metadata": metadata or {}
        }
        
        self.line_items.append(line_item)
        self._recalculate_totals()
    
    def apply_discount(self, discount_amount: Decimal, reason: str = None) -> None:
        """Apply discount to the invoice"""
        self.discount_amount = discount_amount
        if reason:
            if 'discount_reason' not in self.metadata:
                self.metadata['discount_reason'] = reason
        self._recalculate_totals()
    
    def mark_as_paid(self, payment_reference: str = None, payment_method: str = None) -> None:
        """Mark invoice as paid"""
        self.payment_status = PaymentStatus.PAID
        self.invoice_status = InvoiceStatus.PAID
        self.paid_at = datetime.now(timezone.utc)
        if payment_reference:
            self.payment_reference = payment_reference
        if payment_method:
            self.payment_method = payment_method
    
    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        # Format: INV-YYYY-MM-XXXXXXXX
        now = datetime.now()
        random_suffix = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"INV-{now.year}-{now.month:02d}-{random_suffix}"
    
    def _recalculate_totals(self) -> None:
        """Recalculate invoice totals"""
        # Calculate subtotal from line items
        subtotal = Decimal('0.00')
        if self.line_items:
            for item in self.line_items:
                subtotal += Decimal(str(item.get('total_price', 0)))
        
        self.subtotal_amount = subtotal
        
        # Calculate total with tax and discount
        net_amount = self.subtotal_amount - self.discount_amount
        total_with_tax = net_amount + self.tax_amount
        self.total_amount = total_with_tax
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert billing record to dictionary"""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "billing_period": self.billing_period.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "invoice_number": self.invoice_number,
            "invoice_status": self.invoice_status.value,
            "subtotal_amount": float(self.subtotal_amount),
            "tax_amount": float(self.tax_amount),
            "discount_amount": float(self.discount_amount),
            "total_amount": float(self.total_amount),
            "net_amount": float(self.net_amount),
            "currency": self.currency,
            "payment_status": self.payment_status.value,
            "payment_method": self.payment_method,
            "payment_reference": self.payment_reference,
            "due_date": self.due_date.isoformat(),
            "is_overdue": self.is_overdue,
            "days_overdue": self.days_overdue,
            "line_items": self.line_items,
            "usage_breakdown": self.usage_breakdown,
            "notes": self.notes,
            "metadata": self.metadata,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<ClientBillingRecord(invoice_number='{self.invoice_number}', total='{self.total_amount}')>"


class ClientSubscription(BaseModel):
    """
    Manages client subscriptions and pricing plans
    """
    __tablename__ = "client_subscriptions"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # Subscription details
    plan_name = Column(String(255), nullable=False)
    plan_description = Column(Text, nullable=True)
    tier = Column(String(50), nullable=False)  # Links to ClientTier
    
    # Pricing
    monthly_price = Column(Numeric(10, 4), nullable=True)
    annual_price = Column(Numeric(12, 4), nullable=True)
    setup_fee = Column(Numeric(10, 4), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Billing configuration
    billing_period = Column(Enum(BillingPeriod), nullable=False, default=BillingPeriod.MONTHLY)
    next_billing_date = Column(Date, nullable=False)
    billing_day = Column(Integer, nullable=True)  # Day of month for billing
    
    # Subscription lifecycle
    status = Column(String(20), nullable=False, default="active")
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    ends_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Trial period
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    trial_used = Column(Boolean, nullable=False, default=False)
    
    # External references
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Plan configuration
    included_features = Column(JSONB, nullable=False, default=list)
    usage_limits = Column(JSONB, nullable=False, default=dict)
    rate_card = Column(JSONB, nullable=False, default=dict)
    
    # Metadata
    metadata = Column(JSONB, nullable=False, default=dict)
    
    # Relationships
    client = relationship("Client")
    
    # Indexes
    __table_args__ = (
        Index('idx_subscription_client', 'client_id'),
        Index('idx_subscription_status', 'status'),
        Index('idx_subscription_next_billing', 'next_billing_date'),
        Index('idx_subscription_ends_at', 'ends_at'),
    )
    
    @hybrid_property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == "active"
    
    @hybrid_property
    def is_in_trial(self) -> bool:
        """Check if subscription is in trial period"""
        if not self.trial_ends_at:
            return False
        return datetime.now(timezone.utc) < self.trial_ends_at
    
    @hybrid_property
    def days_until_renewal(self) -> int:
        """Calculate days until next billing"""
        today = date.today()
        return (self.next_billing_date - today).days
    
    def get_current_price(self) -> Decimal:
        """Get current subscription price"""
        if self.billing_period == BillingPeriod.MONTHLY:
            return Decimal(str(self.monthly_price or 0))
        elif self.billing_period == BillingPeriod.ANNUALLY:
            return Decimal(str(self.annual_price or 0))
        return Decimal('0.00')
    
    def has_feature(self, feature: str) -> bool:
        """Check if subscription includes specific feature"""
        if not self.included_features:
            return False
        return feature in self.included_features
    
    def get_usage_limit(self, metric: str) -> Optional[int]:
        """Get usage limit for specific metric"""
        if not self.usage_limits:
            return None
        return self.usage_limits.get(metric)
    
    def get_rate(self, metric: str) -> Optional[Decimal]:
        """Get rate for specific usage metric"""
        if not self.rate_card:
            return None
        rate = self.rate_card.get(metric)
        return Decimal(str(rate)) if rate else None
    
    def __repr__(self):
        return f"<ClientSubscription(client_id='{self.client_id}', plan='{self.plan_name}', status='{self.status}')>"