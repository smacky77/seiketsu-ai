# Monitoring & Alerting Guide - Seiketsu AI Platform

## Overview
This guide provides comprehensive monitoring and alerting procedures for the Seiketsu AI enterprise real estate voice agent platform.

---

## Key Metrics to Monitor

### Application Performance Metrics

#### Frontend (Next.js Web Application)
```yaml
Core Web Vitals:
  - First Contentful Paint (FCP): < 1.8s
  - Largest Contentful Paint (LCP): < 2.5s
  - Cumulative Layout Shift (CLS): < 0.1
  - First Input Delay (FID): < 100ms
  - Time to Interactive (TTI): < 3.8s

User Experience:
  - Page Load Time: < 2s (95th percentile)
  - JavaScript Error Rate: < 0.1%
  - Session Duration: > 5 minutes (target)
  - Bounce Rate: < 40%
  - User Actions per Session: > 10
```

#### Backend API (FastAPI)
```yaml
Response Time:
  - P50: < 200ms
  - P95: < 500ms
  - P99: < 1s

Throughput:
  - Requests per Second: Monitor baseline (100-1000 RPS)
  - Concurrent Connections: < 1000

Error Rates:
  - 4xx Error Rate: < 2%
  - 5xx Error Rate: < 0.1%
  - Timeout Rate: < 0.1%

Endpoint-Specific Metrics:
  - /health: < 50ms response time
  - /auth/login: < 300ms response time
  - /voice/synthesize: < 2s response time
  - /properties/search: < 500ms response time
```

### Infrastructure Metrics

#### System Resources
```yaml
CPU Usage:
  - Warning: > 70%
  - Critical: > 85%

Memory Usage:
  - Warning: > 80%
  - Critical: > 90%

Disk Usage:
  - Warning: > 80%
  - Critical: > 90%

Network I/O:
  - Bandwidth Utilization: < 80%
  - Connection Errors: < 1%
```

#### Database Performance (PostgreSQL)
```yaml
Connection Pool:
  - Active Connections: < 80% of max
  - Wait Time: < 100ms

Query Performance:
  - Average Query Time: < 50ms
  - Slow Query Count: < 10 per minute
  - Lock Wait Time: < 100ms

Database Health:
  - Replication Lag: < 1s
  - Deadlock Count: < 1 per hour
  - Cache Hit Ratio: > 95%
```

#### Cache Layer (Redis)
```yaml
Performance:
  - Hit Rate: > 90%
  - Average Response Time: < 1ms
  - Memory Usage: < 80%

Connection Health:
  - Connection Count: < 1000
  - Failed Commands: < 0.1%
  - Keyspace Misses: < 10%
```

### Business Metrics

#### Voice Processing
```yaml
Voice Service Health:
  - ElevenLabs API Success Rate: > 99%
  - Voice Generation Time: < 3s
  - Audio Quality Score: > 8/10
  - Voice Service Uptime: > 99.9%

Usage Metrics:
  - Voice Requests per Hour: Monitor trend
  - Unique Voice Sessions: Monitor trend
  - Voice Error Rate: < 1%
```

#### Real Estate Platform
```yaml
Property Data:
  - Property Search Response Time: < 500ms
  - Property Data Freshness: < 1 hour
  - Search Result Accuracy: > 95%

User Engagement:
  - Daily Active Users: Monitor trend
  - Property Views per Session: > 5
  - Lead Generation Rate: > 2%
```

### Security Metrics
```yaml
Authentication:
  - Failed Login Attempts: < 5 per user per hour
  - Suspicious Login Patterns: Monitor
  - Token Validation Failures: < 0.1%

API Security:
  - Rate Limit Violations: < 1%
  - Unauthorized Access Attempts: Monitor
  - SQL Injection Attempts: 0 tolerance

General Security:
  - SSL Certificate Expiry: > 30 days
  - Security Scan Results: No critical issues
  - Data Breach Indicators: 0 tolerance
```

---

## Alert Thresholds

