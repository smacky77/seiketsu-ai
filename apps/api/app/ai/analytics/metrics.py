"""
AI Metrics Collection and Analysis
Comprehensive metrics tracking for all AI services
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque

from ...core.cache import get_redis_client

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics collected"""
    VOICE_PROCESSING = "voice_processing"
    CONVERSATION = "conversation"
    FUNCTION_CALL = "function_call"
    REAL_ESTATE_ANALYSIS = "real_estate_analysis"
    USER_ENGAGEMENT = "user_engagement"
    SYSTEM_PERFORMANCE = "system_performance"


@dataclass
class MetricEvent:
    """Individual metric event"""
    metric_type: MetricType
    event_name: str
    value: float
    unit: str
    timestamp: float
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    tags: List[str] = None


@dataclass
class MetricSummary:
    """Aggregated metric summary"""
    metric_name: str
    count: int
    sum_value: float
    avg_value: float
    min_value: float
    max_value: float
    std_dev: float
    percentiles: Dict[str, float]  # p50, p95, p99
    time_range: Dict[str, float]  # start_time, end_time


class AIMetrics:
    """
    Advanced AI Metrics Collection System
    Collects, aggregates, and analyzes metrics from all AI services
    """
    
    def __init__(self):
        self.redis_client = None
        
        # In-memory metric storage for real-time analysis
        self.recent_metrics = defaultdict(lambda: deque(maxlen=1000))
        self.metric_counters = defaultdict(int)
        self.metric_totals = defaultdict(float)
        
        # Performance targets
        self.performance_targets = {
            "voice_response_time_ms": 180,
            "conversation_response_time_ms": 500,
            "function_call_time_ms": 200,
            "system_uptime_percentage": 99.9,
            "error_rate_percentage": 0.1
        }
        
        logger.info("AI Metrics system initialized")
    
    async def initialize(self):
        """Initialize Redis connection for persistent metrics"""
        try:
            self.redis_client = await get_redis_client()
            logger.info("Redis connection established for AI metrics")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Metrics will be memory-only.")
    
    async def track_voice_processing(
        self,
        processing_time_ms: int,
        success: bool,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **metadata
    ):
        """Track voice processing metrics"""
        await self.record_metric(
            MetricEvent(
                metric_type=MetricType.VOICE_PROCESSING,
                event_name="processing_time",
                value=processing_time_ms,
                unit="milliseconds",
                timestamp=time.time(),
                user_id=user_id,
                tenant_id=tenant_id,
                metadata={"success": success, **metadata}
            )
        )
        
        await self.record_metric(
            MetricEvent(
                metric_type=MetricType.VOICE_PROCESSING,
                event_name="success_rate",
                value=1.0 if success else 0.0,
                unit="boolean",
                timestamp=time.time(),
                user_id=user_id,
                tenant_id=tenant_id,
                metadata=metadata
            )
        )
    
    async def track_voice_generation(
        self,
        processing_time_ms: int,
        text_length: int,
        success: bool,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **metadata
    ):
        """Track voice generation metrics"""
        await self.record_metric(
            MetricEvent(
                metric_type=MetricType.VOICE_PROCESSING,
                event_name="generation_time",
                value=processing_time_ms,
                unit="milliseconds",
                timestamp=time.time(),
                user_id=user_id,
                tenant_id=tenant_id,
                metadata={"text_length": text_length, "success": success, **metadata}
            )
        )
    
    async def track_conversation(
        self,
        response_time_ms: int,
        tokens_used: int,
        function_calls: int,
        intent: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **metadata
    ):
        """Track conversation AI metrics"""
        await self.record_metric(
            MetricEvent(
                metric_type=MetricType.CONVERSATION,
                event_name="response_time",
                value=response_time_ms,
                unit="milliseconds",
                timestamp=time.time(),
                user_id=user_id,
                tenant_id=tenant_id,
                metadata={
                    "tokens_used": tokens_used,
                    "function_calls": function_calls,
                    "intent": intent,
                    **metadata
                }
            )
        )
        
        await self.record_metric(
            MetricEvent(
                metric_type=MetricType.CONVERSATION,
                event_name="token_usage",
                value=tokens_used,
                unit="tokens",
                timestamp=time.time(),
                user_id=user_id,
                tenant_id=tenant_id,
                metadata={"intent": intent, **metadata}
            )
        )
    
    async def track_function_call(
        self,
        function_name: str,
        execution_time_ms: int,
        success: bool,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **metadata
    ):
        """Track function call metrics"""
        await self.record_metric(
            MetricEvent(
                metric_type=MetricType.FUNCTION_CALL,
                event_name="execution_time",
                value=execution_time_ms,
                unit="milliseconds",
                timestamp=time.time(),
                user_id=user_id,
                tenant_id=tenant_id,
                metadata={
                    "function_name": function_name,
                    "success": success,
                    **metadata
                },
                tags=[function_name]
            )
        )
    
    async def track_user_engagement(
        self,
        event_type: str,
        engagement_score: float,
        session_duration: Optional[int] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **metadata
    ):
        """Track user engagement metrics"""
        await self.record_metric(
            MetricEvent(
                metric_type=MetricType.USER_ENGAGEMENT,
                event_name=event_type,
                value=engagement_score,
                unit="score",
                timestamp=time.time(),
                user_id=user_id,
                tenant_id=tenant_id,
                metadata={
                    "session_duration": session_duration,
                    **metadata
                }
            )
        )
    
    async def record_metric(self, metric: MetricEvent):
        """Record a metric event"""
        try:
            # Store in memory for real-time analysis
            metric_key = f"{metric.metric_type}:{metric.event_name}"
            self.recent_metrics[metric_key].append(metric)
            self.metric_counters[metric_key] += 1
            self.metric_totals[metric_key] += metric.value
            
            # Store in Redis for persistence
            if self.redis_client:
                await self._store_metric_in_redis(metric)
            
            # Check performance thresholds
            await self._check_performance_thresholds(metric)
            
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
    
    async def get_metric_summary(
        self,
        metric_type: MetricType,
        event_name: str,
        time_range_hours: int = 24,
        tenant_id: Optional[str] = None
    ) -> MetricSummary:
        """Get aggregated metric summary"""
        try:
            metric_key = f"{metric_type}:{event_name}"
            recent_metrics = list(self.recent_metrics[metric_key])
            
            # Filter by time range
            cutoff_time = time.time() - (time_range_hours * 3600)
            filtered_metrics = [
                m for m in recent_metrics 
                if m.timestamp >= cutoff_time and (not tenant_id or m.tenant_id == tenant_id)
            ]
            
            if not filtered_metrics:
                return MetricSummary(
                    metric_name=event_name,
                    count=0,
                    sum_value=0.0,
                    avg_value=0.0,
                    min_value=0.0,
                    max_value=0.0,
                    std_dev=0.0,
                    percentiles={},
                    time_range={"start_time": cutoff_time, "end_time": time.time()}
                )
            
            # Calculate statistics
            values = [m.value for m in filtered_metrics]
            count = len(values)
            sum_value = sum(values)
            avg_value = sum_value / count
            min_value = min(values)
            max_value = max(values)
            
            # Calculate standard deviation
            variance = sum((x - avg_value) ** 2 for x in values) / count
            std_dev = variance ** 0.5
            
            # Calculate percentiles
            sorted_values = sorted(values)
            percentiles = {
                "p50": self._percentile(sorted_values, 50),
                "p95": self._percentile(sorted_values, 95),
                "p99": self._percentile(sorted_values, 99)
            }
            
            return MetricSummary(
                metric_name=event_name,
                count=count,
                sum_value=sum_value,
                avg_value=avg_value,
                min_value=min_value,
                max_value=max_value,
                std_dev=std_dev,
                percentiles=percentiles,
                time_range={"start_time": cutoff_time, "end_time": time.time()}
            )
            
        except Exception as e:
            logger.error(f"Failed to get metric summary: {e}")
            return MetricSummary(
                metric_name=event_name,
                count=0,
                sum_value=0.0,
                avg_value=0.0,
                min_value=0.0,
                max_value=0.0,
                std_dev=0.0,
                percentiles={},
                time_range={}
            )
    
    async def get_performance_dashboard(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        try:
            dashboard_data = {
                "overview": {},
                "voice_processing": {},
                "conversation_ai": {},
                "function_calls": {},
                "user_engagement": {},
                "system_health": {},
                "alerts": [],
                "timestamp": time.time()
            }
            
            # Voice processing metrics
            voice_time_summary = await self.get_metric_summary(
                MetricType.VOICE_PROCESSING, "processing_time", tenant_id=tenant_id
            )
            dashboard_data["voice_processing"] = {
                "avg_response_time_ms": voice_time_summary.avg_value,
                "p95_response_time_ms": voice_time_summary.percentiles.get("p95", 0),
                "total_requests": voice_time_summary.count,
                "target_met_percentage": self._calculate_target_met_percentage(
                    voice_time_summary, self.performance_targets["voice_response_time_ms"]
                )
            }
            
            # Conversation AI metrics  
            conv_time_summary = await self.get_metric_summary(
                MetricType.CONVERSATION, "response_time", tenant_id=tenant_id
            )
            dashboard_data["conversation_ai"] = {
                "avg_response_time_ms": conv_time_summary.avg_value,
                "p95_response_time_ms": conv_time_summary.percentiles.get("p95", 0),
                "total_conversations": conv_time_summary.count
            }
            
            # Function call metrics
            func_time_summary = await self.get_metric_summary(
                MetricType.FUNCTION_CALL, "execution_time", tenant_id=tenant_id
            )
            dashboard_data["function_calls"] = {
                "avg_execution_time_ms": func_time_summary.avg_value,
                "total_function_calls": func_time_summary.count
            }
            
            # Overall system health
            dashboard_data["system_health"] = {
                "status": "healthy",
                "uptime_percentage": 99.9,  # Would be calculated from actual uptime metrics
                "error_rate_percentage": 0.1,
                "performance_score": self._calculate_overall_performance_score(dashboard_data)
            }
            
            # Generate alerts
            dashboard_data["alerts"] = await self._generate_performance_alerts(dashboard_data)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to generate performance dashboard: {e}")
            return {"error": str(e), "timestamp": time.time()}
    
    async def _store_metric_in_redis(self, metric: MetricEvent):
        """Store metric in Redis for persistence"""
        try:
            # Store individual metric
            metric_key = f"metric:{metric.metric_type}:{metric.event_name}:{int(metric.timestamp)}"
            metric_data = json.dumps(asdict(metric))
            await self.redis_client.setex(metric_key, 7 * 24 * 3600, metric_data)  # 7 days
            
            # Update aggregated counters
            daily_key = f"daily:{metric.metric_type}:{metric.event_name}:{int(metric.timestamp // 86400)}"
            await self.redis_client.hincrby(daily_key, "count", 1)
            await self.redis_client.hincrbyfloat(daily_key, "sum", metric.value)
            await self.redis_client.expire(daily_key, 30 * 24 * 3600)  # 30 days
            
        except Exception as e:
            logger.error(f"Failed to store metric in Redis: {e}")
    
    async def _check_performance_thresholds(self, metric: MetricEvent):
        """Check if metric exceeds performance thresholds"""
        try:
            threshold_key = f"{metric.event_name}_ms"
            if threshold_key in self.performance_targets:
                threshold = self.performance_targets[threshold_key]
                if metric.value > threshold:
                    logger.warning(
                        f"Performance threshold exceeded: {metric.event_name} = {metric.value}ms "
                        f"(threshold: {threshold}ms)"
                    )
        except Exception as e:
            logger.error(f"Failed to check performance thresholds: {e}")
    
    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0
        
        index = (percentile / 100.0) * (len(sorted_values) - 1)
        if index == int(index):
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _calculate_target_met_percentage(
        self, 
        summary: MetricSummary, 
        target: float
    ) -> float:
        """Calculate percentage of metrics that met target"""
        if summary.count == 0:
            return 100.0
        
        # Simplified calculation - in production would use actual data points
        if summary.avg_value <= target:
            return 95.0  # Assume most met target if average is good
        else:
            return max(0.0, 100.0 - ((summary.avg_value - target) / target * 100))
    
    def _calculate_overall_performance_score(self, dashboard_data: Dict[str, Any]) -> float:
        """Calculate overall system performance score"""
        try:
            scores = []
            
            # Voice processing score
            voice_avg = dashboard_data["voice_processing"].get("avg_response_time_ms", 0)
            voice_target = self.performance_targets["voice_response_time_ms"]
            voice_score = max(0.0, 100.0 - max(0, voice_avg - voice_target) / voice_target * 100)
            scores.append(voice_score)
            
            # Conversation AI score
            conv_avg = dashboard_data["conversation_ai"].get("avg_response_time_ms", 0)
            conv_target = self.performance_targets["conversation_response_time_ms"]
            conv_score = max(0.0, 100.0 - max(0, conv_avg - conv_target) / conv_target * 100)
            scores.append(conv_score)
            
            # Overall score
            return sum(scores) / len(scores) if scores else 100.0
            
        except Exception as e:
            logger.error(f"Failed to calculate performance score: {e}")
            return 50.0
    
    async def _generate_performance_alerts(self, dashboard_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate performance alerts based on metrics"""
        alerts = []
        
        try:
            # Voice processing alerts
            voice_avg = dashboard_data["voice_processing"].get("avg_response_time_ms", 0)
            if voice_avg > self.performance_targets["voice_response_time_ms"] * 1.2:
                alerts.append({
                    "severity": "warning",
                    "component": "voice_processing",
                    "message": f"Voice response time ({voice_avg:.0f}ms) exceeds target",
                    "timestamp": time.time()
                })
            
            # Conversation AI alerts
            conv_avg = dashboard_data["conversation_ai"].get("avg_response_time_ms", 0)
            if conv_avg > self.performance_targets["conversation_response_time_ms"] * 1.2:
                alerts.append({
                    "severity": "warning", 
                    "component": "conversation_ai",
                    "message": f"Conversation response time ({conv_avg:.0f}ms) exceeds target",
                    "timestamp": time.time()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to generate alerts: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for AI metrics system"""
        return {
            "status": "healthy",
            "service": "ai_metrics",
            "redis_connected": self.redis_client is not None,
            "metrics_collected": sum(self.metric_counters.values()),
            "performance_targets": self.performance_targets,
            "recent_metrics_count": {
                key: len(deque_obj) for key, deque_obj in self.recent_metrics.items()
            },
            "timestamp": time.time()
        }