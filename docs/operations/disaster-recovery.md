# Disaster Recovery Runbook - Seiketsu AI Platform

## Overview
This runbook provides comprehensive disaster recovery procedures for the Seiketsu AI enterprise real estate voice agent platform, ensuring business continuity during major service disruptions.

---

## Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

### Service Level Agreements

#### Critical Services (Tier 1)
```yaml
Frontend Web Application:
  RTO: 30 minutes
  RPO: 5 minutes
  Availability: 99.9%
  Business Impact: Complete service outage

Backend API Services:
  RTO: 15 minutes
  RPO: 1 minute
  Availability: 99.95%
  Business Impact: Complete service outage

User Authentication:
  RTO: 15 minutes
  RPO: 1 minute
  Availability: 99.95%
  Business Impact: No user access
```

#### Important Services (Tier 2)
```yaml
Voice Processing:
  RTO: 60 minutes
  RPO: 15 minutes
  Availability: 99.5%
  Business Impact: Degraded user experience

Real Estate Data:
  RTO: 60 minutes
  RPO: 30 minutes
  Availability: 99.5%
  Business Impact: Stale property information

Analytics Dashboard:
  RTO: 4 hours
  RPO: 1 hour
  Availability: 99.0%
  Business Impact: No business insights
```

#### Supporting Services (Tier 3)
```yaml
Monitoring Systems:
  RTO: 2 hours
  RPO: 1 hour
  Availability: 98.0%
  Business Impact: Reduced visibility

Documentation Systems:
  RTO: 8 hours
  RPO: 4 hours
  Availability: 95.0%
  Business Impact: Operational inconvenience

Development Tools:
  RTO: 24 hours
  RPO: 8 hours
  Availability: 95.0%
  Business Impact: Development delays
```

---

## Backup Procedures

### Database Backup Strategy

#### Production Database (PostgreSQL)
```bash
# Automated daily full backup
#!/bin/bash
# scripts/backup-database.sh

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="seiketsu_backup_${BACKUP_DATE}.sql"
S3_BUCKET="seiketsu-backups"

# Create backup
pg_dump $DATABASE_URL > /tmp/$BACKUP_FILE

# Compress backup
gzip /tmp/$BACKUP_FILE

# Upload to S3 with encryption
aws s3 cp "/tmp/${BACKUP_FILE}.gz" "s3://${S3_BUCKET}/database/daily/" \
  --server-side-encryption AES256 \
  --storage-class STANDARD_IA

# Cleanup local files
rm "/tmp/${BACKUP_FILE}.gz"

# Verify backup integrity
aws s3 ls "s3://${S3_BUCKET}/database/daily/${BACKUP_FILE}.gz"

echo "Backup completed: ${BACKUP_FILE}.gz"
```

#### Continuous Backup (Point-in-Time Recovery)
```bash
# Enable WAL archiving for continuous backup
# postgresql.conf settings:
archive_mode = on
archive_command = 'aws s3 cp %p s3://seiketsu-backups/wal/%f'
wal_level = replica
max_wal_senders = 3

# Backup retention policy
Daily backups: 30 days
Weekly backups: 12 weeks  
Monthly backups: 12 months
Annual backups: 7 years
```

#### Read Replica Configuration
```yaml
# Multi-AZ read replica setup
Primary Database:
  Instance: db.r6g.xlarge
  Location: us-east-1a
  Backup Window: 03:00-04:00 UTC
  
Read Replica 1:
  Instance: db.r6g.xlarge
  Location: us-east-1b
  Lag Target: < 1 second
  
Read Replica 2:
  Instance: db.r6g.large
  Location: us-west-2a
  Lag Target: < 5 seconds
  Purpose: Cross-region DR
```

### Application Code Backup