### Critical Alerts (P0) - Immediate Response
```yaml
System Outages:
  - Application Availability: < 95% for 2 minutes
  - API Health Check Failures: > 50% for 1 minute
  - Database Connection Failures: > 10 per minute

Performance Critical:
  - API Response Time: > 5s (P99) for 5 minutes
  - Error Rate: > 5% for 2 minutes
  - CPU Usage: > 95% for 10 minutes
  - Memory Usage: > 95% for 5 minutes

Security Critical:
  - Multiple failed login attempts: > 100 in 5 minutes
  - Suspicious data access patterns detected
  - SSL certificate expired
```

### High Priority Alerts (P1) - Response within 1 hour
```yaml
Performance Degradation:
  - API Response Time: > 1s (P95) for 10 minutes
  - Page Load Time: > 3s for 10 minutes
  - Database Query Time: > 500ms average for 15 minutes

Resource Warnings:
  - CPU Usage: > 85% for 15 minutes
  - Memory Usage: > 85% for 10 minutes
  - Disk Usage: > 90% for any volume

Service Issues:
  - Voice Service Error Rate: > 5% for 10 minutes
  - Cache Hit Rate: < 80% for 30 minutes
  - Queue Depth: > 1000 messages for 10 minutes
```

### Medium Priority Alerts (P2) - Response within 4 hours
```yaml
Performance Issues:
  - API Response Time: > 500ms (P95) for 30 minutes
  - Cache Hit Rate: < 90% for 1 hour
  - Background Job Failures: > 5% for 1 hour

Resource Monitoring:
  - CPU Usage: > 70% for 30 minutes
  - Memory Usage: > 80% for 30 minutes
  - Disk Usage: > 80% for any volume

Business Metrics:
  - User Session Duration: < 2 minutes average
  - Bounce Rate: > 60% for 1 hour
  - API Usage: 50% below baseline for 2 hours
```

### Low Priority Alerts (P3) - Response within 24 hours
```yaml
Trending Issues:
  - Gradual performance degradation over 24 hours
  - Resource usage trending upward
  - Error rate increasing slowly

Maintenance Reminders:
  - SSL certificates expiring in 30 days
  - Database maintenance windows approaching
  - Log retention cleanup needed
```

---

## Dashboard Configurations

### Executive Dashboard
**URL**: https://grafana.seiketsu.ai/dashboard/executive

#### Key Panels
```yaml
Business Metrics (Top Row):
  - Daily Active Users (24h trend)
  - Voice Interactions Count (real-time)
  - Property Searches (hourly)
  - Revenue Impact (daily)

System Health (Second Row):
  - Overall System Status (green/yellow/red)
  - API Response Times (real-time)
  - Error Rates (24h trend)
  - Uptime Percentage (monthly)

Infrastructure (Third Row):
  - Server Resource Usage (CPU/Memory)
  - Database Performance
  - CDN Performance
  - External Service Status
```

### Operations Dashboard
**URL**: https://grafana.seiketsu.ai/dashboard/operations

#### Detailed Monitoring Panels
```yaml
Application Performance:
  - API Endpoint Response Times (by endpoint)
  - Request Volume (requests/second)
  - Error Rate by Service
  - Active User Sessions

Infrastructure Health:
  - Server Metrics (CPU, Memory, Disk, Network)
  - Container Health (Docker/Kubernetes)
  - Load Balancer Statistics
  - Auto-scaling Events

Database Monitoring:
  - Query Performance (slow queries)
  - Connection Pool Status
  - Replication Lag
  - Database Size and Growth

External Services:
  - ElevenLabs API Status
  - Supabase Performance
  - AWS Service Health
  - CDN Performance
```

### Development Dashboard
**URL**: https://grafana.seiketsu.ai/dashboard/development

