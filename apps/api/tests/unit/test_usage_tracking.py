"""
Unit tests for Usage Tracking Service
Tests real-time usage monitoring and billing automation
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any
from decimal import Decimal

from app.services.usage_tracking import (
    UsageTrackingService, 
    ServiceType, 
    UsageRecord
)


class TestUsageTrackingService:
    """Comprehensive unit tests for UsageTrackingService"""
    
    @pytest.fixture
    def service(self):
        """Create UsageTrackingService instance"""
        return UsageTrackingService()
    
    @pytest.fixture
    def mock_client_id(self):
        """Mock client ID for testing"""
        return "client_test123"
    
    # Initialization Tests
    def test_load_pricing_config(self, service):
        """Test pricing configuration loading"""
        config = service._load_pricing_config()
        
        # Verify all service types have pricing
        assert "voice_synthesis" in config
        assert "sms" in config
        assert "voice_calls" in config
        assert "mls_queries" in config
        assert "api_calls" in config
        assert "storage" in config
        assert "bandwidth" in config
        
        # Verify pricing structure
        for service_name, service_config in config.items():
            assert "unit" in service_config
            assert "price_per_unit" in service_config
            assert "tiers" in service_config
            assert len(service_config["tiers"]) == 4  # bronze, silver, gold, enterprise
    
    def test_load_tier_limits(self, service):
        """Test tier limits configuration loading"""
        limits = service._load_tier_limits()
        
        # Verify all tiers exist
        assert "bronze" in limits
        assert "silver" in limits
        assert "gold" in limits
        assert "enterprise" in limits
        
        # Verify bronze tier has all services
        bronze = limits["bronze"]
        assert "voice_synthesis" in bronze
        assert "sms" in bronze
        assert "voice_calls" in bronze
        
        # Verify limits increase with tiers
        assert limits["silver"]["voice_synthesis"]["monthly_limit"] > limits["bronze"]["voice_synthesis"]["monthly_limit"]
        assert limits["gold"]["voice_synthesis"]["monthly_limit"] > limits["silver"]["voice_synthesis"]["monthly_limit"]
        assert limits["enterprise"]["voice_synthesis"]["monthly_limit"] > limits["gold"]["voice_synthesis"]["monthly_limit"]
    
    @pytest.mark.asyncio
    async def test_initialize_client_tracking_success(self, service, mock_client_id):
        """Test successful client tracking initialization"""
        with patch.object(service, '_save_tracking_record', new_callable=AsyncMock) as mock_save, \
             patch.object(service, '_configure_usage_alerts', new_callable=AsyncMock) as mock_alerts:
            
            await service.initialize_client_tracking(mock_client_id)
            
            mock_save.assert_called_once()
            mock_alerts.assert_called_once_with(mock_client_id)
            
            # Verify tracking record structure
            tracking_record = mock_save.call_args[0][0]
            assert tracking_record["client_id"] == mock_client_id
            assert "usage_by_service" in tracking_record
            assert len(tracking_record["usage_by_service"]) == len(ServiceType)
    
    @pytest.mark.asyncio
    async def test_initialize_client_tracking_failure(self, service, mock_client_id):
        """Test client tracking initialization failure handling"""
        with patch.object(service, '_save_tracking_record', new_callable=AsyncMock) as mock_save:
            mock_save.side_effect = Exception("Database error")
            
            with pytest.raises(Exception, match="Database error"):
                await service.initialize_client_tracking(mock_client_id)
    
    # Usage Tracking Tests
    @pytest.mark.asyncio
    async def test_track_usage_success(self, service, mock_client_id):
        """Test successful usage tracking"""
        service_type = ServiceType.VOICE_SYNTHESIS
        quantity = 1000.0
        metadata = {"voice_id": "test_voice", "model": "eleven_monolingual_v1"}
        
        with patch.object(service, '_get_client_tier', new_callable=AsyncMock) as mock_tier, \
             patch.object(service, '_calculate_cost', new_callable=AsyncMock) as mock_cost, \
             patch.object(service, '_check_usage_limits', new_callable=AsyncMock) as mock_limits, \
             patch.object(service, '_save_usage_record', new_callable=AsyncMock) as mock_save, \
             patch.object(service, '_update_usage_counters', new_callable=AsyncMock) as mock_update, \
             patch.object(service, '_check_usage_alerts', new_callable=AsyncMock) as mock_alerts:
            
            mock_tier.return_value = "silver"
            mock_cost.return_value = 0.30
            mock_limits.return_value = {"allowed": True, "remaining": {"daily": 2000, "monthly": 72000}}
            
            result = await service.track_usage(mock_client_id, service_type, quantity, metadata)
            
            assert result["success"] is True
            assert result["client_id"] == mock_client_id
            assert result["service"] == service_type.value
            assert result["quantity"] == quantity
            assert result["cost"] == 0.30
            assert result["unit"] == "characters"
            
            mock_save.assert_called_once()
            mock_update.assert_called_once()
            mock_alerts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_usage_limit_exceeded(self, service, mock_client_id):
        """Test usage tracking when limits are exceeded"""
        service_type = ServiceType.SMS
        quantity = 100.0
        
        with patch.object(service, '_get_client_tier', new_callable=AsyncMock) as mock_tier, \
             patch.object(service, '_calculate_cost', new_callable=AsyncMock) as mock_cost, \
             patch.object(service, '_check_usage_limits', new_callable=AsyncMock) as mock_limits, \
             patch.object(service, '_get_current_usage', new_callable=AsyncMock) as mock_current:
            
            mock_tier.return_value = "bronze"
            mock_cost.return_value = 0.75
            mock_limits.return_value = {
                "allowed": False,
                "limit_type": "daily",
                "limit": 50,
                "current": 45,
                "requested": 100,
                "remaining": 5
            }
            mock_current.return_value = {"daily": 45, "monthly": 800}
            
            result = await service.track_usage(mock_client_id, service_type, quantity)
            
            assert result["success"] is False
            assert result["error"] == "Usage limit exceeded"
            assert "limit_info" in result
            assert "current_usage" in result
    
    @pytest.mark.asyncio
    async def test_track_usage_exception_handling(self, service, mock_client_id):
        """Test usage tracking exception handling"""
        service_type = ServiceType.VOICE_CALLS
        quantity = 50.0
        
        with patch.object(service, '_get_client_tier', side_effect=Exception("Database connection failed")):
            result = await service.track_usage(mock_client_id, service_type, quantity)
            
            assert result["success"] is False
            assert "Database connection failed" in result["error"]
    
    # API Usage Tracking Tests
    @pytest.mark.asyncio
    async def test_track_api_usage_elevenlabs(self, service, mock_client_id):
        """Test ElevenLabs API usage tracking"""
        usage_data = {
            "characters": 2500,
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_monolingual_v1",
            "quality": "high"
        }
        
        with patch.object(service, 'track_usage', new_callable=AsyncMock) as mock_track:
            mock_track.return_value = {"success": True, "cost": 0.75}
            
            result = await service.track_api_usage(mock_client_id, "elevenlabs", usage_data)
            
            assert result["success"] is True
            assert result["service"] == "elevenlabs"
            assert result["total_cost"] == 0.75
            assert len(result["records"]) == 1
            
            # Verify track_usage was called with correct parameters
            mock_track.assert_called_once_with(
                mock_client_id,
                ServiceType.VOICE_SYNTHESIS,
                2500,
                {
                    "service": "elevenlabs",
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "model": "eleven_monolingual_v1",
                    "quality": "high"
                }
            )
    
    @pytest.mark.asyncio
    async def test_track_api_usage_twilio(self, service, mock_client_id):
        """Test Twilio API usage tracking"""
        usage_data = {
            "sms_sent": 5,
            "call_duration_minutes": 12.5,
            "from_number": "+1-555-999-0000",
            "to_number": "+1-555-888-1111",
            "call_sid": "CA_test123",
            "direction": "outbound"
        }
        
        with patch.object(service, 'track_usage', new_callable=AsyncMock) as mock_track:
            mock_track.side_effect = [
                {"success": True, "cost": 0.035},  # SMS cost
                {"success": True, "cost": 0.1625}  # Voice call cost
            ]
            
            result = await service.track_api_usage(mock_client_id, "twilio", usage_data)
            
            assert result["success"] is True
            assert result["service"] == "twilio"
            assert result["total_cost"] == 0.1975  # 0.035 + 0.1625
            assert len(result["records"]) == 2
            
            # Verify both SMS and voice tracking were called
            assert mock_track.call_count == 2
    
    @pytest.mark.asyncio
    async def test_track_api_usage_mls(self, service, mock_client_id):
        """Test MLS API usage tracking"""
        usage_data = {
            "queries_made": 3,
            "query_type": "property_search",
            "results_count": 45
        }
        
        with patch.object(service, 'track_usage', new_callable=AsyncMock) as mock_track:
            mock_track.return_value = {"success": True, "cost": 0.135}
            
            result = await service.track_api_usage(mock_client_id, "mls", usage_data)
            
            assert result["success"] is True
            assert result["service"] == "mls"
            assert result["total_cost"] == 0.135
            assert len(result["records"]) == 1
            
            mock_track.assert_called_once_with(
                mock_client_id,
                ServiceType.MLS_QUERIES,
                3,
                {
                    "service": "mls",
                    "query_type": "property_search",
                    "results_count": 45
                }
            )
    
    @pytest.mark.asyncio
    async def test_track_api_usage_no_usage_data(self, service, mock_client_id):
        """Test API usage tracking with no actual usage"""
        usage_data = {"characters": 0, "sms_sent": 0}
        
        result = await service.track_api_usage(mock_client_id, "elevenlabs", usage_data)
        
        assert result["success"] is True
        assert result["total_cost"] == 0
        assert len(result["records"]) == 0
    
    @pytest.mark.asyncio
    async def test_track_api_usage_error_handling(self, service, mock_client_id):
        """Test API usage tracking error handling"""
        usage_data = {"characters": 1000}
        
        with patch.object(service, 'track_usage', side_effect=Exception("Tracking error")):
            result = await service.track_api_usage(mock_client_id, "elevenlabs", usage_data)
            
            assert result["success"] is False
            assert "Tracking error" in result["error"]
    
    # Cost Calculation Tests
    @pytest.mark.asyncio
    async def test_calculate_cost_bronze_tier(self, service):
        """Test cost calculation for bronze tier"""
        service_type = ServiceType.VOICE_SYNTHESIS
        quantity = 1000.0
        client_tier = "bronze"
        
        cost = await service._calculate_cost(service_type, quantity, client_tier)
        
        # Bronze tier voice synthesis: 0.35 per 1000 characters
        expected_cost = 1000 * (0.35 / 1000)
        assert cost == expected_cost
    
    @pytest.mark.asyncio
    async def test_calculate_cost_enterprise_tier(self, service):
        """Test cost calculation for enterprise tier"""
        service_type = ServiceType.SMS
        quantity = 100.0
        client_tier = "enterprise"
        
        cost = await service._calculate_cost(service_type, quantity, client_tier)
        
        # Enterprise tier SMS: 0.0060 per message
        expected_cost = 100 * 0.0060
        assert cost == expected_cost
    
    @pytest.mark.asyncio
    async def test_calculate_cost_invalid_tier(self, service):
        """Test cost calculation with invalid tier (falls back to default)"""
        service_type = ServiceType.VOICE_CALLS
        quantity = 30.0
        client_tier = "invalid_tier"
        
        cost = await service._calculate_cost(service_type, quantity, client_tier)
        
        # Should fall back to default price_per_unit
        expected_cost = 30 * 0.013
        assert cost == expected_cost
    
    # Usage Limit Tests
    @pytest.mark.asyncio
    async def test_check_usage_limits_within_limits(self, service, mock_client_id):
        """Test usage limit check when within limits"""
        service_type = ServiceType.SMS
        quantity = 10.0
        client_tier = "bronze"
        
        with patch.object(service, '_get_current_usage', new_callable=AsyncMock) as mock_current:
            mock_current.return_value = {"daily": 20, "monthly": 400}
            
            result = await service._check_usage_limits(mock_client_id, service_type, quantity, client_tier)
            
            assert result["allowed"] is True
            assert result["remaining"]["daily"] == 20  # 50 - 20 - 10 = 20 remaining after this usage
            assert result["remaining"]["monthly"] == 590  # 1000 - 400 - 10 = 590 remaining
    
    @pytest.mark.asyncio
    async def test_check_usage_limits_daily_exceeded(self, service, mock_client_id):
        """Test usage limit check when daily limit exceeded"""
        service_type = ServiceType.SMS
        quantity = 20.0
        client_tier = "bronze"
        
        with patch.object(service, '_get_current_usage', new_callable=AsyncMock) as mock_current:
            mock_current.return_value = {"daily": 45, "monthly": 400}
            
            result = await service._check_usage_limits(mock_client_id, service_type, quantity, client_tier)
            
            assert result["allowed"] is False
            assert result["limit_type"] == "daily"
            assert result["limit"] == 50  # Bronze daily SMS limit
            assert result["current"] == 45
            assert result["requested"] == 20
            assert result["remaining"] == 5
    
    @pytest.mark.asyncio
    async def test_check_usage_limits_monthly_exceeded(self, service, mock_client_id):
        """Test usage limit check when monthly limit exceeded"""
        service_type = ServiceType.VOICE_SYNTHESIS
        quantity = 5000.0
        client_tier = "bronze"
        
        with patch.object(service, '_get_current_usage', new_callable=AsyncMock) as mock_current:
            mock_current.return_value = {"daily": 500, "monthly": 22000}
            
            result = await service._check_usage_limits(mock_client_id, service_type, quantity, client_tier)
            
            assert result["allowed"] is False
            assert result["limit_type"] == "monthly"
            assert result["limit"] == 25000  # Bronze monthly voice synthesis limit
            assert result["current"] == 22000
            assert result["requested"] == 5000
            assert result["remaining"] == 3000
    
    # Current Usage Tests
    @pytest.mark.asyncio
    async def test_get_current_usage(self, service, mock_client_id):
        """Test getting current usage"""
        service_type = ServiceType.VOICE_CALLS
        
        result = await service._get_current_usage(mock_client_id, service_type)
        
        assert "daily" in result
        assert "monthly" in result
        assert isinstance(result["daily"], float)
        assert isinstance(result["monthly"], float)
    
    @pytest.mark.asyncio
    async def test_get_client_tier(self, service, mock_client_id):
        """Test getting client tier"""
        result = await service._get_client_tier(mock_client_id)
        assert result in ["bronze", "silver", "gold", "enterprise"]
    
    # Alert Configuration Tests
    @pytest.mark.asyncio
    async def test_configure_usage_alerts(self, service, mock_client_id):
        """Test usage alerts configuration"""
        await service._configure_usage_alerts(mock_client_id)
        # Test passes if no exception is raised
    
    @pytest.mark.asyncio
    async def test_check_usage_alerts_warning(self, service, mock_client_id):
        """Test usage alert checking for warning threshold"""
        service_type = ServiceType.API_CALLS
        quantity = 100.0
        
        with patch.object(service, '_calculate_usage_percentage', new_callable=AsyncMock) as mock_percentage, \
             patch.object(service, '_send_usage_alert', new_callable=AsyncMock) as mock_alert:
            
            mock_percentage.return_value = 85.0
            
            await service._check_usage_alerts(mock_client_id, service_type, quantity)
            
            mock_alert.assert_called_once_with(mock_client_id, service_type, "warning", 85.0)
    
    @pytest.mark.asyncio
    async def test_check_usage_alerts_critical(self, service, mock_client_id):
        """Test usage alert checking for critical threshold"""
        service_type = ServiceType.VOICE_SYNTHESIS
        quantity = 1000.0
        
        with patch.object(service, '_calculate_usage_percentage', new_callable=AsyncMock) as mock_percentage, \
             patch.object(service, '_send_usage_alert', new_callable=AsyncMock) as mock_alert:
            
            mock_percentage.return_value = 97.0
            
            await service._check_usage_alerts(mock_client_id, service_type, quantity)
            
            mock_alert.assert_called_once_with(mock_client_id, service_type, "critical", 97.0)
    
    @pytest.mark.asyncio
    async def test_check_usage_alerts_no_alert(self, service, mock_client_id):
        """Test usage alert checking when no alert needed"""
        service_type = ServiceType.STORAGE
        quantity = 1.0
        
        with patch.object(service, '_calculate_usage_percentage', new_callable=AsyncMock) as mock_percentage, \
             patch.object(service, '_send_usage_alert', new_callable=AsyncMock) as mock_alert:
            
            mock_percentage.return_value = 65.0
            
            await service._check_usage_alerts(mock_client_id, service_type, quantity)
            
            mock_alert.assert_not_called()
    
    # Usage Summary Tests
    @pytest.mark.asyncio
    async def test_get_usage_summary_current_month(self, service, mock_client_id):
        """Test getting usage summary for current month"""
        with patch.object(service, '_get_client_tier', new_callable=AsyncMock) as mock_tier:
            mock_tier.return_value = "silver"
            
            result = await service.get_usage_summary(mock_client_id, "current_month")
            
            assert result["client_id"] == mock_client_id
            assert result["period"] == "current_month"
            assert result["subscription_tier"] == "silver"
            assert "services" in result
            assert "totals" in result
            assert "alerts" in result
            
            # Verify services structure
            services = result["services"]
            assert "voice_synthesis" in services
            assert "sms" in services
            assert "voice_calls" in services
            
            # Verify each service has required fields
            for service_name, service_data in services.items():
                assert "usage" in service_data
                assert "unit" in service_data
                assert "cost" in service_data
                assert "limit" in service_data
                assert "percentage_used" in service_data
    
    @pytest.mark.asyncio
    async def test_get_usage_summary_last_month(self, service, mock_client_id):
        """Test getting usage summary for last month"""
        with patch.object(service, '_get_client_tier', new_callable=AsyncMock) as mock_tier:
            mock_tier.return_value = "gold"
            
            result = await service.get_usage_summary(mock_client_id, "last_month")
            
            assert result["period"] == "last_month"
            assert result["subscription_tier"] == "gold"
            
            # Verify date range is for last month
            start_date = datetime.fromisoformat(result["start_date"])
            end_date = datetime.fromisoformat(result["end_date"])
            assert start_date < end_date
            assert start_date.day == 1  # First day of month
    
    @pytest.mark.asyncio
    async def test_get_usage_summary_custom_period(self, service, mock_client_id):
        """Test getting usage summary for custom period"""
        with patch.object(service, '_get_client_tier', new_callable=AsyncMock) as mock_tier:
            mock_tier.return_value = "enterprise"
            
            result = await service.get_usage_summary(mock_client_id, "custom_30_days")
            
            assert result["period"] == "custom_30_days"
            assert result["subscription_tier"] == "enterprise"
    
    @pytest.mark.asyncio
    async def test_get_usage_summary_error_handling(self, service, mock_client_id):
        """Test usage summary error handling"""
        with patch.object(service, '_get_client_tier', side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Database error"):
                await service.get_usage_summary(mock_client_id)
    
    # Invoice Generation Tests
    @pytest.mark.asyncio
    async def test_generate_invoice_success(self, service, mock_client_id):
        """Test successful invoice generation"""
        billing_month = "2024-01"
        
        with patch.object(service, '_get_billing_period_usage', new_callable=AsyncMock) as mock_usage, \
             patch.object(service, '_calculate_taxes', new_callable=AsyncMock) as mock_taxes, \
             patch.object(service, '_save_invoice', new_callable=AsyncMock) as mock_save:
            
            mock_usage.return_value = {
                "line_items": [
                    {"service": "Voice Synthesis", "amount": 10.50},
                    {"service": "SMS Messages", "amount": 5.25}
                ],
                "subtotal": 15.75
            }
            mock_taxes.return_value = 1.26  # 8% tax
            
            result = await service.generate_invoice(mock_client_id, billing_month)
            
            assert result["client_id"] == mock_client_id
            assert result["billing_month"] == billing_month
            assert result["invoice_id"].startswith("INV-")
            assert result["subtotal"] == 15.75
            assert result["platform_fee"] == 0.7875  # 5% of subtotal
            assert result["taxes"] == 1.26
            assert result["total_amount"] == 17.8175  # 15.75 + 0.7875 + 1.26
            assert result["currency"] == "USD"
            assert result["status"] == "pending"
            
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_invoice_error_handling(self, service, mock_client_id):
        """Test invoice generation error handling"""
        billing_month = "2024-01"
        
        with patch.object(service, '_get_billing_period_usage', side_effect=Exception("Usage data error")):
            with pytest.raises(Exception, match="Usage data error"):
                await service.generate_invoice(mock_client_id, billing_month)
    
    @pytest.mark.asyncio
    async def test_get_billing_period_usage(self, service, mock_client_id):
        """Test getting billing period usage data"""
        billing_month = "2024-01"
        
        result = await service._get_billing_period_usage(mock_client_id, billing_month)
        
        assert "line_items" in result
        assert "subtotal" in result
        assert isinstance(result["line_items"], list)
        assert len(result["line_items"]) > 0
        
        # Verify line item structure
        for item in result["line_items"]:
            assert "service" in item
            assert "quantity" in item
            assert "unit" in item
            assert "rate" in item
            assert "amount" in item
    
    @pytest.mark.asyncio
    async def test_calculate_taxes(self, service, mock_client_id):
        """Test tax calculation"""
        subtotal = 100.00
        
        taxes = await service._calculate_taxes(mock_client_id, subtotal)
        
        # 8% tax rate
        assert taxes == 8.00
    
    # Usage Analytics Tests
    @pytest.mark.asyncio
    async def test_get_usage_analytics(self, service, mock_client_id):
        """Test getting usage analytics"""
        result = await service.get_usage_analytics(mock_client_id, 30)
        
        assert result["client_id"] == mock_client_id
        assert result["period_days"] == 30
        assert "trends" in result
        assert "cost_analysis" in result
        assert "recommendations" in result
        
        # Verify trends structure
        trends = result["trends"]
        for service_name, trend_data in trends.items():
            assert "trend" in trend_data  # "increasing", "stable", or "decreasing"
            assert "change_percentage" in trend_data
            assert "daily_average" in trend_data
            assert "peak_day" in trend_data
        
        # Verify cost analysis
        cost_analysis = result["cost_analysis"]
        assert "total_cost" in cost_analysis
        assert "daily_average_cost" in cost_analysis
        assert "most_expensive_service" in cost_analysis
        assert "cost_efficiency_score" in cost_analysis
        
        # Verify recommendations
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0
    
    # Alert Management Tests
    @pytest.mark.asyncio
    async def test_set_usage_alerts_success(self, service, mock_client_id):
        """Test setting usage alerts"""
        alert_config = {
            "voice_synthesis": {"warning": 75, "critical": 90, "notifications": ["email"]},
            "sms": {"warning": 80, "critical": 95, "notifications": ["email", "webhook"]}
        }
        
        with patch.object(service, '_save_alert_configuration', new_callable=AsyncMock) as mock_save:
            result = await service.set_usage_alerts(mock_client_id, alert_config)
            
            assert result["success"] is True
            assert result["client_id"] == mock_client_id
            assert result["alerts_configured"] == 2
            assert "configuration" in result
            
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_usage_alerts_invalid_service(self, service, mock_client_id):
        """Test setting usage alerts with invalid service"""
        alert_config = {
            "invalid_service": {"warning": 80},
            "voice_synthesis": {"warning": 75}
        }
        
        with patch.object(service, '_save_alert_configuration', new_callable=AsyncMock):
            result = await service.set_usage_alerts(mock_client_id, alert_config)
            
            assert result["success"] is True
            assert result["alerts_configured"] == 1  # Only valid service configured
    
    @pytest.mark.asyncio
    async def test_set_usage_alerts_error_handling(self, service, mock_client_id):
        """Test usage alerts error handling"""
        alert_config = {"voice_synthesis": {"warning": 80}}
        
        with patch.object(service, '_save_alert_configuration', side_effect=Exception("Save error")):
            result = await service.set_usage_alerts(mock_client_id, alert_config)
            
            assert result["success"] is False
            assert "Save error" in result["error"]
    
    # Cost Breakdown Tests
    @pytest.mark.asyncio
    async def test_get_cost_breakdown(self, service, mock_client_id):
        """Test getting detailed cost breakdown"""
        with patch.object(service, 'get_usage_summary', new_callable=AsyncMock) as mock_summary:
            mock_summary.return_value = {
                "subscription_tier": "gold",
                "services": {
                    "voice_synthesis": {"usage": 50000, "cost": 12.50},
                    "sms": {"usage": 2000, "cost": 13.00}
                },
                "totals": {"total_cost": 25.50}
            }
            
            result = await service.get_cost_breakdown(mock_client_id, "current_month")
            
            assert result["client_id"] == mock_client_id
            assert result["period"] == "current_month"
            assert "breakdown_by_service" in result
            assert "cost_trends" in result
            assert "optimization_opportunities" in result
            
            # Verify breakdown structure
            breakdown = result["breakdown_by_service"]
            assert len(breakdown) == 2
            
            for service_breakdown in breakdown:
                assert "service" in service_breakdown
                assert "usage" in service_breakdown
                assert "unit" in service_breakdown
                assert "base_cost" in service_breakdown
                assert "effective_rate" in service_breakdown
                assert "tier_discount" in service_breakdown
                assert "percentage_of_total" in service_breakdown
    
    @pytest.mark.asyncio
    async def test_get_cost_breakdown_error_handling(self, service, mock_client_id):
        """Test cost breakdown error handling"""
        with patch.object(service, 'get_usage_summary', side_effect=Exception("Summary error")):
            with pytest.raises(Exception, match="Summary error"):
                await service.get_cost_breakdown(mock_client_id)


class TestUsageRecord:
    """Test UsageRecord dataclass"""
    
    def test_usage_record_creation(self):
        """Test usage record creation"""
        timestamp = datetime.utcnow()
        record = UsageRecord(
            client_id="client_test123",
            service_type=ServiceType.VOICE_SYNTHESIS,
            quantity=1000.0,
            unit="characters",
            cost=0.30,
            timestamp=timestamp,
            metadata={"voice_id": "test_voice"}
        )
        
        assert record.client_id == "client_test123"
        assert record.service_type == ServiceType.VOICE_SYNTHESIS
        assert record.quantity == 1000.0
        assert record.unit == "characters"
        assert record.cost == 0.30
        assert record.timestamp == timestamp
        assert record.metadata["voice_id"] == "test_voice"
    
    def test_usage_record_minimal(self):
        """Test usage record with minimal required fields"""
        timestamp = datetime.utcnow()
        record = UsageRecord(
            client_id="client_test123",
            service_type=ServiceType.SMS,
            quantity=5.0,
            unit="messages",
            cost=0.0375,
            timestamp=timestamp
        )
        
        assert record.metadata is None


class TestServiceType:
    """Test ServiceType enum"""
    
    def test_service_type_values(self):
        """Test all service type values"""
        assert ServiceType.VOICE_SYNTHESIS.value == "voice_synthesis"
        assert ServiceType.SMS.value == "sms"
        assert ServiceType.VOICE_CALLS.value == "voice_calls"
        assert ServiceType.MLS_QUERIES.value == "mls_queries"
        assert ServiceType.API_CALLS.value == "api_calls"
        assert ServiceType.STORAGE.value == "storage"
        assert ServiceType.BANDWIDTH.value == "bandwidth"
    
    def test_service_type_iteration(self):
        """Test service type iteration"""
        service_types = list(ServiceType)
        assert len(service_types) == 7
        assert ServiceType.VOICE_SYNTHESIS in service_types


# Performance Tests
class TestUsageTrackingPerformance:
    """Performance tests for usage tracking service"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_track_usage_performance(self, benchmark):
        """Benchmark usage tracking performance"""
        service = UsageTrackingService()
        client_id = "client_perf_test"
        service_type = ServiceType.API_CALLS
        quantity = 1.0
        
        with patch.object(service, '_get_client_tier', new_callable=AsyncMock) as mock_tier, \
             patch.object(service, '_calculate_cost', new_callable=AsyncMock) as mock_cost, \
             patch.object(service, '_check_usage_limits', new_callable=AsyncMock) as mock_limits, \
             patch.object(service, '_save_usage_record', new_callable=AsyncMock), \
             patch.object(service, '_update_usage_counters', new_callable=AsyncMock), \
             patch.object(service, '_check_usage_alerts', new_callable=AsyncMock):
            
            mock_tier.return_value = "silver"
            mock_cost.return_value = 0.001
            mock_limits.return_value = {"allowed": True, "remaining": {"daily": 2499, "monthly": 49999}}
            
            # Benchmark should complete within 50ms
            result = await benchmark(service.track_usage, client_id, service_type, quantity)
            assert result["success"] is True


