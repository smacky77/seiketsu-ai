"""
AI Configuration for Seiketsu AI Platform
Centralized configuration for all AI services and models
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseSettings, Field


class AIModelType(str, Enum):
    """Supported AI model types"""
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    WHISPER_1 = "whisper-1"
    ELEVENLABS_VOICE = "elevenlabs"
    CUSTOM_FINE_TUNED = "custom"


class VoiceModel(str, Enum):
    """ElevenLabs voice models"""
    MULTILINGUAL_V2 = "eleven_multilingual_v2"
    MONOLINGUAL_V1 = "eleven_monolingual_v1"
    TURBO_V2 = "eleven_turbo_v2"


@dataclass
class ModelConfig:
    """Configuration for a specific AI model"""
    model_type: AIModelType
    model_id: str
    max_tokens: int
    temperature: float
    timeout: int
    retry_attempts: int
    cache_ttl: int
    cost_per_token: float


@dataclass 
class VoiceConfig:
    """Voice processing configuration"""
    voice_id: str
    model: VoiceModel
    stability: float
    similarity_boost: float
    style: float
    use_speaker_boost: bool


class AISettings(BaseSettings):
    """AI service configuration settings"""
    
    # Model Performance Settings
    RESPONSE_TIME_TARGET_MS: int = 180
    MAX_CONCURRENT_REQUESTS: int = 100
    MODEL_CACHE_SIZE: int = 1000
    CONTEXT_WINDOW_SIZE: int = 32000
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_ORG_ID: Optional[str] = Field(None, env="OPENAI_ORG_ID")
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_TIMEOUT: int = 30
    OPENAI_MAX_RETRIES: int = 3
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY: str = Field(..., env="ELEVENLABS_API_KEY")
    ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io/v1"
    ELEVENLABS_TIMEOUT: int = 30
    ELEVENLABS_CHUNK_SIZE: int = 1024
    
    # Voice Processing Settings
    DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    VOICE_STABILITY: float = 0.75
    VOICE_SIMILARITY_BOOST: float = 0.75
    VOICE_STYLE: float = 0.0
    VOICE_USE_SPEAKER_BOOST: bool = True
    
    # Audio Processing
    AUDIO_SAMPLE_RATE: int = 44100
    AUDIO_CHANNELS: int = 1
    AUDIO_CHUNK_SIZE: int = 1024
    AUDIO_FORMAT: str = "mp3"
    NOISE_REDUCTION_ENABLED: bool = True
    
    # Conversation AI Settings
    CONVERSATION_MEMORY_TURNS: int = 10
    CONVERSATION_TIMEOUT_SECONDS: int = 300
    MAX_FUNCTION_CALLS: int = 5
    ENABLE_FUNCTION_CALLING: bool = True
    
    # Real Estate Domain Settings
    LEAD_QUALIFICATION_THRESHOLD: float = 0.7
    PROPERTY_RECOMMENDATION_COUNT: int = 5
    MARKET_ANALYSIS_CACHE_HOURS: int = 24
    APPOINTMENT_BUFFER_MINUTES: int = 15
    
    # Model Management
    MODEL_VERSION_RETENTION: int = 5
    AB_TEST_TRAFFIC_SPLIT: float = 0.1
    MODEL_MONITORING_INTERVAL: int = 60
    AUTO_SCALING_ENABLED: bool = True
    
    # Analytics Settings
    SENTIMENT_ANALYSIS_ENABLED: bool = True
    ENGAGEMENT_TRACKING_ENABLED: bool = True
    PERFORMANCE_METRICS_ENABLED: bool = True
    ANALYTICS_BATCH_SIZE: int = 100
    
    # Caching Configuration
    REDIS_AI_CACHE_DB: int = 1
    RESPONSE_CACHE_TTL: int = 3600
    MODEL_CACHE_TTL: int = 86400
    CONVERSATION_CACHE_TTL: int = 1800
    
    # Security Settings
    RATE_LIMIT_PER_USER: int = 1000
    MAX_AUDIO_SIZE_MB: int = 25
    ALLOWED_AUDIO_FORMATS: List[str] = ["mp3", "wav", "m4a", "ogg", "webm"]
    CONTENT_MODERATION_ENABLED: bool = True
    
    # Multi-tenant Settings
    TENANT_ISOLATION_ENABLED: bool = True
    CUSTOM_MODEL_TRAINING_ENABLED: bool = True
    TENANT_RATE_LIMITS: Dict[str, int] = {}
    
    # Integration Settings
    CRM_SYNC_INTERVAL_MINUTES: int = 15
    WEBHOOK_RETRY_ATTEMPTS: int = 3
    WEBHOOK_TIMEOUT_SECONDS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Model configurations
MODEL_CONFIGS: Dict[str, ModelConfig] = {
    "gpt-4-conversation": ModelConfig(
        model_type=AIModelType.GPT_4,
        model_id="gpt-4",
        max_tokens=4000,
        temperature=0.7,
        timeout=30,
        retry_attempts=3,
        cache_ttl=1800,
        cost_per_token=0.00003
    ),
    "gpt-4-turbo-analysis": ModelConfig(
        model_type=AIModelType.GPT_4_TURBO,
        model_id="gpt-4-turbo-preview",
        max_tokens=4000,
        temperature=0.3,
        timeout=45,
        retry_attempts=3,
        cache_ttl=3600,
        cost_per_token=0.000015
    ),
    "gpt-3.5-turbo-quick": ModelConfig(
        model_type=AIModelType.GPT_3_5_TURBO,
        model_id="gpt-3.5-turbo",
        max_tokens=2000,
        temperature=0.5,
        timeout=15,
        retry_attempts=2,
        cache_ttl=900,
        cost_per_token=0.0000015
    ),
    "whisper-transcription": ModelConfig(
        model_type=AIModelType.WHISPER_1,
        model_id="whisper-1",
        max_tokens=0,
        temperature=0.0,
        timeout=30,
        retry_attempts=3,
        cache_ttl=3600,
        cost_per_token=0.0006
    )
}

# Voice configurations
VOICE_CONFIGS: Dict[str, VoiceConfig] = {
    "professional-female": VoiceConfig(
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
        model=VoiceModel.MULTILINGUAL_V2,
        stability=0.75,
        similarity_boost=0.75,
        style=0.0,
        use_speaker_boost=True
    ),
    "professional-male": VoiceConfig(
        voice_id="29vD33N1CtxCmqQRPOHJ",  # Drew
        model=VoiceModel.MULTILINGUAL_V2,
        stability=0.8,
        similarity_boost=0.8,
        style=0.0,
        use_speaker_boost=True
    ),
    "friendly-assistant": VoiceConfig(
        voice_id="EXAVITQu4vr4xnSDxMaL",  # Bella
        model=VoiceModel.MULTILINGUAL_V2,
        stability=0.7,
        similarity_boost=0.7,
        style=0.2,
        use_speaker_boost=True
    )
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "voice_response_time_ms": 180,
    "conversation_response_time_ms": 500,
    "model_accuracy_threshold": 0.95,
    "uptime_threshold": 0.999,
    "error_rate_threshold": 0.001
}

# Global AI settings instance
ai_settings = AISettings()