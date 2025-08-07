"""
Analytics background tasks
Report generation, ML sync, and data processing
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import csv
import io
from celery import Task

from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.analytics_service import AnalyticsService
from app.services.twentyonedev_service import TwentyOneDevService
from app.models.organization import Organization

logger = logging.getLogger("seiketsu.analytics_tasks")


class DatabaseTask(Task):
    """Base task with database session management"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
        self.twentyonedev_service = TwentyOneDevService()


@celery_app.task(bind=True, base=DatabaseTask)
def generate_analytics_report(
    self,
    report_id: str,
    organization_id: str,
    user_id: str,
    report_type: str,
    date_range_days: int = 30,
    include_ml_insights: bool = False,
    format: str = "json",
    filters: Optional[Dict[str, Any]] = None
):
    """Generate comprehensive analytics report"""
    try:
        logger.info(f"Starting analytics report generation: {report_id}")
        
        # Update task progress
        self.update_state(state="PROGRESS", meta={"progress": 10, "status": "Initializing"})
        
        # Generate report data
        async def generate_report_data():
            async with AsyncSessionLocal() as db:
                # Get dashboard metrics
                self.update_state(state="PROGRESS", meta={"progress": 30, "status": "Collecting metrics"})
                
                dashboard_metrics = await self.analytics_service.get_real_time_dashboard(
                    organization_id, db
                )
                
                conversation_metrics = await self.analytics_service.get_conversation_metrics(
                    organization_id, db, days=date_range_days
                )
                
                lead_metrics = await self.analytics_service.get_lead_metrics(
                    organization_id, db, days=date_range_days
                )
                
                agent_performance = await self.analytics_service.get_voice_agent_performance(
                    organization_id, db, days=date_range_days
                )
                
                self.update_state(state="PROGRESS", meta={"progress": 60, "status": "Analyzing patterns"})
                
                # Get ML insights if requested
                ml_insights = None
                if include_ml_insights:
                    ml_insights = await self.analytics_service.get_predictive_insights(
                        organization_id, db
                    )
                    
                    conversation_patterns = await self.analytics_service.analyze_conversation_patterns(
                        organization_id, db, days=date_range_days
                    )
                    ml_insights["conversation_patterns"] = conversation_patterns
                
                return {
                    "report_id": report_id,
                    "organization_id": organization_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "generated_by_user_id": user_id,
                    "date_range_days": date_range_days,
                    "dashboard_metrics": dashboard_metrics,
                    "conversation_metrics": conversation_metrics,
                    "lead_metrics": lead_metrics,
                    "agent_performance": agent_performance,
                    "ml_insights": ml_insights,
                    "filters_applied": filters
                }
        
        # Run async function
        import asyncio
        report_data = asyncio.run(generate_report_data())
        
        self.update_state(state="PROGRESS", meta={"progress": 80, "status": "Formatting report"})
        
        # Format report based on requested format
        if format == "json":
            report_content = json.dumps(report_data, indent=2, default=str)
            content_type = "application/json"
        elif format == "csv":
            report_content = convert_to_csv(report_data)
            content_type = "text/csv"
        elif format == "pdf":
            report_content = generate_pdf_report(report_data)
            content_type = "application/pdf"
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Store report (in production, save to S3 or similar)
        report_storage_path = f"reports/{report_id}.{format}"
        # TODO: Implement actual file storage
        
        self.update_state(state="PROGRESS", meta={"progress": 100, "status": "Complete"})
        
        logger.info(f"Analytics report generated successfully: {report_id}")
        
        return {
            "report_id": report_id,
            "status": "completed",
            "download_url": f"/api/v1/analytics/reports/{report_id}/download",
            "content_type": content_type,
            "size_bytes": len(report_content),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate analytics report {report_id}: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "progress": 0}
        )
        raise


