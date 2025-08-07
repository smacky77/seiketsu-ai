"""
21dev.ai Integration Service
Advanced ML analytics and insights for Seiketsu AI
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
import asyncio
import json

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.lead import Lead

logger = logging.getLogger("seiketsu.twentyonedev_service")


class TwentyOneDevService:
    """Service for integrating with 21dev.ai analytics platform"""
    
    def __init__(self):
        self.client = None
        self.base_url = settings.TWENTYONEDEV_BASE_URL
        self.api_key = settings.TWENTYONEDEV_API_KEY
        
        if self.api_key:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Seiketsu-AI/1.0"
                },
                timeout=settings.TWENTYONEDEV_TIMEOUT
            )
            logger.info("21dev.ai client initialized successfully")
        else:
            logger.warning("21dev.ai API key not configured")
    
    async def send_analytics_batch(
        self,
        events: List[Dict[str, Any]],
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Send batch of analytics events to 21dev.ai"""
        if not self.client:
            return None
        
        try:
            payload = {
                "organization_id": organization_id,
                "events": events,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "seiketsu-ai"
            }
            
            response = await self.client.post("/analytics/batch", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Sent {len(events)} events to 21dev.ai for org {organization_id}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending to 21dev.ai: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Failed to send analytics batch to 21dev.ai: {e}")
            return None
    
    async def get_lead_scoring_model(
        self,
        organization_id: str,
        model_version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get lead scoring model from 21dev.ai"""
        if not self.client:
            return None
        
        try:
            params = {"organization_id": organization_id}
            if model_version:
                params["version"] = model_version
            
            response = await self.client.get("/models/lead-scoring", params=params)
            response.raise_for_status()
            
            model_data = response.json()
            logger.info(f"Retrieved lead scoring model for org {organization_id}")
            
            return model_data
            
        except Exception as e:
            logger.error(f"Failed to get lead scoring model: {e}")
            return None
    
    async def predict_lead_conversion(
        self,
        lead_data: Dict[str, Any],
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Predict lead conversion probability using 21dev.ai ML models"""
        if not self.client:
            return None
        
        try:
            payload = {
                "organization_id": organization_id,
                "lead_data": lead_data,
                "model_type": "lead_conversion"
            }
            
            response = await self.client.post("/predict/lead-conversion", json=payload)
            response.raise_for_status()
            
            prediction = response.json()
            logger.debug(f"Generated lead conversion prediction for org {organization_id}")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to predict lead conversion: {e}")
            return None
    
    async def get_conversation_insights(
        self,
        organization_id: str,
        conversation_data: List[Dict[str, Any]],
        insight_type: str = "performance"
    ) -> Optional[Dict[str, Any]]:
        """Get conversation insights from 21dev.ai"""
        if not self.client:
            return None
        
        try:
            payload = {
                "organization_id": organization_id,
                "conversations": conversation_data,
                "insight_type": insight_type,
                "analysis_depth": "detailed"
            }
            
            response = await self.client.post("/insights/conversations", json=payload)
            response.raise_for_status()
            
            insights = response.json()
            logger.info(f"Retrieved conversation insights for org {organization_id}")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get conversation insights: {e}")
            return None
    
    async def optimize_voice_agent_settings(
        self,
        organization_id: str,
        agent_id: str,
        performance_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get optimized voice agent settings from 21dev.ai"""
        if not self.client:
            return None
        
        try:
            payload = {
                "organization_id": organization_id,
                "agent_id": agent_id,
                "performance_data": performance_data,
                "optimization_goals": ["conversion_rate", "call_duration", "customer_satisfaction"]
            }
            
            response = await self.client.post("/optimize/voice-agent", json=payload)
            response.raise_for_status()
            
            optimization = response.json()
            logger.info(f"Retrieved voice agent optimization for {agent_id}")
            
            return optimization
            
        except Exception as e:
            logger.error(f"Failed to optimize voice agent settings: {e}")
            return None
    
    async def get_real_time_recommendations(
        self,
        organization_id: str,
        context: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """Get real-time recommendations for improving performance"""
        if not self.client:
            return None
        
        try:
            payload = {
                "organization_id": organization_id,
                "context": context,
                "recommendation_types": ["lead_qualification", "conversation_flow", "agent_performance"]
            }
            
            response = await self.client.post("/recommendations/real-time", json=payload)
            response.raise_for_status()
            
            recommendations = response.json()
            logger.debug(f"Retrieved real-time recommendations for org {organization_id}")
            
            return recommendations.get("recommendations", [])
            
        except Exception as e:
            logger.error(f"Failed to get real-time recommendations: {e}")
            return None
    
    async def train_custom_model(
        self,
        organization_id: str,
        training_data: Dict[str, Any],
        model_type: str
    ) -> Optional[Dict[str, Any]]:
        """Submit data for custom model training"""
        if not self.client:
            return None
        
        try:
            payload = {
                "organization_id": organization_id,
                "model_type": model_type,
                "training_data": training_data,
                "training_options": {
                    "auto_tune_hyperparameters": True,
                    "cross_validation": True,
                    "feature_selection": True
                }
            }
            
            response = await self.client.post("/models/train", json=payload)
            response.raise_for_status()
            
            training_job = response.json()
            logger.info(f"Started model training job {training_job.get('job_id')} for org {organization_id}")
            
            return training_job
            
        except Exception as e:
            logger.error(f"Failed to start model training: {e}")
            return None
    
    async def get_training_status(
        self,
        job_id: str,
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get status of model training job"""
        if not self.client:
            return None
        
        try:
            response = await self.client.get(
                f"/models/training-status/{job_id}",
                params={"organization_id": organization_id}
            )
            response.raise_for_status()
            
            status = response.json()
            return status
            
        except Exception as e:
            logger.error(f"Failed to get training status: {e}")
            return None
    
    async def get_performance_benchmarks(
        self,
        organization_id: str,
        industry: str = "real_estate"
    ) -> Optional[Dict[str, Any]]:
        """Get industry performance benchmarks"""
        if not self.client:
            return None
        
        try:
            response = await self.client.get(
                "/benchmarks/performance",
                params={
                    "organization_id": organization_id,
                    "industry": industry
                }
            )
            response.raise_for_status()
            
            benchmarks = response.json()
            logger.info(f"Retrieved performance benchmarks for {industry}")
            
            return benchmarks
            
        except Exception as e:
            logger.error(f"Failed to get performance benchmarks: {e}")
            return None
    
    async def analyze_competitor_insights(
        self,
        organization_id: str,
        market_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get competitive analysis insights"""
        if not self.client:
            return None
        
        try:
            payload = {
                "organization_id": organization_id,
                "market_data": market_data,
                "analysis_type": "competitive_positioning"
            }
            
            response = await self.client.post("/insights/competitive", json=payload)
            response.raise_for_status()
            
            insights = response.json()
            logger.info(f"Retrieved competitive insights for org {organization_id}")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to analyze competitor insights: {e}")
            return None
    
    async def create_dashboard_widgets(
        self,
        organization_id: str,
        widget_types: List[str]
    ) -> Optional[List[Dict[str, Any]]]:
        """Create custom dashboard widgets with ML insights"""
        if not self.client:
            return None
        
        try:
            payload = {
                "organization_id": organization_id,
                "widget_types": widget_types,
                "customization_level": "advanced"
            }
            
            response = await self.client.post("/dashboard/widgets", json=payload)
            response.raise_for_status()
            
            widgets = response.json()
            logger.info(f"Created {len(widget_types)} dashboard widgets for org {organization_id}")
            
            return widgets.get("widgets", [])
            
        except Exception as e:
            logger.error(f"Failed to create dashboard widgets: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if 21dev.ai service is healthy"""
        if not self.client:
            return False
        
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"21dev.ai health check failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()
            logger.info("21dev.ai client closed")