#### Development-Focused Metrics
```yaml
Code Quality:
  - Build Success Rate
  - Test Coverage
  - Deployment Frequency
  - Lead Time for Changes

Performance Testing:
  - Load Test Results
  - Performance Benchmarks
  - Memory Usage Trends
  - API Latency Distribution

Error Tracking:
  - JavaScript Errors (frontend)
  - Python Exceptions (backend)
  - Database Errors
  - Integration Failures
```

### Security Dashboard
**URL**: https://grafana.seiketsu.ai/dashboard/security

#### Security Monitoring
```yaml
Authentication & Access:
  - Login Success/Failure Rates
  - Failed Authentication Attempts
  - Suspicious Access Patterns
  - Session Management Metrics

Threat Detection:
  - Rate Limiting Violations
  - SQL Injection Attempts
  - XSS Attack Patterns
  - DDoS Indicators

Compliance Monitoring:
  - Data Access Logs
  - Privacy Compliance Metrics
  - Audit Trail Completeness
  - Certificate Status
```

---

## Log Analysis Procedures

### Log Collection Architecture
```yaml
Application Logs:
  - Location: /var/log/seiketsu/
  - Format: JSON structured logging
  - Retention: 30 days local, 1 year in S3
  - Shipping: Fluentd → ELK Stack

Infrastructure Logs:
  - AWS CloudTrail: All API calls
  - VPC Flow Logs: Network traffic
  - Load Balancer Logs: Request patterns
  - Container Logs: Docker/Kubernetes events

Security Logs:
  - Authentication events
  - Access control changes
  - Failed requests
  - Security tool outputs
```

### Log Analysis Queries

#### Performance Investigation
```bash
# High response time requests
GET /logstash-*/_search
{
  "query": {
    "bool": {
      "must": [
        {"range": {"response_time": {"gte": 1000}}},
        {"range": {"timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "aggs": {
    "slow_endpoints": {
      "terms": {"field": "endpoint.keyword"}
    }
  }
}

# Error rate analysis
GET /logstash-*/_search
{
  "query": {
    "bool": {
      "must": [
        {"range": {"status_code": {"gte": 400}}},
        {"range": {"timestamp": {"gte": "now-4h"}}}
      ]
    }
  },
  "aggs": {
    "errors_by_service": {
      "terms": {"field": "service.keyword"}
    }
  }
}
```

#### Security Analysis
```bash
# Failed authentication attempts
GET /logstash-*/_search
{
  "query": {
    "bool": {
      "must": [
        {"match": {"event_type": "authentication_failure"}},
        {"range": {"timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "aggs": {
    "failed_by_ip": {
      "terms": {"field": "source_ip.keyword"}
    }
  }
}

# Suspicious patterns
GET /logstash-*/_search
{
  "query": {
    "bool": {
      "should": [
        {"match": {"message": "sql injection"}},
        {"match": {"message": "xss attempt"}},
        {"match": {"user_agent": "bot"}}
      ]
    }
  }
}
```

#### Business Intelligence
```bash
# User engagement patterns
GET /logstash-*/_search
{
  "query": {
    "bool": {
      "must": [
        {"match": {"event_type": "user_action"}},
        {"range": {"timestamp": {"gte": "now-24h"}}}
      ]
    }
  },
  "aggs": {
    "actions_by_hour": {
      "date_histogram": {
        "field": "timestamp",
        "calendar_interval": "1h"
      }
    }
  }
}
```

### Log Analysis Best Practices

#### Daily Log Review Process
```bash
# Morning routine (automated report)
./scripts/generate-daily-log-report.sh

# Key metrics to review:
# - Error rate trends
# - Performance anomalies
# - Security incidents
# - User behavior patterns
```

#### Weekly Log Analysis
```bash
# Comprehensive weekly analysis
./scripts/weekly-log-analysis.sh

# Focus areas:
# - Performance trends
# - Capacity planning insights
# - Security posture assessment
# - User experience metrics
```

---

## Performance Baseline Documentation

### Baseline Metrics (Production Environment)

