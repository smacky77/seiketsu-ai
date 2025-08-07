"""
Voice Analytics Service for monitoring and optimizing voice performance
Integrates with 21dev.ai for comprehensive voice metrics tracking
"""
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

from app.services.twentyonedev_service import analytics_service
from app.core.config import settings

logger = logging.getLogger("seiketsu.voice_analytics")

@dataclass
class VoiceMetric:
    """Individual voice processing metric"""
    timestamp: datetime
    voice_agent_id: str
    operation_type: str  # synthesis, streaming, cache_hit, etc.
    processing_time_ms: float
    text_length: int
    language: str
    cached: bool
    quality_score: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analytics"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class PerformanceWindow:
    """Performance metrics for a time window"""
    window_start: datetime
    window_end: datetime
    total_requests: int
    successful_requests: int
    cache_hits: int
    average_processing_time_ms: float
    p95_processing_time_ms: float
    p99_processing_time_ms: float
    average_quality_score: float
    error_rate: float
    languages_used: List[str]
    top_voice_agents: List[Dict[str, Any]]

class VoiceAnalyticsService:
    """
    Service for collecting, analyzing, and reporting voice performance metrics
    """
    
    def __init__(self):
        self.metrics_buffer = deque(maxlen=10000)  # Keep last 10k metrics in memory
        self.agent_metrics = defaultdict(list)  # Metrics per agent
        self.performance_windows = deque(maxlen=144)  # 24 hours of 10-minute windows
        
        # Real-time metrics
        self.current_metrics = {
            "requests_per_minute": deque(maxlen=60),
            "response_times": deque(maxlen=1000),
            "error_count": 0,
            "cache_hit_rate": 0.0
        }
        
        # Performance thresholds
        self.thresholds = {
            "max_response_time_ms": 2000,
            "min_quality_score": 0.8,
            "max_error_rate": 0.05,
            "target_cache_hit_rate": 0.3
        }
        
        # Analytics task
        self._analytics_task = None
        self._window_processing_task = None
    
    async def initialize(self):
        """Initialize analytics service"""
        try:
            # Start background tasks
            self._analytics_task = asyncio.create_task(self._periodic_analytics())
            self._window_processing_task = asyncio.create_task(self._process_time_windows())
            
            logger.info("Voice analytics service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice analytics: {e}")
            raise
    
    async def record_metric(self, metric: VoiceMetric):
        """Record a voice processing metric"""
        try:
            # Add to buffer
            self.metrics_buffer.append(metric)
            
            # Add to agent-specific metrics
            self.agent_metrics[metric.voice_agent_id].append(metric)
            
            # Keep only recent metrics per agent (last 1000)
            if len(self.agent_metrics[metric.voice_agent_id]) > 1000:
                self.agent_metrics[metric.voice_agent_id].pop(0)
            
            # Update real-time metrics
            self._update_realtime_metrics(metric)
            
            # Send to 21dev.ai for immediate processing
            await self._send_metric_to_analytics(metric)
            
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
    
    async def get_performance_summary(
        self,
        time_range_hours: int = 24,
        voice_agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance summary for specified time range"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            # Filter metrics by time and agent
            filtered_metrics = [
                m for m in self.metrics_buffer
                if m.timestamp >= cutoff_time and (
                    voice_agent_id is None or m.voice_agent_id == voice_agent_id
                )
            ]
            
            if not filtered_metrics:
                return {"error": "No metrics found for specified criteria"}
            
            # Calculate summary statistics
            processing_times = [m.processing_time_ms for m in filtered_metrics if not m.error]
            quality_scores = [m.quality_score for m in filtered_metrics if not m.error]
            cache_hits = sum(1 for m in filtered_metrics if m.cached)
            errors = sum(1 for m in filtered_metrics if m.error)
            
            # Language distribution
            language_dist = defaultdict(int)
            for m in filtered_metrics:
                language_dist[m.language] += 1
            
            # Agent distribution
            agent_dist = defaultdict(int)
            for m in filtered_metrics:
                agent_dist[m.voice_agent_id] += 1
            
            summary = {
                "time_range_hours": time_range_hours,
                "total_requests": len(filtered_metrics),
                "successful_requests": len(filtered_metrics) - errors,
                "error_rate": errors / len(filtered_metrics) if filtered_metrics else 0,
                "cache_hit_rate": cache_hits / len(filtered_metrics) if filtered_metrics else 0,
                "performance": {
                    "average_response_time_ms": statistics.mean(processing_times) if processing_times else 0,
                    "median_response_time_ms": statistics.median(processing_times) if processing_times else 0,
                    "p95_response_time_ms": self._percentile(processing_times, 95) if processing_times else 0,
                    "p99_response_time_ms": self._percentile(processing_times, 99) if processing_times else 0,
                    "max_response_time_ms": max(processing_times) if processing_times else 0,
                    "min_response_time_ms": min(processing_times) if processing_times else 0
                },
                "quality": {
                    "average_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
                    "min_quality_score": min(quality_scores) if quality_scores else 0,
                    "quality_scores_below_threshold": sum(
                        1 for q in quality_scores 
                        if q < self.thresholds["min_quality_score"]
                    )
                },
                "distribution": {
                    "languages": dict(language_dist),
                    "voice_agents": dict(sorted(agent_dist.items(), key=lambda x: x[1], reverse=True)[:10])
                },
                "health_indicators": self._calculate_health_indicators(filtered_metrics)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {"error": str(e)}
    
    async def get_agent_performance(self, voice_agent_id: str) -> Dict[str, Any]:
        """Get detailed performance metrics for a specific agent"""
        try:
            agent_metrics = self.agent_metrics.get(voice_agent_id, [])
            if not agent_metrics:
                return {"error": f"No metrics found for agent {voice_agent_id}"}
            
            # Recent metrics (last 24 hours)
            cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_metrics = [m for m in agent_metrics if m.timestamp >= cutoff]
            
            # Calculate trends
            hourly_trends = self._calculate_hourly_trends(recent_metrics)
            
            # Performance by language
            lang_performance = defaultdict(list)
            for m in recent_metrics:
                if not m.error:
                    lang_performance[m.language].append(m.processing_time_ms)
            
            lang_stats = {
                lang: {
                    "avg_response_time_ms": statistics.mean(times),
                    "request_count": len(times)
                }
                for lang, times in lang_performance.items()
            }
            
            return {
                "voice_agent_id": voice_agent_id,
                "total_metrics": len(agent_metrics),
                "recent_metrics_24h": len(recent_metrics),
                "performance_trends": hourly_trends,
                "language_performance": lang_stats,
                "recommendations": self._generate_agent_recommendations(recent_metrics)
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent performance: {e}")
            return {"error": str(e)}
    
    async def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect performance anomalies and issues"""
        try:
            anomalies = []
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            recent_metrics = [m for m in self.metrics_buffer if m.timestamp >= recent_cutoff]
            
            if not recent_metrics:
                return anomalies
            
            # Check for high response times
            slow_requests = [m for m in recent_metrics if m.processing_time_ms > self.thresholds["max_response_time_ms"]]
            if len(slow_requests) > len(recent_metrics) * 0.1:  # More than 10% slow
                anomalies.append({
                    "type": "high_response_time",
                    "severity": "warning",
                    "description": f"{len(slow_requests)} requests took longer than {self.thresholds['max_response_time_ms']}ms",
                    "affected_requests": len(slow_requests),
                    "threshold": self.thresholds["max_response_time_ms"]
                })
            
            # Check for low quality scores
            low_quality = [m for m in recent_metrics if m.quality_score < self.thresholds["min_quality_score"]]
            if len(low_quality) > len(recent_metrics) * 0.05:  # More than 5% low quality
                anomalies.append({
                    "type": "low_quality_score",
                    "severity": "warning",
                    "description": f"{len(low_quality)} requests had quality scores below {self.thresholds['min_quality_score']}",
                    "affected_requests": len(low_quality),
                    "threshold": self.thresholds["min_quality_score"]
                })
            
            # Check error rate
            errors = [m for m in recent_metrics if m.error]
            error_rate = len(errors) / len(recent_metrics)
            if error_rate > self.thresholds["max_error_rate"]:
                anomalies.append({
                    "type": "high_error_rate",
                    "severity": "critical",
                    "description": f"Error rate of {error_rate:.2%} exceeds threshold of {self.thresholds['max_error_rate']:.2%}",
                    "error_count": len(errors),
                    "total_requests": len(recent_metrics)
                })
            
            # Check cache hit rate
            cache_hits = sum(1 for m in recent_metrics if m.cached)
            cache_hit_rate = cache_hits / len(recent_metrics)
            if cache_hit_rate < self.thresholds["target_cache_hit_rate"]:
                anomalies.append({
                    "type": "low_cache_hit_rate",
                    "severity": "info",
                    "description": f"Cache hit rate of {cache_hit_rate:.2%} is below target of {self.thresholds['target_cache_hit_rate']:.2%}",
                    "cache_hits": cache_hits,
                    "total_requests": len(recent_metrics)
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return []
    
    def _update_realtime_metrics(self, metric: VoiceMetric):
        """Update real-time metrics"""
        try:
            # Update requests per minute counter
            current_minute = datetime.utcnow().replace(second=0, microsecond=0)
            if not self.current_metrics["requests_per_minute"] or \
               self.current_metrics["requests_per_minute"][-1][0] != current_minute:
                self.current_metrics["requests_per_minute"].append([current_minute, 1])
            else:
                self.current_metrics["requests_per_minute"][-1][1] += 1
            
            # Update response times
            if not metric.error:
                self.current_metrics["response_times"].append(metric.processing_time_ms)
            
            # Update error count
            if metric.error:
                self.current_metrics["error_count"] += 1
            
            # Update cache hit rate
            cache_hits = sum(1 for m in list(self.metrics_buffer)[-100:] if m.cached)
            total_recent = min(len(self.metrics_buffer), 100)
            self.current_metrics["cache_hit_rate"] = cache_hits / total_recent if total_recent > 0 else 0
            
        except Exception as e:
            logger.error(f"Failed to update realtime metrics: {e}")
    
    async def _send_metric_to_analytics(self, metric: VoiceMetric):
        """Send metric to 21dev.ai analytics"""
        try:
            if not settings.TWENTYONEDEV_API_KEY:
                return
            
            await analytics_service.track_event("voice_metric", metric.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to send metric to analytics: {e}")
    
    async def _periodic_analytics(self):
        """Periodic analytics processing"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Send aggregated metrics
                summary = await self.get_performance_summary(time_range_hours=1)
                await analytics_service.track_event("voice_performance_summary", summary)
                
                # Detect and report anomalies
                anomalies = await self.detect_anomalies()
                if anomalies:
                    await analytics_service.track_event("voice_anomalies", {
                        "anomalies": anomalies,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic analytics error: {e}")
    
    async def _process_time_windows(self):
        """Process metrics into time windows"""
        while True:
            try:
                await asyncio.sleep(600)  # Every 10 minutes
                
                # Process last 10 minutes of metrics
                window_end = datetime.utcnow()
                window_start = window_end - timedelta(minutes=10)
                
                window_metrics = [
                    m for m in self.metrics_buffer
                    if window_start <= m.timestamp < window_end
                ]
                
                if window_metrics:
                    window = self._create_performance_window(window_start, window_end, window_metrics)
                    self.performance_windows.append(window)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Time window processing error: {e}")
    
    def _create_performance_window(self, start: datetime, end: datetime, metrics: List[VoiceMetric]) -> PerformanceWindow:
        """Create performance window from metrics"""
        successful_metrics = [m for m in metrics if not m.error]
        processing_times = [m.processing_time_ms for m in successful_metrics]
        quality_scores = [m.quality_score for m in successful_metrics]
        
        # Top voice agents
        agent_counts = defaultdict(int)
        for m in metrics:
            agent_counts[m.voice_agent_id] += 1
        
        top_agents = [
            {"agent_id": agent_id, "request_count": count}
            for agent_id, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return PerformanceWindow(
            window_start=start,
            window_end=end,
            total_requests=len(metrics),
            successful_requests=len(successful_metrics),
            cache_hits=sum(1 for m in metrics if m.cached),
            average_processing_time_ms=statistics.mean(processing_times) if processing_times else 0,
            p95_processing_time_ms=self._percentile(processing_times, 95) if processing_times else 0,
            p99_processing_time_ms=self._percentile(processing_times, 99) if processing_times else 0,
            average_quality_score=statistics.mean(quality_scores) if quality_scores else 0,
            error_rate=len(metrics) - len(successful_metrics) / len(metrics) if metrics else 0,
            languages_used=list(set(m.language for m in metrics)),
            top_voice_agents=top_agents
        )
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _calculate_health_indicators(self, metrics: List[VoiceMetric]) -> Dict[str, Any]:
        """Calculate health indicators from metrics"""
        if not metrics:
            return {}
        
        processing_times = [m.processing_time_ms for m in metrics if not m.error]
        quality_scores = [m.quality_score for m in metrics if not m.error]
        
        return {
            "response_time_health": "healthy" if statistics.mean(processing_times) < 1500 else "degraded" if processing_times else "unknown",
            "quality_health": "healthy" if statistics.mean(quality_scores) > 0.8 else "degraded" if quality_scores else "unknown",
            "error_health": "healthy" if sum(1 for m in metrics if m.error) / len(metrics) < 0.05 else "degraded",
            "cache_health": "healthy" if sum(1 for m in metrics if m.cached) / len(metrics) > 0.2 else "needs_improvement"
        }
    
    def _calculate_hourly_trends(self, metrics: List[VoiceMetric]) -> Dict[str, List[float]]:
        """Calculate hourly performance trends"""
        hourly_data = defaultdict(list)
        
        for metric in metrics:
            hour = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            if not metric.error:
                hourly_data[hour].append(metric.processing_time_ms)
        
        trends = {}
        for hour, times in hourly_data.items():
            trends[hour.isoformat()] = {
                "avg_response_time_ms": statistics.mean(times),
                "request_count": len(times)
            }
        
        return trends
    
    def _generate_agent_recommendations(self, metrics: List[VoiceMetric]) -> List[str]:
        """Generate recommendations for agent performance"""
        recommendations = []
        
        if not metrics:
            return recommendations
        
        processing_times = [m.processing_time_ms for m in metrics if not m.error]
        quality_scores = [m.quality_score for m in metrics if not m.error]
        
        if processing_times:
            avg_time = statistics.mean(processing_times)
            if avg_time > 1500:
                recommendations.append("Consider optimizing voice synthesis settings for faster response times")
            
            if max(processing_times) > 5000:
                recommendations.append("Investigate occasional very slow responses (>5s)")
        
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            if avg_quality < 0.8:
                recommendations.append("Review voice quality settings to improve audio output quality")
        
        cache_hit_rate = sum(1 for m in metrics if m.cached) / len(metrics)
        if cache_hit_rate < 0.3:
            recommendations.append("Consider pre-generating more common responses to improve cache hit rate")
        
        return recommendations
    
    async def cleanup(self):
        """Cleanup analytics service"""
        try:
            if self._analytics_task:
                self._analytics_task.cancel()
                try:
                    await self._analytics_task
                except asyncio.CancelledError:
                    pass
            
            if self._window_processing_task:
                self._window_processing_task.cancel()
                try:
                    await self._window_processing_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Voice analytics service cleanup completed")
            
        except Exception as e:
            logger.error(f"Voice analytics cleanup failed: {e}")

# Global analytics service instance
voice_analytics = VoiceAnalyticsService()