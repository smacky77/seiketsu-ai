"""
Lead management background tasks
Follow-up reminders, scoring updates, and automated actions
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from celery import Task

from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.lead_service import LeadService
from app.services.analytics_service import AnalyticsService
from app.services.twentyonedev_service import TwentyOneDevService
from app.models.lead import Lead, LeadStatus

logger = logging.getLogger("seiketsu.lead_tasks")


class LeadTask(Task):
    """Base task for lead operations"""
    
    def __init__(self):
        self.lead_service = LeadService()
        self.analytics_service = AnalyticsService()
        self.twentyonedev_service = TwentyOneDevService()


@celery_app.task(bind=True, base=LeadTask)
def schedule_follow_up_reminder(
    self,
    lead_id: str,
    follow_up_date: datetime
):
    """Schedule a follow-up reminder for a lead"""
    try:
        logger.info(f"Scheduling follow-up reminder for lead {lead_id} at {follow_up_date}")
        
        # Calculate delay until follow-up time
        delay_seconds = (follow_up_date - datetime.utcnow()).total_seconds()
        
        if delay_seconds > 0:
            # Schedule the actual reminder task
            send_follow_up_reminder.apply_async(
                args=[lead_id],
                countdown=delay_seconds
            )
            
            logger.info(f"Follow-up reminder scheduled for lead {lead_id} in {delay_seconds} seconds")
            return {"status": "scheduled", "delay_seconds": delay_seconds}
        else:
            # Send immediately if time has passed
            send_follow_up_reminder.apply_async(args=[lead_id])
            return {"status": "sent_immediately"}
            
    except Exception as e:
        logger.error(f"Failed to schedule follow-up reminder for lead {lead_id}: {e}")
        raise


@celery_app.task(bind=True, base=LeadTask)
def send_follow_up_reminder(
    self,
    lead_id: str
):
    """Send follow-up reminder for a lead"""
    try:
        logger.info(f"Sending follow-up reminder for lead {lead_id}")
        
        async def send_reminder():
            async with AsyncSessionLocal() as db:
                # Get lead details
                lead = await self.lead_service.get_lead(lead_id, db)
                if not lead:
                    logger.warning(f"Lead {lead_id} not found for follow-up reminder")
                    return {"status": "lead_not_found"}
                
                # Check if lead still needs follow-up
                if lead.status in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST, LeadStatus.DELETED]:
                    logger.info(f"Lead {lead_id} is closed, skipping follow-up reminder")
                    return {"status": "skipped_closed_lead"}
                
                # Add follow-up note
                await self.lead_service.add_lead_note(
                    lead_id,
                    "Automated follow-up reminder: This lead needs attention",
                    db,
                    user_id="system"
                )
                
                # Track analytics event
                await self.analytics_service.track_event(
                    "leads", "follow_up_reminder_sent", lead.organization_id, db,
                    properties={"lead_id": lead_id, "automated": True}
                )
                
                # TODO: Send notification to assigned agent
                # This could be email, Slack, or in-app notification
                
                logger.info(f"Follow-up reminder sent for lead {lead_id}")
                return {"status": "sent", "lead_id": lead_id}
        
        import asyncio
        return asyncio.run(send_reminder())
        
    except Exception as e:
        logger.error(f"Failed to send follow-up reminder for lead {lead_id}: {e}")
        raise


@celery_app.task(base=LeadTask)
def process_follow_up_reminders():
    """Process all pending follow-up reminders"""
    try:
        logger.info("Processing follow-up reminders")
        
        async def process_reminders():
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select, and_
                
                # Get leads that need follow-up
                now = datetime.utcnow()
                stmt = select(Lead).where(
                    and_(
                        Lead.next_follow_up_date <= now,
                        Lead.status.in_([
                            LeadStatus.NEW, 
                            LeadStatus.CONTACTED, 
                            LeadStatus.QUALIFIED,
                            LeadStatus.INTERESTED
                        ])
                    )
                )
                
                result = await db.execute(stmt)
                leads_needing_followup = result.scalars().all()
                
                reminder_count = 0
                for lead in leads_needing_followup:
                    try:
                        # Send reminder
                        send_follow_up_reminder.apply_async(args=[lead.id])
                        
                        # Update next follow-up date (add 24 hours)
                        lead.next_follow_up_date = now + timedelta(hours=24)
                        reminder_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to process follow-up for lead {lead.id}: {e}")
                        continue
                
                if reminder_count > 0:
                    await db.commit()
                
                logger.info(f"Processed {reminder_count} follow-up reminders")
                return {"processed_reminders": reminder_count}
        
        import asyncio
        return asyncio.run(process_reminders())
        
    except Exception as e:
        logger.error(f"Failed to process follow-up reminders: {e}")
        raise


@celery_app.task(bind=True, base=LeadTask)
def update_lead_score(
    self,
    lead_id: str,
    additional_data: Optional[Dict[str, Any]] = None
):
    """Update lead score using ML model"""
    try:
        logger.info(f"Updating lead score for lead {lead_id}")
        
        async def update_score():
            async with AsyncSessionLocal() as db:
                lead = await self.lead_service.get_lead(lead_id, db)
                if not lead:
                    return {"status": "lead_not_found"}
                
                # Prepare lead data for ML scoring
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
                    "current_score": lead.lead_score
                }
                
                # Add additional data if provided
                if additional_data:
                    lead_data.update(additional_data)\n                \n                # Get ML prediction from 21dev.ai\n                prediction = await self.twentyonedev_service.predict_lead_conversion(\n                    lead_data, lead.organization_id\n                )\n                \n                if prediction and \"score\" in prediction:\n                    old_score = lead.lead_score\n                    new_score = int(prediction[\"score\"] * 100)  # Convert to 0-100 scale\n                    \n                    lead.lead_score = new_score\n                    lead.updated_at = datetime.utcnow()\n                    \n                    # Update qualification status if score changed significantly\n                    if new_score >= 70 and (not old_score or old_score < 70):\n                        lead.status = LeadStatus.QUALIFIED\n                    elif new_score < 50 and old_score and old_score >= 50:\n                        lead.status = LeadStatus.UNQUALIFIED\n                    \n                    await db.commit()\n                    \n                    # Track score update\n                    await self.analytics_service.track_event(\n                        \"leads\", \"score_updated\", lead.organization_id, db,\n                        properties={\n                            \"lead_id\": lead_id,\n                            \"old_score\": old_score,\n                            \"new_score\": new_score,\n                            \"ml_powered\": True\n                        }\n                    )\n                    \n                    logger.info(f\"Updated lead {lead_id} score from {old_score} to {new_score}\")\n                    return {\"status\": \"updated\", \"old_score\": old_score, \"new_score\": new_score}\n                else:\n                    # Fallback to rule-based scoring\n                    lead.update_lead_score()\n                    await db.commit()\n                    \n                    logger.info(f\"Updated lead {lead_id} score using rule-based method\")\n                    return {\"status\": \"updated_fallback\", \"score\": lead.lead_score}\n        \n        import asyncio\n        return asyncio.run(update_score())\n        \n    except Exception as e:\n        logger.error(f\"Failed to update lead score for {lead_id}: {e}\")\n        raise\n\n\n@celery_app.task(bind=True, base=LeadTask)\ndef bulk_update_lead_scores(\n    self,\n    organization_id: str,\n    lead_ids: Optional[List[str]] = None\n):\n    \"\"\"Bulk update lead scores for an organization\"\"\"\n    try:\n        logger.info(f\"Bulk updating lead scores for organization {organization_id}\")\n        \n        async def bulk_update():\n            async with AsyncSessionLocal() as db:\n                from sqlalchemy import select, and_\n                \n                # Get leads to update\n                if lead_ids:\n                    stmt = select(Lead).where(\n                        and_(\n                            Lead.organization_id == organization_id,\n                            Lead.id.in_(lead_ids)\n                        )\n                    )\n                else:\n                    # Update all active leads\n                    stmt = select(Lead).where(\n                        and_(\n                            Lead.organization_id == organization_id,\n                            Lead.status.in_([\n                                LeadStatus.NEW,\n                                LeadStatus.CONTACTED,\n                                LeadStatus.QUALIFIED,\n                                LeadStatus.INTERESTED\n                            ])\n                        )\n                    )\n                \n                result = await db.execute(stmt)\n                leads = result.scalars().all()\n                \n                updated_count = 0\n                for lead in leads:\n                    try:\n                        # Schedule individual score update\n                        update_lead_score.apply_async(args=[lead.id])\n                        updated_count += 1\n                    except Exception as e:\n                        logger.error(f\"Failed to schedule score update for lead {lead.id}: {e}\")\n                        continue\n                \n                logger.info(f\"Scheduled score updates for {updated_count} leads\")\n                return {\"scheduled_updates\": updated_count}\n        \n        import asyncio\n        return asyncio.run(bulk_update())\n        \n    except Exception as e:\n        logger.error(f\"Failed to bulk update lead scores: {e}\")\n        raise\n\n\n@celery_app.task(bind=True, base=LeadTask)\ndef auto_qualify_leads(\n    self,\n    organization_id: str\n):\n    \"\"\"Automatically qualify leads based on ML predictions\"\"\"\n    try:\n        logger.info(f\"Auto-qualifying leads for organization {organization_id}\")\n        \n        async def auto_qualify():\n            async with AsyncSessionLocal() as db:\n                from sqlalchemy import select, and_\n                \n                # Get new leads that haven't been scored recently\n                cutoff_time = datetime.utcnow() - timedelta(hours=1)\n                stmt = select(Lead).where(\n                    and_(\n                        Lead.organization_id == organization_id,\n                        Lead.status == LeadStatus.NEW,\n                        Lead.updated_at < cutoff_time\n                    )\n                )\n                \n                result = await db.execute(stmt)\n                new_leads = result.scalars().all()\n                \n                qualified_count = 0\n                for lead in new_leads:\n                    try:\n                        # Update lead score\n                        update_result = await self.update_lead_score(lead.id)\n                        \n                        if update_result.get(\"new_score\", 0) >= 70:\n                            # Auto-qualify high-scoring leads\n                            await self.lead_service.update_lead_status(\n                                lead.id,\n                                LeadStatus.QUALIFIED,\n                                db,\n                                \"Auto-qualified based on ML scoring\",\n                                \"system\"\n                            )\n                            qualified_count += 1\n                        \n                    except Exception as e:\n                        logger.error(f\"Failed to auto-qualify lead {lead.id}: {e}\")\n                        continue\n                \n                logger.info(f\"Auto-qualified {qualified_count} leads\")\n                return {\"qualified_leads\": qualified_count}\n        \n        import asyncio\n        return asyncio.run(auto_qualify())\n        \n    except Exception as e:\n        logger.error(f\"Failed to auto-qualify leads: {e}\")\n        raise\n\n\n@celery_app.task(bind=True, base=LeadTask)\ndef cleanup_stale_leads(\n    self,\n    organization_id: str,\n    days_threshold: int = 90\n):\n    \"\"\"Clean up stale leads that haven't been updated\"\"\"\n    try:\n        logger.info(f\"Cleaning up stale leads for organization {organization_id}\")\n        \n        async def cleanup_leads():\n            async with AsyncSessionLocal() as db:\n                from sqlalchemy import select, and_\n                \n                # Get stale leads\n                cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)\n                stmt = select(Lead).where(\n                    and_(\n                        Lead.organization_id == organization_id,\n                        Lead.updated_at < cutoff_date,\n                        Lead.status.in_([\n                            LeadStatus.NEW,\n                            LeadStatus.CONTACTED,\n                            LeadStatus.UNQUALIFIED\n                        ])\n                    )\n                )\n                \n                result = await db.execute(stmt)\n                stale_leads = result.scalars().all()\n                \n                cleaned_count = 0\n                for lead in stale_leads:\n                    try:\n                        # Mark as stale/archived\n                        await self.lead_service.update_lead_status(\n                            lead.id,\n                            LeadStatus.ARCHIVED,\n                            db,\n                            f\"Auto-archived after {days_threshold} days of inactivity\",\n                            \"system\"\n                        )\n                        cleaned_count += 1\n                        \n                    except Exception as e:\n                        logger.error(f\"Failed to archive stale lead {lead.id}: {e}\")\n                        continue\n                \n                logger.info(f\"Archived {cleaned_count} stale leads\")\n                return {\"archived_leads\": cleaned_count}\n        \n        import asyncio\n        return asyncio.run(cleanup_leads())\n        \n    except Exception as e:\n        logger.error(f\"Failed to cleanup stale leads: {e}\")\n        raise\n\n\n@celery_app.task(bind=True, base=LeadTask)\ndef generate_lead_insights_report(\n    self,\n    organization_id: str,\n    days: int = 30\n):\n    \"\"\"Generate insights report about lead patterns and trends\"\"\"\n    try:\n        logger.info(f\"Generating lead insights report for organization {organization_id}\")\n        \n        async def generate_insights():\n            async with AsyncSessionLocal() as db:\n                # Get lead metrics\n                lead_metrics = await self.analytics_service.get_lead_metrics(\n                    organization_id, db, days=days\n                )\n                \n                # Get ML insights\n                ml_insights = await self.twentyonedev_service.get_conversation_insights(\n                    organization_id, [], \"lead_generation\"\n                )\n                \n                # Combine insights\n                insights_report = {\n                    \"organization_id\": organization_id,\n                    \"generated_at\": datetime.utcnow().isoformat(),\n                    \"date_range_days\": days,\n                    \"lead_metrics\": lead_metrics,\n                    \"ml_insights\": ml_insights,\n                    \"recommendations\": generate_lead_recommendations(lead_metrics, ml_insights)\n                }\n                \n                # Track report generation\n                await self.analytics_service.track_event(\n                    \"reports\", \"lead_insights_generated\", organization_id, db,\n                    properties={\"days\": days, \"automated\": True}\n                )\n                \n                return insights_report\n        \n        import asyncio\n        return asyncio.run(generate_insights())\n        \n    except Exception as e:\n        logger.error(f\"Failed to generate lead insights report: {e}\")\n        raise\n\n\ndef generate_lead_recommendations(lead_metrics: Dict[str, Any], ml_insights: Optional[Dict[str, Any]]) -> List[str]:\n    \"\"\"Generate actionable recommendations based on lead data\"\"\"\n    recommendations = []\n    \n    # Analyze conversion rates\n    if lead_metrics.get(\"high_quality_rate\", 0) < 25:\n        recommendations.append(\"Improve lead qualification criteria to increase high-quality lead rate\")\n    \n    # Analyze source performance\n    source_breakdown = lead_metrics.get(\"source_breakdown\", {})\n    if \"voice_call\" in source_breakdown and source_breakdown[\"voice_call\"] > 0:\n        recommendations.append(\"Voice calls are generating leads - consider increasing call capacity\")\n    \n    # Add ML-based recommendations\n    if ml_insights and ml_insights.get(\"recommendations\"):\n        recommendations.extend(ml_insights[\"recommendations\"][:3])\n    \n    return recommendations[:5]  # Return top 5 recommendations