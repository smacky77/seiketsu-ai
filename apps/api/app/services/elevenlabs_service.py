"""
ElevenLabs Voice Synthesis Service for Seiketsu AI Platform
Production-ready implementation with sub-2s response times, caching, and monitoring
"""
import asyncio
import logging
import json
import time
import hashlib
from typing import Dict, Any, Optional, List, AsyncGenerator, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import io
import base64

import aiohttp
import aiofiles
import redis.asyncio as redis
from elevenlabs import generate, Voice, VoiceSettings, set_api_key, get_voices
from elevenlabs.client import ElevenLabs
import httpx

from app.core.config import settings
from app.core.cache import get_redis_client
from app.models.voice_agent import VoiceAgent

logger = logging.getLogger("seiketsu.elevenlabs_service")


class AudioFormat(str, Enum):
    MP3 = "mp3_44100_128"
    WAV = "pcm_16000"
    OGG = "ulaw_8000"

class VoiceModel(str, Enum):
    TURBO_V2 = "eleven_turbo_v2"  # Fastest, lowest latency
    MULTILINGUAL_V2 = "eleven_multilingual_v2"  # Multi-language support
    MONOLINGUAL_V1 = "eleven_monolingual_v1"  # High quality English

class Language(str, Enum):
    ENGLISH = "en"
    SPANISH = "es"
    MANDARIN = "zh"

@dataclass
class VoiceProfile:
    """Voice profile configuration for different agent personas"""
    voice_id: str
    name: str
    persona: str
    stability: float = 0.75
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True
    model: VoiceModel = VoiceModel.TURBO_V2
    language: Language = Language.ENGLISH

@dataclass
class SynthesisRequest:
    """Voice synthesis request with optimization settings"""
    text: str
    voice_profile: VoiceProfile
    format: AudioFormat = AudioFormat.MP3
    optimize_streaming_latency: int = 3
    output_format: str = "mp3_44100_128"

@dataclass
class SynthesisResult:
    """Voice synthesis result with metadata"""
    audio_data: bytes
    duration_ms: int
    processing_time_ms: float
    voice_id: str
    text_hash: str
    cached: bool = False
    quality_score: float = 1.0

