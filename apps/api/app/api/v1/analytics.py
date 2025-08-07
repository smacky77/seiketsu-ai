"""
Advanced Analytics API with 21dev.ai ML Integration
Real-time insights, predictive analytics, and performance optimization
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_organization
from app.models.user import User
from app.models.organization import Organization
from app.services.analytics_service import AnalyticsService
from app.services.twentyonedev_service import TwentyOneDevService
from app.tasks.analytics_tasks import generate_analytics_report, sync_data_to_twentyonedev

logger = logging.getLogger("seiketsu.analytics")
router = APIRouter()

# Initialize services
analytics_service = AnalyticsService()
twentyonedev_service = TwentyOneDevService()

# Request/Response Models
class AnalyticsEventRequest(BaseModel):
    event_type: str = Field(..., max_length=50)
    event_name: str = Field(..., max_length=100)
    properties: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None

class DashboardResponse(BaseModel):
    real_time_metrics: Dict[str, Any]
    conversation_metrics: Dict[str, Any]
    lead_metrics: Dict[str, Any]
    voice_agent_performance: List[Dict[str, Any]]
    ml_insights: Optional[Dict[str, Any]] = None
    last_updated: datetime

class PerformanceMetricsResponse(BaseModel):
    organization_metrics: Dict[str, Any]
    agent_performance: List[Dict[str, Any]]
    benchmarks: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None

class ConversationAnalysisResponse(BaseModel):
    patterns: Dict[str, Any]
    insights: Dict[str, Any]
    predictions: Optional[Dict[str, Any]] = None
    optimization_suggestions: List[str]

class ExportRequest(BaseModel):
    report_type: str = Field(..., regex="^(dashboard|conversations|leads|performance|custom)$")
    date_range_days: int = Field(30, ge=1, le=365)
    include_ml_insights: bool = False
    format: str = Field("json", regex="^(json|csv|pdf)$")
    filters: Optional[Dict[str, Any]] = {}

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_metrics(
    days: int = Query(30, ge=1, le=365),
    include_ml: bool = Query(False),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> DashboardResponse:
    """Get comprehensive dashboard metrics with optional ML insights"""
    try:
        # Get real-time metrics
        real_time_metrics = await analytics_service.get_real_time_dashboard(current_org.id, db)
        
        # Get conversation metrics
        conversation_metrics = await analytics_service.get_conversation_metrics(
            current_org.id, db, days=days
        )
        
        # Get lead metrics
        lead_metrics = await analytics_service.get_lead_metrics(
            current_org.id, db, days=days
        )
        
        # Get voice agent performance
        voice_agent_performance = await analytics_service.get_voice_agent_performance(
            current_org.id, db, days=days
        )
        
        # Get ML insights if requested
        ml_insights = None
        if include_ml:
            ml_insights = await analytics_service.get_predictive_insights(current_org.id, db)
        
        # Track dashboard view
        await analytics_service.track_event(
            "analytics", "dashboard_viewed", current_org.id, db,
            user_id=current_user.id,
            properties={"days": days, "include_ml": include_ml}
        )
        
        return DashboardResponse(
            real_time_metrics=real_time_metrics,
            conversation_metrics=conversation_metrics,
            lead_metrics=lead_metrics,
            voice_agent_performance=voice_agent_performance,
            ml_insights=ml_insights,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard metrics")

@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    days: int = Query(30, ge=1, le=90),
    include_benchmarks: bool = Query(False),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> PerformanceMetricsResponse:
    """Get detailed performance metrics with industry benchmarks"""
    try:
        # Get organization metrics
        conversation_metrics = await analytics_service.get_conversation_metrics(
            current_org.id, db, days=days
        )
        lead_metrics = await analytics_service.get_lead_metrics(
            current_org.id, db, days=days
        )
        
        organization_metrics = {
            "conversations": conversation_metrics,
            "leads": lead_metrics,
            "efficiency_score": calculate_efficiency_score(conversation_metrics, lead_metrics)
        }
        
        # Get agent performance
        agent_performance = await analytics_service.get_voice_agent_performance(
            current_org.id, db, days=days
        )
        
        # Get industry benchmarks if requested
        benchmarks = None
        if include_benchmarks:
            benchmarks = await twentyonedev_service.get_performance_benchmarks(
                current_org.id, "real_estate"
            )
        
        # Get AI recommendations
        recommendations = await twentyonedev_service.get_real_time_recommendations(
            current_org.id,
            {
                "conversation_metrics": conversation_metrics,
                "lead_metrics": lead_metrics,
                "agent_performance": agent_performance
            }
        )
        
        return PerformanceMetricsResponse(
            organization_metrics=organization_metrics,
            agent_performance=agent_performance,
            benchmarks=benchmarks,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")

@router.get("/conversations/analysis", response_model=ConversationAnalysisResponse)
async def get_conversation_analysis(
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> ConversationAnalysisResponse:
    """Get advanced conversation pattern analysis"""
    try:
        # Get conversation patterns
        patterns = await analytics_service.analyze_conversation_patterns(
            current_org.id, db, days=days
        )
        
        # Get ML insights from 21dev.ai
        conversation_data = await prepare_conversation_data_for_ml(current_org.id, db, days)
        ml_insights = await twentyonedev_service.get_conversation_insights(
            current_org.id, conversation_data, "performance"
        )
        
        # Get predictions
        predictions = await analytics_service.get_predictive_insights(current_org.id, db)
        
        # Generate optimization suggestions
        optimization_suggestions = generate_optimization_suggestions(
            patterns, ml_insights, predictions
        )
        
        insights = {
            "patterns": patterns,
            "ml_analysis": ml_insights,
            "data_quality_score": calculate_data_quality_score(patterns)
        }
        
        return ConversationAnalysisResponse(
            patterns=patterns,
            insights=insights,
            predictions=predictions,
            optimization_suggestions=optimization_suggestions
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversation analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze conversations")

@router.get("/leads/scoring")
async def get_lead_scoring_insights(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get lead scoring model insights and recommendations"""
    try:
        # Get lead scoring model from 21dev.ai
        scoring_model = await twentyonedev_service.get_lead_scoring_model(current_org.id)
        
        # Get recent lead performance
        lead_metrics = await analytics_service.get_lead_metrics(current_org.id, db, days=30)
        
        # Analyze lead quality trends
        quality_trends = await analyze_lead_quality_trends(current_org.id, db)
        
        return {
            "scoring_model": scoring_model,
            "lead_metrics": lead_metrics,
            "quality_trends": quality_trends,
            "recommendations": generate_lead_scoring_recommendations(scoring_model, lead_metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get lead scoring insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve lead scoring insights")

@router.get("/agents/{agent_id}/optimization")
async def get_agent_optimization(
    agent_id: str,
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get AI-powered optimization suggestions for a specific voice agent"""
    try:
        # Get agent performance data
        performance_data = await get_agent_performance_data(agent_id, current_org.id, db, days)
        
        # Get optimization recommendations from 21dev.ai
        optimization = await twentyonedev_service.optimize_voice_agent_settings(
            current_org.id, agent_id, performance_data
        )
        
        return {
            "agent_id": agent_id,
            "current_performance": performance_data,
            "optimization_recommendations": optimization,
            "estimated_improvements": calculate_estimated_improvements(performance_data, optimization)
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent optimization: {e}")
        raise HTTPException(status_code=500, detail="Failed to get optimization recommendations")

@router.post("/events")
async def track_custom_event(
    request: AnalyticsEventRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Track custom analytics event"""
    try:
        await analytics_service.track_event(
            request.event_type,
            request.event_name,
            current_org.id,
            db,
            user_id=current_user.id,
            session_id=request.session_id,
            properties=request.properties
        )
        
        return {
            "success": True,
            "message": "Event tracked successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to track custom event: {e}")
        raise HTTPException(status_code=500, detail="Failed to track event")

@router.post("/export", status_code=202)
async def export_analytics_report(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Export comprehensive analytics report"""
    try:
        # Generate unique report ID
        import uuid
        report_id = str(uuid.uuid4())
        
        # Schedule report generation in background
        background_tasks.add_task(
            generate_analytics_report,
            report_id=report_id,
            organization_id=current_org.id,
            user_id=current_user.id,
            report_type=request.report_type,
            date_range_days=request.date_range_days,
            include_ml_insights=request.include_ml_insights,
            format=request.format,
            filters=request.filters
        )
        
        # Track export request
        await analytics_service.track_event(
            "analytics", "report_requested", current_org.id, db,
            user_id=current_user.id,
            properties={
                "report_id": report_id,
                "report_type": request.report_type,
                "format": request.format
            }
        )
        
        return {
            "report_id": report_id,
            "status": "processing",
            "estimated_completion_minutes": estimate_report_completion_time(request),
            "download_url": f"/api/v1/analytics/reports/{report_id}/download"
        }
        
    except Exception as e:
        logger.error(f"Failed to export analytics report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create export")

@router.get("/reports/{report_id}/status")
async def get_report_status(
    report_id: str,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization)
) -> Dict[str, Any]:
    """Get status of analytics report generation"""
    try:
        # TODO: Implement report status tracking
        # This would typically check a job queue or database
        
        return {
            "report_id": report_id,
            "status": "completed",  # or "processing", "failed"
            "progress_percentage": 100,
            "download_url": f"/api/v1/analytics/reports/{report_id}/download"
        }
        
    except Exception as e:
        logger.error(f"Failed to get report status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get report status")

@router.post("/ml/train-model")
async def train_custom_model(
    model_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Train custom ML model for organization"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Prepare training data
        training_data = await prepare_training_data(current_org.id, db, model_type)
        
        # Submit training job to 21dev.ai
        training_job = await twentyonedev_service.train_custom_model(
            current_org.id, training_data, model_type
        )
        
        if not training_job:
            raise HTTPException(status_code=503, detail="ML service unavailable")
        
        # Track model training request
        await analytics_service.track_event(
            "ml", "model_training_started", current_org.id, db,
            user_id=current_user.id,
            properties={
                "model_type": model_type,
                "job_id": training_job.get("job_id")
            }
        )
        
        return {
            "success": True,
            "job_id": training_job.get("job_id"),
            "model_type": model_type,
            "estimated_completion_hours": training_job.get("estimated_completion_hours", 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to train custom model: {e}")
        raise HTTPException(status_code=500, detail="Failed to start model training")

@router.post("/sync-to-ml")
async def sync_data_to_ml_service(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization)
) -> Dict[str, Any]:
    """Sync organization data to 21dev.ai ML service"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Schedule data sync in background
        background_tasks.add_task(
            sync_data_to_twentyonedev,
            organization_id=current_org.id,
            sync_type="full"
        )
        
        return {
            "success": True,
            "message": "Data sync initiated",
            "estimated_completion_minutes": 15
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync data to ML service: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate data sync")

# Helper functions
def calculate_efficiency_score(conversation_metrics: Dict[str, Any], lead_metrics: Dict[str, Any]) -> float:
    """Calculate overall efficiency score"""
    try:
        conv_rate = conversation_metrics.get("completion_rate", 0)
        lead_rate = conversation_metrics.get("lead_conversion_rate", 0)
        quality_rate = lead_metrics.get("high_quality_rate", 0)
        
        # Weighted average
        efficiency = (conv_rate * 0.3) + (lead_rate * 0.4) + (quality_rate * 0.3)
        return round(efficiency, 2)
    except:
        return 0.0

def generate_optimization_suggestions(
    patterns: Dict[str, Any],
    ml_insights: Optional[Dict[str, Any]],
    predictions: Optional[Dict[str, Any]]
) -> List[str]:
    """Generate optimization suggestions based on analysis"""
    suggestions = []
    
    # Peak hours optimization
    if patterns.get("peak_hours", {}).get("peak_hour_count", 0) > 0:
        peak_hour = patterns["peak_hours"].get("peak_hour", 0)
        suggestions.append(f"Schedule more agents during peak hour: {peak_hour}:00")
    
    # Duration optimization
    flow_data = patterns.get("conversation_flow", {})
    if flow_data:
        suggestions.append("Optimize conversation flow based on successful completion patterns")
    
    # Sentiment optimization
    sentiment_data = patterns.get("sentiment_patterns", {})
    if sentiment_data.get("negative_rate", 0) > 20:
        suggestions.append("Review agent training to improve customer sentiment")
    
    # ML-based suggestions
    if ml_insights and ml_insights.get("recommendations"):
        suggestions.extend(ml_insights["recommendations"][:3])  # Top 3 ML suggestions
    
    return suggestions[:5]  # Return top 5 suggestions

def calculate_data_quality_score(patterns: Dict[str, Any]) -> float:
    """Calculate data quality score"""
    try:
        total_conversations = patterns.get("peak_hours", {}).get("total_conversations", 0)
        if total_conversations < 10:
            return 0.3  # Low quality due to insufficient data
        elif total_conversations < 50:
            return 0.6  # Medium quality
        else:
            return 0.9  # High quality
    except:
        return 0.0

async def prepare_conversation_data_for_ml(organization_id: str, db: AsyncSession, days: int) -> List[Dict[str, Any]]:
    """Prepare conversation data for ML analysis"""
    # This would fetch and format conversation data
    # Implementation depends on your specific data model
    return []

async def analyze_lead_quality_trends(organization_id: str, db: AsyncSession) -> Dict[str, Any]:
    """Analyze lead quality trends over time"""
    # Implementation for lead quality trend analysis
    return {"trend": "stable", "quality_improvement": 0.0}

def generate_lead_scoring_recommendations(scoring_model: Optional[Dict[str, Any]], lead_metrics: Dict[str, Any]) -> List[str]:
    """Generate lead scoring recommendations"""
    recommendations = []
    
    if lead_metrics.get("high_quality_rate", 0) < 30:
        recommendations.append("Focus on improving lead qualification questions")
    
    if lead_metrics.get("average_lead_score", 0) < 60:
        recommendations.append("Review lead scoring criteria and thresholds")
    
    return recommendations

async def get_agent_performance_data(agent_id: str, organization_id: str, db: AsyncSession, days: int) -> Dict[str, Any]:
    """Get performance data for specific agent"""
    # Implementation for agent-specific performance data
    return {"conversations": 0, "conversion_rate": 0.0}

def calculate_estimated_improvements(performance_data: Dict[str, Any], optimization: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate estimated improvements from optimization"""
    if not optimization:
        return {"estimated_improvement": "No optimization data available"}
    
    return {
        "conversion_rate_improvement": "+5-15%",
        "call_duration_optimization": "-10-20%",
        "customer_satisfaction": "+10-25%"
    }

def estimate_report_completion_time(request: ExportRequest) -> int:
    """Estimate report completion time in minutes"""
    base_time = 2
    if request.include_ml_insights:
        base_time += 3
    if request.date_range_days > 90:
        base_time += 2
    if request.format == "pdf":
        base_time += 1
    return base_time

async def prepare_training_data(organization_id: str, db: AsyncSession, model_type: str) -> Dict[str, Any]:
    """Prepare training data for ML model"""
    # Implementation depends on model type and data requirements
    return {"training_samples": 0, "features": [], "labels": []}