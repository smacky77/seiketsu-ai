"""Voice Intelligence Tables

Revision ID: 001_voice_intelligence
Revises: 
Create Date: 2025-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_voice_intelligence'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Voice Agent Personalities table
    op.create_table('voice_agent_personalities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('tone', sa.String(50), default='professional'),
        sa.Column('pace', sa.String(50), default='normal'),
        sa.Column('enthusiasm_level', sa.Float, default=0.7),
        sa.Column('empathy_level', sa.Float, default=0.7),
        sa.Column('formality_level', sa.Float, default=0.7),
        sa.Column('voice_pitch', sa.Float, default=0.0),
        sa.Column('voice_speed', sa.Float, default=1.0),
        sa.Column('voice_stability', sa.Float, default=0.8),
        sa.Column('interruption_tolerance', sa.Float, default=0.5),
        sa.Column('question_frequency', sa.Float, default=0.3),
        sa.Column('active_listening_cues', postgresql.JSON),
        sa.Column('real_estate_expertise_level', sa.Float, default=0.8),
        sa.Column('market_knowledge_depth', sa.Float, default=0.7),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
    )

    # Emotion Detection Logs table
    op.create_table('emotion_detection_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_turn_id', postgresql.UUID(as_uuid=True)),
        sa.Column('detected_emotion', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('valence', sa.Float, nullable=False),
        sa.Column('arousal', sa.Float, nullable=False),
        sa.Column('trigger_text', sa.Text),
        sa.Column('audio_features', postgresql.JSON),
        sa.Column('processing_time_ms', sa.Integer),
        sa.Column('response_strategy_used', sa.String(100)),
        sa.Column('tone_adjustment', sa.String(50)),
        sa.Column('pace_adjustment', sa.String(50)),
        sa.Column('detected_at', sa.DateTime, server_default=sa.text('now()')),
    )

    # Conversation Intents table
    op.create_table('conversation_intents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_turn_id', postgresql.UUID(as_uuid=True)),
        sa.Column('intent_name', sa.String(100), nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('trigger_text', sa.Text, nullable=False),
        sa.Column('extracted_entities', postgresql.JSON),
        sa.Column('intent_category', sa.String(50)),
        sa.Column('priority_level', sa.String(20), default='medium'),
        sa.Column('recommended_response', sa.Text),
        sa.Column('next_questions', postgresql.JSON),
        sa.Column('escalation_required', sa.Boolean, default=False),
        sa.Column('detected_at', sa.DateTime, server_default=sa.text('now()')),
    )

    # Objection Handling Logs table
    op.create_table('objection_handling_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('objection_type', sa.String(100), nullable=False),
        sa.Column('objection_text', sa.Text, nullable=False),
        sa.Column('objection_category', sa.String(50)),
        sa.Column('severity_level', sa.String(20)),
        sa.Column('handling_strategy', sa.String(100)),
        sa.Column('response_text', sa.Text),
        sa.Column('resolution_approach', sa.String(50)),
        sa.Column('objection_resolved', sa.Boolean, default=False),
        sa.Column('client_satisfaction', sa.Float),
        sa.Column('follow_up_required', sa.Boolean, default=False),
        sa.Column('resolution_time_seconds', sa.Integer),
        sa.Column('confidence_in_resolution', sa.Float),
        sa.Column('detected_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('resolved_at', sa.DateTime),
    )

    # Voice Quality Metrics table
    op.create_table('voice_quality_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clarity_score', sa.Float),
        sa.Column('noise_level', sa.Float),
        sa.Column('volume_consistency', sa.Float),
        sa.Column('audio_dropout_count', sa.Integer, default=0),
        sa.Column('speech_rate_wpm', sa.Float),
        sa.Column('pause_patterns', postgresql.JSON),
        sa.Column('interruption_points', postgresql.JSON),
        sa.Column('turn_taking_smoothness', sa.Float),
        sa.Column('overlap_percentage', sa.Float),
        sa.Column('silence_duration_total', sa.Float),
        sa.Column('latency_speech_to_text_ms', sa.Integer),
        sa.Column('latency_processing_ms', sa.Integer),
        sa.Column('latency_text_to_speech_ms', sa.Integer),
        sa.Column('latency_total_ms', sa.Integer),
        sa.Column('overall_quality_score', sa.Float),
        sa.Column('user_experience_rating', sa.Float),
        sa.Column('analyzed_at', sa.DateTime, server_default=sa.text('now()')),
    )

    # Conversation Flow Analytics table
    op.create_table('conversation_flow_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_stages', postgresql.JSON),
        sa.Column('stage_transitions', postgresql.JSON),
        sa.Column('qualification_progress', sa.Float),
        sa.Column('client_engagement_score', sa.Float),
        sa.Column('agent_effectiveness_score', sa.Float),
        sa.Column('conversation_momentum', sa.Float),
        sa.Column('time_to_qualification', sa.Integer),
        sa.Column('time_to_objection_handling', sa.Integer),
        sa.Column('time_to_next_steps', sa.Integer),
        sa.Column('topics_covered', postgresql.JSON),
        sa.Column('topic_depth_scores', postgresql.JSON),
        sa.Column('missing_important_topics', postgresql.JSON),
        sa.Column('likelihood_to_convert', sa.Float),
        sa.Column('recommended_follow_up_timing', sa.Integer),
        sa.Column('optimal_next_contact_method', sa.String(50)),
        sa.Column('compared_to_top_performers', sa.Float),
        sa.Column('improvement_opportunities', postgresql.JSON),
        sa.Column('analyzed_at', sa.DateTime, server_default=sa.text('now()')),
    )

    # Voice Agent Learning Data table
    op.create_table('voice_agent_learning_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('context_data', postgresql.JSON, nullable=False),
        sa.Column('outcome_data', postgresql.JSON),
        sa.Column('success_metric', sa.Float),
        sa.Column('feedback_source', sa.String(50)),
        sa.Column('feedback_details', sa.Text),
        sa.Column('applied_to_training', sa.Boolean, default=False),
        sa.Column('improvement_implemented', sa.Boolean, default=False),
        sa.Column('implementation_notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('applied_at', sa.DateTime),
    )

    # Real-time Conversation Sessions table
    op.create_table('realtime_conversation_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(100), unique=True, nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('websocket_connection_id', sa.String(100)),
        sa.Column('current_emotion', sa.String(50)),
        sa.Column('current_intent', sa.String(100)),
        sa.Column('current_confidence', sa.Float),
        sa.Column('live_transcription', sa.Text),
        sa.Column('response_times', postgresql.JSON),
        sa.Column('audio_quality_current', sa.Float),
        sa.Column('processing_queue_depth', sa.Integer, default=0),
        sa.Column('total_turns', sa.Integer, default=0),
        sa.Column('successful_interactions', sa.Integer, default=0),
        sa.Column('errors_encountered', sa.Integer, default=0),
        sa.Column('started_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('last_activity', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('ended_at', sa.DateTime),
    )

    # Create indexes for performance
    op.create_index('idx_emotion_logs_conversation', 'emotion_detection_logs', ['conversation_id'])
    op.create_index('idx_emotion_logs_detected_at', 'emotion_detection_logs', ['detected_at'])
    op.create_index('idx_intents_conversation', 'conversation_intents', ['conversation_id'])
    op.create_index('idx_intents_detected_at', 'conversation_intents', ['detected_at'])
    op.create_index('idx_objections_conversation', 'objection_handling_logs', ['conversation_id'])
    op.create_index('idx_objections_detected_at', 'objection_handling_logs', ['detected_at'])
    op.create_index('idx_quality_conversation', 'voice_quality_metrics', ['conversation_id'])
    op.create_index('idx_flow_conversation', 'conversation_flow_analytics', ['conversation_id'])
    op.create_index('idx_learning_agent', 'voice_agent_learning_data', ['agent_id'])
    op.create_index('idx_sessions_agent', 'realtime_conversation_sessions', ['agent_id'])
    op.create_index('idx_sessions_status', 'realtime_conversation_sessions', ['status'])
    op.create_index('idx_sessions_session_id', 'realtime_conversation_sessions', ['session_id'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_sessions_session_id')
    op.drop_index('idx_sessions_status')
    op.drop_index('idx_sessions_agent')
    op.drop_index('idx_learning_agent')
    op.drop_index('idx_flow_conversation')
    op.drop_index('idx_quality_conversation')
    op.drop_index('idx_objections_detected_at')
    op.drop_index('idx_objections_conversation')
    op.drop_index('idx_intents_detected_at')
    op.drop_index('idx_intents_conversation')
    op.drop_index('idx_emotion_logs_detected_at')
    op.drop_index('idx_emotion_logs_conversation')

    # Drop tables
    op.drop_table('realtime_conversation_sessions')
    op.drop_table('voice_agent_learning_data')
    op.drop_table('conversation_flow_analytics')
    op.drop_table('voice_quality_metrics')
    op.drop_table('objection_handling_logs')
    op.drop_table('conversation_intents')
    op.drop_table('emotion_detection_logs')
    op.drop_table('voice_agent_personalities')