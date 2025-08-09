# Incident Response Runbook - Seiketsu AI Platform

## Overview
This runbook provides procedures for responding to incidents affecting the Seiketsu AI enterprise real estate voice agent platform.

---

## Severity Level Definitions

### P0 - Critical (Response Time: 15 minutes)
**Impact**: Complete service outage or critical security breach
- Platform completely inaccessible
- Data breach or security compromise
- Financial transactions failing
- Multiple critical systems down

**Examples**:
- Website returning 500 errors for all users
- Database completely inaccessible
- Payment system compromised
- Voice services completely failing

### P1 - High (Response Time: 1 hour)
**Impact**: Major functionality impaired, significant user impact
- Core features unavailable
- Performance severely degraded
- Partial service outage
- Single critical system failing

**Examples**:
- Voice interface not working
- Authentication system failing
- Dashboard not loading data
- API returning errors for key endpoints

### P2 - Medium (Response Time: 4 hours)
**Impact**: Minor functionality impaired, limited user impact
- Non-critical features unavailable
- Performance degraded but usable
- Isolated component failures
- Cosmetic issues affecting UX

**Examples**:
- Analytics dashboard slow
- Non-critical API endpoints failing
- UI rendering issues
- Email notifications delayed

### P3 - Low (Response Time: 24 hours)
**Impact**: Minimal user impact, minor issues
- Documentation issues
- Minor UI inconsistencies
- Performance optimization opportunities
- Non-urgent feature requests

---

## Escalation Procedures

### Incident Response Team Structure

#### Incident Commander (IC)
- **Primary**: DevOps Lead
- **Secondary**: Senior Backend Engineer
- **Responsibilities**: Overall incident coordination, communications, decisions

#### Technical Lead
- **Primary**: Platform Architect
- **Secondary**: Senior Full-Stack Engineer
- **Responsibilities**: Technical investigation, solution implementation

#### Communications Lead
- **Primary**: Product Manager
- **Secondary**: Engineering Manager
- **Responsibilities**: Internal/external communications, stakeholder updates

### Escalation Matrix

```
P0 Incident Detected
    ↓
Incident Commander (Immediate)
    ↓
Technical Lead (5 minutes)
    ↓
Engineering Manager (15 minutes)
    ↓
VP Engineering (30 minutes)
    ↓
CTO (1 hour if unresolved)
```

### On-Call Rotation
| Week | Primary IC | Technical Lead | Communications |
|------|------------|----------------|----------------|
| W1 | [Name] | [Name] | [Name] |
| W2 | [Name] | [Name] | [Name] |
| W3 | [Name] | [Name] | [Name] |
| W4 | [Name] | [Name] | [Name] |

---

## Incident Response Process

### 1. Detection and Alerting

#### Automated Detection
```bash
# Monitor key metrics
- Application errors > 1%
- Response time > 2s (95th percentile)
- Availability < 99.5%
- CPU usage > 80%
- Memory usage > 85%
- Database connections > 80%
```

#### Manual Detection
- Customer reports
- Internal team notifications
- Third-party service alerts
- Security team notifications

### 2. Initial Response (First 15 minutes)

#### Immediate Actions
1. **Acknowledge Alert**
   ```bash
   # Acknowledge in monitoring system
   curl -X POST "$PAGERDUTY_API/incidents/$INCIDENT_ID/acknowledge"
   ```

2. **Join Incident Channel**
   ```
   Slack: #incident-response
   Zoom: Emergency Response Room
   ```

3. **Initial Assessment**
   - Confirm incident severity
   - Identify affected services
   - Determine user impact
   - Check system status dashboard

4. **Assign Roles**
   - Incident Commander
   - Technical Lead
   - Communications Lead

### 3. Investigation Phase

#### Immediate Checks
```bash
# System Health
curl https://api.seiketsu.ai/health
curl https://seiketsu.ai/health

# Database Connectivity
psql $DATABASE_URL -c "SELECT 1"

# Key Services Status
docker ps | grep seiketsu
kubectl get pods -n seiketsu-prod

# Recent Deployments
git log --oneline -10
kubectl rollout history deployment/seiketsu-api

# Error Logs
tail -f /var/log/seiketsu/application.log
kubectl logs -f deployment/seiketsu-api --tail=100
```

