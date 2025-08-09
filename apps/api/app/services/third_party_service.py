"""
Seiketsu AI Third-Party Integration Service
Automated account creation and management for ElevenLabs, Twilio, MLS APIs
"""

import asyncio
import logging
import json
import uuid
import requests
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..utils.encryption import encrypt_sensitive_data, decrypt_sensitive_data
from ..utils.http_client import AsyncHTTPClient

logger = logging.getLogger(__name__)

@dataclass
class ThirdPartyCredentials:
    """Third-party service credentials"""
    service_name: str
    api_key: str
    api_secret: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None

class ThirdPartyService:
    """
    Automated third-party service account creation and management
    """
    
    def __init__(self):
        self.http_client = AsyncHTTPClient()
        self.service_configs = {
            "elevenlabs": {
                "base_url": "https://api.elevenlabs.io/v1",
                "signup_endpoint": "/user/subscription",
                "voices_endpoint": "/voices"
            },
            "twilio": {
                "base_url": "https://api.twilio.com/2010-04-01",
                "account_endpoint": "/Accounts.json",
                "phone_numbers_endpoint": "/AvailablePhoneNumbers/US/Local.json"
            },
            "mls": {
                "base_url": "https://api.mlsgrid.com/v2",
                "auth_endpoint": "/oauth/token",
                "properties_endpoint": "/Property"
            }
        }
    
    async def create_elevenlabs_account(self, client_id: str, client_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and configure ElevenLabs voice synthesis account
        """
        try:
            logger.info(f"Creating ElevenLabs account for client {client_id}")
            
            # Determine optimal voice settings based on AI analysis
            voice_config = await self._optimize_elevenlabs_config(client_data, ai_analysis)
            
            # Create account (mock implementation - actual ElevenLabs doesn't have automated signup)
            account_result = await self._create_elevenlabs_account_mock(client_id, client_data, voice_config)
            
            # Configure voice settings
            voice_settings = await self._configure_elevenlabs_voices(account_result["api_key"], voice_config)
            
            # Set usage limits based on subscription tier
            usage_limits = await self._set_elevenlabs_usage_limits(
                account_result["api_key"], 
                client_data.get("subscription_tier", "bronze")
            )
            
            return {
                "service": "elevenlabs",
                "account_id": account_result["account_id"],
                "api_key": account_result["api_key"],
                "voice_settings": voice_settings,
                "usage_limits": usage_limits,
                "configuration": voice_config,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"ElevenLabs account creation failed for client {client_id}: {str(e)}")
            raise
    
    async def _optimize_elevenlabs_config(self, client_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-optimized ElevenLabs configuration based on client needs
        """
        company_size = ai_analysis.get("company_size", "small")
        usage_prediction = ai_analysis.get("usage_prediction", {})
        
        # Voice selection based on company profile
        voice_profiles = {
            "startup": {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "style": "friendly"},
            "small": {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "style": "professional"},
            "medium": {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "style": "authoritative"},
            "large": {"voice_id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "style": "executive"},
            "enterprise": {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "style": "corporate"}
        }
        
        selected_voice = voice_profiles.get(company_size, voice_profiles["small"])
        
        # Usage-based configuration
        daily_calls = usage_prediction.get("daily_voice_calls", 50)
        
        config = {
            "primary_voice": selected_voice,
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            },
            "usage_tier": self._calculate_elevenlabs_tier(daily_calls),
            "features": {
                "voice_cloning": company_size in ["large", "enterprise"],
                "professional_voices": True,
                "instant_voice_cloning": company_size == "enterprise",
                "projects": company_size in ["medium", "large", "enterprise"]
            },
            "optimization": {
                "model": "eleven_multilingual_v2" if company_size in ["large", "enterprise"] else "eleven_monolingual_v1",
                "optimize_streaming_latency": daily_calls > 100,
                "output_format": "mp3_44100_128" if daily_calls > 200 else "mp3_22050_64"
            }
        }
        
        return config
    
    def _calculate_elevenlabs_tier(self, daily_calls: int) -> str:
        """Calculate appropriate ElevenLabs subscription tier"""
        monthly_chars = daily_calls * 30 * 200  # Estimate 200 chars per call
        
        if monthly_chars <= 10000:
            return "free"
        elif monthly_chars <= 30000:
            return "starter"
        elif monthly_calls <= 100000:
            return "creator"
        else:
            return "pro"
    
    async def _create_elevenlabs_account_mock(self, client_id: str, client_data: Dict[str, Any], voice_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock ElevenLabs account creation (real implementation would use their API)
        """
        # Generate mock API key
        api_key = f"sk-{uuid.uuid4().hex}"
        account_id = f"elevenlabs_{client_id}_{uuid.uuid4().hex[:8]}"
        
        # In real implementation, this would make API calls to ElevenLabs
        return {
            "account_id": account_id,
            "api_key": api_key,
            "subscription_tier": voice_config["usage_tier"],
            "account_email": client_data["email"]
        }
    
    async def _configure_elevenlabs_voices(self, api_key: str, voice_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure voice settings for the account
        """
        # Mock voice configuration - in real implementation, use ElevenLabs API
        return {
            "primary_voice_configured": True,
            "voice_id": voice_config["primary_voice"]["voice_id"],
            "voice_name": voice_config["primary_voice"]["name"],
            "settings_applied": voice_config["voice_settings"],
            "model_configured": voice_config["optimization"]["model"]
        }
    
    async def _set_elevenlabs_usage_limits(self, api_key: str, subscription_tier: str) -> Dict[str, Any]:
        """
        Set usage limits based on subscription tier
        """
        limits = {
            "bronze": {"monthly_characters": 10000, "concurrent_requests": 2},
            "silver": {"monthly_characters": 30000, "concurrent_requests": 5},
            "gold": {"monthly_characters": 100000, "concurrent_requests": 10},
            "enterprise": {"monthly_characters": 500000, "concurrent_requests": 20}
        }
        
        tier_limits = limits.get(subscription_tier, limits["bronze"])
        
        return {
            "tier": subscription_tier,
            "monthly_character_limit": tier_limits["monthly_characters"],
            "concurrent_request_limit": tier_limits["concurrent_requests"],
            "rate_limit": f"{tier_limits['concurrent_requests']}/second"
        }
    
    async def create_twilio_account(self, client_id: str, client_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and configure Twilio SMS/Voice account
        """
        try:
            logger.info(f"Creating Twilio account for client {client_id}")
            
            # Determine optimal Twilio configuration
            twilio_config = await self._optimize_twilio_config(client_data, ai_analysis)
            
            # Create Twilio subaccount
            account_result = await self._create_twilio_subaccount(client_id, client_data, twilio_config)
            
            # Purchase phone number
            phone_number = await self._purchase_twilio_phone_number(
                account_result["account_sid"],
                account_result["auth_token"],
                twilio_config
            )
            
            # Configure messaging and voice services
            services_config = await self._configure_twilio_services(
                account_result["account_sid"],
                account_result["auth_token"],
                phone_number,
                twilio_config
            )
            
            return {
                "service": "twilio",
                "account_id": account_result["account_sid"],
                "account_sid": account_result["account_sid"],
                "auth_token": account_result["auth_token"],
                "phone_number": phone_number["phone_number"],
                "phone_number_sid": phone_number["sid"],
                "services": services_config,
                "configuration": twilio_config,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Twilio account creation failed for client {client_id}: {str(e)}")
            raise
    
    async def _optimize_twilio_config(self, client_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-optimized Twilio configuration
        """
        usage_prediction = ai_analysis.get("usage_prediction", {})
        company_size = ai_analysis.get("company_size", "small")
        
        monthly_sms = usage_prediction.get("monthly_sms", 1000)
        daily_calls = usage_prediction.get("daily_voice_calls", 50)
        
        config = {
            "phone_number_type": "local",  # Could be "toll-free" for large companies
            "area_code": self._determine_area_code(client_data),
            "features": {
                "sms": True,
                "voice": True,
                "mms": company_size in ["medium", "large", "enterprise"],
                "international": company_size in ["large", "enterprise"]
            },
            "usage_based_pricing": {
                "estimated_monthly_sms": monthly_sms,
                "estimated_monthly_voice_minutes": daily_calls * 30 * 3,  # 3 min average
                "recommended_plan": self._recommend_twilio_plan(monthly_sms, daily_calls)
            },
            "webhook_config": {
                "voice_webhook": f"https://{client_data.get('client_id', 'client')}.seiketsu.ai/webhooks/voice",
                "sms_webhook": f"https://{client_data.get('client_id', 'client')}.seiketsu.ai/webhooks/sms",
                "fallback_webhook": f"https://{client_data.get('client_id', 'client')}.seiketsu.ai/webhooks/fallback"
            }
        }
        
        return config
    
    def _determine_area_code(self, client_data: Dict[str, Any]) -> str:
        """
        Determine appropriate area code based on client location
        """
        # Mock implementation - in real scenario, use geolocation service
        phone = client_data.get("phone", "")
        if phone.startswith("+1"):
            # Extract area code from existing phone number
            clean_phone = phone.replace("+1", "").replace("-", "").replace(" ", "")
            if len(clean_phone) >= 3:
                return clean_phone[:3]
        
        # Default to major metropolitan areas
        return "212"  # New York
    
    def _recommend_twilio_plan(self, monthly_sms: int, daily_calls: int) -> str:
        """
        Recommend appropriate Twilio plan based on usage
        """
        monthly_minutes = daily_calls * 30 * 3
        
        if monthly_sms <= 1000 and monthly_minutes <= 1000:
            return "pay-as-you-go"
        elif monthly_sms <= 10000 and monthly_minutes <= 5000:
            return "starter"
        elif monthly_sms <= 100000 and monthly_minutes <= 20000:
            return "business"
        else:
            return "enterprise"
    
    async def _create_twilio_subaccount(self, client_id: str, client_data: Dict[str, Any], twilio_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Twilio subaccount (mock implementation)
        """
        # Generate mock credentials
        account_sid = f"AC{uuid.uuid4().hex}"
        auth_token = uuid.uuid4().hex
        
        # In real implementation, use Twilio API to create subaccount
        return {
            "account_sid": account_sid,
            "auth_token": auth_token,
            "friendly_name": f"Seiketsu AI - {client_data['company_name']}",
            "status": "active"
        }
    
    async def _purchase_twilio_phone_number(self, account_sid: str, auth_token: str, twilio_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Purchase phone number for the client
        """
        # Mock phone number purchase
        phone_number = f"+1{twilio_config['area_code']}{uuid.uuid4().hex[:7].upper()}"
        phone_sid = f"PN{uuid.uuid4().hex}"
        
        # In real implementation, search and purchase available number
        return {
            "sid": phone_sid,
            "phone_number": phone_number,
            "friendly_name": f"Seiketsu AI Main Line",
            "capabilities": {
                "voice": True,
                "SMS": True,
                "MMS": twilio_config["features"]["mms"]
            }
        }
    
    async def _configure_twilio_services(self, account_sid: str, auth_token: str, phone_number: Dict[str, Any], twilio_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure Twilio messaging and voice services
        """
        # Mock service configuration
        return {
            "voice_service": {
                "configured": True,
                "webhook_url": twilio_config["webhook_config"]["voice_webhook"],
                "recording": "record-from-answer"
            },
            "messaging_service": {
                "configured": True,
                "webhook_url": twilio_config["webhook_config"]["sms_webhook"],
                "delivery_callbacks": True
            },
            "phone_number_config": {
                "voice_url": twilio_config["webhook_config"]["voice_webhook"],
                "sms_url": twilio_config["webhook_config"]["sms_webhook"],
                "voice_method": "POST",
                "sms_method": "POST"
            }
        }
    
    async def create_mls_account(self, client_id: str, client_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and configure MLS API access
        """
        try:
            logger.info(f"Creating MLS account for client {client_id}")
            
            # Determine MLS requirements based on location and size
            mls_config = await self._optimize_mls_config(client_data, ai_analysis)
            
            # Register for MLS access
            account_result = await self._register_mls_access(client_id, client_data, mls_config)
            
            # Configure data access permissions
            data_permissions = await self._configure_mls_permissions(
                account_result["api_key"],
                mls_config
            )
            
            return {
                "service": "mls",
                "account_id": account_result["account_id"],
                "api_key": account_result["api_key"],
                "mls_regions": account_result["mls_regions"],
                "data_permissions": data_permissions,
                "configuration": mls_config,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"MLS account creation failed for client {client_id}: {str(e)}")
            raise
    
    async def _optimize_mls_config(self, client_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize MLS configuration based on client needs
        """
        company_size = ai_analysis.get("company_size", "small")
        usage_prediction = ai_analysis.get("usage_prediction", {})
        
        weekly_queries = usage_prediction.get("weekly_mls_queries", 200)
        
        config = {
            "data_access_level": self._determine_mls_access_level(company_size, weekly_queries),
            "regions": self._determine_mls_regions(client_data),
            "property_types": ["residential", "commercial", "land"],
            "data_fields": self._get_mls_data_fields(company_size),
            "query_limits": {
                "daily_limit": weekly_queries * 2,  # Buffer for daily spikes
                "monthly_limit": weekly_queries * 4.5 * 12,
                "concurrent_requests": 5 if company_size in ["large", "enterprise"] else 2
            },
            "features": {
                "historical_data": company_size in ["medium", "large", "enterprise"],
                "market_analytics": company_size in ["large", "enterprise"],
                "automated_valuations": True,
                "photo_access": company_size != "startup"
            }
        }
        
        return config
    
    def _determine_mls_access_level(self, company_size: str, weekly_queries: int) -> str:
        """
        Determine appropriate MLS access level
        """
        if company_size == "enterprise" or weekly_queries > 1000:
            return "enterprise"
        elif company_size in ["large", "medium"] or weekly_queries > 500:
            return "professional"
        else:
            return "standard"
    
    def _determine_mls_regions(self, client_data: Dict[str, Any]) -> List[str]:
        """
        Determine MLS regions based on client location
        """
        # Mock implementation - in real scenario, use geolocation
        return ["Northeast", "Southeast"]  # Default regions
    
    def _get_mls_data_fields(self, company_size: str) -> List[str]:
        """
        Get appropriate MLS data fields based on company size
        """
        base_fields = [
            "ListingId", "PropertyType", "ListPrice", "Address",
            "BedroomsTotal", "BathroomsTotalDecimal", "LivingArea",
            "ListingStatus", "OnMarketDate", "PhotosCount"
        ]
        
        if company_size in ["medium", "large", "enterprise"]:
            base_fields.extend([
                "DaysOnMarket", "PricePerSquareFoot", "YearBuilt",
                "PropertySubType", "Financing", "SchoolDistrict"
            ])
        
        if company_size in ["large", "enterprise"]:
            base_fields.extend([
                "TaxAmount", "TaxYear", "AssociationFee",
                "WaterSource", "Utilities", "ApproxHOAFee"
            ])
        
        return base_fields
    
    async def _register_mls_access(self, client_id: str, client_data: Dict[str, Any], mls_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register for MLS API access (mock implementation)
        """
        # Generate mock credentials
        api_key = f"mls_{uuid.uuid4().hex}"
        account_id = f"mls_{client_id}_{uuid.uuid4().hex[:8]}"
        
        # In real implementation, would register with MLS providers
        return {
            "account_id": account_id,
            "api_key": api_key,
            "mls_regions": mls_config["regions"],
            "access_level": mls_config["data_access_level"]
        }
    
    async def _configure_mls_permissions(self, api_key: str, mls_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure MLS data access permissions
        """
        return {
            "data_access_configured": True,
            "property_types": mls_config["property_types"],
            "data_fields": mls_config["data_fields"],
            "query_limits": mls_config["query_limits"],
            "features_enabled": mls_config["features"]
        }
    
    async def cleanup_accounts(self, client_id: str):
        """
        Clean up third-party accounts during rollback
        """
        logger.info(f"Cleaning up third-party accounts for client {client_id}")
        
        try:
            # Get all third-party accounts for client
            accounts = await self._get_client_accounts(client_id)
            
            # Clean up each service
            for account in accounts:
                try:
                    if account["service_name"] == "elevenlabs":
                        await self._cleanup_elevenlabs_account(account)
                    elif account["service_name"] == "twilio":
                        await self._cleanup_twilio_account(account)
                    elif account["service_name"] == "mls":
                        await self._cleanup_mls_account(account)
                        
                    logger.info(f"Cleaned up {account['service_name']} account for client {client_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to cleanup {account['service_name']} for client {client_id}: {e}")
            
        except Exception as e:
            logger.error(f"Account cleanup failed for client {client_id}: {str(e)}")
            raise
    
    async def _get_client_accounts(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Get all third-party accounts for a client
        """
        # Mock implementation - in real scenario, query database
        return [
            {"service_name": "elevenlabs", "account_id": f"elevenlabs_{client_id}"},
            {"service_name": "twilio", "account_id": f"twilio_{client_id}"},
            {"service_name": "mls", "account_id": f"mls_{client_id}"}
        ]
    
    async def _cleanup_elevenlabs_account(self, account: Dict[str, Any]):
        """Clean up ElevenLabs account"""
        # In real implementation, cancel subscription and delete account
        pass
    
    async def _cleanup_twilio_account(self, account: Dict[str, Any]):
        """Clean up Twilio account"""
        # In real implementation, close subaccount and release phone numbers
        pass
    
    async def _cleanup_mls_account(self, account: Dict[str, Any]):
        """Clean up MLS account"""
        # In real implementation, cancel MLS access and API keys
        pass
    
    async def get_account_status(self, client_id: str, service_name: str) -> Dict[str, Any]:
        """
        Get status of specific third-party account
        """
        # Mock implementation
        return {
            "client_id": client_id,
            "service": service_name,
            "status": "active",
            "last_checked": datetime.utcnow().isoformat(),
            "usage_current_month": {
                "elevenlabs": "15,000 characters",
                "twilio": "2,500 messages, 150 minutes",
                "mls": "850 queries"
            }.get(service_name, "N/A")
        }
    
    async def update_account_limits(self, client_id: str, service_name: str, new_limits: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update usage limits for third-party account
        """
        logger.info(f"Updating {service_name} limits for client {client_id}")
        
        # Implementation would update service-specific limits
        return {
            "client_id": client_id,
            "service": service_name,
            "limits_updated": True,
            "new_limits": new_limits,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def validate_account_health(self, client_id: str) -> Dict[str, Any]:
        """
        Validate health of all third-party accounts for client
        """
        health_status = {}
        
        services = ["elevenlabs", "twilio", "mls"]
        for service in services:
            try:
                status = await self._check_service_health(client_id, service)
                health_status[service] = status
            except Exception as e:
                health_status[service] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_checked": datetime.utcnow().isoformat()
                }
        
        overall_healthy = all(status.get("status") == "healthy" for status in health_status.values())
        
        return {
            "client_id": client_id,
            "overall_status": "healthy" if overall_healthy else "issues_detected",
            "services": health_status,
            "checked_at": datetime.utcnow().isoformat()
        }
    
    async def _check_service_health(self, client_id: str, service_name: str) -> Dict[str, Any]:
        """
        Check health of specific service
        """
        # Mock health check - in real implementation, ping service APIs
        return {
            "status": "healthy",
            "response_time": "120ms",
            "last_successful_call": datetime.utcnow().isoformat(),
            "rate_limit_remaining": "80%"
        }