#### Git Repository Strategy
```bash
# Multiple repository mirrors
Primary: GitHub Enterprise
Mirror 1: GitLab (daily sync)
Mirror 2: AWS CodeCommit (hourly sync)
Local Backup: Daily tar.gz to S3

# Automated repository backup
#!/bin/bash
# scripts/backup-repositories.sh

REPOS=("seiketsu-web" "seiketsu-api" "seiketsu-infrastructure")
BACKUP_DATE=$(date +%Y%m%d)

for repo in "${REPOS[@]}"; do
  # Clone repository
  git clone --mirror "https://github.com/seiketsu/${repo}.git" "/tmp/${repo}_${BACKUP_DATE}.git"
  
  # Create archive
  tar -czf "/tmp/${repo}_${BACKUP_DATE}.tar.gz" "/tmp/${repo}_${BACKUP_DATE}.git"
  
  # Upload to S3
  aws s3 cp "/tmp/${repo}_${BACKUP_DATE}.tar.gz" "s3://seiketsu-backups/repositories/"
  
  # Cleanup
  rm -rf "/tmp/${repo}_${BACKUP_DATE}.git" "/tmp/${repo}_${BACKUP_DATE}.tar.gz"
done
```

### Configuration and Secrets Backup

#### Environment Configuration Backup
```bash
# scripts/backup-configurations.sh
#!/bin/bash

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
CONFIG_BACKUP="config_backup_${BACKUP_DATE}"

# Create backup directory
mkdir -p "/tmp/${CONFIG_BACKUP}"

# Backup Kubernetes configurations
kubectl get configmaps --all-namespaces -o yaml > "/tmp/${CONFIG_BACKUP}/configmaps.yaml"
kubectl get secrets --all-namespaces -o yaml > "/tmp/${CONFIG_BACKUP}/secrets.yaml"

# Backup Terraform state (encrypted)
aws s3 sync s3://seiketsu-terraform-state "/tmp/${CONFIG_BACKUP}/terraform-state/"

# Backup environment variables (sanitized)
env | grep -E '^(NODE_ENV|API_URL|DATABASE_URL)' > "/tmp/${CONFIG_BACKUP}/env-vars.txt"

# Create encrypted archive
tar -czf "/tmp/${CONFIG_BACKUP}.tar.gz" "/tmp/${CONFIG_BACKUP}"
gpg --cipher-algo AES256 --compress-algo 1 --symmetric --output "/tmp/${CONFIG_BACKUP}.tar.gz.gpg" "/tmp/${CONFIG_BACKUP}.tar.gz"

# Upload encrypted backup
aws s3 cp "/tmp/${CONFIG_BACKUP}.tar.gz.gpg" "s3://seiketsu-backups/configurations/"

# Cleanup
rm -rf "/tmp/${CONFIG_BACKUP}" "/tmp/${CONFIG_BACKUP}.tar.gz" "/tmp/${CONFIG_BACKUP}.tar.gz.gpg"
```

### File Storage Backup

#### User-Generated Content
```bash
# Backup user uploads and generated content
#!/bin/bash
# scripts/backup-user-content.sh

# Sync user uploads to backup bucket
aws s3 sync s3://seiketsu-user-uploads s3://seiketsu-backups/user-content/ \
  --delete \
  --server-side-encryption AES256

# Backup voice recordings
aws s3 sync s3://seiketsu-voice-recordings s3://seiketsu-backups/voice-content/ \
  --delete \
  --server-side-encryption AES256

# Generate inventory report
aws s3api put-bucket-inventory-configuration \
  --bucket seiketsu-backups \
  --id user-content-inventory \
  --inventory-configuration file://inventory-config.json
```

---

## Recovery Procedures

### Database Recovery

