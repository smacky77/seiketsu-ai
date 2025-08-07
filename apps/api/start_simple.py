#!/usr/bin/env python3
"""
Simple server startup script for Seiketsu AI API
Bypasses complex dependencies and starts a basic working server
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_simple_server():
    """Start the simplest possible FastAPI server"""
    try:
        import uvicorn
        from simple_server import app
        
        logger.info("🚀 Starting Seiketsu AI API - Simple Mode")
        logger.info("📍 Server: http://localhost:8000")
        logger.info("📖 Docs: http://localhost:8000/docs")
        logger.info("🔧 Health Check: http://localhost:8000/api/health")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("🔧 Please install: pip install fastapi uvicorn")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_simple_server()