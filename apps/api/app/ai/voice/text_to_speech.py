"""
Text-to-Speech Service using ElevenLabs
High-performance voice synthesis with streaming and caching
"""

import asyncio
import hashlib
import logging
import time
from typing import Optional, Dict, Any, AsyncGenerator
from io import BytesIO

import httpx
import aiofiles

from ..config import ai_settings, VOICE_CONFIGS
from ...core.cache import get_redis_client

logger = logging.getLogger(__name__)


class TextToSpeechService:
    """
    Advanced Text-to-Speech service with ElevenLabs integration
    Features: streaming synthesis, voice cloning, real-time processing
    """
    
    def __init__(self):
        self.api_key = ai_settings.ELEVENLABS_API_KEY
        self.base_url = ai_settings.ELEVENLABS_BASE_URL
        self.timeout = ai_settings.ELEVENLABS_TIMEOUT
        self.chunk_size = ai_settings.ELEVENLABS_CHUNK_SIZE
        
        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        self.redis_client = None
        
        # Performance tracking
        self._synthesis_times = []
        self._cache_hit_rate = 0.0
        self._cache_hits = 0
        self._total_requests = 0
        
        logger.info("Text-to-Speech service initialized")
    
    async def initialize(self):
        """Initialize Redis connection for caching"""
        try:
            self.redis_client = await get_redis_client()
            logger.info("Redis connection established for TTS caching")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
    
    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: str = "eleven_multilingual_v2",
        stability: float = 0.75,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        use_cache: bool = True
    ) -> bytes:
        """
        Convert text to speech audio
        
        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID
            model: Voice model to use
            stability: Voice stability (0.0-1.0)
            similarity_boost: Voice similarity boost (0.0-1.0)
            style: Voice style exaggeration (0.0-1.0)
            use_speaker_boost: Enable speaker boost
            user_id: User identifier
            tenant_id: Tenant identifier
            use_cache: Whether to use caching
            
        Returns:
            Audio data as bytes
        """
        start_time = time.time()
        self._total_requests += 1
        
        try:
            if not voice_id:
                voice_id = ai_settings.DEFAULT_VOICE_ID
            
            # Generate cache key
            cache_key = None
            if use_cache and self.redis_client:
                cache_key = self._generate_cache_key(
                    text, voice_id, model, stability, similarity_boost, style
                )
                
                # Check cache first
                cached_audio = await self._get_cached_audio(cache_key)
                if cached_audio:
                    self._cache_hits += 1
                    self._update_cache_hit_rate()
                    logger.debug(f"Cache hit for TTS: {cache_key[:16]}...")
                    return cached_audio
            
            # Prepare request
            url = f"/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }
            
            # Make request with retry logic
            audio_data = await self._synthesize_with_retry(url, headers, payload)
            
            # Cache the result
            if cache_key and self.redis_client and audio_data:
                await self._cache_audio(cache_key, audio_data)
            
            # Track performance
            processing_time = (time.time() - start_time) * 1000
            self._synthesis_times.append(processing_time)
            
            # Keep only recent metrics
            if len(self._synthesis_times) > 100:
                self._synthesis_times = self._synthesis_times[-100:]
            
            logger.info(f"TTS synthesis completed in {processing_time:.2f}ms: {len(audio_data)} bytes")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Text-to-speech synthesis failed: {e}")
            raise
    
    async def text_to_speech_streaming(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: str = "eleven_multilingual_v2",
        stability: float = 0.75,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech with streaming optimization
        Returns complete audio but processes in streaming fashion for faster start
        """
        try:
            if not voice_id:
                voice_id = ai_settings.DEFAULT_VOICE_ID
            
            url = f"/text-to-speech/{voice_id}/stream"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }
            
            audio_chunks = []
            
            async with self.client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                
                async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                    if chunk:
                        audio_chunks.append(chunk)
            
            return b"".join(audio_chunks)
            
        except Exception as e:
            logger.error(f"Streaming TTS synthesis failed: {e}")
            raise
    
    async def stream_text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: str = "eleven_multilingual_v2",
        stability: float = 0.75,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream text-to-speech audio chunks for real-time playback
        Enables immediate audio playback as synthesis progresses
        """
        try:
            if not voice_id:
                voice_id = ai_settings.DEFAULT_VOICE_ID
            
            url = f"/text-to-speech/{voice_id}/stream"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }
            
            async with self.client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                
                async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                    if chunk:
                        yield chunk
                        
        except Exception as e:
            logger.error(f"TTS streaming failed: {e}")
            yield b""  # Empty chunk to signal error
    
    async def synthesize_batch(
        self,
        texts: list[str],
        voice_id: Optional[str] = None,
        model: str = "eleven_multilingual_v2",
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> list[bytes]:
        """
        Synthesize multiple texts in parallel
        Optimized for batch processing
        """
        try:
            # Process texts in parallel with concurrency limit
            semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
            
            async def synthesize_single(text: str) -> bytes:
                async with semaphore:
                    return await self.text_to_speech(
                        text, voice_id=voice_id, model=model,
                        user_id=user_id, tenant_id=tenant_id
                    )
            
            tasks = [synthesize_single(text) for text in texts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions in results
            audio_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch synthesis {i} failed: {result}")
                    audio_results.append(b"")
                else:
                    audio_results.append(result)
            
            return audio_results
            
        except Exception as e:
            logger.error(f"Batch synthesis failed: {e}")
            return [b""] * len(texts)
    
    async def get_voices(self, user_id: Optional[str] = None) -> list[Dict[str, Any]]:
        """Get available voices for user/tenant"""
        try:
            url = "/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("voices", [])
            
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []
    
    async def clone_voice(
        self,
        name: str,
        audio_files: list[bytes],
        description: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Clone a voice from audio samples
        Returns voice_id if successful
        """
        try:
            url = "/voices/add"
            headers = {"xi-api-key": self.api_key}
            
            # Prepare multipart form data
            files = []
            for i, audio_data in enumerate(audio_files):
                files.append(("files", (f"sample_{i}.mp3", BytesIO(audio_data), "audio/mpeg")))
            
            data = {"name": name}
            if description:
                data["description"] = description
            
            response = await self.client.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            voice_id = result.get("voice_id")
            
            logger.info(f"Voice cloned successfully: {voice_id}")
            return voice_id
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return None
    
    async def _synthesize_with_retry(
        self, 
        url: str, 
        headers: Dict[str, str], 
        payload: Dict[str, Any]
    ) -> bytes:
        """Synthesize with exponential backoff retry logic"""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.content
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1})")
                        await asyncio.sleep(delay)
                    else:
                        raise
                else:
                    raise
                    
            except httpx.TimeoutException:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Request timeout, retrying in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                else:
                    raise
                    
            except Exception as e:
                logger.error(f"Synthesis attempt {attempt + 1} failed: {e}")
                if attempt >= max_retries:
                    raise
                await asyncio.sleep(base_delay)
    
    def _generate_cache_key(
        self,
        text: str,
        voice_id: str,
        model: str,
        stability: float,
        similarity_boost: float,
        style: float
    ) -> str:
        """Generate cache key for TTS synthesis"""
        cache_string = f"{text}:{voice_id}:{model}:{stability}:{similarity_boost}:{style}"
        hasher = hashlib.sha256()
        hasher.update(cache_string.encode())
        return f"tts:{hasher.hexdigest()}"
    
    async def _get_cached_audio(self, cache_key: str) -> Optional[bytes]:
        """Get cached audio result"""
        try:
            if self.redis_client:
                result = await self.redis_client.get(cache_key)
                if result:
                    return result
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
        return None
    
    async def _cache_audio(self, cache_key: str, audio_data: bytes):
        """Cache audio result"""
        try:
            if self.redis_client:
                # Cache for 1 hour by default
                await self.redis_client.setex(cache_key, 3600, audio_data)
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
    
    def _update_cache_hit_rate(self):
        """Update cache hit rate statistics"""
        self._cache_hit_rate = self._cache_hits / self._total_requests if self._total_requests > 0 else 0.0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        if not self._synthesis_times:
            return {
                "status": "no_data",
                "cache_hit_rate": self._cache_hit_rate,
                "total_requests": self._total_requests
            }
        
        return {
            "avg_processing_time_ms": sum(self._synthesis_times) / len(self._synthesis_times),
            "max_processing_time_ms": max(self._synthesis_times),
            "min_processing_time_ms": min(self._synthesis_times),
            "cache_hit_rate": self._cache_hit_rate,
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "recent_requests": len(self._synthesis_times)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for TTS service"""
        health_status = {
            "status": "healthy",
            "service": "text_to_speech",
            "provider": "elevenlabs",
            "cache_enabled": self.redis_client is not None,
            "performance": self.get_performance_metrics(),
            "timestamp": time.time()
        }
        
        try:
            # Test API connectivity
            url = "/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = await asyncio.wait_for(
                self.client.get(url, headers=headers),
                timeout=5.0
            )
            response.raise_for_status()
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()
        logger.info("TTS service cleaned up")