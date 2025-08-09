#!/usr/bin/env python3
"""
Seiketsu AI - Metrics Forwarder Lambda
Forwards CloudWatch metrics to 21dev.ai monitoring platform
"""

import json
import os
import boto3
import requests
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
cloudwatch = boto3.client('cloudwatch')
secrets_manager = boto3.client('secretsmanager')

# Configuration from environment variables
MONITORING_ENDPOINT = os.environ.get('MONITORING_ENDPOINT')
API_KEY_SECRET_ARN = os.environ.get('API_KEY_SECRET_ARN')
PROJECT_NAME = os.environ.get('PROJECT_NAME')
ENVIRONMENT = os.environ.get('ENVIRONMENT')

def get_api_key():
    """Retrieve API key from Secrets Manager"""
    try:
        response = secrets_manager.get_secret_value(SecretId=API_KEY_SECRET_ARN)
        return response['SecretString']
    except Exception as e:
        logger.error(f"Failed to retrieve API key: {e}")
        return None

def get_cloudwatch_metrics():
    """Retrieve key metrics from CloudWatch"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)
    
    metrics_to_collect = [
        {
            'namespace': 'Seiketsu/Performance',
            'metric_name': 'VoiceResponseTime',
            'statistic': 'Average'
        },
        {
            'namespace': 'Seiketsu/Performance',
            'metric_name': 'APIResponseTime',
            'statistic': 'Average'
        },
        {
            'namespace': 'AWS/ECS',
            'metric_name': 'CPUUtilization',
            'dimensions': [{'Name': 'ServiceName', 'Value': f'{PROJECT_NAME}-api-service'}],
            'statistic': 'Average'
        },
        {
            'namespace': 'AWS/ECS',
            'metric_name': 'MemoryUtilization',
            'dimensions': [{'Name': 'ServiceName', 'Value': f'{PROJECT_NAME}-api-service'}],
            'statistic': 'Average'
        },
        {
            'namespace': 'AWS/RDS',
            'metric_name': 'CPUUtilization',
            'dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': f'{PROJECT_NAME}-database'}],
            'statistic': 'Average'
        },
        {
            'namespace': 'AWS/RDS',
            'metric_name': 'DatabaseConnections',
            'dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': f'{PROJECT_NAME}-database'}],
            'statistic': 'Average'
        },
        {
            'namespace': 'AWS/ApplicationELB',
            'metric_name': 'TargetResponseTime',
            'dimensions': [{'Name': 'LoadBalancer', 'Value': f'{PROJECT_NAME}-alb'}],
            'statistic': 'Average'
        },
        {
            'namespace': 'AWS/ApplicationELB',
            'metric_name': 'RequestCount',
            'dimensions': [{'Name': 'LoadBalancer', 'Value': f'{PROJECT_NAME}-alb'}],
            'statistic': 'Sum'
        },
        {
            'namespace': 'Seiketsu/MultiTenant',
            'metric_name': 'ActiveTenants',
            'statistic': 'Maximum'
        },
        {
            'namespace': 'Seiketsu/Performance',
            'metric_name': 'VoiceProcessingErrors',
            'statistic': 'Sum'
        }
    ]
    
    collected_metrics = []
    
    for metric_config in metrics_to_collect:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace=metric_config['namespace'],
                MetricName=metric_config['metric_name'],
                Dimensions=metric_config.get('dimensions', []),
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes
                Statistics=[metric_config['statistic']]
            )
            
            if response['Datapoints']:
                # Get the latest datapoint
                latest_datapoint = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                
                collected_metrics.append({
                    'metric_name': metric_config['metric_name'],
                    'namespace': metric_config['namespace'],
                    'value': latest_datapoint[metric_config['statistic']],
                    'timestamp': latest_datapoint['Timestamp'].isoformat(),
                    'unit': latest_datapoint.get('Unit', 'None'),
                    'dimensions': metric_config.get('dimensions', [])
                })
                
        except Exception as e:
            logger.error(f"Failed to collect metric {metric_config['metric_name']}: {e}")
    
    return collected_metrics

def calculate_derived_metrics(metrics: List[Dict]) -> List[Dict]:
    """Calculate derived metrics for better insights"""
    derived_metrics = []
    
    # Find voice response time and error count
    voice_response_time = None
    voice_errors = None
    
    for metric in metrics:
        if metric['metric_name'] == 'VoiceResponseTime':
            voice_response_time = metric['value']
        elif metric['metric_name'] == 'VoiceProcessingErrors':
            voice_errors = metric['value']
    
    # Calculate SLA compliance
    if voice_response_time is not None:
        sla_compliance = 100 if voice_response_time <= 2000 else 0
        derived_metrics.append({
            'metric_name': 'VoiceSLACompliance',
            'namespace': 'Seiketsu/Performance',
            'value': sla_compliance,
            'timestamp': datetime.utcnow().isoformat(),
            'unit': 'Percent',
            'dimensions': []
        })
    
    # Calculate error rate if we have both metrics
    if voice_errors is not None and voice_errors > 0:
        derived_metrics.append({
            'metric_name': 'VoiceErrorRate',
            'namespace': 'Seiketsu/Performance', 
            'value': voice_errors,
            'timestamp': datetime.utcnow().isoformat(),
            'unit': 'Percent',
            'dimensions': []
        })
    
    return derived_metrics

def format_metrics_for_21dev(metrics: List[Dict]) -> Dict:
    """Format metrics for 21dev.ai API"""
    formatted_metrics = []
    
    for metric in metrics:
        formatted_metric = {
            'name': f"{PROJECT_NAME}.{metric['namespace'].replace('/', '.').lower()}.{metric['metric_name'].lower()}",
            'value': metric['value'],
            'timestamp': metric['timestamp'],
            'tags': {
                'environment': ENVIRONMENT,
                'project': PROJECT_NAME,
                'namespace': metric['namespace'],
                'unit': metric['unit']
            }
        }
        
        # Add dimensions as tags
        for dimension in metric['dimensions']:
            formatted_metric['tags'][dimension['Name'].lower()] = dimension['Value']
        
        formatted_metrics.append(formatted_metric)
    
    return {
        'metrics': formatted_metrics,
        'metadata': {
            'source': 'aws-cloudwatch',
            'project': PROJECT_NAME,
            'environment': ENVIRONMENT,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
    }

def send_metrics_to_21dev(formatted_metrics: Dict, api_key: str) -> bool:
    """Send formatted metrics to 21dev.ai"""
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': f'seiketsu-ai-metrics-forwarder/{ENVIRONMENT}'
        }
        
        response = requests.post(
            MONITORING_ENDPOINT,
            json=formatted_metrics,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully sent {len(formatted_metrics['metrics'])} metrics to 21dev.ai")
            return True
        else:
            logger.error(f"Failed to send metrics. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Exception while sending metrics to 21dev.ai: {e}")
        return False

def send_health_check() -> bool:
    """Send health check metric"""
    health_metric = {
        'metrics': [{
            'name': f"{PROJECT_NAME}.system.health_check",
            'value': 1,
            'timestamp': datetime.utcnow().isoformat(),
            'tags': {
                'environment': ENVIRONMENT,
                'project': PROJECT_NAME,
                'source': 'metrics-forwarder'
            }
        }],
        'metadata': {
            'source': 'health-check',
            'project': PROJECT_NAME,
            'environment': ENVIRONMENT,
            'timestamp': datetime.utcnow().isoformat()
        }
    }
    
    api_key = get_api_key()
    if not api_key:
        return False
    
    return send_metrics_to_21dev(health_metric, api_key)

def handler(event, context):
    """Lambda handler function"""
    logger.info(f"Starting metrics forwarding for {PROJECT_NAME} ({ENVIRONMENT})")
    
    try:
        # Get API key
        api_key = get_api_key()
        if not api_key:
            logger.error("Failed to retrieve API key")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to retrieve API key'})
            }
        
        # Collect metrics from CloudWatch
        logger.info("Collecting metrics from CloudWatch...")
        raw_metrics = get_cloudwatch_metrics()
        
        if not raw_metrics:
            logger.warning("No metrics collected from CloudWatch")
            # Send health check anyway
            send_health_check()
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No metrics to forward, health check sent'})
            }
        
        # Calculate derived metrics
        derived_metrics = calculate_derived_metrics(raw_metrics)
        all_metrics = raw_metrics + derived_metrics
        
        # Format metrics for 21dev.ai
        logger.info(f"Formatting {len(all_metrics)} metrics for 21dev.ai...")
        formatted_metrics = format_metrics_for_21dev(all_metrics)
        
        # Send metrics to 21dev.ai
        logger.info("Sending metrics to 21dev.ai...")
        success = send_metrics_to_21dev(formatted_metrics, api_key)
        
        if success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Successfully forwarded {len(all_metrics)} metrics',
                    'metrics_count': len(all_metrics),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to send metrics to 21dev.ai'})
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in metrics forwarder: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Unexpected error: {str(e)}'})
        }

# For local testing
if __name__ == "__main__":
    test_event = {}
    test_context = {}
    result = handler(test_event, test_context)
    print(json.dumps(result, indent=2))