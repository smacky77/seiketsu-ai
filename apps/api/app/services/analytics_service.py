"""
Advanced Analytics Service with 21dev.ai Integration
Real-time metrics, ML insights, and performance optimization
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
import httpx
import asyncio
import json

from app.models.analytics import AnalyticsEvent
from app.models.conversation import Conversation, ConversationStatus
from app.models.lead import Lead, LeadStatus
from app.models.voice_agent import VoiceAgent
from app.core.config import settings
from app.core.cache import cache_result, get_cached_result

logger = logging.getLogger("seiketsu.analytics_service")


class AnalyticsService:
    """Advanced analytics service with 21dev.ai integration for ML insights"""
    
    def __init__(self):
        self.twentyonedev_client = None
        if settings.TWENTYONEDEV_API_KEY:
            self.twentyonedev_client = httpx.AsyncClient(
                base_url=settings.TWENTYONEDEV_BASE_URL,
                headers={
                    "Authorization": f"Bearer {settings.TWENTYONEDEV_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=settings.TWENTYONEDEV_TIMEOUT
            )
    
    async def track_event(
        self,
        event_type: str,
        event_name: str,
        organization_id: str,
        db: AsyncSession,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        voice_agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Track an analytics event"""
        try:
            event = AnalyticsEvent(
                event_type=event_type,
                event_name=event_name,
                organization_id=organization_id,
                user_id=user_id,
                conversation_id=conversation_id,
                voice_agent_id=voice_agent_id,
                session_id=session_id,
                properties=properties or {},
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow()
            )
            
            db.add(event)
            await db.commit()
            
            logger.debug(f"Tracked event: {event_type}.{event_name} for org {organization_id}")
            
        except Exception as e:
            logger.error(f"Failed to track event {event_type}.{event_name}: {e}")
    
    async def get_conversation_metrics(
        self,
        organization_id: str,
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get conversation metrics for organization"""
        try:
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
            active_conversations = len([c for c in conversations if c.is_active])
            completed_conversations = len([c for c in conversations if c.status == ConversationStatus.COMPLETED])
            transferred_conversations = len([c for c in conversations if c.transferred_to_human])
            
            # Duration metrics
            durations = [c.duration_seconds for c in conversations if c.duration_seconds and c.duration_seconds > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Lead generation
            leads_generated = len([c for c in conversations if c.lead_id])
            
            # Sentiment analysis
            sentiment_scores = [c.sentiment_score for c in conversations if c.sentiment_score is not None]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            # Daily breakdown
            daily_counts = {}
            for conversation in conversations:
                date_key = conversation.started_at.date().isoformat()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            
            return {
                "total_conversations": total_conversations,
                "active_conversations": active_conversations,
                "completed_conversations": completed_conversations,
                "transferred_conversations": transferred_conversations,
                "leads_generated": leads_generated,
                "average_duration_seconds": round(avg_duration, 2),
                "average_duration_minutes": round(avg_duration / 60, 2),
                "average_sentiment_score": round(avg_sentiment, 3),
                "completion_rate": round((completed_conversations / total_conversations * 100), 2) if total_conversations > 0 else 0,
                "lead_conversion_rate": round((leads_generated / total_conversations * 100), 2) if total_conversations > 0 else 0,
                "transfer_rate": round((transferred_conversations / total_conversations * 100), 2) if total_conversations > 0 else 0,
                "daily_conversation_counts": daily_counts,
                "date_range_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation metrics: {e}")
            return self._empty_conversation_metrics(days)
    
    async def get_lead_metrics(
        self,
        organization_id: str,
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get lead metrics for organization"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get leads in date range
            stmt = select(Lead).where(
                and_(
                    Lead.organization_id == organization_id,
                    Lead.created_at >= start_date
                )
            )
            
            result = await db.execute(stmt)
            leads = result.scalars().all()
            
            total_leads = len(leads)
            
            # Status breakdown
            status_counts = {}
            for status in LeadStatus:
                status_counts[status.value] = len([l for l in leads if l.status == status])
            
            # Lead scores
            lead_scores = [l.lead_score for l in leads if l.lead_score is not None]
            avg_lead_score = sum(lead_scores) / len(lead_scores) if lead_scores else 0
            
            # High-quality leads (score >= 75)
            high_quality_leads = len([l for l in leads if l.lead_score and l.lead_score >= 75])
            
            # Source breakdown
            from collections import Counter
            source_counts = Counter([l.source.value if l.source else 'unknown' for l in leads])
            
            # Daily breakdown
            daily_counts = {}
            for lead in leads:
                date_key = lead.created_at.date().isoformat()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            
            return {
                "total_leads": total_leads,
                "status_breakdown": status_counts,
                "average_lead_score": round(avg_lead_score, 2),
                "high_quality_leads": high_quality_leads,
                "high_quality_rate": round((high_quality_leads / total_leads * 100), 2) if total_leads > 0 else 0,
                "source_breakdown": dict(source_counts),
                "daily_lead_counts": daily_counts,
                "date_range_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get lead metrics: {e}")
            return self._empty_lead_metrics(days)
    
    async def get_voice_agent_performance(
        self,
        organization_id: str,
        db: AsyncSession,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance metrics for all voice agents"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get voice agents for organization
            agents_stmt = select(VoiceAgent).where(VoiceAgent.organization_id == organization_id)
            agents_result = await db.execute(agents_stmt)
            agents = agents_result.scalars().all()
            
            agent_metrics = []
            
            for agent in agents:
                # Get conversations for this agent in date range
                conv_stmt = select(Conversation).where(
                    and_(
                        Conversation.voice_agent_id == agent.id,
                        Conversation.started_at >= start_date
                    )
                )
                
                conv_result = await db.execute(conv_stmt)
                conversations = conv_result.scalars().all()
                
                total_conversations = len(conversations)
                completed_conversations = len([c for c in conversations if c.status == ConversationStatus.COMPLETED])
                leads_generated = len([c for c in conversations if c.lead_id])
                
                # Duration metrics
                durations = [c.duration_seconds for c in conversations if c.duration_seconds]
                avg_duration = sum(durations) / len(durations) if durations else 0
                
                # Sentiment metrics
                sentiments = [c.sentiment_score for c in conversations if c.sentiment_score is not None]
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                
                agent_metrics.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "agent_type": agent.type.value,
                    "total_conversations": total_conversations,
                    "completed_conversations": completed_conversations,
                    "leads_generated": leads_generated,
                    "average_duration_seconds": round(avg_duration, 2),
                    "average_sentiment_score": round(avg_sentiment, 3),
                    "completion_rate": round((completed_conversations / total_conversations * 100), 2) if total_conversations > 0 else 0,
                    "lead_conversion_rate": round((leads_generated / total_conversations * 100), 2) if total_conversations > 0 else 0,
                    "phone_number": agent.phone_number,
                    "status": agent.status.value
                })
            
            # Sort by total conversations descending
            agent_metrics.sort(key=lambda x: x["total_conversations"], reverse=True)
            
            return agent_metrics
            
        except Exception as e:
            logger.error(f"Failed to get voice agent performance: {e}")
            return []
    
    async def get_real_time_dashboard(
        self,
        organization_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get real-time dashboard metrics"""
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Today's conversations
            today_conversations_stmt = select(Conversation).where(
                and_(
                    Conversation.organization_id == organization_id,
                    Conversation.started_at >= today_start
                )
            )
            
            today_result = await db.execute(today_conversations_stmt)
            today_conversations = today_result.scalars().all()
            
            # Active conversations
            active_conversations = len([c for c in today_conversations if c.is_active])
            
            # Today's leads
            today_leads_stmt = select(Lead).where(
                and_(
                    Lead.organization_id == organization_id,
                    Lead.created_at >= today_start
                )
            )
            
            today_leads_result = await db.execute(today_leads_stmt)
            today_leads = today_leads_result.scalars().all()
            
            # Recent activity (last 24 hours)
            last_24h = now - timedelta(hours=24)
            
            recent_events_stmt = (
                select(AnalyticsEvent)
                .where(
                    and_(
                        AnalyticsEvent.organization_id == organization_id,
                        AnalyticsEvent.timestamp >= last_24h
                    )
                )
                .order_by(desc(AnalyticsEvent.timestamp))
                .limit(10)
            )
            
            recent_events_result = await db.execute(recent_events_stmt)
            recent_events = recent_events_result.scalars().all()
            
            return {
                "active_conversations": active_conversations,
                "today_total_conversations": len(today_conversations),
                "today_completed_conversations": len([c for c in today_conversations if c.status == ConversationStatus.COMPLETED]),
                "today_leads_generated": len(today_leads),
                "recent_activity": [
                    {
                        "event_type": event.event_type,
                        "event_name": event.event_name,
                        "timestamp": event.timestamp.isoformat(),
                        "properties": event.properties
                    }
                    for event in recent_events
                ],
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time dashboard: {e}")
            return {
                "active_conversations": 0,
                "today_total_conversations": 0,
                "today_completed_conversations": 0,
                "today_leads_generated": 0,
                "recent_activity": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _empty_conversation_metrics(self, days: int) -> Dict[str, Any]:
        """Return empty conversation metrics structure"""
        return {
            "total_conversations": 0,
            "active_conversations": 0,
            "completed_conversations": 0,
            "transferred_conversations": 0,
            "leads_generated": 0,
            "average_duration_seconds": 0,
            "average_duration_minutes": 0,
            "average_sentiment_score": 0,
            "completion_rate": 0,
            "lead_conversion_rate": 0,
            "transfer_rate": 0,
            "daily_conversation_counts": {},
            "date_range_days": days
        }
    
    def _empty_lead_metrics(self, days: int) -> Dict[str, Any]:
        """Return empty lead metrics structure"""
        return {
            "total_leads": 0,
            "status_breakdown": {},
            "average_lead_score": 0,
            "high_quality_leads": 0,
            "high_quality_rate": 0,
            "source_breakdown": {},
            "daily_lead_counts": {},
            "date_range_days": days
        }