#### Complete Database Restore
```bash
# scripts/restore-database.sh
#!/bin/bash

RESTORE_DATE=$1
BACKUP_FILE="seiketsu_backup_${RESTORE_DATE}.sql.gz"

if [ -z "$RESTORE_DATE" ]; then
  echo "Usage: $0 <RESTORE_DATE> (format: YYYYMMDD_HHMMSS)"
  exit 1
fi

# Download backup from S3
aws s3 cp "s3://seiketsu-backups/database/daily/${BACKUP_FILE}" "/tmp/"

# Decompress backup
gunzip "/tmp/${BACKUP_FILE}"

# Stop application services to prevent connections
kubectl scale deployment seiketsu-api --replicas=0
kubectl scale deployment seiketsu-web --replicas=0

# Create new database instance (if needed)
aws rds create-db-instance \
  --db-instance-identifier seiketsu-restore-$(date +%s) \
  --db-instance-class db.r6g.xlarge \
  --engine postgres \
  --master-username seiketsu \
  --master-user-password $DB_PASSWORD \
  --allocated-storage 100

# Wait for instance to be available
aws rds wait db-instance-available --db-instance-identifier seiketsu-restore-*

# Restore database
psql $RESTORE_DATABASE_URL < "/tmp/seiketsu_backup_${RESTORE_DATE}.sql"

# Update application configuration
kubectl patch secret db-credentials -p "{\"data\":{\"url\":\"$(echo $RESTORE_DATABASE_URL | base64)\"}}"

# Restart application services
kubectl scale deployment seiketsu-api --replicas=3
kubectl scale deployment seiketsu-web --replicas=2

# Verify restoration
psql $RESTORE_DATABASE_URL -c "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM properties;"

echo "Database restoration completed for date: $RESTORE_DATE"
```

#### Point-in-Time Recovery
```bash
# scripts/point-in-time-recovery.sh
#!/bin/bash

RECOVERY_TIME=$1  # Format: 2025-08-09T14:30:00Z

# Create new instance from point-in-time
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier seiketsu-prod \
  --target-db-instance-identifier seiketsu-pitr-$(date +%s) \
  --restore-time $RECOVERY_TIME \
  --db-instance-class db.r6g.xlarge

# Wait for instance to be ready
aws rds wait db-instance-available --db-instance-identifier seiketsu-pitr-*

# Get new instance endpoint
NEW_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier seiketsu-pitr-* \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

# Update application configuration
kubectl patch secret db-credentials -p "{\"data\":{\"host\":\"$(echo $NEW_ENDPOINT | base64)\"}}"

# Restart applications
kubectl rollout restart deployment/seiketsu-api
kubectl rollout restart deployment/seiketsu-web

echo "Point-in-time recovery completed to: $RECOVERY_TIME"
```

### Application Recovery

#### Infrastructure Recovery (Terraform)
```bash
# scripts/recover-infrastructure.sh
#!/bin/bash

# Clone infrastructure repository
git clone https://github.com/seiketsu/seiketsu-infrastructure.git /tmp/seiketsu-infra
cd /tmp/seiketsu-infra

# Initialize Terraform with backup state
terraform init -backend-config="bucket=seiketsu-terraform-state"

# Import existing resources (if any survived)
terraform import aws_vpc.main vpc-12345678
terraform import aws_security_group.api sg-87654321

# Plan recovery
terraform plan -var-file=environments/prod.tfvars -out=recovery.plan

# Apply infrastructure recovery
terraform apply recovery.plan

# Verify infrastructure
terraform output

echo "Infrastructure recovery completed"
```

#### Application Deployment Recovery
```bash
# scripts/recover-applications.sh
#!/bin/bash

# Verify infrastructure is ready
kubectl cluster-info
kubectl get nodes

# Deploy applications from latest known good configuration
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress.yaml

# Wait for deployments to be ready
kubectl rollout status deployment/seiketsu-api
kubectl rollout status deployment/seiketsu-web

# Run health checks
kubectl exec deployment/seiketsu-api -- curl localhost:8000/health
kubectl exec deployment/seiketsu-web -- curl localhost:3000/api/health

# Update DNS records if needed
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://dns-recovery.json

echo "Application recovery completed"
```

