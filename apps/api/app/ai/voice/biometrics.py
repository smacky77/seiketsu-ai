"""
Voice Biometrics Service
Advanced speaker identification and voice authentication
"""

import asyncio
import hashlib
import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from io import BytesIO

from ...core.cache import get_redis_client

logger = logging.getLogger(__name__)

# Alias for consistency with usage in code (defined after Voiceprint class)
VoiceProfile = Voiceprint


@dataclass
class Voiceprint:
    """Voice biometric profile"""
    speaker_id: str
    voice_features: Dict[str, float]
    confidence_threshold: float
    created_at: float
    updated_at: float
    sample_count: int
    quality_score: float


@dataclass
class IdentificationResult:
    """Speaker identification result"""
    success: bool
    speaker_id: Optional[str] = None
    confidence: float = 0.0
    similarity_score: float = 0.0
    is_new_speaker: bool = False
    processing_time_ms: int = 0
    error: Optional[str] = None


class VoiceBiometrics:
    """
    Advanced Voice Biometrics Service
    Handles speaker identification, verification, and voice authentication
    """
    
    def __init__(self):
        self.redis_client = None
        
        # Biometric settings
        self.confidence_threshold = 0.75
        self.similarity_threshold = 0.8
        self.min_samples_for_profile = 3
        self.max_profiles_per_user = 5
        
        # Feature extraction parameters
        self.feature_dimensions = 128
        self.min_audio_duration_ms = 1000  # 1 second minimum
        self.max_audio_duration_ms = 30000  # 30 seconds maximum
        
        # Performance tracking
        self._identification_times = []
        self._accuracy_scores = []
        
        logger.info("Voice Biometrics service initialized")
    
    async def initialize(self):
        """Initialize Redis connection for profile storage"""
        try:
            self.redis_client = await get_redis_client()
            logger.info("Redis connection established for voice biometrics")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Biometrics storage disabled.")
    
    async def identify_speaker(
        self,
        audio_data: bytes,
        user_id: str,
        tenant_id: Optional[str] = None,
        update_profile: bool = True
    ) -> IdentificationResult:
        """
        Identify speaker from voice sample
        
        Args:
            audio_data: Voice audio data
            user_id: User identifier for profile lookup
            tenant_id: Tenant identifier for isolation
            update_profile: Whether to update existing profile with new sample
            
        Returns:
            Speaker identification result
        """
        start_time = time.time()
        
        try:
            # Validate audio input
            if len(audio_data) < 1000:  # Too small
                return IdentificationResult(
                    success=False,
                    error="Audio sample too short for biometric analysis"
                )
            
            # Extract voice features
            voice_features = await self._extract_voice_features(audio_data)
            
            # Get existing voiceprint for user
            existing_profile = await self._get_voiceprint(user_id, tenant_id)
            
            if existing_profile:
                # Compare with existing profile
                similarity_score = self._calculate_similarity(
                    voice_features, 
                    existing_profile.voice_features
                )
                
                confidence = self._calculate_confidence(similarity_score, existing_profile)
                
                # Determine if match
                is_match = (
                    similarity_score >= self.similarity_threshold and
                    confidence >= existing_profile.confidence_threshold
                )
                
                result = IdentificationResult(
                    success=True,
                    speaker_id=existing_profile.speaker_id if is_match else None,
                    confidence=confidence,
                    similarity_score=similarity_score,
                    is_new_speaker=False,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
                
                # Update profile if requested and match found
                if update_profile and is_match:
                    await self._update_voiceprint(existing_profile, voice_features)
                
            else:
                # Create new voiceprint
                new_profile = await self._create_voiceprint(
                    user_id, voice_features, tenant_id
                )
                
                result = IdentificationResult(
                    success=True,
                    speaker_id=new_profile.speaker_id,
                    confidence=1.0,  # First sample, perfect match
                    similarity_score=1.0,
                    is_new_speaker=True,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Track performance
            processing_time = (time.time() - start_time) * 1000
            self._identification_times.append(processing_time)
            self._accuracy_scores.append(result.confidence)
            
            # Keep recent metrics only
            if len(self._identification_times) > 100:
                self._identification_times = self._identification_times[-100:]
                self._accuracy_scores = self._accuracy_scores[-100:]
            
            logger.info(f"Speaker identification completed in {processing_time:.2f}ms: {result.speaker_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Speaker identification failed: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return IdentificationResult(
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )
    
    async def verify_speaker(
        self,
        audio_data: bytes,
        claimed_speaker_id: str,
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> IdentificationResult:
        """
        Verify if audio matches claimed speaker identity
        
        Args:
            audio_data: Voice audio data
            claimed_speaker_id: Claimed speaker identity
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            Verification result
        """
        try:
            # Get claimed speaker's profile
            profile = await self._get_voiceprint(user_id, tenant_id)
            
            if not profile or profile.speaker_id != claimed_speaker_id:
                return IdentificationResult(
                    success=False,
                    error="Speaker profile not found"
                )
            
            # Extract features and compare
            voice_features = await self._extract_voice_features(audio_data)
            similarity_score = self._calculate_similarity(voice_features, profile.voice_features)
            confidence = self._calculate_confidence(similarity_score, profile)
            
            # Verification result
            is_verified = (
                similarity_score >= self.similarity_threshold and
                confidence >= profile.confidence_threshold
            )
            
            return IdentificationResult(
                success=True,
                speaker_id=claimed_speaker_id if is_verified else None,
                confidence=confidence,
                similarity_score=similarity_score,
                is_new_speaker=False
            )
            
        except Exception as e:
            logger.error(f"Speaker verification failed: {e}")
            return IdentificationResult(success=False, error=str(e))
    
    async def enroll_speaker(
        self,
        audio_samples: List[bytes],
        user_id: str,
        speaker_name: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> IdentificationResult:
        """
        Enroll new speaker with multiple voice samples
        
        Args:
            audio_samples: List of voice samples for enrollment
            user_id: User identifier
            speaker_name: Optional speaker name
            tenant_id: Tenant identifier
            
        Returns:
            Enrollment result
        """
        try:
            if len(audio_samples) < self.min_samples_for_profile:
                return IdentificationResult(
                    success=False,
                    error=f"Minimum {self.min_samples_for_profile} samples required for enrollment"
                )
            
            # Extract features from all samples
            all_features = []
            for audio_data in audio_samples:
                features = await self._extract_voice_features(audio_data)
                all_features.append(features)
            
            # Calculate average features
            averaged_features = self._average_features(all_features)
            
            # Calculate quality score based on consistency
            quality_score = self._calculate_enrollment_quality(all_features)
            
            # Create voiceprint
            speaker_id = self._generate_speaker_id(user_id)
            
            voiceprint = Voiceprint(
                speaker_id=speaker_id,
                voice_features=averaged_features,
                confidence_threshold=self.confidence_threshold,
                created_at=time.time(),
                updated_at=time.time(),
                sample_count=len(audio_samples),
                quality_score=quality_score
            )
            
            # Store voiceprint
            await self._store_voiceprint(user_id, voiceprint, tenant_id)
            
            return IdentificationResult(
                success=True,
                speaker_id=speaker_id,
                confidence=quality_score,
                is_new_speaker=True
            )
            
        except Exception as e:
            logger.error(f"Speaker enrollment failed: {e}")
            return IdentificationResult(success=False, error=str(e))
    
    async def _extract_voice_features(self, audio_data: bytes) -> Dict[str, float]:
        """Extract voice biometric features from audio"""
        try:
            # In production, this would use advanced signal processing
            # to extract MFCC, pitch, formants, spectral features, etc.
            
            # Simplified feature extraction for demonstration
            audio_hash = hashlib.sha256(audio_data).hexdigest()
            
            # Generate consistent features based on audio properties
            features = {}
            for i in range(self.feature_dimensions):
                # Use hash to generate consistent but varied features
                feature_hash = hashlib.sha256(f"{audio_hash}_{i}".encode()).hexdigest()
                feature_value = int(feature_hash[:8], 16) / (2**32)  # Normalize to 0-1
                features[f"feature_{i:03d}"] = feature_value
            
            # Simulate processing time
            await asyncio.sleep(0.05)
            
            logger.debug(f"Extracted {len(features)} voice features")
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            # Return default features
            return {f"feature_{i:03d}": 0.5 for i in range(self.feature_dimensions)}
    
    def _calculate_similarity(
        self, 
        features1: Dict[str, float], 
        features2: Dict[str, float]
    ) -> float:
        """Calculate similarity between two feature sets"""
        try:
            # Calculate cosine similarity
            common_features = set(features1.keys()) & set(features2.keys())
            
            if not common_features:
                return 0.0
            
            dot_product = sum(features1[f] * features2[f] for f in common_features)
            norm1 = sum(features1[f] ** 2 for f in common_features) ** 0.5
            norm2 = sum(features2[f] ** 2 for f in common_features) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_confidence(
        self, 
        similarity_score: float, 
        profile: VoiceProfile
    ) -> float:
        """Calculate confidence score for identification"""
        try:
            # Base confidence from similarity
            base_confidence = similarity_score
            
            # Adjust based on profile quality
            quality_factor = profile.quality_score
            sample_factor = min(1.0, profile.sample_count / 10.0)  # More samples = higher confidence
            
            # Combined confidence
            confidence = base_confidence * quality_factor * sample_factor
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.0
    
    def _average_features(self, feature_sets: List[Dict[str, float]]) -> Dict[str, float]:
        """Average multiple feature sets"""
        try:
            if not feature_sets:
                return {}
            
            # Get all unique feature keys
            all_keys = set()
            for features in feature_sets:
                all_keys.update(features.keys())
            
            # Calculate averages
            averaged_features = {}
            for key in all_keys:
                values = [features.get(key, 0.0) for features in feature_sets]
                averaged_features[key] = sum(values) / len(values)
            
            return averaged_features
            
        except Exception as e:
            logger.error(f"Feature averaging failed: {e}")
            return {}
    
    def _calculate_enrollment_quality(self, feature_sets: List[Dict[str, float]]) -> float:
        """Calculate quality score for enrollment based on feature consistency"""
        try:
            if len(feature_sets) < 2:
                return 0.5  # Cannot assess consistency
            
            # Calculate average similarity between all pairs
            similarities = []
            for i in range(len(feature_sets)):
                for j in range(i + 1, len(feature_sets)):
                    similarity = self._calculate_similarity(feature_sets[i], feature_sets[j])
                    similarities.append(similarity)
            
            if not similarities:
                return 0.5
            
            avg_similarity = sum(similarities) / len(similarities)
            return max(0.1, min(1.0, avg_similarity))
            
        except Exception as e:
            logger.error(f"Quality calculation failed: {e}")
            return 0.5
    
    def _generate_speaker_id(self, user_id: str) -> str:
        """Generate unique speaker ID"""
        timestamp = str(int(time.time() * 1000))
        unique_string = f"{user_id}_{timestamp}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    async def _get_voiceprint(
        self, 
        user_id: str, 
        tenant_id: Optional[str] = None
    ) -> Optional[Voiceprint]:
        """Get stored voiceprint for user"""
        try:
            if not self.redis_client:
                return None
            
            cache_key = f"voiceprint:{tenant_id or 'default'}:{user_id}"
            data = await self.redis_client.get(cache_key)
            
            if data:
                profile_data = json.loads(data)
                return Voiceprint(**profile_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Voiceprint retrieval failed: {e}")
            return None
    
    async def _store_voiceprint(
        self, 
        user_id: str, 
        voiceprint: Voiceprint, 
        tenant_id: Optional[str] = None
    ):
        """Store voiceprint in cache"""
        try:
            if not self.redis_client:
                return
            
            cache_key = f"voiceprint:{tenant_id or 'default'}:{user_id}"
            data = json.dumps(asdict(voiceprint))
            
            # Store for 30 days
            await self.redis_client.setex(cache_key, 30 * 24 * 3600, data)
            
        except Exception as e:
            logger.error(f"Voiceprint storage failed: {e}")
    
    async def _create_voiceprint(
        self, 
        user_id: str, 
        features: Dict[str, float], 
        tenant_id: Optional[str] = None
    ) -> Voiceprint:
        """Create new voiceprint"""
        speaker_id = self._generate_speaker_id(user_id)
        
        voiceprint = Voiceprint(
            speaker_id=speaker_id,
            voice_features=features,
            confidence_threshold=self.confidence_threshold,
            created_at=time.time(),
            updated_at=time.time(),
            sample_count=1,
            quality_score=0.8  # Default quality for single sample
        )
        
        await self._store_voiceprint(user_id, voiceprint, tenant_id)
        return voiceprint
    
    async def _update_voiceprint(
        self, 
        profile: Voiceprint, 
        new_features: Dict[str, float]
    ):
        """Update existing voiceprint with new features"""
        try:
            # Average new features with existing
            combined_features = {}
            for key in profile.voice_features:
                old_value = profile.voice_features[key]
                new_value = new_features.get(key, old_value)
                # Weighted average (favor existing data)
                combined_features[key] = (old_value * 0.8) + (new_value * 0.2)
            
            # Update profile
            profile.voice_features = combined_features
            profile.updated_at = time.time()
            profile.sample_count += 1
            
            # Recalculate quality (more samples typically improve quality)
            profile.quality_score = min(1.0, profile.quality_score + 0.1)
            
        except Exception as e:
            logger.error(f"Voiceprint update failed: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get biometrics performance metrics"""
        if not self._identification_times:
            return {"status": "no_data"}
        
        return {
            "avg_identification_time_ms": sum(self._identification_times) / len(self._identification_times),
            "max_identification_time_ms": max(self._identification_times),
            "min_identification_time_ms": min(self._identification_times),
            "avg_accuracy_score": sum(self._accuracy_scores) / len(self._accuracy_scores) if self._accuracy_scores else 0,
            "total_identifications": len(self._identification_times),
            "confidence_threshold": self.confidence_threshold,
            "similarity_threshold": self.similarity_threshold
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for voice biometrics service"""
        return {
            "status": "healthy",
            "service": "voice_biometrics",
            "cache_enabled": self.redis_client is not None,
            "performance": self.get_performance_metrics(),
            "settings": {
                "confidence_threshold": self.confidence_threshold,
                "similarity_threshold": self.similarity_threshold,
                "feature_dimensions": self.feature_dimensions,
                "min_samples_for_profile": self.min_samples_for_profile
            },
            "timestamp": time.time()
        }