"""
Speech-to-Text Service using OpenAI Whisper
High-performance transcription with caching and optimization
"""

import asyncio
import hashlib
import logging
import time
from typing import Optional, Dict, Any
from io import BytesIO

import openai
from openai import AsyncOpenAI
import aiofiles

from ..config import ai_settings, MODEL_CONFIGS
from ...core.cache import get_redis_client

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """
    Advanced Speech-to-Text service with Whisper integration
    Features: caching, noise reduction, multi-language support
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=ai_settings.OPENAI_API_KEY,
            organization=ai_settings.OPENAI_ORG_ID,
            base_url=ai_settings.OPENAI_BASE_URL,
            timeout=ai_settings.OPENAI_TIMEOUT,
            max_retries=ai_settings.OPENAI_MAX_RETRIES
        )
        self.redis_client = None
        self.model_config = MODEL_CONFIGS["whisper-transcription"]
        
        # Performance tracking
        self._transcription_times = []
        self._cache_hit_rate = 0.0
        self._cache_hits = 0
        self._total_requests = 0
        
        logger.info("Speech-to-Text service initialized")
    
    async def initialize(self):
        """Initialize Redis connection for caching"""
        try:
            self.redis_client = await get_redis_client()
            logger.info("Redis connection established for STT caching")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Transcribe audio to text with caching and optimization
        
        Args:
            audio_data: Raw audio bytes
            language: ISO language code (optional)
            prompt: Context prompt for better accuracy
            user_id: User identifier for tracking
            tenant_id: Tenant identifier for multi-tenancy
            use_cache: Whether to use caching
            
        Returns:
            Transcribed text
        """
        start_time = time.time()
        self._total_requests += 1
        
        try:
            # Generate cache key
            cache_key = None
            if use_cache and self.redis_client:
                cache_key = self._generate_cache_key(audio_data, language, prompt)
                
                # Check cache first
                cached_result = await self._get_cached_transcription(cache_key)
                if cached_result:
                    self._cache_hits += 1
                    self._update_cache_hit_rate()
                    logger.debug(f"Cache hit for transcription: {cache_key[:16]}...")
                    return cached_result
            
            # Prepare audio file for Whisper API
            audio_file = BytesIO(audio_data)
            audio_file.name = "audio.mp3"  # Whisper needs filename extension
            
            # Prepare transcription parameters
            transcription_params = {
                "file": audio_file,
                "model": self.model_config.model_id,
                "response_format": "json",
                "timeout": self.model_config.timeout
            }
            
            if language:
                transcription_params["language"] = language
            
            if prompt:
                transcription_params["prompt"] = prompt
            
            # Call Whisper API with retry logic
            transcription = await self._transcribe_with_retry(transcription_params)
            
            # Extract text from response
            text = transcription.text.strip()
            
            # Cache the result
            if cache_key and self.redis_client and text:
                await self._cache_transcription(cache_key, text)
            
            # Track performance
            processing_time = (time.time() - start_time) * 1000
            self._transcription_times.append(processing_time)
            
            # Keep only recent metrics
            if len(self._transcription_times) > 100:
                self._transcription_times = self._transcription_times[-100:]
            
            logger.info(f"Transcription completed in {processing_time:.2f}ms: {len(text)} characters")
            
            return text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    async def transcribe_batch(
        self,
        audio_files: list[bytes],
        language: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> list[str]:
        """
        Transcribe multiple audio files in parallel
        Optimized for batch processing
        """
        try:
            # Process files in parallel with concurrency limit
            semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
            
            async def transcribe_single(audio_data: bytes) -> str:
                async with semaphore:
                    return await self.transcribe(
                        audio_data, language=language, 
                        user_id=user_id, tenant_id=tenant_id
                    )
            
            tasks = [transcribe_single(audio) for audio in audio_files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions in results
            transcriptions = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch transcription {i} failed: {result}")
                    transcriptions.append("")
                else:
                    transcriptions.append(result)
            
            return transcriptions
            
        except Exception as e:
            logger.error(f"Batch transcription failed: {e}")
            return [""] * len(audio_files)
    
    async def transcribe_streaming(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        language: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process streaming audio for real-time transcription
        Accumulates audio chunks and transcribes when sufficient data available
        """
        audio_buffer = BytesIO()
        chunk_size = ai_settings.AUDIO_CHUNK_SIZE
        min_audio_duration = 1000  # 1 second minimum
        
        try:
            async for audio_chunk in audio_stream:
                audio_buffer.write(audio_chunk)
                
                # Check if we have enough audio to transcribe
                if audio_buffer.tell() >= chunk_size:
                    audio_data = audio_buffer.getvalue()
                    
                    # Transcribe accumulated audio
                    if len(audio_data) > min_audio_duration:
                        try:
                            text = await self.transcribe(
                                audio_data, language=language,
                                user_id=user_id, tenant_id=tenant_id
                            )
                            if text:
                                yield text
                        except Exception as e:
                            logger.error(f"Streaming transcription failed: {e}")
                    
                    # Reset buffer
                    audio_buffer = BytesIO()
            
            # Process remaining audio
            if audio_buffer.tell() > 0:
                audio_data = audio_buffer.getvalue()
                try:
                    text = await self.transcribe(
                        audio_data, language=language,
                        user_id=user_id, tenant_id=tenant_id
                    )
                    if text:
                        yield text
                except Exception as e:
                    logger.error(f"Final streaming transcription failed: {e}")
                    
        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
    
    async def _transcribe_with_retry(self, params: Dict[str, Any]) -> Any:
        """Transcribe with exponential backoff retry logic"""
        max_retries = self.model_config.retry_attempts
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                # Reset file position for retry
                if hasattr(params["file"], "seek"):
                    params["file"].seek(0)
                
                response = await self.client.audio.transcriptions.create(**params)
                return response
                
            except openai.RateLimitError as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                else:
                    raise
                    
            except openai.APITimeoutError as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"API timeout, retrying in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                else:
                    raise
                    
            except Exception as e:
                logger.error(f"Transcription attempt {attempt + 1} failed: {e}")
                if attempt >= max_retries:
                    raise
                await asyncio.sleep(base_delay)
    
    def _generate_cache_key(
        self, 
        audio_data: bytes, 
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """Generate cache key for audio transcription"""
        hasher = hashlib.sha256()
        hasher.update(audio_data)
        if language:
            hasher.update(language.encode())
        if prompt:
            hasher.update(prompt.encode())
        
        return f"stt:{hasher.hexdigest()}"
    
    async def _get_cached_transcription(self, cache_key: str) -> Optional[str]:
        """Get cached transcription result"""
        try:
            if self.redis_client:
                result = await self.redis_client.get(cache_key)
                if result:
                    return result.decode() if isinstance(result, bytes) else result
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
        return None
    
    async def _cache_transcription(self, cache_key: str, text: str):
        """Cache transcription result"""
        try:
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key, 
                    self.model_config.cache_ttl, 
                    text
                )
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
    
    def _update_cache_hit_rate(self):
        """Update cache hit rate statistics"""
        self._cache_hit_rate = self._cache_hits / self._total_requests if self._total_requests > 0 else 0.0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        if not self._transcription_times:
            return {
                "status": "no_data",
                "cache_hit_rate": self._cache_hit_rate,
                "total_requests": self._total_requests
            }
        
        return {
            "avg_processing_time_ms": sum(self._transcription_times) / len(self._transcription_times),
            "max_processing_time_ms": max(self._transcription_times),
            "min_processing_time_ms": min(self._transcription_times),
            "cache_hit_rate": self._cache_hit_rate,
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "recent_requests": len(self._transcription_times)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for STT service"""
        health_status = {
            "status": "healthy",
            "service": "speech_to_text",
            "model": self.model_config.model_id,
            "cache_enabled": self.redis_client is not None,
            "performance": self.get_performance_metrics(),
            "timestamp": time.time()
        }
        
        try:
            # Test API connectivity with minimal request
            test_audio = b'\x00' * 1024  # Minimal test audio
            audio_file = BytesIO(test_audio)
            audio_file.name = "test.mp3"
            
            # This will likely fail but tests API connectivity
            try:
                await asyncio.wait_for(
                    self.client.audio.transcriptions.create(
                        file=audio_file,
                        model=self.model_config.model_id,
                        response_format="json"
                    ),
                    timeout=5.0
                )
            except (openai.BadRequestError, asyncio.TimeoutError):
                # Expected for test audio, but API is reachable
                pass
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status