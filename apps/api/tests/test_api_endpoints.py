"""
Comprehensive tests for all Seiketsu AI API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json
from typing import Dict, Any

# Test data fixtures
@pytest.fixture
def test_user_data():
    return {
        "email": "agent@realestate.com",
        "password": "SecurePass123!",
        "full_name": "John Agent",
        "role": "agent",
        "organization_id": "org_123"
    }

@pytest.fixture
def test_organization_data():
    return {
        "name": "Premier Real Estate Agency",
        "subdomain": "premier",
        "settings": {
            "max_agents": 50,
            "voice_minutes": 10000,
            "features": ["voice_ai", "lead_scoring", "market_intelligence"]
        }
    }

@pytest.fixture
def test_conversation_data():
    return {
        "lead_id": "lead_456",
        "agent_id": "agent_123",
        "duration_seconds": 180,
        "transcript": "Hello, I'm interested in properties in downtown...",
        "sentiment_score": 0.85,
        "lead_score": 78,
        "status": "qualified"
    }

@pytest.fixture
def test_voice_agent_data():
    return {
        "name": "Sarah Professional",
        "voice_id": "eleven_labs_voice_123",
        "personality": "professional_friendly",
        "language": "en-US",
        "pitch": 1.0,
        "speed": 1.0,
        "script_template": "professional_qualifier"
    }

@pytest.fixture
def test_lead_data():
    return {
        "name": "Jane Prospect",
        "email": "jane@example.com",
        "phone": "+1234567890",
        "source": "website",
        "property_preferences": {
            "type": "single_family",
            "min_price": 300000,
            "max_price": 500000,
            "bedrooms": 3,
            "location": "downtown"
        },
        "qualification_status": "new"
    }

@pytest.fixture
def test_property_data():
    return {
        "mls_id": "MLS123456",
        "address": "123 Main St, Downtown",
        "price": 425000,
        "bedrooms": 3,
        "bathrooms": 2,
        "square_feet": 2200,
        "property_type": "single_family",
        "listing_status": "active"
    }


class TestHealthEndpoints:
    """Test health check and system status endpoints"""
    
    def test_health_check_basic(self, client: TestClient):
        """Test basic health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_check_detailed(self, client: TestClient):
        """Test detailed health check with component status"""
        response = client.get("/api/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert data["components"]["database"]["status"] == "healthy"
        assert data["components"]["cache"]["status"] == "healthy"
        assert data["components"]["voice_service"]["status"] == "healthy"
        assert "response_time_ms" in data["components"]["database"]


class TestAuthenticationEndpoints:
    """Test authentication and authorization endpoints"""
    
    def test_user_registration(self, client: TestClient, test_user_data):
        """Test user registration endpoint"""
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == test_user_data["email"]
        assert "password" not in data
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_user_login(self, client: TestClient, test_user_data):
        """Test user login endpoint"""
        # First register
        client.post("/api/auth/register", json=test_user_data)
        
        # Then login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_token_refresh(self, client: TestClient, test_user_data):
        """Test token refresh endpoint"""
        # Register and get tokens
        reg_response = client.post("/api/auth/register", json=test_user_data)
        refresh_token = reg_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post("/api/auth/refresh", 
                             json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_logout(self, client: TestClient, authorized_headers):
        """Test logout endpoint"""
        response = client.post("/api/auth/logout", headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
    
    def test_unauthorized_access(self, client: TestClient):
        """Test accessing protected endpoint without auth"""
        response = client.get("/api/users/profile")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"


class TestUserEndpoints:
    """Test user management endpoints"""
    
    def test_get_user_profile(self, client: TestClient, authorized_headers):
        """Test get user profile endpoint"""
        response = client.get("/api/users/profile", headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "role" in data
        assert "organization_id" in data
    
    def test_update_user_profile(self, client: TestClient, authorized_headers):
        """Test update user profile endpoint"""
        update_data = {
            "full_name": "John Updated Agent",
            "phone": "+1234567890",
            "timezone": "America/New_York"
        }
        response = client.put("/api/users/profile", 
                            json=update_data, 
                            headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["phone"] == update_data["phone"]
        assert data["timezone"] == update_data["timezone"]
    
    def test_change_password(self, client: TestClient, authorized_headers):
        """Test change password endpoint"""
        password_data = {
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass456!"
        }
        response = client.post("/api/users/change-password", 
                             json=password_data, 
                             headers=authorized_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"
    
    def test_list_organization_users(self, client: TestClient, admin_headers):
        """Test list users in organization (admin only)"""
        response = client.get("/api/users/organization", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data


class TestOrganizationEndpoints:
    """Test organization management endpoints"""
    
    def test_create_organization(self, client: TestClient, admin_headers, test_organization_data):
        """Test create organization endpoint (super admin only)"""
        response = client.post("/api/organizations", 
                             json=test_organization_data, 
                             headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_organization_data["name"]
        assert data["subdomain"] == test_organization_data["subdomain"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_organization(self, client: TestClient, authorized_headers):
        """Test get organization details endpoint"""
        response = client.get("/api/organizations/current", headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "settings" in data
        assert "subscription_status" in data
    
    def test_update_organization_settings(self, client: TestClient, admin_headers):
        """Test update organization settings (admin only)"""
        settings_update = {
            "settings": {
                "default_voice_agent": "sarah_professional",
                "lead_qualification_threshold": 75,
                "auto_schedule_appointments": True
            }
        }
        response = client.patch("/api/organizations/settings", 
                              json=settings_update, 
                              headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["default_voice_agent"] == "sarah_professional"


class TestConversationEndpoints:
    """Test conversation management endpoints"""
    
    def test_create_conversation(self, client: TestClient, authorized_headers, test_conversation_data):
        """Test create conversation endpoint"""
        response = client.post("/api/conversations", 
                             json=test_conversation_data, 
                             headers=authorized_headers)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["lead_id"] == test_conversation_data["lead_id"]
        assert data["duration_seconds"] == test_conversation_data["duration_seconds"]
        assert data["lead_score"] == test_conversation_data["lead_score"]
    
    def test_get_conversation(self, client: TestClient, authorized_headers):
        """Test get conversation by ID endpoint"""
        # Create conversation first
        conv_response = client.post("/api/conversations", 
                                  json=test_conversation_data, 
                                  headers=authorized_headers)
        conv_id = conv_response.json()["id"]
        
        # Get conversation
        response = client.get(f"/api/conversations/{conv_id}", headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv_id
        assert "transcript" in data
        assert "sentiment_score" in data
        assert "lead_score" in data
    
    def test_list_conversations(self, client: TestClient, authorized_headers):
        """Test list conversations with filters"""
        response = client.get("/api/conversations?status=qualified&limit=10", 
                            headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data
        assert "filters" in data
        assert data["filters"]["status"] == "qualified"
    
    def test_update_conversation_status(self, client: TestClient, authorized_headers):
        """Test update conversation status endpoint"""
        # Create conversation
        conv_response = client.post("/api/conversations", 
                                  json=test_conversation_data, 
                                  headers=authorized_headers)
        conv_id = conv_response.json()["id"]
        
        # Update status
        update_data = {"status": "appointment_scheduled"}
        response = client.patch(f"/api/conversations/{conv_id}/status", 
                              json=update_data, 
                              headers=authorized_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "appointment_scheduled"
    
    def test_get_conversation_analytics(self, client: TestClient, authorized_headers):
        """Test get conversation analytics endpoint"""
        response = client.get("/api/conversations/analytics/summary", 
                            headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "average_duration" in data
        assert "average_lead_score" in data
        assert "conversion_rate" in data
        assert "sentiment_distribution" in data


class TestVoiceAgentEndpoints:
    """Test voice agent management endpoints"""
    
    def test_create_voice_agent(self, client: TestClient, admin_headers, test_voice_agent_data):
        """Test create voice agent endpoint"""
        response = client.post("/api/voice-agents", 
                             json=test_voice_agent_data, 
                             headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_voice_agent_data["name"]
        assert data["voice_id"] == test_voice_agent_data["voice_id"]
        assert "id" in data
    
    def test_list_voice_agents(self, client: TestClient, authorized_headers):
        """Test list voice agents endpoint"""
        response = client.get("/api/voice-agents", headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
    
    def test_update_voice_agent(self, client: TestClient, admin_headers):
        """Test update voice agent endpoint"""
        # Create agent first
        agent_response = client.post("/api/voice-agents", 
                                   json=test_voice_agent_data, 
                                   headers=admin_headers)
        agent_id = agent_response.json()["id"]
        
        # Update agent
        update_data = {
            "personality": "professional_warm",
            "pitch": 1.1,
            "speed": 0.95
        }
        response = client.patch(f"/api/voice-agents/{agent_id}", 
                              json=update_data, 
                              headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["personality"] == update_data["personality"]
        assert data["pitch"] == update_data["pitch"]
    
    def test_delete_voice_agent(self, client: TestClient, admin_headers):
        """Test delete voice agent endpoint"""
        # Create agent
        agent_response = client.post("/api/voice-agents", 
                                   json=test_voice_agent_data, 
                                   headers=admin_headers)
        agent_id = agent_response.json()["id"]
        
        # Delete agent
        response = client.delete(f"/api/voice-agents/{agent_id}", 
                               headers=admin_headers)
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get(f"/api/voice-agents/{agent_id}", 
                                headers=admin_headers)
        assert get_response.status_code == 404


class TestLeadEndpoints:
    """Test lead management endpoints"""
    
    def test_create_lead(self, client: TestClient, authorized_headers, test_lead_data):
        """Test create lead endpoint"""
        response = client.post("/api/leads", 
                             json=test_lead_data, 
                             headers=authorized_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_lead_data["name"]
        assert data["email"] == test_lead_data["email"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_lead(self, client: TestClient, authorized_headers):
        """Test get lead by ID endpoint"""
        # Create lead
        lead_response = client.post("/api/leads", 
                                  json=test_lead_data, 
                                  headers=authorized_headers)
        lead_id = lead_response.json()["id"]
        
        # Get lead
        response = client.get(f"/api/leads/{lead_id}", headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead_id
        assert "property_preferences" in data
        assert "qualification_status" in data
    
    def test_update_lead_status(self, client: TestClient, authorized_headers):
        """Test update lead qualification status"""
        # Create lead
        lead_response = client.post("/api/leads", 
                                  json=test_lead_data, 
                                  headers=authorized_headers)
        lead_id = lead_response.json()["id"]
        
        # Update status
        update_data = {
            "qualification_status": "qualified",
            "lead_score": 85,
            "notes": "Interested in downtown properties, budget confirmed"
        }
        response = client.patch(f"/api/leads/{lead_id}/status", 
                              json=update_data, 
                              headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["qualification_status"] == "qualified"
        assert data["lead_score"] == 85
    
    def test_search_leads(self, client: TestClient, authorized_headers):
        """Test search leads with filters"""
        response = client.get("/api/leads/search?status=qualified&min_score=75", 
                            headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "filters" in data


class TestPropertyEndpoints:
    """Test property management endpoints"""
    
    def test_create_property(self, client: TestClient, authorized_headers, test_property_data):
        """Test create property listing endpoint"""
        response = client.post("/api/properties", 
                             json=test_property_data, 
                             headers=authorized_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["mls_id"] == test_property_data["mls_id"]
        assert data["price"] == test_property_data["price"]
        assert "id" in data
    
    def test_search_properties(self, client: TestClient, authorized_headers):
        """Test property search endpoint"""
        search_params = {
            "min_price": 300000,
            "max_price": 500000,
            "bedrooms": 3,
            "property_type": "single_family"
        }
        response = client.post("/api/properties/search", 
                             json=search_params, 
                             headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "properties" in data
        assert "total" in data
        assert "search_criteria" in data
    
    def test_get_property_market_analysis(self, client: TestClient, authorized_headers):
        """Test property market analysis endpoint"""
        # Create property
        prop_response = client.post("/api/properties", 
                                  json=test_property_data, 
                                  headers=authorized_headers)
        prop_id = prop_response.json()["id"]
        
        # Get market analysis
        response = client.get(f"/api/properties/{prop_id}/market-analysis", 
                            headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "average_area_price" in data
        assert "price_trend" in data
        assert "days_on_market_average" in data
        assert "comparable_properties" in data


class TestAnalyticsEndpoints:
    """Test analytics and reporting endpoints"""
    
    def test_get_dashboard_metrics(self, client: TestClient, authorized_headers):
        """Test dashboard metrics endpoint"""
        response = client.get("/api/analytics/dashboard", headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "conversations_today" in data
        assert "leads_qualified_today" in data
        assert "average_call_duration" in data
        assert "conversion_rate" in data
        assert "active_agents" in data
    
    def test_get_agent_performance(self, client: TestClient, admin_headers):
        """Test agent performance analytics"""
        response = client.get("/api/analytics/agent-performance?period=week", 
                            headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        if data["agents"]:
            agent = data["agents"][0]
            assert "agent_id" in agent
            assert "total_conversations" in agent
            assert "conversion_rate" in agent
            assert "average_lead_score" in agent
    
    def test_get_lead_source_analytics(self, client: TestClient, authorized_headers):
        """Test lead source analytics endpoint"""
        response = client.get("/api/analytics/lead-sources", headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)
        if data["sources"]:
            source = data["sources"][0]
            assert "source_name" in source
            assert "lead_count" in source
            assert "conversion_rate" in source
    
    def test_export_analytics_report(self, client: TestClient, admin_headers):
        """Test export analytics report endpoint"""
        export_params = {
            "report_type": "monthly_summary",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "format": "pdf"
        }
        response = client.post("/api/analytics/export", 
                             json=export_params, 
                             headers=admin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestWebhookEndpoints:
    """Test webhook configuration endpoints"""
    
    def test_create_webhook(self, client: TestClient, admin_headers):
        """Test create webhook endpoint"""
        webhook_data = {
            "url": "https://example.com/webhook",
            "events": ["conversation.completed", "lead.qualified"],
            "active": True,
            "secret": "webhook_secret_123"
        }
        response = client.post("/api/webhooks", 
                             json=webhook_data, 
                             headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == webhook_data["url"]
        assert set(data["events"]) == set(webhook_data["events"])
        assert "id" in data
    
    def test_list_webhooks(self, client: TestClient, admin_headers):
        """Test list webhooks endpoint"""
        response = client.get("/api/webhooks", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "webhooks" in data
        assert isinstance(data["webhooks"], list)
    
    def test_test_webhook(self, client: TestClient, admin_headers):
        """Test webhook test endpoint"""
        # Create webhook first
        webhook_data = {
            "url": "https://example.com/webhook",
            "events": ["test.event"],
            "active": True
        }
        webhook_response = client.post("/api/webhooks", 
                                     json=webhook_data, 
                                     headers=admin_headers)
        webhook_id = webhook_response.json()["id"]
        
        # Test webhook
        response = client.post(f"/api/webhooks/{webhook_id}/test", 
                             headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert "response_code" in data


class TestErrorHandling:
    """Test error handling across all endpoints"""
    
    def test_invalid_json_format(self, client: TestClient, authorized_headers):
        """Test handling of invalid JSON in request body"""
        response = client.post("/api/leads", 
                             data="invalid json", 
                             headers=authorized_headers)
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_missing_required_fields(self, client: TestClient, authorized_headers):
        """Test handling of missing required fields"""
        incomplete_lead = {"name": "John"}  # Missing required fields
        response = client.post("/api/leads", 
                             json=incomplete_lead, 
                             headers=authorized_headers)
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert isinstance(errors, list)
        assert any("required" in str(error).lower() for error in errors)
    
    def test_invalid_field_types(self, client: TestClient, authorized_headers):
        """Test handling of invalid field types"""
        invalid_lead = {
            "name": "John Doe",
            "email": "not-an-email",  # Invalid email format
            "phone": "123"  # Invalid phone format
        }
        response = client.post("/api/leads", 
                             json=invalid_lead, 
                             headers=authorized_headers)
        assert response.status_code == 422
    
    def test_resource_not_found(self, client: TestClient, authorized_headers):
        """Test handling of non-existent resources"""
        response = client.get("/api/leads/non-existent-id", 
                            headers=authorized_headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Lead not found"
    
    def test_unauthorized_organization_access(self, client: TestClient, authorized_headers):
        """Test prevention of cross-organization data access"""
        # Try to access resource from different organization
        response = client.get("/api/organizations/different-org-id/data", 
                            headers=authorized_headers)
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    def test_rate_limiting(self, client: TestClient, authorized_headers):
        """Test rate limiting on API endpoints"""
        # Make many requests quickly
        responses = []
        for _ in range(150):  # Exceed rate limit
            response = client.get("/api/leads", headers=authorized_headers)
            responses.append(response)
        
        # Check that some requests were rate limited
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0
        assert rate_limited[0].json()["detail"] == "Rate limit exceeded"


class TestPaginationAndFiltering:
    """Test pagination and filtering across endpoints"""
    
    def test_pagination_parameters(self, client: TestClient, authorized_headers):
        """Test pagination with page and page_size parameters"""
        response = client.get("/api/leads?page=2&page_size=10", 
                            headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["page"] == 2
        assert data["page_size"] == 10
    
    def test_sorting_parameters(self, client: TestClient, authorized_headers):
        """Test sorting functionality"""
        response = client.get("/api/leads?sort_by=created_at&sort_order=desc", 
                            headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # Verify results are sorted correctly
        if len(data["results"]) > 1:
            dates = [r["created_at"] for r in data["results"]]
            assert dates == sorted(dates, reverse=True)
    
    def test_date_range_filtering(self, client: TestClient, authorized_headers):
        """Test date range filtering"""
        response = client.get(
            "/api/conversations?start_date=2024-01-01&end_date=2024-01-31", 
            headers=authorized_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "filters" in data
        assert data["filters"]["start_date"] == "2024-01-01"
        assert data["filters"]["end_date"] == "2024-01-31"


class TestVoiceIntegration:
    """Test ElevenLabs voice integration endpoints"""
    
    def test_synthesize_speech(self, client: TestClient, authorized_headers):
        """Test text-to-speech synthesis endpoint"""
        tts_data = {
            "text": "Hello, I'm Sarah from Premier Real Estate. How can I help you today?",
            "voice_id": "sarah_professional",
            "settings": {
                "stability": 0.75,
                "similarity_boost": 0.85
            }
        }
        response = client.post("/api/voice/synthesize", 
                             json=tts_data, 
                             headers=authorized_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
    
    def test_transcribe_audio(self, client: TestClient, authorized_headers):
        """Test speech-to-text transcription endpoint"""
        # This would normally include audio file upload
        # For testing, we'll verify the endpoint structure
        with open("test_audio.mp3", "rb") as audio_file:
            response = client.post(
                "/api/voice/transcribe",
                files={"audio": ("test.mp3", audio_file, "audio/mpeg")},
                headers=authorized_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "transcript" in data
        assert "confidence" in data
        assert "duration_seconds" in data
    
    def test_voice_session_management(self, client: TestClient, authorized_headers):
        """Test voice session creation and management"""
        session_data = {
            "lead_id": "lead_123",
            "voice_agent_id": "agent_456",
            "scheduled_time": "2024-01-15T10:00:00Z"
        }
        response = client.post("/api/voice/sessions", 
                             json=session_data, 
                             headers=authorized_headers)
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "call_url" in data
        assert "status" == "scheduled"


class TestBulkOperations:
    """Test bulk operation endpoints"""
    
    def test_bulk_lead_import(self, client: TestClient, admin_headers):
        """Test bulk lead import endpoint"""
        bulk_leads = {
            "leads": [
                {
                    "name": "Lead 1",
                    "email": "lead1@example.com",
                    "phone": "+1234567890",
                    "source": "import"
                },
                {
                    "name": "Lead 2", 
                    "email": "lead2@example.com",
                    "phone": "+1234567891",
                    "source": "import"
                }
            ]
        }
        response = client.post("/api/leads/bulk-import", 
                             json=bulk_leads, 
                             headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 2
        assert data["failed"] == 0
        assert "results" in data
    
    def test_bulk_status_update(self, client: TestClient, authorized_headers):
        """Test bulk status update for multiple leads"""
        bulk_update = {
            "lead_ids": ["lead1", "lead2", "lead3"],
            "status": "contacted",
            "notes": "Bulk status update after email campaign"
        }
        response = client.post("/api/leads/bulk-update", 
                             json=bulk_update, 
                             headers=authorized_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == len(bulk_update["lead_ids"])
        assert "results" in data


# Additional test fixtures and utilities
@pytest.fixture
def client():
    """Create test client"""
    from main import app
    return TestClient(app)

@pytest.fixture
def authorized_headers(client: TestClient, test_user_data):
    """Get headers with valid auth token"""
    response = client.post("/api/auth/register", json=test_user_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client: TestClient):
    """Get headers with admin auth token"""
    admin_data = {
        "email": "admin@seiketsu.ai",
        "password": "AdminPass123!",
        "role": "admin"
    }
    response = client.post("/api/auth/register", json=admin_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}