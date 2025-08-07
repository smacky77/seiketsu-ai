#!/usr/bin/env python3
"""
Production-ready server runner for Seiketsu AI API
Handles both simple and full server modes
"""
import sys
import os
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import uvicorn
        import fastapi
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install required dependencies"""
    logger.info("📦 Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "fastapi", "uvicorn[standard]", "python-dotenv", 
            "pydantic", "pydantic-settings", "aiosqlite"
        ], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def start_server():
    """Start the appropriate server"""
    if not check_dependencies():
        logger.warning("⚠️  Dependencies not found. Installing...")
        if not install_dependencies():
            logger.error("❌ Failed to install dependencies")
            sys.exit(1)
    
    # Try to import and start simple server
    try:
        logger.info("🚀 Starting Seiketsu AI API Server")
        logger.info("📍 URL: http://localhost:8000")
        logger.info("📖 Docs: http://localhost:8000/docs")
        
        # Use subprocess to run uvicorn directly
        cmd = [
            sys.executable, "-m", "uvicorn",
            "simple_server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()