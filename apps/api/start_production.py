#!/usr/bin/env python3
"""
Production startup script for Seiketsu AI FastAPI Backend
"""
import os
import sys
import logging
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        # Check database connection
        from app.core.database import init_db
        await init_db()
        print("✅ Database connection successful")
        
        # Check Redis connection
        from app.core.cache import init_cache
        await init_cache()
        print("✅ Redis connection successful")
        
        # Check external services
        from app.services.voice_service import VoiceService
        voice_service = VoiceService()
        await voice_service.initialize()
        print("✅ Voice services initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Dependency check failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Seiketsu AI FastAPI Backend...")
    print("=" * 60)
    
    # Check environment
    environment = os.getenv("ENVIRONMENT", "development")
    print(f"🌍 Environment: {environment}")
    
    # Check required environment variables
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "ELEVEN_LABS_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print("✅ Environment variables configured")
    
    # Check dependencies
    try:
        dependencies_ok = asyncio.run(check_dependencies())
        if not dependencies_ok:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to check dependencies: {e}")
        sys.exit(1)
    
    print("=" * 60)
    print("🎉 All systems ready! Starting FastAPI server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/api/health")
    print("=" * 60)
    
    # Import and run the FastAPI app
    import uvicorn
    from main import app
    
    # Production configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=int(os.getenv("WORKERS", 4)),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=True,
        server_header=False,
        date_header=False,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )

if __name__ == "__main__":
    main()