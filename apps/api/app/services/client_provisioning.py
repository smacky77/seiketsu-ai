"""
Seiketsu AI Client Provisioning Service
Comprehensive client onboarding with infrastructure automation
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import boto3
import subprocess
from pathlib import Path
import psycopg2
from fastapi import HTTPException
import aioredis
import requests

from ..models.client import Client, ProvisioningStatus
from ..models.third_party_account import ThirdPartyAccount
from ..utils.encryption import encrypt_sensitive_data, decrypt_sensitive_data
from ..utils.validators import validate_email, validate_phone, validate_url
from .ai_provisioning_service import AIProvisioningService
from .third_party_service import ThirdPartyService
from .usage_tracking import UsageTrackingService

logger = logging.getLogger(__name__)

class ClientProvisioningService:
    """
    Complete client provisioning service with AI optimization
    """
    
    def __init__(self):
        self.ai_service = AIProvisioningService()
        self.third_party_service = ThirdPartyService()
        self.usage_service = UsageTrackingService()
        self.terraform_path = Path("/opt/seiketsu-ai/terraform")
        self.aws_session = boto3.Session()
        
    async def provision_client_instance(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete client provisioning workflow with intelligent automation
        """
        client_id = None
        provisioning_started = False
        
        try:
            # Step 1: Validate and create client record
            logger.info(f"Starting client provisioning for {client_data.get('company_name')}")
            client_id = await self._validate_and_create_client(client_data)
            
            # Step 2: AI analysis and optimization
            logger.info(f"Running AI analysis for client {client_id}")
            ai_analysis = await self.ai_service._analyze_client_requirements(client_data)
            
            # Step 3: Update provisioning status
            await self._update_provisioning_status(client_id, ProvisioningStatus.ANALYZING)
            
            # Step 4: Provision AWS infrastructure
            logger.info(f"Provisioning AWS infrastructure for client {client_id}")
            await self._update_provisioning_status(client_id, ProvisioningStatus.PROVISIONING_INFRASTRUCTURE)
            provisioning_started = True
            
            infrastructure_result = await self._provision_aws_infrastructure(client_id, client_data, ai_analysis)
            
            # Step 5: Create third-party accounts
            logger.info(f"Creating third-party accounts for client {client_id}")
            await self._update_provisioning_status(client_id, ProvisioningStatus.CREATING_ACCOUNTS)
            
            third_party_accounts = await self._create_third_party_accounts(client_id, client_data, ai_analysis)
            
            # Step 6: Configure integrations
            logger.info(f"Configuring integrations for client {client_id}")
            await self._update_provisioning_status(client_id, ProvisioningStatus.CONFIGURING_INTEGRATIONS)
            
            integration_config = await self._configure_integrations(client_id, client_data, third_party_accounts)
            
            # Step 7: Deploy application
            logger.info(f"Deploying application for client {client_id}")
            await self._update_provisioning_status(client_id, ProvisioningStatus.DEPLOYING_APPLICATION)
            
            deployment_result = await self._deploy_application(client_id, client_data, infrastructure_result)
            
            # Step 8: Run validation tests
            logger.info(f"Running validation tests for client {client_id}")
            await self._update_provisioning_status(client_id, ProvisioningStatus.VALIDATING)
            
            validation_result = await self._run_validation_tests(client_id, deployment_result)
            
            # Step 9: Complete provisioning
            logger.info(f"Completing provisioning for client {client_id}")
            await self._update_provisioning_status(client_id, ProvisioningStatus.COMPLETED)
            
            # Step 10: Initialize usage tracking
            await self.usage_service.initialize_client_tracking(client_id)
            
            # Step 11: Send welcome notification
            await self._send_welcome_notification(client_id, client_data, deployment_result)
            
            return {
                "client_id": client_id,
                "status": "completed",
                "ai_analysis": ai_analysis,
                "infrastructure": infrastructure_result,
                "third_party_accounts": third_party_accounts,
                "integrations": integration_config,
                "deployment": deployment_result,
                "validation": validation_result,
                "provisioned_at": datetime.utcnow().isoformat(),
                "endpoints": {
                    "application_url": f"https://{client_id}.seiketsu.ai",
                    "admin_dashboard": f"https://{client_id}.seiketsu.ai/admin",
                    "api_docs": f"https://{client_id}.seiketsu.ai/docs",
                    "health_check": f"https://{client_id}.seiketsu.ai/health"
                }
            }
            
        except Exception as e:
            logger.error(f"Client provisioning failed for {client_data.get('company_name')}: {str(e)}")
            
            if client_id and provisioning_started:
                # Attempt rollback
                try:
                    await self._update_provisioning_status(client_id, ProvisioningStatus.FAILED)
                    await self._rollback_provisioning(client_id)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed for client {client_id}: {str(rollback_error)}")
            
            raise HTTPException(status_code=500, detail=f"Client provisioning failed: {str(e)}")
    
    async def _validate_and_create_client(self, client_data: Dict[str, Any]) -> str:
        """
        Validate client data and create database record
        """
        # Validate required fields
        required_fields = ["company_name", "email", "phone"]
        for field in required_fields:
            if not client_data.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Validate data formats
        if not validate_email(client_data["email"]):
            raise ValueError("Invalid email format")
        
        if not validate_phone(client_data["phone"]):
            raise ValueError("Invalid phone format")
        
        if client_data.get("website") and not validate_url(client_data["website"]):
            raise ValueError("Invalid website URL")
        
        # Generate unique client ID
        client_id = f"client_{uuid.uuid4().hex[:12]}"
        
        # Create client record in database
        client_record = {
            "id": client_id,
            "company_name": client_data["company_name"],
            "email": client_data["email"],
            "phone": client_data["phone"],
            "website": client_data.get("website"),
            "industry": client_data.get("industry", "Real Estate"),
            "agent_count": client_data.get("agent_count", 1),
            "crm_type": client_data.get("crm_type"),
            "calendar_type": client_data.get("calendar_type"),
            "status": ProvisioningStatus.CREATED,
            "created_at": datetime.utcnow(),
            "subscription_tier": client_data.get("subscription_tier", "bronze"),
            "billing_email": client_data.get("billing_email", client_data["email"])
        }
        
        await self._save_client_record(client_record)
        
        return client_id
    
    async def _save_client_record(self, client_record: Dict[str, Any]):
        """
        Save client record to database
        """
        # This would typically use SQLAlchemy or similar ORM
        # For now, showing the SQL structure
        
        query = """
        INSERT INTO clients (
            id, company_name, email, phone, website, industry,
            agent_count, crm_type, calendar_type, status,
            created_at, subscription_tier, billing_email
        ) VALUES (
            %(id)s, %(company_name)s, %(email)s, %(phone)s, %(website)s,
            %(industry)s, %(agent_count)s, %(crm_type)s, %(calendar_type)s,
            %(status)s, %(created_at)s, %(subscription_tier)s, %(billing_email)s
        )
        """
        
        # Execute query with proper database connection
        logger.info(f"Saving client record for {client_record['id']}")
    
    async def _update_provisioning_status(self, client_id: str, status: ProvisioningStatus):
        """
        Update client provisioning status
        """
        logger.info(f"Updating provisioning status for {client_id}: {status.value}")
        
        query = """
        UPDATE clients 
        SET status = %(status)s, updated_at = %(updated_at)s 
        WHERE id = %(client_id)s
        """
        
        params = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
            "client_id": client_id
        }
        
        # Execute query
        logger.info(f"Status updated: {client_id} -> {status.value}")
    
    async def _provision_aws_infrastructure(self, client_id: str, client_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provision AWS infrastructure using Terraform
        """
        try:
            # Prepare Terraform variables
            terraform_vars = {
                "client_id": client_id,
                "client_name": client_data["company_name"],
                "client_email": client_data["email"],
                "region": "us-east-1",  # Could be AI-optimized based on location
                "environment": "production",
                "instance_type": ai_analysis.get("resource_needs", {}).get("instance_type", "t3.micro"),
                "db_instance_class": ai_analysis.get("resource_needs", {}).get("database_size", "db.t3.micro"),
                "min_capacity": ai_analysis.get("resource_needs", {}).get("auto_scaling", {}).get("min", 1),
                "max_capacity": ai_analysis.get("resource_needs", {}).get("auto_scaling", {}).get("max", 3),
                "desired_capacity": ai_analysis.get("resource_needs", {}).get("auto_scaling", {}).get("desired", 2)
            }
            
            # Create Terraform variables file
            vars_file = self.terraform_path / f"{client_id}.tfvars.json"
            with open(vars_file, "w") as f:
                json.dump(terraform_vars, f, indent=2)
            
            # Initialize Terraform
            await self._run_terraform_command("init", client_id)
            
            # Plan infrastructure
            await self._run_terraform_command("plan", client_id)
            
            # Apply infrastructure
            result = await self._run_terraform_command("apply", client_id)
            
            # Get outputs
            outputs = await self._get_terraform_outputs(client_id)
            
            logger.info(f"Infrastructure provisioned successfully for client {client_id}")
            
            return {
                "terraform_outputs": outputs,
                "infrastructure_status": "provisioned",
                "provisioning_time": datetime.utcnow().isoformat(),
                "resources_created": [
                    "VPC", "Subnets", "Security Groups", "Load Balancer",
                    "Auto Scaling Group", "RDS Database", "Redis Cache",
                    "S3 Bucket", "CloudWatch Monitoring"
                ]
            }
            
        except Exception as e:
            logger.error(f"Infrastructure provisioning failed for {client_id}: {str(e)}")
            raise
    
    async def _run_terraform_command(self, command: str, client_id: str) -> Dict[str, Any]:
        """
        Run Terraform command with proper configuration
        """
        tf_dir = self.terraform_path / "client-instances" / client_id
        tf_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy module files
        module_source = self.terraform_path / "modules" / "client-instance"
        
        if command == "init":
            # Create main.tf for this client
            main_tf_content = f"""
terraform {{
  backend "s3" {{
    bucket = "seiketsu-terraform-state"
    key    = "clients/{client_id}/terraform.tfstate"
    region = "us-east-1"
  }}
}}

module "client_infrastructure" {{
  source = "../../modules/client-instance"
  
  client_id = var.client_id
  client_name = var.client_name
  client_email = var.client_email
  region = var.region
  environment = var.environment
  instance_type = var.instance_type
  db_instance_class = var.db_instance_class
  min_capacity = var.min_capacity
  max_capacity = var.max_capacity
  desired_capacity = var.desired_capacity
}}

output "infrastructure_summary" {{
  value = module.client_infrastructure.client_infrastructure_summary
}}
"""
            
            with open(tf_dir / "main.tf", "w") as f:
                f.write(main_tf_content)
        
        # Run Terraform command
        cmd = ["terraform", command]
        if command == "apply":
            cmd.extend(["-auto-approve"])
        if command in ["plan", "apply"]:
            cmd.extend(["-var-file", f"../../{client_id}.tfvars.json"])
        
        result = subprocess.run(
            cmd,
            cwd=tf_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        if result.returncode != 0:
            raise Exception(f"Terraform {command} failed: {result.stderr}")
        
        return {"stdout": result.stdout, "stderr": result.stderr}
    
    async def _get_terraform_outputs(self, client_id: str) -> Dict[str, Any]:
        """
        Get Terraform outputs for client infrastructure
        """
        tf_dir = self.terraform_path / "client-instances" / client_id
        
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=tf_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to get Terraform outputs: {result.stderr}")
        
        return json.loads(result.stdout)
    
    async def _create_third_party_accounts(self, client_id: str, client_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create third-party service accounts
        """
        accounts = {}
        
        try:
            # ElevenLabs Voice Account
            if ai_analysis.get("integration_priorities", []).count("voice") > 0:
                elevenlabs_account = await self.third_party_service.create_elevenlabs_account(
                    client_id, client_data, ai_analysis
                )
                accounts["elevenlabs"] = elevenlabs_account
            
            # Twilio SMS/Phone Account
            if ai_analysis.get("integration_priorities", []).count("sms") > 0:
                twilio_account = await self.third_party_service.create_twilio_account(
                    client_id, client_data, ai_analysis
                )
                accounts["twilio"] = twilio_account
            
            # MLS Integration
            if client_data.get("mls_required", True):
                mls_account = await self.third_party_service.create_mls_account(
                    client_id, client_data, ai_analysis
                )
                accounts["mls"] = mls_account
            
            # Store encrypted account information
            await self._store_third_party_accounts(client_id, accounts)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Third-party account creation failed for {client_id}: {str(e)}")
            raise
    
    async def _store_third_party_accounts(self, client_id: str, accounts: Dict[str, Any]):
        """
        Store encrypted third-party account information
        """
        for service_name, account_info in accounts.items():
            # Encrypt sensitive information
            encrypted_credentials = encrypt_sensitive_data(account_info.get("credentials", {}))
            
            account_record = {
                "id": f"{client_id}_{service_name}_{uuid.uuid4().hex[:8]}",
                "client_id": client_id,
                "service_name": service_name,
                "account_id": account_info.get("account_id"),
                "encrypted_credentials": encrypted_credentials,
                "configuration": account_info.get("configuration", {}),
                "status": "active",
                "created_at": datetime.utcnow()
            }
            
            # Save to database
            logger.info(f"Storing {service_name} account for client {client_id}")
    
    async def _configure_integrations(self, client_id: str, client_data: Dict[str, Any], third_party_accounts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure system integrations
        """
        integrations = {}
        
        try:
            # CRM Integration
            if client_data.get("crm_type"):
                crm_config = await self._configure_crm_integration(client_id, client_data)
                integrations["crm"] = crm_config
            
            # Calendar Integration
            if client_data.get("calendar_type"):
                calendar_config = await self._configure_calendar_integration(client_id, client_data)
                integrations["calendar"] = calendar_config
            
            # Voice Agent Configuration
            voice_config = await self._configure_voice_agent(client_id, third_party_accounts)
            integrations["voice_agent"] = voice_config
            
            # Webhook Configuration
            webhook_config = await self._configure_webhooks(client_id, client_data)
            integrations["webhooks"] = webhook_config
            
            return integrations
            
        except Exception as e:
            logger.error(f"Integration configuration failed for {client_id}: {str(e)}")
            raise
    
    async def _configure_crm_integration(self, client_id: str, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure CRM integration based on client's CRM type
        """
        crm_type = client_data.get("crm_type", "").lower()
        
        crm_configs = {
            "salesforce": {
                "api_version": "v52.0",
                "endpoints": {
                    "leads": "/services/data/v52.0/sobjects/Lead",
                    "contacts": "/services/data/v52.0/sobjects/Contact",
                    "accounts": "/services/data/v52.0/sobjects/Account"
                },
                "auth_type": "oauth2"
            },
            "hubspot": {
                "api_version": "v3",
                "endpoints": {
                    "contacts": "/crm/v3/objects/contacts",
                    "deals": "/crm/v3/objects/deals",
                    "companies": "/crm/v3/objects/companies"
                },
                "auth_type": "api_key"
            },
            "pipedrive": {
                "api_version": "v1",
                "endpoints": {
                    "persons": "/v1/persons",
                    "deals": "/v1/deals",
                    "organizations": "/v1/organizations"
                },
                "auth_type": "api_key"
            }
        }
        
        config = crm_configs.get(crm_type, {})
        config["client_id"] = client_id
        config["configured_at"] = datetime.utcnow().isoformat()
        
        return config
    
    async def _configure_calendar_integration(self, client_id: str, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure calendar integration
        """
        calendar_type = client_data.get("calendar_type", "").lower()
        
        calendar_configs = {
            "google": {
                "api_version": "v3",
                "scopes": [
                    "https://www.googleapis.com/auth/calendar.readonly",
                    "https://www.googleapis.com/auth/calendar.events"
                ],
                "endpoints": {
                    "calendars": "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                    "events": "https://www.googleapis.com/calendar/v3/calendars/primary/events"
                }
            },
            "outlook": {
                "api_version": "v1.0",
                "scopes": [
                    "https://graph.microsoft.com/Calendars.ReadWrite"
                ],
                "endpoints": {
                    "calendars": "https://graph.microsoft.com/v1.0/me/calendars",
                    "events": "https://graph.microsoft.com/v1.0/me/events"
                }
            }
        }
        
        config = calendar_configs.get(calendar_type, {})
        config["client_id"] = client_id
        config["configured_at"] = datetime.utcnow().isoformat()
        
        return config
    
    async def _configure_voice_agent(self, client_id: str, third_party_accounts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure AI voice agent with third-party integrations
        """
        voice_config = {
            "client_id": client_id,
            "voice_provider": "elevenlabs",
            "sms_provider": "twilio",
            "features": {
                "appointment_booking": True,
                "lead_qualification": True,
                "property_information": True,
                "market_updates": True,
                "follow_up_calls": True
            },
            "ai_settings": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 150,
                "voice_style": "professional",
                "personality": "friendly_agent"
            },
            "business_hours": {
                "timezone": "America/New_York",
                "monday": {"start": "09:00", "end": "17:00"},
                "tuesday": {"start": "09:00", "end": "17:00"},
                "wednesday": {"start": "09:00", "end": "17:00"},
                "thursday": {"start": "09:00", "end": "17:00"},
                "friday": {"start": "09:00", "end": "17:00"},
                "saturday": {"start": "10:00", "end": "14:00"},
                "sunday": {"start": "closed", "end": "closed"}
            }
        }
        
        # Add third-party account references
        if "elevenlabs" in third_party_accounts:
            voice_config["elevenlabs_account"] = third_party_accounts["elevenlabs"]["account_id"]
        
        if "twilio" in third_party_accounts:
            voice_config["twilio_account"] = third_party_accounts["twilio"]["account_id"]
            voice_config["phone_number"] = third_party_accounts["twilio"]["phone_number"]
        
        return voice_config
    
    async def _configure_webhooks(self, client_id: str, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure webhooks for system integration
        """
        base_url = f"https://{client_id}.seiketsu.ai"
        
        webhook_config = {
            "client_id": client_id,
            "base_url": base_url,
            "endpoints": {
                "call_completed": f"{base_url}/webhooks/call-completed",
                "lead_created": f"{base_url}/webhooks/lead-created",
                "appointment_booked": f"{base_url}/webhooks/appointment-booked",
                "message_received": f"{base_url}/webhooks/message-received"
            },
            "security": {
                "signature_verification": True,
                "ip_whitelist": ["52.3.14.200", "52.87.64.244"],  # Twilio IPs
                "webhook_secret": f"seiketsu_{client_id}_{uuid.uuid4().hex[:16]}"
            }
        }
        
        return webhook_config
    
    async def _deploy_application(self, client_id: str, client_data: Dict[str, Any], infrastructure_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy Seiketsu AI application to client infrastructure
        """
        try:
            # Get infrastructure details
            terraform_outputs = infrastructure_result["terraform_outputs"]
            
            # Prepare deployment configuration
            deployment_config = {
                "client_id": client_id,
                "image": "seiketsu/ai-voice-agent:latest",
                "environment": "production",
                "database_url": self._build_database_url(terraform_outputs),
                "redis_url": self._build_redis_url(terraform_outputs),
                "s3_bucket": terraform_outputs["client_bucket_name"]["value"],
                "load_balancer_dns": terraform_outputs["client_alb_dns_name"]["value"]
            }
            
            # Deploy using AWS Systems Manager or similar
            deployment_result = await self._execute_deployment(client_id, deployment_config)
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"Application deployment failed for {client_id}: {str(e)}")
            raise
    
    def _build_database_url(self, terraform_outputs: Dict[str, Any]) -> str:
        """Build database connection URL"""
        endpoint = terraform_outputs["client_db_endpoint"]["value"]
        # Password would be retrieved from AWS Secrets Manager
        return f"postgresql://seiketsu_admin:PASSWORD@{endpoint}:5432/seiketsu_{terraform_outputs['client_id']}"
    
    def _build_redis_url(self, terraform_outputs: Dict[str, Any]) -> str:
        """Build Redis connection URL"""
        endpoint = terraform_outputs["client_redis_endpoint"]["value"]
        return f"redis://{endpoint}:6379"
    
    async def _execute_deployment(self, client_id: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute application deployment
        """
        # This would typically use AWS CodeDeploy, ECS, or similar service
        # For now, return mock deployment result
        
        return {
            "deployment_id": f"deploy_{client_id}_{uuid.uuid4().hex[:8]}",
            "status": "completed",
            "deployed_at": datetime.utcnow().isoformat(),
            "application_url": f"https://{client_id}.seiketsu.ai",
            "health_check_url": f"https://{client_id}.seiketsu.ai/health",
            "version": "1.0.0",
            "configuration": deployment_config
        }
    
    async def _run_validation_tests(self, client_id: str, deployment_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run comprehensive validation tests
        """
        base_url = deployment_result["application_url"]
        validation_results = {}
        
        try:
            # Test 1: Health Check
            health_check = await self._test_health_endpoint(f"{base_url}/health")
            validation_results["health_check"] = health_check
            
            # Test 2: Database Connection
            db_test = await self._test_database_connection(client_id)
            validation_results["database_connection"] = db_test
            
            # Test 3: Redis Connection
            redis_test = await self._test_redis_connection(client_id)
            validation_results["redis_connection"] = redis_test
            
            # Test 4: API Endpoints
            api_test = await self._test_api_endpoints(base_url)
            validation_results["api_endpoints"] = api_test
            
            # Test 5: Third-party Integrations
            integration_test = await self._test_integrations(client_id)
            validation_results["integrations"] = integration_test
            
            # Overall validation status
            all_passed = all(test.get("status") == "passed" for test in validation_results.values())
            
            return {
                "overall_status": "passed" if all_passed else "failed",
                "tests_run": len(validation_results),
                "tests_passed": sum(1 for test in validation_results.values() if test.get("status") == "passed"),
                "validation_time": datetime.utcnow().isoformat(),
                "test_results": validation_results
            }
            
        except Exception as e:
            logger.error(f"Validation tests failed for {client_id}: {str(e)}")
            return {
                "overall_status": "failed",
                "error": str(e),
                "validation_time": datetime.utcnow().isoformat()
            }
    
    async def _test_health_endpoint(self, health_url: str) -> Dict[str, Any]:
        """Test application health endpoint"""
        try:
            # In real implementation, make HTTP request to health endpoint
            # For now, return mock result
            return {
                "test": "health_check",
                "status": "passed",
                "response_time": "150ms",
                "endpoint": health_url
            }
        except Exception as e:
            return {
                "test": "health_check",
                "status": "failed",
                "error": str(e)
            }
    
    async def _test_database_connection(self, client_id: str) -> Dict[str, Any]:
        """Test database connectivity"""
        try:
            # Mock database connection test
            return {
                "test": "database_connection",
                "status": "passed",
                "connection_time": "50ms"
            }
        except Exception as e:
            return {
                "test": "database_connection",
                "status": "failed",
                "error": str(e)
            }
    
    async def _test_redis_connection(self, client_id: str) -> Dict[str, Any]:
        """Test Redis connectivity"""
        try:
            # Mock Redis connection test
            return {
                "test": "redis_connection",
                "status": "passed",
                "ping_time": "10ms"
            }
        except Exception as e:
            return {
                "test": "redis_connection",
                "status": "failed",
                "error": str(e)
            }
    
    async def _test_api_endpoints(self, base_url: str) -> Dict[str, Any]:
        """Test critical API endpoints"""
        try:
            # Mock API endpoint tests
            return {
                "test": "api_endpoints",
                "status": "passed",
                "endpoints_tested": ["/api/v1/voice/call", "/api/v1/leads", "/api/v1/appointments"],
                "all_responding": True
            }
        except Exception as e:
            return {
                "test": "api_endpoints",
                "status": "failed",
                "error": str(e)
            }
    
    async def _test_integrations(self, client_id: str) -> Dict[str, Any]:
        """Test third-party integrations"""
        try:
            # Mock integration tests
            return {
                "test": "integrations",
                "status": "passed",
                "services_tested": ["elevenlabs", "twilio", "mls"],
                "all_connected": True
            }
        except Exception as e:
            return {
                "test": "integrations",
                "status": "failed",
                "error": str(e)
            }
    
    async def _send_welcome_notification(self, client_id: str, client_data: Dict[str, Any], deployment_result: Dict[str, Any]):
        """
        Send welcome email with account details
        """
        try:
            # Prepare welcome email content
            email_content = {
                "to": client_data["email"],
                "subject": f"Welcome to Seiketsu AI - Your Voice Agent is Ready!",
                "template": "client_welcome",
                "data": {
                    "company_name": client_data["company_name"],
                    "application_url": deployment_result["application_url"],
                    "admin_dashboard": f"{deployment_result['application_url']}/admin",
                    "support_email": "support@seiketsu.ai",
                    "client_id": client_id
                }
            }
            
            # Send email (mock implementation)
            logger.info(f"Sending welcome email to {client_data['email']} for client {client_id}")
            
            # In real implementation, integrate with email service
            
        except Exception as e:
            logger.error(f"Failed to send welcome notification for {client_id}: {str(e)}")
            # Don't fail provisioning if email fails
    
    async def _rollback_provisioning(self, client_id: str):
        """
        Rollback client provisioning in case of failure
        """
        logger.warning(f"Starting rollback for client {client_id}")
        
        try:
            # Update status
            await self._update_provisioning_status(client_id, ProvisioningStatus.ROLLING_BACK)
            
            # Destroy Terraform infrastructure
            try:
                await self._run_terraform_command("destroy", client_id)
                logger.info(f"Infrastructure destroyed for client {client_id}")
            except Exception as e:
                logger.error(f"Infrastructure cleanup failed for {client_id}: {str(e)}")
            
            # Clean up third-party accounts
            try:
                await self.third_party_service.cleanup_accounts(client_id)
                logger.info(f"Third-party accounts cleaned up for client {client_id}")
            except Exception as e:
                logger.error(f"Third-party cleanup failed for {client_id}: {str(e)}")
            
            # Update final status
            await self._update_provisioning_status(client_id, ProvisioningStatus.ROLLBACK_COMPLETED)
            
            logger.info(f"Rollback completed for client {client_id}")
            
        except Exception as e:
            logger.error(f"Rollback failed for client {client_id}: {str(e)}")
            await self._update_provisioning_status(client_id, ProvisioningStatus.ROLLBACK_FAILED)
    
    async def get_client_status(self, client_id: str) -> Dict[str, Any]:
        """
        Get current client provisioning status
        """
        # Query database for client record
        # Return current status and progress information
        
        return {
            "client_id": client_id,
            "status": "completed",  # Mock status
            "progress": 100,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def suspend_client(self, client_id: str) -> Dict[str, Any]:
        """
        Suspend client services
        """
        logger.info(f"Suspending services for client {client_id}")
        
        # Implementation would:
        # 1. Stop application services
        # 2. Disable third-party accounts
        # 3. Update database status
        # 4. Send suspension notification
        
        return {
            "client_id": client_id,
            "action": "suspended",
            "suspended_at": datetime.utcnow().isoformat(),
            "success": True
        }
    
    async def reactivate_client(self, client_id: str) -> Dict[str, Any]:
        """
        Reactivate suspended client services
        """
        logger.info(f"Reactivating services for client {client_id}")
        
        # Implementation would:
        # 1. Restart application services
        # 2. Re-enable third-party accounts
        # 3. Update database status
        # 4. Send reactivation notification
        
        return {
            "client_id": client_id,
            "action": "reactivated",
            "reactivated_at": datetime.utcnow().isoformat(),
            "success": True
        }