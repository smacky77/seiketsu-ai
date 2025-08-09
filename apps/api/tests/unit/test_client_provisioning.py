"""
Unit tests for Client Provisioning Service
Tests comprehensive client onboarding with infrastructure automation
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from app.services.client_provisioning import ClientProvisioningService
from app.models.client import ProvisioningStatus


class TestClientProvisioningService:
    """Comprehensive unit tests for ClientProvisioningService"""
    
    @pytest.fixture
    def service(self):
        """Create ClientProvisioningService instance with mocked dependencies"""
        with patch('app.services.client_provisioning.AIProvisioningService') as mock_ai, \
             patch('app.services.client_provisioning.ThirdPartyService') as mock_third_party, \
             patch('app.services.client_provisioning.UsageTrackingService') as mock_usage:
            
            service = ClientProvisioningService()
            service.ai_service = mock_ai.return_value
            service.third_party_service = mock_third_party.return_value
            service.usage_service = mock_usage.return_value
            
            # Mock external dependencies
            service.aws_session = Mock()
            service.terraform_path = Mock()
            
            return service
    
    @pytest.fixture
    def valid_client_data(self):
        """Valid client data for testing"""
        return {
            "company_name": "Test Real Estate Co",
            "email": "admin@testrealestate.com",
            "phone": "+1-555-123-4567",
            "website": "https://testrealestate.com",
            "industry": "Real Estate",
            "agent_count": 5,
            "crm_type": "salesforce",
            "calendar_type": "google",
            "subscription_tier": "silver"
        }
    
    @pytest.fixture
    def mock_ai_analysis(self):
        """Mock AI analysis result"""
        return {
            "company_size": "medium",
            "resource_needs": {
                "instance_type": "t3.small",
                "database_size": "db.t3.small",
                "auto_scaling": {"min": 2, "desired": 3, "max": 5}
            },
            "integration_priorities": ["voice", "sms"],
            "usage_prediction": {
                "daily_voice_calls": 100,
                "monthly_sms": 2000,
                "weekly_mls_queries": 400
            }
        }
    
    # Validation Tests
    @pytest.mark.asyncio
    async def test_validate_and_create_client_success(self, service, valid_client_data):
        """Test successful client validation and creation"""
        with patch.object(service, '_save_client_record', new_callable=AsyncMock) as mock_save:
            client_id = await service._validate_and_create_client(valid_client_data)
            
            assert client_id.startswith("client_")
            assert len(client_id) == 19  # "client_" + 12 hex chars
            mock_save.assert_called_once()
            
            # Verify saved data structure
            saved_data = mock_save.call_args[0][0]
            assert saved_data["company_name"] == valid_client_data["company_name"]
            assert saved_data["email"] == valid_client_data["email"]
            assert saved_data["status"] == ProvisioningStatus.CREATED
    
    @pytest.mark.asyncio
    async def test_validate_missing_required_fields(self, service):
        """Test validation failure for missing required fields"""
        incomplete_data = {"company_name": "Test Co"}
        
        with pytest.raises(ValueError, match="Missing required field: email"):
            await service._validate_and_create_client(incomplete_data)
    
    @pytest.mark.asyncio
    async def test_validate_invalid_email_format(self, service):
        """Test validation failure for invalid email"""
        invalid_data = {
            "company_name": "Test Co",
            "email": "invalid-email",
            "phone": "+1-555-123-4567"
        }
        
        with patch('app.services.client_provisioning.validate_email', return_value=False):
            with pytest.raises(ValueError, match="Invalid email format"):
                await service._validate_and_create_client(invalid_data)
    
    @pytest.mark.asyncio
    async def test_validate_invalid_phone_format(self, service):
        """Test validation failure for invalid phone"""
        invalid_data = {
            "company_name": "Test Co",
            "email": "test@example.com",
            "phone": "invalid-phone"
        }
        
        with patch('app.services.client_provisioning.validate_email', return_value=True), \
             patch('app.services.client_provisioning.validate_phone', return_value=False):
            with pytest.raises(ValueError, match="Invalid phone format"):
                await service._validate_and_create_client(invalid_data)
    
    @pytest.mark.asyncio
    async def test_validate_invalid_website_url(self, service):
        """Test validation failure for invalid website URL"""
        invalid_data = {
            "company_name": "Test Co",
            "email": "test@example.com",
            "phone": "+1-555-123-4567",
            "website": "invalid-url"
        }
        
        with patch('app.services.client_provisioning.validate_email', return_value=True), \
             patch('app.services.client_provisioning.validate_phone', return_value=True), \
             patch('app.services.client_provisioning.validate_url', return_value=False):
            with pytest.raises(ValueError, match="Invalid website URL"):
                await service._validate_and_create_client(invalid_data)
    
    # Provisioning Status Tests
    @pytest.mark.asyncio
    async def test_update_provisioning_status(self, service):
        """Test provisioning status updates"""
        client_id = "client_test123"
        status = ProvisioningStatus.ANALYZING
        
        with patch.object(service, '_save_client_record', new_callable=AsyncMock):
            await service._update_provisioning_status(client_id, status)
            # Test passes if no exception is raised
    
    # Infrastructure Provisioning Tests
    @pytest.mark.asyncio
    async def test_provision_aws_infrastructure_success(self, service, valid_client_data, mock_ai_analysis):
        """Test successful AWS infrastructure provisioning"""
        client_id = "client_test123"
        
        with patch.object(service, '_run_terraform_command', new_callable=AsyncMock) as mock_terraform, \
             patch.object(service, '_get_terraform_outputs', new_callable=AsyncMock) as mock_outputs, \
             patch('builtins.open', mock_open()):
            
            mock_outputs.return_value = {
                "client_alb_dns_name": {"value": "test-alb.us-east-1.elb.amazonaws.com"},
                "client_db_endpoint": {"value": "test-db.cluster.amazonaws.com"},
                "client_redis_endpoint": {"value": "test-redis.cache.amazonaws.com"}
            }
            
            result = await service._provision_aws_infrastructure(client_id, valid_client_data, mock_ai_analysis)
            
            # Verify terraform commands called
            assert mock_terraform.call_count == 3  # init, plan, apply
            mock_terraform.assert_any_call("init", client_id)
            mock_terraform.assert_any_call("plan", client_id)
            mock_terraform.assert_any_call("apply", client_id)
            
            # Verify result structure
            assert result["infrastructure_status"] == "provisioned"
            assert "terraform_outputs" in result
            assert "resources_created" in result
            assert len(result["resources_created"]) > 0
    
    @pytest.mark.asyncio
    async def test_terraform_command_execution(self, service):
        """Test Terraform command execution"""
        client_id = "client_test123"
        
        with patch('subprocess.run') as mock_subprocess, \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "Success"
            mock_subprocess.return_value.stderr = ""
            
            result = await service._run_terraform_command("init", client_id)
            
            assert result["stdout"] == "Success"
            mock_subprocess.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_terraform_command_failure(self, service):
        """Test Terraform command failure handling"""
        client_id = "client_test123"
        
        with patch('subprocess.run') as mock_subprocess, \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            mock_subprocess.return_value.returncode = 1
            mock_subprocess.return_value.stderr = "Terraform error"
            
            with pytest.raises(Exception, match="Terraform init failed: Terraform error"):
                await service._run_terraform_command("init", client_id)
    
    # Third-Party Account Creation Tests
    @pytest.mark.asyncio
    async def test_create_third_party_accounts_success(self, service, valid_client_data, mock_ai_analysis):
        """Test successful third-party account creation"""
        client_id = "client_test123"
        
        mock_accounts = {
            "elevenlabs": {"account_id": "elevenlabs_test", "api_key": "sk_test"},
            "twilio": {"account_id": "twilio_test", "phone_number": "+1-555-999-0000"}
        }
        
        service.third_party_service.create_elevenlabs_account = AsyncMock(return_value=mock_accounts["elevenlabs"])
        service.third_party_service.create_twilio_account = AsyncMock(return_value=mock_accounts["twilio"])
        
        with patch.object(service, '_store_third_party_accounts', new_callable=AsyncMock) as mock_store:
            result = await service._create_third_party_accounts(client_id, valid_client_data, mock_ai_analysis)
            
            assert "elevenlabs" in result
            assert "twilio" in result
            mock_store.assert_called_once_with(client_id, result)
    
    @pytest.mark.asyncio
    async def test_store_third_party_accounts(self, service):
        """Test third-party account storage"""
        client_id = "client_test123"
        accounts = {
            "elevenlabs": {
                "account_id": "elevenlabs_test",
                "credentials": {"api_key": "sk_test"}
            }
        }
        
        with patch('app.services.client_provisioning.encrypt_sensitive_data') as mock_encrypt:
            mock_encrypt.return_value = "encrypted_data"
            
            await service._store_third_party_accounts(client_id, accounts)
            mock_encrypt.assert_called_once()
    
    # Integration Configuration Tests
    @pytest.mark.asyncio
    async def test_configure_crm_integration(self, service, valid_client_data):
        """Test CRM integration configuration"""
        client_id = "client_test123"
        
        result = await service._configure_crm_integration(client_id, valid_client_data)
        
        assert result["client_id"] == client_id
        assert "api_version" in result
        assert "endpoints" in result
        assert "auth_type" in result
        assert "configured_at" in result
    
    @pytest.mark.asyncio
    async def test_configure_calendar_integration(self, service, valid_client_data):
        """Test calendar integration configuration"""
        client_id = "client_test123"
        
        result = await service._configure_calendar_integration(client_id, valid_client_data)
        
        assert result["client_id"] == client_id
        assert "api_version" in result
        assert "scopes" in result
        assert "endpoints" in result
    
    @pytest.mark.asyncio
    async def test_configure_voice_agent(self, service):
        """Test voice agent configuration"""
        client_id = "client_test123"
        third_party_accounts = {
            "elevenlabs": {"account_id": "elevenlabs_test"},
            "twilio": {"account_id": "twilio_test", "phone_number": "+1-555-999-0000"}
        }
        
        result = await service._configure_voice_agent(client_id, third_party_accounts)
        
        assert result["client_id"] == client_id
        assert result["voice_provider"] == "elevenlabs"
        assert result["sms_provider"] == "twilio"
        assert "features" in result
        assert "ai_settings" in result
        assert "business_hours" in result
        assert result["elevenlabs_account"] == "elevenlabs_test"
        assert result["phone_number"] == "+1-555-999-0000"
    
    @pytest.mark.asyncio
    async def test_configure_webhooks(self, service, valid_client_data):
        """Test webhook configuration"""
        client_id = "client_test123"
        
        result = await service._configure_webhooks(client_id, valid_client_data)
        
        assert result["client_id"] == client_id
        assert result["base_url"] == f"https://{client_id}.seiketsu.ai"
        assert "endpoints" in result
        assert "security" in result
        assert result["security"]["signature_verification"] is True
        assert len(result["security"]["webhook_secret"]) > 20
    
    # Application Deployment Tests
    @pytest.mark.asyncio
    async def test_deploy_application(self, service, valid_client_data):
        """Test application deployment"""
        client_id = "client_test123"
        infrastructure_result = {
            "terraform_outputs": {
                "client_bucket_name": {"value": "seiketsu-client-test123"},
                "client_alb_dns_name": {"value": "test-alb.us-east-1.elb.amazonaws.com"},
                "client_db_endpoint": {"value": "test-db.cluster.amazonaws.com"},
                "client_redis_endpoint": {"value": "test-redis.cache.amazonaws.com"}
            }
        }
        
        with patch.object(service, '_execute_deployment', new_callable=AsyncMock) as mock_deploy:
            mock_deploy.return_value = {
                "deployment_id": "deploy_test123",
                "status": "completed"
            }
            
            result = await service._deploy_application(client_id, valid_client_data, infrastructure_result)
            
            mock_deploy.assert_called_once()
            assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_build_database_url(self, service):
        """Test database URL construction"""
        terraform_outputs = {
            "client_db_endpoint": {"value": "test-db.cluster.amazonaws.com"},
            "client_id": "test123"
        }
        
        url = service._build_database_url(terraform_outputs)
        
        assert "postgresql://" in url
        assert "test-db.cluster.amazonaws.com" in url
        assert ":5432/" in url
    
    @pytest.mark.asyncio
    async def test_build_redis_url(self, service):
        """Test Redis URL construction"""
        terraform_outputs = {
            "client_redis_endpoint": {"value": "test-redis.cache.amazonaws.com"}
        }
        
        url = service._build_redis_url(terraform_outputs)
        
        assert url == "redis://test-redis.cache.amazonaws.com:6379"
    
    # Validation Tests
    @pytest.mark.asyncio
    async def test_run_validation_tests_success(self, service):
        """Test successful validation test execution"""
        client_id = "client_test123"
        deployment_result = {"application_url": "https://client_test123.seiketsu.ai"}
        
        with patch.object(service, '_test_health_endpoint', new_callable=AsyncMock) as mock_health, \
             patch.object(service, '_test_database_connection', new_callable=AsyncMock) as mock_db, \
             patch.object(service, '_test_redis_connection', new_callable=AsyncMock) as mock_redis, \
             patch.object(service, '_test_api_endpoints', new_callable=AsyncMock) as mock_api, \
             patch.object(service, '_test_integrations', new_callable=AsyncMock) as mock_integrations:
            
            # Mock all tests to pass
            mock_health.return_value = {"status": "passed"}
            mock_db.return_value = {"status": "passed"}
            mock_redis.return_value = {"status": "passed"}
            mock_api.return_value = {"status": "passed"}
            mock_integrations.return_value = {"status": "passed"}
            
            result = await service._run_validation_tests(client_id, deployment_result)
            
            assert result["overall_status"] == "passed"
            assert result["tests_run"] == 5
            assert result["tests_passed"] == 5
    
    @pytest.mark.asyncio
    async def test_run_validation_tests_failure(self, service):
        """Test validation test execution with failures"""
        client_id = "client_test123"
        deployment_result = {"application_url": "https://client_test123.seiketsu.ai"}
        
        with patch.object(service, '_test_health_endpoint', new_callable=AsyncMock) as mock_health, \
             patch.object(service, '_test_database_connection', new_callable=AsyncMock) as mock_db, \
             patch.object(service, '_test_redis_connection', new_callable=AsyncMock) as mock_redis, \
             patch.object(service, '_test_api_endpoints', new_callable=AsyncMock) as mock_api, \
             patch.object(service, '_test_integrations', new_callable=AsyncMock) as mock_integrations:
            
            # Mock some tests to fail
            mock_health.return_value = {"status": "passed"}
            mock_db.return_value = {"status": "failed", "error": "Connection timeout"}
            mock_redis.return_value = {"status": "passed"}
            mock_api.return_value = {"status": "failed", "error": "404 Not Found"}
            mock_integrations.return_value = {"status": "passed"}
            
            result = await service._run_validation_tests(client_id, deployment_result)
            
            assert result["overall_status"] == "failed"
            assert result["tests_run"] == 5
            assert result["tests_passed"] == 3
    
    # Complete Provisioning Flow Tests
    @pytest.mark.asyncio
    async def test_provision_client_instance_success(self, service, valid_client_data, mock_ai_analysis):
        """Test complete client provisioning flow success"""
        with patch.object(service, '_validate_and_create_client', new_callable=AsyncMock) as mock_validate, \
             patch.object(service.ai_service, '_analyze_client_requirements', new_callable=AsyncMock) as mock_ai, \
             patch.object(service, '_update_provisioning_status', new_callable=AsyncMock), \
             patch.object(service, '_provision_aws_infrastructure', new_callable=AsyncMock) as mock_infra, \
             patch.object(service, '_create_third_party_accounts', new_callable=AsyncMock) as mock_accounts, \
             patch.object(service, '_configure_integrations', new_callable=AsyncMock) as mock_integrations, \
             patch.object(service, '_deploy_application', new_callable=AsyncMock) as mock_deploy, \
             patch.object(service, '_run_validation_tests', new_callable=AsyncMock) as mock_validate_tests, \
             patch.object(service.usage_service, 'initialize_client_tracking', new_callable=AsyncMock), \
             patch.object(service, '_send_welcome_notification', new_callable=AsyncMock):
            
            # Setup mocks
            mock_validate.return_value = "client_test123"
            mock_ai.return_value = mock_ai_analysis
            mock_infra.return_value = {"terraform_outputs": {}, "infrastructure_status": "provisioned"}
            mock_accounts.return_value = {"elevenlabs": {}, "twilio": {}}
            mock_integrations.return_value = {"crm": {}, "voice_agent": {}}
            mock_deploy.return_value = {"deployment_id": "deploy_test123", "application_url": "https://client_test123.seiketsu.ai"}
            mock_validate_tests.return_value = {"overall_status": "passed"}
            
            result = await service.provision_client_instance(valid_client_data)
            
            assert result["client_id"] == "client_test123"
            assert result["status"] == "completed"
            assert "ai_analysis" in result
            assert "infrastructure" in result
            assert "third_party_accounts" in result
            assert "integrations" in result
            assert "deployment" in result
            assert "validation" in result
            assert "endpoints" in result
    
    @pytest.mark.asyncio
    async def test_provision_client_instance_failure_with_rollback(self, service, valid_client_data):
        """Test client provisioning failure with rollback"""
        with patch.object(service, '_validate_and_create_client', new_callable=AsyncMock) as mock_validate, \
             patch.object(service.ai_service, '_analyze_client_requirements', new_callable=AsyncMock), \
             patch.object(service, '_update_provisioning_status', new_callable=AsyncMock), \
             patch.object(service, '_provision_aws_infrastructure', new_callable=AsyncMock) as mock_infra, \
             patch.object(service, '_rollback_provisioning', new_callable=AsyncMock) as mock_rollback:
            
            mock_validate.return_value = "client_test123"
            mock_infra.side_effect = Exception("Infrastructure provisioning failed")
            
            with pytest.raises(Exception):
                await service.provision_client_instance(valid_client_data)
            
            mock_rollback.assert_called_once_with("client_test123")
    
    # Rollback Tests
    @pytest.mark.asyncio
    async def test_rollback_provisioning(self, service):
        """Test provisioning rollback"""
        client_id = "client_test123"
        
        with patch.object(service, '_update_provisioning_status', new_callable=AsyncMock), \
             patch.object(service, '_run_terraform_command', new_callable=AsyncMock) as mock_terraform, \
             patch.object(service.third_party_service, 'cleanup_accounts', new_callable=AsyncMock) as mock_cleanup:
            
            await service._rollback_provisioning(client_id)
            
            mock_terraform.assert_called_once_with("destroy", client_id)
            mock_cleanup.assert_called_once_with(client_id)
    
    @pytest.mark.asyncio
    async def test_rollback_provisioning_with_failures(self, service):
        """Test rollback provisioning with partial failures"""
        client_id = "client_test123"
        
        with patch.object(service, '_update_provisioning_status', new_callable=AsyncMock), \
             patch.object(service, '_run_terraform_command', new_callable=AsyncMock) as mock_terraform, \
             patch.object(service.third_party_service, 'cleanup_accounts', new_callable=AsyncMock) as mock_cleanup:
            
            # Mock terraform destroy to fail, but cleanup to succeed
            mock_terraform.side_effect = Exception("Terraform destroy failed")
            
            # Should not raise exception, but handle gracefully
            await service._rollback_provisioning(client_id)
            
            mock_terraform.assert_called_once_with("destroy", client_id)
            mock_cleanup.assert_called_once_with(client_id)
    
    # Client Management Tests
    @pytest.mark.asyncio
    async def test_get_client_status(self, service):
        """Test getting client provisioning status"""
        client_id = "client_test123"
        
        result = await service.get_client_status(client_id)
        
        assert result["client_id"] == client_id
        assert "status" in result
        assert "progress" in result
        assert "last_updated" in result
    
    @pytest.mark.asyncio
    async def test_suspend_client(self, service):
        """Test client suspension"""
        client_id = "client_test123"
        
        result = await service.suspend_client(client_id)
        
        assert result["client_id"] == client_id
        assert result["action"] == "suspended"
        assert result["success"] is True
        assert "suspended_at" in result
    
    @pytest.mark.asyncio
    async def test_reactivate_client(self, service):
        """Test client reactivation"""
        client_id = "client_test123"
        
        result = await service.reactivate_client(client_id)
        
        assert result["client_id"] == client_id
        assert result["action"] == "reactivated"
        assert result["success"] is True
        assert "reactivated_at" in result


def mock_open(mock_data=""):
    """Helper function to create mock file operations"""
    return MagicMock(
        return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock(write=MagicMock())),
            __exit__=MagicMock(return_value=None)
        )
    )


# Performance Tests
class TestClientProvisioningPerformance:
    """Performance tests for client provisioning service"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_validate_client_data_performance(self, benchmark):
        """Benchmark client data validation performance"""
        service = ClientProvisioningService()
        client_data = {
            "company_name": "Performance Test Co",
            "email": "test@performance.com",
            "phone": "+1-555-123-4567"
        }
        
        with patch.object(service, '_save_client_record', new_callable=AsyncMock), \
             patch('app.services.client_provisioning.validate_email', return_value=True), \
             patch('app.services.client_provisioning.validate_phone', return_value=True):
            
            # Benchmark should complete within 100ms
            result = await benchmark(service._validate_and_create_client, client_data)
            assert result.startswith("client_")


