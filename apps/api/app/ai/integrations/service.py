"""
AI Integration Service
Central orchestrator for all AI-powered integrations and automations
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .crm_integration import CRMIntegration
from .workflow_automation import WorkflowAutomation
from .webhook_handler import WebhookHandler
from .data_sync import DataSynchronizationService
from ..config import ai_settings

logger = logging.getLogger(__name__)


@dataclass
class IntegrationResult:
    """Result of integration operation"""
    success: bool
    integration_type: str
    action: str
    data: Dict[str, Any] = None
    processing_time_ms: int = 0
    error: Optional[str] = None


class AIIntegrationService:
    """
    Advanced AI Integration Service
    Orchestrates all enterprise integrations with AI-powered automation
    """
    
    def __init__(self):
        # Initialize integration components
        self.crm_integration = CRMIntegration()
        self.workflow_automation = WorkflowAutomation()
        self.webhook_handler = WebhookHandler()
        self.data_sync = DataSynchronizationService()
        
        # Configuration
        self.sync_interval = ai_settings.CRM_SYNC_INTERVAL_MINUTES
        self.auto_sync_enabled = True
        
        # Integration status tracking
        self.integration_health = {}
        self.last_sync_times = {}
        
        logger.info("AI Integration Service initialized")
    
    async def initialize(self):
        """Initialize all integration components"""
        await asyncio.gather(
            self.crm_integration.initialize(),
            self.workflow_automation.initialize(),
            self.webhook_handler.initialize(),
            self.data_sync.initialize()
        )
        
        # Start background sync processes
        if self.auto_sync_enabled:
            asyncio.create_task(self._background_sync_process())
        
        logger.info("AI Integration Service components initialized")
    
    async def process_conversation_completion(
        self,
        conversation_data: Dict[str, Any],
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> List[IntegrationResult]:
        """
        Process completed conversation with all relevant integrations
        
        Args:
            conversation_data: Complete conversation data and analysis
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            List of integration results
        """
        start_time = time.time()
        results = []
        
        try:
            # Extract key data
            lead_score = conversation_data.get("lead_score", 0.0)
            intent = conversation_data.get("intent")
            properties_discussed = conversation_data.get("properties", [])
            
            # Run integrations in parallel
            integration_tasks = []
            
            # CRM integration - update lead information
            if lead_score > 0.5:  # Qualified lead threshold
                integration_tasks.append(
                    self._execute_crm_integration(conversation_data, user_id, tenant_id)
                )
            
            # Workflow automation - trigger follow-up actions
            if conversation_data.get("follow_up_actions"):
                integration_tasks.append(
                    self._execute_workflow_automation(conversation_data, user_id, tenant_id)
                )
            
            # Data synchronization - sync conversation insights
            integration_tasks.append(
                self._execute_data_sync(conversation_data, user_id, tenant_id)
            )
            
            # Execute all integrations
            if integration_tasks:
                integration_results = await asyncio.gather(
                    *integration_tasks, return_exceptions=True
                )
                
                for result in integration_results:
                    if isinstance(result, Exception):
                        logger.error(f"Integration failed: {result}")
                        results.append(IntegrationResult(
                            success=False,
                            integration_type="unknown",
                            action="process_conversation",
                            error=str(result)
                        ))
                    else:
                        results.append(result)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Conversation integrations completed in {processing_time_ms}ms: {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Conversation integration processing failed: {e}")
            return [IntegrationResult(
                success=False,
                integration_type="ai_integration_service",
                action="process_conversation",
                error=str(e)
            )]
    
    async def sync_lead_data(
        self,
        lead_data: Dict[str, Any],
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> IntegrationResult:
        """Sync lead data to CRM systems"""
        try:
            result = await self.crm_integration.sync_lead(lead_data, user_id, tenant_id)
            return result
            
        except Exception as e:
            logger.error(f"Lead data sync failed: {e}")
            return IntegrationResult(
                success=False,
                integration_type="crm",
                action="sync_lead",
                error=str(e)
            )
    
    async def trigger_workflow(
        self,
        workflow_type: str,
        trigger_data: Dict[str, Any],
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> IntegrationResult:
        """Trigger automated workflow"""
        try:
            result = await self.workflow_automation.trigger_workflow(
                workflow_type, trigger_data, user_id, tenant_id
            )
            return result
            
        except Exception as e:
            logger.error(f"Workflow trigger failed: {e}")
            return IntegrationResult(
                success=False,
                integration_type="workflow",
                action="trigger_workflow",
                error=str(e)
            )
    
    async def handle_webhook(
        self,
        webhook_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        tenant_id: Optional[str] = None
    ) -> IntegrationResult:
        """Handle incoming webhook with AI processing"""
        try:
            result = await self.webhook_handler.process_webhook(
                webhook_type, payload, headers, tenant_id
            )
            return result
            
        except Exception as e:
            logger.error(f"Webhook handling failed: {e}")
            return IntegrationResult(
                success=False,
                integration_type="webhook",
                action="handle_webhook",
                error=str(e)
            )
    
    async def sync_property_data(
        self,
        property_data: List[Dict[str, Any]],
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> IntegrationResult:
        """Sync property data across systems"""
        try:
            result = await self.data_sync.sync_properties(
                property_data, user_id, tenant_id
            )
            return result
            
        except Exception as e:
            logger.error(f"Property data sync failed: {e}")
            return IntegrationResult(
                success=False,
                integration_type="data_sync",
                action="sync_properties",
                error=str(e)
            )
    
    async def get_integration_status(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive integration status"""
        try:
            status = {
                "overall_health": "healthy",
                "integrations": {},
                "sync_status": {},
                "last_activity": {},
                "error_summary": {},
                "timestamp": time.time()
            }
            
            # Check component health
            components = [
                ("crm", self.crm_integration),
                ("workflow", self.workflow_automation),
                ("webhook", self.webhook_handler),
                ("data_sync", self.data_sync)
            ]
            
            for name, component in components:
                try:
                    health = await component.health_check()
                    status["integrations"][name] = health
                    
                    if health.get("status") != "healthy":
                        status["overall_health"] = "degraded"
                        
                except Exception as e:
                    status["integrations"][name] = {"status": "error", "error": str(e)}
                    status["overall_health"] = "degraded"
            
            # Get sync status
            status["sync_status"] = {
                "auto_sync_enabled": self.auto_sync_enabled,
                "sync_interval_minutes": self.sync_interval,
                "last_sync_times": dict(self.last_sync_times)
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Integration status check failed: {e}")
            return {"error": str(e), "timestamp": time.time()}
    
    async def _execute_crm_integration(
        self,
        conversation_data: Dict[str, Any],
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> IntegrationResult:
        """Execute CRM integration for conversation"""
        start_time = time.time()
        
        try:
            # Extract lead information
            lead_data = {
                "user_id": user_id,
                "lead_score": conversation_data.get("lead_score", 0.0),
                "intent": conversation_data.get("intent"),
                "interests": conversation_data.get("interests", []),
                "budget_range": conversation_data.get("budget_range"),
                "location_preferences": conversation_data.get("location_preferences", []),
                "conversation_summary": conversation_data.get("summary", ""),
                "contact_preferences": conversation_data.get("contact_preferences", {}),
                "next_steps": conversation_data.get("follow_up_actions", [])
            }
            
            # Sync to CRM
            sync_result = await self.crm_integration.sync_lead(lead_data, user_id, tenant_id)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return IntegrationResult(
                success=sync_result["success"],
                integration_type="crm",
                action="sync_conversation_lead",
                data=sync_result.get("data", {}),
                processing_time_ms=processing_time_ms,
                error=sync_result.get("error")
            )
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            return IntegrationResult(
                success=False,
                integration_type="crm",
                action="sync_conversation_lead",
                processing_time_ms=processing_time_ms,
                error=str(e)
            )
    
    async def _execute_workflow_automation(
        self,
        conversation_data: Dict[str, Any],
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> IntegrationResult:
        """Execute workflow automation for conversation"""
        start_time = time.time()
        
        try:
            follow_up_actions = conversation_data.get("follow_up_actions", [])
            
            if not follow_up_actions:
                return IntegrationResult(
                    success=True,
                    integration_type="workflow",
                    action="no_actions_needed",
                    processing_time_ms=0
                )
            
            # Trigger workflows for each action
            workflow_results = []
            for action in follow_up_actions:
                result = await self.workflow_automation.trigger_workflow(
                    action.get("type", "general"),
                    {
                        "user_id": user_id,
                        "action_data": action,
                        "conversation_context": {
                            "lead_score": conversation_data.get("lead_score"),
                            "intent": conversation_data.get("intent")
                        }
                    },
                    user_id,
                    tenant_id
                )
                workflow_results.append(result)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return IntegrationResult(
                success=all(r["success"] for r in workflow_results),
                integration_type="workflow",
                action="trigger_follow_up_workflows",
                data={"workflows_triggered": len(workflow_results), "results": workflow_results},
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            return IntegrationResult(
                success=False,
                integration_type="workflow",
                action="trigger_follow_up_workflows",
                processing_time_ms=processing_time_ms,
                error=str(e)
            )
    
    async def _execute_data_sync(
        self,
        conversation_data: Dict[str, Any],
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> IntegrationResult:
        """Execute data synchronization for conversation"""
        start_time = time.time()
        
        try:
            # Prepare sync data
            sync_data = {
                "conversation_insights": {
                    "lead_score": conversation_data.get("lead_score"),
                    "intent": conversation_data.get("intent"),
                    "sentiment": conversation_data.get("sentiment"),
                    "engagement_level": conversation_data.get("engagement_level"),
                    "topics_discussed": conversation_data.get("topics", []),
                    "properties_mentioned": conversation_data.get("properties", [])
                },
                "user_profile_updates": conversation_data.get("user_profile_updates", {}),
                "preferences_extracted": conversation_data.get("preferences", {}),
                "timestamp": time.time()
            }
            
            # Sync conversation insights
            sync_result = await self.data_sync.sync_conversation_insights(
                sync_data, user_id, tenant_id
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return IntegrationResult(
                success=sync_result["success"],
                integration_type="data_sync",
                action="sync_conversation_insights",
                data=sync_result.get("data", {}),
                processing_time_ms=processing_time_ms,
                error=sync_result.get("error")
            )
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            return IntegrationResult(
                success=False,
                integration_type="data_sync",
                action="sync_conversation_insights",
                processing_time_ms=processing_time_ms,
                error=str(e)
            )
    
    async def _background_sync_process(self):
        """Background process for periodic data synchronization"""
        logger.info("Starting background sync process")
        
        while True:
            try:
                # Wait for sync interval
                await asyncio.sleep(self.sync_interval * 60)
                
                # Perform periodic sync operations
                sync_tasks = [
                    self.data_sync.periodic_sync(),
                    self.crm_integration.periodic_sync(),
                ]
                
                await asyncio.gather(*sync_tasks, return_exceptions=True)
                
                # Update last sync time
                self.last_sync_times["periodic_sync"] = time.time()
                
                logger.debug("Background sync completed")
                
            except Exception as e:
                logger.error(f"Background sync failed: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for AI integration service"""
        health_status = {
            "status": "healthy",
            "service": "ai_integration_service",
            "components": {},
            "sync_enabled": self.auto_sync_enabled,
            "sync_interval_minutes": self.sync_interval,
            "timestamp": time.time()
        }
        
        # Check components
        components = [
            ("crm_integration", self.crm_integration),
            ("workflow_automation", self.workflow_automation),
            ("webhook_handler", self.webhook_handler),
            ("data_sync", self.data_sync)
        ]
        
        for name, component in components:
            try:
                component_health = await component.health_check()
                health_status["components"][name] = component_health
                
                if component_health.get("status") != "healthy":
                    health_status["status"] = "degraded"
                    
            except Exception as e:
                health_status["components"][name] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
        
        return health_status