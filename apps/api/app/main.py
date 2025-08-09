"""
Seiketsu AI Backend - Main FastAPI Application
Optimized enterprise-grade real estate voice agent platform
"""

import logging
import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import uvicorn

# Core imports
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import APIException, ValidationException, AuthenticationException
from app.core.dependencies import get_current_user, get_db, get_redis_client
from app.core.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestTracingMiddleware,
    PerformanceMiddleware
)

# Database and cache
from app.core.database import init_database, close_database
from app.core.cache import init_redis, close_redis

# API routers
from app.routers import (
    auth,
    users,
    voice,
    leads,
    properties,
    analytics,
    webhooks,
    admin,
    health,
    client_management
)

# Services
from app.services.circuit_breaker import CircuitBreakerService
from app.services.metrics import MetricsService

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Global services
circuit_breaker_service = CircuitBreakerService()
metrics_service = MetricsService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup/shutdown events
    """
    # Startup
    logger.info("🚀 Starting Seiketsu AI API...")
    
    try:
        # Initialize database connection
        await init_database()
        logger.info("✅ Database connection established")
        
        # Initialize Redis cache
        await init_redis()
        logger.info("✅ Redis cache connected")
        
        # Initialize services
        await circuit_breaker_service.initialize()
        await metrics_service.initialize()
        logger.info("✅ Core services initialized")
        
        # Health check for external services
        await perform_startup_health_checks()
        logger.info("✅ External service health checks passed")
        
        logger.info("🎉 Seiketsu AI API startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise
    
    finally:
        # Shutdown
        logger.info("🔄 Shutting down Seiketsu AI API...")
        
        try:
            # Close database connections
            await close_database()
            logger.info("✅ Database connections closed")
            
            # Close Redis connections
            await close_redis()
            logger.info("✅ Redis connections closed")
            
            # Cleanup services
            await circuit_breaker_service.cleanup()
            await metrics_service.cleanup()
            logger.info("✅ Services cleanup complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {str(e)}")
        
        logger.info("👋 Seiketsu AI API shutdown complete")

async def perform_startup_health_checks():
    """
    Perform health checks for external services on startup
    """
    checks = [
        ("ElevenLabs API", check_elevenlabs_health),
        ("OpenAI API", check_openai_health),
        ("Supabase", check_supabase_health),
    ]
    
    failed_checks = []
    
    for service_name, check_func in checks:
        try:
            await asyncio.wait_for(check_func(), timeout=10)
            logger.info(f"✅ {service_name} health check passed")
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ {service_name} health check timed out")
            failed_checks.append(service_name)
        except Exception as e:
            logger.error(f"❌ {service_name} health check failed: {str(e)}")
            failed_checks.append(service_name)
    
    if failed_checks:
        logger.warning(f"⚠️ Some external services are unavailable: {failed_checks}")
    else:
        logger.info("✅ All external service health checks passed")

async def check_elevenlabs_health():
    """Check ElevenLabs API health"""
    if not settings.ELEVEN_LABS_API_KEY:
        raise Exception("ElevenLabs API key not configured")
    # Add actual health check logic here

async def check_openai_health():
    """Check OpenAI API health"""
    if not settings.OPENAI_API_KEY:
        raise Exception("OpenAI API key not configured")
    # Add actual health check logic here

async def check_supabase_health():
    """Check Supabase health"""
    if not settings.SUPABASE_URL:
        raise Exception("Supabase URL not configured")
    # Add actual health check logic here

def create_application() -> FastAPI:
    """
    Create and configure FastAPI application
    """
    
    # Create FastAPI instance with lifespan
    app = FastAPI(
        title="Seiketsu AI API",
        description="Enterprise Real Estate Voice Agent Platform",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
        debug=settings.DEBUG
    )
    
    # Add middleware (order matters!)
    setup_middleware(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Include API routers
    setup_routers(app)
    
    # Setup custom OpenAPI schema
    setup_openapi_schema(app)
    
    return app

def setup_middleware(app: FastAPI):
    """
    Configure application middleware in correct order
    """
    
    # Security headers middleware (first for security)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"]
    )
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom middleware
    app.add_middleware(RequestTracingMiddleware)
    app.add_middleware(PerformanceMiddleware)
    app.add_middleware(RateLimitMiddleware, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)

def setup_exception_handlers(app: FastAPI):
    """
    Configure custom exception handlers
    """
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        logger.error(f"API Exception: {exc.message}", extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        })
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                    "code": exc.error_code,
                    "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None
                }
            }
        )
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        logger.warning(f"Validation error: {exc.message}", extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors
        })
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "ValidationError",
                    "message": exc.message,
                    "details": exc.errors,
                    "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None
                }
            }
        )
    
    @app.exception_handler(AuthenticationException)
    async def auth_exception_handler(request: Request, exc: AuthenticationException):
        logger.warning(f"Authentication error: {exc.message}", extra={
            "path": request.url.path,
            "method": request.method
        })
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "type": "AuthenticationError",
                    "message": exc.message,
                    "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": exc.__class__.__name__
        }, exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "InternalServerError",
                    "message": "An internal server error occurred",
                    "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None
                }
            }
        )

def setup_routers(app: FastAPI):
    """
    Configure API routers with prefixes and tags
    """
    
    # Health check endpoint (no prefix for load balancers)
    app.include_router(health.router, tags=["Health"])
    
    # Authentication endpoints
    app.include_router(
        auth.router,
        prefix="/api/v1/auth",
        tags=["Authentication"]
    )
    
    # User management
    app.include_router(
        users.router,
        prefix="/api/v1/users",
        tags=["Users"],
        dependencies=[Depends(get_current_user)]
    )
    
    # Voice AI endpoints
    app.include_router(
        voice.router,
        prefix="/api/v1/voice",
        tags=["Voice AI"]
    )
    
    # Lead management
    app.include_router(
        leads.router,
        prefix="/api/v1/leads",
        tags=["Leads"],
        dependencies=[Depends(get_current_user)]
    )
    
    # Property management
    app.include_router(
        properties.router,
        prefix="/api/v1/properties",
        tags=["Properties"],
        dependencies=[Depends(get_current_user)]
    )
    
    # Analytics and reporting
    app.include_router(
        analytics.router,
        prefix="/api/v1/analytics",
        tags=["Analytics"],
        dependencies=[Depends(get_current_user)]
    )
    
    # Webhook endpoints
    app.include_router(
        webhooks.router,
        prefix="/api/v1/webhooks",
        tags=["Webhooks"]
    )
    
    # Client management
    app.include_router(
        client_management.router,
        prefix="/api/v1/clients",
        tags=["Client Management"]
    )
    
    # Admin endpoints
    app.include_router(
        admin.router,
        prefix="/api/v1/admin",
        tags=["Admin"]
    )

def setup_openapi_schema(app: FastAPI):
    """
    Customize OpenAPI schema
    """
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Seiketsu AI API",
            version=settings.APP_VERSION,
            description="""