# Edge Case Tests
class TestClientProvisioningEdgeCases:
    """Edge case tests for client provisioning"""
    
    @pytest.mark.asyncio
    async def test_provision_with_unicode_company_name(self):
        """Test provisioning with Unicode characters in company name"""
        service = ClientProvisioningService()
        client_data = {
            "company_name": "测试房地产公司 Real Estate",
            "email": "test@unicode.com",
            "phone": "+1-555-123-4567"
        }
        
        with patch.object(service, '_save_client_record', new_callable=AsyncMock), \
             patch('app.services.client_provisioning.validate_email', return_value=True), \
             patch('app.services.client_provisioning.validate_phone', return_value=True):
            
            client_id = await service._validate_and_create_client(client_data)
            assert client_id.startswith("client_")
    
    @pytest.mark.asyncio
    async def test_provision_with_minimal_data(self):
        """Test provisioning with minimal required data"""
        service = ClientProvisioningService()
        minimal_data = {
            "company_name": "Minimal Co",
            "email": "minimal@test.com",
            "phone": "+1-555-123-4567"
        }
        
        with patch.object(service, '_save_client_record', new_callable=AsyncMock), \
             patch('app.services.client_provisioning.validate_email', return_value=True), \
             patch('app.services.client_provisioning.validate_phone', return_value=True):
            
            client_id = await service._validate_and_create_client(minimal_data)
            assert client_id.startswith("client_")
    
    @pytest.mark.asyncio
    async def test_provision_with_maximum_agent_count(self):
        """Test provisioning with large agent count"""
        service = ClientProvisioningService()
        client_data = {
            "company_name": "Large Enterprise",
            "email": "admin@large.com",
            "phone": "+1-555-123-4567",
            "agent_count": 1000
        }
        
        with patch.object(service, '_save_client_record', new_callable=AsyncMock), \
             patch('app.services.client_provisioning.validate_email', return_value=True), \
             patch('app.services.client_provisioning.validate_phone', return_value=True):
            
            client_id = await service._validate_and_create_client(client_data)
            assert client_id.startswith("client_")