"""
Unit tests for Third-Party Integration Service
Tests automated account creation and management for ElevenLabs, Twilio, MLS APIs
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from app.services.third_party_service import ThirdPartyService, ThirdPartyCredentials


class TestThirdPartyService:
    """Comprehensive unit tests for ThirdPartyService"""
    
    @pytest.fixture
    def service(self):
        """Create ThirdPartyService instance with mocked dependencies"""
        with patch('app.services.third_party_service.AsyncHTTPClient') as mock_client:
            service = ThirdPartyService()
            service.http_client = mock_client.return_value
            return service
    
    @pytest.fixture
    def mock_client_data(self):
        """Mock client data for testing"""
        return {
            "company_name": "Test Real Estate Co",
            "email": "admin@testrealestate.com",
            "phone": "+1-555-123-4567",
            "website": "https://testrealestate.com",
            "subscription_tier": "silver"
        }
    
    @pytest.fixture
    def mock_ai_analysis(self):
        """Mock AI analysis result"""
        return {
            "company_size": "medium",
            "usage_prediction": {
                "daily_voice_calls": 100,
                "monthly_sms": 2000,
                "weekly_mls_queries": 400
            },
            "integration_priorities": ["voice", "sms", "mls"]
        }
    
    # ElevenLabs Tests
    @pytest.mark.asyncio
    async def test_create_elevenlabs_account_success(self, service, mock_client_data, mock_ai_analysis):
        """Test successful ElevenLabs account creation"""
        client_id = "client_test123"
        
        with patch.object(service, '_optimize_elevenlabs_config', new_callable=AsyncMock) as mock_config, \
             patch.object(service, '_create_elevenlabs_account_mock', new_callable=AsyncMock) as mock_create, \
             patch.object(service, '_configure_elevenlabs_voices', new_callable=AsyncMock) as mock_voices, \
             patch.object(service, '_set_elevenlabs_usage_limits', new_callable=AsyncMock) as mock_limits:
            
            # Setup mocks
            mock_config.return_value = {"usage_tier": "creator", "primary_voice": {"voice_id": "test_voice"}}
            mock_create.return_value = {"account_id": "elevenlabs_test", "api_key": "sk_test"}
            mock_voices.return_value = {"primary_voice_configured": True}
            mock_limits.return_value = {"tier": "silver", "monthly_character_limit": 30000}
            
            result = await service.create_elevenlabs_account(client_id, mock_client_data, mock_ai_analysis)
            
            assert result["service"] == "elevenlabs"
            assert result["account_id"] == "elevenlabs_test"
            assert result["api_key"] == "sk_test"
            assert result["status"] == "active"
            assert "voice_settings" in result
            assert "usage_limits" in result
            assert "configuration" in result
    
    @pytest.mark.asyncio
    async def test_optimize_elevenlabs_config_startup(self, service, mock_client_data):
        """Test ElevenLabs config optimization for startup"""
        ai_analysis = {
            "company_size": "startup",
            "usage_prediction": {"daily_voice_calls": 20}
        }
        
        config = await service._optimize_elevenlabs_config(mock_client_data, ai_analysis)
        
        assert config["primary_voice"]["name"] == "Rachel"
        assert config["primary_voice"]["style"] == "friendly"
        assert config["usage_tier"] == "free"
        assert config["features"]["voice_cloning"] is False
        assert config["optimization"]["model"] == "eleven_monolingual_v1"
    
    @pytest.mark.asyncio
    async def test_optimize_elevenlabs_config_enterprise(self, service, mock_client_data):
        """Test ElevenLabs config optimization for enterprise"""
        ai_analysis = {
            "company_size": "enterprise",
            "usage_prediction": {"daily_voice_calls": 300}
        }
        
        config = await service._optimize_elevenlabs_config(mock_client_data, ai_analysis)
        
        assert config["primary_voice"]["name"] == "Arnold"
        assert config["primary_voice"]["style"] == "corporate"
        assert config["usage_tier"] == "pro"
        assert config["features"]["voice_cloning"] is True
        assert config["features"]["instant_voice_cloning"] is True
        assert config["optimization"]["model"] == "eleven_multilingual_v2"
        assert config["optimization"]["optimize_streaming_latency"] is True
    
    def test_calculate_elevenlabs_tier(self, service):
        """Test ElevenLabs tier calculation"""
        assert service._calculate_elevenlabs_tier(10) == "free"  # 60,000 chars/month
        assert service._calculate_elevenlabs_tier(50) == "starter"  # 300,000 chars/month
        assert service._calculate_elevenlabs_tier(100) == "creator"  # 600,000 chars/month
        assert service._calculate_elevenlabs_tier(200) == "pro"  # 1,200,000 chars/month
    
    @pytest.mark.asyncio
    async def test_create_elevenlabs_account_mock(self, service, mock_client_data):
        """Test mock ElevenLabs account creation"""
        client_id = "client_test123"
        voice_config = {"usage_tier": "creator"}
        
        result = await service._create_elevenlabs_account_mock(client_id, mock_client_data, voice_config)
        
        assert result["account_id"].startswith("elevenlabs_client_test123")
        assert result["api_key"].startswith("sk-")
        assert result["subscription_tier"] == "creator"
        assert result["account_email"] == mock_client_data["email"]
    
    @pytest.mark.asyncio
    async def test_configure_elevenlabs_voices(self, service):
        """Test ElevenLabs voice configuration"""
        api_key = "sk_test"
        voice_config = {
            "primary_voice": {"voice_id": "test_voice", "name": "TestVoice"},
            "voice_settings": {"stability": 0.75, "similarity_boost": 0.75},
            "optimization": {"model": "eleven_monolingual_v1"}
        }
        
        result = await service._configure_elevenlabs_voices(api_key, voice_config)
        
        assert result["primary_voice_configured"] is True
        assert result["voice_id"] == "test_voice"
        assert result["voice_name"] == "TestVoice"
        assert result["settings_applied"] == voice_config["voice_settings"]
        assert result["model_configured"] == "eleven_monolingual_v1"
    
    @pytest.mark.asyncio
    async def test_set_elevenlabs_usage_limits(self, service):
        """Test ElevenLabs usage limits setting"""
        api_key = "sk_test"
        
        # Test different subscription tiers
        bronze_limits = await service._set_elevenlabs_usage_limits(api_key, "bronze")
        assert bronze_limits["monthly_character_limit"] == 10000
        assert bronze_limits["concurrent_request_limit"] == 2
        
        gold_limits = await service._set_elevenlabs_usage_limits(api_key, "gold")
        assert gold_limits["monthly_character_limit"] == 100000
        assert gold_limits["concurrent_request_limit"] == 10
        
        enterprise_limits = await service._set_elevenlabs_usage_limits(api_key, "enterprise")
        assert enterprise_limits["monthly_character_limit"] == 500000
        assert enterprise_limits["concurrent_request_limit"] == 20
    
    # Twilio Tests
    @pytest.mark.asyncio
    async def test_create_twilio_account_success(self, service, mock_client_data, mock_ai_analysis):
        """Test successful Twilio account creation"""
        client_id = "client_test123"
        
        with patch.object(service, '_optimize_twilio_config', new_callable=AsyncMock) as mock_config, \
             patch.object(service, '_create_twilio_subaccount', new_callable=AsyncMock) as mock_create, \
             patch.object(service, '_purchase_twilio_phone_number', new_callable=AsyncMock) as mock_phone, \
             patch.object(service, '_configure_twilio_services', new_callable=AsyncMock) as mock_services:
            
            # Setup mocks
            mock_config.return_value = {"phone_number_type": "local", "area_code": "555"}
            mock_create.return_value = {"account_sid": "AC_test", "auth_token": "auth_test"}
            mock_phone.return_value = {"phone_number": "+1-555-999-0000", "sid": "PN_test"}
            mock_services.return_value = {"voice_service": {"configured": True}}
            
            result = await service.create_twilio_account(client_id, mock_client_data, mock_ai_analysis)
            
            assert result["service"] == "twilio"
            assert result["account_sid"] == "AC_test"
            assert result["auth_token"] == "auth_test"
            assert result["phone_number"] == "+1-555-999-0000"
            assert result["phone_number_sid"] == "PN_test"
            assert result["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_optimize_twilio_config_small_business(self, service, mock_client_data):
        """Test Twilio config optimization for small business"""
        ai_analysis = {
            "company_size": "small",
            "usage_prediction": {"monthly_sms": 500, "daily_voice_calls": 20}
        }
        
        config = await service._optimize_twilio_config(mock_client_data, ai_analysis)
        
        assert config["phone_number_type"] == "local"
        assert config["features"]["sms"] is True
        assert config["features"]["voice"] is True
        assert config["features"]["mms"] is False
        assert config["features"]["international"] is False
        assert config["usage_based_pricing"]["recommended_plan"] == "pay-as-you-go"
    
    @pytest.mark.asyncio
    async def test_optimize_twilio_config_enterprise(self, service, mock_client_data):
        """Test Twilio config optimization for enterprise"""
        ai_analysis = {
            "company_size": "enterprise",
            "usage_prediction": {"monthly_sms": 50000, "daily_voice_calls": 500}
        }
        
        config = await service._optimize_twilio_config(mock_client_data, ai_analysis)
        
        assert config["features"]["mms"] is True
        assert config["features"]["international"] is True
        assert config["usage_based_pricing"]["recommended_plan"] == "enterprise"
    
    def test_determine_area_code_from_phone(self, service):
        """Test area code determination from existing phone number"""
        client_data = {"phone": "+1-212-555-1234"}
        area_code = service._determine_area_code(client_data)
        assert area_code == "212"
    
    def test_determine_area_code_default(self, service):
        """Test default area code when no phone provided"""
        client_data = {"phone": "invalid"}
        area_code = service._determine_area_code(client_data)
        assert area_code == "212"  # Default NYC area code
    
    def test_recommend_twilio_plan(self, service):
        """Test Twilio plan recommendation logic"""
        assert service._recommend_twilio_plan(500, 10) == "pay-as-you-go"
        assert service._recommend_twilio_plan(5000, 50) == "starter"
        assert service._recommend_twilio_plan(50000, 200) == "business"
        assert service._recommend_twilio_plan(200000, 1000) == "enterprise"
    
    @pytest.mark.asyncio
    async def test_create_twilio_subaccount(self, service, mock_client_data):
        """Test Twilio subaccount creation"""
        client_id = "client_test123"
        twilio_config = {"features": {"sms": True}}
        
        result = await service._create_twilio_subaccount(client_id, mock_client_data, twilio_config)
        
        assert result["account_sid"].startswith("AC")
        assert len(result["auth_token"]) == 32  # UUID hex length
        assert result["friendly_name"] == f"Seiketsu AI - {mock_client_data['company_name']}"
        assert result["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_purchase_twilio_phone_number(self, service):
        """Test Twilio phone number purchase"""
        account_sid = "AC_test"
        auth_token = "auth_test"
        twilio_config = {
            "area_code": "555",
            "features": {"sms": True, "mms": True}
        }
        
        result = await service._purchase_twilio_phone_number(account_sid, auth_token, twilio_config)
        
        assert result["phone_number"].startswith("+1555")
        assert result["sid"].startswith("PN")
        assert result["friendly_name"] == "Seiketsu AI Main Line"
        assert result["capabilities"]["voice"] is True
        assert result["capabilities"]["SMS"] is True
        assert result["capabilities"]["MMS"] is True
    
    @pytest.mark.asyncio
    async def test_configure_twilio_services(self, service):
        """Test Twilio services configuration"""
        account_sid = "AC_test"
        auth_token = "auth_test"
        phone_number = {"sid": "PN_test", "phone_number": "+1-555-999-0000"}
        twilio_config = {
            "webhook_config": {
                "voice_webhook": "https://test.seiketsu.ai/webhooks/voice",
                "sms_webhook": "https://test.seiketsu.ai/webhooks/sms"
            }
        }
        
        result = await service._configure_twilio_services(account_sid, auth_token, phone_number, twilio_config)
        
        assert result["voice_service"]["configured"] is True
        assert result["voice_service"]["webhook_url"] == twilio_config["webhook_config"]["voice_webhook"]
        assert result["messaging_service"]["configured"] is True
        assert result["messaging_service"]["webhook_url"] == twilio_config["webhook_config"]["sms_webhook"]
        assert result["phone_number_config"]["voice_url"] == twilio_config["webhook_config"]["voice_webhook"]
        assert result["phone_number_config"]["sms_url"] == twilio_config["webhook_config"]["sms_webhook"]
    
    # MLS Tests
    @pytest.mark.asyncio
    async def test_create_mls_account_success(self, service, mock_client_data, mock_ai_analysis):
        """Test successful MLS account creation"""
        client_id = "client_test123"
        
        with patch.object(service, '_optimize_mls_config', new_callable=AsyncMock) as mock_config, \
             patch.object(service, '_register_mls_access', new_callable=AsyncMock) as mock_register, \
             patch.object(service, '_configure_mls_permissions', new_callable=AsyncMock) as mock_permissions:
            
            # Setup mocks
            mock_config.return_value = {"data_access_level": "professional", "regions": ["Northeast"]}
            mock_register.return_value = {"account_id": "mls_test", "api_key": "mls_key_test"}
            mock_permissions.return_value = {"data_access_configured": True}
            
            result = await service.create_mls_account(client_id, mock_client_data, mock_ai_analysis)
            
            assert result["service"] == "mls"
            assert result["account_id"] == "mls_test"
            assert result["api_key"] == "mls_key_test"
            assert result["status"] == "active"
            assert "mls_regions" in result
            assert "data_permissions" in result
    
    @pytest.mark.asyncio
    async def test_optimize_mls_config_small_company(self, service, mock_client_data):
        """Test MLS config optimization for small company"""
        ai_analysis = {
            "company_size": "small",
            "usage_prediction": {"weekly_mls_queries": 100}
        }
        
        config = await service._optimize_mls_config(mock_client_data, ai_analysis)
        
        assert config["data_access_level"] == "standard"
        assert config["query_limits"]["daily_limit"] == 200  # 100 * 2 buffer
        assert config["query_limits"]["concurrent_requests"] == 2
        assert config["features"]["historical_data"] is False
        assert config["features"]["market_analytics"] is False
        assert config["features"]["photo_access"] is True  # Not startup
    
    @pytest.mark.asyncio
    async def test_optimize_mls_config_enterprise(self, service, mock_client_data):
        """Test MLS config optimization for enterprise"""
        ai_analysis = {
            "company_size": "enterprise",
            "usage_prediction": {"weekly_mls_queries": 1500}
        }
        
        config = await service._optimize_mls_config(mock_client_data, ai_analysis)
        
        assert config["data_access_level"] == "enterprise"
        assert config["query_limits"]["concurrent_requests"] == 5
        assert config["features"]["historical_data"] is True
        assert config["features"]["market_analytics"] is True
        assert config["features"]["automated_valuations"] is True
    
    def test_determine_mls_access_level(self, service):
        """Test MLS access level determination"""
        assert service._determine_mls_access_level("startup", 50) == "standard"
        assert service._determine_mls_access_level("medium", 600) == "professional"
        assert service._determine_mls_access_level("enterprise", 200) == "enterprise"
        assert service._determine_mls_access_level("small", 1200) == "enterprise"  # High usage overrides size
    
    def test_determine_mls_regions(self, service, mock_client_data):
        """Test MLS regions determination"""
        regions = service._determine_mls_regions(mock_client_data)
        assert isinstance(regions, list)
        assert len(regions) > 0
        assert "Northeast" in regions or "Southeast" in regions
    
    def test_get_mls_data_fields(self, service):
        """Test MLS data fields based on company size"""
        startup_fields = service._get_mls_data_fields("startup")
        assert "ListingId" in startup_fields
        assert "PropertyType" in startup_fields
        assert "DaysOnMarket" not in startup_fields  # Not included for startup
        
        medium_fields = service._get_mls_data_fields("medium")
        assert "DaysOnMarket" in medium_fields  # Included for medium+
        assert "TaxAmount" not in medium_fields  # Not included for medium
        
        enterprise_fields = service._get_mls_data_fields("enterprise")
        assert "TaxAmount" in enterprise_fields  # Included for enterprise
        assert len(enterprise_fields) > len(startup_fields)
    
    @pytest.mark.asyncio
    async def test_register_mls_access(self, service, mock_client_data):
        """Test MLS access registration"""
        client_id = "client_test123"
        mls_config = {
            "regions": ["Northeast", "Southeast"],
            "data_access_level": "professional"
        }
        
        result = await service._register_mls_access(client_id, mock_client_data, mls_config)
        
        assert result["account_id"].startswith("mls_client_test123")
        assert result["api_key"].startswith("mls_")
        assert result["mls_regions"] == mls_config["regions"]
        assert result["access_level"] == "professional"
    
    @pytest.mark.asyncio
    async def test_configure_mls_permissions(self, service):
        """Test MLS permissions configuration"""
        api_key = "mls_test_key"
        mls_config = {
            "property_types": ["residential", "commercial"],
            "data_fields": ["ListingId", "PropertyType"],
            "query_limits": {"daily_limit": 200},
            "features": {"historical_data": True}
        }
        
        result = await service._configure_mls_permissions(api_key, mls_config)
        
        assert result["data_access_configured"] is True
        assert result["property_types"] == mls_config["property_types"]
        assert result["data_fields"] == mls_config["data_fields"]
        assert result["query_limits"] == mls_config["query_limits"]
        assert result["features_enabled"] == mls_config["features"]
    
    # Cleanup Tests
    @pytest.mark.asyncio
    async def test_cleanup_accounts_success(self, service):
        """Test successful account cleanup"""
        client_id = "client_test123"
        
        with patch.object(service, '_get_client_accounts', new_callable=AsyncMock) as mock_get_accounts, \
             patch.object(service, '_cleanup_elevenlabs_account', new_callable=AsyncMock) as mock_cleanup_el, \
             patch.object(service, '_cleanup_twilio_account', new_callable=AsyncMock) as mock_cleanup_tw, \
             patch.object(service, '_cleanup_mls_account', new_callable=AsyncMock) as mock_cleanup_mls:
            
            mock_get_accounts.return_value = [
                {"service_name": "elevenlabs", "account_id": "elevenlabs_test"},
                {"service_name": "twilio", "account_id": "twilio_test"},
                {"service_name": "mls", "account_id": "mls_test"}
            ]
            
            await service.cleanup_accounts(client_id)
            
            mock_cleanup_el.assert_called_once()
            mock_cleanup_tw.assert_called_once()
            mock_cleanup_mls.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_accounts_partial_failure(self, service):
        """Test account cleanup with partial failures"""
        client_id = "client_test123"
        
        with patch.object(service, '_get_client_accounts', new_callable=AsyncMock) as mock_get_accounts, \
             patch.object(service, '_cleanup_elevenlabs_account', new_callable=AsyncMock) as mock_cleanup_el, \
             patch.object(service, '_cleanup_twilio_account', new_callable=AsyncMock) as mock_cleanup_tw:
            
            mock_get_accounts.return_value = [
                {"service_name": "elevenlabs", "account_id": "elevenlabs_test"},
                {"service_name": "twilio", "account_id": "twilio_test"}
            ]
            
            # Mock ElevenLabs cleanup to fail
            mock_cleanup_el.side_effect = Exception("ElevenLabs cleanup failed")
            
            # Should not raise exception but continue with other cleanups
            await service.cleanup_accounts(client_id)
            
            mock_cleanup_el.assert_called_once()
            mock_cleanup_tw.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_client_accounts(self, service):
        """Test getting client accounts"""
        client_id = "client_test123"
        
        accounts = await service._get_client_accounts(client_id)
        
        assert isinstance(accounts, list)
        assert len(accounts) > 0
        assert all("service_name" in account for account in accounts)
        assert all("account_id" in account for account in accounts)
    
    # Status and Management Tests
    @pytest.mark.asyncio
    async def test_get_account_status(self, service):
        """Test getting account status"""
        client_id = "client_test123"
        service_name = "elevenlabs"
        
        result = await service.get_account_status(client_id, service_name)
        
        assert result["client_id"] == client_id
        assert result["service"] == service_name
        assert result["status"] == "active"
        assert "last_checked" in result
        assert "usage_current_month" in result
    
    @pytest.mark.asyncio
    async def test_update_account_limits(self, service):
        """Test updating account limits"""
        client_id = "client_test123"
        service_name = "elevenlabs"
        new_limits = {"monthly_characters": 50000, "concurrent_requests": 5}
        
        result = await service.update_account_limits(client_id, service_name, new_limits)
        
        assert result["client_id"] == client_id
        assert result["service"] == service_name
        assert result["limits_updated"] is True
        assert result["new_limits"] == new_limits
        assert "updated_at" in result
    
    @pytest.mark.asyncio
    async def test_validate_account_health_all_healthy(self, service):
        """Test account health validation when all services are healthy"""
        client_id = "client_test123"
        
        with patch.object(service, '_check_service_health', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {"status": "healthy", "response_time": "120ms"}
            
            result = await service.validate_account_health(client_id)
            
            assert result["client_id"] == client_id
            assert result["overall_status"] == "healthy"
            assert len(result["services"]) == 3  # elevenlabs, twilio, mls
            assert all(service["status"] == "healthy" for service in result["services"].values())
    
    @pytest.mark.asyncio
    async def test_validate_account_health_some_unhealthy(self, service):
        """Test account health validation with some unhealthy services"""
        client_id = "client_test123"
        
        def mock_health_check(client_id, service_name):
            if service_name == "elevenlabs":
                return {"status": "healthy"}
            else:
                raise Exception("Service unavailable")
        
        with patch.object(service, '_check_service_health', side_effect=mock_health_check):
            result = await service.validate_account_health(client_id)
            
            assert result["overall_status"] == "issues_detected"
            assert result["services"]["elevenlabs"]["status"] == "healthy"
            assert result["services"]["twilio"]["status"] == "unhealthy"
            assert result["services"]["mls"]["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_check_service_health(self, service):
        """Test individual service health check"""
        client_id = "client_test123"
        service_name = "elevenlabs"
        
        result = await service._check_service_health(client_id, service_name)
        
        assert result["status"] == "healthy"
        assert "response_time" in result
        assert "last_successful_call" in result
        assert "rate_limit_remaining" in result


class TestThirdPartyCredentials:
    """Test ThirdPartyCredentials dataclass"""
    
    def test_credentials_creation(self):
        """Test credentials creation"""
        creds = ThirdPartyCredentials(
            service_name="elevenlabs",
            api_key="sk_test123",
            api_secret="secret_test",
            additional_config={"voice_id": "test_voice"}
        )
        
        assert creds.service_name == "elevenlabs"
        assert creds.api_key == "sk_test123"
        assert creds.api_secret == "secret_test"
        assert creds.additional_config["voice_id"] == "test_voice"
    
    def test_credentials_minimal(self):
        """Test credentials with minimal required fields"""
        creds = ThirdPartyCredentials(
            service_name="twilio",
            api_key="AC_test123"
        )
        
        assert creds.service_name == "twilio"
        assert creds.api_key == "AC_test123"
        assert creds.api_secret is None
        assert creds.additional_config is None


# Performance Tests
class TestThirdPartyServicePerformance:
    """Performance tests for third-party service"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_account_creation_performance(self, benchmark):
        """Benchmark account creation performance"""
        service = ThirdPartyService()
        client_id = "client_perf_test"
        client_data = {"company_name": "Perf Test", "email": "perf@test.com", "phone": "+1-555-123-4567"}
        ai_analysis = {"company_size": "small", "usage_prediction": {"daily_voice_calls": 50}}
        
        with patch.object(service, '_optimize_elevenlabs_config', new_callable=AsyncMock) as mock_config, \
             patch.object(service, '_create_elevenlabs_account_mock', new_callable=AsyncMock) as mock_create, \
             patch.object(service, '_configure_elevenlabs_voices', new_callable=AsyncMock) as mock_voices, \
             patch.object(service, '_set_elevenlabs_usage_limits', new_callable=AsyncMock) as mock_limits:
            
            mock_config.return_value = {"usage_tier": "free"}
            mock_create.return_value = {"account_id": "test", "api_key": "sk_test"}
            mock_voices.return_value = {"configured": True}
            mock_limits.return_value = {"tier": "free"}
            
            # Benchmark should complete within 200ms
            result = await benchmark(service.create_elevenlabs_account, client_id, client_data, ai_analysis)
            assert result["service"] == "elevenlabs"


