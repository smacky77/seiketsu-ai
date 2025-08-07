"""
Real Estate Intelligence Engine
Central orchestrator for all real estate domain AI capabilities
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .lead_qualification import LeadQualificationEngine
from .property_recommendations import PropertyRecommendationEngine
from .market_analysis import MarketAnalysisEngine
from .scheduling import AppointmentSchedulingEngine
from .follow_up import FollowUpRecommendationEngine
from ..config import ai_settings

logger = logging.getLogger(__name__)


@dataclass
class RealEstateAnalysisResult:
    """Result of real estate AI analysis"""
    success: bool
    lead_score: Optional[float] = None
    property_recommendations: List[Dict[str, Any]] = None
    market_insights: Dict[str, Any] = None
    scheduling_suggestions: List[Dict[str, Any]] = None
    follow_up_actions: List[Dict[str, Any]] = None
    processing_time_ms: int = 0
    confidence: float = 0.0
    error: Optional[str] = None


class RealEstateIntelligence:
    """
    Real Estate Domain Intelligence Engine
    Orchestrates all real estate AI capabilities for comprehensive analysis
    """
    
    def __init__(self):
        # Initialize domain engines
        self.lead_qualifier = LeadQualificationEngine()
        self.property_recommender = PropertyRecommendationEngine()
        self.market_analyzer = MarketAnalysisEngine()
        self.scheduler = AppointmentSchedulingEngine()
        self.follow_up_engine = FollowUpRecommendationEngine()
        
        # Configuration
        self.qualification_threshold = ai_settings.LEAD_QUALIFICATION_THRESHOLD
        self.recommendation_count = ai_settings.PROPERTY_RECOMMENDATION_COUNT
        
        logger.info("Real Estate Intelligence engine initialized")
    
    async def initialize(self):
        """Initialize all domain engines"""
        await asyncio.gather(
            self.lead_qualifier.initialize(),
            self.property_recommender.initialize(),
            self.market_analyzer.initialize(),
            self.scheduler.initialize(),
            self.follow_up_engine.initialize()
        )
        logger.info("Real Estate Intelligence components initialized")
    
    async def analyze_conversation(
        self,
        conversation_history: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        context: Dict[str, Any],
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> RealEstateAnalysisResult:
        """
        Comprehensive real estate analysis of conversation
        
        Args:
            conversation_history: Full conversation history
            user_profile: User profile information
            context: Additional context (location, preferences, etc.)
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            Complete real estate analysis result
        """
        start_time = time.time()
        
        try:
            # Run analyses in parallel for performance
            tasks = []
            
            # Lead qualification
            tasks.append(("lead_qualification", self.lead_qualifier.qualify_lead(
                conversation_history, user_profile, context, user_id, tenant_id
            )))
            
            # Property recommendations (if lead is qualified)
            tasks.append(("property_recommendations", self.property_recommender.recommend_properties(
                conversation_history, user_profile, context, user_id, tenant_id
            )))
            
            # Market analysis
            tasks.append(("market_analysis", self.market_analyzer.analyze_market_context(
                conversation_history, user_profile, context, user_id, tenant_id
            )))
            
            # Scheduling suggestions
            tasks.append(("scheduling", self.scheduler.suggest_appointments(
                conversation_history, user_profile, context, user_id, tenant_id
            )))
            
            # Follow-up recommendations
            tasks.append(("follow_up", self.follow_up_engine.recommend_follow_ups(
                conversation_history, user_profile, context, user_id, tenant_id
            )))
            
            # Execute all tasks
            results = {}
            completed_tasks = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            
            for i, (task_name, _) in enumerate(tasks):
                if isinstance(completed_tasks[i], Exception):
                    logger.error(f"Task {task_name} failed: {completed_tasks[i]}")
                    results[task_name] = None
                else:
                    results[task_name] = completed_tasks[i]
            
            # Calculate overall confidence
            confidence_scores = []
            if results["lead_qualification"]:
                confidence_scores.append(results["lead_qualification"].get("confidence", 0.0))
            if results["property_recommendations"]:
                confidence_scores.append(results["property_recommendations"].get("confidence", 0.0))
            if results["market_analysis"]:
                confidence_scores.append(results["market_analysis"].get("confidence", 0.0))
            
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Build result
            result = RealEstateAnalysisResult(
                success=True,
                lead_score=results["lead_qualification"].get("score") if results["lead_qualification"] else None,
                property_recommendations=results["property_recommendations"].get("properties", []) if results["property_recommendations"] else [],
                market_insights=results["market_analysis"] if results["market_analysis"] else {},
                scheduling_suggestions=results["scheduling"].get("suggestions", []) if results["scheduling"] else [],
                follow_up_actions=results["follow_up"].get("actions", []) if results["follow_up"] else [],
                processing_time_ms=processing_time_ms,
                confidence=overall_confidence
            )
            
            logger.info(f"Real estate analysis completed in {processing_time_ms}ms: {overall_confidence:.3f} confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"Real estate analysis failed: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return RealEstateAnalysisResult(
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )
    
    async def qualify_lead_quick(
        self,
        conversation_text: str,
        user_profile: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Quick lead qualification from single conversation"""
        try:
            # Convert text to conversation history format
            conversation_history = [{"role": "user", "content": conversation_text, "timestamp": time.time()}]
            
            result = await self.lead_qualifier.qualify_lead(
                conversation_history, user_profile or {}, {}, user_id, tenant_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Quick lead qualification failed: {e}")
            return {"score": 0.0, "qualified": False, "error": str(e)}
    
    async def get_property_recommendations(
        self,
        preferences: Dict[str, Any],
        location: str,
        budget_range: Optional[tuple[int, int]] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get property recommendations based on preferences"""
        try:
            # Create mock conversation with preferences
            conversation_history = [{
                "role": "user",
                "content": f"I'm looking for properties in {location} with preferences: {preferences}",
                "timestamp": time.time()
            }]
            
            context = {
                "location": location,
                "budget_range": budget_range,
                "preferences": preferences
            }
            
            result = await self.property_recommender.recommend_properties(
                conversation_history, {}, context, user_id, tenant_id
            )
            
            return result.get("properties", [])
            
        except Exception as e:
            logger.error(f"Property recommendations failed: {e}")
            return []
    
    async def analyze_market_trends(
        self,
        location: str,
        property_type: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get market analysis for specific location and property type"""
        try:
            context = {
                "location": location,
                "property_type": property_type
            }
            
            result = await self.market_analyzer.analyze_market_context(
                [], {}, context, user_id, tenant_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {"error": str(e)}
    
    async def suggest_next_actions(
        self,
        conversation_history: List[Dict[str, Any]],
        lead_score: float,
        user_profile: Dict[str, Any],
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Suggest next actions based on conversation and lead score"""
        try:
            actions = []
            
            # High-value lead actions
            if lead_score >= self.qualification_threshold:
                # Schedule appointment
                scheduling_result = await self.scheduler.suggest_appointments(
                    conversation_history, user_profile, {}, user_id, tenant_id
                )
                if scheduling_result and scheduling_result.get("suggestions"):
                    actions.extend(scheduling_result["suggestions"])
                
                # Property recommendations
                actions.append({
                    "type": "property_recommendations",
                    "priority": "high",
                    "description": "Send personalized property recommendations",
                    "action": "send_property_list"
                })
            
            # Follow-up recommendations
            follow_up_result = await self.follow_up_engine.recommend_follow_ups(
                conversation_history, user_profile, {"lead_score": lead_score}, user_id, tenant_id
            )
            if follow_up_result and follow_up_result.get("actions"):
                actions.extend(follow_up_result["actions"])
            
            return actions
            
        except Exception as e:
            logger.error(f"Next actions suggestion failed: {e}")
            return []
    
    async def get_lead_insights(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """Get lead insights and analytics"""
        try:
            insights = {
                "total_leads": 0,
                "qualified_leads": 0,
                "qualification_rate": 0.0,
                "avg_lead_score": 0.0,
                "top_interests": [],
                "conversion_funnel": {},
                "recommendations": []
            }
            
            # In production, this would query actual lead data
            # For now, return mock insights
            insights.update({
                "total_leads": 150,
                "qualified_leads": 45,
                "qualification_rate": 30.0,
                "avg_lead_score": 0.72,
                "top_interests": ["Single Family Homes", "Condos", "Investment Properties"],
                "conversion_funnel": {
                    "initial_contact": 150,
                    "qualified": 45,
                    "appointment_scheduled": 25,
                    "property_viewed": 15,
                    "offer_made": 8,
                    "closed": 3
                },
                "recommendations": [
                    "Focus on lead qualification optimization",
                    "Improve appointment scheduling conversion",
                    "Target single family home market"
                ]
            })
            
            return insights
            
        except Exception as e:
            logger.error(f"Lead insights generation failed: {e}")
            return {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get real estate intelligence performance metrics"""
        return {
            "qualification_threshold": self.qualification_threshold,
            "recommendation_count": self.recommendation_count,
            "components": {
                "lead_qualifier": "active",
                "property_recommender": "active", 
                "market_analyzer": "active",
                "scheduler": "active",
                "follow_up_engine": "active"
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for real estate intelligence engine"""
        health_status = {
            "status": "healthy",
            "service": "real_estate_intelligence",
            "components": {},
            "performance": self.get_performance_metrics(),
            "timestamp": time.time()
        }
        
        # Check components
        components = [
            ("lead_qualifier", self.lead_qualifier),
            ("property_recommender", self.property_recommender),
            ("market_analyzer", self.market_analyzer),
            ("scheduler", self.scheduler),
            ("follow_up_engine", self.follow_up_engine)
        ]
        
        for name, component in components:
            try:
                component_health = await component.health_check()
                health_status["components"][name] = component_health
            except Exception as e:
                health_status["components"][name] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
        
        return health_status