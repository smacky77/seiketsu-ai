"""
Voice services initialization and lifecycle management
"""
import logging
import asyncio
from typing import Dict, Any
from contextlib import asynccontextmanager

from app.services.voice_service import VoiceService
from app.services.elevenlabs_service import elevenlabs_service
from app.core.config import settings

logger = logging.getLogger("seiketsu.voice_init")

class VoiceServiceManager:
    """Manages initialization and lifecycle of voice services"""
    
    def __init__(self):
        self.voice_service: VoiceService = None
        self.elevenlabs_service = elevenlabs_service
        self.initialized = False
        self._health_check_task = None
    
    async def initialize(self):
        """Initialize all voice services"""
        try:
            logger.info("Starting voice services initialization...")
            
            # Initialize ElevenLabs service first
            await self.elevenlabs_service.initialize()
            
            # Initialize main voice service
            self.voice_service = VoiceService()
            await self.voice_service.initialize()
            
            # Start health monitoring
            await self._start_health_monitoring()
            
            self.initialized = True
            logger.info("Voice services initialized successfully")
            
        except Exception as e:
            logger.error(f"Voice services initialization failed: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup all voice services"""
        try:
            logger.info("Cleaning up voice services...")
            
            # Stop health monitoring
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Cleanup services
            if self.elevenlabs_service:
                await self.elevenlabs_service.cleanup()
            
            self.initialized = False
            logger.info("Voice services cleanup completed")
            
        except Exception as e:
            logger.error(f"Voice services cleanup failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all voice services"""
        if not self.initialized:
            return {
                "status": "not_initialized",
                "services": {}
            }
        
        try:
            # Get health status from all services
            elevenlabs_health = await self.elevenlabs_service.health_check()
            voice_service_health = await self.voice_service.get_voice_service_health()
            
            # Overall status assessment
            overall_status = "healthy"
            if elevenlabs_health["status"] != "healthy":
                overall_status = "degraded"
            elif voice_service_health["overall_status"] != "healthy":
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "services": {
                    "elevenlabs": elevenlabs_health,
                    "voice_processing": voice_service_health
                },
                "initialized": self.initialized
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self.initialized
            }
    
    async def _start_health_monitoring(self):
        """Start background health monitoring"""
        async def health_monitor():
            while True:
                try:
                    await asyncio.sleep(60)  # Check every minute
                    health = await self.health_check()
                    
                    if health["status"] == "unhealthy":
                        logger.warning(f"Voice services health check failed: {health}")
                    elif health["status"] == "degraded":
                        logger.warning(f"Voice services performance degraded: {health}")
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
        
        self._health_check_task = asyncio.create_task(health_monitor())

# Global voice service manager
voice_manager = VoiceServiceManager()

@asynccontextmanager
async def voice_service_lifespan():
    """Context manager for voice service lifecycle"""
    try:
        await voice_manager.initialize()
        yield voice_manager
    finally:
        await voice_manager.cleanup()

async def get_voice_manager() -> VoiceServiceManager:
    """Dependency to get voice service manager"""
    if not voice_manager.initialized:
        await voice_manager.initialize()
    return voice_manager