### Multi-Region Failover

#### Cross-Region Recovery Procedure
```bash
# scripts/cross-region-failover.sh
#!/bin/bash

PRIMARY_REGION="us-east-1"
DR_REGION="us-west-2"
FAILOVER_TIME=$(date -u +%Y%m%d_%H%M%S)

echo "Initiating cross-region failover to $DR_REGION at $FAILOVER_TIME"

# 1. Promote read replica to primary
aws rds promote-read-replica \
  --db-instance-identifier seiketsu-replica-west \
  --region $DR_REGION

# 2. Update DNS to point to DR region
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.seiketsu.ai",
        "Type": "CNAME",
        "TTL": 60,
        "ResourceRecords": [{"Value": "api-dr.seiketsu.ai"}]
      }
    }]
  }'

# 3. Deploy applications to DR region
kubectl config use-context dr-cluster
kubectl apply -f k8s/dr-deployment/

# 4. Update CDN configuration
aws cloudfront update-distribution \
  --id E123456789 \
  --distribution-config file://cdn-dr-config.json

# 5. Notify stakeholders
curl -X POST $SLACK_WEBHOOK \
  -H 'Content-type: application/json' \
  --data "{\"text\":\"🚨 DR Activation: Failover to $DR_REGION completed at $FAILOVER_TIME\"}"

echo "Cross-region failover completed"
```

### Service-Specific Recovery

#### Voice Service Recovery
```bash
# scripts/recover-voice-service.sh
#!/bin/bash

# Check ElevenLabs API status
ELEVENLABS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  https://api.elevenlabs.io/v1/user)

if [ "$ELEVENLABS_STATUS" != "200" ]; then
  echo "ElevenLabs API unavailable, activating fallback TTS service"
  
  # Enable fallback service
  kubectl patch configmap voice-config -p '{"data":{"fallback_enabled":"true"}}'
  
  # Scale up fallback service
  kubectl scale deployment fallback-tts --replicas=3
else
  echo "ElevenLabs API available, ensuring voice service is running"
  
  # Scale up voice service
  kubectl scale deployment voice-service --replicas=3
fi

# Verify voice service health
kubectl wait --for=condition=ready pod -l app=voice-service --timeout=300s
kubectl exec deployment/voice-service -- curl localhost:8080/health

echo "Voice service recovery completed"
```

#### Real Estate Data Recovery
```bash
# scripts/recover-real-estate-data.sh
#!/bin/bash

# Check data freshness
LAST_UPDATE=$(psql $DATABASE_URL -t -c "SELECT MAX(updated_at) FROM properties;")
CURRENT_TIME=$(date -u +%Y-%m-%d\ %H:%M:%S)

echo "Last data update: $LAST_UPDATE"
echo "Current time: $CURRENT_TIME"

# If data is more than 4 hours old, trigger fresh import
if [[ $(date -d "$LAST_UPDATE" +%s) -lt $(date -d "4 hours ago" +%s) ]]; then
  echo "Data is stale, triggering fresh import"
  
  # Trigger data import job
  kubectl create job property-import-$(date +%s) --from=cronjob/property-import
  
  # Wait for job completion
  kubectl wait --for=condition=complete job/property-import-* --timeout=1800s
else
  echo "Data is fresh, no import needed"
fi

# Verify data availability
PROPERTY_COUNT=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM properties WHERE status = 'active';")
echo "Active properties available: $PROPERTY_COUNT"

if [ "$PROPERTY_COUNT" -lt 1000 ]; then
  echo "Warning: Low property count detected, check data import"
fi

echo "Real estate data recovery completed"
```

---

## Testing Schedules

### Disaster Recovery Testing Calendar

