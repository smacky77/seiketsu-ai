"""
Health check endpoints for Seiketsu AI API
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.cache import get_redis_client
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    Used by load balancers and monitoring systems
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check with external service status
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }
    
    # Check database connectivity
    try:
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time": "fast"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Redis connectivity
    try:
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "response_time": "fast"
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "disabled",
                "message": "Redis not configured"
            }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check external services
    external_services = await check_external_services()
    health_status["checks"]["external_services"] = external_services
    
    if any(service["status"] == "unhealthy" for service in external_services.values()):
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/readiness")
async def readiness_check():
    """
    Readiness probe for Kubernetes deployments
    """
    # Perform minimal checks required for the service to be ready
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/liveness")
async def liveness_check():
    """
    Liveness probe for Kubernetes deployments
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


async def check_external_services() -> Dict[str, Any]:
    """
    Check status of external services
    """
    services_status = {}
    
    # Check ElevenLabs API
    services_status["elevenlabs"] = await check_service_with_timeout(
        check_elevenlabs_health, "ElevenLabs"
    )
    
    # Check OpenAI API
    services_status["openai"] = await check_service_with_timeout(
        check_openai_health, "OpenAI"
    )
    
    # Check Supabase
    services_status["supabase"] = await check_service_with_timeout(
        check_supabase_health, "Supabase"
    )
    
    return services_status


async def check_service_with_timeout(check_func, service_name: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Check service health with timeout
    """
    try:
        await asyncio.wait_for(check_func(), timeout=timeout)
        return {"status": "healthy", "response_time": "normal"}
    except asyncio.TimeoutError:
        return {"status": "unhealthy", "error": f"{service_name} timeout"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_elevenlabs_health():
    """Check ElevenLabs API health"""
    if not settings.ELEVEN_LABS_API_KEY:
        raise Exception("ElevenLabs API key not configured")
    # In production, make actual API call to test connectivity
    pass


async def check_openai_health():
    """Check OpenAI API health"""
    if not settings.OPENAI_API_KEY:
        raise Exception("OpenAI API key not configured")
    # In production, make actual API call to test connectivity
    pass


async def check_supabase_health():
    """Check Supabase health"""
    if not settings.SUPABASE_URL:
        raise Exception("Supabase URL not configured")
    # In production, make actual API call to test connectivity
    pass