import json
import boto3
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Initialize AWS clients
cloudwatch = boto3.client('cloudwatch')
secretsmanager = boto3.client('secretsmanager')

def handler(event, context):
    """
    Lambda function to forward CloudWatch metrics to 21dev.ai monitoring platform
    """
    try:
        # Get configuration from environment variables
        monitoring_endpoint = os.environ['MONITORING_ENDPOINT']
        api_key_secret_arn = os.environ['API_KEY_SECRET_ARN']
        project_name = os.environ['PROJECT_NAME']
        environment = os.environ['ENVIRONMENT']
        
        # Retrieve API key from Secrets Manager
        api_key = get_secret(api_key_secret_arn)
        
        # Get current time for metric queries
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        # Collect metrics from various AWS services
        metrics_data = {
            'timestamp': end_time.isoformat(),
            'project': project_name,
            'environment': environment,
            'metrics': {
                'performance': collect_performance_metrics(start_time, end_time, project_name),
                'infrastructure': collect_infrastructure_metrics(start_time, end_time, project_name),
                'application': collect_application_metrics(start_time, end_time, project_name),
                'multi_tenant': collect_tenant_metrics(start_time, end_time, project_name)
            }
        }
        
        # Forward metrics to 21dev.ai
        response = forward_metrics(monitoring_endpoint, api_key, metrics_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Metrics forwarded successfully',
                'metrics_count': len(metrics_data['metrics']),
                'response_status': response.status_code
            })
        }
        
    except Exception as e:
        print(f"Error forwarding metrics: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def get_secret(secret_arn: str) -> str:
    """Retrieve secret from AWS Secrets Manager"""
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_arn)
        return response['SecretString']
    except Exception as e:
        raise Exception(f"Failed to retrieve secret: {str(e)}")

def collect_performance_metrics(start_time: datetime, end_time: datetime, project_name: str) -> Dict[str, Any]:
    """Collect performance-related metrics"""
    metrics = {}
    
    try:
        # Voice response time
        voice_response = get_metric_statistics(
            namespace='Seiketsu/Performance',
            metric_name='VoiceResponseTime',
            start_time=start_time,
            end_time=end_time,
            statistic='Average'
        )
        metrics['voice_response_time_ms'] = voice_response
        
        # API response time
        api_response = get_metric_statistics(
            namespace='Seiketsu/Performance',
            metric_name='APIResponseTime',
            start_time=start_time,
            end_time=end_time,
            statistic='Average'
        )
        metrics['api_response_time_ms'] = api_response
        
        # ALB response time
        alb_response = get_metric_statistics(
            namespace='AWS/ApplicationELB',
            metric_name='TargetResponseTime',
            dimensions=[{'Name': 'LoadBalancer', 'Value': f'{project_name}-alb'}],
            start_time=start_time,
            end_time=end_time,
            statistic='Average'
        )
        metrics['alb_response_time_ms'] = alb_response * 1000 if alb_response else None
        
    except Exception as e:
        print(f"Error collecting performance metrics: {str(e)}")
    
    return metrics

def collect_infrastructure_metrics(start_time: datetime, end_time: datetime, project_name: str) -> Dict[str, Any]:
    """Collect infrastructure-related metrics"""
    metrics = {}
    
    try:
        # ECS CPU utilization
        ecs_cpu = get_metric_statistics(
            namespace='AWS/ECS',
            metric_name='CPUUtilization',
            dimensions=[
                {'Name': 'ServiceName', 'Value': f'{project_name}-api-service'},
                {'Name': 'ClusterName', 'Value': f'{project_name}-cluster'}
            ],
            start_time=start_time,
            end_time=end_time,
            statistic='Average'
        )
        metrics['ecs_cpu_utilization'] = ecs_cpu
        
        # ECS memory utilization
        ecs_memory = get_metric_statistics(
            namespace='AWS/ECS',
            metric_name='MemoryUtilization',
            dimensions=[
                {'Name': 'ServiceName', 'Value': f'{project_name}-api-service'},
                {'Name': 'ClusterName', 'Value': f'{project_name}-cluster'}
            ],
            start_time=start_time,
            end_time=end_time,
            statistic='Average'
        )
        metrics['ecs_memory_utilization'] = ecs_memory
        
        # RDS CPU utilization
        rds_cpu = get_metric_statistics(
            namespace='AWS/RDS',
            metric_name='CPUUtilization',
            dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': f'{project_name}-database'}],
            start_time=start_time,
            end_time=end_time,
            statistic='Average'
        )
        metrics['rds_cpu_utilization'] = rds_cpu
        
        # RDS database connections
        rds_connections = get_metric_statistics(
            namespace='AWS/RDS',
            metric_name='DatabaseConnections',
            dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': f'{project_name}-database'}],
            start_time=start_time,
            end_time=end_time,
            statistic='Average'
        )
        metrics['rds_connections'] = rds_connections
        
    except Exception as e:
        print(f"Error collecting infrastructure metrics: {str(e)}")
    
    return metrics