#### Monthly Tests (First Saturday)
```yaml
Database Recovery Test:
  Frequency: Monthly
  Duration: 2 hours
  Scope: Restore from previous day backup
  Success Criteria: Complete restore within RTO
  
Application Recovery Test:
  Frequency: Monthly  
  Duration: 1 hour
  Scope: Deploy to staging from backup
  Success Criteria: All services healthy
  
Backup Integrity Test:
  Frequency: Monthly
  Duration: 30 minutes
  Scope: Verify all backup files
  Success Criteria: No corrupt backups
```

#### Quarterly Tests (First Saturday of Quarter)
```yaml
Full DR Simulation:
  Frequency: Quarterly
  Duration: 8 hours
  Scope: Complete cross-region failover
  Success Criteria: Meet all RTO/RPO targets
  
Network Isolation Test:
  Frequency: Quarterly
  Duration: 4 hours
  Scope: Simulate network partition
  Success Criteria: Graceful degradation
  
Security Incident Recovery:
  Frequency: Quarterly
  Duration: 6 hours
  Scope: Simulate security breach
  Success Criteria: Complete containment and recovery
```

#### Annual Tests (Scheduled Maintenance Window)
```yaml
Complete Infrastructure Recreation:
  Frequency: Annually
  Duration: 24 hours
  Scope: Rebuild from scratch
  Success Criteria: Full service restoration
  
Multi-Failure Simulation:
  Frequency: Annually
  Duration: 12 hours
  Scope: Multiple simultaneous failures
  Success Criteria: Service continuity maintained
  
Compliance Audit Simulation:
  Frequency: Annually
  Duration: 8 hours
  Scope: Regulatory compliance verification
  Success Criteria: All audit requirements met
```

### Test Execution Procedures

#### Pre-Test Checklist
```bash
# Pre-test validation script
#!/bin/bash
# scripts/pre-dr-test-checklist.sh

echo "=== Disaster Recovery Test Pre-Checklist ==="

# 1. Verify backup integrity
echo "Checking backup integrity..."
aws s3 ls s3://seiketsu-backups/database/daily/ | tail -7

# 2. Check system health
echo "Verifying system health..."
kubectl get pods --all-namespaces | grep -v Running

# 3. Notify stakeholders
echo "Notifying stakeholders..."
curl -X POST $SLACK_WEBHOOK \
  -d "{\"text\":\"🧪 DR Test Starting: $(date)\"}"

# 4. Create test tracking issue
gh issue create \
  --title "DR Test - $(date +%Y-%m-%d)" \
  --body "Disaster recovery test execution tracking"

# 5. Verify monitoring is active
curl -s http://prometheus:9090/api/v1/targets | jq '.data.activeTargets | length'

echo "Pre-test checklist completed"
```

#### Post-Test Validation
```bash
# Post-test validation script
#!/bin/bash
# scripts/post-dr-test-validation.sh

echo "=== Disaster Recovery Test Post-Validation ==="

TEST_RESULTS_FILE="/tmp/dr-test-results-$(date +%Y%m%d).log"

# 1. Verify all services are operational
echo "Testing service endpoints..." | tee -a $TEST_RESULTS_FILE
curl -s https://seiketsu.ai/health >> $TEST_RESULTS_FILE
curl -s https://api.seiketsu.ai/health >> $TEST_RESULTS_FILE

# 2. Validate data integrity
echo "Checking data integrity..." | tee -a $TEST_RESULTS_FILE
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;" >> $TEST_RESULTS_FILE
psql $DATABASE_URL -c "SELECT COUNT(*) FROM properties;" >> $TEST_RESULTS_FILE

# 3. Performance baseline comparison
echo "Running performance tests..." | tee -a $TEST_RESULTS_FILE
k6 run --quiet performance-tests/baseline-test.js >> $TEST_RESULTS_FILE

# 4. Generate test report
cat > /tmp/dr-test-report.md << EOF
# Disaster Recovery Test Report

**Date**: $(date)
**Test Type**: $1
**Duration**: $2 hours
**Status**: $3

## Results Summary
$(cat $TEST_RESULTS_FILE)

## Action Items
- [ ] Review any performance degradation
- [ ] Update runbooks based on lessons learned
- [ ] Schedule next test

EOF

# 5. Upload test report
aws s3 cp /tmp/dr-test-report.md s3://seiketsu-backups/test-reports/

echo "Post-test validation completed"
```

