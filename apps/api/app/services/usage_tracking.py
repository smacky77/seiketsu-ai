"""
Seiketsu AI Usage Tracking Service
Real-time usage monitoring and billing automation
"""

import asyncio
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class ServiceType(Enum):
    VOICE_SYNTHESIS = "voice_synthesis"
    SMS = "sms"
    VOICE_CALLS = "voice_calls"
    MLS_QUERIES = "mls_queries"
    API_CALLS = "api_calls"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"

@dataclass
class UsageRecord:
    client_id: str
    service_type: ServiceType
    quantity: float
    unit: str
    cost: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class UsageTrackingService:
    """
    Real-time usage tracking and billing automation
    """
    
    def __init__(self):
        self.pricing_config = self._load_pricing_config()
        self.tier_limits = self._load_tier_limits()
        
    def _load_pricing_config(self) -> Dict[str, Any]:
        """
        Load pricing configuration for all services
        """
        return {
            "voice_synthesis": {
                "unit": "characters",
                "price_per_unit": 0.30 / 1000,  # $0.30 per 1K characters
                "tiers": {
                    "bronze": 0.35 / 1000,
                    "silver": 0.30 / 1000,
                    "gold": 0.25 / 1000,
                    "enterprise": 0.20 / 1000
                }
            },
            "sms": {
                "unit": "messages",
                "price_per_unit": 0.0075,  # $0.0075 per message
                "tiers": {
                    "bronze": 0.0075,
                    "silver": 0.0070,
                    "gold": 0.0065,
                    "enterprise": 0.0060
                }
            },
            "voice_calls": {
                "unit": "minutes",
                "price_per_unit": 0.013,  # $0.013 per minute
                "tiers": {
                    "bronze": 0.013,
                    "silver": 0.012,
                    "gold": 0.011,
                    "enterprise": 0.010
                }
            },
            "mls_queries": {
                "unit": "queries",
                "price_per_unit": 0.05,  # $0.05 per query
                "tiers": {
                    "bronze": 0.05,
                    "silver": 0.045,
                    "gold": 0.040,
                    "enterprise": 0.035
                }
            },
            "api_calls": {
                "unit": "calls",
                "price_per_unit": 0.001,  # $0.001 per API call
                "tiers": {
                    "bronze": 0.001,
                    "silver": 0.0009,
                    "gold": 0.0008,
                    "enterprise": 0.0007
                }
            },
            "storage": {
                "unit": "gb_month",
                "price_per_unit": 0.023,  # $0.023 per GB-month
                "tiers": {
                    "bronze": 0.023,
                    "silver": 0.021,
                    "gold": 0.019,
                    "enterprise": 0.017
                }
            },
            "bandwidth": {
                "unit": "gb",
                "price_per_unit": 0.09,  # $0.09 per GB transfer
                "tiers": {
                    "bronze": 0.09,
                    "silver": 0.085,
                    "gold": 0.08,
                    "enterprise": 0.075
                }
            }
        }
    
    def _load_tier_limits(self) -> Dict[str, Any]:
        """
        Load usage limits for each subscription tier
        """
        return {
            "bronze": {
                "voice_synthesis": {"monthly_limit": 25000, "daily_limit": 1000},
                "sms": {"monthly_limit": 1000, "daily_limit": 50},
                "voice_calls": {"monthly_limit": 300, "daily_limit": 15},  # minutes
                "mls_queries": {"monthly_limit": 500, "daily_limit": 25},
                "api_calls": {"monthly_limit": 10000, "daily_limit": 500},
                "storage": {"limit_gb": 5},
                "bandwidth": {"monthly_limit_gb": 10}
            },
            "silver": {
                "voice_synthesis": {"monthly_limit": 75000, "daily_limit": 3000},
                "sms": {"monthly_limit": 3000, "daily_limit": 150},
                "voice_calls": {"monthly_limit": 1000, "daily_limit": 50},
                "mls_queries": {"monthly_limit": 1500, "daily_limit": 75},
                "api_calls": {"monthly_limit": 50000, "daily_limit": 2500},
                "storage": {"limit_gb": 20},
                "bandwidth": {"monthly_limit_gb": 50}
            },
            "gold": {
                "voice_synthesis": {"monthly_limit": 200000, "daily_limit": 8000},
                "sms": {"monthly_limit": 10000, "daily_limit": 500},
                "voice_calls": {"monthly_limit": 3000, "daily_limit": 150},
                "mls_queries": {"monthly_limit": 5000, "daily_limit": 250},
                "api_calls": {"monthly_limit": 200000, "daily_limit": 10000},
                "storage": {"limit_gb": 100},
                "bandwidth": {"monthly_limit_gb": 200}
            },
            "enterprise": {
                "voice_synthesis": {"monthly_limit": 1000000, "daily_limit": 40000},
                "sms": {"monthly_limit": 50000, "daily_limit": 2500},
                "voice_calls": {"monthly_limit": 15000, "daily_limit": 750},
                "mls_queries": {"monthly_limit": 25000, "daily_limit": 1250},
                "api_calls": {"monthly_limit": 1000000, "daily_limit": 50000},
                "storage": {"limit_gb": 500},
                "bandwidth": {"monthly_limit_gb": 1000}
            }
        }
    
    async def initialize_client_tracking(self, client_id: str):
        """
        Initialize usage tracking for new client
        """
        try:
            logger.info(f"Initializing usage tracking for client {client_id}")
            
            # Create usage tracking records
            tracking_record = {
                "client_id": client_id,
                "initialized_at": datetime.utcnow(),
                "current_month": datetime.utcnow().strftime("%Y-%m"),
                "usage_by_service": {},
                "monthly_totals": {},
                "alerts_configured": True,
                "billing_enabled": True
            }
            
            # Initialize service counters
            for service in ServiceType:
                tracking_record["usage_by_service"][service.value] = {
                    "daily_usage": 0,
                    "monthly_usage": 0,
                    "total_cost": 0,
                    "last_reset": datetime.utcnow().isoformat()
                }
            
            # Save tracking record (mock implementation)
            await self._save_tracking_record(tracking_record)
            
            # Set up usage alerts
            await self._configure_usage_alerts(client_id)
            
            logger.info(f"Usage tracking initialized for client {client_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize usage tracking for {client_id}: {str(e)}")
            raise
    
    async def track_usage(self, client_id: str, service_type: ServiceType, quantity: float, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Track usage for a specific service
        """
        try:
            # Get client subscription tier
            client_tier = await self._get_client_tier(client_id)
            
            # Calculate cost
            cost = await self._calculate_cost(service_type, quantity, client_tier)
            
            # Check usage limits
            limit_check = await self._check_usage_limits(client_id, service_type, quantity, client_tier)
            
            if not limit_check["allowed"]:
                return {
                    "success": False,
                    "error": "Usage limit exceeded",
                    "limit_info": limit_check,
                    "current_usage": await self._get_current_usage(client_id, service_type)
                }
            
            # Create usage record
            usage_record = UsageRecord(
                client_id=client_id,
                service_type=service_type,
                quantity=quantity,
                unit=self.pricing_config[service_type.value]["unit"],
                cost=cost,
                timestamp=datetime.utcnow(),
                metadata=metadata
            )
            
            # Save usage record
            await self._save_usage_record(usage_record)
            
            # Update usage counters
            await self._update_usage_counters(client_id, service_type, quantity, cost)
            
            # Check for usage alerts
            await self._check_usage_alerts(client_id, service_type, quantity)
            
            return {
                "success": True,
                "usage_id": str(uuid.uuid4()),
                "client_id": client_id,
                "service": service_type.value,
                "quantity": quantity,
                "unit": self.pricing_config[service_type.value]["unit"],
                "cost": cost,
                "timestamp": usage_record.timestamp.isoformat(),
                "remaining_limit": limit_check["remaining"]
            }
            
        except Exception as e:
            logger.error(f"Usage tracking failed for client {client_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def track_api_usage(self, client_id: str, service: str, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track API-specific usage (ElevenLabs, Twilio, MLS)
        """
        try:
            usage_records = []
            
            if service == "elevenlabs":
                # Track character usage
                characters = usage_data.get("characters", 0)
                if characters > 0:
                    record = await self.track_usage(client_id, ServiceType.VOICE_SYNTHESIS, characters, {
                        "service": "elevenlabs",
                        "voice_id": usage_data.get("voice_id"),
                        "model": usage_data.get("model"),
                        "quality": usage_data.get("quality")
                    })
                    usage_records.append(record)
            
            elif service == "twilio":
                # Track SMS usage
                sms_count = usage_data.get("sms_sent", 0)
                if sms_count > 0:
                    record = await self.track_usage(client_id, ServiceType.SMS, sms_count, {
                        "service": "twilio",
                        "from_number": usage_data.get("from_number"),
                        "to_number": usage_data.get("to_number")
                    })
                    usage_records.append(record)
                
                # Track voice call minutes
                call_minutes = usage_data.get("call_duration_minutes", 0)
                if call_minutes > 0:
                    record = await self.track_usage(client_id, ServiceType.VOICE_CALLS, call_minutes, {
                        "service": "twilio",
                        "call_sid": usage_data.get("call_sid"),
                        "direction": usage_data.get("direction")
                    })
                    usage_records.append(record)
            
            elif service == "mls":
                # Track MLS queries
                queries = usage_data.get("queries_made", 0)
                if queries > 0:
                    record = await self.track_usage(client_id, ServiceType.MLS_QUERIES, queries, {
                        "service": "mls",
                        "query_type": usage_data.get("query_type"),
                        "results_returned": usage_data.get("results_count")
                    })
                    usage_records.append(record)
            
            # Calculate total cost for this API call
            total_cost = sum(record.get("cost", 0) for record in usage_records if record.get("success"))
            
            return {
                "success": True,
                "service": service,
                "records": usage_records,
                "total_cost": total_cost,
                "tracked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"API usage tracking failed for {service}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _calculate_cost(self, service_type: ServiceType, quantity: float, client_tier: str) -> float:
        """
        Calculate cost based on service type, quantity, and client tier
        """
        service_config = self.pricing_config[service_type.value]
        tier_pricing = service_config["tiers"]
        
        price_per_unit = tier_pricing.get(client_tier, service_config["price_per_unit"])
        return quantity * price_per_unit
    
    async def _check_usage_limits(self, client_id: str, service_type: ServiceType, quantity: float, client_tier: str) -> Dict[str, Any]:
        """
        Check if usage is within limits for client's tier
        """
        tier_limits = self.tier_limits[client_tier]
        service_limits = tier_limits.get(service_type.value, {})
        
        # Get current usage
        current_usage = await self._get_current_usage(client_id, service_type)
        
        # Check daily limit
        daily_limit = service_limits.get("daily_limit")
        if daily_limit and (current_usage["daily"] + quantity) > daily_limit:
            return {
                "allowed": False,
                "limit_type": "daily",
                "limit": daily_limit,
                "current": current_usage["daily"],
                "requested": quantity,
                "remaining": daily_limit - current_usage["daily"]
            }
        
        # Check monthly limit
        monthly_limit = service_limits.get("monthly_limit")
        if monthly_limit and (current_usage["monthly"] + quantity) > monthly_limit:
            return {
                "allowed": False,
                "limit_type": "monthly",
                "limit": monthly_limit,
                "current": current_usage["monthly"],
                "requested": quantity,
                "remaining": monthly_limit - current_usage["monthly"]
            }
        
        return {
            "allowed": True,
            "remaining": {
                "daily": (daily_limit - current_usage["daily"]) if daily_limit else "unlimited",
                "monthly": (monthly_limit - current_usage["monthly"]) if monthly_limit else "unlimited"
            }
        }
    
    async def _get_current_usage(self, client_id: str, service_type: ServiceType) -> Dict[str, float]:
        """
        Get current usage for service type
        """
        # Mock implementation - in real scenario, query from database
        return {
            "daily": 150.0,
            "monthly": 2500.0
        }
    
    async def _get_client_tier(self, client_id: str) -> str:
        """
        Get client's subscription tier
        """
        # Mock implementation - in real scenario, query from client database
        return "silver"
    
    async def _save_usage_record(self, usage_record: UsageRecord):
        """
        Save usage record to database
        """
        # Mock implementation - in real scenario, save to database
        logger.info(f"Saving usage record for client {usage_record.client_id}: {usage_record.service_type.value} = {usage_record.quantity} {usage_record.unit}")
    
    async def _save_tracking_record(self, tracking_record: Dict[str, Any]):
        """
        Save tracking record to database
        """
        # Mock implementation
        logger.info(f"Saving tracking record for client {tracking_record['client_id']}")
    
    async def _update_usage_counters(self, client_id: str, service_type: ServiceType, quantity: float, cost: float):
        """
        Update usage counters for client
        """
        # Mock implementation - in real scenario, update database counters
        logger.info(f"Updating usage counters for {client_id}: {service_type.value} +{quantity} (${cost:.4f})")
    
    async def _configure_usage_alerts(self, client_id: str):
        """
        Configure usage alert thresholds
        """
        alert_config = {
            "client_id": client_id,
            "thresholds": {
                "warning_percentage": 80,  # Alert at 80% of limit
                "critical_percentage": 95,  # Critical alert at 95% of limit
            },
            "notification_methods": ["email", "webhook"],
            "configured_at": datetime.utcnow().isoformat()
        }
        
        # Save alert configuration
        logger.info(f"Usage alerts configured for client {client_id}")
    
    async def _check_usage_alerts(self, client_id: str, service_type: ServiceType, quantity: float):
        """
        Check if usage triggers any alerts
        """
        # Get current usage percentage
        usage_percentage = await self._calculate_usage_percentage(client_id, service_type)
        
        if usage_percentage >= 95:
            await self._send_usage_alert(client_id, service_type, "critical", usage_percentage)
        elif usage_percentage >= 80:
            await self._send_usage_alert(client_id, service_type, "warning", usage_percentage)
    
    async def _calculate_usage_percentage(self, client_id: str, service_type: ServiceType) -> float:
        """
        Calculate current usage percentage of limit
        """
        # Mock implementation
        return 85.5
    
    async def _send_usage_alert(self, client_id: str, service_type: ServiceType, alert_level: str, usage_percentage: float):
        """
        Send usage alert notification
        """
        logger.warning(f"Usage alert for {client_id}: {service_type.value} at {usage_percentage:.1f}% ({alert_level})")
    
    async def get_usage_summary(self, client_id: str, period: str = "current_month") -> Dict[str, Any]:
        """
        Get usage summary for client
        """
        try:
            # Calculate period dates
            if period == "current_month":
                start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = datetime.utcnow()
            elif period == "last_month":
                end_date = datetime.utcnow().replace(day=1) - timedelta(days=1)
                start_date = end_date.replace(day=1)
            else:
                # Custom period parsing could go here
                start_date = datetime.utcnow() - timedelta(days=30)
                end_date = datetime.utcnow()
            
            # Mock usage data
            usage_summary = {
                "client_id": client_id,
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "subscription_tier": await self._get_client_tier(client_id),
                "services": {
                    "voice_synthesis": {
                        "usage": 18500,
                        "unit": "characters",
                        "cost": 5.55,
                        "limit": 25000,
                        "percentage_used": 74.0
                    },
                    "sms": {
                        "usage": 425,
                        "unit": "messages",
                        "cost": 2.98,
                        "limit": 1000,
                        "percentage_used": 42.5
                    },
                    "voice_calls": {
                        "usage": 127,
                        "unit": "minutes",
                        "cost": 1.52,
                        "limit": 300,
                        "percentage_used": 42.3
                    },
                    "mls_queries": {
                        "usage": 234,
                        "unit": "queries",
                        "cost": 10.53,
                        "limit": 500,
                        "percentage_used": 46.8
                    },
                    "api_calls": {
                        "usage": 8950,
                        "unit": "calls",
                        "cost": 8.06,
                        "limit": 10000,
                        "percentage_used": 89.5
                    }
                },
                "totals": {
                    "total_cost": 28.64,
                    "estimated_monthly": 31.50,
                    "projected_overage": 0.00
                },
                "alerts": [
                    {
                        "service": "api_calls",
                        "level": "warning",
                        "message": "API calls usage at 89.5% of monthly limit"
                    }
                ]
            }
            
            return usage_summary
            
        except Exception as e:
            logger.error(f"Failed to get usage summary for {client_id}: {str(e)}")
            raise
    
    async def generate_invoice(self, client_id: str, billing_month: str) -> Dict[str, Any]:
        """
        Generate invoice for client's usage
        """
        try:
            # Get usage data for billing month
            usage_data = await self._get_billing_period_usage(client_id, billing_month)
            
            # Calculate taxes and fees
            taxes = await self._calculate_taxes(client_id, usage_data["subtotal"])
            platform_fee = usage_data["subtotal"] * 0.05  # 5% platform fee
            
            invoice = {
                "invoice_id": f"INV-{client_id}-{billing_month.replace('-', '')}",
                "client_id": client_id,
                "billing_month": billing_month,
                "issue_date": datetime.utcnow().isoformat(),
                "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "line_items": usage_data["line_items"],
                "subtotal": usage_data["subtotal"],
                "platform_fee": platform_fee,
                "taxes": taxes,
                "total_amount": usage_data["subtotal"] + platform_fee + taxes,
                "currency": "USD",
                "status": "pending"
            }
            
            # Save invoice
            await self._save_invoice(invoice)
            
            return invoice
            
        except Exception as e:
            logger.error(f"Invoice generation failed for {client_id}: {str(e)}")
            raise
    
    async def _get_billing_period_usage(self, client_id: str, billing_month: str) -> Dict[str, Any]:
        """
        Get usage data for billing period
        """
        # Mock billing data
        return {
            "line_items": [
                {"service": "Voice Synthesis", "quantity": 18500, "unit": "characters", "rate": 0.0003, "amount": 5.55},
                {"service": "SMS Messages", "quantity": 425, "unit": "messages", "rate": 0.007, "amount": 2.98},
                {"service": "Voice Calls", "quantity": 127, "unit": "minutes", "rate": 0.012, "amount": 1.52},
                {"service": "MLS Queries", "quantity": 234, "unit": "queries", "rate": 0.045, "amount": 10.53},
                {"service": "API Calls", "quantity": 8950, "unit": "calls", "rate": 0.0009, "amount": 8.06}
            ],
            "subtotal": 28.64
        }
    
    async def _calculate_taxes(self, client_id: str, subtotal: float) -> float:
        """
        Calculate applicable taxes
        """
        # Mock tax calculation - in real scenario, use tax service
        tax_rate = 0.08  # 8% sales tax
        return subtotal * tax_rate
    
    async def _save_invoice(self, invoice: Dict[str, Any]):
        """
        Save invoice to database
        """
        logger.info(f"Saving invoice {invoice['invoice_id']} for client {invoice['client_id']}")
    
    async def get_usage_analytics(self, client_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get usage analytics and trends
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Mock analytics data
        analytics = {
            "client_id": client_id,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trends": {
                "voice_synthesis": {
                    "trend": "increasing",
                    "change_percentage": 15.3,
                    "daily_average": 617,
                    "peak_day": "2024-01-15"
                },
                "sms": {
                    "trend": "stable",
                    "change_percentage": 2.1,
                    "daily_average": 14,
                    "peak_day": "2024-01-10"
                },
                "voice_calls": {
                    "trend": "decreasing",
                    "change_percentage": -8.7,
                    "daily_average": 4.2,
                    "peak_day": "2024-01-08"
                }
            },
            "cost_analysis": {
                "total_cost": 87.65,
                "daily_average_cost": 2.92,
                "most_expensive_service": "mls_queries",
                "cost_efficiency_score": 8.2
            },
            "recommendations": [
                "Consider upgrading to Gold tier for better voice synthesis rates",
                "SMS usage is consistent - current plan is optimal",
                "Voice call usage declining - monitor for potential downgrades"
            ]
        }
        
        return analytics
    
    async def set_usage_alerts(self, client_id: str, alert_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure usage alert settings for client
        """
        try:
            # Validate alert configuration
            valid_services = [service.value for service in ServiceType]
            configured_alerts = []
            
            for service, thresholds in alert_config.items():
                if service not in valid_services:
                    continue
                
                alert_setting = {
                    "service": service,
                    "warning_threshold": thresholds.get("warning", 80),
                    "critical_threshold": thresholds.get("critical", 95),
                    "notifications": thresholds.get("notifications", ["email"])
                }
                configured_alerts.append(alert_setting)
            
            # Save alert configuration
            alert_record = {
                "client_id": client_id,
                "alerts": configured_alerts,
                "updated_at": datetime.utcnow().isoformat(),
                "enabled": True
            }
            
            await self._save_alert_configuration(alert_record)
            
            return {
                "success": True,
                "client_id": client_id,
                "alerts_configured": len(configured_alerts),
                "configuration": alert_record
            }
            
        except Exception as e:
            logger.error(f"Failed to set usage alerts for {client_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _save_alert_configuration(self, alert_record: Dict[str, Any]):
        """
        Save alert configuration to database
        """
        logger.info(f"Saving alert configuration for client {alert_record['client_id']}")
    
    async def get_cost_breakdown(self, client_id: str, period: str = "current_month") -> Dict[str, Any]:
        """
        Get detailed cost breakdown by service
        """
        try:
            # Get usage data
            usage_summary = await self.get_usage_summary(client_id, period)
            
            # Calculate cost breakdown with details
            cost_breakdown = {
                "client_id": client_id,
                "period": period,
                "breakdown_by_service": [],
                "cost_trends": {},
                "optimization_opportunities": []
            }
            
            for service_name, service_data in usage_summary["services"].items():
                service_breakdown = {
                    "service": service_name,
                    "usage": service_data["usage"],
                    "unit": service_data["unit"],
                    "base_cost": service_data["cost"],
                    "effective_rate": service_data["cost"] / service_data["usage"] if service_data["usage"] > 0 else 0,
                    "tier_discount": 0.15 if usage_summary["subscription_tier"] in ["gold", "enterprise"] else 0.05,
                    "percentage_of_total": (service_data["cost"] / usage_summary["totals"]["total_cost"]) * 100
                }
                cost_breakdown["breakdown_by_service"].append(service_breakdown)
            
            # Add optimization opportunities
            cost_breakdown["optimization_opportunities"] = [
                "Upgrade to Gold tier for 20% savings on voice synthesis",
                "Bundle SMS and voice calls for additional 10% discount",
                "Consider annual billing for 15% platform fee reduction"
            ]
            
            return cost_breakdown
            
        except Exception as e:
            logger.error(f"Failed to get cost breakdown for {client_id}: {str(e)}")
            raise