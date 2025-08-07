"""
Voice Processing Engine - Core voice processing orchestrator
Handles real-time voice processing with <180ms response time requirement
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from io import BytesIO

from .speech_to_text import SpeechToTextService
from .text_to_speech import TextToSpeechService
from .voice_quality import VoiceQualityAssessment
from .audio_processor import AudioProcessor
from .biometrics import VoiceBiometrics
from ..config import ai_settings, VOICE_CONFIGS
from ..analytics.metrics import AIMetrics

logger = logging.getLogger(__name__)


@dataclass
class VoiceProcessingResult:
    """Result of voice processing operation"""
    success: bool
    transcription: Optional[str] = None
    audio_data: Optional[bytes] = None
    processing_time_ms: int = 0
    quality_score: float = 0.0
    speaker_id: Optional[str] = None
    confidence: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class VoiceConfig:
    """Voice processing configuration"""
    voice_id: str
    voice_model: str
    enable_noise_reduction: bool = True
    enable_quality_assessment: bool = True
    enable_biometrics: bool = True
    target_response_time_ms: int = 180


class VoiceProcessingEngine:
    """
    Advanced Voice Processing Engine
    Orchestrates all voice processing operations with enterprise-grade performance
    """
    
    def __init__(self):
        self.stt_service = SpeechToTextService()
        self.tts_service = TextToSpeechService()
        self.quality_assessor = VoiceQualityAssessment()
        self.audio_processor = AudioProcessor()
        self.biometrics = VoiceBiometrics()
        self.metrics = AIMetrics()
        
        # Performance tracking
        self._processing_times: List[float] = []
        self._quality_scores: List[float] = []
        
        logger.info("Voice Processing Engine initialized")
    
    async def process_voice_input(
        self,
        audio_data: bytes,
        config: Optional[VoiceConfig] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> VoiceProcessingResult:
        """
        Process incoming voice input with full pipeline
        Target: <180ms total processing time
        """
        start_time = time.time()
        
        try:
            # Default configuration
            if not config:
                config = VoiceConfig(
                    voice_id=ai_settings.DEFAULT_VOICE_ID,
                    voice_model="eleven_multilingual_v2"
                )
            
            # Start parallel processing tasks
            tasks = []
            
            # Core transcription (highest priority)
            transcription_task = asyncio.create_task(
                self._transcribe_audio(audio_data, user_id, tenant_id)
            )
            tasks.append(("transcription", transcription_task))
            
            # Optional quality assessment
            if config.enable_quality_assessment:
                quality_task = asyncio.create_task(
                    self.quality_assessor.assess_quality(audio_data)
                )
                tasks.append(("quality", quality_task))
            
            # Optional biometrics
            if config.enable_biometrics and user_id:
                biometrics_task = asyncio.create_task(
                    self.biometrics.identify_speaker(audio_data, user_id)
                )
                tasks.append(("biometrics", biometrics_task))
            
            # Audio preprocessing
            if config.enable_noise_reduction:
                processing_task = asyncio.create_task(
                    self.audio_processor.enhance_audio(audio_data)
                )
                tasks.append(("processing", processing_task))
            
            # Execute tasks with timeout
            results = {}
            timeout = config.target_response_time_ms / 1000.0 * 0.8  # 80% of target
            
            completed_tasks = await asyncio.wait(
                [task for _, task in tasks],
                timeout=timeout,
                return_when=asyncio.ALL_COMPLETED
            )
            
            # Collect results
            for task_name, task in tasks:
                if task in completed_tasks[0]:  # completed
                    try:
                        results[task_name] = await task
                    except Exception as e:
                        logger.error(f"Task {task_name} failed: {e}")
                        results[task_name] = None
                else:  # timeout
                    logger.warning(f"Task {task_name} timed out")
                    task.cancel()
                    results[task_name] = None
            
            # Build result
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            result = VoiceProcessingResult(
                success=results.get("transcription") is not None,
                transcription=results.get("transcription"),
                processing_time_ms=processing_time_ms,
                quality_score=results.get("quality", {}).get("score", 0.0),
                speaker_id=results.get("biometrics", {}).get("speaker_id"),
                confidence=results.get("transcription_confidence", 1.0),
                metadata={
                    "audio_duration_ms": results.get("processing", {}).get("duration_ms", 0),
                    "noise_level": results.get("quality", {}).get("noise_level", 0.0),
                    "voice_config": config.__dict__
                }
            )
            
            # Track metrics
            self._track_performance(processing_time_ms, result.quality_score)
            await self.metrics.track_voice_processing(
                processing_time_ms, result.success, user_id, tenant_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return VoiceProcessingResult(
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )
    
    async def generate_voice_response(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> VoiceProcessingResult:
        """
        Generate voice response from text
        Target: <180ms processing time
        """
        start_time = time.time()
        
        try:
            if not config:
                config = VoiceConfig(
                    voice_id=ai_settings.DEFAULT_VOICE_ID,
                    voice_model="eleven_multilingual_v2"
                )
            
            # Generate speech with streaming for better performance
            audio_data = await self.tts_service.text_to_speech_streaming(
                text=text,
                voice_id=config.voice_id,
                model=config.voice_model
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            result = VoiceProcessingResult(
                success=True,
                audio_data=audio_data,
                processing_time_ms=processing_time_ms,
                metadata={
                    "text_length": len(text),
                    "audio_size_bytes": len(audio_data) if audio_data else 0,
                    "voice_config": config.__dict__
                }
            )
            
            # Track metrics
            await self.metrics.track_voice_generation(
                processing_time_ms, len(text), result.success, user_id, tenant_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return VoiceProcessingResult(
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )
    
    async def process_conversation_turn(
        self,
        audio_input: bytes,
        response_text: str,
        config: Optional[VoiceConfig] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> tuple[VoiceProcessingResult, VoiceProcessingResult]:
        """
        Process complete conversation turn: audio input + text response
        Optimized for minimal latency with parallel processing
        """
        start_time = time.time()
        
        # Process input and generate response in parallel
        input_task = asyncio.create_task(
            self.process_voice_input(audio_input, config, user_id, tenant_id)
        )
        
        response_task = asyncio.create_task(
            self.generate_voice_response(response_text, config, user_id, tenant_id)
        )
        
        input_result, response_result = await asyncio.gather(
            input_task, response_task, return_exceptions=True
        )
        
        total_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Conversation turn processed in {total_time_ms}ms")
        
        # Handle exceptions
        if isinstance(input_result, Exception):
            input_result = VoiceProcessingResult(success=False, error=str(input_result))
        if isinstance(response_result, Exception):
            response_result = VoiceProcessingResult(success=False, error=str(response_result))
        
        return input_result, response_result
    
    async def stream_voice_response(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream voice response for real-time playback
        Reduces perceived latency by streaming audio chunks
        """
        try:
            if not config:
                config = VoiceConfig(
                    voice_id=ai_settings.DEFAULT_VOICE_ID,
                    voice_model="eleven_multilingual_v2"
                )
            
            async for audio_chunk in self.tts_service.stream_text_to_speech(
                text=text,
                voice_id=config.voice_id,
                model=config.voice_model
            ):
                yield audio_chunk
                
        except Exception as e:
            logger.error(f"Voice streaming failed: {e}")
            yield b""  # Empty chunk to signal error
    
    async def _transcribe_audio(
        self,
        audio_data: bytes,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[str]:
        """Internal transcription with error handling"""
        try:
            return await self.stt_service.transcribe(
                audio_data, user_id=user_id, tenant_id=tenant_id
            )
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def _track_performance(self, processing_time_ms: int, quality_score: float):
        """Track performance metrics for optimization"""
        self._processing_times.append(processing_time_ms)
        self._quality_scores.append(quality_score)
        
        # Keep only recent metrics (last 100)
        if len(self._processing_times) > 100:
            self._processing_times = self._processing_times[-100:]
            self._quality_scores = self._quality_scores[-100:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        if not self._processing_times:
            return {}
        
        return {
            "avg_processing_time_ms": sum(self._processing_times) / len(self._processing_times),
            "max_processing_time_ms": max(self._processing_times),
            "min_processing_time_ms": min(self._processing_times),
            "avg_quality_score": sum(self._quality_scores) / len(self._quality_scores) if self._quality_scores else 0,
            "total_requests": len(self._processing_times),
            "target_met_percentage": len([t for t in self._processing_times if t <= ai_settings.RESPONSE_TIME_TARGET_MS]) / len(self._processing_times) * 100
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for voice processing engine"""
        health_status = {
            "status": "healthy",
            "components": {},
            "performance": self.get_performance_stats(),
            "timestamp": time.time()
        }
        
        # Check individual components
        components = [
            ("stt_service", self.stt_service),
            ("tts_service", self.tts_service),
            ("quality_assessor", self.quality_assessor),
            ("audio_processor", self.audio_processor),
            ("biometrics", self.biometrics)
        ]
        
        for name, component in components:
            try:
                if hasattr(component, 'health_check'):
                    component_health = await component.health_check()
                    health_status["components"][name] = component_health
                else:
                    health_status["components"][name] = {"status": "unknown"}
            except Exception as e:
                health_status["components"][name] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
        
        return health_status