---

## Contact Information

### Disaster Recovery Team

#### Primary DR Coordinator
```yaml
Name: [DR_COORDINATOR_NAME]
Role: Disaster Recovery Lead
Phone: +1-XXX-XXX-XXXX
Email: dr-coordinator@seiketsu.ai
Backup: [BACKUP_DR_COORDINATOR]
```

#### Technical Recovery Team
```yaml
Infrastructure Lead:
  Name: [INFRA_LEAD_NAME]
  Phone: +1-XXX-XXX-XXXX
  Email: infra-lead@seiketsu.ai
  
Database Administrator:
  Name: [DBA_NAME] 
  Phone: +1-XXX-XXX-XXXX
  Email: dba@seiketsu.ai
  
Application Lead:
  Name: [APP_LEAD_NAME]
  Phone: +1-XXX-XXX-XXXX
  Email: app-lead@seiketsu.ai

Security Lead:
  Name: [SEC_LEAD_NAME]
  Phone: +1-XXX-XXX-XXXX
  Email: security@seiketsu.ai
```

#### Executive Team
```yaml
VP Engineering:
  Name: [VP_NAME]
  Phone: +1-XXX-XXX-XXXX
  Email: vp-eng@seiketsu.ai
  Escalation: P0 incidents > 2 hours

CTO:
  Name: [CTO_NAME]
  Phone: +1-XXX-XXX-XXXX
  Email: cto@seiketsu.ai
  Escalation: P0 incidents > 4 hours

CEO:
  Name: [CEO_NAME]
  Phone: +1-XXX-XXX-XXXX
  Email: ceo@seiketsu.ai
  Escalation: P0 incidents > 8 hours
```

### External Vendor Support

#### Cloud Provider Support
```yaml
AWS Enterprise Support:
  Phone: +1-206-266-4064
  Case Portal: https://console.aws.amazon.com/support/
  TAM: [TAM_NAME] - [TAM_EMAIL]
  Emergency Escalation: Available 24/7

Vercel Support:
  Email: support@vercel.com
  Portal: https://vercel.com/help
  Account Manager: [AM_NAME]
```

#### Third-Party Services
```yaml
Supabase:
  Support: support@supabase.io
  Status: https://status.supabase.com
  Emergency: Enterprise support portal

ElevenLabs:
  Support: support@elevenlabs.io
  API Status: https://status.elevenlabs.io
  Account Manager: [AM_NAME]

Monitoring (DataDog):
  Support: support@datadoghq.com
  Phone: +1-866-329-4466
  Status: https://status.datadoghq.com
```

### Communication Channels

#### Primary Channels
```yaml
Emergency War Room:
  Slack: #dr-emergency-room
  Zoom: https://zoom.us/j/emergency-room
  Bridge: +1-XXX-XXX-XXXX, PIN: XXXX

Status Updates:
  Internal: #dr-status-updates
  Customer: status@seiketsu.ai
  Status Page: https://status.seiketsu.ai

Documentation:
  Incident Tracking: GitHub Issues
  Recovery Logs: S3 Bucket (seiketsu-dr-logs)
  Runbook Updates: GitHub DR repository
```

#### Escalation Communication Tree
```
DR Coordinator
    ↓
VP Engineering ← → CTO
    ↓              ↓
Team Leads     CEO (if needed)
    ↓
Team Members
```

---

## Recovery Validation Checklists

### Post-Recovery System Validation

