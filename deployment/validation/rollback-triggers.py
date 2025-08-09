#!/usr/bin/env python3
"""
Seiketsu AI Automatic Rollback System
Real-time monitoring and automatic rollback triggers for production deployments
"""

import asyncio
import aiohttp
import logging
import json
import os
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import psutil
import boto3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RollbackSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RollbackAction(Enum):
    MONITOR = "monitor"
    ALERT = "alert"
    PREPARE = "prepare"
    EXECUTE = "execute"

@dataclass
class RollbackTrigger:
    name: str
    severity: RollbackSeverity
    action: RollbackAction
    condition: str
    threshold: float
    duration: int  # seconds
    message: str
    first_detected: Optional[datetime] = None
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class RollbackMonitor:
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.triggers = self._initialize_triggers()
        self.session = None
        self.monitoring = True
        self.metrics_history = []
        self.rollback_initiated = False
        
    def _load_config(self, config_file: str = None) -> Dict:
        """Load configuration from file or environment"""
        default_config = {
            'api_base_url': os.getenv('API_BASE_URL', 'https://api.seiketsu-ai.com'),
            'web_base_url': os.getenv('WEB_BASE_URL', 'https://seiketsu-ai.com'),
            'monitoring_interval': int(os.getenv('MONITORING_INTERVAL', '30')),  # seconds
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
            'ecs_cluster': os.getenv('ECS_CLUSTER', 'seiketsu-ai-production-cluster'),
            'ecs_service': os.getenv('ECS_SERVICE', 'seiketsu-ai-production-api-service'),
            'cloudwatch_namespace': os.getenv('CLOUDWATCH_NAMESPACE', 'SeiketsuAI/Production'),
            'slack_webhook': os.getenv('SLACK_WEBHOOK_URL'),
            'pagerduty_key': os.getenv('PAGERDUTY_SERVICE_KEY'),
            'rollback_script': os.getenv('ROLLBACK_SCRIPT', './scripts/emergency-rollback.sh'),
            'notification_channels': ['slack', 'pagerduty', 'email']
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                default_config.update(file_config)
        
        return default_config
    
    def _initialize_triggers(self) -> List[RollbackTrigger]:
        """Initialize rollback triggers based on configuration"""
        return [
            # Performance-based triggers
            RollbackTrigger(
                name="voice_response_time_critical",
                severity=RollbackSeverity.CRITICAL,
                action=RollbackAction.EXECUTE,
                condition="voice_response_time_p95 > threshold",
                threshold=5000.0,  # 5 seconds
                duration=300,  # 5 minutes
                message="Voice response time critically high - initiating rollback"
            ),
            RollbackTrigger(
                name="api_error_rate_high",
                severity=RollbackSeverity.HIGH,
                action=RollbackAction.EXECUTE,
                condition="error_rate > threshold",
                threshold=5.0,  # 5%
                duration=180,  # 3 minutes
                message="API error rate too high - initiating rollback"
            ),
            RollbackTrigger(
                name="database_unavailable",
                severity=RollbackSeverity.CRITICAL,
                action=RollbackAction.EXECUTE,
                condition="database_availability < threshold",
                threshold=50.0,  # 50% availability
                duration=120,  # 2 minutes
                message="Database critically unavailable - initiating rollback"
            ),
            RollbackTrigger(
                name="memory_exhaustion",
                severity=RollbackSeverity.HIGH,
                action=RollbackAction.PREPARE,
                condition="memory_usage > threshold",
                threshold=95.0,  # 95%
                duration=600,  # 10 minutes
                message="Memory usage critically high - preparing rollback"
            ),
            
            # Security-based triggers
            RollbackTrigger(
                name="authentication_failures_spike",
                severity=RollbackSeverity.MEDIUM,
                action=RollbackAction.ALERT,
                condition="auth_failures_per_minute > threshold",
                threshold=100.0,  # 100 failures per minute
                duration=300,  # 5 minutes
                message="Authentication failures spike detected"
            ),
            RollbackTrigger(
                name="ssl_certificate_issues",
                severity=RollbackSeverity.HIGH,
                action=RollbackAction.EXECUTE,
                condition="ssl_certificate_valid == false",
                threshold=1.0,  # Boolean check
                duration=60,  # 1 minute
                message="SSL certificate issues detected - initiating rollback"
            ),
            
            # Business continuity triggers
            RollbackTrigger(
                name="client_satisfaction_drop",
                severity=RollbackSeverity.MEDIUM,
                action=RollbackAction.ALERT,
                condition="client_satisfaction < threshold",
                threshold=7.0,  # Out of 10
                duration=1800,  # 30 minutes
                message="Client satisfaction dropping significantly"
            ),
            RollbackTrigger(
                name="revenue_impact_high",
                severity=RollbackSeverity.HIGH,
                action=RollbackAction.PREPARE,
                condition="revenue_impact_per_hour > threshold",
                threshold=10000.0,  # $10K per hour
                duration=900,  # 15 minutes
                message="High revenue impact detected"
            ),
            
            # Infrastructure triggers
            RollbackTrigger(
                name="load_balancer_failures",
                severity=RollbackSeverity.HIGH,
                action=RollbackAction.EXECUTE,
                condition="load_balancer_healthy_targets < threshold",
                threshold=50.0,  # 50% of targets healthy
                duration=180,  # 3 minutes
                message="Load balancer health critically low - initiating rollback"
            ),
            RollbackTrigger(
                name="disk_space_critical",
                severity=RollbackSeverity.MEDIUM,
                action=RollbackAction.ALERT,
                condition="disk_usage > threshold",
                threshold=90.0,  # 90%
                duration=900,  # 15 minutes
                message="Disk space critically low"
            )
        ]

    async def collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics for evaluation"""
        metrics = {}
        
        try:
            # API performance metrics
            api_metrics = await self._get_api_metrics()
            metrics.update(api_metrics)
            
            # Database metrics
            db_metrics = await self._get_database_metrics()
            metrics.update(db_metrics)
            
            # Infrastructure metrics
            infra_metrics = await self._get_infrastructure_metrics()
            metrics.update(infra_metrics)
            
            # Business metrics
            business_metrics = await self._get_business_metrics()
            metrics.update(business_metrics)
            
            # Security metrics
            security_metrics = await self._get_security_metrics()
            metrics.update(security_metrics)
            
            # Add timestamp
            metrics['timestamp'] = time.time()
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            metrics['collection_error'] = True
            
        return metrics

    async def _get_api_metrics(self) -> Dict[str, float]:
        """Get API performance metrics"""
        metrics = {}
        
        try:
            # Test API response time
            start_time = time.time()
            async with self.session.get(f"{self.config['api_base_url']}/health") as response:
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                metrics['api_response_time'] = response_time
                metrics['api_status_code'] = response.status
                
                if response.status == 200:
                    data = await response.json()
                    metrics.update({
                        'api_availability': 100.0,
                        'voice_response_time_p95': data.get('voice_latency_p95', 0),
                        'error_rate': data.get('error_rate', 0)
                    })
                else:
                    metrics['api_availability'] = 0.0
                    metrics['error_rate'] = 100.0
                    
        except Exception as e:
            logger.error(f"Error getting API metrics: {str(e)}")
            metrics.update({
                'api_availability': 0.0,
                'api_response_time': 30000.0,  # 30 seconds timeout
                'error_rate': 100.0
            })
            
        return metrics

    async def _get_database_metrics(self) -> Dict[str, float]:
        """Get database performance metrics"""
        metrics = {}
        
        try:
            # Test database connectivity through API
            async with self.session.get(f"{self.config['api_base_url']}/admin/health/database") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.update({
                        'database_availability': 100.0,
                        'database_response_time': data.get('response_time_ms', 0),
                        'database_connections': data.get('active_connections', 0)
                    })
                else:
                    metrics['database_availability'] = 0.0
                    
        except Exception as e:
            logger.error(f"Error getting database metrics: {str(e)}")
            metrics['database_availability'] = 0.0
            
        return metrics

    async def _get_infrastructure_metrics(self) -> Dict[str, float]:
        """Get infrastructure metrics from CloudWatch"""
        metrics = {}
        
        try:
            # Use CloudWatch to get ECS service metrics
            cloudwatch = boto3.client('cloudwatch', region_name=self.config['aws_region'])
            
            # CPU and Memory utilization
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            # Get CPU utilization
            cpu_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/ECS',
                MetricName='CPUUtilization',
                Dimensions=[
                    {'Name': 'ServiceName', 'Value': self.config['ecs_service']},
                    {'Name': 'ClusterName', 'Value': self.config['ecs_cluster']}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if cpu_response['Datapoints']:
                metrics['cpu_usage'] = cpu_response['Datapoints'][-1]['Average']
            
            # Get Memory utilization
            memory_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/ECS',
                MetricName='MemoryUtilization',
                Dimensions=[
                    {'Name': 'ServiceName', 'Value': self.config['ecs_service']},
                    {'Name': 'ClusterName', 'Value': self.config['ecs_cluster']}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if memory_response['Datapoints']:
                metrics['memory_usage'] = memory_response['Datapoints'][-1]['Average']
            
            # Get load balancer health
            alb_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='HealthyHostCount',
                Dimensions=[
                    {'Name': 'LoadBalancer', 'Value': f"app/seiketsu-ai-{os.getenv('ENVIRONMENT', 'production')}-alb"}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if alb_response['Datapoints']:
                metrics['load_balancer_healthy_targets'] = alb_response['Datapoints'][-1]['Average']
            
        except Exception as e:
            logger.error(f"Error getting infrastructure metrics: {str(e)}")
            # Use local system metrics as fallback
            metrics.update({
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            })
            
        return metrics

    async def _get_business_metrics(self) -> Dict[str, float]:
        """Get business performance metrics"""
        metrics = {}
        
        try:
            # Get business metrics through API
            async with self.session.get(f"{self.config['api_base_url']}/admin/metrics/business") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.update({
                        'client_satisfaction': data.get('client_satisfaction', 8.5),
                        'revenue_impact_per_hour': data.get('revenue_impact_per_hour', 0),
                        'tenant_provisioning_time': data.get('tenant_provisioning_time', 1800),
                        'active_tenants': data.get('active_tenants', 0)
                    })
                    
        except Exception as e:
            logger.error(f"Error getting business metrics: {str(e)}")
            # Use default values if metrics unavailable
            metrics.update({
                'client_satisfaction': 8.5,
                'revenue_impact_per_hour': 0,
                'tenant_provisioning_time': 1800,
                'active_tenants': 0
            })
            
        return metrics

    async def _get_security_metrics(self) -> Dict[str, float]:
        """Get security-related metrics"""
        metrics = {}
        
        try:
            # Check SSL certificate validity
            import ssl
            import socket
            from urllib.parse import urlparse
            
            parsed_url = urlparse(self.config['api_base_url'])
            context = ssl.create_default_context()
            
            with socket.create_connection((parsed_url.hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=parsed_url.hostname) as ssock:
                    cert = ssock.getpeercert()
                    # Check if certificate is valid (simplified check)
                    metrics['ssl_certificate_valid'] = 1.0 if cert else 0.0
            
            # Get authentication failure metrics through API
            async with self.session.get(f"{self.config['api_base_url']}/admin/metrics/security") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.update({
                        'auth_failures_per_minute': data.get('auth_failures_per_minute', 0),
                        'suspicious_activity_score': data.get('suspicious_activity_score', 0)
                    })
                    
        except Exception as e:
            logger.error(f"Error getting security metrics: {str(e)}")
            metrics.update({
                'ssl_certificate_valid': 0.0,
                'auth_failures_per_minute': 0,
                'suspicious_activity_score': 0
            })
            
        return metrics

    def evaluate_triggers(self, metrics: Dict[str, float]) -> List[RollbackTrigger]:
        """Evaluate all triggers against current metrics"""
        triggered = []
        current_time = datetime.utcnow()
        
        for trigger in self.triggers:
            try:
                # Evaluate the trigger condition
                if self._evaluate_condition(trigger, metrics):
                    # First detection
                    if trigger.first_detected is None:
                        trigger.first_detected = current_time
                        logger.warning(f"Trigger detected: {trigger.name}")
                    
                    # Check if duration threshold is met
                    time_since_detection = (current_time - trigger.first_detected).total_seconds()
                    
                    if time_since_detection >= trigger.duration:
                        trigger.last_triggered = current_time
                        trigger.trigger_count += 1
                        trigger.metadata['current_value'] = self._get_metric_value(trigger, metrics)
                        trigger.metadata['threshold'] = trigger.threshold
                        trigger.metadata['duration_exceeded'] = time_since_detection
                        
                        triggered.append(trigger)
                        logger.error(f"Trigger activated: {trigger.name} - {trigger.message}")
                else:
                    # Reset if condition no longer met
                    if trigger.first_detected is not None:
                        logger.info(f"Trigger condition cleared: {trigger.name}")
                        trigger.first_detected = None
                        
            except Exception as e:
                logger.error(f"Error evaluating trigger {trigger.name}: {str(e)}")
        
        return triggered

    def _evaluate_condition(self, trigger: RollbackTrigger, metrics: Dict[str, float]) -> bool:
        """Evaluate a specific trigger condition against metrics"""
        try:
            # Parse the condition and evaluate it
            condition = trigger.condition
            threshold = trigger.threshold
            
            if "voice_response_time_p95 > threshold" in condition:
                return metrics.get('voice_response_time_p95', 0) > threshold
            elif "error_rate > threshold" in condition:
                return metrics.get('error_rate', 0) > threshold
            elif "database_availability < threshold" in condition:
                return metrics.get('database_availability', 100) < threshold
            elif "memory_usage > threshold" in condition:
                return metrics.get('memory_usage', 0) > threshold
            elif "auth_failures_per_minute > threshold" in condition:
                return metrics.get('auth_failures_per_minute', 0) > threshold
            elif "ssl_certificate_valid == false" in condition:
                return metrics.get('ssl_certificate_valid', 1) < 0.5
            elif "client_satisfaction < threshold" in condition:
                return metrics.get('client_satisfaction', 10) < threshold
            elif "revenue_impact_per_hour > threshold" in condition:
                return metrics.get('revenue_impact_per_hour', 0) > threshold
            elif "load_balancer_healthy_targets < threshold" in condition:
                return metrics.get('load_balancer_healthy_targets', 100) < threshold
            elif "disk_usage > threshold" in condition:
                return metrics.get('disk_usage', 0) > threshold
            else:
                logger.warning(f"Unknown condition: {condition}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition {condition}: {str(e)}")
            return False

    def _get_metric_value(self, trigger: RollbackTrigger, metrics: Dict[str, float]) -> float:
        """Get the current metric value for a trigger"""
        condition = trigger.condition
        
        if "voice_response_time_p95" in condition:
            return metrics.get('voice_response_time_p95', 0)
        elif "error_rate" in condition:
            return metrics.get('error_rate', 0)
        elif "database_availability" in condition:
            return metrics.get('database_availability', 100)
        elif "memory_usage" in condition:
            return metrics.get('memory_usage', 0)
        elif "auth_failures_per_minute" in condition:
            return metrics.get('auth_failures_per_minute', 0)
        elif "ssl_certificate_valid" in condition:
            return metrics.get('ssl_certificate_valid', 1)
        elif "client_satisfaction" in condition:
            return metrics.get('client_satisfaction', 10)
        elif "revenue_impact_per_hour" in condition:
            return metrics.get('revenue_impact_per_hour', 0)
        elif "load_balancer_healthy_targets" in condition:
            return metrics.get('load_balancer_healthy_targets', 100)
        elif "disk_usage" in condition:
            return metrics.get('disk_usage', 0)
        else:
            return 0

    async def handle_triggers(self, triggered: List[RollbackTrigger]):
        """Handle triggered rollback conditions"""
        if not triggered:
            return
        
        # Sort by severity
        critical_triggers = [t for t in triggered if t.severity == RollbackSeverity.CRITICAL]
        high_triggers = [t for t in triggered if t.severity == RollbackSeverity.HIGH]
        
        # Handle critical triggers - immediate rollback
        if critical_triggers and not self.rollback_initiated:
            logger.critical("Critical triggers detected - initiating emergency rollback")
            await self._send_notifications(critical_triggers, "CRITICAL")
            await self._execute_rollback(critical_triggers)
            self.rollback_initiated = True
            return
        
        # Handle high severity triggers - prepare rollback
        if high_triggers:
            execute_triggers = [t for t in high_triggers if t.action == RollbackAction.EXECUTE]
            if execute_triggers and not self.rollback_initiated:
                logger.error("High severity triggers detected - initiating rollback")
                await self._send_notifications(execute_triggers, "HIGH")
                await self._execute_rollback(execute_triggers)
                self.rollback_initiated = True
                return
            
            prepare_triggers = [t for t in high_triggers if t.action == RollbackAction.PREPARE]
            if prepare_triggers:
                logger.warning("Preparing rollback due to high severity triggers")
                await self._send_notifications(prepare_triggers, "PREPARE")
                await self._prepare_rollback(prepare_triggers)
        
        # Handle medium severity triggers - alerting
        medium_triggers = [t for t in triggered if t.severity == RollbackSeverity.MEDIUM]
        if medium_triggers:
            logger.warning("Medium severity triggers detected - sending alerts")
            await self._send_notifications(medium_triggers, "ALERT")

    async def _execute_rollback(self, triggers: List[RollbackTrigger]):
        """Execute emergency rollback procedure"""
        logger.critical("EXECUTING EMERGENCY ROLLBACK")
        
        try:
            # Run rollback script
            result = subprocess.run([
                self.config['rollback_script'],
                '--reason', f"Triggered by: {', '.join([t.name for t in triggers])}",
                '--severity', 'critical'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("Rollback script executed successfully")
                await self._send_notifications(triggers, "ROLLBACK_SUCCESS")
            else:
                logger.error(f"Rollback script failed: {result.stderr}")
                await self._send_notifications(triggers, "ROLLBACK_FAILED")
                
        except Exception as e:
            logger.critical(f"Rollback execution failed: {str(e)}")
            await self._send_notifications(triggers, "ROLLBACK_ERROR")

    async def _prepare_rollback(self, triggers: List[RollbackTrigger]):
        """Prepare for potential rollback"""
        logger.warning("Preparing rollback systems")
        
        try:
            # Prepare rollback without executing
            result = subprocess.run([
                self.config['rollback_script'],
                '--prepare-only',
                '--reason', f"Preparation for: {', '.join([t.name for t in triggers])}"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info("Rollback preparation completed")
            else:
                logger.error(f"Rollback preparation failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Rollback preparation error: {str(e)}")

    async def _send_notifications(self, triggers: List[RollbackTrigger], alert_type: str):
        """Send notifications about triggered conditions"""
        message = f"🚨 Seiketsu AI {alert_type}: {', '.join([t.name for t in triggers])}"
        
        # Send Slack notification
        if 'slack' in self.config['notification_channels'] and self.config['slack_webhook']:
            await self._send_slack_notification(message, triggers, alert_type)
        
        # Send PagerDuty alert
        if 'pagerduty' in self.config['notification_channels'] and self.config['pagerduty_key']:
            await self._send_pagerduty_alert(message, triggers, alert_type)
        
        logger.info(f"Notifications sent for {alert_type}")

    async def _send_slack_notification(self, message: str, triggers: List[RollbackTrigger], alert_type: str):
        """Send Slack notification"""
        try:
            payload = {
                "text": message,
                "attachments": [{
                    "color": "danger" if alert_type in ["CRITICAL", "HIGH"] else "warning",
                    "fields": [{
                        "title": t.name,
                        "value": f"{t.message}\nValue: {t.metadata.get('current_value', 'N/A')} (Threshold: {t.threshold})",
                        "short": True
                    } for t in triggers]
                }]
            }
            
            async with self.session.post(self.config['slack_webhook'], json=payload) as response:
                if response.status == 200:
                    logger.info("Slack notification sent successfully")
                else:
                    logger.error(f"Slack notification failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Slack notification error: {str(e)}")

    async def _send_pagerduty_alert(self, message: str, triggers: List[RollbackTrigger], alert_type: str):
        """Send PagerDuty alert"""
        try:
            payload = {
                "routing_key": self.config['pagerduty_key'],
                "event_action": "trigger",
                "payload": {
                    "summary": message,
                    "severity": "critical" if alert_type in ["CRITICAL", "HIGH"] else "warning",
                    "source": "seiketsu-ai-rollback-monitor",
                    "component": "deployment-monitor",
                    "custom_details": {
                        "triggers": [t.name for t in triggers],
                        "alert_type": alert_type
                    }
                }
            }
            
            async with self.session.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload
            ) as response:
                if response.status == 202:
                    logger.info("PagerDuty alert sent successfully")
                else:
                    logger.error(f"PagerDuty alert failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"PagerDuty alert error: {str(e)}")

    async def start_monitoring(self):
        """Start continuous monitoring loop"""
        logger.info("Starting rollback monitoring system")
        
        # Initialize HTTP session
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        try:
            while self.monitoring:
                # Collect metrics
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 100 metric samples
                if len(self.metrics_history) > 100:
                    self.metrics_history.pop(0)
                
                # Evaluate triggers
                triggered = self.evaluate_triggers(metrics)
                
                # Handle triggered conditions
                if triggered:
                    await self.handle_triggers(triggered)
                
                # Log status
                logger.info(f"Monitoring cycle complete - {len(triggered)} triggers active")
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.config['monitoring_interval'])
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {str(e)}")
        finally:
            await self.session.close()

    def stop_monitoring(self):
        """Stop monitoring system"""
        self.monitoring = False
        logger.info("Stopping rollback monitoring system")

async def main():
    """Main monitoring execution"""
    monitor = RollbackMonitor()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"Monitoring system error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())