@celery_app.task(bind=True, base=DatabaseTask)
def sync_data_to_twentyonedev(
    self,
    organization_id: str,
    sync_type: str = "incremental"
):
    """Sync organization data to 21dev.ai ML service"""
    try:
        logger.info(f"Starting data sync to 21dev.ai: {organization_id}")
        
        async def sync_data():
            async with AsyncSessionLocal() as db:
                # Get recent conversations
                recent_conversations = await self.analytics_service._get_recent_conversations(
                    organization_id, db, days=7 if sync_type == "incremental" else 90
                )
                
                # Get recent leads
                recent_leads = await self.analytics_service._get_recent_leads(
                    organization_id, db, days=7 if sync_type == "incremental" else 90
                )
                
                # Format data for ML service
                events = []
                
                # Add conversation events
                for conv in recent_conversations:
                    events.append({
                        "event_type": "conversation",
                        "timestamp": conv.started_at.isoformat(),
                        "data": {
                            "conversation_id": conv.id,
                            "duration_seconds": conv.duration_seconds,
                            "status": conv.status.value,
                            "sentiment_score": conv.sentiment_score,
                            "converted_to_lead": bool(conv.lead_id),
                            "voice_agent_id": conv.voice_agent_id
                        }
                    })
                
                # Add lead events
                for lead in recent_leads:
                    events.append({
                        "event_type": "lead",
                        "timestamp": lead.created_at.isoformat(),
                        "data": {
                            "lead_id": lead.id,
                            "score": lead.lead_score,
                            "status": lead.status.value,
                            "source": lead.source.value if lead.source else None,
                            "budget_range": lead.budget_max - lead.budget_min if lead.budget_max and lead.budget_min else None,
                            "qualified": lead.lead_score >= 70 if lead.lead_score else False
                        }
                    })
                
                # Send to 21dev.ai
                if events:
                    result = await self.twentyonedev_service.send_analytics_batch(
                        events, organization_id
                    )
                    
                    if result:
                        logger.info(f"Successfully synced {len(events)} events to 21dev.ai")
                        return {"synced_events": len(events), "status": "success"}
                    else:
                        logger.warning("Failed to sync data to 21dev.ai")
                        return {"synced_events": 0, "status": "failed"}
                else:
                    logger.info("No new data to sync")
                    return {"synced_events": 0, "status": "no_data"}
        
        return asyncio.run(sync_data())
        
    except Exception as e:
        logger.error(f"Failed to sync data to 21dev.ai: {e}")
        raise


@celery_app.task(base=DatabaseTask)
def sync_analytics_to_twentyonedev():
    """Periodic task to sync analytics data to 21dev.ai"""
    try:
        logger.info("Starting periodic analytics sync to 21dev.ai")
        
        async def sync_all_organizations():
            async with AsyncSessionLocal() as db:
                # Get all active organizations
                from sqlalchemy import select
                stmt = select(Organization).where(Organization.is_active == True)
                result = await db.execute(stmt)
                organizations = result.scalars().all()
                
                synced_count = 0
                for org in organizations:
                    try:
                        sync_result = await sync_data_to_twentyonedev.apply_async(
                            args=[org.id, "incremental"]
                        )
                        if sync_result:
                            synced_count += 1
                    except Exception as e:
                        logger.error(f"Failed to sync org {org.id}: {e}")
                        continue
                
                return synced_count
        
        synced_orgs = asyncio.run(sync_all_organizations())
        logger.info(f"Periodic sync completed for {synced_orgs} organizations")
        
        return {"synced_organizations": synced_orgs}
        
    except Exception as e:
        logger.error(f"Periodic analytics sync failed: {e}")
        raise


@celery_app.task(base=DatabaseTask)
def generate_daily_reports():
    """Generate daily analytics reports for all organizations"""
    try:
        logger.info("Starting daily report generation")
        
        async def generate_reports():
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                stmt = select(Organization).where(Organization.is_active == True)
                result = await db.execute(stmt)
                organizations = result.scalars().all()
                
                generated_count = 0
                for org in organizations:
                    try:
                        # Generate report for organization
                        report_id = f"daily_{org.id}_{datetime.utcnow().strftime('%Y%m%d')}"
                        
                        generate_analytics_report.apply_async(
                            args=[
                                report_id,
                                org.id,
                                "system",  # System-generated report
                                "dashboard",
                                1,  # 1 day
                                False,  # No ML insights for daily reports
                                "json"
                            ]
                        )
                        
                        generated_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to generate daily report for org {org.id}: {e}")
                        continue
                
                return generated_count
        
        generated_reports = asyncio.run(generate_reports())
        logger.info(f"Generated {generated_reports} daily reports")
        
        return {"generated_reports": generated_reports}
        
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}")
        raise


def convert_to_csv(report_data: Dict[str, Any]) -> str:
    """Convert report data to CSV format"""
    output = io.StringIO()
    
    # Write conversation metrics
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    
    conv_metrics = report_data.get("conversation_metrics", {})
    for key, value in conv_metrics.items():
        if isinstance(value, (int, float, str)):
            writer.writerow([key.replace("_", " ").title(), value])
    
    writer.writerow([])  # Empty row
    writer.writerow(["Lead Metrics"])
    
    lead_metrics = report_data.get("lead_metrics", {})
    for key, value in lead_metrics.items():
        if isinstance(value, (int, float, str)):
            writer.writerow([key.replace("_", " ").title(), value])
    
    return output.getvalue()


def generate_pdf_report(report_data: Dict[str, Any]) -> bytes:
    """Generate PDF report from data"""
    # This would use a library like reportlab or weasyprint
    # For now, return a placeholder
    pdf_content = f"PDF Report - {report_data.get('report_id', 'Unknown')}"
    return pdf_content.encode('utf-8')