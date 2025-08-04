"""
Webhook service for external integrations
"""
import asyncio
import logging
import json
import hmac
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.webhook import Webhook, WebhookEvent, WebhookStatus

logger = logging.getLogger("seiketsu.webhook_service")


class WebhookService:
    """Service for managing and sending webhooks"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.WEBHOOK_TIMEOUT)
        )
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def send_webhook(
        self,
        organization_id: str,
        event_type: str,
        payload: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ):
        """Send webhook to all registered endpoints for event type"""
        if not db:
            return
        
        try:
            # Get webhooks for organization and event type
            webhooks = await self._get_webhooks_for_event(
                organization_id, event_type, db
            )
            
            if not webhooks:
                logger.debug(f"No webhooks configured for event {event_type} in org {organization_id}")
                return
            
            # Send to all webhooks concurrently
            tasks = [
                self._send_single_webhook(webhook, event_type, payload)
                for webhook in webhooks
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Failed to send webhooks for event {event_type}: {e}")
    
    async def _get_webhooks_for_event(
        self,
        organization_id: str,
        event_type: str,
        db: AsyncSession
    ) -> List[Webhook]:
        """Get active webhooks that support the event type"""
        try:
            stmt = select(Webhook).where(
                Webhook.organization_id == organization_id,
                Webhook.status == WebhookStatus.ACTIVE
            )
            
            result = await db.execute(stmt)
            all_webhooks = result.scalars().all()
            
            # Filter webhooks that support this event type
            matching_webhooks = [
                webhook for webhook in all_webhooks
                if webhook.supports_event(WebhookEvent(event_type))
            ]
            
            return matching_webhooks
            
        except Exception as e:
            logger.error(f"Failed to get webhooks for event {event_type}: {e}")
            return []
    
    async def _send_single_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """Send webhook to a single endpoint with retry logic"""
        webhook_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": webhook.id,
            "data": payload
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"Seiketsu-Webhook/1.0",
            "X-Webhook-Event": event_type,
            "X-Webhook-ID": webhook.id
        }
        
        # Add custom headers
        if webhook.headers:
            headers.update(webhook.headers)
        
        # Add signature if secret is configured
        if webhook.secret:
            signature = self._generate_signature(
                json.dumps(webhook_payload, sort_keys=True),
                webhook.secret
            )
            headers["X-Webhook-Signature"] = signature
        
        # Attempt delivery with retries
        for attempt in range(webhook.max_retries + 1):
            try:
                success = await self._attempt_webhook_delivery(
                    webhook.url, webhook_payload, headers, webhook.timeout_seconds
                )
                
                # Record delivery result
                webhook.record_delivery(success)
                
                if success:
                    logger.info(f"Webhook delivered successfully to {webhook.url} (attempt {attempt + 1})")
                    return
                else:
                    logger.warning(f"Webhook delivery failed to {webhook.url} (attempt {attempt + 1})")
                    
                    # Wait before retry (except on last attempt)
                    if attempt < webhook.max_retries:
                        await asyncio.sleep(webhook.retry_delay_seconds)
                        
            except Exception as e:
                logger.error(f"Webhook delivery error to {webhook.url} (attempt {attempt + 1}): {e}")
                webhook.record_delivery(False)
                
                if attempt < webhook.max_retries:
                    await asyncio.sleep(webhook.retry_delay_seconds)
        
        logger.error(f"Webhook delivery failed permanently to {webhook.url} after {webhook.max_retries + 1} attempts")
    
    async def _attempt_webhook_delivery(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        timeout_seconds: int
    ) -> bool:
        """Attempt single webhook delivery"""
        if not self.session:
            await self.initialize()
        
        try:
            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            ) as response:
                # Consider 2xx status codes as success
                success = 200 <= response.status < 300
                
                if not success:
                    response_text = await response.text()
                    logger.warning(
                        f"Webhook returned {response.status}: {response_text[:200]}"
                    )
                
                return success
                
        except asyncio.TimeoutError:
            logger.warning(f"Webhook delivery timed out to {url}")
            return False
        except Exception as e:
            logger.error(f"Webhook delivery exception to {url}: {e}")
            return False
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    async def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """Verify webhook signature"""
        expected_signature = self._generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    async def test_webhook_endpoint(
        self,
        webhook_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Test webhook endpoint with ping event"""
        try:
            stmt = select(Webhook).where(Webhook.id == webhook_id)
            result = await db.execute(stmt)
            webhook = result.scalar_one_or_none()
            
            if not webhook:
                return {"success": False, "error": "Webhook not found"}
            
            # Send test payload
            test_payload = {
                "message": "This is a test webhook from Seiketsu AI",
                "timestamp": datetime.utcnow().isoformat(),
                "webhook_id": webhook.id
            }
            
            await self._send_single_webhook(webhook, "webhook.test", test_payload)
            
            # Update last ping time
            webhook.last_ping = datetime.utcnow()
            await db.commit()
            
            return {
                "success": True,
                "message": "Test webhook sent successfully",
                "endpoint": webhook.url
            }
            
        except Exception as e:
            logger.error(f"Failed to test webhook {webhook_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_webhook_delivery_stats(
        self,
        webhook_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get delivery statistics for webhook"""
        try:
            stmt = select(Webhook).where(Webhook.id == webhook_id)
            result = await db.execute(stmt)
            webhook = result.scalar_one_or_none()
            
            if not webhook:
                return {"error": "Webhook not found"}
            
            return {
                "webhook_id": webhook.id,
                "total_deliveries": webhook.total_deliveries,
                "successful_deliveries": webhook.successful_deliveries,
                "failed_deliveries": webhook.failed_deliveries,
                "success_rate": webhook.success_rate,
                "last_delivery_at": webhook.last_delivery_at.isoformat() if webhook.last_delivery_at else None,
                "last_success_at": webhook.last_success_at.isoformat() if webhook.last_success_at else None,
                "last_failure_at": webhook.last_failure_at.isoformat() if webhook.last_failure_at else None,
                "is_healthy": webhook.is_healthy,
                "status": webhook.status.value
            }
            
        except Exception as e:
            logger.error(f"Failed to get webhook stats {webhook_id}: {e}")
            return {"error": str(e)}
    
    async def bulk_send_webhook(
        self,
        organization_ids: List[str],
        event_type: str,
        payload_generator: callable,
        db: AsyncSession
    ):
        """Send webhook to multiple organizations"""
        tasks = []
        
        for org_id in organization_ids:
            payload = payload_generator(org_id)
            task = self.send_webhook(org_id, event_type, payload, db)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Sent bulk webhook {event_type} to {len(organization_ids)} organizations")


# Webhook event types for easy reference
class WebhookEvents:
    """Standard webhook event types"""
    
    # Conversation events
    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_ENDED = "conversation.ended" 
    CONVERSATION_TRANSFERRED = "conversation.transferred"
    
    # Lead events
    LEAD_CREATED = "lead.created"
    LEAD_UPDATED = "lead.updated"
    LEAD_QUALIFIED = "lead.qualified"
    
    # Appointment events
    APPOINTMENT_SCHEDULED = "appointment.scheduled"
    APPOINTMENT_CONFIRMED = "appointment.confirmed"
    APPOINTMENT_CANCELLED = "appointment.cancelled"
    
    # Voice agent events
    VOICE_AGENT_CREATED = "voice_agent.created"
    VOICE_AGENT_UPDATED = "voice_agent.updated"
    VOICE_AGENT_STATUS_CHANGED = "voice_agent.status_changed"
    
    # System events
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_ALERT = "system.alert"
    
    # Test events
    WEBHOOK_TEST = "webhook.test"