# Error Handling Tests
class TestThirdPartyServiceErrorHandling:
    """Error handling tests for third-party service"""
    
    @pytest.mark.asyncio
    async def test_elevenlabs_account_creation_failure(self):
        """Test ElevenLabs account creation failure handling"""
        service = ThirdPartyService()
        client_id = "client_error_test"
        client_data = {"company_name": "Error Test", "email": "error@test.com", "phone": "+1-555-123-4567"}
        ai_analysis = {"company_size": "small"}
        
        with patch.object(service, '_optimize_elevenlabs_config', side_effect=Exception("Config error")):
            with pytest.raises(Exception):
                await service.create_elevenlabs_account(client_id, client_data, ai_analysis)
    
    @pytest.mark.asyncio
    async def test_twilio_account_creation_failure(self):
        """Test Twilio account creation failure handling"""
        service = ThirdPartyService()
        client_id = "client_error_test"
        client_data = {"company_name": "Error Test", "email": "error@test.com", "phone": "+1-555-123-4567"}
        ai_analysis = {"company_size": "small"}
        
        with patch.object(service, '_optimize_twilio_config', side_effect=Exception("Twilio config error")):
            with pytest.raises(Exception):
                await service.create_twilio_account(client_id, client_data, ai_analysis)
    
    @pytest.mark.asyncio
    async def test_mls_account_creation_failure(self):
        """Test MLS account creation failure handling"""
        service = ThirdPartyService()
        client_id = "client_error_test"
        client_data = {"company_name": "Error Test", "email": "error@test.com", "phone": "+1-555-123-4567"}
        ai_analysis = {"company_size": "small"}
        
        with patch.object(service, '_optimize_mls_config', side_effect=Exception("MLS config error")):
            with pytest.raises(Exception):
                await service.create_mls_account(client_id, client_data, ai_analysis)