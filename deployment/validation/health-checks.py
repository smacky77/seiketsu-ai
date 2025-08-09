#!/usr/bin/env python3
"""
Seiketsu AI Health Check System
Comprehensive health monitoring and validation for production deployments
"""

import asyncio
import aiohttp
import logging
import time
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import psycopg2
import redis
import subprocess
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

@dataclass
class HealthCheckResult:
    name: str
    status: HealthStatus
    response_time: float
    message: str
    timestamp: datetime
    metadata: Dict = None

class HealthChecker:
    def __init__(self, config: Dict = None):
        self.config = config or self._load_config()
        self.session = None
        
    def _load_config(self) -> Dict:
        """Load configuration from environment and defaults"""
        return {
            'api_base_url': os.getenv('API_BASE_URL', 'https://api.seiketsu-ai.com'),
            'web_base_url': os.getenv('WEB_BASE_URL', 'https://seiketsu-ai.com'),
            'database_url': os.getenv('DATABASE_URL'),
            'redis_url': os.getenv('REDIS_URL'),
            'elevenlabs_api_key': os.getenv('ELEVENLABS_API_KEY'),
            'timeout': int(os.getenv('HEALTH_CHECK_TIMEOUT', '30')),
            'max_concurrent': int(os.getenv('MAX_CONCURRENT_CHECKS', '10')),
            'thresholds': {
                'api_response_time': float(os.getenv('API_RESPONSE_THRESHOLD', '0.5')),
                'voice_response_time': float(os.getenv('VOICE_RESPONSE_THRESHOLD', '2.0')),
                'database_query_time': float(os.getenv('DB_QUERY_THRESHOLD', '0.1')),
                'cache_response_time': float(os.getenv('CACHE_RESPONSE_THRESHOLD', '0.05'))
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=self.config['max_concurrent'])
        timeout = aiohttp.ClientTimeout(total=self.config['timeout'])
        self.session = aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def check_api_health(self) -> HealthCheckResult:
        """Check API service health and performance"""
        start_time = time.time()
        
        try:
            async with self.session.get(f"{self.config['api_base_url']}/health") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check response time threshold
                    if response_time > self.config['thresholds']['api_response_time']:
                        status = HealthStatus.DEGRADED
                        message = f"API responding but slow: {response_time:.3f}s"
                    else:
                        status = HealthStatus.HEALTHY
                        message = f"API healthy: {response_time:.3f}s"
                    
                    return HealthCheckResult(
                        name="api_health",
                        status=status,
                        response_time=response_time,
                        message=message,
                        timestamp=datetime.utcnow(),
                        metadata=data
                    )
                else:
                    return HealthCheckResult(
                        name="api_health",
                        status=HealthStatus.UNHEALTHY,
                        response_time=response_time,
                        message=f"API returned {response.status}",
                        timestamp=datetime.utcnow()
                    )
        
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                name="api_health",
                status=HealthStatus.CRITICAL,
                response_time=response_time,
                message=f"API check failed: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def check_voice_service(self) -> HealthCheckResult:
        """Check voice service integration and latency"""
        start_time = time.time()
        
        try:
            test_payload = {
                "text": "Hello, this is a test message for voice synthesis.",
                "voice_id": "test_voice",
                "model_id": "eleven_monolingual_v1"
            }
            
            async with self.session.post(
                f"{self.config['api_base_url']}/voice/synthesize",
                json=test_payload,
                headers={"Authorization": f"Bearer {self.config.get('api_token', '')}"}
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    # Check voice response time threshold
                    if response_time > self.config['thresholds']['voice_response_time']:
                        status = HealthStatus.DEGRADED
                        message = f"Voice service slow: {response_time:.3f}s"
                    else:
                        status = HealthStatus.HEALTHY
                        message = f"Voice service healthy: {response_time:.3f}s"
                    
                    return HealthCheckResult(
                        name="voice_service",
                        status=status,
                        response_time=response_time,
                        message=message,
                        timestamp=datetime.utcnow(),
                        metadata={"content_length": response.headers.get('Content-Length', 0)}
                    )
                else:
                    return HealthCheckResult(
                        name="voice_service",
                        status=HealthStatus.UNHEALTHY,
                        response_time=response_time,
                        message=f"Voice service returned {response.status}",
                        timestamp=datetime.utcnow()
                    )
        
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                name="voice_service",
                status=HealthStatus.CRITICAL,
                response_time=response_time,
                message=f"Voice service check failed: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test database connection and simple query
            conn = psycopg2.connect(self.config['database_url'])
            cursor = conn.cursor()
            
            # Simple performance test query
            cursor.execute("SELECT 1, NOW(), COUNT(*) FROM pg_stat_activity;")
            result = cursor.fetchone()
            
            response_time = time.time() - start_time
            
            cursor.close()
            conn.close()
            
            if response_time > self.config['thresholds']['database_query_time']:
                status = HealthStatus.DEGRADED
                message = f"Database slow: {response_time:.3f}s"
            else:
                status = HealthStatus.HEALTHY
                message = f"Database healthy: {response_time:.3f}s"
            
            return HealthCheckResult(
                name="database",
                status=status,
                response_time=response_time,
                message=message,
                timestamp=datetime.utcnow(),
                metadata={"active_connections": result[2] if result else 0}
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                name="database",
                status=HealthStatus.CRITICAL,
                response_time=response_time,
                message=f"Database check failed: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def check_redis_cache(self) -> HealthCheckResult:
        """Check Redis cache connectivity and performance"""
        start_time = time.time()
        
        try:
            r = redis.from_url(self.config['redis_url'])
            
            # Test basic operations
            test_key = f"health_check_{int(time.time())}"
            r.set(test_key, "test_value", ex=60)  # Expire in 60 seconds
            value = r.get(test_key)
            r.delete(test_key)
            
            response_time = time.time() - start_time
            
            if value == b"test_value":
                if response_time > self.config['thresholds']['cache_response_time']:
                    status = HealthStatus.DEGRADED
                    message = f"Redis slow: {response_time:.3f}s"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Redis healthy: {response_time:.3f}s"
                
                info = r.info()
                return HealthCheckResult(
                    name="redis_cache",
                    status=status,
                    response_time=response_time,
                    message=message,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "memory_usage": info.get('used_memory_human', 'unknown'),
                        "connected_clients": info.get('connected_clients', 0)
                    }
                )
            else:
                return HealthCheckResult(
                    name="redis_cache",
                    status=HealthStatus.UNHEALTHY,
                    response_time=response_time,
                    message="Redis operation failed",
                    timestamp=datetime.utcnow()
                )
        
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                name="redis_cache",
                status=HealthStatus.CRITICAL,
                response_time=response_time,
                message=f"Redis check failed: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def check_web_frontend(self) -> HealthCheckResult:
        """Check web frontend availability and basic functionality"""
        start_time = time.time()
        
        try:
            async with self.session.get(self.config['web_base_url']) as response:
                response_time = time.time() - start_time
                content = await response.text()
                
                if response.status == 200 and "Seiketsu AI" in content:
                    status = HealthStatus.HEALTHY
                    message = f"Frontend healthy: {response_time:.3f}s"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = f"Frontend issues: status {response.status}"
                
                return HealthCheckResult(
                    name="web_frontend",
                    status=status,
                    response_time=response_time,
                    message=message,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "status_code": response.status,
                        "content_length": len(content)
                    }
                )
        
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                name="web_frontend",
                status=HealthStatus.CRITICAL,
                response_time=response_time,
                message=f"Frontend check failed: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def check_multi_tenant_isolation(self) -> HealthCheckResult:
        """Test multi-tenant data isolation"""
        start_time = time.time()
        
        try:
            # Create test tenants and verify isolation
            test_payload = {
                "action": "test_isolation",
                "tenant_count": 3
            }
            
            async with self.session.post(
                f"{self.config['api_base_url']}/admin/test-tenant-isolation",
                json=test_payload,
                headers={"Authorization": f"Bearer {self.config.get('admin_token', '')}"}
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get('isolation_passed', False):
                        status = HealthStatus.HEALTHY
                        message = f"Tenant isolation verified: {response_time:.3f}s"
                    else:
                        status = HealthStatus.CRITICAL
                        message = f"Tenant isolation FAILED: {result.get('error', 'Unknown error')}"
                    
                    return HealthCheckResult(
                        name="multi_tenant_isolation",
                        status=status,
                        response_time=response_time,
                        message=message,
                        timestamp=datetime.utcnow(),
                        metadata=result
                    )
                else:
                    return HealthCheckResult(
                        name="multi_tenant_isolation",
                        status=HealthStatus.UNHEALTHY,
                        response_time=response_time,
                        message=f"Isolation test failed with status {response.status}",
                        timestamp=datetime.utcnow()
                    )
        
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                name="multi_tenant_isolation",
                status=HealthStatus.CRITICAL,
                response_time=response_time,
                message=f"Isolation test error: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def check_external_services(self) -> HealthCheckResult:
        """Check external service dependencies"""
        start_time = time.time()
        
        try:
            # Test ElevenLabs API connectivity
            headers = {"xi-api-key": self.config['elevenlabs_api_key']}
            
            async with self.session.get(
                "https://api.elevenlabs.io/v1/user",
                headers=headers
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    user_data = await response.json()
                    status = HealthStatus.HEALTHY
                    message = f"External services healthy: {response_time:.3f}s"
                    metadata = {
                        "elevenlabs_quota": user_data.get('subscription', {}).get('character_limit', 'unknown')
                    }
                else:
                    status = HealthStatus.DEGRADED
                    message = f"ElevenLabs API issues: {response.status}"
                    metadata = None
                
                return HealthCheckResult(
                    name="external_services",
                    status=status,
                    response_time=response_time,
                    message=message,
                    timestamp=datetime.utcnow(),
                    metadata=metadata
                )
        
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                name="external_services",
                status=HealthStatus.DEGRADED,
                response_time=response_time,
                message=f"External service check failed: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks concurrently"""
        logger.info("Starting comprehensive health checks...")
        
        checks = [
            self.check_api_health(),
            self.check_voice_service(),
            self.check_database(),
            self.check_redis_cache(),
            self.check_web_frontend(),
            self.check_multi_tenant_isolation(),
            self.check_external_services()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Handle exceptions in results
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                health_results.append(HealthCheckResult(
                    name=f"check_{i}",
                    status=HealthStatus.CRITICAL,
                    response_time=0.0,
                    message=f"Health check exception: {str(result)}",
                    timestamp=datetime.utcnow()
                ))
            else:
                health_results.append(result)
        
        return health_results

    def generate_report(self, results: List[HealthCheckResult]) -> Dict:
        """Generate comprehensive health report"""
        total_checks = len(results)
        healthy_checks = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        degraded_checks = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        unhealthy_checks = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        critical_checks = sum(1 for r in results if r.status == HealthStatus.CRITICAL)
        
        # Determine overall system health
        if critical_checks > 0:
            overall_status = HealthStatus.CRITICAL
        elif unhealthy_checks > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_checks > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status.value,
            "summary": {
                "total_checks": total_checks,
                "healthy": healthy_checks,
                "degraded": degraded_checks,
                "unhealthy": unhealthy_checks,
                "critical": critical_checks,
                "health_percentage": (healthy_checks / total_checks) * 100 if total_checks > 0 else 0
            },
            "checks": [asdict(result) for result in results],
            "recommendations": self._generate_recommendations(results)
        }
    
    def _generate_recommendations(self, results: List[HealthCheckResult]) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        for result in results:
            if result.status == HealthStatus.CRITICAL:
                recommendations.append(f"URGENT: {result.name} is critical - {result.message}")
            elif result.status == HealthStatus.UNHEALTHY:
                recommendations.append(f"ATTENTION: {result.name} needs immediate attention - {result.message}")
            elif result.status == HealthStatus.DEGRADED:
                recommendations.append(f"WARNING: {result.name} performance degraded - {result.message}")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("All systems are healthy and operating within normal parameters")
        
        return recommendations

async def main():
    """Main health check execution"""
    try:
        async with HealthChecker() as checker:
            results = await checker.run_all_checks()
            report = checker.generate_report(results)
            
            # Output results
            print(json.dumps(report, indent=2, default=str))
            
            # Determine exit code based on overall health
            if report["overall_status"] in ["critical", "unhealthy"]:
                exit(1)
            elif report["overall_status"] == "degraded":
                exit(2)
            else:
                exit(0)
                
    except Exception as e:
        logger.error(f"Health check execution failed: {str(e)}")
        print(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "critical",
            "error": str(e)
        }, indent=2))
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())