#### Application Performance Baselines
```yaml
API Response Times (P95):
  - GET /health: 25ms
  - POST /auth/login: 180ms
  - GET /properties/search: 320ms
  - POST /voice/synthesize: 1.8s
  - GET /dashboard/data: 450ms

Frontend Performance:
  - Page Load Time: 1.2s
  - Time to Interactive: 2.1s
  - Bundle Size: 1.8MB
  - JavaScript Execution Time: 150ms

Database Performance:
  - Average Query Time: 12ms
  - Connection Pool Usage: 35%
  - Cache Hit Ratio: 96.2%
  - Slow Query Count: 2 per hour
```

#### Infrastructure Baselines
```yaml
Server Resources (Normal Load):
  - CPU Usage: 25-40%
  - Memory Usage: 60-75%
  - Disk I/O: 15% utilization
  - Network I/O: 30% utilization

Database Server:
  - CPU Usage: 20-35%
  - Memory Usage: 70-80%
  - Connection Count: 45-60
  - Transaction Rate: 150 TPS

Redis Cache:
  - Memory Usage: 45-60%
  - Hit Rate: 94-97%
  - Operations/Second: 500-800
  - Average Latency: 0.8ms
```

#### Traffic Patterns
```yaml
Daily Traffic Pattern:
  - Peak Hours: 9 AM - 5 PM EST
  - Peak RPS: 850 requests/second
  - Off-Peak RPS: 120 requests/second
  - Weekend Traffic: 60% of weekday

Seasonal Variations:
  - Q4 (Oct-Dec): +40% traffic
  - Summer (Jun-Aug): -15% traffic
  - New Year (Jan): +25% for first 2 weeks

Geographic Distribution:
  - US East Coast: 45%
  - US West Coast: 30%
  - International: 25%
```

### Performance Testing Procedures

#### Load Testing Protocol
```bash
# Weekly load testing
k6 run --vus 100 --duration 30m performance-tests/load-test.js

# Monthly stress testing
k6 run --vus 500 --duration 60m performance-tests/stress-test.js

# Performance regression testing (after deployments)
k6 run --vus 50 --duration 10m performance-tests/regression-test.js
```

#### Performance Test Scenarios
```javascript
// Baseline Load Test
export default function () {
  // 70% property searches
  if (Math.random() < 0.7) {
    http.get(`${BASE_URL}/properties/search?location=downtown`);
  }
  
  // 20% voice interactions
  if (Math.random() < 0.2) {
    http.post(`${BASE_URL}/voice/synthesize`, {
      text: "Hello, how can I help you find a property today?"
    });
  }
  
  // 10% user management
  if (Math.random() < 0.1) {
    http.get(`${BASE_URL}/dashboard/data`);
  }
  
  sleep(1);
}
```

### Capacity Planning Guidelines

#### Scaling Triggers
```yaml
Horizontal Scaling Triggers:
  - CPU Usage > 70% for 10 minutes
  - Memory Usage > 80% for 5 minutes
  - Response Time > 500ms (P95) for 15 minutes
  - Queue Length > 100 for 5 minutes

Vertical Scaling Considerations:
  - Memory-intensive operations (voice processing)
  - Database connection limits
  - Cache size requirements

Auto-scaling Configuration:
  - Min Instances: 3
  - Max Instances: 20
  - Scale-out Cooldown: 5 minutes
  - Scale-in Cooldown: 10 minutes
```

#### Resource Planning Formula
```yaml
# Capacity planning calculations
Target RPS = Peak_RPS * Growth_Factor * Safety_Buffer
Required_Instances = Target_RPS / Instance_Capacity
Required_Memory = Base_Memory + (Active_Users * Memory_Per_User)
Required_Storage = Current_Usage * (1 + Monthly_Growth_Rate)^Months
```

---

## Alerting Configuration Examples

### Prometheus Alert Rules
```yaml
# prometheus-alerts.yml
groups:
  - name: seiketsu-api
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"
      
      - alert: DatabaseConnectionHigh
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connection count"
          description: "Active connections: {{ $value }}"
```