class ElevenLabsService:
    """
    Production ElevenLabs service with enterprise features:
    - Sub-2 second response times
    - Multi-language support
    - Voice caching and pre-generation
    - Real-time streaming
    - Quality monitoring and fallback
    - Background voice generation
    - Analytics integration
    """
    
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.ELEVEN_LABS_API_KEY)
        self.redis_client: Optional[redis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Voice profiles for different agent personas
        self.voice_profiles = self._initialize_voice_profiles()
        
        # Pre-generated common responses cache
        self.common_responses = {}
        self.pregeneration_enabled = True
        
        # Performance monitoring
        self.response_times = []
        self.synthesis_count = 0
        self.cache_hits = 0
        self.quality_failures = 0
        
        # Fallback voices for quality issues
        self.fallback_voices = {
            Language.ENGLISH: "21m00Tcm4TlvDq8ikWAM",  # Rachel
            Language.SPANISH: "VR6AewLTigWG4xSOukaG",   # Arnold
            Language.MANDARIN: "pNInz6obpgDQGcFmaJgB"   # Adam
        }
        
        # Concurrent processing limits
        self.max_concurrent_requests = 50
        self.active_requests = 0
        self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
    
    async def initialize(self):
        """Initialize the ElevenLabs service"""
        try:
            # Set API key
            set_api_key(settings.ELEVEN_LABS_API_KEY)
            
            # Initialize Redis client
            self.redis_client = await get_redis_client()
            
            # Initialize HTTP client with optimized settings
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                http2=True
            )
            
            # Test connection and validate voices
            await self._test_connection()
            await self._validate_voice_profiles()
            
            # Pre-generate common responses
            if self.pregeneration_enabled:
                await self._pregenerate_common_responses()
            
            logger.info("ElevenLabs service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs service: {e}")
            raise
    
    def _initialize_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """Initialize voice profiles for different agent personas"""
        return {
            "professional_male": VoiceProfile(
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel (clear, professional)
                name="Professional Male",
                persona="professional",
                stability=0.8,
                similarity_boost=0.8,
                style=0.1,
                model=VoiceModel.TURBO_V2
            ),
            "friendly_female": VoiceProfile(
                voice_id="AZnzlk1XvdvUeBnXmlld",  # Domi (warm, friendly)
                name="Friendly Female",
                persona="friendly",
                stability=0.7,
                similarity_boost=0.75,
                style=0.2,
                model=VoiceModel.TURBO_V2
            ),
            "authoritative_male": VoiceProfile(
                voice_id="EXAVITQu4vr4xnSDxMaL",  # Bella (confident, clear)
                name="Authoritative Male",
                persona="authoritative",
                stability=0.85,
                similarity_boost=0.8,
                style=0.0,
                model=VoiceModel.TURBO_V2
            ),
            "casual_male": VoiceProfile(
                voice_id="ErXwobaYiN019PkySvjV",  # Antoni (casual, conversational)
                name="Casual Male",
                persona="casual",
                stability=0.6,
                similarity_boost=0.7,
                style=0.3,
                model=VoiceModel.TURBO_V2
            ),
            "multilingual_female": VoiceProfile(
                voice_id="Xb7hH8MSUJpSbSDYk0k2",  # Alice (multilingual)
                name="Multilingual Female",
                persona="multilingual",
                stability=0.75,
                similarity_boost=0.75,
                style=0.1,
                model=VoiceModel.MULTILINGUAL_V2,
                language=Language.ENGLISH
            )
        }
    
    async def synthesize_speech(
        self,
        text: str,
        voice_agent: VoiceAgent,
        format: AudioFormat = AudioFormat.MP3,
        language: Language = Language.ENGLISH,
        enable_caching: bool = True,
        optimize_for_speed: bool = True
    ) -> SynthesisResult:
        """
        Synthesize speech with sub-2s response time optimization
        """
        start_time = time.time()
        
        async with self.request_semaphore:
            self.active_requests += 1
            
            try:
                # Get voice profile for agent
                voice_profile = self._get_voice_profile_for_agent(voice_agent, language)
                
                # Check cache first
                if enable_caching:
                    cached_result = await self._get_cached_audio(text, voice_profile, format)
                    if cached_result:
                        self.cache_hits += 1
                        processing_time = (time.time() - start_time) * 1000
                        cached_result.processing_time_ms = processing_time
                        cached_result.cached = True
                        return cached_result
                
                # Create synthesis request
                request = SynthesisRequest(
                    text=text,
                    voice_profile=voice_profile,
                    format=format,
                    optimize_streaming_latency=3 if optimize_for_speed else 1
                )
                
                # Synthesize audio
                audio_data = await self._synthesize_audio(request)
                
                # Calculate duration and processing time
                duration_ms = self._estimate_audio_duration(audio_data, format)
                processing_time_ms = (time.time() - start_time) * 1000
                
                # Create result
                text_hash = self._hash_text(text, voice_profile)
                result = SynthesisResult(
                    audio_data=audio_data,
                    duration_ms=duration_ms,
                    processing_time_ms=processing_time_ms,
                    voice_id=voice_profile.voice_id,
                    text_hash=text_hash,
                    cached=False
                )
                
                # Cache result for future use
                if enable_caching:
                    await self._cache_audio(text, voice_profile, format, result)
                
                # Update performance metrics
                self.response_times.append(processing_time_ms)
                if len(self.response_times) > 1000:
                    self.response_times.pop(0)
                
                self.synthesis_count += 1
                
                # Log slow responses
                if processing_time_ms > 2000:  # >2s
                    logger.warning(f"Slow synthesis: {processing_time_ms:.1f}ms for text: {text[:50]}...")
                
                # Monitor to 21dev.ai
                await self._send_analytics_event("voice_synthesis", {
                    "processing_time_ms": processing_time_ms,
                    "text_length": len(text),
                    "voice_id": voice_profile.voice_id,
                    "language": language.value,
                    "cached": False
                })
                
                return result
                
            except Exception as e:
                processing_time_ms = (time.time() - start_time) * 1000
                logger.error(f"Speech synthesis failed after {processing_time_ms:.1f}ms: {e}")
                
                # Attempt fallback
                if hasattr(self, '_fallback_synthesis'):
                    try:
                        return await self._fallback_synthesis(text, language, format)
                    except Exception as fallback_error:
                        logger.error(f"Fallback synthesis also failed: {fallback_error}")
                
                raise
                
            finally:
                self.active_requests -= 1
    
    async def synthesize_streaming(
        self,
        text: str,
        voice_agent: VoiceAgent,
        language: Language = Language.ENGLISH
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio synthesis for real-time applications
        """
        try:
            voice_profile = self._get_voice_profile_for_agent(voice_agent, language)
            
            # Use ElevenLabs streaming API
            url = f"{settings.ELEVEN_LABS_BASE_URL}/text-to-speech/{voice_profile.voice_id}/stream"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": settings.ELEVEN_LABS_API_KEY,
            }
            
            data = {
                "text": text,
                "model_id": voice_profile.model.value,
                "voice_settings": {
                    "stability": voice_profile.stability,
                    "similarity_boost": voice_profile.similarity_boost,
                    "style": voice_profile.style,
                    "use_speaker_boost": voice_profile.use_speaker_boost
                },
                "optimize_streaming_latency": 3,
                "output_format": "mp3_44100_128"
            }
            
            async with self.http_client.stream("POST", url, headers=headers, json=data) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"ElevenLabs API error: {response.status_code} - {error_text}")
                
                async for chunk in response.aiter_bytes(chunk_size=1024):
                    if chunk:
                        yield chunk
                        
        except Exception as e:
            logger.error(f"Streaming synthesis failed: {e}")
            raise
    
    async def bulk_synthesize(
        self,
        texts: List[str],
        voice_agent: VoiceAgent,
        language: Language = Language.ENGLISH,
        max_concurrent: int = 10
    ) -> List[SynthesisResult]:
        """
        Bulk synthesize multiple texts with concurrency control
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def synthesize_single(text: str) -> SynthesisResult:
            async with semaphore:
                return await self.synthesize_speech(text, voice_agent, language=language)
        
        tasks = [synthesize_single(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Bulk synthesis failed for text {i}: {result}")
            else:
                successful_results.append(result)
        
        return successful_results
    
    async def pregenerate_responses(
        self,
        voice_agent: VoiceAgent,
        responses: List[str],
        language: Language = Language.ENGLISH
    ):
        """
        Pre-generate common responses for faster retrieval
        """
        try:
            logger.info(f"Pre-generating {len(responses)} responses for agent {voice_agent.name}")
            
            results = await self.bulk_synthesize(responses, voice_agent, language)
            
            logger.info(f"Successfully pre-generated {len(results)} responses")
            
            # Store in Redis with extended TTL
            for i, result in enumerate(results):
                cache_key = f"pregenerated:{voice_agent.id}:{language.value}:{self._hash_text(responses[i], self._get_voice_profile_for_agent(voice_agent, language))}"
                await self.redis_client.setex(
                    cache_key,
                    86400 * 7,  # 7 days TTL
                    json.dumps({
                        "audio_data": base64.b64encode(result.audio_data).decode(),
                        "duration_ms": result.duration_ms,
                        "voice_id": result.voice_id
                    })
                )
            
        except Exception as e:
            logger.error(f"Pre-generation failed: {e}")
    
    async def get_voice_quality_score(
        self,
        text: str,
        voice_agent: VoiceAgent,
        audio_data: bytes
    ) -> float:
        """
        Analyze voice quality and return score (0.0-1.0)
        """
        try:
            # Simple quality checks
            quality_score = 1.0
            
            # Check audio size (too small = poor quality)
            if len(audio_data) < len(text) * 50:  # Rough heuristic
                quality_score -= 0.2
            
            # Check for common audio artifacts
            if b'\x00' * 100 in audio_data:  # Large blocks of silence
                quality_score -= 0.3
            
            # Check text-to-audio ratio
            expected_duration = len(text) * 50  # Rough ms per character
            actual_size = len(audio_data)
            if actual_size < expected_duration * 10:  # Too compressed
                quality_score -= 0.2
            
            return max(0.0, quality_score)
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return 0.5  # Default score
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check and return service status
        """
        try:
            start_time = time.time()
            
            # Test synthesis with simple text
            test_text = "Health check test"
            voice_profile = list(self.voice_profiles.values())[0]
            
            # Try synthesis
            audio = await self._synthesize_audio(SynthesisRequest(
                text=test_text,
                voice_profile=voice_profile
            ))
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Check Redis connectivity
            redis_status = "healthy"
            try:
                await self.redis_client.ping()
            except Exception:
                redis_status = "unhealthy"
            
            # Calculate performance metrics
            avg_response_time = sum(self.response_times[-100:]) / len(self.response_times[-100:]) if self.response_times else 0
            cache_hit_rate = (self.cache_hits / max(self.synthesis_count, 1)) * 100
            
            status = {
                "status": "healthy" if response_time_ms < 5000 else "degraded",
                "response_time_ms": response_time_ms,
                "average_response_time_ms": avg_response_time,
                "cache_hit_rate_percent": cache_hit_rate,
                "total_syntheses": self.synthesis_count,
                "active_requests": self.active_requests,
                "redis_status": redis_status,
                "voice_profiles_available": len(self.voice_profiles),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Private methods
    
    def _get_voice_profile_for_agent(
        self,
        voice_agent: VoiceAgent,
        language: Language = Language.ENGLISH
    ) -> VoiceProfile:
        """Get appropriate voice profile for agent"""
        # Try to get custom voice profile from agent settings
        if hasattr(voice_agent, 'voice_settings') and voice_agent.voice_settings:
            voice_settings = voice_agent.voice_settings
            if isinstance(voice_settings, str):
                voice_settings = json.loads(voice_settings)
            
            profile_name = voice_settings.get('profile', 'professional_male')
            if profile_name in self.voice_profiles:
                profile = self.voice_profiles[profile_name]
                
                # Override with agent-specific settings if provided
                if 'voice_id' in voice_settings:
                    profile.voice_id = voice_settings['voice_id']
                if 'stability' in voice_settings:
                    profile.stability = voice_settings['stability']
                if 'similarity_boost' in voice_settings:
                    profile.similarity_boost = voice_settings['similarity_boost']
                
                profile.language = language
                return profile
        
        # Default based on agent persona or type
        agent_type = getattr(voice_agent, 'type', 'professional')
        if agent_type in self.voice_profiles:
            profile = self.voice_profiles[agent_type]
            profile.language = language
            return profile
        
        # Default fallback
        profile = self.voice_profiles['professional_male']
        profile.language = language
        return profile
    
    async def _synthesize_audio(self, request: SynthesisRequest) -> bytes:
        """Synthesize audio using ElevenLabs API"""
        try:
            # Use ElevenLabs Python library for optimal performance
            audio = generate(
                text=request.text,
                voice=Voice(
                    voice_id=request.voice_profile.voice_id,
                    settings=VoiceSettings(
                        stability=request.voice_profile.stability,
                        similarity_boost=request.voice_profile.similarity_boost,
                        style=request.voice_profile.style,
                        use_speaker_boost=request.voice_profile.use_speaker_boost
                    )
                ),
                model=request.voice_profile.model.value,
                stream=False
            )
            
            return audio
            
        except Exception as e:
            logger.error(f"ElevenLabs API synthesis failed: {e}")
            raise
    
    async def _get_cached_audio(
        self,
        text: str,
        voice_profile: VoiceProfile,
        format: AudioFormat
    ) -> Optional[SynthesisResult]:
        """Get cached audio if available"""
        try:
            cache_key = f"audio:{self._hash_text(text, voice_profile)}:{format.value}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                return SynthesisResult(
                    audio_data=base64.b64decode(data['audio_data']),
                    duration_ms=data['duration_ms'],
                    processing_time_ms=0,  # Will be set by caller
                    voice_id=voice_profile.voice_id,
                    text_hash=self._hash_text(text, voice_profile),
                    cached=True
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None
    
    async def _cache_audio(
        self,
        text: str,
        voice_profile: VoiceProfile,
        format: AudioFormat,
        result: SynthesisResult
    ):
        """Cache audio result"""
        try:
            cache_key = f"audio:{self._hash_text(text, voice_profile)}:{format.value}"
            cache_data = {
                "audio_data": base64.b64encode(result.audio_data).decode(),
                "duration_ms": result.duration_ms,
                "voice_id": result.voice_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Cache for 24 hours
            await self.redis_client.setex(cache_key, 86400, json.dumps(cache_data))
            
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
    
    def _hash_text(self, text: str, voice_profile: VoiceProfile) -> str:
        """Create hash for text and voice profile combination"""
        content = f"{text}:{voice_profile.voice_id}:{voice_profile.stability}:{voice_profile.similarity_boost}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _estimate_audio_duration(self, audio_data: bytes, format: AudioFormat) -> int:
        """Estimate audio duration in milliseconds"""
        # Simple estimation based on audio format and size
        if format == AudioFormat.MP3:
            # Rough estimation: 1 second ≈ 16KB for 128kbps MP3
            return int((len(audio_data) / 16000) * 1000)
        elif format == AudioFormat.WAV:
            # WAV is uncompressed: 16-bit, 16kHz = 32KB per second
            return int((len(audio_data) / 32000) * 1000)
        else:
            # Default estimation
            return int((len(audio_data) / 20000) * 1000)
    
    async def _pregenerate_common_responses(self):
        """Pre-generate common greeting and response phrases"""
        common_phrases = [
            "Hello! How can I help you today?",
            "Thank you for your interest in our properties.",
            "I'd be happy to help you find the perfect home.",
            "What type of property are you looking for?",
            "Let me check our available listings for you.",
            "I can schedule a viewing for you right away.",
            "What's your budget range for this property?",
            "Are you looking to buy or rent?",
            "I'll transfer you to one of our specialists.",
            "Thank you for your time. Have a great day!"
        ]
        
        try:
            for profile_name, profile in self.voice_profiles.items():
                for phrase in common_phrases:
                    cache_key = f"common:{profile_name}:{self._hash_text(phrase, profile)}"
                    
                    # Check if already cached
                    if await self.redis_client.exists(cache_key):
                        continue
                    
                    # Generate and cache
                    try:
                        request = SynthesisRequest(text=phrase, voice_profile=profile)
                        audio_data = await self._synthesize_audio(request)
                        
                        cache_data = {
                            "audio_data": base64.b64encode(audio_data).decode(),
                            "duration_ms": self._estimate_audio_duration(audio_data, AudioFormat.MP3),
                            "voice_id": profile.voice_id
                        }
                        
                        await self.redis_client.setex(cache_key, 86400 * 7, json.dumps(cache_data))
                        
                    except Exception as e:
                        logger.error(f"Failed to pregenerate '{phrase}' for {profile_name}: {e}")
                        continue
            
            logger.info("Common response pre-generation completed")
            
        except Exception as e:
            logger.error(f"Pre-generation failed: {e}")
    
    async def _test_connection(self):
        """Test ElevenLabs API connection"""
        try:
            # Get available voices to test connection
            voices = get_voices()
            if not voices:
                raise Exception("No voices available from ElevenLabs API")
            
            logger.info(f"ElevenLabs connection successful. {len(voices)} voices available.")
            
        except Exception as e:
            logger.error(f"ElevenLabs connection test failed: {e}")
            raise
    
    async def _validate_voice_profiles(self):
        """Validate that all configured voice profiles exist"""
        try:
            available_voices = get_voices()
            available_voice_ids = {voice.voice_id for voice in available_voices}
            
            for profile_name, profile in self.voice_profiles.items():
                if profile.voice_id not in available_voice_ids:
                    logger.warning(f"Voice profile '{profile_name}' uses unavailable voice ID: {profile.voice_id}")
                    # Use fallback voice
                    profile.voice_id = self.fallback_voices[Language.ENGLISH]
            
        except Exception as e:
            logger.error(f"Voice profile validation failed: {e}")
    
    async def _send_analytics_event(self, event_type: str, data: Dict[str, Any]):
        """Send analytics event to 21dev.ai"""
        try:
            if not settings.TWENTYONEDEV_API_KEY:
                return
            
            payload = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "elevenlabs",
                "data": data
            }
            
            headers = {
                "Authorization": f"Bearer {settings.TWENTYONEDEV_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with self.http_client.post(
                f"{settings.TWENTYONEDEV_BASE_URL}/analytics/events",
                json=payload,
                headers=headers
            ) as response:
                if response.status_code != 200:
                    logger.warning(f"Analytics event failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Analytics event failed: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.http_client:
                await self.http_client.aclose()
                
            if self.redis_client:
                await self.redis_client.close()
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global service instance
elevenlabs_service = ElevenLabsService()