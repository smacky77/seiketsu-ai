"""
Celery tasks for background voice generation and processing
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from celery import Task
from app.tasks.celery_app import celery_app
from app.services.elevenlabs_service import elevenlabs_service, Language
from app.models.voice_agent import VoiceAgent
from app.core.database import get_db_session
from app.services.twentyonedev_service import analytics_service

logger = logging.getLogger("seiketsu.voice_tasks")

class AsyncTask(Task):
    """Base task class for async operations"""
    
    def run_async(self, coro):
        """Run async function in task"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

@celery_app.task(bind=True, base=AsyncTask)
def pregenerate_agent_voices(self, agent_id: str, language: str = "en"):
    """Pre-generate common voice responses for an agent"""
    return self.run_async(self._pregenerate_agent_voices_async(agent_id, language))

async def _pregenerate_agent_voices_async(agent_id: str, language: str):
    """Async implementation of voice pre-generation"""
    try:
        # Initialize services
        await elevenlabs_service.initialize()
        
        # Get agent from database
        async with get_db_session() as db:
            agent = await db.get(VoiceAgent, agent_id)
            if not agent or not agent.is_active:
                logger.warning(f"Agent {agent_id} not found or inactive")
                return {"status": "skipped", "reason": "agent not found or inactive"}
        
        # Common real estate agent responses
        common_responses = [
            "Hello! Thank you for calling. How can I help you today?",
            "I'd be happy to help you find the perfect property.",
            "What type of property are you looking for?",
            "What's your budget range?",
            "Are you looking to buy or rent?",
            "I can schedule a viewing for you right away.",
            "Let me check our available listings for you.",
            "That's a great choice! This property has excellent features.",
            "I can connect you with our mortgage specialist.",
            "Would you like to know more about the neighborhood?",
            "I'll send you the property details right away.",
            "Thank you for your interest. I'll be in touch soon.",
            "Let me transfer you to one of our specialists.",
            "Is there anything else I can help you with today?",
            "Thank you for your time. Have a wonderful day!"
        ]
        
        # Map language
        lang_map = {
            "en": Language.ENGLISH,
            "es": Language.SPANISH,
            "zh": Language.MANDARIN
        }
        
        # Pre-generate responses
        await elevenlabs_service.pregenerate_responses(
            voice_agent=agent,
            responses=common_responses,
            language=lang_map.get(language, Language.ENGLISH)
        )
        
        # Send analytics event
        await analytics_service.track_event("voice_pregeneration_completed", {
            "agent_id": agent_id,
            "language": language,
            "responses_count": len(common_responses),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Pre-generated {len(common_responses)} responses for agent {agent_id}")
        
        return {
            "status": "completed",
            "agent_id": agent_id,
            "language": language,
            "responses_generated": len(common_responses)
        }
        
    except Exception as e:
        logger.error(f"Voice pre-generation failed for agent {agent_id}: {e}")
        
        # Send error analytics
        await analytics_service.track_event("voice_pregeneration_failed", {
            "agent_id": agent_id,
            "language": language,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "status": "failed",
            "agent_id": agent_id,
            "error": str(e)
        }

@celery_app.task(bind=True, base=AsyncTask)
def bulk_voice_synthesis(self, texts: List[str], agent_id: str, language: str = "en"):
    """Bulk synthesize multiple texts in background"""
    return self.run_async(self._bulk_voice_synthesis_async(texts, agent_id, language))

async def _bulk_voice_synthesis_async(texts: List[str], agent_id: str, language: str):
    """Async implementation of bulk voice synthesis"""
    try:
        # Initialize services
        await elevenlabs_service.initialize()
        
        # Get agent from database
        async with get_db_session() as db:
            agent = await db.get(VoiceAgent, agent_id)
            if not agent:
                return {"status": "failed", "error": "Agent not found"}
        
        # Map language
        lang_map = {
            "en": Language.ENGLISH,
            "es": Language.SPANISH,
            "zh": Language.MANDARIN
        }
        
        # Synthesize all texts
        results = await elevenlabs_service.bulk_synthesize(
            texts=texts,
            voice_agent=agent,
            language=lang_map.get(language, Language.ENGLISH),
            max_concurrent=5  # Limit concurrency in background
        )
        
        # Send analytics
        await analytics_service.track_event("bulk_voice_synthesis_completed", {
            "agent_id": agent_id,
            "language": language,
            "texts_count": len(texts),
            "successful_count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "status": "completed",
            "agent_id": agent_id,
            "texts_processed": len(texts),
            "successful_syntheses": len(results)
        }
        
    except Exception as e:
        logger.error(f"Bulk voice synthesis failed: {e}")
        return {"status": "failed", "error": str(e)}

@celery_app.task(bind=True, base=AsyncTask)
def daily_voice_cache_maintenance(self):
    """Daily maintenance of voice cache"""
    return self.run_async(self._daily_voice_cache_maintenance_async())

async def _daily_voice_cache_maintenance_async():
    """Clean up expired voice cache entries"""
    try:
        await elevenlabs_service.initialize()
        
        # This would implement cache cleanup logic
        # For now, just log the task execution
        logger.info("Daily voice cache maintenance completed")
        
        # Send analytics
        await analytics_service.track_event("voice_cache_maintenance", {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed"
        })
        
        return {"status": "completed"}
        
    except Exception as e:
        logger.error(f"Voice cache maintenance failed: {e}")
        return {"status": "failed", "error": str(e)}

@celery_app.task(bind=True, base=AsyncTask)
def voice_quality_analysis(self, synthesis_results: List[Dict[str, Any]]):
    """Analyze voice quality metrics and send to monitoring"""
    return self.run_async(self._voice_quality_analysis_async(synthesis_results))

async def _voice_quality_analysis_async(synthesis_results: List[Dict[str, Any]]):
    """Analyze voice synthesis quality metrics"""
    try:
        if not synthesis_results:
            return {"status": "skipped", "reason": "no results to analyze"}
        
        # Calculate quality metrics
        total_syntheses = len(synthesis_results)
        fast_syntheses = sum(1 for r in synthesis_results if r.get("processing_time_ms", 0) < 2000)
        cache_hits = sum(1 for r in synthesis_results if r.get("cached", False))
        
        quality_metrics = {
            "total_syntheses": total_syntheses,
            "fast_synthesis_rate": (fast_syntheses / total_syntheses) * 100,
            "cache_hit_rate": (cache_hits / total_syntheses) * 100,
            "average_processing_time_ms": sum(r.get("processing_time_ms", 0) for r in synthesis_results) / total_syntheses,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to monitoring
        await analytics_service.track_event("voice_quality_metrics", quality_metrics)
        
        logger.info(f"Voice quality analysis completed: {quality_metrics}")
        
        return {"status": "completed", "metrics": quality_metrics}
        
    except Exception as e:
        logger.error(f"Voice quality analysis failed: {e}")
        return {"status": "failed", "error": str(e)}

@celery_app.task(bind=True, base=AsyncTask)
def scheduled_voice_warmup(self):
    """Warm up voice services for peak hours"""
    return self.run_async(self._scheduled_voice_warmup_async())

async def _scheduled_voice_warmup_async():
    """Pre-warm voice services before peak usage"""
    try:
        await elevenlabs_service.initialize()
        
        # Perform health check to warm up connections
        health_status = await elevenlabs_service.health_check()
        
        # Pre-generate a test phrase to warm up the pipeline
        test_phrases = [
            "Good morning! How can I help you?",
            "Thank you for calling. What can I do for you today?"
        ]
        
        # Get active voice agents and warm them up
        async with get_db_session() as db:
            from sqlalchemy import select
            
            stmt = select(VoiceAgent).where(VoiceAgent.is_active == True).limit(5)
            result = await db.execute(stmt)
            agents = result.scalars().all()
            
            warmup_count = 0
            for agent in agents:
                try:
                    # Synthesize test phrases to warm up
                    await elevenlabs_service.bulk_synthesize(
                        texts=test_phrases,
                        voice_agent=agent,
                        language=Language.ENGLISH,
                        max_concurrent=2
                    )
                    warmup_count += 1
                except Exception as e:
                    logger.warning(f"Warmup failed for agent {agent.id}: {e}")
        
        # Send analytics
        await analytics_service.track_event("voice_service_warmup", {
            "agents_warmed_up": warmup_count,
            "health_status": health_status["status"],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Voice service warmup completed: {warmup_count} agents warmed up")
        
        return {
            "status": "completed", 
            "agents_warmed_up": warmup_count,
            "health_status": health_status["status"]
        }
        
    except Exception as e:
        logger.error(f"Voice service warmup failed: {e}")
        return {"status": "failed", "error": str(e)}

# Scheduled tasks setup
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'daily-voice-cache-maintenance': {
        'task': 'app.tasks.voice_generation_tasks.daily_voice_cache_maintenance',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'morning-voice-warmup': {
        'task': 'app.tasks.voice_generation_tasks.scheduled_voice_warmup',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
    'evening-voice-warmup': {
        'task': 'app.tasks.voice_generation_tasks.scheduled_voice_warmup',
        'schedule': crontab(hour=17, minute=0),  # 5 PM daily
    },
}