#### Investigation Checklist
- [ ] Check recent deployments/changes
- [ ] Review error logs and metrics
- [ ] Verify external service dependencies
- [ ] Check infrastructure status
- [ ] Analyze user impact and scope
- [ ] Identify potential root causes

### 4. Containment and Mitigation

#### Immediate Mitigation Options
```bash
# Quick rollback
./scripts/emergency-rollback.sh

# Scale up resources
kubectl scale deployment seiketsu-api --replicas=10

# Enable maintenance mode
./scripts/maintenance-mode.sh enable

# Circuit breaker activation
curl -X POST "$API_BASE/admin/circuit-breaker/enable"

# Traffic rerouting
aws elbv2 modify-rule --rule-arn $RULE_ARN --actions Type=fixed-response,FixedResponseConfig='{StatusCode=503}'
```

#### Containment Strategies by Incident Type

**Application Errors**
1. Identify error patterns
2. Implement circuit breakers
3. Scale affected services
4. Consider feature flag toggles

**Database Issues**
1. Check connection pools
2. Identify slow/blocking queries
3. Consider read replica routing
4. Implement query timeout

**Infrastructure Problems**
1. Check AWS service status
2. Verify auto-scaling policies
3. Examine load balancer health
4. Consider multi-AZ failover

**Security Incidents**
1. Isolate affected systems
2. Preserve logs and evidence
3. Change compromised credentials
4. Implement access restrictions

---

## Common Issues and Resolutions

### High Error Rate (5xx Errors)

#### Investigation Steps
```bash
# Check application logs
grep "ERROR\|500\|502\|503\|504" /var/log/seiketsu/app.log | tail -50

# Check database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check memory usage
free -h
docker stats seiketsu-api

# Check disk space
df -h
```

#### Common Causes & Solutions
1. **Database Connection Pool Exhausted**
   ```python
   # Increase pool size
   DATABASE_POOL_SIZE = 50
   DATABASE_MAX_OVERFLOW = 20
   ```

2. **Memory Leaks**
   ```bash
   # Restart application containers
   docker-compose restart api
   kubectl rollout restart deployment/seiketsu-api
   ```

3. **Third-party Service Outage**
   ```python
   # Implement fallback/mock responses
   if not elevenlabs_available():
       return mock_voice_response()
   ```

### High Response Times

#### Investigation Steps
```bash
# Check API performance
curl -w "@curl-format.txt" -s -o /dev/null https://api.seiketsu.ai/properties

# Database query analysis
psql $DATABASE_URL -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Resource utilization
top -p $(pgrep -f seiketsu)
```

#### Common Solutions
1. **Optimize Database Queries**
   ```sql
   -- Add missing indexes
   CREATE INDEX CONCURRENTLY idx_properties_location ON properties(latitude, longitude);
   
   -- Analyze slow queries
   EXPLAIN ANALYZE SELECT * FROM properties WHERE location = 'Downtown';
   ```

2. **Implement Caching**
   ```python
   # Redis caching
   @cache.memoize(timeout=300)
   def get_property_data(property_id):
       return db.query_property(property_id)
   ```

3. **Scale Resources**
   ```bash
   # Horizontal scaling
   kubectl scale deployment seiketsu-api --replicas=5
   
   # Vertical scaling
   kubectl patch deployment seiketsu-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"requests":{"cpu":"500m","memory":"1Gi"}}}]}}}}'
   ```

### Voice Service Failures

#### Investigation Steps
```bash
# Check ElevenLabs API status
curl -H "xi-api-key: $ELEVENLABS_API_KEY" https://api.elevenlabs.io/v1/user

# Check voice processing logs
grep -i "voice\|elevenlabs\|tts" /var/log/seiketsu/app.log | tail -20

# Test voice endpoints
curl -X POST "$API_BASE/voice/synthesize" -d '{"text":"test"}'
```

