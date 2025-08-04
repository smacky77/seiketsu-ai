"""
Lead model for real estate prospects
"""
from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

from .base import BaseModel, TenantMixin, AuditMixin


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    OPPORTUNITY = "opportunity"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class LeadSource(str, Enum):
    VOICE_CALL = "voice_call"
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    ADVERTISING = "advertising"
    WALK_IN = "walk_in"
    OTHER = "other"


class PropertyType(str, Enum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    COMMERCIAL = "commercial"
    LAND = "land"
    OTHER = "other"


class Lead(BaseModel, TenantMixin, AuditMixin):
    """Real estate lead and prospect information"""
    __tablename__ = "leads"
    
    # Basic contact information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50), index=True)
    phone_secondary = Column(String(50))
    
    # Address information
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="US")
    
    # Lead management
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    source = Column(SQLEnum(LeadSource), default=LeadSource.VOICE_CALL)
    source_details = Column(String(500))
    
    # Qualification and scoring
    lead_score = Column(Integer, default=0)  # 0 to 100
    qualification_notes = Column(Text)
    budget_min = Column(Float)
    budget_max = Column(Float)
    timeline = Column(String(100))  # "immediate", "3_months", "6_months", etc.
    
    # Property preferences
    preferred_property_type = Column(SQLEnum(PropertyType))
    preferred_bedrooms = Column(Integer)
    preferred_bathrooms = Column(Float)
    preferred_sqft_min = Column(Integer)
    preferred_sqft_max = Column(Integer)
    preferred_locations = Column(JSON, default=list)
    special_requirements = Column(Text)
    
    # Buying/selling intent
    is_buyer = Column(Boolean, default=True)
    is_seller = Column(Boolean, default=False)
    current_home_value = Column(Float)
    needs_to_sell_first = Column(Boolean, default=False)
    
    # Financing information
    pre_approved = Column(Boolean, default=False)
    financing_type = Column(String(100))  # "conventional", "fha", "va", "cash"
    down_payment_amount = Column(Float)
    down_payment_percentage = Column(Float)
    
    # Agent assignment and tracking
    assigned_agent_id = Column(String, ForeignKey("users.id"), index=True)
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id])
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    created_by_user = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_leads")
    
    # Conversation relationship
    conversation_id = Column(String, ForeignKey("conversations.id"), index=True)
    conversation = relationship("Conversation", back_populates="lead")
    
    # CRM integration
    crm_contact_id = Column(String(255), index=True)  # External CRM ID
    crm_last_sync = Column(DateTime)
    crm_sync_status = Column(String(100))
    
    # Marketing and attribution
    utm_source = Column(String(255))
    utm_medium = Column(String(255))
    utm_campaign = Column(String(255))
    utm_term = Column(String(255))
    utm_content = Column(String(255))
    
    # Activity tracking
    last_contact_date = Column(DateTime)
    last_contact_method = Column(String(100))
    contact_attempts = Column(Integer, default=0)
    next_follow_up_date = Column(DateTime)
    
    # Preferences and communication
    preferred_contact_method = Column(String(100), default="phone")
    preferred_contact_time = Column(String(100))
    timezone = Column(String(50))
    do_not_call = Column(Boolean, default=False)
    do_not_email = Column(Boolean, default=False)
    
    # Additional data
    notes = Column(Text)
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    
    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="leads")
    
    def __repr__(self):
        return f"<Lead(id={self.id}, name={self.full_name}, status={self.status})>"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def budget_range_formatted(self) -> Optional[str]:
        if self.budget_min and self.budget_max:
            return f"${self.budget_min:,} - ${self.budget_max:,}"
        elif self.budget_min:
            return f"${self.budget_min:,}+"
        elif self.budget_max:
            return f"Under ${self.budget_max:,}"
        return None
    
    @property
    def is_hot_lead(self) -> bool:
        """Determine if this is a hot lead based on score and timeline"""
        return (
            self.lead_score >= 75 or
            self.timeline in ["immediate", "1_month"] or
            self.pre_approved
        )
    
    @property
    def days_since_last_contact(self) -> Optional[int]:
        if not self.last_contact_date:
            return None
        return (datetime.utcnow() - self.last_contact_date).days
    
    @property
    def needs_follow_up(self) -> bool:
        if not self.next_follow_up_date:
            return False
        return datetime.utcnow() >= self.next_follow_up_date
    
    def update_lead_score(self):
        """Calculate and update lead score based on available data"""
        score = 0
        
        # Contact information completeness
        if self.email:
            score += 10
        if self.phone:
            score += 10
        
        # Budget defined
        if self.budget_min or self.budget_max:
            score += 20
        
        # Timeline urgency
        timeline_scores = {
            "immediate": 30,
            "1_month": 25,
            "3_months": 15,
            "6_months": 10,
            "1_year": 5
        }
        score += timeline_scores.get(self.timeline, 0)
        
        # Pre-approval status
        if self.pre_approved:
            score += 25
        
        # Conversation quality (if from voice call)
        if self.conversation and self.conversation.sentiment_score:
            if self.conversation.sentiment_score > 0.5:
                score += 15
            elif self.conversation.sentiment_score > 0:
                score += 5
        
        self.lead_score = min(score, 100)
        return self.lead_score
    
    def add_tag(self, tag: str):
        """Add a tag to the lead"""
        tags = self.tags or []
        if tag not in tags:
            tags.append(tag)
            self.tags = tags
    
    def remove_tag(self, tag: str):
        """Remove a tag from the lead"""
        tags = self.tags or []
        if tag in tags:
            tags.remove(tag)
            self.tags = tags
    
    def update_last_contact(self, method: str = "phone"):
        """Update last contact information"""
        self.last_contact_date = datetime.utcnow()
        self.last_contact_method = method
        self.contact_attempts = (self.contact_attempts or 0) + 1