# Seiketsu AI - Real Estate Voice Agent Platform

Enterprise-grade API for AI-powered real estate voice agents with advanced lead qualification, 
property intelligence, and multi-tenant architecture.

## Features
- 🎙️ **Voice AI Integration**: ElevenLabs voice synthesis with emotion detection
- 🏠 **Real Estate Intelligence**: MLS integration, property analytics, market insights
- 📞 **Lead Management**: Automated qualification, scoring, and CRM integration
- 🔐 **Enterprise Security**: Multi-tenant, RBAC, SOC2 compliant
- 📊 **Advanced Analytics**: Performance metrics, ROI tracking, conversation intelligence
- 🔄 **Webhooks**: Real-time integrations with CRM, calendar, and notification systems

## Authentication
This API uses JWT Bearer token authentication. Include your token in the Authorization header:
```
Authorization: Bearer your_jwt_token_here
```
            """,
            routes=app.routes,
            servers=[
                {"url": "https://api.seiketsu.ai", "description": "Production"},
                {"url": "https://staging-api.seiketsu.ai", "description": "Staging"},
                {"url": "http://localhost:8000", "description": "Development"}
            ]
        )
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
        
        # Add global security
        openapi_schema["security"] = [{"BearerAuth": []}]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi

# Create the application
app = create_application()

# Add root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Seiketsu AI API",
        "version": settings.APP_VERSION,
        "description": "Enterprise Real Estate Voice Agent Platform",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else "Contact support for API documentation",
        "status": "operational",
        "timestamp": time.time()
    }

# Metrics endpoint for monitoring
@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    return Response(
        content=await metrics_service.get_metrics(),
        media_type="text/plain"
    )

if __name__ == "__main__":
    # This allows running with python main.py for development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True
    )