# Deployment Runbook - Seiketsu AI Platform

## Overview
This runbook provides step-by-step procedures for deploying the Seiketsu AI enterprise real estate voice agent platform.

## Environment Overview
- **Development**: Local development environment
- **Staging**: Pre-production testing environment
- **Production**: Live production environment

---

## Pre-Deployment Checklist

### Code Quality Validation
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code review approved
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Documentation updated

### Infrastructure Validation
- [ ] Infrastructure health checks passed
- [ ] Database migrations tested
- [ ] Backup systems verified
- [ ] Monitoring alerts configured
- [ ] SSL certificates valid

### Configuration Validation
- [ ] Environment variables configured
- [ ] Feature flags set correctly
- [ ] API keys and secrets updated
- [ ] Third-party integrations tested
- [ ] Load balancer configuration verified

---

## Deployment Procedures

### 1. Frontend Deployment (Next.js)

#### Build and Deploy
```bash
# 1. Build application
cd apps/web
npm run build

# 2. Run pre-deployment tests
npm run test:e2e

# 3. Deploy to staging
npm run deploy:staging

# 4. Validate staging deployment
npm run validate:staging

# 5. Deploy to production
npm run deploy:production
```

#### Validation Steps
- [ ] Application loads correctly
- [ ] Authentication flow works
- [ ] Voice interface functional
- [ ] Dashboard displays data
- [ ] Mobile responsiveness verified

### 2. Backend API Deployment (FastAPI)

#### Deploy API Services
```bash
# 1. Navigate to API directory
cd apps/api

# 2. Run database migrations
python -m alembic upgrade head

# 3. Build Docker image
docker build -t seiketsu-api:$(git rev-parse --short HEAD) .

# 4. Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# 5. Run health checks
python scripts/health_check.py --env staging

# 6. Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

#### API Validation
- [ ] Health endpoint responds (200 OK)
- [ ] Authentication endpoints working
- [ ] Voice processing endpoints functional
- [ ] Real estate data APIs responding
- [ ] WebSocket connections stable

### 3. Infrastructure Deployment (Terraform)

#### Deploy Infrastructure
```bash
# 1. Navigate to infrastructure directory
cd infrastructure/terraform

# 2. Initialize Terraform
terraform init

# 3. Plan deployment
terraform plan -var-file=environments/prod.tfvars

# 4. Apply infrastructure changes
terraform apply -var-file=environments/prod.tfvars

# 5. Verify infrastructure
terraform output
```

#### Infrastructure Validation
- [ ] AWS resources provisioned correctly
- [ ] Load balancers healthy
- [ ] Auto-scaling groups configured
- [ ] Database connections established
- [ ] CDN distributions active

---

## Environment Configurations

### Production Environment Variables
```bash
# Application
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.seiketsu.ai
NEXT_PUBLIC_WS_URL=wss://ws.seiketsu.ai

# Database
DATABASE_URL=postgresql://user:pass@prod-db.seiketsu.ai:5432/seiketsu
REDIS_URL=redis://prod-redis.seiketsu.ai:6379

# External Services
ELEVENLABS_API_KEY=***
OPENAI_API_KEY=***
SUPABASE_URL=https://prod.supabase.co
SUPABASE_ANON_KEY=***

# Monitoring
SENTRY_DSN=***
DATADOG_API_KEY=***
```

### Staging Environment Variables
```bash
# Application
NODE_ENV=staging
NEXT_PUBLIC_API_URL=https://api-staging.seiketsu.ai
NEXT_PUBLIC_WS_URL=wss://ws-staging.seiketsu.ai

# Database
DATABASE_URL=postgresql://user:pass@staging-db.seiketsu.ai:5432/seiketsu
REDIS_URL=redis://staging-redis.seiketsu.ai:6379
```

---

## Rollback Procedures

### Emergency Rollback (< 5 minutes)

#### Frontend Rollback
```bash
# 1. Identify last known good version
git log --oneline -10

# 2. Quick rollback to previous version
cd apps/web
git checkout <previous-commit-hash>
npm run deploy:production:emergency

# 3. Verify rollback
curl -I https://seiketsu.ai
```

#### Backend Rollback
```bash
# 1. Rollback API deployment
cd apps/api
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# 2. Rollback database if needed
python -m alembic downgrade -1

# 3. Verify API health
curl https://api.seiketsu.ai/health
```

### Standard Rollback (15-30 minutes)

#### Complete Environment Rollback
```bash
# 1. Rollback infrastructure
cd infrastructure/terraform
terraform plan -var-file=environments/prod.tfvars -target=module.previous
terraform apply -var-file=environments/prod.tfvars -target=module.previous

