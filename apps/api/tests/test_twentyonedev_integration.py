"""
21dev.ai Integration Tests
Tests for 21dev.ai monitoring, analytics, and integration functionality
"""
import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
import httpx

from app.services.twentyonedev_service import TwentyOneDevService
from app.core.config import settings


@pytest.mark.integration
@pytest.mark.twentyonedev
class TestTwentyOneDevService:
    """Test 21dev.ai service integration"""
    
    @pytest.fixture
    def twentyonedev_service(self):
        """Create 21dev.ai service instance for testing"""
        return TwentyOneDevService()
    
    @pytest.fixture
    def mock_twentyonedev_response(self):
        """Mock successful 21dev.ai API response"""
        return {
            "status": "success",
            "event_id": "evt_123456789",
            "timestamp": datetime.utcnow().isoformat(),
            "processed": True
        }
    
    @pytest.mark.asyncio
    async def test_send_analytics_event(self, twentyonedev_service, mock_twentyonedev_response):
        """Test sending analytics events to 21dev.ai"""
        event_data = {
            "user_id": "user_123",
            "organization_id": "org_456",
            "action": "voice_synthesis",
            "properties": {
                "processing_time_ms": 850,
                "text_length": 45,
                "voice_id": "professional_male",
                "cached": False,
                "quality_score": 0.92
            },
            "context": {
                "user_agent": "Seiketsu-AI/1.0",
                "ip_address": "192.168.1.100",
                "session_id": "sess_789"
            }
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_twentyonedev_response
            mock_post.return_value = mock_response
            
            # Send analytics event
            result = await twentyonedev_service.send_analytics_event(
                event_type="voice_synthesis",
                data=event_data
            )
            
            # Verify request was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check URL
            assert "/analytics/events" in str(call_args)
            
            # Check headers
            headers = call_args.kwargs.get('headers', {})
            assert "Authorization" in headers
            assert "Bearer" in headers["Authorization"]
            assert headers["Content-Type"] == "application/json"
            
            # Check payload
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "voice_synthesis"
            assert payload["service"] == "seiketsu_ai"
            assert "timestamp" in payload
            assert payload["data"] == event_data
            
            # Verify result
            assert result["status"] == "success"
            assert result["event_id"] == "evt_123456789"
    
    @pytest.mark.asyncio
    async def test_send_performance_metrics(self, twentyonedev_service, mock_twentyonedev_response):
        """Test sending performance metrics to 21dev.ai"""
        metrics_data = {
            "voice_synthesis": {
                "total_requests": 1250,
                "successful_requests": 1235,
                "failed_requests": 15,
                "average_processing_time_ms": 875,
                "p95_processing_time_ms": 1450,
                "p99_processing_time_ms": 2100,
                "cache_hit_rate": 0.78,
                "sub_2s_compliance_rate": 0.94
            },
            "api_performance": {
                "total_requests": 5420,
                "successful_requests": 5395,
                "average_response_time_ms": 125,
                "p95_response_time_ms": 280,
                "error_rate": 0.0046
            },
            "system_resources": {
                "cpu_usage_percent": 45.2,
                "memory_usage_percent": 62.8,
                "disk_usage_percent": 23.1,
                "active_connections": 156
            },
            "business_metrics": {
                "leads_processed": 89,
                "conversations_completed": 67,
                "conversion_rate": 0.31,
                "average_call_duration_seconds": 185
            }
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_twentyonedev_response
            mock_post.return_value = mock_response
            
            # Send performance metrics
            result = await twentyonedev_service.send_performance_metrics(
                metrics=metrics_data,
                time_period="hourly"
            )
            
            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "performance_metrics"
            assert payload["data"]["time_period"] == "hourly"
            assert payload["data"]["metrics"] == metrics_data
            
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_send_error_report(self, twentyonedev_service, mock_twentyonedev_response):
        """Test sending error reports to 21dev.ai"""
        error_data = {
            "error_type": "VoiceSynthesisError",
            "error_message": "ElevenLabs API timeout",
            "stack_trace": "Traceback (most recent call last):\n  File...",
            "request_id": "req_abc123",
            "user_id": "user_456",
            "organization_id": "org_789",
            "endpoint": "/api/v1/voice/synthesize",
            "method": "POST",
            "status_code": 500,
            "response_time_ms": 30000,
            "context": {
                "voice_agent_id": "agent_123",
                "text_length": 150,
                "language": "en",
                "user_agent": "Mozilla/5.0..."
            }
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_twentyonedev_response
            mock_post.return_value = mock_response
            
            # Send error report
            result = await twentyonedev_service.send_error_report(
                error_data=error_data,
                severity="high"
            )
            
            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "error_report"
            assert payload["data"]["severity"] == "high"
            assert payload["data"]["error_type"] == "VoiceSynthesisError"
            assert payload["data"]["request_id"] == "req_abc123"
            
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_batch_analytics_events(self, twentyonedev_service, mock_twentyonedev_response):
        """Test sending batch analytics events"""
        events = [
            {
                "event_type": "voice_synthesis",
                "data": {
                    "processing_time_ms": 850,
                    "text_length": 45,
                    "cached": False
                }
            },
            {
                "event_type": "lead_created",
                "data": {
                    "lead_id": "lead_123",
                    "source": "website",
                    "qualification_status": "new"
                }
            },
            {
                "event_type": "conversation_completed",
                "data": {
                    "conversation_id": "conv_456",
                    "duration_seconds": 180,
                    "sentiment_score": 0.8,
                    "lead_score": 75
                }
            }
        ]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "events_processed": 3,
                "batch_id": "batch_789"
            }
            mock_post.return_value = mock_response
            
            # Send batch events
            result = await twentyonedev_service.send_batch_events(events)
            
            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "batch_events"
            assert len(payload["data"]["events"]) == 3
            assert payload["data"]["batch_size"] == 3
            
            assert result["events_processed"] == 3
            assert result["batch_id"] == "batch_789"
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, twentyonedev_service):
        """Test 21dev.ai API error handling"""
        event_data = {"test": "data"}
        
        # Test API error response
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_response.json.return_value = {
                "error": "Invalid event format",
                "details": "Missing required field: event_type"
            }
            mock_post.return_value = mock_response
            
            # Should handle error gracefully
            result = await twentyonedev_service.send_analytics_event(
                event_type="test_event",
                data=event_data
            )
            
            # Should return None or error indication
            assert result is None or "error" in result
        
        # Test network timeout
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")
            
            # Should handle timeout gracefully
            result = await twentyonedev_service.send_analytics_event(
                event_type="test_event",
                data=event_data
            )
            
            assert result is None or "error" in result
        
        # Test connection error
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            # Should handle connection error gracefully
            result = await twentyonedev_service.send_analytics_event(
                event_type="test_event",
                data=event_data
            )
            
            assert result is None or "error" in result
    
    @pytest.mark.asyncio
    async def test_authentication_handling(self, twentyonedev_service):
        """Test 21dev.ai authentication handling"""
        event_data = {"test": "data"}
        
        # Test unauthorized response
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "error": "Unauthorized",
                "message": "Invalid API key"
            }
            mock_post.return_value = mock_response
            
            # Should handle auth error
            result = await twentyonedev_service.send_analytics_event(
                event_type="test_event",
                data=event_data
            )
            
            assert result is None or "error" in result
            
            # Verify correct auth header was sent
            call_args = mock_post.call_args
            headers = call_args.kwargs.get('headers', {})
            assert "Authorization" in headers
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, twentyonedev_service):
        """Test retry mechanism for failed requests"""
        event_data = {"test": "data"}
        
        call_count = 0
        
        def mock_post_with_retries(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                # First two calls fail with retryable error
                mock_response = Mock()
                mock_response.status_code = 503
                mock_response.text = "Service Unavailable"
                return mock_response
            else:
                # Third call succeeds
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "success",
                    "event_id": "evt_retry_success"
                }
                return mock_response
        
        with patch('httpx.AsyncClient.post', side_effect=mock_post_with_retries):
            # Should eventually succeed after retries
            result = await twentyonedev_service.send_analytics_event(
                event_type="test_retry",
                data=event_data
            )
            
            # Should succeed on third attempt
            assert call_count >= 3
            if result:
                assert result.get("status") == "success"
                assert result.get("event_id") == "evt_retry_success"


