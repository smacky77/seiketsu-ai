"""
Enhanced Usage Tracking Service
Complete usage monitoring, billing automation, and analytics
"""

import asyncio
import logging
import json
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ..core.config import settings
from ..core.database import get_db
from ..core.exceptions import UsageLimitException, ExternalServiceException, DatabaseException
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.retry_decorator import retry_async

logger = logging.getLogger(__name__)

class ServiceType(Enum):
    VOICE_SYNTHESIS = "voice_synthesis"
    SMS = "sms" 
    VOICE_CALLS = "voice_calls"
    MLS_QUERIES = "mls_queries"
    API_CALLS = "api_calls"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"

class UsageEventType(Enum):
    USAGE = "usage"
    LIMIT_WARNING = "limit_warning"
    LIMIT_EXCEEDED = "limit_exceeded"
    BILLING_GENERATED = "billing_generated"

@dataclass
class UsageRecord:
    id: Optional[str] = None
    client_id: str = ""
    service_type: ServiceType = ServiceType.API_CALLS
    quantity: float = 0.0
    unit: str = ""
    cost: float = 0.0
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class UsageLimit:
    service_type: ServiceType
    limit_type: str  # "daily", "monthly", "total"
    limit_value: float
    current_usage: float = 0.0
    reset_date: Optional[datetime] = None
    
@dataclass
class BillingPeriod:
    client_id: str
    period_start: datetime
    period_end: datetime
    subtotal: float = 0.0
    taxes: float = 0.0
    fees: float = 0.0
    total: float = 0.0
    status: str = "pending"  # pending, generated, paid, failed