#### Common Solutions
1. **API Rate Limiting**
   ```python
   # Implement exponential backoff
   @retry(wait=wait_exponential(multiplier=1, min=4, max=10))
   def call_elevenlabs_api(text):
       return elevenlabs.generate_voice(text)
   ```

2. **Fallback Voice Service**
   ```python
   def synthesize_voice(text):
       try:
           return elevenlabs.generate(text)
       except Exception:
           return backup_tts_service.generate(text)
   ```

### Authentication Issues

#### Investigation Steps
```bash
# Check JWT token validation
curl -H "Authorization: Bearer $JWT_TOKEN" "$API_BASE/auth/validate"

# Check user session data
redis-cli GET "session:$USER_ID"

# Review authentication logs
grep -i "auth\|jwt\|login" /var/log/seiketsu/app.log | tail -20
```

#### Common Solutions
1. **Token Expiration Issues**
   ```python
   # Extend token validity
   JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
   ```

2. **Session Store Problems**
   ```bash
   # Clear Redis cache
   redis-cli FLUSHDB
   ```

---

## Recovery Procedures

### Database Recovery

#### Point-in-Time Recovery
```bash
# Restore from backup
aws rds restore-db-instance-to-point-in-time \
    --source-db-instance-identifier seiketsu-prod \
    --target-db-instance-identifier seiketsu-recovery \
    --restore-time 2025-08-09T10:00:00Z

# Switch connection strings
kubectl patch secret db-credentials -p '{"data":{"url":"<new-db-url>"}}'
```

#### Database Failover
```bash
# Promote read replica
aws rds promote-read-replica --db-instance-identifier seiketsu-replica

# Update DNS records
aws route53 change-resource-record-sets --hosted-zone-id Z123 --change-batch file://dns-change.json
```

### Application Recovery

#### Full Service Restart
```bash
# Kubernetes deployment
kubectl rollout restart deployment/seiketsu-api
kubectl rollout restart deployment/seiketsu-web

# Docker Compose
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

#### Partial Service Recovery
```bash
# Restart specific services
kubectl delete pod -l app=voice-service
kubectl delete pod -l app=real-estate-api
```

### Infrastructure Recovery

#### Multi-AZ Failover
```bash
# Check current AZ status
aws ec2 describe-availability-zones --filters Name=state,Values=available

# Trigger auto-scaling in different AZ
aws autoscaling set-desired-capacity --auto-scaling-group-name seiketsu-asg --desired-capacity 6

# Update load balancer targets
aws elbv2 register-targets --target-group-arn $TG_ARN --targets Id=i-newinstance
```

---

## Post-Incident Review Process

### Immediate Post-Incident (Within 1 hour)

#### Incident Closure Checklist
- [ ] Service fully restored and stable
- [ ] Monitoring showing normal metrics
- [ ] Customer impact resolved
- [ ] Stakeholders notified of resolution
- [ ] Incident timeline documented

#### Initial Documentation
```markdown
## Incident Summary
- **Start Time**: [UTC timestamp]
- **End Time**: [UTC timestamp]
- **Duration**: [time]
- **Severity**: P[0-3]
- **Root Cause**: [brief description]
- **Resolution**: [brief description]
- **Customer Impact**: [description]
```

### Post-Incident Review Meeting (Within 48 hours)

#### Meeting Agenda
1. Incident timeline review
2. Root cause analysis
3. Response effectiveness
4. Customer impact assessment
5. Action items identification

#### Action Items Template
| Item | Owner | Due Date | Status |
|------|-------|----------|--------|
| Implement additional monitoring | DevOps | 2025-08-15 | Open |
| Update runbook with new procedure | SRE | 2025-08-12 | Open |
| Add automated failover | Platform | 2025-08-20 | Open |

### Incident Report (Within 1 week)

#### Report Structure
1. **Executive Summary**
2. **Incident Details**
3. **Timeline of Events**
4. **Root Cause Analysis**
5. **Impact Assessment**
6. **Response Analysis**
7. **Lessons Learned**
8. **Action Items**

---

## Communication Templates

### Initial Incident Notification
```
🚨 INCIDENT ALERT - P[SEVERITY]