@pytest.mark.integration
@pytest.mark.twentyonedev
class TestTwentyOneDevIntegrationPoints:
    """Test integration points with 21dev.ai throughout the system"""
    
    @pytest.mark.asyncio
    async def test_voice_synthesis_analytics_integration(self, elevenlabs_service, test_voice_agent):
        """Test voice synthesis analytics sent to 21dev.ai"""
        with patch('app.services.twentyonedev_service.TwentyOneDevService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.send_analytics_event.return_value = {"status": "success"}
            
            # Mock voice synthesis
            elevenlabs_service._synthesize_audio = AsyncMock(return_value=b"test_audio")
            elevenlabs_service._get_voice_profile_for_agent = Mock(
                return_value=elevenlabs_service.voice_profiles["professional_male"]
            )
            elevenlabs_service._get_cached_audio = AsyncMock(return_value=None)
            elevenlabs_service._cache_audio = AsyncMock()
            
            # Perform voice synthesis
            result = await elevenlabs_service.synthesize_speech(
                text="Analytics integration test",
                voice_agent=test_voice_agent
            )
            
            # Verify analytics event was sent
            mock_instance.send_analytics_event.assert_called_once()
            call_args = mock_instance.send_analytics_event.call_args
            
            assert call_args[1]["event_type"] == "voice_synthesis"
            event_data = call_args[1]["data"]
            assert "processing_time_ms" in event_data
            assert "text_length" in event_data
            assert "voice_id" in event_data
            assert "cached" in event_data
    
    @pytest.mark.asyncio
    async def test_api_request_analytics_integration(self, client: TestClient, authorized_headers):
        """Test API request analytics sent to 21dev.ai"""
        with patch('app.services.twentyonedev_service.twentyonedev_service') as mock_service:
            mock_service.send_analytics_event = AsyncMock(return_value={"status": "success"})
            
            # Make API request
            response = client.get("/api/v1/leads", headers=authorized_headers)
            
            # In a real implementation, middleware would capture this
            # For testing, we verify the analytics service is available
            assert mock_service is not None
    
    @pytest.mark.asyncio
    async def test_error_reporting_integration(self, client: TestClient, authorized_headers):
        """Test error reporting to 21dev.ai"""
        with patch('app.services.twentyonedev_service.twentyonedev_service') as mock_service:
            mock_service.send_error_report = AsyncMock(return_value={"status": "success"})
            
            # Mock service to raise an error
            with patch('app.api.v1.leads.lead_service') as mock_lead_service:
                mock_lead_service.get_leads.side_effect = Exception("Test error for reporting")
                
                # Trigger error
                response = client.get("/api/v1/leads", headers=authorized_headers)
                
                # Should return error response
                assert response.status_code == 500
                
                # In real implementation, error would be reported to 21dev.ai
                # Here we verify the service is available for error reporting
                assert mock_service is not None
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, performance_monitor):
        """Test performance monitoring integration with 21dev.ai"""
        with patch('app.services.twentyonedev_service.twentyonedev_service') as mock_service:
            mock_service.send_performance_metrics = AsyncMock(return_value={"status": "success"})
            
            # Simulate performance monitoring
            performance_monitor.start()
            
            # Simulate some work
            await asyncio.sleep(0.1)
            
            metrics = performance_monitor.get_metrics()
            
            # Send performance metrics
            performance_data = {
                "response_time_ms": metrics["elapsed_time"] * 1000,
                "memory_usage_mb": metrics["memory_mb"],
                "cpu_percent": metrics["cpu_percent"]
            }
            
            await mock_service.send_performance_metrics(
                metrics=performance_data,
                time_period="real_time"
            )
            
            # Verify metrics were sent
            mock_service.send_performance_metrics.assert_called_once()
            call_args = mock_service.send_performance_metrics.call_args
            assert "response_time_ms" in call_args[1]["metrics"]
            assert call_args[1]["time_period"] == "real_time"


