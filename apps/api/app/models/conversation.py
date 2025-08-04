"""
Conversation and message models for voice interactions
"""
from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from .base import BaseModel, TenantMixin, AuditMixin


class ConversationStatus(str, Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    TRANSFERRED = "transferred"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class ConversationOutcome(str, Enum):
    LEAD_QUALIFIED = "lead_qualified"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    INFORMATION_PROVIDED = "information_provided"
    TRANSFERRED_TO_HUMAN = "transferred_to_human"
    NO_INTEREST = "no_interest"
    INCOMPLETE = "incomplete"


class MessageType(str, Enum):
    USER_SPEECH = "user_speech"
    AGENT_SPEECH = "agent_speech"
    SYSTEM_EVENT = "system_event"
    TRANSFER_REQUEST = "transfer_request"
    APPOINTMENT_BOOKING = "appointment_booking"


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Conversation(BaseModel, TenantMixin, AuditMixin):
    """Voice conversation session"""
    __tablename__ = "conversations"
    
    # Basic information
    call_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(String(255), index=True)
    
    # Participants
    caller_phone = Column(String(50), nullable=False, index=True)
    caller_name = Column(String(255))
    caller_email = Column(String(255))
    
    # Voice agent
    voice_agent_id = Column(String, ForeignKey("voice_agents.id"), nullable=False, index=True)
    voice_agent = relationship("VoiceAgent", back_populates="conversations")
    
    # Status and outcome
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.INITIATED)
    outcome = Column(SQLEnum(ConversationOutcome))
    outcome_details = Column(JSON, default=dict)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer, default=0)
    
    # Quality metrics
    sentiment_score = Column(Float)  # -1 to 1
    confidence_score = Column(Float)  # 0 to 1
    transcription_quality = Column(Float)  # 0 to 1
    
    # Lead information (if qualified)
    lead_score = Column(Integer, default=0)  # 0 to 100
    lead_id = Column(String, ForeignKey("leads.id"), index=True)
    lead = relationship("Lead", back_populates="conversation")
    
    # Human handoff
    transferred_to_human = Column(Boolean, default=False)
    transfer_reason = Column(String(500))
    human_agent_name = Column(String(255))
    transfer_timestamp = Column(DateTime)
    
    # Assignment and ownership
    assigned_to_user_id = Column(String, ForeignKey("users.id"), index=True)
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id], back_populates="assigned_conversations")
    created_by_user_id = Column(String, ForeignKey("users.id"), index=True)
    created_by_user = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_conversations")
    
    # Recording and transcription
    recording_url = Column(String(500))
    recording_duration = Column(Integer)  # seconds
    transcription_url = Column(String(500))
    full_transcription = Column(Text)
    
    # Technical details
    call_provider = Column(String(100))  # Twilio, etc.
    call_provider_id = Column(String(255))
    audio_quality_score = Column(Float)
    
    # Business context
    campaign_id = Column(String(255), index=True)
    source = Column(String(100))  # website, google_ads, etc.
    utm_parameters = Column(JSON, default=dict)
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    next_follow_up_date = Column(DateTime)
    
    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="conversations")
    
    # Messages relationship
    messages = relationship(
        "ConversationMessage", 
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.timestamp"
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, call_id={self.call_id}, status={self.status})>"
    
    @property
    def duration_minutes(self) -> float:
        return self.duration_seconds / 60.0 if self.duration_seconds else 0.0
    
    @property
    def is_active(self) -> bool:
        return self.status in [ConversationStatus.INITIATED, ConversationStatus.IN_PROGRESS]
    
    @property
    def was_successful(self) -> bool:
        return self.outcome in [
            ConversationOutcome.LEAD_QUALIFIED,
            ConversationOutcome.APPOINTMENT_SCHEDULED,
            ConversationOutcome.INFORMATION_PROVIDED
        ]
    
    def end_conversation(self, outcome: ConversationOutcome, outcome_details: Optional[Dict[str, Any]] = None):
        """End the conversation with specified outcome"""
        self.ended_at = datetime.utcnow()
        self.status = ConversationStatus.COMPLETED
        self.outcome = outcome
        if outcome_details:
            self.outcome_details = outcome_details
        
        if self.started_at:
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())
    
    def transfer_to_human(self, reason: str, agent_name: Optional[str] = None):
        """Transfer conversation to human agent"""
        self.transferred_to_human = True
        self.transfer_reason = reason
        self.human_agent_name = agent_name
        self.transfer_timestamp = datetime.utcnow()
        self.status = ConversationStatus.TRANSFERRED
    
    def calculate_lead_score(self) -> int:
        """Calculate lead score based on conversation data"""
        score = 0
        
        # Duration indicates engagement
        if self.duration_seconds:
            if self.duration_seconds > 300:  # 5+ minutes
                score += 30
            elif self.duration_seconds > 120:  # 2+ minutes
                score += 20
            elif self.duration_seconds > 60:  # 1+ minute
                score += 10
        
        # Positive sentiment
        if self.sentiment_score and self.sentiment_score > 0.5:
            score += 25
        elif self.sentiment_score and self.sentiment_score > 0:
            score += 10
        
        # Successful outcome
        if self.was_successful:
            score += 35
        
        # Contact information provided
        if self.caller_email:
            score += 10
        
        self.lead_score = min(score, 100)
        return self.lead_score


class ConversationMessage(BaseModel):
    """Individual message in a conversation"""
    __tablename__ = "conversation_messages"
    
    # Conversation relationship
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    conversation = relationship("Conversation", back_populates="messages")
    
    # Message details
    message_type = Column(SQLEnum(MessageType), nullable=False)
    direction = Column(SQLEnum(MessageDirection), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Speaker information
    speaker_name = Column(String(255))
    speaker_type = Column(String(100))  # "user", "agent", "system"
    
    # Audio details (for speech messages)
    audio_url = Column(String(500))
    audio_duration_ms = Column(Integer)
    
    # Transcription details
    transcription_confidence = Column(Float)
    raw_transcription = Column(Text)  # Before processing
    processed_text = Column(Text)  # After NLP processing
    
    # AI processing
    intent = Column(String(255))
    entities = Column(JSON, default=dict)  # Named entities extracted
    sentiment = Column(Float)  # Message-level sentiment
    
    # Technical metadata
    sequence_number = Column(Integer, nullable=False)
    processing_time_ms = Column(Integer)
    
    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, type={self.message_type}, speaker={self.speaker_name})>"
    
    @property
    def duration_seconds(self) -> float:
        return self.audio_duration_ms / 1000.0 if self.audio_duration_ms else 0.0
    
    def to_transcript_format(self) -> str:
        """Format message for transcript display"""
        timestamp_str = self.timestamp.strftime("%H:%M:%S")
        speaker = self.speaker_name or self.speaker_type or "Unknown"
        return f"[{timestamp_str}] {speaker}: {self.content}"