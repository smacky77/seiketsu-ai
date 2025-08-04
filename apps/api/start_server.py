"""
Server startup script for Seiketsu AI API
"""
import uvicorn
import asyncio
import logging
import sys
import os
from main import app
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/server.log") if os.path.exists("logs") else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


def start_development_server():
    """Start development server with hot reload"""
    logger.info("🔥 Starting Seiketsu AI API in DEVELOPMENT mode...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info",
        access_log=True,
        server_header=False,
        date_header=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
        loop="asyncio"
    )


def start_production_server():
    """Start production server with optimized settings"""
    logger.info("🚀 Starting Seiketsu AI API in PRODUCTION mode...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Multiple workers for production
        log_level="warning",
        access_log=False,  # Disable access logs in production
        server_header=False,
        date_header=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
        loop="asyncio",
        backlog=2048,
        keepalive_timeout=5,
        h11_max_incomplete_event_size=16384
    )


def start_test_server():
    """Start test server for automated testing"""
    logger.info("🧪 Starting Seiketsu AI API in TEST mode...")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,  # Different port for testing
        log_level="critical",  # Minimal logging for tests
        access_log=False,
        server_header=False,
        date_header=False,
        loop="asyncio"
    )


if __name__ == "__main__":
    """Main entry point - detect environment and start appropriate server"""
    
    environment = settings.ENVIRONMENT.lower()
    
    try:
        if environment == "development":
            start_development_server()
        elif environment == "production":
            start_production_server()
        elif environment == "test":
            start_test_server()
        else:
            logger.error(f"❌ Unknown environment: {environment}")
            logger.info("Valid environments: development, production, test")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Server shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)