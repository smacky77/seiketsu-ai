"""
Voice Agent model for AI-powered voice interactions
"""
from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from enum import Enum
from typing import Optional, Dict, Any, List

from .base import BaseModel, TenantMixin, AuditMixin


class VoiceAgentStatus(str, Enum):
    DRAFT = "draft"
    TRAINING = "training"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class VoiceAgentType(str, Enum):
    LEAD_QUALIFICATION = "lead_qualification"
    PROPERTY_SHOWING = "property_showing"
    CUSTOMER_SERVICE = "customer_service"
    FOLLOW_UP = "follow_up"
    GENERAL_INQUIRY = "general_inquiry"
    CUSTOM = "custom"


class VoiceProvider(str, Enum):
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"
    AZURE = "azure"
    GOOGLE = "google"


class VoiceAgent(BaseModel, TenantMixin, AuditMixin):
    """AI Voice Agent configuration and management"""
    __tablename__ = "voice_agents"
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(VoiceAgentType), default=VoiceAgentType.LEAD_QUALIFICATION)
    status = Column(SQLEnum(VoiceAgentStatus), default=VoiceAgentStatus.DRAFT)
    
    # Voice configuration
    voice_provider = Column(SQLEnum(VoiceProvider), default=VoiceProvider.ELEVENLABS)
    voice_id = Column(String(255))  # Provider-specific voice ID
    voice_name = Column(String(255))  # Human-readable voice name
    voice_settings = Column(JSON, default=dict)  # Speed, pitch, stability, etc.
    
    # AI Model configuration
    ai_model = Column(String(100), default="gpt-4")  # OpenAI model or equivalent
    system_prompt = Column(Text, nullable=False)
    max_tokens = Column(Integer, default=2000)
    temperature = Column(Float, default=0.7)
    
    # Conversation flow
    greeting_message = Column(Text)
    fallback_message = Column(Text)
    goodbye_message = Column(Text)
    conversation_starters = Column(JSON, default=list)
    
    # Knowledge base and training
    knowledge_base = Column(JSON, default=dict)
    training_data = Column(JSON, default=list)
    fine_tuning_job_id = Column(String(255))  # For custom model training
    
    # Business logic
    qualification_criteria = Column(JSON, default=dict)
    lead_scoring_rules = Column(JSON, default=dict)
    integration_webhooks = Column(JSON, default=list)
    
    # Performance settings
    response_timeout_ms = Column(Integer, default=5000)
    max_conversation_duration_minutes = Column(Integer, default=30)
    max_silence_duration_seconds = Column(Integer, default=10)
    
    # Analytics and monitoring
    total_conversations = Column(Integer, default=0)
    total_leads_generated = Column(Integer, default=0)
    average_conversation_duration = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    
    # Features and capabilities
    can_transfer_to_human = Column(Boolean, default=True)
    can_schedule_appointments = Column(Boolean, default=True)
    can_send_emails = Column(Boolean, default=False)
    can_send_sms = Column(Boolean, default=False)
    can_access_crm = Column(Boolean, default=True)
    
    # Phone number assignment
    phone_number = Column(String(50), unique=True, index=True)
    phone_number_provider = Column(String(100))  # Twilio, etc.
    phone_number_sid = Column(String(255))  # Provider-specific ID
    
    # Working hours and availability
    working_hours = Column(JSON, default=dict)  # Day/time availability
    timezone = Column(String(50), default="UTC")
    is_24_7_available = Column(Boolean, default=False)
    
    # Compliance and recording
    call_recording_enabled = Column(Boolean, default=True)
    compliance_disclaimers = Column(JSON, default=list)
    data_retention_days = Column(Integer, default=90)
    
    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="voice_agents")
    
    # Conversations relationship
    conversations = relationship("Conversation", back_populates="voice_agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<VoiceAgent(id={self.id}, name={self.name}, type={self.type})>"
    
    @property
    def is_active(self) -> bool:
        return self.status == VoiceAgentStatus.ACTIVE
    
    @property
    def average_conversation_duration_minutes(self) -> float:
        return self.average_conversation_duration / 60.0 if self.average_conversation_duration else 0.0
    
    def can_handle_call(self) -> bool:
        """Check if agent can handle calls right now"""
        if not self.is_active:
            return False
        
        if self.is_24_7_available:
            return True
        
        # Check working hours (would need timezone logic)
        # This is a simplified version
        return True
    
    def update_performance_stats(self, conversation_duration: float, was_successful: bool):
        """Update performance statistics"""
        self.total_conversations += 1
        
        if was_successful:
            self.total_leads_generated += 1
        
        # Update average duration
        if self.total_conversations == 1:
            self.average_conversation_duration = conversation_duration
        else:
            total_duration = self.average_conversation_duration * (self.total_conversations - 1)
            self.average_conversation_duration = (total_duration + conversation_duration) / self.total_conversations
        
        # Update success rate
        self.success_rate = self.total_leads_generated / self.total_conversations
    
    def get_voice_settings_for_provider(self) -> Dict[str, Any]:
        """Get voice settings formatted for the specific provider"""
        settings = self.voice_settings or {}
        
        if self.voice_provider == VoiceProvider.ELEVENLABS:
            return {
                "voice_id": self.voice_id,
                "model_id": settings.get("model_id", "eleven_monolingual_v1"),
                "voice_settings": {
                    "stability": settings.get("stability", 0.75),
                    "similarity_boost": settings.get("similarity_boost", 0.75),
                    "style": settings.get("style", 0.0),
                    "use_speaker_boost": settings.get("use_speaker_boost", True)
                }
            }
        
        return settings
    
    def get_system_prompt_with_context(self, additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Get system prompt with organization and agent context"""
        context = {
            "agent_name": self.name,
            "agent_type": self.type.value,
            "organization_name": self.organization.name if self.organization else "Unknown",
            "phone_number": self.phone_number,
            **(additional_context or {})
        }
        
        prompt = self.system_prompt
        for key, value in context.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        
        return prompt