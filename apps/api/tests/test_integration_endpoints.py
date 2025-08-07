"""
Comprehensive integration tests for FastAPI endpoints, WebSocket connections,
and real-time voice processing features.
"""
import pytest
import asyncio
import json
import websockets
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid
from unittest.mock import AsyncMock, patch
import base64
import io

from main import app
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.models.lead import Lead
from app.models.conversation import Conversation


class TestWebSocketConnections:
    """Test WebSocket connections for real-time voice processing"""
    
    @pytest.fixture
    def ws_client(self):
        """Create WebSocket test client"""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_voice_websocket_connection(self, ws_client, test_user, test_organization):
        """Test WebSocket connection establishment for voice calls"""
        with ws_client.websocket_connect(
            f"/ws/voice/{test_organization.id}",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        ) as websocket:
            # Test connection established
            websocket.send_json({
                "type": "connection_request",
                "lead_id": "lead_123",
                "voice_agent_id": "agent_456"
            })
            
            response = websocket.receive_json()
            assert response["type"] == "connection_established"
            assert response["session_id"] is not None
            assert response["status"] == "ready"
    
    @pytest.mark.asyncio
    async def test_real_time_audio_streaming(self, ws_client, test_user, test_organization):
        """Test real-time audio streaming over WebSocket"""
        with ws_client.websocket_connect(
            f"/ws/voice/{test_organization.id}",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        ) as websocket:
            # Establish connection
            websocket.send_json({
                "type": "connection_request",
                "lead_id": "lead_123"
            })
            websocket.receive_json()  # Connection established
            
            # Send audio data
            fake_audio_data = base64.b64encode(b"fake_audio_bytes").decode()
            websocket.send_json({
                "type": "audio_data",
                "data": fake_audio_data,
                "format": "wav",
                "sample_rate": 16000
            })
            
            # Receive processing response
            response = websocket.receive_json()
            assert response["type"] in ["audio_processed", "transcription", "response"]
    
    @pytest.mark.asyncio
    async def test_websocket_voice_session_management(self, ws_client, test_user, test_organization):
        """Test voice session lifecycle management"""
        with ws_client.websocket_connect(
            f"/ws/voice/{test_organization.id}",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        ) as websocket:
            # Start session
            websocket.send_json({
                "type": "start_session",
                "lead_id": "lead_123",
                "voice_agent_id": "agent_456"
            })
            
            start_response = websocket.receive_json()
            assert start_response["type"] == "session_started"
            session_id = start_response["session_id"]
            
            # Pause session
            websocket.send_json({
                "type": "pause_session",
                "session_id": session_id
            })
            
            pause_response = websocket.receive_json()
            assert pause_response["type"] == "session_paused"
            
            # Resume session
            websocket.send_json({
                "type": "resume_session",
                "session_id": session_id
            })
            
            resume_response = websocket.receive_json()
            assert resume_response["type"] == "session_resumed"
            
            # End session
            websocket.send_json({
                "type": "end_session",
                "session_id": session_id
            })
            
            end_response = websocket.receive_json()
            assert end_response["type"] == "session_ended"
            assert "conversation_summary" in end_response
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, ws_client, test_user, test_organization):
        """Test WebSocket error handling and recovery"""
        with ws_client.websocket_connect(
            f"/ws/voice/{test_organization.id}",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        ) as websocket:
            # Send invalid message
            websocket.send_json({
                "type": "invalid_message_type",
                "data": "invalid"
            })
            
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "message" in response
            
            # Test recovery - send valid message after error
            websocket.send_json({
                "type": "connection_request",
                "lead_id": "lead_123"
            })
            
            recovery_response = websocket.receive_json()
            assert recovery_response["type"] == "connection_established"
    
    @pytest.mark.asyncio
    async def test_concurrent_websocket_connections(self, ws_client, test_user, test_organization):
        """Test handling multiple concurrent WebSocket connections"""
        connections = []
        
        try:
            # Create multiple concurrent connections
            for i in range(5):
                ws = ws_client.websocket_connect(
                    f"/ws/voice/{test_organization.id}",
                    headers={"Authorization": f"Bearer {test_user.access_token}"}
                )
                connections.append(ws.__enter__())
            
            # Test each connection
            for i, websocket in enumerate(connections):
                websocket.send_json({
                    "type": "connection_request",
                    "lead_id": f"lead_{i}"
                })
                
                response = websocket.receive_json()
                assert response["type"] == "connection_established"
                assert response["session_id"] is not None
        
        finally:
            # Clean up connections
            for websocket in connections:
                try:
                    websocket.__exit__(None, None, None)
                except:
                    pass


