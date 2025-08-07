"""
Comprehensive API Endpoint Tests
Tests for all API endpoints including authentication, voice, leads, analytics, and multi-tenant functionality
"""
import pytest
import asyncio
import json
import time
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


@pytest.mark.api
class TestLeadsAPI:
    """Test leads management API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_lead(self, client: TestClient, authorized_headers, sample_lead_data):
        """Test lead creation endpoint"""
        response = client.post(
            "/api/v1/leads",
            json=sample_lead_data,
            headers=authorized_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == sample_lead_data["name"]
        assert result["email"] == sample_lead_data["email"]
        assert result["phone"] == sample_lead_data["phone"]
        assert result["qualification_status"] == "new"
        assert "id" in result
        assert "created_at" in result
    
    @pytest.mark.asyncio
    async def test_lead_validation(self, client: TestClient, authorized_headers):
        """Test lead data validation"""
        # Test invalid email
        invalid_lead = {
            "name": "Test Lead",
            "email": "invalid-email",
            "phone": "+1234567890"
        }
        
        response = client.post(
            "/api/v1/leads",
            json=invalid_lead,
            headers=authorized_headers
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert "email" in error_detail["loc"]
        
        # Test missing required fields
        incomplete_lead = {
            "name": "Test Lead"
            # Missing email and phone
        }
        
        response = client.post(
            "/api/v1/leads",
            json=incomplete_lead,
            headers=authorized_headers
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_lead_qualification_workflow(self, client: TestClient, authorized_headers, sample_lead_data):
        """Test lead qualification workflow"""
        # Create lead
        create_response = client.post(
            "/api/v1/leads",
            json=sample_lead_data,
            headers=authorized_headers
        )
        lead_id = create_response.json()["id"]
        
        # Update qualification status
        qualification_update = {
            "qualification_status": "qualified",
            "lead_score": 85,
            "notes": "Highly interested buyer with pre-approval",
            "qualification_data": {
                "budget_confirmed": True,
                "timeline": "immediate",
                "decision_maker": True,
                "financing_approved": True
            }
        }
        
        response = client.patch(
            f"/api/v1/leads/{lead_id}/qualification",
            json=qualification_update,
            headers=authorized_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["qualification_status"] == "qualified"
        assert result["lead_score"] == 85
        assert result["qualification_data"]["budget_confirmed"] == True
    
    @pytest.mark.asyncio
    async def test_lead_search_and_filtering(self, client: TestClient, authorized_headers, test_organization):
        """Test lead search and filtering functionality"""
        # Create multiple leads with different properties
        leads_data = [
            {
                "name": "John Buyer",
                "email": "john@example.com",
                "phone": "+1234567890",
                "qualification_status": "qualified",
                "property_preferences": {"type": "single_family", "min_price": 300000}
            },
            {
                "name": "Jane Renter",
                "email": "jane@example.com",
                "phone": "+1234567891",
                "qualification_status": "new",
                "property_preferences": {"type": "apartment", "max_price": 200000}
            },
            {
                "name": "Bob Investor",
                "email": "bob@example.com",
                "phone": "+1234567892",
                "qualification_status": "qualified",
                "property_preferences": {"type": "commercial", "min_price": 500000}
            }
        ]
        
        # Create leads
        for lead_data in leads_data:
            client.post("/api/v1/leads", json=lead_data, headers=authorized_headers)
        
        # Test filtering by qualification status
        response = client.get(
            "/api/v1/leads",
            headers=authorized_headers,
            params={"qualification_status": "qualified"}
        )
        
        assert response.status_code == 200
        results = response.json()["items"]
        assert len(results) >= 2  # Should include John and Bob
        assert all(lead["qualification_status"] == "qualified" for lead in results)
        
        # Test search by name
        response = client.get(
            "/api/v1/leads",
            headers=authorized_headers,
            params={"search": "John"}
        )
        
        assert response.status_code == 200
        results = response.json()["items"]
        assert len(results) >= 1
        assert any("John" in lead["name"] for lead in results)
        
        # Test property type filtering
        response = client.get(
            "/api/v1/leads",
            headers=authorized_headers,
            params={"property_type": "single_family"}
        )
        
        assert response.status_code == 200
        results = response.json()["items"]
        assert len(results) >= 1
    
    @pytest.mark.asyncio
    async def test_lead_export_functionality(self, client: TestClient, authorized_headers):
        """Test lead data export functionality"""
        response = client.get(
            "/api/v1/leads/export",
            headers=authorized_headers,
            params={
                "format": "csv",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]


@pytest.mark.api
class TestConversationsAPI:
    """Test conversations management API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, client: TestClient, authorized_headers, test_lead, test_user, sample_conversation_data):
        """Test conversation creation endpoint"""
        conversation_data = {
            **sample_conversation_data,
            "lead_id": test_lead.id,
            "agent_id": test_user.id
        }
        
        response = client.post(
            "/api/v1/conversations",
            json=conversation_data,
            headers=authorized_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["lead_id"] == test_lead.id
        assert result["agent_id"] == test_user.id
        assert result["duration_seconds"] == sample_conversation_data["duration_seconds"]
        assert result["sentiment_score"] == sample_conversation_data["sentiment_score"]
        assert "id" in result
    
    @pytest.mark.asyncio
    async def test_conversation_analytics(self, client: TestClient, authorized_headers, test_conversation):
        """Test conversation analytics endpoint"""
        response = client.get(
            f"/api/v1/conversations/{test_conversation.id}/analytics",
            headers=authorized_headers
        )
        
        assert response.status_code == 200
        analytics = response.json()
        assert "sentiment_analysis" in analytics
        assert "key_topics" in analytics
        assert "buying_signals" in analytics
        assert "next_steps" in analytics
        assert "quality_score" in analytics
    
    @pytest.mark.asyncio
    async def test_conversation_transcript_processing(self, client: TestClient, authorized_headers, test_conversation):
        """Test conversation transcript processing and AI insights"""
        response = client.post(
            f"/api/v1/conversations/{test_conversation.id}/process-transcript",
            headers=authorized_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "ai_insights" in result
        assert "sentiment_score" in result
        assert "key_entities" in result
        assert "action_items" in result
    
    @pytest.mark.asyncio
    async def test_conversation_recording_upload(self, client: TestClient, authorized_headers, test_conversation, temp_directory):
        """Test conversation recording upload"""
        # Create a mock audio file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(b"mock audio data")
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, "rb") as audio_file:
                response = client.post(
                    f"/api/v1/conversations/{test_conversation.id}/upload-recording",
                    files={"recording": ("test_recording.mp3", audio_file, "audio/mpeg")},
                    headers=authorized_headers
                )
            
            assert response.status_code == 200
            result = response.json()
            assert "recording_url" in result
            assert result["status"] == "uploaded"
            
        finally:
            os.unlink(temp_file_path)


@pytest.mark.api
class TestAnalyticsAPI:
    """Test analytics and reporting API endpoints"""
    
    @pytest.mark.asyncio
    async def test_agent_performance_analytics(self, client: TestClient, admin_headers, test_organization, test_user):
        """Test agent performance analytics"""
        response = client.get(
            "/api/v1/analytics/agent-performance",
            headers=admin_headers,
            params={
                "agent_id": test_user.id,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        )
        
        assert response.status_code == 200
        analytics = response.json()
        assert "total_conversations" in analytics
        assert "average_call_duration" in analytics
        assert "conversion_rate" in analytics
        assert "quality_score" in analytics
        assert "voice_synthesis_performance" in analytics
    
    @pytest.mark.asyncio
    async def test_organization_dashboard_metrics(self, client: TestClient, admin_headers, test_organization):
        """Test organization dashboard metrics"""
        response = client.get(
            "/api/v1/analytics/dashboard",
            headers=admin_headers,
            params={"period": "last_30_days"}
        )
        
        assert response.status_code == 200
        metrics = response.json()
        assert "total_leads" in metrics
        assert "qualified_leads" in metrics
        assert "conversion_rate" in metrics
        assert "average_response_time" in metrics
        assert "voice_synthesis_metrics" in metrics
        assert "active_agents" in metrics
    
    @pytest.mark.asyncio
    async def test_voice_performance_analytics(self, client: TestClient, admin_headers):
        """Test voice performance analytics"""
        response = client.get(
            "/api/v1/analytics/voice-performance",
            headers=admin_headers,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        )
        
        assert response.status_code == 200
        voice_analytics = response.json()
        assert "total_syntheses" in voice_analytics
        assert "average_processing_time_ms" in voice_analytics
        assert "cache_hit_rate" in voice_analytics
        assert "quality_scores" in voice_analytics
        assert "performance_by_voice_profile" in voice_analytics
        assert "sub_2s_compliance_rate" in voice_analytics
    
    @pytest.mark.asyncio
    async def test_real_time_metrics(self, client: TestClient, admin_headers):
        """Test real-time metrics endpoint"""
        response = client.get(
            "/api/v1/analytics/real-time",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        metrics = response.json()
        assert "active_conversations" in metrics
        assert "current_load" in metrics
        assert "system_health" in metrics
        assert "response_times" in metrics
        assert "timestamp" in metrics
    
    @pytest.mark.asyncio
    async def test_custom_report_generation(self, client: TestClient, admin_headers):
        """Test custom report generation"""
        report_config = {
            "name": "Custom Performance Report",
            "metrics": [
                "total_conversations",
                "conversion_rate",
                "voice_synthesis_performance",
                "lead_quality_scores"
            ],
            "filters": {
                "date_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                },
                "agent_ids": [],
                "qualification_status": ["qualified"]
            },
            "format": "json"
        }
        
        response = client.post(
            "/api/v1/analytics/custom-report",
            json=report_config,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        report = response.json()
        assert "report_id" in report
        assert "data" in report
        assert "generated_at" in report
        assert report["name"] == "Custom Performance Report"


@pytest.mark.api
class TestPropertiesAPI:
    """Test properties management API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_property(self, client: TestClient, authorized_headers, sample_property_data):
        """Test property creation endpoint"""
        response = client.post(
            "/api/v1/properties",
            json=sample_property_data,
            headers=authorized_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["mls_id"] == sample_property_data["mls_id"]
        assert result["address"] == sample_property_data["address"]
        assert result["price"] == sample_property_data["price"]
        assert result["listing_status"] == "active"
        assert "id" in result
    
    @pytest.mark.asyncio
    async def test_property_search(self, client: TestClient, authorized_headers):
        """Test property search functionality"""
        search_params = {
            "min_price": 300000,
            "max_price": 600000,
            "bedrooms": 3,
            "property_type": "single_family",
            "location": "downtown"
        }
        
        response = client.get(
            "/api/v1/properties/search",
            headers=authorized_headers,
            params=search_params
        )
        
        assert response.status_code == 200
        results = response.json()
        assert "items" in results
        assert "total" in results
        assert "page" in results
    
    @pytest.mark.asyncio
    async def test_property_recommendations(self, client: TestClient, authorized_headers, test_lead):
        """Test AI-powered property recommendations"""
        response = client.get(
            f"/api/v1/properties/recommendations/{test_lead.id}",
            headers=authorized_headers,
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        recommendations = response.json()
        assert "properties" in recommendations
        assert "match_scores" in recommendations
        assert "reasoning" in recommendations
        assert len(recommendations["properties"]) <= 10
    
    @pytest.mark.asyncio
    async def test_property_valuation(self, client: TestClient, authorized_headers, test_property):
        """Test property valuation endpoint"""
        response = client.post(
            f"/api/v1/properties/{test_property.id}/valuation",
            headers=authorized_headers
        )
        
        assert response.status_code == 200
        valuation = response.json()
        assert "estimated_value" in valuation
        assert "confidence_score" in valuation
        assert "comparable_properties" in valuation
        assert "market_trends" in valuation


@pytest.mark.api
class TestWebhooksAPI:
    """Test webhook management API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_webhook(self, client: TestClient, admin_headers):
        """Test webhook creation"""
        webhook_data = {
            "name": "Lead Notification Webhook",
            "url": "https://external-system.com/webhooks/leads",
            "events": ["lead.created", "lead.qualified", "conversation.completed"],
            "is_active": True,
            "secret": "webhook_secret_key"
        }
        
        response = client.post(
            "/api/v1/webhooks",
            json=webhook_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == webhook_data["name"]
        assert result["url"] == webhook_data["url"]
        assert result["events"] == webhook_data["events"]
        assert result["is_active"] == True
        assert "id" in result
    
    @pytest.mark.asyncio
    async def test_webhook_delivery_logs(self, client: TestClient, admin_headers):
        """Test webhook delivery logs"""
        # First create a webhook
        webhook_data = {
            "name": "Test Webhook",
            "url": "https://httpbin.org/post",
            "events": ["lead.created"],
            "is_active": True
        }
        
        create_response = client.post(
            "/api/v1/webhooks",
            json=webhook_data,
            headers=admin_headers
        )
        webhook_id = create_response.json()["id"]
        
        # Get delivery logs
        response = client.get(
            f"/api/v1/webhooks/{webhook_id}/deliveries",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        deliveries = response.json()
        assert "items" in deliveries
        assert "total" in deliveries
    
    @pytest.mark.asyncio
    async def test_webhook_retry_mechanism(self, client: TestClient, admin_headers):
        """Test webhook retry functionality"""
        # Create webhook with invalid URL to trigger retries
        webhook_data = {
            "name": "Retry Test Webhook",
            "url": "https://invalid-url-for-testing.com/webhook",
            "events": ["lead.created"],
            "is_active": True
        }
        
        create_response = client.post(
            "/api/v1/webhooks",
            json=webhook_data,
            headers=admin_headers
        )
        webhook_id = create_response.json()["id"]
        
        # Test manual retry
        response = client.post(
            f"/api/v1/webhooks/{webhook_id}/retry-failed",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "retried_count" in result


@pytest.mark.api
@pytest.mark.security
class TestMultiTenantSecurity:
    """Test multi-tenant security and data isolation"""
    
    @pytest.mark.asyncio
    async def test_tenant_data_isolation(self, client: TestClient, db_session):
        """Test that tenants cannot access each other's data"""
        # Create two organizations
        from app.models.organization import Organization
        from app.models.user import User
        from app.core.security import get_password_hash
        
        org1 = Organization(
            name="Org 1",
            subdomain="org1",
            settings={},
            subscription_status="active"
        )
        org2 = Organization(
            name="Org 2",
            subdomain="org2",
            settings={},
            subscription_status="active"
        )
        
        db_session.add_all([org1, org2])
        await db_session.commit()
        await db_session.refresh(org1)
        await db_session.refresh(org2)
        
        # Create users for each org
        user1 = User(
            email="user1@org1.com",
            hashed_password=get_password_hash("password123"),
            full_name="User One",
            organization_id=org1.id,
            role="admin",
            is_active=True
        )
        user2 = User(
            email="user2@org2.com",
            hashed_password=get_password_hash("password123"),
            full_name="User Two",
            organization_id=org2.id,
            role="admin",
            is_active=True
        )
        
        db_session.add_all([user1, user2])
        await db_session.commit()
        
        # Login as user1
        login_response1 = client.post("/api/v1/auth/login", json={
            "email": "user1@org1.com",
            "password": "password123"
        })
        token1 = login_response1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        # Login as user2
        login_response2 = client.post("/api/v1/auth/login", json={
            "email": "user2@org2.com",
            "password": "password123"
        })
        token2 = login_response2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create lead for org1
        lead_data = {
            "name": "Org1 Lead",
            "email": "lead@org1.com",
            "phone": "+1234567890"
        }
        
        create_response = client.post(
            "/api/v1/leads",
            json=lead_data,
            headers=headers1
        )
        lead_id = create_response.json()["id"]
        
        # User1 can access their lead
        response = client.get(f"/api/v1/leads/{lead_id}", headers=headers1)
        assert response.status_code == 200
        
        # User2 cannot access org1's lead
        response = client.get(f"/api/v1/leads/{lead_id}", headers=headers2)
        assert response.status_code == 404  # Should be not found due to tenant isolation
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting(self, client: TestClient, authorized_headers):
        """Test API rate limiting functionality"""
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(100):  # Exceed typical rate limit
            response = client.get("/api/v1/leads", headers=authorized_headers)
            responses.append(response.status_code)
            
            # If we hit rate limit, break
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        assert 429 in responses, "Rate limiting should be enforced"
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, client: TestClient, authorized_headers):
        """Test protection against SQL injection attacks"""
        # Attempt SQL injection in search parameter
        malicious_search = "'; DROP TABLE leads; --"
        
        response = client.get(
            "/api/v1/leads",
            headers=authorized_headers,
            params={"search": malicious_search}
        )
        
        # Should not cause server error and should be safely handled
        assert response.status_code in [200, 400]  # Either safely handled or rejected
        
        # Verify that the database is still functional
        normal_response = client.get("/api/v1/leads", headers=authorized_headers)
        assert normal_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_xss_protection(self, client: TestClient, authorized_headers):
        """Test protection against XSS attacks"""
        # Attempt to inject script in lead name
        xss_payload = {
            "name": "<script>alert('XSS')</script>",
            "email": "test@example.com",
            "phone": "+1234567890"
        }
        
        response = client.post(
            "/api/v1/leads",
            json=xss_payload,
            headers=authorized_headers
        )
        
        if response.status_code == 201:
            result = response.json()
            # Script tags should be escaped or removed
            assert "<script>" not in result["name"]
            assert "alert" not in result["name"]
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly configured"""
        response = client.options("/api/v1/leads")
        
        assert response.status_code == 200
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        assert "access-control-allow-headers" in headers


@pytest.mark.api
@pytest.mark.performance
class TestAPIPerformance:
    """Test API performance requirements"""
    
    @pytest.mark.asyncio
    async def test_api_response_times(self, client: TestClient, authorized_headers, performance_monitor):
        """Test that API endpoints meet response time requirements"""
        endpoints = [
            ("/api/v1/leads", "GET"),
            ("/api/v1/conversations", "GET"),
            ("/api/v1/properties/search", "GET"),
            ("/api/v1/analytics/dashboard", "GET"),
            ("/api/health", "GET")
        ]
        
        for endpoint, method in endpoints:
            performance_monitor.start()
            
            if method == "GET":
                response = client.get(endpoint, headers=authorized_headers)
            elif method == "POST":
                response = client.post(endpoint, json={}, headers=authorized_headers)
            
            metrics = performance_monitor.get_metrics()
            
            # API endpoints should respond within reasonable time
            assert metrics["elapsed_time"] < 5.0, f"{endpoint} took {metrics['elapsed_time']:.3f}s"
            assert response.status_code in [200, 201, 400, 401, 403, 422]  # Expected status codes
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, client: TestClient, authorized_headers):
        """Test handling of concurrent API requests"""
        import threading
        import time
        
        results = []
        start_time = time.time()
        
        def make_request():
            response = client.get("/api/v1/leads", headers=authorized_headers)
            results.append({
                "status_code": response.status_code,
                "response_time": time.time() - start_time
            })
        
        # Create 50 concurrent requests
        threads = []
        for _ in range(50):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests completed successfully
        assert len(results) == 50
        success_count = sum(1 for r in results if r["status_code"] == 200)
        assert success_count >= 45  # At least 90% success rate
        
        # Verify reasonable response times under load
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert avg_response_time < 10.0  # Average response time under load
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, client: TestClient, authorized_headers):
        """Test API performance with large datasets"""
        # Test pagination with large page sizes
        response = client.get(
            "/api/v1/leads",
            headers=authorized_headers,
            params={"page_size": 1000}  # Large page size
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result
        assert "page" in result
        
        # Test search with complex filters
        complex_search = {
            "search": "property buyer real estate",
            "qualification_status": "qualified",
            "min_lead_score": 50,
            "property_type": "single_family",
            "created_after": "2024-01-01"
        }
        
        response = client.get(
            "/api/v1/leads",
            headers=authorized_headers,
            params=complex_search
        )
        
        assert response.status_code == 200
        # Response should complete in reasonable time even with complex filtering