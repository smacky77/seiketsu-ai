"""
Seiketsu AI FastAPI Main Application
Enterprise Real Estate Voice Agent Platform
"""
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging
import sys
from datetime import datetime
import uuid

# Import core modules
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.middleware import (
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    RateLimitMiddleware,
    TenantContextMiddleware,
    SecurityHeadersMiddleware
)
from app.core.security_middleware import (
    AdvancedRateLimitMiddleware,
    TenantIsolationMiddleware,
    ThreatDetectionMiddleware,
    DataValidationMiddleware
)

# Import API routes
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.leads import router as leads_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.voice_agents import router as voice_agents_router
from app.api.v1.properties import router as properties_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.voice import router as voice_router
from app.api.v1.voice_enhanced import router as voice_enhanced_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.admin import router as admin_router

# Import services for health checks
from app.services.health_service import HealthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events"""
    
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Seiketsu AI API Server...")
    
    try:
        # Initialize database
        logger.info("📁 Initializing database connection...")
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Initialize health service
        app.state.health_service = HealthService()
        await app.state.health_service.initialize()
        logger.info("✅ Health service initialized")
        
        # Initialize caching
        from app.core.cache import init_cache
        await init_cache()
        logger.info("✅ Cache system initialized")
        
        # Initialize external services
        from app.services.elevenlabs_service import ElevenLabsService
        app.state.voice_service = ElevenLabsService()
        await app.state.voice_service.initialize()
        logger.info("✅ ElevenLabs voice service initialized")
        
        logger.info("🎉 Seiketsu AI API Server startup complete!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Seiketsu AI API Server...")
    
    # Cleanup resources
    if hasattr(app.state, 'health_service'):
        await app.state.health_service.cleanup()
    
    if hasattr(app.state, 'voice_service'):
        await app.state.voice_service.cleanup()
    
    logger.info("✅ Server shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Seiketsu AI API",
    description="Enterprise Real Estate Voice Agent Platform - API Documentation",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
    # Generate unique request ID for tracking
    generate_unique_id_function=lambda route: f"{route.tags[0]}_{route.name}" if route.tags else route.name
)

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


# Add enhanced security middleware stack
app.add_middleware(DataValidationMiddleware)
app.add_middleware(ThreatDetectionMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Add advanced rate limiting middleware
app.add_middleware(AdvancedRateLimitMiddleware)

# Add tenant isolation middleware for multi-tenant support
app.add_middleware(TenantIsolationMiddleware)

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Seiketsu AI - Enterprise Real Estate Voice Agent Platform",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "api_endpoints": {
            "health": "/api/health",
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "organizations": "/api/v1/organizations",
            "leads": "/api/v1/leads",
            "conversations": "/api/v1/conversations",
            "voice_agents": "/api/v1/voice-agents",
            "properties": "/api/v1/properties",
            "analytics": "/api/v1/analytics",
            "voice": "/api/v1/voice",
            "webhooks": "/api/v1/webhooks",
            "admin": "/api/v1/admin"
        }
    }


# Health check endpoints
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/api/health/detailed", tags=["Health"])
async def detailed_health_check(request: Request):
    """Detailed health check with component status"""
    health_service: HealthService = request.app.state.health_service
    health_status = await health_service.get_detailed_health()
    
    return health_status


@app.get("/api/health/ready", tags=["Health"])
async def readiness_check(request: Request):
    """Kubernetes readiness probe endpoint"""
    health_service: HealthService = request.app.state.health_service
    is_ready = await health_service.is_ready()
    
    if is_ready:
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "timestamp": datetime.utcnow().isoformat()}
        )


@app.get("/api/health/live", tags=["Health"])
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - app.state.start_time).total_seconds()
    }


# Include API routers
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"]
)

app.include_router(
    organizations_router,
    prefix="/api/v1/organizations",
    tags=["Organizations"]
)

app.include_router(
    leads_router,
    prefix="/api/v1/leads",
    tags=["Leads"]
)

app.include_router(
    conversations_router,
    prefix="/api/v1/conversations",
    tags=["Conversations"]
)

app.include_router(
    voice_agents_router,
    prefix="/api/v1/voice-agents",
    tags=["Voice Agents"]
)

app.include_router(
    properties_router,
    prefix="/api/v1/properties",
    tags=["Properties"]
)

app.include_router(
    analytics_router,
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)

app.include_router(
    voice_router,
    prefix="/api/v1/voice",
    tags=["Voice Processing"]
)

# Include enhanced voice endpoints
app.include_router(
    voice_enhanced_router,
    prefix="/api/v1/voice",
    tags=["Voice Processing"]
)

app.include_router(
    webhooks_router,
    prefix="/api/v1/webhooks",
    tags=["Webhooks"]
)

app.include_router(
    admin_router,
    prefix="/api/v1/admin",
    tags=["Administration"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.error(
        f"Unhandled exception in request {request_id}: {exc}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers)
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Store startup time for uptime calculation
app.state.start_time = datetime.utcnow()


# Development server configuration
if __name__ == "__main__":
    logger.info("🔥 Starting Seiketsu AI API in development mode...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        reload_dirs=["app"] if settings.ENVIRONMENT == "development" else None,
        log_level="info",
        access_log=True,
        server_header=False,  # Security: hide server header
        date_header=False,    # Security: hide date header
        proxy_headers=True,   # Enable proxy headers for load balancing
        forwarded_allow_ips="*",  # Allow forwarded IPs
        loop="asyncio",
        http="httptools",
        ws="websockets"
    )


# Production server configuration function
def create_production_app():
    """Create production-ready app instance"""
    return app


# Custom startup message
@app.on_event("startup")
async def startup_message():
    """Display startup message with configuration"""
    logger.info("=" * 60)
    logger.info("🏢 Seiketsu AI - Enterprise Real Estate Voice Agent Platform")
    logger.info("=" * 60)
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🚀 Server: FastAPI {app.version}")
    logger.info(f"🔗 Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Connected'}")
    logger.info(f"🎙️  Voice Service: ElevenLabs Integration")
    logger.info(f"🏠 Multi-tenant: Enabled")
    logger.info(f"🔐 Authentication: JWT with refresh tokens")
    logger.info(f"📊 Analytics: Real-time conversation tracking")
    logger.info("=" * 60)
    logger.info("✅ Server is ready to handle requests!")
    logger.info("=" * 60)