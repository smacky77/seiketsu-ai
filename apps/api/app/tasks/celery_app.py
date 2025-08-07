"""
Celery application configuration for background job processing
"""
from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger("seiketsu.celery")

# Create Celery instance
celery_app = Celery(
    "seiketsu_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.analytics_tasks",
        "app.tasks.lead_tasks",
        "app.tasks.voice_tasks",
        "app.tasks.ml_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Routes
    task_routes={
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
        "app.tasks.lead_tasks.*": {"queue": "leads"},
        "app.tasks.voice_tasks.*": {"queue": "voice"},
        "app.tasks.ml_tasks.*": {"queue": "ml"},
    },
    # Beat schedule for periodic tasks
    beat_schedule={
        "sync-analytics-to-ml": {
            "task": "app.tasks.analytics_tasks.sync_analytics_to_twentyonedev",
            "schedule": 300.0,  # Every 5 minutes
        },
        "process-follow-up-reminders": {
            "task": "app.tasks.lead_tasks.process_follow_up_reminders",
            "schedule": 3600.0,  # Every hour
        },
        "cleanup-expired-conversations": {
            "task": "app.tasks.voice_tasks.cleanup_expired_conversations",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "update-lead-scores": {
            "task": "app.tasks.ml_tasks.update_lead_scores",
            "schedule": 7200.0,  # Every 2 hours
        },
        "generate-daily-reports": {
            "task": "app.tasks.analytics_tasks.generate_daily_reports",
            "schedule": {
                "hour": 6,
                "minute": 0,
            },  # Daily at 6 AM UTC
        },
    },
)

logger.info("Celery application configured successfully")