#### Core System Health Check
```bash
# scripts/system-health-check.sh
#!/bin/bash

echo "=== System Health Validation ==="

# Application Health
echo "1. Checking application health..."
curl -f https://seiketsu.ai/health || echo "❌ Frontend health check failed"
curl -f https://api.seiketsu.ai/health || echo "❌ API health check failed"

# Database Connectivity
echo "2. Checking database connectivity..."
psql $DATABASE_URL -c "SELECT 1;" > /dev/null && echo "✅ Database connected" || echo "❌ Database connection failed"

# Cache Layer
echo "3. Checking cache layer..."
redis-cli ping | grep -q PONG && echo "✅ Redis connected" || echo "❌ Redis connection failed"

# External Services
echo "4. Checking external services..."
curl -f -H "xi-api-key: $ELEVENLABS_API_KEY" https://api.elevenlabs.io/v1/user > /dev/null && echo "✅ ElevenLabs API accessible" || echo "❌ ElevenLabs API failed"

# Performance Baseline
echo "5. Running performance baseline..."
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' https://api.seiketsu.ai/properties/search?limit=10)
if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
  echo "✅ API response time acceptable: ${RESPONSE_TIME}s"
else
  echo "⚠️ API response time high: ${RESPONSE_TIME}s"
fi
```

#### Data Integrity Validation
```bash
# scripts/data-integrity-check.sh
#!/bin/bash

echo "=== Data Integrity Validation ==="

# User data validation
USER_COUNT=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM users;")
echo "Users in database: $USER_COUNT"
if [ "$USER_COUNT" -lt 1 ]; then
  echo "❌ No users found in database"
else
  echo "✅ User data present"
fi

# Property data validation
PROPERTY_COUNT=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM properties WHERE status = 'active';")
echo "Active properties: $PROPERTY_COUNT"
if [ "$PROPERTY_COUNT" -lt 100 ]; then
  echo "⚠️ Low property count detected"
else
  echo "✅ Property data adequate"
fi

# Recent data validation
RECENT_UPDATES=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM properties WHERE updated_at > NOW() - INTERVAL '24 hours';")
echo "Recent property updates: $RECENT_UPDATES"

# Data consistency checks
ORPHANED_RECORDS=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM user_properties up LEFT JOIN users u ON up.user_id = u.id WHERE u.id IS NULL;")
if [ "$ORPHANED_RECORDS" -gt 0 ]; then
  echo "⚠️ Found $ORPHANED_RECORDS orphaned records"
else
  echo "✅ No orphaned records detected"
fi
```

#### Security Validation
```bash
# scripts/security-validation.sh  
#!/bin/bash

echo "=== Security Validation ==="

# SSL certificate validation
echo "1. Checking SSL certificates..."
openssl s_client -connect seiketsu.ai:443 -servername seiketsu.ai < /dev/null 2>/dev/null | openssl x509 -noout -dates
openssl s_client -connect api.seiketsu.ai:443 -servername api.seiketsu.ai < /dev/null 2>/dev/null | openssl x509 -noout -dates

# Authentication system validation
echo "2. Testing authentication system..."
AUTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://api.seiketsu.ai/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid","password":"invalid"}')

if [ "$AUTH_RESPONSE" = "401" ]; then
  echo "✅ Authentication system rejecting invalid credentials"
else
  echo "⚠️ Unexpected authentication response: $AUTH_RESPONSE"
fi

# API security headers validation
echo "3. Checking security headers..."
curl -s -I https://api.seiketsu.ai/health | grep -i "x-content-type-options\|x-frame-options\|strict-transport-security" || echo "⚠️ Missing security headers"

# Rate limiting validation
echo "4. Testing rate limiting..."
for i in {1..5}; do
  curl -s -o /dev/null -w "%{http_code} " https://api.seiketsu.ai/health
done
echo ""
```

### Business Continuity Validation

