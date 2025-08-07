"""
Voice Agent Intelligence Models
Database models for enterprise voice intelligence features
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base

class VoiceAgentPersonality(Base):
    """Voice agent personality configuration"""
    __tablename__ = "voice_agent_personalities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Personality traits
    tone = Column(String(50), default="professional")  # professional, friendly, enthusiastic, authoritative
    pace = Column(String(50), default="normal")  # slow, normal, fast
    enthusiasm_level = Column(Float, default=0.7)  # 0.0 to 1.0
    empathy_level = Column(Float, default=0.7)  # 0.0 to 1.0
    formality_level = Column(Float, default=0.7)  # 0.0 to 1.0
    
    # Voice characteristics
    voice_pitch = Column(Float, default=0.0)  # -1.0 to 1.0
    voice_speed = Column(Float, default=1.0)  # 0.5 to 2.0
    voice_stability = Column(Float, default=0.8)  # 0.0 to 1.0
    
    # Conversation behavior
    interruption_tolerance = Column(Float, default=0.5)  # 0.0 to 1.0
    question_frequency = Column(Float, default=0.3)  # 0.0 to 1.0
    active_listening_cues = Column(JSON)  # ["I see", "That makes sense", etc.]
    
    # Domain expertise
    real_estate_expertise_level = Column(Float, default=0.8)  # 0.0 to 1.0
    market_knowledge_depth = Column(Float, default=0.7)  # 0.0 to 1.0
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agents = relationship("VoiceAgent", back_populates="personality")

class EmotionDetectionLog(Base):
    """Log of detected emotions during conversations"""
    __tablename__ = "emotion_detection_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    conversation_turn_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Emotion data
    detected_emotion = Column(String(50), nullable=False)  # joy, anger, fear, sadness, surprise, disgust, neutral
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    valence = Column(Float, nullable=False)  # -1.0 (negative) to 1.0 (positive)
    arousal = Column(Float, nullable=False)  # 0.0 (calm) to 1.0 (excited)
    
    # Context
    trigger_text = Column(Text)
    audio_features = Column(JSON)  # Extracted audio features
    processing_time_ms = Column(Integer)
    
    # Response adaptation
    response_strategy_used = Column(String(100))
    tone_adjustment = Column(String(50))
    pace_adjustment = Column(String(50))
    
    detected_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="emotion_logs")

class ConversationIntent(Base):
    """Detected intents during conversations"""
    __tablename__ = "conversation_intents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    conversation_turn_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Intent classification
    intent_name = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Context and entities
    trigger_text = Column(Text, nullable=False)
    extracted_entities = Column(JSON)  # {"location": ["downtown"], "budget": ["$500k"], etc.}
    
    # Intent-specific data
    intent_category = Column(String(50))  # property_search, scheduling, budget, etc.
    priority_level = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Follow-up actions
    recommended_response = Column(Text)
    next_questions = Column(JSON)
    escalation_required = Column(Boolean, default=False)
    
    detected_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="intent_logs")

class ObjectionHandlingLog(Base):
    """Log of objections and how they were handled"""
    __tablename__ = "objection_handling_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    # Objection details
    objection_type = Column(String(100), nullable=False)
    objection_text = Column(Text, nullable=False)
    objection_category = Column(String(50))  # price, location, timing, features, etc.
    severity_level = Column(String(20))  # low, medium, high
    
    # Handling strategy
    handling_strategy = Column(String(100))
    response_text = Column(Text)
    resolution_approach = Column(String(50))  # empathetic, data-driven, alternative, etc.
    
    # Outcome
    objection_resolved = Column(Boolean, default=False)
    client_satisfaction = Column(Float)  # 0.0 to 1.0 if measurable
    follow_up_required = Column(Boolean, default=False)
    
    # Analytics
    resolution_time_seconds = Column(Integer)
    confidence_in_resolution = Column(Float)
    
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="objection_logs")

class VoiceQualityMetrics(Base):
    """Voice quality metrics for conversation analysis"""
    __tablename__ = "voice_quality_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    # Audio quality metrics
    clarity_score = Column(Float)  # 0.0 to 1.0
    noise_level = Column(Float)  # 0.0 to 1.0
    volume_consistency = Column(Float)  # 0.0 to 1.0
    audio_dropout_count = Column(Integer, default=0)
    
    # Speech characteristics
    speech_rate_wpm = Column(Float)  # Words per minute
    pause_patterns = Column(JSON)  # Array of pause durations
    interruption_points = Column(JSON)  # Timestamps of interruptions
    
    # Conversation flow
    turn_taking_smoothness = Column(Float)  # 0.0 to 1.0
    overlap_percentage = Column(Float)  # Percentage of overlapping speech
    silence_duration_total = Column(Float)  # Total silence in seconds
    
    # Processing performance
    latency_speech_to_text_ms = Column(Integer)
    latency_processing_ms = Column(Integer)
    latency_text_to_speech_ms = Column(Integer)
    latency_total_ms = Column(Integer)
    
    # Quality scores
    overall_quality_score = Column(Float)  # Composite score 0.0 to 1.0
    user_experience_rating = Column(Float)  # 0.0 to 5.0 if available
    
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="quality_metrics")

class ConversationFlowAnalytics(Base):
    """Analytics for conversation flow and effectiveness"""
    __tablename__ = "conversation_flow_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    # Flow metrics
    conversation_stages = Column(JSON)  # Array of stages with timings
    stage_transitions = Column(JSON)  # Transitions between stages
    qualification_progress = Column(Float)  # 0.0 to 1.0
    
    # Engagement metrics
    client_engagement_score = Column(Float)  # 0.0 to 1.0
    agent_effectiveness_score = Column(Float)  # 0.0 to 1.0
    conversation_momentum = Column(Float)  # -1.0 to 1.0
    
    # Timing analysis
    time_to_qualification = Column(Integer)  # Seconds
    time_to_objection_handling = Column(Integer)  # Seconds
    time_to_next_steps = Column(Integer)  # Seconds
    
    # Topic analysis
    topics_covered = Column(JSON)  # Array of topics discussed
    topic_depth_scores = Column(JSON)  # Depth score for each topic
    missing_important_topics = Column(JSON)  # Topics that should have been covered
    
    # Outcome predictions
    likelihood_to_convert = Column(Float)  # 0.0 to 1.0
    recommended_follow_up_timing = Column(Integer)  # Hours
    optimal_next_contact_method = Column(String(50))
    
    # Performance benchmarks
    compared_to_top_performers = Column(Float)  # -1.0 to 1.0
    improvement_opportunities = Column(JSON)  # Array of specific improvements
    
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="flow_analytics")

class VoiceAgentLearningData(Base):
    """Learning data for continuous AI improvement"""
    __tablename__ = "voice_agent_learning_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("voice_agents.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    
    # Learning event
    event_type = Column(String(50), nullable=False)  # successful_handling, failed_response, etc.
    context_data = Column(JSON, nullable=False)
    outcome_data = Column(JSON)
    
    # Performance feedback
    success_metric = Column(Float)  # 0.0 to 1.0
    feedback_source = Column(String(50))  # system, human_supervisor, client_feedback
    feedback_details = Column(Text)
    
    # Learning application
    applied_to_training = Column(Boolean, default=False)
    improvement_implemented = Column(Boolean, default=False)
    implementation_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime)
    
    # Relationships
    agent = relationship("VoiceAgent")
    conversation = relationship("Conversation")

class RealTimeConversationSession(Base):
    """Real-time conversation session tracking"""
    __tablename__ = "realtime_conversation_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("voice_agents.id"), nullable=False)
    
    # Session state
    status = Column(String(20), default="active")  # active, paused, ended, error
    websocket_connection_id = Column(String(100))
    
    # Real-time metrics
    current_emotion = Column(String(50))
    current_intent = Column(String(100))
    current_confidence = Column(Float)
    live_transcription = Column(Text)
    
    # Performance tracking
    response_times = Column(JSON)  # Array of recent response times
    audio_quality_current = Column(Float)
    processing_queue_depth = Column(Integer, default=0)
    
    # Session analytics
    total_turns = Column(Integer, default=0)
    successful_interactions = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    
    # Relationships
    agent = relationship("VoiceAgent")
    conversation = relationship("Conversation")

# Add relationships to existing models
from app.models.conversation import Conversation
from app.models.voice_agent import VoiceAgent

# Extend Conversation model with new relationships
Conversation.emotion_logs = relationship("EmotionDetectionLog", back_populates="conversation")
Conversation.intent_logs = relationship("ConversationIntent", back_populates="conversation") 
Conversation.objection_logs = relationship("ObjectionHandlingLog", back_populates="conversation")
Conversation.quality_metrics = relationship("VoiceQualityMetrics", back_populates="conversation", uselist=False)
Conversation.flow_analytics = relationship("ConversationFlowAnalytics", back_populates="conversation", uselist=False)

# Extend VoiceAgent model
VoiceAgent.personality = relationship("VoiceAgentPersonality", back_populates="agents", uselist=False)
VoiceAgent.learning_data = relationship("VoiceAgentLearningData", back_populates="agent")