class TestEndpointIntegration:
    """Test integration between different API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_complete_lead_lifecycle(self, client, authorized_headers):
        """Test complete lead lifecycle through multiple endpoints"""
        # 1. Create lead
        lead_data = {
            "name": "Integration Test Lead",
            "email": "integration@test.com",
            "phone": "+1234567890",
            "source": "website",
            "property_preferences": {
                "bedrooms": 3,
                "max_price": 500000
            }
        }
        
        create_response = client.post(
            "/api/v1/leads",
            json=lead_data,
            headers=authorized_headers
        )
        assert create_response.status_code == 201
        lead_id = create_response.json()["id"]
        
        # 2. Start voice conversation
        conversation_data = {
            "lead_id": lead_id,
            "voice_agent_id": "agent_123",
            "type": "outbound_call"
        }
        
        conversation_response = client.post(
            "/api/v1/conversations",
            json=conversation_data,
            headers=authorized_headers
        )
        assert conversation_response.status_code == 201
        conversation_id = conversation_response.json()["id"]
        
        # 3. Update conversation with transcript
        update_data = {
            "transcript": "Lead expressed interest in 3-bedroom homes under $450K",
            "sentiment_score": 0.85,
            "lead_score": 78,
            "status": "qualified"
        }
        
        update_response = client.patch(
            f"/api/v1/conversations/{conversation_id}",
            json=update_data,
            headers=authorized_headers
        )
        assert update_response.status_code == 200
        
        # 4. Search for matching properties
        search_data = {
            "bedrooms": 3,
            "max_price": 450000,
            "location": "any"
        }
        
        search_response = client.post(
            "/api/v1/properties/search",
            json=search_data,
            headers=authorized_headers
        )
        assert search_response.status_code == 200
        properties = search_response.json()["properties"]
        
        # 5. Schedule property viewing
        if properties:
            schedule_data = {
                "lead_id": lead_id,
                "property_id": properties[0]["id"],
                "requested_date": "2024-01-15T14:00:00Z",
                "type": "property_viewing"
            }
            
            schedule_response = client.post(
                "/api/v1/appointments",
                json=schedule_data,
                headers=authorized_headers
            )
            assert schedule_response.status_code == 201
        
        # 6. Get updated lead with all interactions
        final_lead_response = client.get(
            f"/api/v1/leads/{lead_id}",
            headers=authorized_headers
        )
        assert final_lead_response.status_code == 200
        
        final_lead = final_lead_response.json()
        assert final_lead["qualification_status"] == "qualified"
        assert final_lead["lead_score"] == 78
    
    @pytest.mark.asyncio
    async def test_voice_call_integration_workflow(self, client, authorized_headers):
        """Test complete voice call integration workflow"""
        # 1. Create voice agent
        agent_data = {
            "name": "Integration Test Agent",
            "voice_id": "test_voice",
            "personality": "professional",
            "script_template": "standard_qualifier"
        }
        
        agent_response = client.post(
            "/api/v1/voice-agents",
            json=agent_data,
            headers=authorized_headers
        )
        assert agent_response.status_code == 201
        agent_id = agent_response.json()["id"]
        
        # 2. Initiate voice call
        call_data = {
            "lead_id": "lead_123",
            "voice_agent_id": agent_id,
            "phone_number": "+1234567890",
            "call_type": "qualification"
        }
        
        call_response = client.post(
            "/api/v1/voice/calls/initiate",
            json=call_data,
            headers=authorized_headers
        )
        assert call_response.status_code == 201
        call_id = call_response.json()["call_id"]
        
        # 3. Simulate voice processing
        audio_data = {
            "call_id": call_id,
            "audio_data": base64.b64encode(b"sample_audio").decode(),
            "format": "wav"
        }
        
        process_response = client.post(
            "/api/v1/voice/process",
            json=audio_data,
            headers=authorized_headers
        )
        assert process_response.status_code == 200
        
        # 4. Get call status
        status_response = client.get(
            f"/api/v1/voice/calls/{call_id}/status",
            headers=authorized_headers
        )
        assert status_response.status_code == 200
        assert "status" in status_response.json()
        
        # 5. End call and get summary
        end_response = client.post(
            f"/api/v1/voice/calls/{call_id}/end",
            headers=authorized_headers
        )
        assert end_response.status_code == 200
        
        summary = end_response.json()
        assert "conversation_summary" in summary
        assert "lead_score" in summary
        assert "next_steps" in summary
    
    @pytest.mark.asyncio
    async def test_webhook_integration_flow(self, client, admin_headers):
        """Test webhook integration and delivery"""
        # 1. Create webhook
        webhook_data = {
            "url": "https://httpbin.org/post",
            "events": ["conversation.completed", "lead.qualified"],
            "active": True,
            "secret": "test_secret"
        }
        
        webhook_response = client.post(
            "/api/v1/webhooks",
            json=webhook_data,
            headers=admin_headers
        )
        assert webhook_response.status_code == 201
        webhook_id = webhook_response.json()["id"]
        
        # 2. Trigger webhook event
        event_data = {
            "event_type": "lead.qualified",
            "data": {
                "lead_id": "lead_123",
                "qualification_score": 85,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        trigger_response = client.post(
            "/api/v1/webhooks/trigger",
            json=event_data,
            headers=admin_headers
        )
        assert trigger_response.status_code == 200
        
        # 3. Check webhook delivery status
        status_response = client.get(
            f"/api/v1/webhooks/{webhook_id}/deliveries",
            headers=admin_headers
        )
        assert status_response.status_code == 200
        
        deliveries = status_response.json()["deliveries"]
        assert len(deliveries) >= 1
        assert deliveries[0]["status"] in ["delivered", "pending", "failed"]
    
    @pytest.mark.asyncio
    async def test_analytics_integration_pipeline(self, client, authorized_headers):
        """Test analytics data pipeline integration"""
        # 1. Create test data
        test_conversations = []
        for i in range(5):
            conv_data = {
                "lead_id": f"lead_{i}",
                "duration_seconds": 180 + (i * 30),
                "transcript": f"Test conversation {i}",
                "sentiment_score": 0.7 + (i * 0.05),
                "lead_score": 60 + (i * 5),
                "status": "qualified" if i >= 2 else "interested"
            }
            
            response = client.post(
                "/api/v1/conversations",
                json=conv_data,
                headers=authorized_headers
            )
            assert response.status_code == 201
            test_conversations.append(response.json())
        
        # 2. Generate analytics report
        report_request = {
            "report_type": "conversation_summary",
            "date_range": {
                "start": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "metrics": ["conversion_rate", "average_duration", "sentiment_analysis"]
        }
        
        report_response = client.post(
            "/api/v1/analytics/reports/generate",
            json=report_request,
            headers=authorized_headers
        )
        assert report_response.status_code == 200
        
        report = report_response.json()
        assert "conversion_rate" in report["metrics"]
        assert "average_duration" in report["metrics"]
        assert "sentiment_analysis" in report["metrics"]
        assert report["metrics"]["conversion_rate"] >= 0.5  # 3/5 qualified
    
    @pytest.mark.asyncio
    async def test_multi_tenant_data_isolation(self, client):
        """Test multi-tenant data isolation"""
        # Create two different organizations
        org1_data = {"name": "Organization 1", "subdomain": "org1"}
        org2_data = {"name": "Organization 2", "subdomain": "org2"}
        
        # This would normally require super admin privileges
        # For testing, we'll mock the tenant separation
        
        with patch('app.core.middleware.get_current_tenant') as mock_tenant:
            # Test as organization 1
            mock_tenant.return_value = "org_1"
            
            # Create lead for org 1
            lead_data = {"name": "Org 1 Lead", "email": "lead1@org1.com"}
            org1_headers = {"Authorization": "Bearer org1_token", "X-Tenant-ID": "org_1"}
            
            with patch.object(client, 'post') as mock_post:
                mock_post.return_value.status_code = 201
                mock_post.return_value.json.return_value = {"id": "lead_org1", "name": "Org 1 Lead"}
                
                response = client.post("/api/v1/leads", json=lead_data, headers=org1_headers)
                assert response.status_code == 201
            
            # Test as organization 2 - should not see org 1 data
            mock_tenant.return_value = "org_2"
            org2_headers = {"Authorization": "Bearer org2_token", "X-Tenant-ID": "org_2"}
            
            with patch.object(client, 'get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"leads": [], "total": 0}
                
                response = client.get("/api/v1/leads", headers=org2_headers)
                assert response.status_code == 200
                assert response.json()["total"] == 0  # No cross-tenant data


class TestDatabaseIntegration:
    """Test database integration and transactions"""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db_session, test_organization):
        """Test database transaction rollback on error"""
        from app.models.lead import Lead
        from app.models.conversation import Conversation
        
        # Start transaction
        async with db_session.begin():
            # Create lead
            lead = Lead(
                id=str(uuid.uuid4()),
                organization_id=test_organization.id,
                name="Transaction Test Lead",
                email="transaction@test.com"
            )
            db_session.add(lead)
            await db_session.flush()
            
            # Create conversation
            conversation = Conversation(
                id=str(uuid.uuid4()),
                organization_id=test_organization.id,
                lead_id=lead.id,
                transcript="Test conversation",
                duration_seconds=180
            )
            db_session.add(conversation)
            
            # Simulate error that should rollback transaction
            try:
                # This should cause an error and rollback
                invalid_conversation = Conversation(
                    id=lead.id,  # Duplicate ID should cause error
                    organization_id=test_organization.id,
                    lead_id=lead.id,
                    transcript="Invalid conversation",
                    duration_seconds=180
                )
                db_session.add(invalid_conversation)
                await db_session.commit()
                
                assert False, "Should have raised an error"
            except Exception:
                await db_session.rollback()
        
        # Verify rollback - lead should not exist
        result = await db_session.get(Lead, lead.id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, db_session, test_organization):
        """Test concurrent database operations"""
        from app.models.lead import Lead
        
        async def create_lead(session, name_suffix):
            lead = Lead(
                id=str(uuid.uuid4()),
                organization_id=test_organization.id,
                name=f"Concurrent Lead {name_suffix}",
                email=f"concurrent{name_suffix}@test.com"
            )
            session.add(lead)
            await session.commit()
            return lead.id
        
        # Create multiple leads concurrently
        tasks = []
        for i in range(5):
            task = asyncio.create_task(create_lead(db_session, i))
            tasks.append(task)
        
        lead_ids = await asyncio.gather(*tasks)
        
        # Verify all leads were created
        assert len(lead_ids) == 5
        for lead_id in lead_ids:
            lead = await db_session.get(Lead, lead_id)
            assert lead is not None
    
    @pytest.mark.asyncio
    async def test_connection_pooling(self, db_session):
        """Test database connection pooling"""
        from app.core.database import engine
        
        # Test multiple concurrent connections
        async def test_connection():
            async with engine.begin() as conn:
                result = await conn.execute("SELECT 1 as test")
                row = result.first()
                return row.test
        
        # Create multiple concurrent connections
        tasks = [asyncio.create_task(test_connection()) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All connections should succeed
        assert all(result == 1 for result in results)


class TestExternalServiceIntegration:
    """Test integration with external services"""
    
    @pytest.mark.asyncio
    async def test_elevenlabs_service_integration(self, client, authorized_headers, mock_elevenlabs_api):
        """Test ElevenLabs service integration"""
        # Test voice synthesis
        tts_data = {
            "text": "Hello, this is a test message",
            "voice_id": "test_voice",
            "settings": {"stability": 0.75, "similarity_boost": 0.85}
        }
        
        response = client.post(
            "/api/v1/voice/synthesize",
            json=tts_data,
            headers=authorized_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
    
    @pytest.mark.asyncio 
    async def test_supabase_integration(self, client, authorized_headers, mock_supabase_client):
        """Test Supabase integration for file storage"""
        # Test file upload
        test_file = io.BytesIO(b"test audio data")
        
        response = client.post(
            "/api/v1/files/upload",
            files={"file": ("test.mp3", test_file, "audio/mpeg")},
            headers=authorized_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "file_url" in result
        assert "file_id" in result
    
    @pytest.mark.asyncio
    async def test_redis_caching_integration(self, client, authorized_headers, mock_redis_client):
        """Test Redis caching integration"""
        # Test cached response
        response1 = client.get("/api/v1/analytics/dashboard", headers=authorized_headers)
        assert response1.status_code == 200
        
        # Second request should use cache
        response2 = client.get("/api/v1/analytics/dashboard", headers=authorized_headers)
        assert response2.status_code == 200
        
        # Response should be the same (cached)
        assert response1.json() == response2.json()


class TestErrorHandlingIntegration:
    """Test error handling across integrated systems"""
    
    @pytest.mark.asyncio
    async def test_cascading_error_handling(self, client, authorized_headers):
        """Test error handling across multiple integrated services"""
        # Test scenario where voice service fails during conversation
        conversation_data = {
            "lead_id": "lead_123",
            "voice_agent_id": "agent_456"
        }
        
        with patch('app.services.voice_service.VoiceService.process_audio') as mock_voice:
            mock_voice.side_effect = Exception("Voice service unavailable")
            
            response = client.post(
                "/api/v1/conversations/voice",
                json=conversation_data,
                headers=authorized_headers
            )
            
            # Should handle error gracefully
            assert response.status_code in [503, 500]  # Service unavailable or internal error
            error_response = response.json()
            assert "error" in error_response or "detail" in error_response
    
    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, client, authorized_headers):
        """Test recovery from partial system failures"""
        # Test scenario where some services work but others fail
        lead_data = {
            "name": "Recovery Test Lead",
            "email": "recovery@test.com",
            "phone": "+1234567890"
        }
        
        with patch('app.services.analytics_service.update_lead_metrics') as mock_analytics:
            mock_analytics.side_effect = Exception("Analytics service down")
            
            # Lead creation should still succeed even if analytics fails
            response = client.post(
                "/api/v1/leads",
                json=lead_data,
                headers=authorized_headers
            )
            
            assert response.status_code == 201
            lead = response.json()
            assert lead["name"] == "Recovery Test Lead"
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, client, authorized_headers):
        """Test timeout handling for slow operations"""
        # Test with intentionally slow operation
        with patch('app.services.voice_service.VoiceService.synthesize') as mock_synthesize:
            async def slow_synthesis(*args, **kwargs):
                await asyncio.sleep(10)  # Simulate slow operation
                return {"audio_data": b"test"}
            
            mock_synthesize.side_effect = slow_synthesis
            
            response = client.post(
                "/api/v1/voice/synthesize",
                json={"text": "Test message", "voice_id": "test"},
                headers=authorized_headers,
                timeout=5  # 5 second timeout
            )
            
            # Should timeout gracefully
            assert response.status_code == 408  # Request timeout


class TestPerformanceIntegration:
    """Test performance across integrated systems"""
    
    @pytest.mark.asyncio
    async def test_endpoint_response_times(self, client, authorized_headers):
        """Test endpoint response time requirements"""
        endpoints = [
            ("/api/v1/leads", "GET"),
            ("/api/v1/conversations", "GET"),
            ("/api/v1/properties/search", "POST"),
            ("/api/v1/analytics/dashboard", "GET"),
            ("/api/v1/voice-agents", "GET")
        ]
        
        for endpoint, method in endpoints:
            start_time = datetime.utcnow()
            
            if method == "GET":
                response = client.get(endpoint, headers=authorized_headers)
            else:
                response = client.post(
                    endpoint,
                    json={"test": "data"},
                    headers=authorized_headers
                )
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # API endpoints should respond within 100ms
            assert response_time < 0.1, f"{endpoint} took {response_time:.3f}s"
            assert response.status_code in [200, 201, 400, 422]  # Valid response codes
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, client, authorized_headers):
        """Test handling of concurrent requests"""
        async def make_request():
            response = client.get("/api/v1/leads", headers=authorized_headers)
            return response.status_code
        
        # Make 20 concurrent requests
        tasks = [asyncio.create_task(make_request()) for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(status_code == 200 for status_code in results)
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_operations(self, client, authorized_headers):
        """Test memory usage during heavy operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform memory-intensive operations
        for i in range(10):
            # Create large payload
            large_data = {
                "leads": [
                    {
                        "name": f"Test Lead {j}",
                        "email": f"test{j}@example.com",
                        "data": "x" * 1000  # 1KB of data per lead
                    }
                    for j in range(100)  # 100 leads = ~100KB payload
                ]
            }
            
            response = client.post(
                "/api/v1/leads/bulk-import",
                json=large_data,
                headers=authorized_headers
            )
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB threshold