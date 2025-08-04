"""
Comprehensive authentication and authorization tests
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt
from app.core.config import settings


class TestAuthenticationFlow:
    """Test complete authentication flow"""
    
    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, client: TestClient):
        """Test complete authentication flow from registration to logout"""
        # 1. Register new user
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User",
            "role": "agent"
        }
        
        register_response = client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert "access_token" in register_data
        assert "refresh_token" in register_data
        assert register_data["email"] == user_data["email"]
        
        # 2. Use access token to access protected endpoint
        headers = {"Authorization": f"Bearer {register_data['access_token']}"}
        profile_response = client.get("/api/users/profile", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == user_data["email"]
        
        # 3. Logout
        logout_response = client.post("/api/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # 4. Verify token is invalidated
        profile_response_after = client.get("/api/users/profile", headers=headers)
        assert profile_response_after.status_code == 401
        
        # 5. Login again
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "access_token" in login_result
        
        # 6. Refresh token
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": login_result["refresh_token"]}
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert refresh_data["access_token"] != login_result["access_token"]
    
    @pytest.mark.asyncio
    async def test_registration_validation(self, client: TestClient):
        """Test registration input validation"""
        # Test invalid email
        invalid_email_data = {
            "email": "not-an-email",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=invalid_email_data)
        assert response.status_code == 422
        
        # Test weak password
        weak_password_data = {
            "email": "test@example.com",
            "password": "weak",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=weak_password_data)
        assert response.status_code == 422
        
        # Test duplicate email
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        # First registration
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Duplicate registration
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_validation(self, client: TestClient):
        """Test login validation and error handling"""
        # Test login with non-existent user
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
        
        # Register user first
        user_data = {
            "email": "testlogin@example.com",
            "password": "CorrectPass123!",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Test login with wrong password
        wrong_password_data = {
            "email": user_data["email"],
            "password": "WrongPass123!"
        }
        response = client.post("/api/auth/login", json=wrong_password_data)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
        
        # Test successful login
        correct_login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = client.post("/api/auth/login", json=correct_login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    @pytest.mark.asyncio
    async def test_token_expiration(self, client: TestClient):
        """Test token expiration handling"""
        # Register user
        user_data = {
            "email": "expiry@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        register_response = client.post("/api/auth/register", json=user_data)
        tokens = register_response.json()
        
        # Create expired token
        expired_payload = {
            "sub": user_data["email"],
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        # Try to use expired token
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/users/profile", headers=headers)
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_token_format(self, client: TestClient):
        """Test various invalid token formats"""
        # Test malformed token
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/users/profile", headers=headers)
        assert response.status_code == 401
        
        # Test missing Bearer prefix
        headers = {"Authorization": "just_a_token"}
        response = client.get("/api/users/profile", headers=headers)
        assert response.status_code == 401
        
        # Test empty authorization header
        headers = {"Authorization": ""}
        response = client.get("/api/users/profile", headers=headers)
        assert response.status_code == 401
        
        # Test no authorization header
        response = client.get("/api/users/profile")
        assert response.status_code == 401


class TestAuthorizationRoles:
    """Test role-based authorization"""
    
    @pytest.mark.asyncio
    async def test_agent_role_permissions(self, client: TestClient):
        """Test agent role permissions"""
        # Register agent user
        agent_data = {
            "email": "agent@example.com",
            "password": "AgentPass123!",
            "full_name": "Test Agent",
            "role": "agent"
        }
        response = client.post("/api/auth/register", json=agent_data)
        agent_token = response.json()["access_token"]
        agent_headers = {"Authorization": f"Bearer {agent_token}"}
        
        # Agent can access general endpoints
        response = client.get("/api/leads", headers=agent_headers)
        assert response.status_code == 200
        
        response = client.get("/api/conversations", headers=agent_headers)
        assert response.status_code == 200
        
        # Agent cannot access admin endpoints
        response = client.get("/api/admin/users", headers=agent_headers)
        assert response.status_code == 403
        
        response = client.post("/api/organizations", json={}, headers=agent_headers)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_role_permissions(self, client: TestClient):
        """Test admin role permissions"""
        # Register admin user
        admin_data = {
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "full_name": "Test Admin",
            "role": "admin"
        }
        response = client.post("/api/auth/register", json=admin_data)
        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Admin can access all endpoints
        response = client.get("/api/leads", headers=admin_headers)
        assert response.status_code == 200
        
        response = client.get("/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        
        response = client.get("/api/analytics/agent-performance", headers=admin_headers)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, client: TestClient):
        """Test multi-tenant data isolation"""
        # Create two organizations
        org1_admin = {
            "email": "admin1@org1.com",
            "password": "Admin1Pass123!",
            "full_name": "Org1 Admin",
            "role": "admin",
            "organization_id": "org1"
        }
        org2_admin = {
            "email": "admin2@org2.com",
            "password": "Admin2Pass123!",
            "full_name": "Org2 Admin",
            "role": "admin",
            "organization_id": "org2"
        }
        
        # Register admins
        response1 = client.post("/api/auth/register", json=org1_admin)
        token1 = response1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        response2 = client.post("/api/auth/register", json=org2_admin)
        token2 = response2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create lead for org1
        lead_data = {
            "name": "Org1 Lead",
            "email": "lead@org1.com",
            "phone": "+1234567890"
        }
        create_response = client.post("/api/leads", json=lead_data, headers=headers1)
        assert create_response.status_code == 201
        lead_id = create_response.json()["id"]
        
        # Org1 admin can access their lead
        response = client.get(f"/api/leads/{lead_id}", headers=headers1)
        assert response.status_code == 200
        
        # Org2 admin cannot access org1's lead
        response = client.get(f"/api/leads/{lead_id}", headers=headers2)
        assert response.status_code == 404  # Not found due to tenant isolation


class TestPasswordManagement:
    """Test password reset and change functionality"""
    
    @pytest.mark.asyncio
    async def test_password_reset_flow(self, client: TestClient):
        """Test complete password reset flow"""
        # Register user
        user_data = {
            "email": "reset@example.com",
            "password": "OldPass123!",
            "full_name": "Reset User"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Request password reset
        reset_request = {"email": user_data["email"]}
        response = client.post("/api/auth/forgot-password", json=reset_request)
        assert response.status_code == 200
        assert "reset token sent" in response.json()["message"].lower()
        
        # In real implementation, get reset token from email
        # For testing, we'll mock this
        reset_token = "mocked_reset_token"
        
        # Reset password with token
        new_password_data = {
            "token": reset_token,
            "new_password": "NewSecurePass456!"
        }
        response = client.post("/api/auth/reset-password", json=new_password_data)
        assert response.status_code == 200
        
        # Login with new password
        login_data = {
            "email": user_data["email"],
            "password": "NewSecurePass456!"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        # Old password should not work
        old_login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = client.post("/api/auth/login", json=old_login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_password_change(self, client: TestClient):
        """Test authenticated password change"""
        # Register and login
        user_data = {
            "email": "change@example.com",
            "password": "CurrentPass123!",
            "full_name": "Change User"
        }
        register_response = client.post("/api/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Change password
        change_data = {
            "current_password": user_data["password"],
            "new_password": "UpdatedPass456!"
        }
        response = client.post("/api/users/change-password", 
                             json=change_data, 
                             headers=headers)
        assert response.status_code == 200
        
        # Login with new password
        new_login_data = {
            "email": user_data["email"],
            "password": "UpdatedPass456!"
        }
        response = client.post("/api/auth/login", json=new_login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestSessionManagement:
    """Test session and token management"""
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, client: TestClient):
        """Test handling of concurrent sessions"""
        user_data = {
            "email": "concurrent@example.com",
            "password": "SecurePass123!",
            "full_name": "Concurrent User"
        }
        
        # Register user
        client.post("/api/auth/register", json=user_data)
        
        # Create multiple sessions
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        # Session 1
        response1 = client.post("/api/auth/login", json=login_data)
        token1 = response1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        # Session 2
        response2 = client.post("/api/auth/login", json=login_data)
        token2 = response2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Both sessions should be valid
        assert client.get("/api/users/profile", headers=headers1).status_code == 200
        assert client.get("/api/users/profile", headers=headers2).status_code == 200
        
        # Logout from session 1
        client.post("/api/auth/logout", headers=headers1)
        
        # Session 1 should be invalid
        assert client.get("/api/users/profile", headers=headers1).status_code == 401
        
        # Session 2 should still be valid
        assert client.get("/api/users/profile", headers=headers2).status_code == 200
    
    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, client: TestClient):
        """Test refresh token rotation for security"""
        # Register and get initial tokens
        user_data = {
            "email": "rotation@example.com",
            "password": "SecurePass123!",
            "full_name": "Rotation User"
        }
        register_response = client.post("/api/auth/register", json=user_data)
        initial_tokens = register_response.json()
        
        # Use refresh token
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": initial_tokens["refresh_token"]}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        
        # New tokens should be different
        assert new_tokens["access_token"] != initial_tokens["access_token"]
        assert new_tokens["refresh_token"] != initial_tokens["refresh_token"]
        
        # Old refresh token should be invalidated
        old_refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": initial_tokens["refresh_token"]}
        )
        assert old_refresh_response.status_code == 401
        
        # New refresh token should work
        newest_refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": new_tokens["refresh_token"]}
        )
        assert newest_refresh_response.status_code == 200