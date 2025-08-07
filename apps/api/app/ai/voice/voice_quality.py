"""
Voice Quality Assessment
Advanced audio quality analysis and enhancement recommendations
"""

import asyncio
import logging
import time
import numpy as np
from typing import Dict, Any, Optional, Tuple
from io import BytesIO
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Voice quality assessment metrics"""
    overall_score: float  # 0.0 - 1.0
    noise_level: float   # 0.0 - 1.0 (lower is better)
    clarity_score: float # 0.0 - 1.0
    volume_level: float  # 0.0 - 1.0
    frequency_balance: float  # 0.0 - 1.0
    duration_ms: int
    sample_rate: int
    channels: int
    recommendations: list[str]


class VoiceQualityAssessment:
    """
    Voice Quality Assessment Service
    Analyzes audio quality and provides enhancement recommendations
    """
    
    def __init__(self):
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.7,
            "fair": 0.5,
            "poor": 0.0
        }
        
        # Audio analysis parameters
        self.min_sample_rate = 16000
        self.target_sample_rate = 44100
        self.min_duration_ms = 100
        self.max_duration_ms = 300000  # 5 minutes
        
        logger.info("Voice Quality Assessment service initialized")
    
    async def assess_quality(
        self,
        audio_data: bytes,
        expected_duration_ms: Optional[int] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive voice quality assessment
        
        Args:
            audio_data: Raw audio bytes
            expected_duration_ms: Expected duration for validation
            context: Context for quality assessment (e.g., "phone_call", "studio")
            
        Returns:
            Quality assessment results
        """
        start_time = time.time()
        
        try:
            # Parse audio properties
            audio_properties = await self._analyze_audio_properties(audio_data)
            
            # Perform quality analysis
            quality_metrics = await self._analyze_quality_metrics(audio_data, audio_properties)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(quality_metrics, context)
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_score(quality_metrics)
            
            # Determine quality level
            quality_level = self._determine_quality_level(overall_score)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                "overall_score": overall_score,
                "quality_level": quality_level,
                "metrics": {
                    "noise_level": quality_metrics.noise_level,
                    "clarity_score": quality_metrics.clarity_score,
                    "volume_level": quality_metrics.volume_level,
                    "frequency_balance": quality_metrics.frequency_balance,
                    "duration_ms": quality_metrics.duration_ms,
                    "sample_rate": quality_metrics.sample_rate,
                    "channels": quality_metrics.channels
                },
                "audio_properties": audio_properties,
                "recommendations": recommendations,
                "processing_time_ms": processing_time,
                "timestamp": time.time()
            }
            
            logger.info(f"Quality assessment completed in {processing_time:.2f}ms: {quality_level} ({overall_score:.3f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {
                "overall_score": 0.0,
                "quality_level": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def assess_batch_quality(
        self,
        audio_files: list[bytes],
        context: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """Assess quality for multiple audio files in parallel"""
        try:
            tasks = [
                self.assess_quality(audio_data, context=context)
                for audio_data in audio_files
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            quality_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch quality assessment {i} failed: {result}")
                    quality_results.append({
                        "overall_score": 0.0,
                        "quality_level": "error",
                        "error": str(result)
                    })
                else:
                    quality_results.append(result)
            
            return quality_results
            
        except Exception as e:
            logger.error(f"Batch quality assessment failed: {e}")
            return [{"overall_score": 0.0, "quality_level": "error", "error": str(e)}] * len(audio_files)
    
    async def _analyze_audio_properties(self, audio_data: bytes) -> Dict[str, Any]:
        """Analyze basic audio properties"""
        try:
            # For production, you would use a library like librosa or pydub
            # This is a simplified implementation
            
            audio_size = len(audio_data)
            
            # Estimate properties based on common formats
            # This would be replaced with actual audio analysis
            estimated_duration = audio_size / (44100 * 2 * 2)  # Assume 44.1kHz, 16-bit, stereo
            
            return {
                "file_size_bytes": audio_size,
                "estimated_duration_seconds": estimated_duration,
                "estimated_sample_rate": 44100,
                "estimated_channels": 2,
                "format": "unknown",
                "bitrate_kbps": 0
            }
            
        except Exception as e:
            logger.error(f"Audio property analysis failed: {e}")
            return {
                "file_size_bytes": len(audio_data),
                "error": str(e)
            }
    
    async def _analyze_quality_metrics(
        self, 
        audio_data: bytes, 
        properties: Dict[str, Any]
    ) -> QualityMetrics:
        """Analyze detailed quality metrics"""
        try:
            # In production, this would use actual audio analysis libraries
            # This is a simplified implementation for demonstration
            
            file_size = len(audio_data)
            duration_ms = int(properties.get("estimated_duration_seconds", 1.0) * 1000)
            
            # Simulate quality analysis based on file properties
            # Real implementation would analyze frequency spectrum, SNR, etc.
            
            # Noise level estimation (lower is better)
            noise_level = min(0.8, max(0.1, 1.0 - (file_size / 1000000)))  # Larger files typically less compressed
            
            # Clarity score estimation
            clarity_score = max(0.2, min(0.95, file_size / 500000))
            
            # Volume level estimation
            volume_level = 0.7  # Would be calculated from actual audio analysis
            
            # Frequency balance estimation
            frequency_balance = 0.8  # Would analyze frequency spectrum
            
            recommendations = []
            
            return QualityMetrics(
                overall_score=0.0,  # Will be calculated later
                noise_level=noise_level,
                clarity_score=clarity_score,
                volume_level=volume_level,
                frequency_balance=frequency_balance,
                duration_ms=duration_ms,
                sample_rate=properties.get("estimated_sample_rate", 44100),
                channels=properties.get("estimated_channels", 2),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Quality metrics analysis failed: {e}")
            return QualityMetrics(
                overall_score=0.1,
                noise_level=0.9,
                clarity_score=0.1,
                volume_level=0.1,
                frequency_balance=0.1,
                duration_ms=0,
                sample_rate=0,
                channels=0,
                recommendations=["Error in quality analysis"]
            )
    
    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """Calculate weighted overall quality score"""
        try:
            # Weighted scoring
            weights = {
                "clarity": 0.3,
                "noise": 0.25,
                "volume": 0.2,
                "frequency": 0.15,
                "duration": 0.1
            }
            
            # Normalize scores (noise_level is inverted - lower is better)
            clarity_score = metrics.clarity_score
            noise_score = 1.0 - metrics.noise_level  # Invert noise level
            volume_score = min(1.0, metrics.volume_level * 1.5)  # Boost volume importance
            frequency_score = metrics.frequency_balance
            
            # Duration score (penalize very short or very long recordings)
            duration_score = 1.0
            if metrics.duration_ms < 500:  # Too short
                duration_score = metrics.duration_ms / 500.0
            elif metrics.duration_ms > 180000:  # Too long (over 3 minutes)
                duration_score = max(0.5, 1.0 - (metrics.duration_ms - 180000) / 180000)
            
            # Calculate weighted average
            overall_score = (
                clarity_score * weights["clarity"] +
                noise_score * weights["noise"] +
                volume_score * weights["volume"] +
                frequency_score * weights["frequency"] +
                duration_score * weights["duration"]
            )
            
            return round(max(0.0, min(1.0, overall_score)), 3)
            
        except Exception as e:
            logger.error(f"Overall score calculation failed: {e}")
            return 0.1
    
    def _determine_quality_level(self, score: float) -> str:
        """Determine quality level from score"""
        if score >= self.quality_thresholds["excellent"]:
            return "excellent"
        elif score >= self.quality_thresholds["good"]:
            return "good"
        elif score >= self.quality_thresholds["fair"]:
            return "fair"
        else:
            return "poor"
    
    def _generate_recommendations(
        self, 
        metrics: QualityMetrics, 
        context: Optional[str] = None
    ) -> list[str]:
        """Generate improvement recommendations based on quality analysis"""
        recommendations = []
        
        try:
            # Noise level recommendations
            if metrics.noise_level > 0.7:
                recommendations.append("High background noise detected. Use noise reduction or record in quieter environment.")
            elif metrics.noise_level > 0.4:
                recommendations.append("Moderate background noise detected. Consider using noise reduction.")
            
            # Clarity recommendations
            if metrics.clarity_score < 0.5:
                recommendations.append("Low audio clarity. Check microphone quality and positioning.")
            elif metrics.clarity_score < 0.7:
                recommendations.append("Audio clarity could be improved. Ensure proper microphone distance.")
            
            # Volume recommendations
            if metrics.volume_level < 0.3:
                recommendations.append("Audio volume is too low. Increase recording level or speak louder.")
            elif metrics.volume_level > 0.9:
                recommendations.append("Audio volume is too high. Risk of clipping. Reduce recording level.")
            
            # Frequency balance recommendations
            if metrics.frequency_balance < 0.6:
                recommendations.append("Unbalanced frequency response. Check audio equipment or room acoustics.")
            
            # Duration recommendations
            if metrics.duration_ms < 500:
                recommendations.append("Recording is very short. Longer samples provide better quality analysis.")
            elif metrics.duration_ms > 300000:
                recommendations.append("Recording is very long. Consider splitting into shorter segments.")
            
            # Sample rate recommendations
            if metrics.sample_rate < 22050:
                recommendations.append("Low sample rate detected. Higher sample rates (44.1kHz+) improve quality.")
            
            # Context-specific recommendations
            if context == "phone_call" and metrics.overall_score < 0.6:
                recommendations.append("For phone calls, ensure good cellular/internet connection and use headset if possible.")
            elif context == "studio" and metrics.overall_score < 0.8:
                recommendations.append("For studio recordings, use professional microphone and treated acoustic space.")
            
            # No issues found
            if not recommendations and metrics.overall_score > 0.8:
                recommendations.append("Audio quality is good. No specific improvements needed.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return ["Error generating recommendations"]
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality assessment statistics"""
        # In production, this would track historical quality metrics
        return {
            "total_assessments": 0,
            "average_quality_score": 0.0,
            "quality_distribution": {
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0
            },
            "common_issues": [],
            "performance_metrics": {
                "avg_processing_time_ms": 0.0
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for voice quality assessment service"""
        return {
            "status": "healthy",
            "service": "voice_quality_assessment",
            "thresholds": self.quality_thresholds,
            "parameters": {
                "min_sample_rate": self.min_sample_rate,
                "target_sample_rate": self.target_sample_rate,
                "min_duration_ms": self.min_duration_ms,
                "max_duration_ms": self.max_duration_ms
            },
            "timestamp": time.time()
        }