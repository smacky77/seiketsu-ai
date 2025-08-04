"""
Conversation management service
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.conversation import Conversation, ConversationMessage, ConversationStatus, ConversationOutcome, MessageType, MessageDirection
from app.models.voice_agent import VoiceAgent
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger("seiketsu.conversation_service")


class ConversationService:
    """Service for managing voice conversations"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    async def create_conversation(
        self,
        caller_phone: str,
        voice_agent_id: str,
        organization_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            caller_phone=caller_phone,
            voice_agent_id=voice_agent_id,
            organization_id=organization_id,
            status=ConversationStatus.INITIATED,
            call_id=f"call_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{caller_phone[-4:]}",
            session_id=f"session_{datetime.utcnow().timestamp()}",
            started_at=datetime.utcnow()
        )
        
        # Add metadata if provided
        if metadata:
            conversation.caller_name = metadata.get("caller_name")
            conversation.caller_email = metadata.get("caller_email")
            conversation.created_by_user_id = metadata.get("created_by_user_id")
        
        return conversation
    
    async def get_conversation(
        self,
        conversation_id: str,
        db: AsyncSession
    ) -> Optional[Conversation]:
        """Get conversation by ID"""
        try:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None
    
    async def get_conversations_for_organization(
        self,
        organization_id: str,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[ConversationStatus] = None
    ) -> List[Conversation]:
        """Get conversations for organization"""
        try:
            conditions = [Conversation.organization_id == organization_id]
            
            if status_filter:
                conditions.append(Conversation.status == status_filter)
            
            stmt = (
                select(Conversation)
                .where(and_(*conditions))
                .order_by(desc(Conversation.started_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get conversations for org {organization_id}: {e}")
            return []
    
    async def end_conversation(
        self,
        conversation_id: str,
        outcome: str,
        outcome_details: Optional[Dict[str, Any]] = None
    ) -> Optional[Conversation]:
        """End a conversation with specified outcome"""
        # This would typically be called with a database session
        # For now, return a mock conversation
        conversation = Conversation(
            id=conversation_id,
            status=ConversationStatus.COMPLETED,
            ended_at=datetime.utcnow()
        )
        
        # Set outcome
        if outcome == "lead_qualified":
            conversation.outcome = ConversationOutcome.LEAD_QUALIFIED
        elif outcome == "appointment_scheduled":
            conversation.outcome = ConversationOutcome.APPOINTMENT_SCHEDULED
        elif outcome == "transferred":
            conversation.outcome = ConversationOutcome.TRANSFERRED_TO_HUMAN
        else:
            conversation.outcome = ConversationOutcome.COMPLETED
        
        if outcome_details:
            conversation.outcome_details = outcome_details
        
        # Calculate duration
        if conversation.started_at:
            conversation.duration_seconds = int((conversation.ended_at - conversation.started_at).total_seconds())
        
        return conversation
    
    async def transfer_to_human(
        self,
        conversation_id: str,
        reason: str,
        target_agent: Optional[str] = None
    ) -> Optional[Conversation]:
        """Transfer conversation to human agent"""
        # Mock implementation - would update database
        conversation = Conversation(
            id=conversation_id,
            status=ConversationStatus.TRANSFERRED,
            transferred_to_human=True,
            transfer_reason=reason,
            human_agent_name=target_agent,
            transfer_timestamp=datetime.utcnow()
        )
        
        return conversation
    
    async def add_message(
        self,
        conversation_id: str,
        message_type: MessageType,
        direction: MessageDirection,
        content: str,
        db: AsyncSession,
        speaker_name: Optional[str] = None,
        audio_url: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ) -> ConversationMessage:
        """Add message to conversation"""
        try:
            # Get message sequence number
            stmt = select(ConversationMessage).where(
                ConversationMessage.conversation_id == conversation_id
            ).order_by(desc(ConversationMessage.sequence_number))
            
            result = await db.execute(stmt)
            last_message = result.scalar_one_or_none()
            sequence_number = (last_message.sequence_number + 1) if last_message else 1
            
            message = ConversationMessage(
                conversation_id=conversation_id,
                message_type=message_type,
                direction=direction,
                content=content,
                speaker_name=speaker_name,
                sequence_number=sequence_number,
                audio_url=audio_url,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.utcnow()
            )
            
            db.add(message)
            await db.commit()
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            raise
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        db: AsyncSession,
        limit: int = 100
    ) -> List[ConversationMessage]:
        """Get messages for conversation"""
        try:
            stmt = (
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == conversation_id)
                .order_by(ConversationMessage.sequence_number)
                .limit(limit)
            )
            
            result = await db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            return []
    
    async def get_conversation_transcript(
        self,
        conversation_id: str,
        db: AsyncSession
    ) -> str:
        """Get formatted transcript for conversation"""
        messages = await self.get_conversation_messages(conversation_id, db)
        
        transcript_lines = []
        for message in messages:
            if message.message_type in [MessageType.USER_SPEECH, MessageType.AGENT_SPEECH]:
                transcript_lines.append(message.to_transcript_format())
        
        return "\n".join(transcript_lines)
    
    async def update_conversation_sentiment(
        self,
        conversation_id: str,
        sentiment_score: float,
        db: AsyncSession
    ):
        """Update conversation sentiment score"""
        try:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await db.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                conversation.sentiment_score = sentiment_score
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to update sentiment for conversation {conversation_id}: {e}")
    
    async def get_conversation_analytics(
        self,
        organization_id: str,
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get conversation analytics for organization"""
        try:
            from datetime import timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get conversations in date range
            stmt = select(Conversation).where(
                and_(
                    Conversation.organization_id == organization_id,
                    Conversation.started_at >= start_date
                )
            )
            
            result = await db.execute(stmt)
            conversations = result.scalars().all()
            
            # Calculate metrics
            total_conversations = len(conversations)
            completed_conversations = len([c for c in conversations if c.status == ConversationStatus.COMPLETED])
            leads_generated = len([c for c in conversations if c.lead_id])
            transferred_conversations = len([c for c in conversations if c.transferred_to_human])
            
            avg_duration = 0
            if conversations:
                durations = [c.duration_seconds for c in conversations if c.duration_seconds]
                if durations:
                    avg_duration = sum(durations) / len(durations)
            
            # Conversion rates
            completion_rate = (completed_conversations / total_conversations * 100) if total_conversations > 0 else 0
            lead_conversion_rate = (leads_generated / total_conversations * 100) if total_conversations > 0 else 0
            transfer_rate = (transferred_conversations / total_conversations * 100) if total_conversations > 0 else 0
            
            return {
                "total_conversations": total_conversations,
                "completed_conversations": completed_conversations,
                "leads_generated": leads_generated,
                "transferred_conversations": transferred_conversations,
                "average_duration_seconds": avg_duration,
                "completion_rate_percent": round(completion_rate, 2),
                "lead_conversion_rate_percent": round(lead_conversion_rate, 2),
                "transfer_rate_percent": round(transfer_rate, 2),
                "date_range_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation analytics: {e}")
            return {
                "total_conversations": 0,
                "completed_conversations": 0,
                "leads_generated": 0,
                "transferred_conversations": 0,
                "average_duration_seconds": 0,
                "completion_rate_percent": 0,
                "lead_conversion_rate_percent": 0,
                "transfer_rate_percent": 0,
                "date_range_days": days
            }