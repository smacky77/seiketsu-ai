"""
Twilio Service Integration
SMS, Voice, and Phone Number Management with Webhooks
"""

import asyncio
import logging
import json
import aiohttp
import base64
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlencode

from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse

from ..core.config import settings
from ..core.exceptions import ExternalServiceException, RateLimitException, ServiceUnavailableException
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.retry_decorator import retry_async
from ..utils.rate_limiter import RateLimiter
from ..services.usage_service import UsageService

logger = logging.getLogger(__name__)

class MessageDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class CallDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound-api"

class CallStatus(Enum):
    QUEUED = "queued"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    BUSY = "busy"
    FAILED = "failed"
    NO_ANSWER = "no-answer"
    CANCELED = "canceled"

@dataclass
class PhoneNumberCapabilities:
    voice: bool = True
    sms: bool = True
    mms: bool = False
    fax: bool = False

@dataclass
class WebhookConfig:
    voice_url: Optional[str] = None
    voice_method: str = "POST"
    sms_url: Optional[str] = None
    sms_method: str = "POST"
    status_callback_url: Optional[str] = None
    status_callback_method: str = "POST"

class TwilioService:
    """
    Production-ready Twilio integration for SMS, Voice, and Phone Numbers
    """
    
    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.client = None
        self.usage_service = UsageService()
        
        # Circuit breaker for fault tolerance
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=ExternalServiceException
        )
        
        # Rate limiter for API calls
        self.rate_limiter = RateLimiter(
            requests_per_second=5,
            burst_size=10
        )
        
        # Webhook handlers registry
        self.webhook_handlers: Dict[str, Callable] = {}
        
        # Initialize client
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Twilio client"""
        if self.account_sid and self.auth_token:
            self.client = TwilioClient(self.account_sid, self.auth_token)
        else:
            logger.warning("Twilio credentials not configured")
            
    @retry_async(max_attempts=3, backoff_factor=1.5)
    async def send_sms(
        self,
        to: str,
        message: str,
        from_number: str,
        client_id: str,
        media_urls: Optional[List[str]] = None,
        status_callback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS message
        
        Args:
            to: Recipient phone number
            message: Message content
            from_number: Sender phone number
            client_id: Client identifier for usage tracking
            media_urls: Optional media URLs for MMS
            status_callback: Optional status callback URL
            
        Returns:
            Message details and status
        """
        try:
            if not self.client:
                raise ExternalServiceException("twilio", "Twilio client not initialized")
            
            await self.rate_limiter.acquire()
            
            # Validate input
            if not message.strip():
                raise ExternalServiceException("twilio", "Message content cannot be empty")
                
            if len(message) > 1600:  # Twilio SMS limit
                raise ExternalServiceException("twilio", "Message exceeds maximum length (1600 characters)")
            
            # Track SMS usage upfront
            usage_result = await self.usage_service.track_api_usage(
                client_id=client_id,
                service="twilio",
                usage_data={
                    "sms_sent": 1,
                    "from_number": from_number,
                    "to_number": to
                }
            )
            
            if not usage_result.get("success"):
                raise ExternalServiceException("twilio", f"Usage limit exceeded: {usage_result.get('error')}")
            
            start_time = time.time()
            
            async with self.circuit_breaker:
                # Prepare message parameters
                message_params = {
                    "to": to,
                    "from_": from_number,
                    "body": message
                }
                
                if media_urls:
                    message_params["media_url"] = media_urls
                    
                if status_callback:
                    message_params["status_callback"] = status_callback
                
                # Send message using asyncio to avoid blocking
                try:
                    loop = asyncio.get_event_loop()
                    twilio_message = await loop.run_in_executor(
                        None,
                        lambda: self.client.messages.create(**message_params)
                    )
                    
                    response_time = time.time() - start_time
                    
                    logger.info(f"SMS sent successfully: {twilio_message.sid} to {to}")
                    
                    return {
                        "success": True,
                        "message_sid": twilio_message.sid,
                        "to": to,
                        "from": from_number,
                        "body": message,
                        "status": twilio_message.status,
                        "direction": MessageDirection.OUTBOUND.value,
                        "price": twilio_message.price,
                        "price_unit": twilio_message.price_unit,
                        "num_segments": twilio_message.num_segments,
                        "num_media": twilio_message.num_media,
                        "date_created": twilio_message.date_created.isoformat() if twilio_message.date_created else None,
                        "response_time": response_time,
                        "usage_tracked": usage_result.get("success", False)
                    }
                    
                except TwilioRestException as e:
                    logger.error(f"Twilio SMS error: {e.msg} (Code: {e.code})")
                    
                    if e.code in [20003, 20004]:  # Authentication errors
                        raise ExternalServiceException("twilio", f"Authentication failed: {e.msg}")
                    elif e.code == 20429:  # Rate limit
                        raise RateLimitException(message="Twilio rate limit exceeded")
                    elif e.code in [21211, 21212, 21213]:  # Invalid phone numbers
                        raise ExternalServiceException("twilio", f"Invalid phone number: {e.msg}")
                    else:
                        raise ExternalServiceException("twilio", f"SMS failed: {e.msg}", service_error_code=str(e.code))
                        
        except (RateLimitException, ExternalServiceException):
            raise
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            raise ExternalServiceException("twilio", f"SMS sending failed: {str(e)}")
            
    @retry_async(max_attempts=3, backoff_factor=1.5)
    async def make_call(
        self,
        to: str,
        from_number: str,
        twiml_url: str,
        client_id: str,
        timeout: int = 30,
        record: bool = False,
        status_callback: Optional[str] = None,
        machine_detection: bool = False
    ) -> Dict[str, Any]:
        """
        Make outbound voice call
        
        Args:
            to: Recipient phone number
            from_number: Caller phone number
            twiml_url: TwiML URL for call instructions
            client_id: Client identifier for usage tracking
            timeout: Call timeout in seconds
            record: Whether to record the call
            status_callback: Optional status callback URL
            machine_detection: Enable answering machine detection
            
        Returns:
            Call details and status
        """
        try:
            if not self.client:
                raise ExternalServiceException("twilio", "Twilio client not initialized")
            
            await self.rate_limiter.acquire()
            
            # Track call usage upfront
            usage_result = await self.usage_service.track_api_usage(
                client_id=client_id,
                service="twilio",
                usage_data={
                    "call_initiated": 1,
                    "from_number": from_number,
                    "to_number": to
                }
            )
            
            if not usage_result.get("success"):
                raise ExternalServiceException("twilio", f"Usage limit exceeded: {usage_result.get('error')}")
            
            start_time = time.time()
            
            async with self.circuit_breaker:
                # Prepare call parameters
                call_params = {
                    "to": to,
                    "from_": from_number,
                    "url": twiml_url,
                    "timeout": timeout
                }
                
                if record:
                    call_params["record"] = "record-from-answer"
                    
                if status_callback:
                    call_params["status_callback"] = status_callback
                    call_params["status_callback_event"] = [
                        "initiated", "ringing", "answered", "completed"
                    ]
                    
                if machine_detection:
                    call_params["machine_detection"] = "Enable"
                
                try:
                    loop = asyncio.get_event_loop()
                    twilio_call = await loop.run_in_executor(
                        None,
                        lambda: self.client.calls.create(**call_params)
                    )
                    
                    response_time = time.time() - start_time
                    
                    logger.info(f"Call initiated successfully: {twilio_call.sid} to {to}")
                    
                    return {
                        "success": True,
                        "call_sid": twilio_call.sid,
                        "to": to,
                        "from": from_number,
                        "status": twilio_call.status,
                        "direction": CallDirection.OUTBOUND.value,
                        "price": twilio_call.price,
                        "price_unit": twilio_call.price_unit,
                        "duration": twilio_call.duration,
                        "start_time": twilio_call.start_time.isoformat() if twilio_call.start_time else None,
                        "date_created": twilio_call.date_created.isoformat() if twilio_call.date_created else None,
                        "response_time": response_time,
                        "usage_tracked": usage_result.get("success", False)
                    }
                    
                except TwilioRestException as e:
                    logger.error(f"Twilio call error: {e.msg} (Code: {e.code})")
                    
                    if e.code in [20003, 20004]:  # Authentication errors
                        raise ExternalServiceException("twilio", f"Authentication failed: {e.msg}")
                    elif e.code == 20429:  # Rate limit
                        raise RateLimitException(message="Twilio rate limit exceeded")
                    else:
                        raise ExternalServiceException("twilio", f"Call failed: {e.msg}", service_error_code=str(e.code))
                        
        except (RateLimitException, ExternalServiceException):
            raise
        except Exception as e:
            logger.error(f"Call initiation failed: {str(e)}")
            raise ExternalServiceException("twilio", f"Call initiation failed: {str(e)}")
            
    @retry_async(max_attempts=3, backoff_factor=1.5)
    async def purchase_phone_number(
        self,
        area_code: Optional[str] = None,
        country_code: str = "US",
        phone_number: Optional[str] = None,
        capabilities: Optional[PhoneNumberCapabilities] = None,
        webhook_config: Optional[WebhookConfig] = None,
        friendly_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Purchase a phone number
        
        Args:
            area_code: Preferred area code
            country_code: Country code (default: US)
            phone_number: Specific phone number to purchase
            capabilities: Required capabilities
            webhook_config: Webhook configuration
            friendly_name: Friendly name for the number
            
        Returns:
            Purchased phone number details
        """
        try:
            if not self.client:
                raise ExternalServiceException("twilio", "Twilio client not initialized")
            
            await self.rate_limiter.acquire()
            
            if capabilities is None:
                capabilities = PhoneNumberCapabilities()
                
            async with self.circuit_breaker:
                try:
                    loop = asyncio.get_event_loop()
                    
                    if phone_number:
                        # Purchase specific number
                        purchased_number = await loop.run_in_executor(
                            None,
                            lambda: self.client.incoming_phone_numbers.create(phone_number=phone_number)
                        )
                    else:
                        # Search for available numbers
                        search_params = {
                            "voice_enabled": capabilities.voice,
                            "sms_enabled": capabilities.sms,
                            "mms_enabled": capabilities.mms,
                            "fax_enabled": capabilities.fax,
                        }
                        
                        if area_code:
                            search_params["area_code"] = area_code
                        
                        available_numbers = await loop.run_in_executor(
                            None,
                            lambda: self.client.available_phone_numbers(country_code).local.list(**search_params, limit=1)
                        )
                        
                        if not available_numbers:
                            raise ExternalServiceException("twilio", "No available phone numbers found")
                        
                        # Purchase the first available number
                        selected_number = available_numbers[0]
                        purchased_number = await loop.run_in_executor(
                            None,
                            lambda: self.client.incoming_phone_numbers.create(
                                phone_number=selected_number.phone_number
                            )
                        )
                    
                    # Configure webhooks if provided
                    if webhook_config:
                        await self._configure_phone_number_webhooks(
                            purchased_number.sid,
                            webhook_config,
                            friendly_name
                        )
                    
                    logger.info(f"Phone number purchased: {purchased_number.phone_number}")
                    
                    return {
                        "success": True,
                        "phone_number_sid": purchased_number.sid,
                        "phone_number": purchased_number.phone_number,
                        "friendly_name": purchased_number.friendly_name,
                        "capabilities": {
                            "voice": purchased_number.capabilities["voice"],
                            "sms": purchased_number.capabilities["sms"],
                            "mms": purchased_number.capabilities["mms"],
                            "fax": purchased_number.capabilities["fax"]
                        },
                        "date_created": purchased_number.date_created.isoformat(),
                        "monthly_cost": "1.00",  # Typical Twilio cost
                        "currency": "USD"
                    }
                    
                except TwilioRestException as e:
                    logger.error(f"Phone number purchase error: {e.msg} (Code: {e.code})")
                    
                    if e.code == 21452:  # Number not available
                        raise ExternalServiceException("twilio", "Phone number not available for purchase")
                    elif e.code in [20003, 20004]:  # Authentication errors
                        raise ExternalServiceException("twilio", f"Authentication failed: {e.msg}")
                    else:
                        raise ExternalServiceException("twilio", f"Phone number purchase failed: {e.msg}")
                        
        except ExternalServiceException:
            raise
        except Exception as e:
            logger.error(f"Phone number purchase failed: {str(e)}")
            raise ExternalServiceException("twilio", f"Phone number purchase failed: {str(e)}")
            
    async def _configure_phone_number_webhooks(
        self,
        phone_number_sid: str,
        webhook_config: WebhookConfig,
        friendly_name: Optional[str] = None
    ):
        """Configure webhooks for purchased phone number"""
        try:
            loop = asyncio.get_event_loop()
            
            update_params = {}
            
            if webhook_config.voice_url:
                update_params["voice_url"] = webhook_config.voice_url
                update_params["voice_method"] = webhook_config.voice_method
                
            if webhook_config.sms_url:
                update_params["sms_url"] = webhook_config.sms_url
                update_params["sms_method"] = webhook_config.sms_method
                
            if webhook_config.status_callback_url:
                update_params["status_callback"] = webhook_config.status_callback_url
                update_params["status_callback_method"] = webhook_config.status_callback_method
                
            if friendly_name:
                update_params["friendly_name"] = friendly_name
            
            if update_params:
                await loop.run_in_executor(
                    None,
                    lambda: self.client.incoming_phone_numbers(phone_number_sid).update(**update_params)
                )
                
        except Exception as e:
            logger.error(f"Failed to configure webhooks for {phone_number_sid}: {str(e)}")
            raise
            
    async def handle_webhook(self, webhook_type: str, data: Dict[str, Any]) -> str:
        """
        Handle incoming webhooks from Twilio
        
        Args:
            webhook_type: Type of webhook (voice, sms, status)
            data: Webhook data from Twilio
            
        Returns:
            TwiML response
        """
        try:
            handler = self.webhook_handlers.get(webhook_type)
            
            if not handler:
                logger.warning(f"No handler registered for webhook type: {webhook_type}")
                return self._default_webhook_response(webhook_type)
            
            # Call registered handler
            response = await handler(data)
            
            # Track usage for incoming communications
            if webhook_type == "sms" and data.get("From"):
                # This is an incoming SMS
                await self._track_incoming_sms(data)
            elif webhook_type == "voice" and data.get("From"):
                # This is an incoming call
                await self._track_incoming_call(data)
            
            return response
            
        except Exception as e:
            logger.error(f"Webhook handling failed for {webhook_type}: {str(e)}")
            return self._error_webhook_response(webhook_type)
            
    def register_webhook_handler(self, webhook_type: str, handler: Callable):
        """Register a webhook handler function"""
        self.webhook_handlers[webhook_type] = handler
        logger.info(f"Registered webhook handler for {webhook_type}")
        
    def _default_webhook_response(self, webhook_type: str) -> str:
        """Generate default webhook response"""
        if webhook_type == "voice":
            response = VoiceResponse()
            response.say("Thank you for calling. Please try again later.")
            return str(response)
        elif webhook_type == "sms":
            response = MessagingResponse()
            response.message("Thank you for your message. We'll get back to you soon.")
            return str(response)
        else:
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
            
    def _error_webhook_response(self, webhook_type: str) -> str:
        """Generate error webhook response"""
        if webhook_type == "voice":
            response = VoiceResponse()
            response.say("Sorry, we're experiencing technical difficulties. Please try again later.")
            return str(response)
        elif webhook_type == "sms":
            response = MessagingResponse()
            response.message("Sorry, we're currently unable to process your message. Please try again later.")
            return str(response)
        else:
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
            
    async def _track_incoming_sms(self, data: Dict[str, Any]):
        """Track incoming SMS for usage analytics"""
        try:
            # Extract client_id from phone number or other identifier
            # This would typically be determined by routing logic
            client_id = self._extract_client_id_from_number(data.get("To"))
            
            if client_id:
                await self.usage_service.track_api_usage(
                    client_id=client_id,
                    service="twilio",
                    usage_data={
                        "sms_received": 1,
                        "from_number": data.get("From"),
                        "to_number": data.get("To"),
                        "message_sid": data.get("MessageSid")
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track incoming SMS: {str(e)}")
            
    async def _track_incoming_call(self, data: Dict[str, Any]):
        """Track incoming call for usage analytics"""
        try:
            client_id = self._extract_client_id_from_number(data.get("To"))
            
            if client_id:
                await self.usage_service.track_api_usage(
                    client_id=client_id,
                    service="twilio",
                    usage_data={
                        "call_received": 1,
                        "from_number": data.get("From"),
                        "to_number": data.get("To"),
                        "call_sid": data.get("CallSid")
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track incoming call: {str(e)}")
            
    def _extract_client_id_from_number(self, phone_number: str) -> Optional[str]:
        """Extract client ID from phone number (implement based on your routing logic)"""
        # This is a placeholder - implement based on how you route numbers to clients
        # Could use a database lookup, number mapping, etc.
        return "default_client"
        
    async def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """Get details for a specific call"""
        try:
            if not self.client:
                raise ExternalServiceException("twilio", "Twilio client not initialized")
            
            loop = asyncio.get_event_loop()
            call = await loop.run_in_executor(
                None,
                lambda: self.client.calls(call_sid).fetch()
            )
            
            return {
                "call_sid": call.sid,
                "from": call.from_,
                "to": call.to,
                "status": call.status,
                "direction": call.direction,
                "duration": call.duration,
                "price": call.price,
                "price_unit": call.price_unit,
                "start_time": call.start_time.isoformat() if call.start_time else None,
                "end_time": call.end_time.isoformat() if call.end_time else None,
                "date_created": call.date_created.isoformat() if call.date_created else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get call details: {str(e)}")
            raise ExternalServiceException("twilio", f"Failed to get call details: {str(e)}")
            
    async def get_message_details(self, message_sid: str) -> Dict[str, Any]:
        """Get details for a specific message"""
        try:
            if not self.client:
                raise ExternalServiceException("twilio", "Twilio client not initialized")
            
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.client.messages(message_sid).fetch()
            )
            
            return {
                "message_sid": message.sid,
                "from": message.from_,
                "to": message.to,
                "body": message.body,
                "status": message.status,
                "direction": message.direction,
                "price": message.price,
                "price_unit": message.price_unit,
                "num_segments": message.num_segments,
                "num_media": message.num_media,
                "date_created": message.date_created.isoformat() if message.date_created else None,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get message details: {str(e)}")
            raise ExternalServiceException("twilio", f"Failed to get message details: {str(e)}")
            
    async def health_check(self) -> Dict[str, Any]:
        """Health check for Twilio service"""
        try:
            if not self.client:
                return {
                    "service": "twilio",
                    "status": "unhealthy",
                    "error": "Client not initialized",
                    "last_checked": datetime.utcnow().isoformat()
                }
            
            start_time = time.time()
            
            # Test API connectivity by fetching account info
            loop = asyncio.get_event_loop()
            account = await loop.run_in_executor(
                None,
                lambda: self.client.api.account.fetch()
            )
            
            response_time = time.time() - start_time
            
            return {
                "service": "twilio",
                "status": "healthy",
                "account_sid": account.sid,
                "account_status": account.status,
                "response_time": response_time,
                "circuit_breaker_state": self.circuit_breaker.state,
                "last_checked": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "service": "twilio",
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker_state": self.circuit_breaker.state,
                "last_checked": datetime.utcnow().isoformat()
            }