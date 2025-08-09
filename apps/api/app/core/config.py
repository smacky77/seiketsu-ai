"""
Configuration settings for Seiketsu AI API
"""
import os
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import validator
import secrets


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    APP_NAME: str = "Seiketsu AI API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://seiketsu_user:seiketsu_pass@localhost/seiketsu_ai"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_POOL_SIZE: int = 10
    REDIS_TIMEOUT: int = 5
    
    # ElevenLabs settings
    ELEVEN_LABS_API_KEY: str = os.getenv("ELEVEN_LABS_API_KEY", "")
    ELEVEN_LABS_BASE_URL: str = "https://api.elevenlabs.io/v1"
    ELEVEN_LABS_TIMEOUT: int = 30
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # 21dev.ai integration settings
    TWENTYONEDEV_API_KEY: str = os.getenv("TWENTYONE_DEV_API_KEY", "")
    TWENTYONEDEV_BASE_URL: str = os.getenv("TWENTYONE_DEV_BASE_URL", "https://api.21dev.ai/v1")
    TWENTYONEDEV_TIMEOUT: int = 30
    
    # Container Studio settings
    CONTAINER_STUDIO_URL: str = os.getenv("CONTAINER_STUDIO_URL", "")
    CONTAINER_STUDIO_TOKEN: str = os.getenv("CONTAINER_STUDIO_TOKEN", "")
    
    # AWS ECS settings
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    ECS_CLUSTER_NAME: str = os.getenv("ECS_CLUSTER_NAME", "seiketsu-ai-cluster")
    
    # Celery settings for background jobs
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    CELERY_TIMEZONE: str = "UTC"
    
    # Voice processing settings
    VOICE_RESPONSE_TIMEOUT_MS: int = int(os.getenv("VOICE_RESPONSE_TIMEOUT_MS", "2000"))
    VOICE_QUALITY_BITRATE: int = int(os.getenv("VOICE_QUALITY_BITRATE", "128"))
    MAX_CONVERSATION_DURATION_MINUTES: int = int(os.getenv("MAX_CONVERSATION_DURATION_MINUTES", "60"))
    
    # Multi-tenant settings
    ENABLE_MULTI_TENANT: bool = os.getenv("ENABLE_MULTI_TENANT", "true").lower() == "true"
    DEFAULT_TENANT_ID: str = os.getenv("DEFAULT_TENANT_ID", "default")
    
    # Third-party service settings
    # Twilio settings
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Stripe settings
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Real estate data settings
    MLS_API_KEY: str = os.getenv("MLS_API_KEY", "")
    MLS_BASE_URL: str = os.getenv("MLS_BASE_URL", "https://api.mlsgrid.com/v2")
    ZILLOW_API_KEY: str = os.getenv("ZILLOW_API_KEY", "")
    
    # Lead scoring settings
    LEAD_SCORING_MODEL_PATH: str = os.getenv("LEAD_SCORING_MODEL_PATH", "models/lead_scoring.pkl")
    LEAD_QUALIFICATION_THRESHOLD: float = float(os.getenv("LEAD_QUALIFICATION_THRESHOLD", "0.7"))
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://seiketsu.ai",
        "https://app.seiketsu.ai"
    ]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Allowed hosts for security
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "seiketsu.ai",
        "*.seiketsu.ai",
        "api.seiketsu.ai"
    ]
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Rate limiting settings
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200
    
    # File upload settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_AUDIO_FORMATS: List[str] = ["mp3", "wav", "m4a", "ogg"]
    
    # Webhook settings
    WEBHOOK_TIMEOUT: int = 30
    WEBHOOK_RETRY_ATTEMPTS: int = 3
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Email settings (for notifications)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Circuit breaker settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    
    # Rate limiting settings
    DEFAULT_RATE_LIMIT_PER_SECOND: float = 10.0
    DEFAULT_RATE_LIMIT_BURST: int = 20
    
    # Usage tracking settings
    USAGE_TRACKING_ENABLED: bool = True
    USAGE_ALERT_THRESHOLDS: Dict[str, int] = {
        "warning": 80,
        "critical": 95
    }
    
    # Billing settings
    BILLING_CURRENCY: str = "usd"
    BILLING_TAX_RATE: float = 0.08  # 8% default sales tax
    BILLING_PLATFORM_FEE_RATE: float = 0.05  # 5% platform fee
    
    # Monitoring settings
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Testing settings
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://test_user:test_pass@localhost/seiketsu_test"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()