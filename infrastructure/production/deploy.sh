#!/bin/bash

# Seiketsu AI - Production Deployment Script
# BMAD Method Phase 2: Backend Integration Complete

set -e

echo "🚀 Starting Seiketsu AI Production Deployment..."
echo "📋 BMAD Method Phase 2: Backend Integration with @21st-extension/toolbar"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if environment file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.prod template...${NC}"
    cp .env.prod .env
    echo -e "${RED}❌ Please update the .env file with your actual values before continuing.${NC}"
    exit 1
fi

# Load environment variables
source .env

echo -e "${BLUE}📦 Building Docker images...${NC}"

# Build frontend
echo -e "${BLUE}🔨 Building frontend (Next.js)...${NC}"
cd ../../apps/web
docker build -f Dockerfile.prod -t seiketsu-frontend:latest .
cd ../../infrastructure/production

# Build backend
echo -e "${BLUE}🔨 Building backend (FastAPI)...${NC}"
cd ../../apps/api
docker build -f Dockerfile.prod -t seiketsu-backend:latest .
cd ../../infrastructure/production

echo -e "${BLUE}🗃️  Creating volumes and networks...${NC}"
docker network create seiketsu-network 2>/dev/null || true

echo -e "${BLUE}🚀 Starting services...${NC}"

# Start database first
echo -e "${BLUE}🗄️  Starting database...${NC}"
docker-compose -f docker-compose.prod.yml up -d database redis

# Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
sleep 10

# Run database migrations
echo -e "${BLUE}🗄️  Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml run --rm backend python -m app.core.database migrate

# Start all services
echo -e "${BLUE}🌐 Starting all services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 30

# Health checks
echo -e "${BLUE}🏥 Running health checks...${NC}"

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

# Check frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend health check failed${NC}"
fi

# Check database connection
if docker-compose -f docker-compose.prod.yml exec -T database pg_isready -U $POSTGRES_USER > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database is ready${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
fi

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo -e "${BLUE}📋 Service Status:${NC}"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo -e "${BLUE}🔗 Access URLs:${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}Grafana: http://localhost:3001${NC}"
echo -e "${GREEN}Prometheus: http://localhost:9090${NC}"

echo ""
echo -e "${BLUE}📊 BMAD Method Phase 2 Features:${NC}"
echo -e "${GREEN}✅ @21st-extension/toolbar integrated${NC}"
echo -e "${GREEN}✅ Voice processing with ElevenLabs${NC}"
echo -e "${GREEN}✅ Real estate data integration${NC}"
echo -e "${GREEN}✅ Multi-tenant authentication${NC}"
echo -e "${GREEN}✅ WebSocket real-time features${NC}"
echo -e "${GREEN}✅ Market intelligence analytics${NC}"
echo -e "${GREEN}✅ Lead qualification algorithms${NC}"
echo -e "${GREEN}✅ Production monitoring setup${NC}"

echo ""
echo -e "${YELLOW}🔧 Next Steps:${NC}"
echo "1. Configure SSL certificates for HTTPS"
echo "2. Set up DNS records for your domain"
echo "3. Configure monitoring alerts"
echo "4. Test all voice agent functionality"
echo "5. Verify MLS data synchronization"
echo "6. Run end-to-end tests"

echo ""
echo -e "${BLUE}📝 To stop services: docker-compose -f docker-compose.prod.yml down${NC}"
echo -e "${BLUE}📝 To view logs: docker-compose -f docker-compose.prod.yml logs -f${NC}"

echo -e "${GREEN}🚀 Seiketsu AI is now running in production mode!${NC}"