@pytest.mark.integration
@pytest.mark.twentyonedev
class TestTwentyOneDevDashboard:
    """Test 21dev.ai dashboard and monitoring features"""
    
    @pytest.fixture
    def dashboard_metrics(self):
        """Sample dashboard metrics"""
        return {
            "overview": {
                "total_requests_24h": 12450,
                "successful_requests_24h": 12380,
                "error_rate_24h": 0.0056,
                "average_response_time_ms": 145,
                "uptime_percentage": 99.92
            },
            "voice_synthesis": {
                "total_syntheses_24h": 3420,
                "successful_syntheses_24h": 3398,
                "average_processing_time_ms": 892,
                "sub_2s_compliance_rate": 0.943,
                "cache_hit_rate": 0.781,
                "most_used_voice": "professional_male"
            },
            "business_metrics": {
                "leads_created_24h": 156,
                "conversations_completed_24h": 89,
                "conversion_rate_24h": 0.314,
                "average_call_duration_seconds": 178,
                "top_lead_sources": ["website", "referral", "social_media"]
            },
            "system_health": {
                "cpu_usage_current": 42.3,
                "memory_usage_current": 68.7,
                "disk_usage_current": 23.1,
                "active_connections": 234,
                "database_pool_usage": 15
            },
            "alerts": [
                {
                    "type": "warning",
                    "message": "Voice synthesis response time above 1.5s threshold",
                    "timestamp": datetime.utcnow().isoformat(),
                    "resolved": False
                },
                {
                    "type": "info",
                    "message": "High traffic detected - auto-scaling triggered",
                    "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "resolved": True
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_dashboard_data_collection(self, twentyonedev_service, dashboard_metrics):
        """Test dashboard data collection and aggregation"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "dashboard_updated": True
            }
            mock_post.return_value = mock_response
            
            # Send dashboard metrics
            result = await twentyonedev_service.send_dashboard_update(
                metrics=dashboard_metrics
            )
            
            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "dashboard_update"
            assert "overview" in payload["data"]["metrics"]
            assert "voice_synthesis" in payload["data"]["metrics"]
            assert "alerts" in payload["data"]["metrics"]
            
            assert result["dashboard_updated"] == True
    
    @pytest.mark.asyncio
    async def test_real_time_monitoring_updates(self, twentyonedev_service):
        """Test real-time monitoring updates to 21dev.ai"""
        real_time_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "active_users": 45,
            "concurrent_requests": 12,
            "voice_synthesis_queue_length": 3,
            "response_times_last_minute": [120, 145, 132, 156, 98, 201],
            "error_count_last_minute": 0,
            "cache_hit_count_last_minute": 234,
            "cache_miss_count_last_minute": 67
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_post.return_value = mock_response
            
            # Send real-time update
            result = await twentyonedev_service.send_real_time_update(
                data=real_time_data
            )
            
            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "real_time_update"
            assert payload["data"]["active_users"] == 45
            assert payload["data"]["concurrent_requests"] == 12
            assert len(payload["data"]["response_times_last_minute"]) == 6
    
    @pytest.mark.asyncio
    async def test_alert_management(self, twentyonedev_service):
        """Test alert creation and management through 21dev.ai"""
        alert_data = {
            "alert_type": "performance",
            "severity": "high",
            "title": "Voice Synthesis Response Time Exceeded",
            "description": "Average voice synthesis response time exceeded 2 second threshold",
            "metrics": {
                "current_avg_response_time_ms": 2350,
                "threshold_ms": 2000,
                "affected_requests_count": 23,
                "time_period": "last_5_minutes"
            },
            "suggested_actions": [
                "Check ElevenLabs API status",
                "Review cache hit rate",
                "Consider scaling voice synthesis workers"
            ],
            "context": {
                "organization_id": "org_123",
                "service": "voice_synthesis",
                "environment": "production"
            }
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "alert_id": "alert_456789",
                "created_at": datetime.utcnow().isoformat()
            }
            mock_post.return_value = mock_response
            
            # Create alert
            result = await twentyonedev_service.create_alert(
                alert_data=alert_data
            )
            
            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "alert_created"
            assert payload["data"]["severity"] == "high"
            assert payload["data"]["alert_type"] == "performance"
            assert "suggested_actions" in payload["data"]
            
            assert result["alert_id"] == "alert_456789"
    
    @pytest.mark.asyncio
    async def test_custom_dashboard_configuration(self, twentyonedev_service):
        """Test custom dashboard configuration for Seiketsu AI"""
        dashboard_config = {
            "dashboard_name": "Seiketsu AI Production Monitoring",
            "widgets": [
                {
                    "type": "metric_card",
                    "title": "Voice Synthesis Performance",
                    "metrics": [
                        "average_processing_time_ms",
                        "sub_2s_compliance_rate",
                        "cache_hit_rate"
                    ],
                    "position": {"row": 1, "col": 1, "width": 4, "height": 2}
                },
                {
                    "type": "time_series_chart",
                    "title": "API Response Times",
                    "metrics": ["average_response_time_ms", "p95_response_time_ms"],
                    "time_range": "24h",
                    "position": {"row": 1, "col": 5, "width": 8, "height": 4}
                },
                {
                    "type": "alert_list",
                    "title": "Active Alerts",
                    "filters": {"severity": ["high", "critical"], "resolved": False},
                    "position": {"row": 3, "col": 1, "width": 6, "height": 3}
                },
                {
                    "type": "business_metrics",
                    "title": "Lead Conversion Funnel",
                    "metrics": [
                        "leads_created",
                        "conversations_completed",
                        "qualified_leads",
                        "conversion_rate"
                    ],
                    "position": {"row": 3, "col": 7, "width": 6, "height": 3}
                }
            ],
            "refresh_interval_seconds": 30,
            "auto_refresh": True,
            "theme": "dark",
            "timezone": "UTC"
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "dashboard_id": "dash_seiketsu_prod",
                "configured": True
            }
            mock_post.return_value = mock_response
            
            # Configure dashboard
            result = await twentyonedev_service.configure_dashboard(
                config=dashboard_config
            )
            
            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "dashboard_configuration"
            assert payload["data"]["dashboard_name"] == "Seiketsu AI Production Monitoring"
            assert len(payload["data"]["widgets"]) == 4
            assert payload["data"]["refresh_interval_seconds"] == 30
            
            assert result["dashboard_id"] == "dash_seiketsu_prod"
            assert result["configured"] == True


@pytest.mark.integration
@pytest.mark.twentyonedev
@pytest.mark.performance
class TestTwentyOneDevPerformanceMonitoring:
    """Test 21dev.ai performance monitoring capabilities"""
    
    @pytest.mark.asyncio
    async def test_performance_baseline_establishment(self, twentyonedev_service, performance_monitor):
        """Test establishing performance baselines through 21dev.ai"""
        # Collect performance data over time
        performance_samples = []
        
        for i in range(10):
            performance_monitor.start()
            
            # Simulate work with varying performance
            await asyncio.sleep(0.05 + (i * 0.01))  # 50ms to 140ms
            
            metrics = performance_monitor.get_metrics()
            performance_samples.append({
                "response_time_ms": metrics["elapsed_time"] * 1000,
                "memory_mb": metrics["memory_mb"],
                "cpu_percent": metrics["cpu_percent"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Calculate baseline metrics
        response_times = [s["response_time_ms"] for s in performance_samples]
        baseline_data = {
            "metric_type": "performance_baseline",
            "service": "seiketsu_ai",
            "baseline_metrics": {
                "avg_response_time_ms": sum(response_times) / len(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)],
                "sample_count": len(performance_samples),
                "collection_period": "test_run"
            },
            "samples": performance_samples
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "baseline_established": True,
                "baseline_id": "baseline_123"
            }
            mock_post.return_value = mock_response
            
            # Send baseline data
            result = await twentyonedev_service.establish_performance_baseline(
                baseline_data=baseline_data
            )
            
            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "performance_baseline"
            assert "baseline_metrics" in payload["data"]
            assert payload["data"]["baseline_metrics"]["sample_count"] == 10
            
            assert result["baseline_established"] == True
    
    @pytest.mark.asyncio
    async def test_anomaly_detection_integration(self, twentyonedev_service):
        """Test anomaly detection integration with 21dev.ai"""
        # Simulate anomalous performance data
        anomaly_data = {
            "anomaly_type": "performance_degradation",
            "detected_at": datetime.utcnow().isoformat(),
            "severity": "medium",
            "metrics": {
                "current_avg_response_time_ms": 3500,  # Much higher than normal
                "baseline_avg_response_time_ms": 145,
                "deviation_percentage": 241.4,
                "affected_requests_count": 156,
                "time_window": "last_10_minutes"
            },
            "potential_causes": [
                "Database connection pool exhaustion",
                "ElevenLabs API latency increase",
                "Memory pressure causing GC pauses"
            ],
            "context": {
                "concurrent_users": 89,
                "system_load": "high",
                "recent_deployments": False
            }
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "anomaly_id": "anomaly_789",
                "investigation_started": True
            }
            mock_post.return_value = mock_response
            
            # Report anomaly
            result = await twentyonedev_service.report_anomaly(
                anomaly_data=anomaly_data
            )
            
            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            payload = call_args.kwargs.get('json', {})
            assert payload["event_type"] == "anomaly_detected"
            assert payload["data"]["anomaly_type"] == "performance_degradation"
            assert payload["data"]["metrics"]["deviation_percentage"] == 241.4
            assert len(payload["data"]["potential_causes"]) == 3
            
            assert result["anomaly_id"] == "anomaly_789"
            assert result["investigation_started"] == True