# 2. Rollback application code
git revert <commit-hash>
git push origin main

# 3. Trigger redeployment
./scripts/deploy.sh --env production --version previous
```

---

## Post-Deployment Validation

### Automated Validation
```bash
# Run comprehensive post-deployment tests
./scripts/post-deployment-validation.sh

# Key validation points:
# - API health checks
# - Frontend accessibility
# - Database connectivity
# - External service integrations
# - Performance benchmarks
```

### Manual Validation Checklist
- [ ] **Frontend**: Login flow, voice interface, dashboard functionality
- [ ] **API**: All endpoints responding correctly
- [ ] **Voice**: ElevenLabs integration working
- [ ] **Real Estate**: Property data loading correctly
- [ ] **Performance**: Page load times < 2s
- [ ] **Monitoring**: All dashboards showing green status
- [ ] **Alerts**: No critical alerts firing

### Performance Validation
```bash
# Load testing
k6 run performance-tests/load-test.js

# Key metrics to verify:
# - Response time < 500ms (95th percentile)
# - Throughput > 1000 RPS
# - Error rate < 0.1%
# - Memory usage < 80%
# - CPU usage < 70%
```

---

## Communication Templates

### Pre-Deployment Notification
```
Subject: Seiketsu AI Deployment Starting - [DATE] [TIME]

Team,

Deployment of Seiketsu AI v[VERSION] is starting at [TIME].

Expected duration: [DURATION]
Affected services: [SERVICES]
Expected downtime: [DOWNTIME]

Deployment engineer: [NAME]
Monitoring: [MONITORING_LINK]

Updates will be provided every 15 minutes.
```

### Deployment Success Notification
```
Subject: Seiketsu AI Deployment Complete - SUCCESS

Team,

Deployment of Seiketsu AI v[VERSION] completed successfully at [TIME].

✅ All services healthy
✅ Performance metrics normal
✅ No alerts firing

Post-deployment validation: PASSED
Rollback plan: Not needed

Monitoring dashboard: [LINK]
```

### Deployment Failure Notification
```
Subject: Seiketsu AI Deployment - ISSUE DETECTED

Team,

Issue detected during deployment of v[VERSION] at [TIME].

Issue: [DESCRIPTION]
Impact: [IMPACT_LEVEL]
Action: Initiating rollback procedure

ETA for resolution: [TIME]
Incident commander: [NAME]

Updates will be provided every 5 minutes.
```

---

## Emergency Contacts

### Primary On-Call
- **DevOps Lead**: [NAME] - [PHONE] - [EMAIL]
- **Backend Lead**: [NAME] - [PHONE] - [EMAIL]
- **Frontend Lead**: [NAME] - [PHONE] - [EMAIL]

### Escalation Chain
1. Engineering Manager - [CONTACT]
2. VP of Engineering - [CONTACT]
3. CTO - [CONTACT]

### External Vendors
- **AWS Support**: Premium Support Case
- **Supabase**: Enterprise Support
- **ElevenLabs**: API Support

---

## Troubleshooting Common Issues

### Frontend Deployment Issues

#### Build Failures
```bash
# Clear cache and rebuild
npm run clean
rm -rf .next node_modules
npm install
npm run build
```

#### CDN Cache Issues
```bash
# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E123456789 --paths "/*"
```

### Backend Deployment Issues

#### Database Connection Issues
```bash
# Check database connectivity
python -c "import psycopg2; conn = psycopg2.connect('$DATABASE_URL'); print('Connected')"

# Check for blocking queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

#### Container Issues
```bash
# Check container logs
docker logs seiketsu-api-container

# Restart container
docker-compose restart api
```

### Infrastructure Issues

#### Load Balancer Problems
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...
```

#### Auto Scaling Issues
```bash
# Check auto scaling group
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names seiketsu-asg
```

---

## Metrics and KPIs

### Deployment Success Metrics
- **Deployment Success Rate**: > 95%
- **Deployment Duration**: < 30 minutes
- **Rollback Time**: < 5 minutes (emergency)
- **Post-Deployment Issues**: < 5%

### Service Level Indicators
- **Availability**: 99.9% uptime
- **Performance**: < 2s page load time
- **API Response**: < 500ms (95th percentile)
- **Error Rate**: < 0.1%

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-08-09 | Initial deployment runbook | Seiketsu Team |

---

*Last Updated: 2025-08-09*
*Next Review: 2025-09-09*