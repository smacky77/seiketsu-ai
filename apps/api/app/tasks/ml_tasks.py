"""
Machine Learning background tasks
Model training, scoring, and optimization
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from celery import Task
import hashlib
import json

from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.twentyonedev_service import TwentyOneDevService
from app.services.analytics_service import AnalyticsService
from app.models.lead import Lead, LeadStatus
from app.models.conversation import Conversation
from app.models.organization import Organization
from app.core.cache import cache_ml_prediction, get_cached_ml_prediction

logger = logging.getLogger("seiketsu.ml_tasks")


class MLTask(Task):
    """Base task for ML operations"""
    
    def __init__(self):
        self.twentyonedev_service = TwentyOneDevService()
        self.analytics_service = AnalyticsService()


@celery_app.task(bind=True, base=MLTask)
def update_lead_scores(self):
    """Periodic task to update lead scores using ML models"""
    try:
        logger.info("Starting periodic lead score updates")
        
        async def update_scores():
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                
                # Get all active organizations
                stmt = select(Organization).where(Organization.is_active == True)
                result = await db.execute(stmt)
                organizations = result.scalars().all()
                
                total_updated = 0
                for org in organizations:
                    try:
                        # Get leads that need score updates (older than 4 hours)
                        cutoff_time = datetime.utcnow() - timedelta(hours=4)
                        leads_stmt = select(Lead).where(
                            Lead.organization_id == org.id,
                            Lead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED]),
                            Lead.updated_at < cutoff_time
                        ).limit(50)  # Limit to prevent overwhelming the system
                        
                        leads_result = await db.execute(leads_stmt)
                        leads = leads_result.scalars().all()
                        
                        for lead in leads:
                            # Schedule individual score update
                            predict_lead_conversion.apply_async(
                                args=[lead.id, org.id],
                                countdown=5  # Spread out the requests
                            )
                            total_updated += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to update scores for org {org.id}: {e}")
                        continue
                
                return total_updated
        
        import asyncio
        updated_count = asyncio.run(update_scores())
        
        logger.info(f"Scheduled score updates for {updated_count} leads")
        return {"updated_leads": updated_count}
        
    except Exception as e:
        logger.error(f"Periodic lead score update failed: {e}")
        raise


@celery_app.task(bind=True, base=MLTask)
def predict_lead_conversion(
    self,
    lead_id: str,
    organization_id: str
):
    """Predict lead conversion probability using ML"""
    try:
        async def make_prediction():
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                
                # Get lead data
                stmt = select(Lead).where(Lead.id == lead_id)
                result = await db.execute(stmt)
                lead = result.scalar_one_or_none()
                
                if not lead:
                    logger.warning(f"Lead {lead_id} not found for prediction")
                    return None
                
                # Prepare feature data
                lead_data = {
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "email": lead.email,
                    "phone": lead.phone,
                    "source": lead.source.value if lead.source else None,
                    "budget_min": lead.budget_min,
                    "budget_max": lead.budget_max,
                    "timeline": lead.timeline,
                    "property_type": lead.preferred_property_type,
                    "bedrooms": lead.preferred_bedrooms,
                    "bathrooms": lead.preferred_bathrooms,
                    "created_at": lead.created_at.isoformat(),
                    "days_since_creation": (datetime.utcnow() - lead.created_at).days
                }
                
                # Generate hash for caching
                data_hash = hashlib.md5(json.dumps(lead_data, sort_keys=True).encode()).hexdigest()
                
                # Check cache first
                cached_prediction = await get_cached_ml_prediction("lead_conversion", data_hash)
                if cached_prediction:
                    logger.debug(f"Using cached prediction for lead {lead_id}")
                    return cached_prediction
                
                # Get prediction from 21dev.ai
                prediction = await self.twentyonedev_service.predict_lead_conversion(
                    lead_data, organization_id
                )
                
                if prediction:
                    # Cache the prediction
                    await cache_ml_prediction("lead_conversion", data_hash, prediction, ttl=7200)
                    
                    # Update lead score
                    new_score = int(prediction.get("score", 0) * 100)
                    lead.lead_score = new_score
                    lead.updated_at = datetime.utcnow()
                    
                    # Update qualification status based on score
                    if new_score >= 70 and lead.status == LeadStatus.NEW:
                        lead.status = LeadStatus.QUALIFIED
                    elif new_score < 40 and lead.status in [LeadStatus.NEW, LeadStatus.CONTACTED]:
                        lead.status = LeadStatus.UNQUALIFIED
                    
                    await db.commit()
                    
                    logger.info(f"Updated lead {lead_id} score to {new_score}")
                    return {
                        "lead_id": lead_id,
                        "score": new_score,
                        "confidence": prediction.get("confidence", 0),
                        "factors": prediction.get("factors", [])
                    }
                else:
                    logger.warning(f"No prediction received for lead {lead_id}")
                    return None
        
        import asyncio
        return asyncio.run(make_prediction())
        
    except Exception as e:
        logger.error(f"Lead conversion prediction failed for {lead_id}: {e}")
        raise


@celery_app.task(bind=True, base=MLTask)
def optimize_conversation_flow(
    self,
    organization_id: str,
    voice_agent_id: str
):
    """Optimize conversation flow using ML insights"""
    try:
        async def optimize_flow():
            async with AsyncSessionLocal() as db:
                # Get recent conversations for this agent
                recent_conversations = await self._get_agent_conversations(
                    voice_agent_id, organization_id, db, days=30
                )
                
                if len(recent_conversations) < 10:
                    logger.info(f"Not enough conversation data for agent {voice_agent_id}")
                    return {"status": "insufficient_data"}
                
                # Prepare conversation data for ML analysis
                conversation_data = []
                for conv in recent_conversations:
                    conversation_data.append({
                        "duration_seconds": conv.duration_seconds,
                        "status": conv.status.value,
                        "sentiment_score": conv.sentiment_score,
                        "lead_generated": bool(conv.lead_id),
                        "transferred": conv.transferred_to_human,
                        "hour_of_day": conv.started_at.hour,
                        "day_of_week": conv.started_at.weekday()
                    })
                
                # Get optimization insights from 21dev.ai
                insights = await self.twentyonedev_service.get_conversation_insights(
                    organization_id, conversation_data, "optimization"
                )
                
                if insights:
                    # Apply optimization recommendations
                    optimizations_applied = await self._apply_conversation_optimizations(
                        voice_agent_id, insights, db
                    )
                    
                    logger.info(f"Applied {optimizations_applied} optimizations to agent {voice_agent_id}")
                    return {
                        "status": "optimized",
                        "insights": insights,
                        "optimizations_applied": optimizations_applied
                    }
                else:
                    return {"status": "no_insights"}
        
        import asyncio
        return asyncio.run(optimize_flow())
        
    except Exception as e:
        logger.error(f"Conversation flow optimization failed: {e}")
        raise


@celery_app.task(bind=True, base=MLTask)
def analyze_customer_sentiment(
    self,
    organization_id: str,
    days: int = 30
):
    """Analyze customer sentiment patterns"""
    try:
        async def analyze_sentiment():
            async with AsyncSessionLocal() as db:
                # Get conversations with sentiment data
                conversations = await self._get_conversations_with_sentiment(
                    organization_id, db, days
                )
                
                if not conversations:
                    return {"status": "no_data"}
                
                # Analyze patterns
                sentiment_patterns = {
                    "hourly_sentiment": self._analyze_hourly_sentiment(conversations),
                    "agent_sentiment": await self._analyze_agent_sentiment(conversations, db),
                    "outcome_correlation": self._analyze_sentiment_outcomes(conversations),
                    "trend_analysis": self._analyze_sentiment_trends(conversations)
                }
                
                # Get ML insights
                ml_insights = await self.twentyonedev_service.get_conversation_insights(
                    organization_id, 
                    [self._conversation_to_dict(conv) for conv in conversations],
                    "sentiment_analysis"
                )\n                \n                return {\n                    \"status\": \"completed\",\n                    \"patterns\": sentiment_patterns,\n                    \"ml_insights\": ml_insights,\n                    \"recommendations\": self._generate_sentiment_recommendations(sentiment_patterns)\n                }\n        \n        import asyncio\n        return asyncio.run(analyze_sentiment())\n        \n    except Exception as e:\n        logger.error(f\"Sentiment analysis failed: {e}\")\n        raise\n\n\n@celery_app.task(bind=True, base=MLTask)\ndef train_custom_lead_scoring_model(\n    self,\n    organization_id: str\n):\n    \"\"\"Train custom lead scoring model for organization\"\"\"\n    try:\n        async def train_model():\n            async with AsyncSessionLocal() as db:\n                # Get training data (leads with known outcomes)\n                training_data = await self._prepare_lead_training_data(organization_id, db)\n                \n                if len(training_data[\"leads\"]) < 100:\n                    logger.warning(f\"Insufficient training data for org {organization_id}\")\n                    return {\"status\": \"insufficient_data\", \"required\": 100, \"available\": len(training_data[\"leads\"])}\n                \n                # Submit training job to 21dev.ai\n                training_job = await self.twentyonedev_service.train_custom_model(\n                    organization_id, training_data, \"lead_scoring\"\n                )\n                \n                if training_job:\n                    # Track training job\n                    await self.analytics_service.track_event(\n                        \"ml\", \"model_training_started\", organization_id, db,\n                        properties={\n                            \"model_type\": \"lead_scoring\",\n                            \"job_id\": training_job.get(\"job_id\"),\n                            \"training_samples\": len(training_data[\"leads\"])\n                        }\n                    )\n                    \n                    logger.info(f\"Started lead scoring model training for org {organization_id}\")\n                    return {\"status\": \"training_started\", \"job_id\": training_job.get(\"job_id\")}\n                else:\n                    return {\"status\": \"training_failed\"}\n        \n        import asyncio\n        return asyncio.run(train_model())\n        \n    except Exception as e:\n        logger.error(f\"Model training failed: {e}\")\n        raise\n\n\n@celery_app.task(bind=True, base=MLTask)\ndef generate_predictive_insights(\n    self,\n    organization_id: str\n):\n    \"\"\"Generate predictive insights for organization\"\"\"\n    try:\n        async def generate_insights():\n            async with AsyncSessionLocal() as db:\n                # Get predictive insights\n                insights = await self.analytics_service.get_predictive_insights(\n                    organization_id, db\n                )\n                \n                if insights:\n                    # Store insights for later retrieval\n                    from app.core.cache import cache_analytics_data\n                    await cache_analytics_data(\n                        organization_id, \"predictive_insights\", insights, ttl=3600\n                    )\n                    \n                    # Track insight generation\n                    await self.analytics_service.track_event(\n                        \"ml\", \"insights_generated\", organization_id, db,\n                        properties={\"insight_types\": list(insights.keys())}\n                    )\n                    \n                    logger.info(f\"Generated predictive insights for org {organization_id}\")\n                    return {\"status\": \"completed\", \"insights\": insights}\n                else:\n                    return {\"status\": \"no_insights\"}\n        \n        import asyncio\n        return asyncio.run(generate_insights())\n        \n    except Exception as e:\n        logger.error(f\"Predictive insights generation failed: {e}\")\n        raise\n\n\n# Helper methods\nasync def _get_agent_conversations(self, agent_id: str, org_id: str, db, days: int) -> List[Conversation]:\n    \"\"\"Get conversations for specific agent\"\"\"\n    from sqlalchemy import select, and_\n    \n    start_date = datetime.utcnow() - timedelta(days=days)\n    stmt = select(Conversation).where(\n        and_(\n            Conversation.voice_agent_id == agent_id,\n            Conversation.organization_id == org_id,\n            Conversation.started_at >= start_date\n        )\n    )\n    \n    result = await db.execute(stmt)\n    return result.scalars().all()\n\n\nasync def _apply_conversation_optimizations(self, agent_id: str, insights: Dict[str, Any], db) -> int:\n    \"\"\"Apply ML-recommended optimizations\"\"\"\n    # This would update voice agent settings based on ML insights\n    # For now, return mock count\n    return len(insights.get(\"recommendations\", []))\n\n\nasync def _get_conversations_with_sentiment(self, org_id: str, db, days: int) -> List[Conversation]:\n    \"\"\"Get conversations with sentiment scores\"\"\"\n    from sqlalchemy import select, and_\n    \n    start_date = datetime.utcnow() - timedelta(days=days)\n    stmt = select(Conversation).where(\n        and_(\n            Conversation.organization_id == org_id,\n            Conversation.started_at >= start_date,\n            Conversation.sentiment_score.isnot(None)\n        )\n    )\n    \n    result = await db.execute(stmt)\n    return result.scalars().all()\n\n\ndef _analyze_hourly_sentiment(self, conversations: List[Conversation]) -> Dict[int, float]:\n    \"\"\"Analyze sentiment by hour of day\"\"\"\n    hourly_sentiment = {}\n    hourly_counts = {}\n    \n    for conv in conversations:\n        hour = conv.started_at.hour\n        if hour not in hourly_sentiment:\n            hourly_sentiment[hour] = 0.0\n            hourly_counts[hour] = 0\n        \n        hourly_sentiment[hour] += conv.sentiment_score\n        hourly_counts[hour] += 1\n    \n    # Calculate averages\n    for hour in hourly_sentiment:\n        if hourly_counts[hour] > 0:\n            hourly_sentiment[hour] = hourly_sentiment[hour] / hourly_counts[hour]\n    \n    return hourly_sentiment\n\n\nasync def _analyze_agent_sentiment(self, conversations: List[Conversation], db) -> Dict[str, Dict[str, float]]:\n    \"\"\"Analyze sentiment by voice agent\"\"\"\n    agent_sentiment = {}\n    \n    for conv in conversations:\n        agent_id = conv.voice_agent_id\n        if agent_id not in agent_sentiment:\n            agent_sentiment[agent_id] = {\"total\": 0.0, \"count\": 0, \"average\": 0.0}\n        \n        agent_sentiment[agent_id][\"total\"] += conv.sentiment_score\n        agent_sentiment[agent_id][\"count\"] += 1\n    \n    # Calculate averages\n    for agent_id in agent_sentiment:\n        count = agent_sentiment[agent_id][\"count\"]\n        if count > 0:\n            agent_sentiment[agent_id][\"average\"] = agent_sentiment[agent_id][\"total\"] / count\n    \n    return agent_sentiment\n\n\ndef _analyze_sentiment_outcomes(self, conversations: List[Conversation]) -> Dict[str, Any]:\n    \"\"\"Analyze correlation between sentiment and outcomes\"\"\"\n    positive_leads = 0\n    negative_leads = 0\n    positive_total = 0\n    negative_total = 0\n    \n    for conv in conversations:\n        if conv.sentiment_score > 0.1:  # Positive sentiment\n            positive_total += 1\n            if conv.lead_id:\n                positive_leads += 1\n        elif conv.sentiment_score < -0.1:  # Negative sentiment\n            negative_total += 1\n            if conv.lead_id:\n                negative_leads += 1\n    \n    return {\n        \"positive_conversion_rate\": (positive_leads / positive_total * 100) if positive_total > 0 else 0,\n        \"negative_conversion_rate\": (negative_leads / negative_total * 100) if negative_total > 0 else 0,\n        \"positive_conversations\": positive_total,\n        \"negative_conversations\": negative_total\n    }\n\n\ndef _analyze_sentiment_trends(self, conversations: List[Conversation]) -> Dict[str, Any]:\n    \"\"\"Analyze sentiment trends over time\"\"\"\n    # Group by day and calculate average sentiment\n    daily_sentiment = {}\n    daily_counts = {}\n    \n    for conv in conversations:\n        date_key = conv.started_at.date().isoformat()\n        if date_key not in daily_sentiment:\n            daily_sentiment[date_key] = 0.0\n            daily_counts[date_key] = 0\n        \n        daily_sentiment[date_key] += conv.sentiment_score\n        daily_counts[date_key] += 1\n    \n    # Calculate daily averages\n    for date_key in daily_sentiment:\n        if daily_counts[date_key] > 0:\n            daily_sentiment[date_key] = daily_sentiment[date_key] / daily_counts[date_key]\n    \n    # Calculate trend (simple linear trend)\n    dates = sorted(daily_sentiment.keys())\n    if len(dates) >= 2:\n        first_week_avg = sum(daily_sentiment[date] for date in dates[:7]) / min(7, len(dates))\n        last_week_avg = sum(daily_sentiment[date] for date in dates[-7:]) / min(7, len(dates[-7:]))\n        trend = \"improving\" if last_week_avg > first_week_avg else \"declining\"\n    else:\n        trend = \"stable\"\n    \n    return {\n        \"daily_averages\": daily_sentiment,\n        \"trend\": trend,\n        \"overall_average\": sum(daily_sentiment.values()) / len(daily_sentiment) if daily_sentiment else 0\n    }\n\n\ndef _conversation_to_dict(self, conv: Conversation) -> Dict[str, Any]:\n    \"\"\"Convert conversation to dictionary for ML processing\"\"\"\n    return {\n        \"duration_seconds\": conv.duration_seconds,\n        \"sentiment_score\": conv.sentiment_score,\n        \"status\": conv.status.value,\n        \"lead_generated\": bool(conv.lead_id),\n        \"transferred\": conv.transferred_to_human,\n        \"hour_of_day\": conv.started_at.hour,\n        \"day_of_week\": conv.started_at.weekday()\n    }\n\n\ndef _generate_sentiment_recommendations(self, patterns: Dict[str, Any]) -> List[str]:\n    \"\"\"Generate recommendations based on sentiment patterns\"\"\"\n    recommendations = []\n    \n    # Analyze hourly patterns\n    hourly = patterns.get(\"hourly_sentiment\", {})\n    if hourly:\n        worst_hours = sorted(hourly.items(), key=lambda x: x[1])[:3]\n        if worst_hours and worst_hours[0][1] < -0.2:\n            recommendations.append(f\"Consider additional training for agents working during hour {worst_hours[0][0]}\")\n    \n    # Analyze conversion correlation\n    outcomes = patterns.get(\"outcome_correlation\", {})\n    positive_rate = outcomes.get(\"positive_conversion_rate\", 0)\n    negative_rate = outcomes.get(\"negative_conversion_rate\", 0)\n    \n    if positive_rate > negative_rate * 2:\n        recommendations.append(\"Focus on maintaining positive conversation tone to improve conversion rates\")\n    \n    # Analyze trends\n    trend = patterns.get(\"trend_analysis\", {}).get(\"trend\")\n    if trend == \"declining\":\n        recommendations.append(\"Customer sentiment is declining - review recent conversation quality\")\n    \n    return recommendations[:5]  # Return top 5 recommendations\n\n\nasync def _prepare_lead_training_data(self, organization_id: str, db) -> Dict[str, Any]:\n    \"\"\"Prepare training data for lead scoring model\"\"\"\n    from sqlalchemy import select, and_\n    \n    # Get leads with known outcomes (closed won/lost)\n    stmt = select(Lead).where(\n        and_(\n            Lead.organization_id == organization_id,\n            Lead.status.in_([LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST])\n        )\n    ).limit(1000)  # Limit for performance\n    \n    result = await db.execute(stmt)\n    leads = result.scalars().all()\n    \n    training_samples = []\n    for lead in leads:\n        sample = {\n            \"features\": {\n                \"source\": lead.source.value if lead.source else \"unknown\",\n                \"budget_min\": lead.budget_min or 0,\n                \"budget_max\": lead.budget_max or 0,\n                \"timeline\": lead.timeline or \"unknown\",\n                \"property_type\": lead.preferred_property_type or \"unknown\",\n                \"bedrooms\": lead.preferred_bedrooms or 0,\n                \"bathrooms\": lead.preferred_bathrooms or 0,\n                \"has_email\": bool(lead.email),\n                \"days_to_close\": (lead.updated_at - lead.created_at).days\n            },\n            \"label\": 1 if lead.status == LeadStatus.CLOSED_WON else 0\n        }\n        training_samples.append(sample)\n    \n    return {\n        \"leads\": training_samples,\n        \"organization_id\": organization_id,\n        \"created_at\": datetime.utcnow().isoformat()\n    }