def collect_application_metrics(start_time: datetime, end_time: datetime, project_name: str) -> Dict[str, Any]:
    """Collect application-related metrics"""
    metrics = {}
    
    try:
        # ALB request count
        request_count = get_metric_statistics(
            namespace='AWS/ApplicationELB',
            metric_name='RequestCount',
            dimensions=[{'Name': 'LoadBalancer', 'Value': f'{project_name}-alb'}],
            start_time=start_time,
            end_time=end_time,
            statistic='Sum'
        )
        metrics['request_count'] = request_count
        
        # HTTP 2xx responses
        http_2xx = get_metric_statistics(
            namespace='AWS/ApplicationELB',
            metric_name='HTTPCode_Target_2XX_Count',
            dimensions=[{'Name': 'LoadBalancer', 'Value': f'{project_name}-alb'}],
            start_time=start_time,
            end_time=end_time,
            statistic='Sum'
        )
        metrics['http_2xx_count'] = http_2xx
        
        # HTTP 4xx responses
        http_4xx = get_metric_statistics(
            namespace='AWS/ApplicationELB',
            metric_name='HTTPCode_Target_4XX_Count',
            dimensions=[{'Name': 'LoadBalancer', 'Value': f'{project_name}-alb'}],
            start_time=start_time,
            end_time=end_time,
            statistic='Sum'
        )
        metrics['http_4xx_count'] = http_4xx
        
        # HTTP 5xx responses
        http_5xx = get_metric_statistics(
            namespace='AWS/ApplicationELB',
            metric_name='HTTPCode_Target_5XX_Count',
            dimensions=[{'Name': 'LoadBalancer', 'Value': f'{project_name}-alb'}],
            start_time=start_time,
            end_time=end_time,
            statistic='Sum'
        )
        metrics['http_5xx_count'] = http_5xx
        
        # Calculate error rate
        if request_count and request_count > 0:
            error_count = (http_4xx or 0) + (http_5xx or 0)
            metrics['error_rate'] = (error_count / request_count) * 100
        
    except Exception as e:
        print(f"Error collecting application metrics: {str(e)}")
    
    return metrics

def collect_tenant_metrics(start_time: datetime, end_time: datetime, project_name: str) -> Dict[str, Any]:
    """Collect multi-tenant specific metrics"""
    metrics = {}
    
    try:
        # Tenant request count
        tenant_requests = get_metric_statistics(
            namespace='Seiketsu/MultiTenant',
            metric_name='TenantRequests',
            start_time=start_time,
            end_time=end_time,
            statistic='Sum'
        )
        metrics['tenant_requests'] = tenant_requests
        
    except Exception as e:
        print(f"Error collecting tenant metrics: {str(e)}")
    
    return metrics

def get_metric_statistics(namespace: str, metric_name: str, start_time: datetime, 
                         end_time: datetime, statistic: str, dimensions: List[Dict] = None) -> float:
    """Get metric statistics from CloudWatch"""
    try:
        params = {
            'Namespace': namespace,
            'MetricName': metric_name,
            'StartTime': start_time,
            'EndTime': end_time,
            'Period': 300,
            'Statistics': [statistic]
        }
        
        if dimensions:
            params['Dimensions'] = dimensions
        
        response = cloudwatch.get_metric_statistics(**params)
        
        if response['Datapoints']:
            # Return the most recent datapoint
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            return datapoints[-1][statistic]
        
        return None
        
    except Exception as e:
        print(f"Error getting metric {metric_name}: {str(e)}")
        return None

def forward_metrics(endpoint: str, api_key: str, metrics_data: Dict[str, Any]) -> requests.Response:
    """Forward metrics to 21dev.ai monitoring platform"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'Seiketsu-AI-Metrics-Forwarder/1.0'
    }
    
    response = requests.post(
        endpoint,
        json=metrics_data,
        headers=headers,
        timeout=30
    )
    
    response.raise_for_status()
    return response