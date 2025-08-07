"""
AI Model Manager
Central management system for all AI models and their lifecycle
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum

from .versioning import ModelVersionManager
from .deployment import ModelDeploymentManager
from .optimization import ModelOptimizer
from .ab_testing import ABTestingManager
from ..config import ai_settings, MODEL_CONFIGS
from ...core.cache import get_redis_client

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """Model deployment status"""
    INACTIVE = "inactive"
    LOADING = "loading"
    ACTIVE = "active"
    TESTING = "testing"
    DEPRECATED = "deprecated"
    ERROR = "error"


@dataclass
class ModelInfo:
    """Model information and metadata"""
    model_id: str
    model_type: str
    version: str
    status: ModelStatus
    deployment_time: float
    performance_metrics: Dict[str, float]
    usage_statistics: Dict[str, int]
    configuration: Dict[str, Any]
    tags: List[str] = None
    description: str = ""


@dataclass
class ModelPerformance:
    """Model performance metrics"""
    accuracy: float
    latency_ms: float
    throughput_rps: float
    error_rate: float
    cost_per_request: float
    user_satisfaction: float
    last_updated: float


class AIModelManager:
    """
    Advanced AI Model Management System
    Handles model lifecycle, versioning, deployment, and optimization
    """
    
    def __init__(self):
        # Initialize management components
        self.version_manager = ModelVersionManager()
        self.deployment_manager = ModelDeploymentManager()
        self.optimizer = ModelOptimizer()
        self.ab_testing = ABTestingManager()
        
        # Model registry
        self.active_models: Dict[str, ModelInfo] = {}
        self.model_performance: Dict[str, ModelPerformance] = {}
        
        # Configuration
        self.redis_client = None
        self.auto_scaling_enabled = ai_settings.AUTO_SCALING_ENABLED
        self.ab_test_traffic_split = ai_settings.AB_TEST_TRAFFIC_SPLIT
        
        logger.info("AI Model Manager initialized")
    
    async def initialize(self):
        """Initialize all management components"""
        self.redis_client = await get_redis_client()
        
        await asyncio.gather(
            self.version_manager.initialize(),
            self.deployment_manager.initialize(),
            self.optimizer.initialize(),
            self.ab_testing.initialize()
        )
        
        # Load active models
        await self._load_active_models()
        
        logger.info("AI Model Manager components initialized")
    
    async def deploy_model(
        self,
        model_id: str,
        model_type: str,
        configuration: Dict[str, Any],
        version: Optional[str] = None,
        tenant_id: Optional[str] = None,
        deploy_strategy: str = "blue_green"
    ) -> Dict[str, Any]:
        """
        Deploy a new model or model version
        
        Args:
            model_id: Unique model identifier
            model_type: Type of model (gpt-4, whisper, etc.)
            configuration: Model configuration
            version: Model version (auto-generated if not provided)
            tenant_id: Tenant identifier for multi-tenant deployments
            deploy_strategy: Deployment strategy (blue_green, canary, rolling)
            
        Returns:
            Deployment result
        """
        try:
            # Generate version if not provided
            if not version:
                version = await self.version_manager.create_version(model_id, configuration)
            
            # Validate configuration
            validation_result = await self._validate_model_configuration(model_type, configuration)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid configuration: {validation_result['errors']}"
                }
            
            # Deploy model
            deployment_result = await self.deployment_manager.deploy(
                model_id, model_type, version, configuration, deploy_strategy, tenant_id
            )
            
            if deployment_result["success"]:
                # Create model info
                model_info = ModelInfo(
                    model_id=model_id,
                    model_type=model_type,
                    version=version,
                    status=ModelStatus.ACTIVE,
                    deployment_time=time.time(),
                    performance_metrics={},
                    usage_statistics={"requests": 0, "errors": 0},
                    configuration=configuration,
                    tags=configuration.get("tags", []),
                    description=configuration.get("description", "")
                )
                
                # Register model
                self.active_models[model_id] = model_info
                await self._save_model_registry()
                
                # Initialize performance tracking
                self.model_performance[model_id] = ModelPerformance(
                    accuracy=0.0,
                    latency_ms=0.0,
                    throughput_rps=0.0,
                    error_rate=0.0,
                    cost_per_request=0.0,
                    user_satisfaction=0.0,
                    last_updated=time.time()
                )
                
                logger.info(f"Model deployed successfully: {model_id} v{version}")
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"Model deployment failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_model(
        self,
        model_id: str,
        configuration: Dict[str, Any],
        update_strategy: str = "rolling"
    ) -> Dict[str, Any]:
        """Update existing model with new configuration"""
        try:
            if model_id not in self.active_models:
                return {"success": False, "error": "Model not found"}
            
            current_model = self.active_models[model_id]
            
            # Create new version
            new_version = await self.version_manager.create_version(
                model_id, configuration, current_model.version
            )
            
            # Deploy updated model
            result = await self.deploy_model(
                model_id, current_model.model_type, configuration, 
                new_version, deploy_strategy=update_strategy
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Model update failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def rollback_model(
        self,
        model_id: str,
        target_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rollback model to previous version"""
        try:
            if model_id not in self.active_models:
                return {"success": False, "error": "Model not found"}
            
            current_model = self.active_models[model_id]
            
            # Get target version (previous if not specified)
            if not target_version:
                target_version = await self.version_manager.get_previous_version(
                    model_id, current_model.version
                )
            
            if not target_version:
                return {"success": False, "error": "No previous version available"}
            
            # Get configuration for target version
            target_config = await self.version_manager.get_version_config(
                model_id, target_version
            )
            
            # Deploy target version
            result = await self.deployment_manager.deploy(
                model_id, current_model.model_type, target_version, 
                target_config, "blue_green"
            )
            
            if result["success"]:
                # Update model info
                current_model.version = target_version
                current_model.configuration = target_config
                current_model.deployment_time = time.time()
                
                await self._save_model_registry()
                
                logger.info(f"Model rolled back successfully: {model_id} to v{target_version}")
            
            return result
            
        except Exception as e:
            logger.error(f"Model rollback failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def start_ab_test(
        self,
        model_a_id: str,
        model_b_id: str,
        traffic_split: float = 0.5,
        test_duration_hours: int = 24,
        success_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Start A/B test between two models"""
        try:
            if success_metrics is None:
                success_metrics = ["accuracy", "latency_ms", "user_satisfaction"]
            
            test_result = await self.ab_testing.start_test(
                model_a_id, model_b_id, traffic_split, 
                test_duration_hours, success_metrics
            )
            
            return test_result
            
        except Exception as e:
            logger.error(f"A/B test start failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_model_recommendations(
        self,
        model_id: str,
        optimization_goal: str = "latency"
    ) -> Dict[str, Any]:
        """Get optimization recommendations for model"""
        try:
            if model_id not in self.active_models:
                return {"error": "Model not found"}
            
            model_info = self.active_models[model_id]
            performance = self.model_performance.get(model_id)
            
            recommendations = await self.optimizer.get_recommendations(
                model_info, performance, optimization_goal
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Model recommendations failed: {e}")
            return {"error": str(e)}
    
    async def update_model_performance(
        self,
        model_id: str,
        metrics: Dict[str, float]
    ):
        """Update model performance metrics"""
        try:
            if model_id not in self.model_performance:
                self.model_performance[model_id] = ModelPerformance(
                    accuracy=0.0, latency_ms=0.0, throughput_rps=0.0,
                    error_rate=0.0, cost_per_request=0.0, user_satisfaction=0.0,
                    last_updated=time.time()
                )
            
            performance = self.model_performance[model_id]
            
            # Update metrics
            for metric, value in metrics.items():
                if hasattr(performance, metric):
                    setattr(performance, metric, value)
            
            performance.last_updated = time.time()
            
            # Update usage statistics
            if model_id in self.active_models:
                self.active_models[model_id].usage_statistics["requests"] += 1
            
            # Check if auto-optimization is needed
            await self._check_auto_optimization(model_id)
            
        except Exception as e:
            logger.error(f"Performance update failed: {e}")
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get detailed model information"""
        return self.active_models.get(model_id)
    
    async def list_models(
        self,
        model_type: Optional[str] = None,
        status: Optional[ModelStatus] = None,
        tenant_id: Optional[str] = None
    ) -> List[ModelInfo]:
        """List models with optional filtering"""
        models = list(self.active_models.values())
        
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        
        if status:
            models = [m for m in models if m.status == status]
        
        # In production, would filter by tenant_id
        
        return models
    
    async def get_model_metrics(
        self,
        model_id: str,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """Get comprehensive model metrics"""
        try:
            if model_id not in self.active_models:
                return {"error": "Model not found"}
            
            model_info = self.active_models[model_id]
            performance = self.model_performance.get(model_id)
            
            metrics = {
                "model_info": asdict(model_info),
                "performance": asdict(performance) if performance else {},
                "deployment_health": await self.deployment_manager.get_health_status(model_id),
                "version_history": await self.version_manager.get_version_history(model_id),
                "usage_trends": await self._get_usage_trends(model_id, time_range_hours),
                "cost_analysis": await self._get_cost_analysis(model_id, time_range_hours)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Model metrics retrieval failed: {e}")
            return {"error": str(e)}
    
    async def _validate_model_configuration(
        self,
        model_type: str,
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate model configuration"""
        try:
            errors = []
            
            # Check required fields
            required_fields = ["model_id", "timeout", "max_tokens"]
            for field in required_fields:
                if field not in configuration:
                    errors.append(f"Missing required field: {field}")
            
            # Validate model type
            if model_type not in MODEL_CONFIGS:
                errors.append(f"Unsupported model type: {model_type}")
            
            # Validate timeout
            if "timeout" in configuration and configuration["timeout"] <= 0:
                errors.append("Timeout must be positive")
            
            # Validate max_tokens
            if "max_tokens" in configuration and configuration["max_tokens"] <= 0:
                errors.append("Max tokens must be positive")
            
            return {"valid": len(errors) == 0, "errors": errors}
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return {"valid": False, "errors": [str(e)]}
    
    async def _load_active_models(self):
        """Load active models from storage"""
        try:
            if self.redis_client:
                data = await self.redis_client.get("ai_models:registry")
                if data:
                    registry_data = json.loads(data)
                    for model_id, model_data in registry_data.items():
                        self.active_models[model_id] = ModelInfo(**model_data)
            
            logger.info(f"Loaded {len(self.active_models)} active models")
            
        except Exception as e:
            logger.error(f"Failed to load active models: {e}")
    
    async def _save_model_registry(self):
        """Save model registry to storage"""
        try:
            if self.redis_client:
                registry_data = {
                    model_id: asdict(model_info) 
                    for model_id, model_info in self.active_models.items()
                }
                
                await self.redis_client.set(
                    "ai_models:registry",
                    json.dumps(registry_data)
                )
            
        except Exception as e:
            logger.error(f"Failed to save model registry: {e}")
    
    async def _check_auto_optimization(self, model_id: str):
        """Check if model needs auto-optimization"""
        try:
            if not self.auto_scaling_enabled:
                return
            
            performance = self.model_performance.get(model_id)
            if not performance:
                return
            
            # Check performance thresholds
            needs_optimization = False
            
            if performance.latency_ms > 1000:  # 1 second threshold
                needs_optimization = True
                logger.info(f"Model {model_id} exceeds latency threshold")
            
            if performance.error_rate > 0.05:  # 5% error rate threshold
                needs_optimization = True
                logger.info(f"Model {model_id} exceeds error rate threshold")
            
            if needs_optimization:
                # Trigger optimization
                recommendations = await self.optimizer.get_recommendations(
                    self.active_models[model_id], performance, "auto"
                )
                
                # Apply automatic optimizations
                await self._apply_auto_optimizations(model_id, recommendations)
            
        except Exception as e:
            logger.error(f"Auto-optimization check failed: {e}")
    
    async def _apply_auto_optimizations(
        self,
        model_id: str,
        recommendations: Dict[str, Any]
    ):
        """Apply automatic optimizations"""
        try:
            auto_optimizations = recommendations.get("auto_apply", [])
            
            for optimization in auto_optimizations:
                if optimization["type"] == "scale_up":
                    await self.deployment_manager.scale_model(model_id, "up")
                elif optimization["type"] == "config_update":
                    await self.update_model(model_id, optimization["config"])
            
            logger.info(f"Applied {len(auto_optimizations)} auto-optimizations for {model_id}")
            
        except Exception as e:
            logger.error(f"Auto-optimization application failed: {e}")
    
    async def _get_usage_trends(
        self,
        model_id: str,
        time_range_hours: int
    ) -> Dict[str, Any]:
        """Get usage trends for model"""
        # In production, this would query actual usage data
        return {
            "requests_per_hour": [100, 120, 150, 180, 200],
            "error_rate_trend": [0.1, 0.08, 0.05, 0.03, 0.02],
            "latency_trend": [150, 140, 135, 130, 125],
            "cost_trend": [10.5, 12.0, 15.0, 18.0, 20.0]
        }
    
    async def _get_cost_analysis(
        self,
        model_id: str,
        time_range_hours: int
    ) -> Dict[str, Any]:
        """Get cost analysis for model"""
        # In production, this would calculate actual costs
        return {
            "total_cost": 156.78,
            "cost_per_request": 0.012,
            "cost_breakdown": {
                "compute": 120.50,
                "storage": 15.28,
                "network": 21.00
            },
            "cost_trends": "decreasing",
            "optimization_potential": 15.5
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for AI model manager"""
        health_status = {
            "status": "healthy",
            "service": "ai_model_manager",
            "active_models_count": len(self.active_models),
            "components": {},
            "auto_scaling_enabled": self.auto_scaling_enabled,
            "timestamp": time.time()
        }
        
        # Check components
        components = [
            ("version_manager", self.version_manager),
            ("deployment_manager", self.deployment_manager),
            ("optimizer", self.optimizer),
            ("ab_testing", self.ab_testing)
        ]
        
        for name, component in components:
            try:
                component_health = await component.health_check()
                health_status["components"][name] = component_health
            except Exception as e:
                health_status["components"][name] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
        
        # Check model statuses
        unhealthy_models = [
            model_id for model_id, model_info in self.active_models.items()
            if model_info.status == ModelStatus.ERROR
        ]
        
        if unhealthy_models:
            health_status["status"] = "degraded"
            health_status["unhealthy_models"] = unhealthy_models
        
        return health_status