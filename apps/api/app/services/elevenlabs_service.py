"""
ElevenLabs voice service integration
"""
import asyncio
import httpx
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger("seiketsu.voice")


class ElevenLabsService:
    """Service for ElevenLabs voice integration"""
    
    def __init__(self):
        self.api_key = settings.ELEVEN_LABS_API_KEY
        self.base_url = settings.ELEVEN_LABS_BASE_URL
        self.timeout = settings.ELEVEN_LABS_TIMEOUT
        self.client = None
    
    async def initialize(self):
        """Initialize ElevenLabs service"""
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured - voice features will be limited")
            return
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
        )
        
        # Test connection
        try:
            await self.get_voices()
            logger.info("ElevenLabs service initialized successfully")
        except Exception as e:
            logger.error(f"ElevenLabs service initialization failed: {e}")
    
    async def cleanup(self):
        """Cleanup ElevenLabs service"""
        if self.client:
            await self.client.aclose()
            logger.info("ElevenLabs service cleanup complete")
    
    async def get_voices(self) -> List[Dict[str, Any]]:
        """Get available voices from ElevenLabs"""
        if not self.client:
            return []
        
        try:
            response = await self.client.get(f"{self.base_url}/voices")
            response.raise_for_status()
            
            voices_data = response.json()
            return voices_data.get("voices", [])
            
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []
    
    async def synthesize_speech(
        self, 
        text: str, 
        voice_id: str,
        settings_override: Optional[Dict[str, Any]] = None
    ) -> Optional[bytes]:
        """Synthesize speech from text"""
        if not self.client:
            logger.error("ElevenLabs client not initialized")
            return None
        
        try:
            # Default voice settings
            voice_settings = {
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": 0.0,
                "use_speaker_boost": True
            }
            
            # Apply overrides
            if settings_override:
                voice_settings.update(settings_override)
            
            # Prepare request
            payload = {
                "text": text,
                "voice_settings": voice_settings
            }
            
            # Make request
            response = await self.client.post(
                f"{self.base_url}/text-to-speech/{voice_id}",
                json=payload
            )
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            return None
    
    async def get_voice_info(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific voice"""
        if not self.client:
            return None
        
        try:
            response = await self.client.get(f"{self.base_url}/voices/{voice_id}")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get voice info for {voice_id}: {e}")
            return None
    
    async def clone_voice(self, name: str, files: List[bytes]) -> Optional[str]:
        """Clone a voice (enterprise feature)"""
        if not self.client:
            return None
        
        try:
            # This would implement voice cloning
            # Requires enterprise ElevenLabs account
            logger.warning("Voice cloning requires enterprise ElevenLabs account")
            return None
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return None