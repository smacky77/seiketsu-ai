"""
Health check service for monitoring system components
"""
import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from app.core.config import settings
from app.core.database import engine
from app.core.cache import redis_client

logger = logging.getLogger("seiketsu.health")


class HealthService:
    """Service for monitoring system health"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.last_check = None
        self.component_status = {}
    
    async def initialize(self):
        """Initialize health service"""
        logger.info("Health service initialized")
        self.last_check = datetime.utcnow()
    
    async def cleanup(self):
        """Cleanup health service resources"""
        logger.info("Health service cleanup complete")
    
    async def get_basic_health(self) -> Dict[str, Any]:
        """Get basic health status"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed health status with component checks"""
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "components": {}
        }
        
        # Check all components
        components = [
            ("database", self._check_database),
            ("cache", self._check_cache),
            ("voice_service", self._check_voice_service),
            ("system", self._check_system_resources)
        ]
        
        overall_healthy = True
        
        for component_name, check_func in components:
            try:
                start_time = time.time()
                component_health = await check_func()
                response_time = (time.time() - start_time) * 1000  # ms
                
                health_status["components"][component_name] = {
                    **component_health,
                    "response_time_ms": round(response_time, 2)
                }
                
                if component_health["status"] != "healthy":
                    overall_healthy = False
                    
            except Exception as e:
                logger.error(f"Health check failed for {component_name}: {e}")
                health_status["components"][component_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "response_time_ms": 0
                }
                overall_healthy = False
        
        # Set overall status
        health_status["status"] = "healthy" if overall_healthy else "unhealthy"
        
        return health_status
    
    async def is_ready(self) -> bool:
        """Check if service is ready to accept requests"""
        try:
            # Check critical components
            db_health = await self._check_database()
            
            # Service is ready if database is accessible
            return db_health["status"] == "healthy"
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return False
    
    async def is_alive(self) -> bool:
        """Check if service is alive (liveness probe)"""
        try:
            # Basic liveness check - can we respond?
            return True
        except Exception:
            return False
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            async with engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                await result.fetchone()
            
            return {
                "status": "healthy",
                "message": "Database connection successful"
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed"
            }
    
    async def _check_cache(self) -> Dict[str, Any]:
        """Check Redis cache connectivity"""
        try:
            if not redis_client:
                return {
                    "status": "warning",
                    "message": "Cache not configured"
                }
            
            await redis_client.ping()
            
            return {
                "status": "healthy",
                "message": "Cache connection successful"
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "degraded",
                "error": str(e),
                "message": "Cache connection failed - running without cache"
            }
    
    async def _check_voice_service(self) -> Dict[str, Any]:
        """Check ElevenLabs voice service"""
        try:
            # This would check ElevenLabs API connectivity
            # For now, just check if API key is configured
            if not settings.ELEVEN_LABS_API_KEY:
                return {
                    "status": "warning",
                    "message": "ElevenLabs API key not configured"
                }
            
            return {
                "status": "healthy",
                "message": "Voice service configured"
            }
            
        except Exception as e:
            logger.error(f"Voice service health check failed: {e}")
            return {
                "status": "degraded",
                "error": str(e),
                "message": "Voice service check failed"
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources (CPU, memory, disk)"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Define thresholds
            cpu_threshold = 85
            memory_threshold = 85
            disk_threshold = 90
            
            status = "healthy"
            warnings = []
            
            if cpu_percent > cpu_threshold:
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > memory_threshold:
                status = "warning" 
                warnings.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > disk_threshold:
                status = "warning"
                warnings.append(f"High disk usage: {disk.percent}%")
            
            return {
                "status": status,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                "warnings": warnings if warnings else None,
                "message": "System resources checked"
            }
            
        except Exception as e:
            logger.error(f"System resources health check failed: {e}")
            return {
                "status": "warning",
                "error": str(e),
                "message": "Could not check system resources"
            }