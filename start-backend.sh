#!/bin/bash

# Seiketsu AI Backend Server Startup Script
# This script starts the FastAPI backend server for the Seiketsu AI platform

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Seiketsu AI Backend Server Startup${NC}"
echo -e "${BLUE}====================================${NC}"

# Change to API directory
cd "$(dirname "$0")/apps/api"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install --upgrade pip
pip install fastapi "uvicorn[standard]" python-dotenv pydantic pydantic-settings aiosqlite

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Using development defaults.${NC}"
fi

# Start the server
echo -e "${GREEN}🎉 Starting Seiketsu AI API Server...${NC}"
echo -e "${GREEN}📍 Server URL: http://localhost:8000${NC}"
echo -e "${GREEN}📖 API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}🔧 Health Check: http://localhost:8000/api/health${NC}"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo ""

# Start server (try full server first, fallback to simple)
if python main.py 2>/dev/null; then
    echo -e "${GREEN}✅ Full server started successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Full server failed, starting simple server...${NC}"
    python start_simple.py
fi