class UsageService:
    """
    Complete usage tracking service with real-time monitoring and billing
    """
    
    def __init__(self):
        self.redis_client = None
        self.pricing_config = self._load_pricing_config()
        self.tier_limits = self._load_tier_limits()
        
        # Circuit breakers for external dependencies
        self.redis_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception
        )
        
        self.db_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=DatabaseException
        )
        
        # Initialize Redis connection
        asyncio.create_task(self._initialize_redis())
        
    async def _initialize_redis(self):
        """Initialize Redis connection for caching and real-time counters"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established for usage tracking")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {str(e)}")
            self.redis_client = None
            
    def _load_pricing_config(self) -> Dict[str, Any]:
        """Load comprehensive pricing configuration"""
        return {
            "voice_synthesis": {
                "unit": "characters",
                "base_price": 0.30 / 1000,  # $0.30 per 1K characters
                "tiers": {
                    "bronze": {"price": 0.35 / 1000, "included": 25000},
                    "silver": {"price": 0.30 / 1000, "included": 75000},
                    "gold": {"price": 0.25 / 1000, "included": 200000},
                    "enterprise": {"price": 0.20 / 1000, "included": 1000000}
                },
                "overage_multiplier": 1.5
            },
            "sms": {
                "unit": "messages",
                "base_price": 0.0075,
                "tiers": {
                    "bronze": {"price": 0.0075, "included": 1000},
                    "silver": {"price": 0.0070, "included": 3000},
                    "gold": {"price": 0.0065, "included": 10000},
                    "enterprise": {"price": 0.0060, "included": 50000}
                },
                "overage_multiplier": 1.3
            },
            "voice_calls": {
                "unit": "minutes",
                "base_price": 0.013,
                "tiers": {
                    "bronze": {"price": 0.013, "included": 300},
                    "silver": {"price": 0.012, "included": 1000},
                    "gold": {"price": 0.011, "included": 3000},
                    "enterprise": {"price": 0.010, "included": 15000}
                },
                "overage_multiplier": 1.4
            },
            "mls_queries": {
                "unit": "queries",
                "base_price": 0.05,
                "tiers": {
                    "bronze": {"price": 0.05, "included": 500},
                    "silver": {"price": 0.045, "included": 1500},
                    "gold": {"price": 0.040, "included": 5000},
                    "enterprise": {"price": 0.035, "included": 25000}
                },
                "overage_multiplier": 1.6
            },
            "api_calls": {
                "unit": "calls",
                "base_price": 0.001,
                "tiers": {
                    "bronze": {"price": 0.001, "included": 10000},
                    "silver": {"price": 0.0009, "included": 50000},
                    "gold": {"price": 0.0008, "included": 200000},
                    "enterprise": {"price": 0.0007, "included": 1000000}
                },
                "overage_multiplier": 1.2
            },
            "storage": {
                "unit": "gb_month",
                "base_price": 0.023,
                "tiers": {
                    "bronze": {"price": 0.023, "included": 5},
                    "silver": {"price": 0.021, "included": 20},
                    "gold": {"price": 0.019, "included": 100},
                    "enterprise": {"price": 0.017, "included": 500}
                },
                "overage_multiplier": 1.3
            },
            "bandwidth": {
                "unit": "gb",
                "base_price": 0.09,
                "tiers": {
                    "bronze": {"price": 0.09, "included": 10},
                    "silver": {"price": 0.085, "included": 50},
                    "gold": {"price": 0.08, "included": 200},
                    "enterprise": {"price": 0.075, "included": 1000}
                },
                "overage_multiplier": 1.5
            }
        }
    
    def _load_tier_limits(self) -> Dict[str, Any]:
        """Load usage limits with soft and hard limits"""
        return {
            "bronze": {
                "voice_synthesis": {"monthly_soft": 25000, "monthly_hard": 30000, "daily_hard": 2000},
                "sms": {"monthly_soft": 1000, "monthly_hard": 1200, "daily_hard": 50},
                "voice_calls": {"monthly_soft": 300, "monthly_hard": 360, "daily_hard": 20},
                "mls_queries": {"monthly_soft": 500, "monthly_hard": 600, "daily_hard": 30},
                "api_calls": {"monthly_soft": 10000, "monthly_hard": 12000, "daily_hard": 600},
                "storage": {"total_hard": 5}, 
                "bandwidth": {"monthly_hard": 10, "daily_hard": 1}
            },
            "silver": {
                "voice_synthesis": {"monthly_soft": 75000, "monthly_hard": 90000, "daily_hard": 5000},
                "sms": {"monthly_soft": 3000, "monthly_hard": 3600, "daily_hard": 150},
                "voice_calls": {"monthly_soft": 1000, "monthly_hard": 1200, "daily_hard": 60},
                "mls_queries": {"monthly_soft": 1500, "monthly_hard": 1800, "daily_hard": 80},
                "api_calls": {"monthly_soft": 50000, "monthly_hard": 60000, "daily_hard": 2500},
                "storage": {"total_hard": 20},
                "bandwidth": {"monthly_hard": 50, "daily_hard": 3}
            },
            "gold": {
                "voice_synthesis": {"monthly_soft": 200000, "monthly_hard": 240000, "daily_hard": 12000},
                "sms": {"monthly_soft": 10000, "monthly_hard": 12000, "daily_hard": 500},
                "voice_calls": {"monthly_soft": 3000, "monthly_hard": 3600, "daily_hard": 180},
                "mls_queries": {"monthly_soft": 5000, "monthly_hard": 6000, "daily_hard": 300},
                "api_calls": {"monthly_soft": 200000, "monthly_hard": 240000, "daily_hard": 12000},
                "storage": {"total_hard": 100},
                "bandwidth": {"monthly_hard": 200, "daily_hard": 10}
            },
            "enterprise": {
                "voice_synthesis": {"monthly_soft": 1000000, "monthly_hard": 1200000, "daily_hard": 50000},
                "sms": {"monthly_soft": 50000, "monthly_hard": 60000, "daily_hard": 2500},
                "voice_calls": {"monthly_soft": 15000, "monthly_hard": 18000, "daily_hard": 800},
                "mls_queries": {"monthly_soft": 25000, "monthly_hard": 30000, "daily_hard": 1500},
                "api_calls": {"monthly_soft": 1000000, "monthly_hard": 1200000, "daily_hard": 50000},
                "storage": {"total_hard": 500},
                "bandwidth": {"monthly_hard": 1000, "daily_hard": 40}
            }
        }
    
    @retry_async(max_attempts=3, backoff_factor=1.5)
    async def track_usage(
        self,
        client_id: str,
        service_type: ServiceType,
        quantity: float,
        metadata: Optional[Dict[str, Any]] = None,
        force_allow: bool = False
    ) -> Dict[str, Any]:
        """
        Track usage with comprehensive validation and real-time limits
        
        Args:
            client_id: Client identifier
            service_type: Type of service being used
            quantity: Amount of usage
            metadata: Additional metadata
            force_allow: Override usage limits (admin only)
            
        Returns:
            Usage tracking result with limits and billing info
        """
        try:
            # Get client subscription info
            client_tier, billing_period = await self._get_client_billing_info(client_id)
            
            # Check usage limits unless forced
            if not force_allow:
                limit_check = await self._check_comprehensive_limits(
                    client_id, service_type, quantity, client_tier
                )
                
                if not limit_check["allowed"]:
                    # Log limit exceeded event
                    await self._log_usage_event(
                        client_id, UsageEventType.LIMIT_EXCEEDED, {
                            "service_type": service_type.value,
                            "quantity": quantity,
                            "limit_info": limit_check
                        }
                    )
                    
                    raise UsageLimitException(
                        message=f"Usage limit exceeded for {service_type.value}",
                        limit_type=limit_check.get("limit_type"),
                        current_usage=limit_check.get("current_usage"),
                        limit=limit_check.get("limit")
                    )
            
            # Calculate cost with tier pricing
            cost_info = await self._calculate_comprehensive_cost(
                service_type, quantity, client_tier, client_id
            )
            
            # Create usage record
            usage_record = UsageRecord(
                client_id=client_id,
                service_type=service_type,
                quantity=quantity,
                unit=self.pricing_config[service_type.value]["unit"],
                cost=cost_info["total_cost"],
                metadata={
                    **(metadata or {}),
                    "tier": client_tier,
                    "billing_period": billing_period,
                    "cost_breakdown": cost_info,
                    "force_allowed": force_allow
                }
            )
            
            # Save to database and update counters
            async with self.db_circuit_breaker:
                await self._save_usage_record(usage_record)
                
            async with self.redis_circuit_breaker:
                await self._update_real_time_counters(client_id, service_type, quantity, cost_info["total_cost"])
            
            # Check for warning thresholds
            await self._check_usage_warnings(client_id, service_type, quantity, client_tier)
            
            # Update billing totals
            await self._update_billing_totals(client_id, billing_period, cost_info["total_cost"])
            
            # Log successful usage
            await self._log_usage_event(
                client_id, UsageEventType.USAGE, {
                    "service_type": service_type.value,
                    "quantity": quantity,
                    "cost": cost_info["total_cost"],
                    "usage_id": usage_record.id
                }
            )
            
            return {
                "success": True,
                "usage_id": usage_record.id,
                "client_id": client_id,
                "service_type": service_type.value,
                "quantity": quantity,
                "unit": usage_record.unit,
                "cost": cost_info["total_cost"],
                "cost_breakdown": cost_info,
                "timestamp": usage_record.timestamp.isoformat(),
                "billing_period": billing_period,
                "remaining_limits": await self._get_remaining_limits(client_id, client_tier),
                "tier": client_tier
            }
            
        except UsageLimitException:
            raise
        except Exception as e:
            logger.error(f"Usage tracking failed for {client_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "client_id": client_id,
                "service_type": service_type.value
            }
    
    async def track_api_usage(
        self,
        client_id: str,
        service: str,
        usage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track API-specific usage with service mapping
        
        Args:
            client_id: Client identifier
            service: Service name (elevenlabs, twilio, mls)
            usage_data: Usage details
            
        Returns:
            Aggregated usage tracking results
        """
        try:
            usage_records = []
            total_cost = 0.0
            
            # Map service usage to our tracking system
            if service == "elevenlabs":
                if usage_data.get("characters", 0) > 0:
                    result = await self.track_usage(
                        client_id=client_id,
                        service_type=ServiceType.VOICE_SYNTHESIS,
                        quantity=float(usage_data["characters"]),
                        metadata={
                            "service": "elevenlabs",
                            "voice_id": usage_data.get("voice_id"),
                            "model": usage_data.get("model"),
                            "streaming": usage_data.get("streaming", False)
                        }
                    )
                    usage_records.append(result)
                    if result.get("success"):
                        total_cost += result.get("cost", 0)
            
            elif service == "twilio":
                # Track SMS
                if usage_data.get("sms_sent", 0) > 0:
                    result = await self.track_usage(
                        client_id=client_id,
                        service_type=ServiceType.SMS,
                        quantity=float(usage_data["sms_sent"]),
                        metadata={
                            "service": "twilio",
                            "from_number": usage_data.get("from_number"),
                            "to_number": usage_data.get("to_number"),
                            "message_sid": usage_data.get("message_sid")
                        }
                    )
                    usage_records.append(result)
                    if result.get("success"):
                        total_cost += result.get("cost", 0)
                
                # Track voice minutes
                if usage_data.get("call_duration_minutes", 0) > 0:
                    result = await self.track_usage(
                        client_id=client_id,
                        service_type=ServiceType.VOICE_CALLS,
                        quantity=float(usage_data["call_duration_minutes"]),
                        metadata={
                            "service": "twilio",
                            "call_sid": usage_data.get("call_sid"),
                            "direction": usage_data.get("direction"),
                            "from_number": usage_data.get("from_number"),
                            "to_number": usage_data.get("to_number")
                        }
                    )
                    usage_records.append(result)
                    if result.get("success"):
                        total_cost += result.get("cost", 0)
                
                # Track API calls (for initiated calls/SMS)
                if usage_data.get("call_initiated") or usage_data.get("sms_sent"):
                    result = await self.track_usage(
                        client_id=client_id,
                        service_type=ServiceType.API_CALLS,
                        quantity=1.0,
                        metadata={
                            "service": "twilio",
                            "operation": "call" if usage_data.get("call_initiated") else "sms"
                        }
                    )
                    usage_records.append(result)
                    if result.get("success"):
                        total_cost += result.get("cost", 0)
            
            elif service == "mls":
                if usage_data.get("queries_made", 0) > 0:
                    result = await self.track_usage(
                        client_id=client_id,
                        service_type=ServiceType.MLS_QUERIES,
                        quantity=float(usage_data["queries_made"]),
                        metadata={
                            "service": "mls",
                            "query_type": usage_data.get("query_type"),
                            "results_returned": usage_data.get("results_count"),
                            "listing_id": usage_data.get("listing_id")
                        }
                    )
                    usage_records.append(result)
                    if result.get("success"):
                        total_cost += result.get("cost", 0)
            
            # Check if any tracking succeeded
            successful_records = [r for r in usage_records if r.get("success")]
            
            return {
                "success": len(successful_records) > 0,
                "service": service,
                "records": usage_records,
                "successful_records": len(successful_records),
                "total_records": len(usage_records),
                "total_cost": total_cost,
                "tracked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"API usage tracking failed for {service}: {str(e)}")
            return {
                "success": False,
                "service": service,
                "error": str(e)
            }
    
    async def _get_client_billing_info(self, client_id: str) -> Tuple[str, str]:
        """Get client tier and current billing period"""
        # This would query the client database
        # For now, return mock data
        return "silver", datetime.utcnow().strftime("%Y-%m")
    
    async def _check_comprehensive_limits(
        self,
        client_id: str,
        service_type: ServiceType,
        quantity: float,
        client_tier: str
    ) -> Dict[str, Any]:
        """Check all usage limits (daily, monthly, hard limits)"""
        try:
            tier_limits = self.tier_limits.get(client_tier, {})
            service_limits = tier_limits.get(service_type.value, {})
            
            if not service_limits:
                return {"allowed": True, "no_limits": True}
            
            # Get current usage from Redis counters
            current_usage = await self._get_current_usage_from_redis(client_id, service_type)
            
            # Check daily hard limit
            daily_hard = service_limits.get("daily_hard")
            if daily_hard and (current_usage["daily"] + quantity) > daily_hard:
                return {
                    "allowed": False,
                    "limit_type": "daily_hard",
                    "limit": daily_hard,
                    "current_usage": current_usage["daily"],
                    "requested": quantity,
                    "remaining": max(0, daily_hard - current_usage["daily"])
                }
            
            # Check monthly hard limit
            monthly_hard = service_limits.get("monthly_hard")
            if monthly_hard and (current_usage["monthly"] + quantity) > monthly_hard:
                return {
                    "allowed": False,
                    "limit_type": "monthly_hard",
                    "limit": monthly_hard,
                    "current_usage": current_usage["monthly"],
                    "requested": quantity,
                    "remaining": max(0, monthly_hard - current_usage["monthly"])
                }
            
            # Check total hard limit (for storage)
            total_hard = service_limits.get("total_hard")
            if total_hard and (current_usage["total"] + quantity) > total_hard:
                return {
                    "allowed": False,
                    "limit_type": "total_hard",
                    "limit": total_hard,
                    "current_usage": current_usage["total"],
                    "requested": quantity,
                    "remaining": max(0, total_hard - current_usage["total"])
                }
            
            return {
                "allowed": True,
                "current_usage": current_usage,
                "limits": service_limits
            }
            
        except Exception as e:
            logger.error(f"Limit check failed: {str(e)}")
            # Fail open for availability
            return {"allowed": True, "error": str(e)}
    
    async def _calculate_comprehensive_cost(
        self,
        service_type: ServiceType,
        quantity: float,
        client_tier: str,
        client_id: str
    ) -> Dict[str, Any]:
        """Calculate cost with tier pricing, included amounts, and overages"""
        try:
            service_config = self.pricing_config[service_type.value]
            tier_config = service_config["tiers"].get(client_tier)
            
            if not tier_config:
                # Fallback to base pricing
                base_price = service_config["base_price"]
                return {
                    "base_cost": quantity * base_price,
                    "overage_cost": 0.0,
                    "total_cost": quantity * base_price,
                    "included_used": 0.0,
                    "pricing_tier": "base"
                }
            
            # Get current monthly usage to calculate included vs overage
            current_monthly = await self._get_monthly_usage(client_id, service_type)
            included_amount = tier_config.get("included", 0)
            tier_price = tier_config["price"]
            
            # Calculate included and overage amounts
            total_usage = current_monthly + quantity
            
            if total_usage <= included_amount:
                # All usage is within included amount
                return {
                    "base_cost": 0.0,
                    "overage_cost": 0.0,
                    "total_cost": 0.0,
                    "included_used": quantity,
                    "included_remaining": included_amount - total_usage,
                    "pricing_tier": client_tier
                }
            elif current_monthly >= included_amount:
                # All new usage is overage
                overage_price = tier_price * service_config["overage_multiplier"]
                overage_cost = quantity * overage_price
                
                return {
                    "base_cost": 0.0,
                    "overage_cost": overage_cost,
                    "total_cost": overage_cost,
                    "included_used": 0.0,
                    "overage_used": quantity,
                    "overage_rate": overage_price,
                    "pricing_tier": client_tier
                }
            else:
                # Split between included and overage
                included_portion = included_amount - current_monthly
                overage_portion = quantity - included_portion
                overage_price = tier_price * service_config["overage_multiplier"]
                overage_cost = overage_portion * overage_price
                
                return {
                    "base_cost": 0.0,
                    "overage_cost": overage_cost,
                    "total_cost": overage_cost,
                    "included_used": included_portion,
                    "overage_used": overage_portion,
                    "overage_rate": overage_price,
                    "pricing_tier": client_tier
                }
                
        except Exception as e:
            logger.error(f"Cost calculation failed: {str(e)}")
            # Fallback calculation
            base_price = self.pricing_config[service_type.value]["base_price"]
            return {
                "total_cost": quantity * base_price,
                "error": str(e),
                "pricing_tier": "fallback"
            }
    
    async def _get_current_usage_from_redis(
        self,
        client_id: str,
        service_type: ServiceType
    ) -> Dict[str, float]:
        """Get real-time usage counters from Redis"""
        try:
            if not self.redis_client:
                return {"daily": 0.0, "monthly": 0.0, "total": 0.0}
            
            today = datetime.utcnow().strftime("%Y-%m-%d")
            month = datetime.utcnow().strftime("%Y-%m")
            
            # Get counters from Redis
            keys = [
                f"usage:{client_id}:{service_type.value}:daily:{today}",
                f"usage:{client_id}:{service_type.value}:monthly:{month}",
                f"usage:{client_id}:{service_type.value}:total"
            ]
            
            values = await self.redis_client.mget(keys)
            
            return {
                "daily": float(values[0] or 0),
                "monthly": float(values[1] or 0),
                "total": float(values[2] or 0)
            }
            
        except Exception as e:
            logger.error(f"Redis usage lookup failed: {str(e)}")
            return {"daily": 0.0, "monthly": 0.0, "total": 0.0}
    
    async def _update_real_time_counters(
        self,
        client_id: str,
        service_type: ServiceType,
        quantity: float,
        cost: float
    ):
        """Update Redis counters for real-time usage tracking"""
        try:
            if not self.redis_client:
                return
            
            today = datetime.utcnow().strftime("%Y-%m-%d")
            month = datetime.utcnow().strftime("%Y-%m")
            
            pipe = self.redis_client.pipeline()
            
            # Update usage counters
            pipe.incrbyfloat(f"usage:{client_id}:{service_type.value}:daily:{today}", quantity)
            pipe.incrbyfloat(f"usage:{client_id}:{service_type.value}:monthly:{month}", quantity)
            pipe.incrbyfloat(f"usage:{client_id}:{service_type.value}:total", quantity)
            
            # Update cost counters
            pipe.incrbyfloat(f"cost:{client_id}:{service_type.value}:daily:{today}", cost)
            pipe.incrbyfloat(f"cost:{client_id}:{service_type.value}:monthly:{month}", cost)
            pipe.incrbyfloat(f"cost:{client_id}:total", cost)
            
            # Set expiration for daily counters (keep for 7 days)
            pipe.expire(f"usage:{client_id}:{service_type.value}:daily:{today}", 604800)
            pipe.expire(f"cost:{client_id}:{service_type.value}:daily:{today}", 604800)
            
            # Set expiration for monthly counters (keep for 1 year)
            pipe.expire(f"usage:{client_id}:{service_type.value}:monthly:{month}", 31536000)
            pipe.expire(f"cost:{client_id}:{service_type.value}:monthly:{month}", 31536000)
            
            await pipe.execute()
            
        except Exception as e:
            logger.error(f"Counter update failed: {str(e)}")
    
    async def _save_usage_record(self, usage_record: UsageRecord):
        """Save usage record to database"""
        try:
            # This would save to your database
            # For now, just log the record
            logger.info(f"Usage record saved: {usage_record.client_id} - {usage_record.service_type.value} - {usage_record.quantity}")
            
        except Exception as e:
            logger.error(f"Database save failed: {str(e)}")
            raise DatabaseException(f"Failed to save usage record: {str(e)}")
    
    async def _log_usage_event(
        self,
        client_id: str,
        event_type: UsageEventType,
        event_data: Dict[str, Any]
    ):
        """Log usage events for analytics and alerting"""
        try:
            event_record = {
                "id": str(uuid.uuid4()),
                "client_id": client_id,
                "event_type": event_type.value,
                "event_data": event_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log to structured logs
            logger.info(f"Usage event: {event_type.value}", extra=event_record)
            
            # Could also send to analytics system, alerting system, etc.
            
        except Exception as e:
            logger.error(f"Event logging failed: {str(e)}")
    
    async def get_usage_summary(
        self,
        client_id: str,
        period: str = "current_month"
    ) -> Dict[str, Any]:
        """
        Get comprehensive usage summary with analytics
        
        Args:
            client_id: Client identifier
            period: Period for summary (current_month, last_month, etc.)
            
        Returns:
            Detailed usage summary with costs and analytics
        """
        try:
            # Calculate period dates
            now = datetime.utcnow()
            if period == "current_month":
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                redis_key_suffix = now.strftime("%Y-%m")
            elif period == "last_month":
                end_date = now.replace(day=1) - timedelta(days=1)
                start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                redis_key_suffix = end_date.strftime("%Y-%m")
            else:
                # Default to current month
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                redis_key_suffix = now.strftime("%Y-%m")
            
            # Get client info
            client_tier, billing_period = await self._get_client_billing_info(client_id)
            tier_limits = self.tier_limits.get(client_tier, {})
            
            # Build service usage data
            services_data = {}
            total_cost = 0.0
            
            for service_type in ServiceType:
                try:
                    # Get usage from Redis
                    usage_key = f"usage:{client_id}:{service_type.value}:monthly:{redis_key_suffix}"
                    cost_key = f"cost:{client_id}:{service_type.value}:monthly:{redis_key_suffix}"
                    
                    usage = 0.0
                    cost = 0.0
                    
                    if self.redis_client:
                        usage_val = await self.redis_client.get(usage_key)
                        cost_val = await self.redis_client.get(cost_key)
                        usage = float(usage_val or 0)
                        cost = float(cost_val or 0)
                    
                    # Get limits for this service
                    service_limits = tier_limits.get(service_type.value, {})
                    monthly_soft = service_limits.get("monthly_soft", 0)
                    monthly_hard = service_limits.get("monthly_hard", 0)
                    
                    # Calculate usage percentage
                    limit_for_percentage = monthly_soft or monthly_hard
                    percentage_used = (usage / limit_for_percentage * 100) if limit_for_percentage else 0
                    
                    services_data[service_type.value] = {
                        "usage": usage,
                        "unit": self.pricing_config[service_type.value]["unit"],
                        "cost": cost,
                        "limits": {
                            "monthly_soft": monthly_soft,
                            "monthly_hard": monthly_hard
                        },
                        "percentage_used": round(percentage_used, 1),
                        "status": self._get_usage_status(percentage_used)
                    }
                    
                    total_cost += cost
                    
                except Exception as e:
                    logger.warning(f"Failed to get usage for {service_type.value}: {str(e)}")
                    continue
            
            # Calculate projections
            days_in_period = (end_date - start_date).days + 1
            days_elapsed = (now - start_date).days + 1
            estimated_monthly_cost = (total_cost / days_elapsed) * days_in_period if days_elapsed > 0 else total_cost
            
            # Generate alerts
            alerts = []
            for service_name, service_data in services_data.items():
                percentage = service_data["percentage_used"]
                if percentage >= 95:
                    alerts.append({
                        "service": service_name,
                        "level": "critical",
                        "message": f"{service_name} usage at {percentage}% of limit"
                    })
                elif percentage >= 80:
                    alerts.append({
                        "service": service_name,
                        "level": "warning",
                        "message": f"{service_name} usage at {percentage}% of limit"
                    })
            
            return {
                "client_id": client_id,
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "subscription_tier": client_tier,
                "billing_period": billing_period,
                "services": services_data,
                "totals": {
                    "total_cost": round(total_cost, 2),
                    "estimated_monthly_cost": round(estimated_monthly_cost, 2),
                    "days_in_period": days_in_period,
                    "days_elapsed": days_elapsed
                },
                "alerts": alerts,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Usage summary failed for {client_id}: {str(e)}")
            raise ExternalServiceException("usage_service", f"Usage summary failed: {str(e)}")
    
    def _get_usage_status(self, percentage: float) -> str:
        """Get usage status based on percentage"""
        if percentage >= 95:
            return "critical"
        elif percentage >= 80:
            return "warning"
        elif percentage >= 60:
            return "moderate"
        else:
            return "normal"
    
    async def _get_monthly_usage(self, client_id: str, service_type: ServiceType) -> float:
        """Get current monthly usage for a service"""
        try:
            if not self.redis_client:
                return 0.0
            
            month = datetime.utcnow().strftime("%Y-%m")
            usage_key = f"usage:{client_id}:{service_type.value}:monthly:{month}"
            
            usage_val = await self.redis_client.get(usage_key)
            return float(usage_val or 0)
            
        except Exception as e:
            logger.error(f"Monthly usage lookup failed: {str(e)}")
            return 0.0
    
    async def _get_remaining_limits(self, client_id: str, client_tier: str) -> Dict[str, Any]:
        """Get remaining limits for all services"""
        tier_limits = self.tier_limits.get(client_tier, {})
        remaining_limits = {}
        
        for service_type in ServiceType:
            try:
                current_usage = await self._get_current_usage_from_redis(client_id, service_type)
                service_limits = tier_limits.get(service_type.value, {})
                
                remaining = {}
                for limit_type in ["daily_hard", "monthly_hard", "monthly_soft"]:
                    limit_value = service_limits.get(limit_type)
                    if limit_value:
                        usage_key = "daily" if "daily" in limit_type else "monthly"
                        remaining[limit_type] = max(0, limit_value - current_usage.get(usage_key, 0))
                
                remaining_limits[service_type.value] = remaining
                
            except Exception as e:
                logger.warning(f"Failed to get remaining limits for {service_type.value}: {str(e)}")
                continue
        
        return remaining_limits
    
    async def _check_usage_warnings(
        self,
        client_id: str,
        service_type: ServiceType,
        quantity: float,
        client_tier: str
    ):
        """Check if usage should trigger warnings"""
        try:
            tier_limits = self.tier_limits.get(client_tier, {})
            service_limits = tier_limits.get(service_type.value, {})
            
            if not service_limits:
                return
            
            current_usage = await self._get_current_usage_from_redis(client_id, service_type)
            
            # Check monthly soft limit warning (80% threshold)
            monthly_soft = service_limits.get("monthly_soft")
            if monthly_soft:
                new_monthly = current_usage["monthly"] + quantity
                percentage = (new_monthly / monthly_soft) * 100
                
                if percentage >= 80 and (current_usage["monthly"] / monthly_soft * 100) < 80:
                    # Crossed 80% threshold
                    await self._log_usage_event(
                        client_id, UsageEventType.LIMIT_WARNING, {
                            "service_type": service_type.value,
                            "limit_type": "monthly_soft",
                            "percentage": percentage,
                            "limit": monthly_soft,
                            "usage": new_monthly
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Warning check failed: {str(e)}")
    
    async def _update_billing_totals(self, client_id: str, billing_period: str, cost: float):
        """Update billing totals for the period"""
        try:
            if not self.redis_client:
                return
            
            billing_key = f"billing:{client_id}:{billing_period}"
            await self.redis_client.incrbyfloat(billing_key, cost)
            
            # Set expiration for 2 years
            await self.redis_client.expire(billing_key, 63072000)
            
        except Exception as e:
            logger.error(f"Billing total update failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for usage service"""
        try:
            health_info = {
                "service": "usage_tracking",
                "status": "healthy",
                "components": {},
                "last_checked": datetime.utcnow().isoformat()
            }
            
            # Check Redis
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                    health_info["components"]["redis"] = {"status": "healthy"}
                except Exception as e:
                    health_info["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
                    health_info["status"] = "degraded"
            else:
                health_info["components"]["redis"] = {"status": "not_configured"}
            
            # Check database connectivity would go here
            health_info["components"]["database"] = {"status": "healthy"}  # Placeholder
            
            # Check circuit breakers
            health_info["components"]["circuit_breakers"] = {
                "redis": self.redis_circuit_breaker.state,
                "database": self.db_circuit_breaker.state
            }
            
            return health_info
            
        except Exception as e:
            return {
                "service": "usage_tracking",
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }
    
    async def cleanup(self):
        """Clean up resources"""
        if self.redis_client:
            await self.redis_client.close()