# Edge Case Tests
class TestUsageTrackingEdgeCases:
    """Edge case tests for usage tracking"""
    
    @pytest.mark.asyncio
    async def test_track_zero_usage(self):
        """Test tracking zero usage"""
        service = UsageTrackingService()
        client_id = "client_edge_test"
        service_type = ServiceType.VOICE_SYNTHESIS
        quantity = 0.0
        
        with patch.object(service, '_get_client_tier', new_callable=AsyncMock) as mock_tier, \
             patch.object(service, '_calculate_cost', new_callable=AsyncMock) as mock_cost, \
             patch.object(service, '_check_usage_limits', new_callable=AsyncMock) as mock_limits, \
             patch.object(service, '_save_usage_record', new_callable=AsyncMock), \
             patch.object(service, '_update_usage_counters', new_callable=AsyncMock), \
             patch.object(service, '_check_usage_alerts', new_callable=AsyncMock):
            
            mock_tier.return_value = "bronze"
            mock_cost.return_value = 0.0
            mock_limits.return_value = {"allowed": True, "remaining": {"daily": 1000, "monthly": 25000}}
            
            result = await service.track_usage(client_id, service_type, quantity)
            
            assert result["success"] is True
            assert result["cost"] == 0.0
            assert result["quantity"] == 0.0
    
    @pytest.mark.asyncio
    async def test_track_very_large_usage(self):
        """Test tracking very large usage amounts"""
        service = UsageTrackingService()
        client_id = "client_edge_test"
        service_type = ServiceType.BANDWIDTH
        quantity = 1000000.0  # 1TB
        
        with patch.object(service, '_get_client_tier', new_callable=AsyncMock) as mock_tier, \
             patch.object(service, '_calculate_cost', new_callable=AsyncMock) as mock_cost, \
             patch.object(service, '_check_usage_limits', new_callable=AsyncMock) as mock_limits, \
             patch.object(service, '_save_usage_record', new_callable=AsyncMock), \
             patch.object(service, '_update_usage_counters', new_callable=AsyncMock), \
             patch.object(service, '_check_usage_alerts', new_callable=AsyncMock):
            
            mock_tier.return_value = "enterprise"
            mock_cost.return_value = 75000.0  # $75,000 for 1TB at enterprise rates
            mock_limits.return_value = {"allowed": True, "remaining": {"monthly": "unlimited"}}
            
            result = await service.track_usage(client_id, service_type, quantity)
            
            assert result["success"] is True
            assert result["cost"] == 75000.0
            assert result["quantity"] == 1000000.0