Platform: Seiketsu AI
Severity: P[0-3] ([SEVERITY_LEVEL])
Start Time: [UTC_TIME]
Status: Investigating

Impact: [USER_IMPACT_DESCRIPTION]
Services Affected: [SERVICE_LIST]

Incident Commander: [NAME]
Status Updates: Every 15 minutes
Next Update: [TIME]

Investigation in progress...
```

### Status Updates
```
📢 INCIDENT UPDATE - P[SEVERITY] - [TIMESTAMP]

Current Status: [INVESTIGATING/MITIGATING/RESOLVED]
Progress: [PROGRESS_DESCRIPTION]
ETA: [ESTIMATED_RESOLUTION_TIME]

Actions Taken:
- [ACTION_1]
- [ACTION_2]

Next Update: [TIME]
```

### Resolution Notification
```
✅ INCIDENT RESOLVED - P[SEVERITY]

The incident affecting Seiketsu AI has been resolved.

Resolution Time: [UTC_TIME]
Total Duration: [DURATION]
Root Cause: [BRIEF_DESCRIPTION]

All services are now operating normally.
Post-incident review scheduled for [DATE].

Thank you for your patience.
```

### Customer Communication
```
Subject: Service Restoration - Seiketsu AI Platform

Dear Seiketsu AI Users,

We have resolved the service issue that affected our platform between [START_TIME] and [END_TIME] UTC.

What happened: [BRIEF_CUSTOMER_FRIENDLY_DESCRIPTION]
What we did: [BRIEF_RESOLUTION_DESCRIPTION]
What we're doing to prevent this: [PREVENTION_MEASURES]

We sincerely apologize for any inconvenience this may have caused.

If you continue to experience issues, please contact our support team.

Best regards,
Seiketsu AI Team
```

---

## Tools and Resources

### Monitoring Dashboards
- **Primary Dashboard**: https://grafana.seiketsu.ai/dashboard/main
- **Infrastructure**: https://datadog.com/dashboard/seiketsu-infra
- **Application Performance**: https://newrelic.com/seiketsu-apm
- **User Analytics**: https://amplitude.com/seiketsu

### Communication Channels
- **Slack**: #incident-response, #engineering-alerts
- **Email**: incidents@seiketsu.ai
- **Phone**: Emergency hotline (+1-XXX-XXX-XXXX)
- **Status Page**: https://status.seiketsu.ai

### External Services Status
- **AWS**: https://status.aws.amazon.com
- **Supabase**: https://status.supabase.com
- **ElevenLabs**: https://status.elevenlabs.io
- **Vercel**: https://www.vercel-status.com

---

## Emergency Contacts

### Internal Team
- **On-Call Engineer**: [PHONE] / [EMAIL]
- **DevOps Lead**: [PHONE] / [EMAIL]
- **Engineering Manager**: [PHONE] / [EMAIL]
- **CTO**: [PHONE] / [EMAIL]

### External Vendors
- **AWS Enterprise Support**: [CASE_PORTAL]
- **Supabase Support**: support@supabase.io
- **ElevenLabs Support**: support@elevenlabs.io

### Executive Team
- **CEO**: [PHONE] / [EMAIL] (P0 incidents only)
- **VP Engineering**: [PHONE] / [EMAIL] (P0/P1 incidents)

---

## Metrics and KPIs

### Incident Response Metrics
- **Mean Time to Detection (MTTD)**: < 5 minutes
- **Mean Time to Response (MTTR)**: < 15 minutes (P0), < 60 minutes (P1)
- **Mean Time to Resolution (MTTR)**: < 4 hours
- **Incident Volume**: < 10 P0-P2 incidents per month

### Service Level Objectives
- **Availability**: 99.9% uptime
- **Performance**: < 2s response time (95th percentile)
- **Error Rate**: < 0.1%

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-08-09 | Initial incident response runbook | Seiketsu Team |

---

*Last Updated: 2025-08-09*
*Next Review: 2025-09-09*