### PagerDuty Integration
```yaml
# pagerduty-config.yml
services:
  - name: seiketsu-critical
    escalation_policy: immediate-escalation
    alert_grouping: intelligent
    
  - name: seiketsu-warning
    escalation_policy: standard-escalation
    alert_grouping: time

routing_rules:
  - conditions:
      - field: severity
        operator: equals
        value: critical
    actions:
      - route:
          type: route
          value: seiketsu-critical
  
  - conditions:
      - field: severity
        operator: equals
        value: warning
    actions:
      - route:
          type: route
          value: seiketsu-warning
```

### Slack Notifications
```yaml
# slack-notifications.yml
channels:
  critical: "#incident-response"
  warning: "#engineering-alerts"
  info: "#system-notifications"

message_templates:
  critical: |
    🚨 CRITICAL ALERT 🚨
    Service: {{ .CommonLabels.service }}
    Alert: {{ .CommonLabels.alertname }}
    Description: {{ .CommonAnnotations.description }}
    Runbook: {{ .CommonAnnotations.runbook }}
  
  warning: |
    ⚠️ WARNING
    Service: {{ .CommonLabels.service }}
    Alert: {{ .CommonLabels.alertname }}
    Description: {{ .CommonAnnotations.description }}
```

---

## Monitoring Tools Configuration

### Grafana Setup
```yaml
# grafana-datasources.yml
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
  
  - name: Elasticsearch
    type: elasticsearch
    url: http://elasticsearch:9200
    database: logstash-*
    timeField: "@timestamp"
  
  - name: PostgreSQL
    type: postgres
    url: postgres://monitor:password@db:5432/seiketsu
```

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "prometheus-alerts.yml"

scrape_configs:
  - job_name: 'seiketsu-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
    scrape_interval: 10s
  
  - job_name: 'seiketsu-web'
    static_configs:
      - targets: ['web:3000']
    metrics_path: /api/metrics
    scrape_interval: 15s
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### Custom Metrics Collection
```python
# Python metrics collection (FastAPI)
from prometheus_client import Counter, Histogram, Gauge
import time

# Custom metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
VOICE_REQUESTS = Counter('voice_requests_total', 'Total voice synthesis requests', ['status'])
ACTIVE_USERS = Gauge('active_users_current', 'Current active users')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    
    return response
```

```javascript
// Frontend metrics collection (Next.js)
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  fetch('/api/metrics', {
    method: 'POST',
    body: JSON.stringify(metric),
    headers: { 'Content-Type': 'application/json' }
  });
}

// Collect Core Web Vitals
getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);

// Custom business metrics
export function trackVoiceInteraction(duration, success) {
  sendToAnalytics({
    name: 'voice_interaction',
    value: duration,
    success: success,
    timestamp: Date.now()
  });
}
```

---

## Troubleshooting Common Monitoring Issues

### Missing Metrics
```bash
# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets

# Verify metric endpoints
curl http://api:8000/metrics
curl http://web:3000/api/metrics

# Check Grafana data sources
curl -u admin:password http://grafana:3000/api/datasources
```

### Alert Fatigue Prevention
```yaml
# Alert grouping configuration
route:
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 24h
  
  routes:
    - match:
        severity: critical
      group_wait: 0s
      repeat_interval: 1h
    
    - match:
        severity: warning
      group_wait: 5m
      repeat_interval: 12h
```

### Dashboard Performance Optimization
```yaml
# Query optimization for Grafana
- Use recording rules for complex queries
- Limit time ranges for heavy queries  
- Use template variables for filtering
- Implement query caching where possible

# Example recording rule
groups:
  - name: seiketsu_aggregations
    interval: 30s
    rules:
      - record: seiketsu:api_request_rate
        expr: rate(http_requests_total{service="seiketsu-api"}[5m])
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-08-09 | Initial monitoring and alerting guide | Seiketsu Team |

---

*Last Updated: 2025-08-09*
*Next Review: 2025-09-09*