"""
Real-Time Voice Processor
Handles streaming audio processing with sub-2 second response times
"""
import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime
import numpy as np
from dataclasses import dataclass

# Audio processing
import librosa
import webrtcvad
from pydub import AudioSegment
import noisereduce as nr

# AI/ML imports
import openai
from transformers import pipeline
import torch

# Core services
from app.core.config import settings
from app.services.voice_intelligence_service import voice_intelligence_service
from app.core.database import AsyncSessionLocal
from app.models.voice_agent_intelligence import (
    RealTimeConversationSession,
    EmotionDetectionLog, 
    ConversationIntent,
    VoiceQualityMetrics
)

logger = logging.getLogger("seiketsu.realtime_voice_processor")

@dataclass
class ProcessingMetrics:
    speech_to_text_ms: int = 0
    emotion_detection_ms: int = 0
    intent_classification_ms: int = 0
    response_generation_ms: int = 0
    text_to_speech_ms: int = 0
    total_processing_ms: int = 0

@dataclass
class AudioQuality:
    clarity_score: float = 0.0
    noise_level: float = 0.0
    volume_consistency: float = 0.0
    is_speech: bool = False

class RealTimeVoiceProcessor:
    """High-performance real-time voice processing pipeline"""
    
    def __init__(self):
        self.vad = webrtcvad.Vad(3)  # Most aggressive VAD setting
        self.sample_rate = 16000
        self.frame_duration_ms = 30
        self.processing_buffer = []
        self.is_processing = False
        
        # Performance optimization
        self.cache = {}
        self.response_templates = self._load_response_templates()
        
        # Quality thresholds
        self.min_speech_confidence = 0.6
        self.max_noise_level = 0.3
        self.target_response_time_ms = 2000
        
    def _load_response_templates(self) -> Dict[str, List[str]]:
        """Load pre-computed response templates for faster generation"""
        return {
            "greeting": [
                "Hello! I'm excited to help you find your perfect property today.",
                "Hi there! I'm here to assist with all your real estate needs.",
                "Welcome! Let's find you an amazing property that fits your lifestyle."
            ],
            "qualification": [
                "Tell me about what you're looking for in your ideal home.",
                "What's most important to you in your next property?",
                "Let's start with your must-haves for your perfect home."
            ],
            "objection_price": [
                "I understand budget is important. Let me show you some excellent value options.",
                "Price is definitely a key factor. I have properties that offer great ROI.",
                "Let's explore properties that give you the best value for your investment."
            ],
            "objection_location": [
                "Location is crucial! Let me suggest some areas that might surprise you.",
                "I know some hidden gems in neighborhoods you might not have considered.",
                "Great point about location. I have properties in several desirable areas."
            ],
            "scheduling": [
                "I'd love to show you some properties. When works best for your schedule?",
                "Let's set up a viewing. Are weekends or weekdays better for you?",
                "Perfect! I can arrange showings that fit your timeline."
            ]
        }
    
    async def process_audio_stream(
        self,
        audio_data: bytes,
        session_id: str,
        agent_id: str,
        conversation_context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process streaming audio with enterprise performance"""
        
        start_time = time.time()
        metrics = ProcessingMetrics()
        
        try:
            # Step 1: Audio preprocessing and VAD (< 50ms)
            preprocessing_start = time.time()
            
            audio_quality, processed_audio = await self._preprocess_audio_optimized(audio_data)
            
            if not audio_quality.is_speech:
                yield {
                    "type": "silence_detected",
                    "timestamp": datetime.utcnow(),
                    "audio_quality": audio_quality.__dict__
                }
                return
            
            preprocessing_ms = int((time.time() - preprocessing_start) * 1000)
            
            # Step 2: Parallel processing pipeline
            stt_start = time.time()
            
            # Run tasks in parallel for maximum speed
            tasks = await asyncio.gather(
                self._speech_to_text_optimized(processed_audio),
                self._analyze_audio_features(processed_audio),
                self._update_session_state(session_id, "processing"),
                return_exceptions=True
            )
            
            transcript = tasks[0] if not isinstance(tasks[0], Exception) else ""
            audio_features = tasks[1] if not isinstance(tasks[1], Exception) else {}
            
            metrics.speech_to_text_ms = int((time.time() - stt_start) * 1000)
            
            if not transcript or len(transcript.strip()) < 2:
                yield {
                    "type": "no_speech_detected",
                    "timestamp": datetime.utcnow(),
                    "processing_time_ms": preprocessing_ms + metrics.speech_to_text_ms
                }
                return
            
            # Yield transcription immediately
            yield {
                "type": "transcription",
                "text": transcript,
                "confidence": 0.95,  # Mock confidence - would come from actual STT
                "timestamp": datetime.utcnow(),
                "processing_time_ms": metrics.speech_to_text_ms
            }
            
            # Step 3: Parallel AI analysis (< 300ms)
            analysis_start = time.time()
            
            analysis_tasks = await asyncio.gather(
                self._detect_emotion_fast(transcript, audio_features),
                self._classify_intent_fast(transcript, conversation_context),
                self._detect_objections_fast(transcript),
                self._extract_entities_fast(transcript),
                return_exceptions=True
            )
            
            emotion_data = analysis_tasks[0] if not isinstance(analysis_tasks[0], Exception) else {}
            intent_data = analysis_tasks[1] if not isinstance(analysis_tasks[1], Exception) else {}
            objections = analysis_tasks[2] if not isinstance(analysis_tasks[2], Exception) else []
            entities = analysis_tasks[3] if not isinstance(analysis_tasks[3], Exception) else {}
            
            metrics.emotion_detection_ms = int((time.time() - analysis_start) * 1000 / 4)
            metrics.intent_classification_ms = metrics.emotion_detection_ms
            
            # Yield analysis results
            if emotion_data:
                yield {
                    "type": "emotion_detected",
                    "emotion": emotion_data.get("emotion", "neutral"),
                    "confidence": emotion_data.get("confidence", 0.5),
                    "valence": emotion_data.get("valence", 0.0),
                    "arousal": emotion_data.get("arousal", 0.2),
                    "timestamp": datetime.utcnow()
                }
            
            if intent_data:
                yield {
                    "type": "intent_classified",
                    "intent": intent_data.get("intent", "general_inquiry"),
                    "confidence": intent_data.get("confidence", 0.5),
                    "entities": entities,
                    "timestamp": datetime.utcnow()
                }
            
            if objections:
                yield {
                    "type": "objection_detected",
                    "objections": objections,
                    "timestamp": datetime.utcnow()
                }
            
            # Step 4: Response generation (< 500ms)
            response_start = time.time()
            
            response_strategy = await self._determine_response_strategy_fast(
                transcript, emotion_data, intent_data, objections, conversation_context
            )
            
            response_text = await self._generate_response_optimized(
                transcript, response_strategy, entities, conversation_context
            )
            
            metrics.response_generation_ms = int((time.time() - response_start) * 1000)
            
            # Step 5: Text-to-speech (< 400ms)
            tts_start = time.time()
            
            audio_response = await self._text_to_speech_optimized(
                response_text, agent_id, response_strategy
            )
            
            metrics.text_to_speech_ms = int((time.time() - tts_start) * 1000)
            metrics.total_processing_ms = int((time.time() - start_time) * 1000)
            
            # Final response
            yield {
                "type": "response_generated",
                "text": response_text,
                "strategy": response_strategy,
                "audio_url": audio_response.get("url", ""),
                "processing_time_ms": metrics.total_processing_ms,
                "performance_metrics": metrics.__dict__,
                "timestamp": datetime.utcnow()
            }
            
            # Log performance metrics
            await self._log_performance_metrics(
                session_id, transcript, metrics, audio_quality
            )
            
            # Log to console if response time exceeds target
            if metrics.total_processing_ms > self.target_response_time_ms:
                logger.warning(
                    f"Response time {metrics.total_processing_ms}ms exceeded target "
                    f"{self.target_response_time_ms}ms for session {session_id}"
                )
            else:
                logger.info(
                    f"Processed voice input in {metrics.total_processing_ms}ms "
                    f"(target: {self.target_response_time_ms}ms)"
                )
        
        except Exception as e:
            logger.error(f"Voice processing error for session {session_id}: {e}")
            yield {
                "type": "error",
                "message": "I'm experiencing some technical difficulties. Let me try again.",
                "error_code": "PROCESSING_ERROR",
                "timestamp": datetime.utcnow()
            }
    
    async def _preprocess_audio_optimized(self, audio_data: bytes) -> tuple[AudioQuality, np.ndarray]:
        """Optimized audio preprocessing with quality assessment"""
        try:
            # Convert audio data
            audio_segment = AudioSegment.from_raw(
                audio_data, 
                sample_width=2, 
                frame_rate=self.sample_rate, 
                channels=1
            )
            
            # Convert to numpy
            audio_np = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
            audio_np = audio_np / 32768.0  # Normalize to [-1, 1]
            
            # Quick quality assessment
            volume_level = np.sqrt(np.mean(audio_np**2))
            noise_estimate = np.std(audio_np[:min(1600, len(audio_np))])  # First 100ms
            
            quality = AudioQuality(
                clarity_score=min(1.0, volume_level * 10),
                noise_level=min(1.0, noise_estimate * 5),
                volume_consistency=1.0 - np.std(np.abs(audio_np)),
                is_speech=volume_level > 0.01  # Basic speech detection
            )
            
            # Apply noise reduction if needed
            if quality.noise_level > 0.2:
                audio_np = nr.reduce_noise(y=audio_np, sr=self.sample_rate, prop_decrease=0.8)
            
            # Voice activity detection
            frame_length = int(self.sample_rate * self.frame_duration_ms / 1000)
            has_speech = False
            
            for i in range(0, len(audio_np), frame_length):
                frame = audio_np[i:i+frame_length]
                if len(frame) == frame_length:
                    frame_bytes = (frame * 32767).astype(np.int16).tobytes()
                    if self.vad.is_speech(frame_bytes, self.sample_rate):
                        has_speech = True
                        break
            
            quality.is_speech = has_speech
            
            return quality, audio_np
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            return AudioQuality(), np.array([])
    
    async def _speech_to_text_optimized(self, audio_data: np.ndarray) -> str:
        """Optimized speech-to-text processing"""
        try:
            # In production, this would use a local Whisper model or optimized API call
            # For now, simulate fast processing
            
            if len(audio_data) < 1600:  # Less than 100ms of audio
                return ""
            
            # Cache key based on audio characteristics
            audio_hash = hash(audio_data.tobytes()[:1000])  # Hash first 1000 bytes
            
            if audio_hash in self.cache:
                return self.cache[audio_hash]
            
            # Simulate API call to OpenAI Whisper
            import tempfile
            import soundfile as sf
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                sf.write(tmp_file.name, audio_data, self.sample_rate)
                
                # This would be replaced with local Whisper model for production
                with open(tmp_file.name, "rb") as audio_file:
                    response = await asyncio.to_thread(
                        openai.Audio.transcribe,
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )
                    
                    transcript = response.text.strip()
                    
                    # Cache the result
                    if len(transcript) > 0:
                        self.cache[audio_hash] = transcript
                    
                    return transcript
                    
        except Exception as e:
            logger.error(f"Speech-to-text failed: {e}")
            return ""
    
    async def _analyze_audio_features(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Extract audio features for emotion detection"""
        try:
            if len(audio_data) < 1600:
                return {}
            
            # Extract basic audio features
            features = {}
            
            # Energy and volume
            features["rms_energy"] = float(np.sqrt(np.mean(audio_data**2)))
            features["zero_crossing_rate"] = float(np.mean(librosa.feature.zero_crossing_rate(audio_data)))
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate)
            features["spectral_centroid"] = float(np.mean(spectral_centroids))
            
            # Pitch estimation (basic)
            fundamental_freq = librosa.yin(audio_data, fmin=80, fmax=300)
            features["fundamental_frequency"] = float(np.mean(fundamental_freq[fundamental_freq > 0]))
            
            return features
            
        except Exception as e:
            logger.error(f"Audio feature extraction failed: {e}")
            return {}
    
    async def _detect_emotion_fast(self, text: str, audio_features: Dict[str, Any]) -> Dict[str, Any]:
        """Fast emotion detection using cached models and heuristics"""
        try:
            # Use simple keyword-based detection for speed
            text_lower = text.lower()
            
            # Emotional keywords
            emotion_keywords = {
                "joy": ["great", "wonderful", "excellent", "love", "perfect", "amazing"],
                "anger": ["terrible", "awful", "hate", "angry", "frustrated", "mad"],
                "fear": ["worried", "scared", "nervous", "anxious", "afraid"],
                "sadness": ["disappointed", "sad", "unhappy", "depressed"],
                "surprise": ["wow", "amazing", "incredible", "unbelievable"],
                "neutral": ["okay", "fine", "alright", "yes", "no"]
            }
            
            detected_emotion = "neutral"
            confidence = 0.5
            
            for emotion, keywords in emotion_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        detected_emotion = emotion
                        confidence = 0.8
                        break
                if confidence > 0.5:
                    break
            
            # Adjust based on audio features
            if audio_features.get("rms_energy", 0) > 0.1:
                if detected_emotion == "neutral":
                    detected_emotion = "excited"
                confidence = min(1.0, confidence + 0.1)
            
            # Map to valence/arousal
            emotion_mapping = {
                "joy": {"valence": 0.8, "arousal": 0.7},
                "anger": {"valence": -0.8, "arousal": 0.9},
                "fear": {"valence": -0.6, "arousal": 0.8},
                "sadness": {"valence": -0.7, "arousal": 0.3},
                "surprise": {"valence": 0.1, "arousal": 0.8},
                "excited": {"valence": 0.6, "arousal": 0.9},
                "neutral": {"valence": 0.0, "arousal": 0.2}
            }
            
            mapping = emotion_mapping.get(detected_emotion, {"valence": 0.0, "arousal": 0.2})
            
            return {
                "emotion": detected_emotion,
                "confidence": confidence,
                "valence": mapping["valence"],
                "arousal": mapping["arousal"]
            }
            
        except Exception as e:
            logger.error(f"Fast emotion detection failed: {e}")
            return {
                "emotion": "neutral",
                "confidence": 0.5,
                "valence": 0.0,
                "arousal": 0.2
            }
    
    async def _classify_intent_fast(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fast intent classification using keyword matching"""
        try:
            text_lower = text.lower()
            
            # Intent patterns
            intent_patterns = {
                "property_search": ["looking for", "want to buy", "need", "searching", "find"],
                "schedule_viewing": ["see", "visit", "tour", "viewing", "appointment", "schedule"],
                "budget_discussion": ["budget", "afford", "cost", "price", "expensive", "cheap"],
                "location_preferences": ["area", "neighborhood", "location", "where", "near"],
                "financing_help": ["mortgage", "loan", "financing", "pre-approved", "bank"],
                "market_information": ["market", "prices", "trends", "conditions", "value"],
                "property_features": ["bedrooms", "bathrooms", "kitchen", "garage", "yard"],
                "timeline_discussion": ["when", "timeline", "soon", "urgent", "time"],
                "general_inquiry": ["tell me", "information", "help", "questions"]
            }
            
            detected_intent = "general_inquiry"
            confidence = 0.5
            
            for intent, patterns in intent_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        detected_intent = intent
                        confidence = 0.8
                        break
                if confidence > 0.5:
                    break
            
            return {
                "intent": detected_intent,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Fast intent classification failed: {e}")
            return {
                "intent": "general_inquiry",
                "confidence": 0.5
            }
    
    async def _detect_objections_fast(self, text: str) -> List[str]:
        """Fast objection detection using pattern matching"""
        try:
            text_lower = text.lower()
            objections = []
            
            objection_patterns = {
                "price_too_high": ["expensive", "too much", "can't afford", "over budget", "costly"],
                "wrong_location": ["too far", "wrong area", "bad neighborhood", "location"],
                "timing_concerns": ["not ready", "too soon", "need time", "rushing"],
                "need_more_info": ["more details", "need to know", "tell me more", "information"],
                "comparison_shopping": ["other options", "looking around", "comparing", "alternatives"]
            }
            
            for objection_type, patterns in objection_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        objections.append(objection_type)
                        break
            
            return objections
            
        except Exception as e:
            logger.error(f"Fast objection detection failed: {e}")
            return []
    
    async def _extract_entities_fast(self, text: str) -> Dict[str, List[str]]:
        """Fast entity extraction using regex and keywords"""
        try:
            import re
            
            entities = {
                "locations": [],
                "prices": [],
                "numbers": [],
                "property_types": []
            }
            
            # Extract prices
            price_patterns = [
                r'\$[\d,]+(?:k|K|000)?',
                r'\$?[\d,]+\s*(?:thousand|million|k|K|M)'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, text)
                entities["prices"].extend(matches)
            
            # Extract numbers
            number_pattern = r'\b\d+\b'
            entities["numbers"] = re.findall(number_pattern, text)
            
            # Property types
            property_types = ["house", "condo", "apartment", "townhouse", "commercial", "land"]
            for prop_type in property_types:
                if prop_type in text.lower():
                    entities["property_types"].append(prop_type)
            
            return entities
            
        except Exception as e:
            logger.error(f"Fast entity extraction failed: {e}")
            return {}
    
    async def _determine_response_strategy_fast(
        self, 
        text: str, 
        emotion_data: Dict[str, Any], 
        intent_data: Dict[str, Any],
        objections: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fast response strategy determination"""
        
        strategy = {
            "tone": "professional",
            "pace": "normal",
            "approach": "direct",
            "template_category": "general"
        }
        
        # Adjust based on emotion
        emotion = emotion_data.get("emotion", "neutral")
        if emotion in ["anger", "frustrated"]:
            strategy["tone"] = "empathetic"
            strategy["pace"] = "slow"
            strategy["approach"] = "calming"
        elif emotion in ["joy", "excited"]:
            strategy["tone"] = "enthusiastic"
            strategy["approach"] = "encouraging"
        elif emotion in ["fear", "nervous"]:
            strategy["tone"] = "reassuring"
            strategy["pace"] = "slow"
            strategy["approach"] = "supportive"
        
        # Adjust based on intent
        intent = intent_data.get("intent", "general_inquiry")
        if intent == "property_search":
            strategy["template_category"] = "qualification"
        elif intent == "schedule_viewing":
            strategy["template_category"] = "scheduling"
        elif intent == "budget_discussion":
            strategy["template_category"] = "budget"
        
        # Handle objections
        if objections:
            primary_objection = objections[0]
            if primary_objection == "price_too_high":
                strategy["template_category"] = "objection_price"
            elif primary_objection == "wrong_location":
                strategy["template_category"] = "objection_location"
        
        return strategy
    
    async def _generate_response_optimized(
        self,
        text: str,
        strategy: Dict[str, Any],
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Optimized response generation using templates and patterns"""
        
        try:
            template_category = strategy.get("template_category", "general")
            templates = self.response_templates.get(template_category, 
                                                  self.response_templates["qualification"])
            
            # Select template based on context
            import random
            base_response = random.choice(templates)
            
            # Personalize with extracted entities
            if entities.get("property_types"):
                prop_type = entities["property_types"][0]
                base_response += f" I have some excellent {prop_type} options that might be perfect."
            
            if entities.get("prices"):
                price = entities["prices"][0]
                base_response += f" With your {price} budget range, we have great opportunities available."
            
            # Adjust tone
            tone = strategy.get("tone", "professional")
            if tone == "enthusiastic":
                base_response = base_response.replace(".", "!")
            elif tone == "empathetic":
                base_response = "I completely understand. " + base_response
            elif tone == "reassuring":
                base_response = "Don't worry, " + base_response.lower()
            
            return base_response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I'd be happy to help you with that. Could you tell me more about what you're looking for?"
    
    async def _text_to_speech_optimized(
        self,
        text: str,
        agent_id: str,
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimized text-to-speech processing"""
        try:
            # This would integrate with ElevenLabs API or local TTS
            # For now, return a mock response
            
            return {
                "url": f"/api/v1/voice/audio/{hash(text)}",
                "duration_seconds": len(text) / 20,  # Approximate duration
                "quality_score": 0.95
            }
            
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            return {"url": "", "duration_seconds": 0, "quality_score": 0}
    
    async def _update_session_state(self, session_id: str, status: str):
        """Update real-time session state"""
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                
                stmt = select(RealTimeConversationSession).where(
                    RealTimeConversationSession.session_id == session_id
                )
                result = await db.execute(stmt)
                session = result.scalar_one_or_none()
                
                if session:
                    session.status = status
                    session.last_activity = datetime.utcnow()
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"Failed to update session state: {e}")
    
    async def _log_performance_metrics(
        self,
        session_id: str,
        transcript: str,
        metrics: ProcessingMetrics,
        audio_quality: AudioQuality
    ):
        """Log performance metrics for analysis"""
        try:
            async with AsyncSessionLocal() as db:
                # Update session metrics
                from sqlalchemy import select
                
                stmt = select(RealTimeConversationSession).where(
                    RealTimeConversationSession.session_id == session_id
                )
                result = await db.execute(stmt)
                session = result.scalar_one_or_none()
                
                if session:
                    # Update performance metrics
                    if not session.response_times:
                        session.response_times = []
                    
                    session.response_times.append(metrics.total_processing_ms)
                    # Keep only last 10 response times
                    session.response_times = session.response_times[-10:]
                    
                    session.audio_quality_current = audio_quality.clarity_score
                    session.total_turns += 1
                    
                    if metrics.total_processing_ms <= self.target_response_time_ms:
                        session.successful_interactions += 1
                    
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"Failed to log performance metrics: {e}")

# Create singleton instance
real_time_voice_processor = RealTimeVoiceProcessor()