#### Customer Impact Assessment
```bash
# scripts/customer-impact-assessment.sh
#!/bin/bash

echo "=== Customer Impact Assessment ==="

# Active user sessions
ACTIVE_SESSIONS=$(redis-cli keys "session:*" | wc -l)
echo "Active user sessions: $ACTIVE_SESSIONS"

# Recent user activity
RECENT_ACTIVITY=$(psql $DATABASE_URL -t -c "SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE created_at > NOW() - INTERVAL '1 hour';")
echo "Users active in last hour: $RECENT_ACTIVITY"

# Voice service usage
VOICE_REQUESTS=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM voice_requests WHERE created_at > NOW() - INTERVAL '1 hour';")
echo "Voice requests in last hour: $VOICE_REQUESTS"

# Property searches
PROPERTY_SEARCHES=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM search_logs WHERE created_at > NOW() - INTERVAL '1 hour';")
echo "Property searches in last hour: $PROPERTY_SEARCHES"

# Error rates during recovery
ERROR_COUNT=$(grep -c "ERROR" /var/log/seiketsu/app.log | tail -100)
echo "Recent error count: $ERROR_COUNT"
```

---

## Lessons Learned and Improvements

### Recovery Testing Results Database

#### Test Results Tracking
```sql
-- DR test results tracking table
CREATE TABLE dr_test_results (
    id SERIAL PRIMARY KEY,
    test_date TIMESTAMP NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    duration_hours DECIMAL(4,2),
    rto_met BOOLEAN NOT NULL,
    rpo_met BOOLEAN NOT NULL,
    issues_found TEXT[],
    improvements_identified TEXT[],
    action_items JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Example test result entry
INSERT INTO dr_test_results (
    test_date,
    test_type,
    duration_hours,
    rto_met,
    rpo_met,
    issues_found,
    improvements_identified,
    action_items
) VALUES (
    '2025-08-09 10:00:00',
    'Database Recovery',
    1.5,
    true,
    true,
    ARRAY['Slow DNS propagation', 'Missing monitoring alert'],
    ARRAY['Automate DNS updates', 'Add DR-specific alerts'],
    '{"assigned_to": "devops-team", "due_date": "2025-08-23"}'
);
```

#### Continuous Improvement Process
```yaml
Monthly Review Process:
  1. Analyze test results and real incidents
  2. Identify patterns and recurring issues  
  3. Update procedures and automation
  4. Schedule training sessions
  5. Review and update contact information

Quarterly Assessment:
  1. Review RTO/RPO targets vs actual performance
  2. Assess cost effectiveness of DR solutions
  3. Evaluate new technologies and approaches
  4. Update risk assessments
  5. Conduct stakeholder feedback sessions

Annual Strategy Review:
  1. Complete DR capability assessment
  2. Business continuity planning review
  3. Regulatory compliance verification
  4. Budget planning for next year
  5. DR team training and certification
```

---

## Automation Scripts

### Automated Recovery Orchestration
```bash
# scripts/automated-dr-orchestration.sh
#!/bin/bash

DR_TYPE=$1  # "database", "application", "full"
RECOVERY_LEVEL=$2  # "test", "partial", "full"

case $DR_TYPE in
  "database")
    echo "Initiating database recovery..."
    ./scripts/restore-database.sh
    ;;
  "application")
    echo "Initiating application recovery..."
    ./scripts/recover-applications.sh
    ;;
  "full")
    echo "Initiating full disaster recovery..."
    ./scripts/recover-infrastructure.sh
    ./scripts/restore-database.sh
    ./scripts/recover-applications.sh
    ;;
  *)
    echo "Invalid DR type. Use: database, application, or full"
    exit 1
    ;;
esac

# Run validation
./scripts/system-health-check.sh
./scripts/data-integrity-check.sh

echo "Disaster recovery completed for type: $DR_TYPE"
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-08-09 | Initial disaster recovery runbook | Seiketsu Team |

---

*Last Updated: 2025-08-09*
*Next Review: 2025-11-09*
*Next DR Test: 2025-09-07*