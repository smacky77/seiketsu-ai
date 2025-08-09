"""
Billing Service Integration
Stripe payments, subscription management, and usage-based billing
"""

import asyncio
import logging
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

import stripe
from stripe.error import StripeError, CardError, RateLimitError, InvalidRequestError

from ..core.config import settings
from ..core.exceptions import ExternalServiceException, RateLimitException, BusinessLogicException
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.retry_decorator import retry_async
from ..services.usage_service import UsageService

logger = logging.getLogger(__name__)

class SubscriptionTier(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    ENTERPRISE = "enterprise"

class BillingCycle(Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"

class InvoiceStatus(Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REQUIRES_ACTION = "requires_action"

@dataclass
class SubscriptionPlan:
    id: str
    name: str
    tier: SubscriptionTier
    monthly_price: Decimal
    annual_price: Decimal
    features: List[str]
    usage_limits: Dict[str, Any]
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_annual: Optional[str] = None

@dataclass
class Invoice:
    id: str
    client_id: str
    subscription_id: Optional[str]
    amount_due: Decimal
    amount_paid: Decimal
    currency: str = "usd"
    status: InvoiceStatus = InvoiceStatus.DRAFT
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    due_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    stripe_invoice_id: Optional[str] = None
    line_items: Optional[List[Dict[str, Any]]] = None

class BillingService:
    """
    Production-ready billing service with Stripe integration
    """
    
    def __init__(self):
        # Configure Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_version = "2023-10-16"  # Use stable API version
        
        self.usage_service = UsageService()
        
        # Circuit breaker for Stripe API
        self.stripe_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            expected_exception=ExternalServiceException
        )
        
        # Subscription plans configuration
        self.subscription_plans = self._load_subscription_plans()
        
        # Tax rates by location (simplified)
        self.tax_rates = self._load_tax_rates()
        
    def _load_subscription_plans(self) -> Dict[str, SubscriptionPlan]:
        """Load subscription plan configurations"""
        return {
            "bronze": SubscriptionPlan(
                id="bronze",
                name="Bronze Plan",
                tier=SubscriptionTier.BRONZE,
                monthly_price=Decimal("49.00"),
                annual_price=Decimal("490.00"),  # 2 months free
                features=[
                    "Basic voice synthesis",
                    "SMS messaging",
                    "Phone number",
                    "Basic MLS access",
                    "Email support"
                ],
                usage_limits={
                    "voice_synthesis": 25000,  # characters/month
                    "sms": 1000,  # messages/month
                    "voice_calls": 300,  # minutes/month
                    "mls_queries": 500,  # queries/month
                    "storage": 5  # GB
                },
                stripe_price_id_monthly="price_bronze_monthly",
                stripe_price_id_annual="price_bronze_annual"
            ),
            "silver": SubscriptionPlan(
                id="silver",
                name="Silver Plan",
                tier=SubscriptionTier.SILVER,
                monthly_price=Decimal("149.00"),
                annual_price=Decimal("1490.00"),
                features=[
                    "Advanced voice synthesis",
                    "SMS & MMS messaging",
                    "Multiple phone numbers",
                    "Enhanced MLS access",
                    "Call recording",
                    "Priority support"
                ],
                usage_limits={
                    "voice_synthesis": 75000,
                    "sms": 3000,
                    "voice_calls": 1000,
                    "mls_queries": 1500,
                    "storage": 20
                },
                stripe_price_id_monthly="price_silver_monthly",
                stripe_price_id_annual="price_silver_annual"
            ),
            "gold": SubscriptionPlan(
                id="gold",
                name="Gold Plan", 
                tier=SubscriptionTier.GOLD,
                monthly_price=Decimal("299.00"),
                annual_price=Decimal("2990.00"),
                features=[
                    "Premium voice synthesis",
                    "Voice cloning",
                    "Advanced SMS/MMS",
                    "Toll-free numbers",
                    "Full MLS access",
                    "Advanced analytics",
                    "API access",
                    "Dedicated support"
                ],
                usage_limits={
                    "voice_synthesis": 200000,
                    "sms": 10000,
                    "voice_calls": 3000,
                    "mls_queries": 5000,
                    "storage": 100
                },
                stripe_price_id_monthly="price_gold_monthly",
                stripe_price_id_annual="price_gold_annual"
            ),
            "enterprise": SubscriptionPlan(
                id="enterprise",
                name="Enterprise Plan",
                tier=SubscriptionTier.ENTERPRISE,
                monthly_price=Decimal("999.00"),
                annual_price=Decimal("9990.00"),
                features=[
                    "Unlimited voice synthesis",
                    "Custom voice cloning",
                    "White-label solution",
                    "Custom integrations",
                    "Dedicated infrastructure",
                    "24/7 phone support",
                    "SLA guarantees"
                ],
                usage_limits={
                    "voice_synthesis": 1000000,
                    "sms": 50000,
                    "voice_calls": 15000,
                    "mls_queries": 25000,
                    "storage": 500
                },
                stripe_price_id_monthly="price_enterprise_monthly",
                stripe_price_id_annual="price_enterprise_annual"
            )
        }
    
    def _load_tax_rates(self) -> Dict[str, Decimal]:
        """Load tax rates by location"""
        return {
            "US_DEFAULT": Decimal("0.08"),  # 8% default US sales tax
            "US_CA": Decimal("0.0725"),     # California
            "US_NY": Decimal("0.08"),       # New York
            "US_TX": Decimal("0.0625"),     # Texas
            "US_FL": Decimal("0.06"),       # Florida
            "CA": Decimal("0.05"),          # Canada GST
            "EU": Decimal("0.20"),          # EU VAT
        }
    
    @retry_async(max_attempts=3, backoff_factor=2.0)
    async def create_customer(
        self,
        client_id: str,
        email: str,
        name: str,
        phone: Optional[str] = None,
        address: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe customer
        
        Args:
            client_id: Internal client identifier
            email: Customer email
            name: Customer name
            phone: Customer phone
            address: Customer address
            metadata: Additional metadata
            
        Returns:
            Customer creation result
        """
        try:
            async with self.stripe_circuit_breaker:
                # Prepare customer data
                customer_data = {
                    "email": email,
                    "name": name,
                    "metadata": {
                        "client_id": client_id,
                        **(metadata or {})
                    }
                }
                
                if phone:
                    customer_data["phone"] = phone
                
                if address:
                    customer_data["address"] = {
                        "line1": address.get("line1", ""),
                        "line2": address.get("line2", ""),
                        "city": address.get("city", ""),
                        "state": address.get("state", ""),
                        "postal_code": address.get("postal_code", ""),
                        "country": address.get("country", "US")
                    }
                
                # Create customer in Stripe
                loop = asyncio.get_event_loop()
                customer = await loop.run_in_executor(
                    None,
                    lambda: stripe.Customer.create(**customer_data)
                )
                
                logger.info(f"Stripe customer created: {customer.id} for client {client_id}")
                
                return {
                    "success": True,
                    "customer_id": customer.id,
                    "client_id": client_id,
                    "email": email,
                    "created_at": datetime.fromtimestamp(customer.created).isoformat()
                }
                
        except CardError as e:
            logger.error(f"Card error creating customer: {e.user_message}")
            raise ExternalServiceException("stripe", f"Card error: {e.user_message}")
        except RateLimitError:
            raise RateLimitException("Stripe rate limit exceeded")
        except InvalidRequestError as e:
            logger.error(f"Invalid request creating customer: {e.user_message}")
            raise ExternalServiceException("stripe", f"Invalid request: {e.user_message}")
        except StripeError as e:
            logger.error(f"Stripe error creating customer: {str(e)}")
            raise ExternalServiceException("stripe", f"Customer creation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Customer creation failed: {str(e)}")
            raise ExternalServiceException("stripe", f"Customer creation failed: {str(e)}")
    
    @retry_async(max_attempts=3, backoff_factor=2.0)
    async def create_subscription(
        self,
        client_id: str,
        customer_id: str,
        plan_id: str,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        payment_method_id: Optional[str] = None,
        trial_period_days: Optional[int] = None,
        proration_behavior: str = "create_prorations"
    ) -> Dict[str, Any]:
        """
        Create subscription for customer
        
        Args:
            client_id: Internal client identifier
            customer_id: Stripe customer ID
            plan_id: Subscription plan ID
            billing_cycle: Monthly or annual billing
            payment_method_id: Payment method for subscription
            trial_period_days: Free trial period in days
            proration_behavior: How to handle prorations
            
        Returns:
            Subscription creation result
        """
        try:
            plan = self.subscription_plans.get(plan_id)
            if not plan:
                raise BusinessLogicException(f"Invalid plan ID: {plan_id}")
            
            # Determine price ID based on billing cycle
            if billing_cycle == BillingCycle.ANNUAL:
                stripe_price_id = plan.stripe_price_id_annual
            else:
                stripe_price_id = plan.stripe_price_id_monthly
            
            if not stripe_price_id:
                raise BusinessLogicException(f"Price ID not configured for plan {plan_id}")
            
            async with self.stripe_circuit_breaker:
                # Prepare subscription data
                subscription_data = {
                    "customer": customer_id,
                    "items": [{"price": stripe_price_id}],
                    "metadata": {
                        "client_id": client_id,
                        "plan_id": plan_id,
                        "billing_cycle": billing_cycle.value
                    },
                    "proration_behavior": proration_behavior,
                    "expand": ["latest_invoice.payment_intent"]
                }
                
                if payment_method_id:
                    subscription_data["default_payment_method"] = payment_method_id
                
                if trial_period_days:
                    subscription_data["trial_period_days"] = trial_period_days
                
                # Create subscription
                loop = asyncio.get_event_loop()
                subscription = await loop.run_in_executor(
                    None,
                    lambda: stripe.Subscription.create(**subscription_data)
                )
                
                # Process payment intent if needed
                payment_status = PaymentStatus.SUCCEEDED
                payment_intent = None
                
                if subscription.latest_invoice and subscription.latest_invoice.payment_intent:
                    payment_intent = subscription.latest_invoice.payment_intent
                    
                    if payment_intent.status == "requires_action":
                        payment_status = PaymentStatus.REQUIRES_ACTION
                    elif payment_intent.status == "requires_payment_method":
                        payment_status = PaymentStatus.FAILED
                
                logger.info(f"Subscription created: {subscription.id} for client {client_id}")
                
                return {
                    "success": True,
                    "subscription_id": subscription.id,
                    "client_id": client_id,
                    "customer_id": customer_id,
                    "plan_id": plan_id,
                    "billing_cycle": billing_cycle.value,
                    "status": subscription.status,
                    "payment_status": payment_status.value,
                    "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
                    "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                    "trial_end": datetime.fromtimestamp(subscription.trial_end).isoformat() if subscription.trial_end else None,
                    "client_secret": payment_intent.client_secret if payment_intent and payment_status == PaymentStatus.REQUIRES_ACTION else None
                }
                
        except BusinessLogicException:
            raise
        except CardError as e:
            logger.error(f"Card error creating subscription: {e.user_message}")
            raise ExternalServiceException("stripe", f"Card error: {e.user_message}")
        except StripeError as e:
            logger.error(f"Stripe error creating subscription: {str(e)}")
            raise ExternalServiceException("stripe", f"Subscription creation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Subscription creation failed: {str(e)}")
            raise ExternalServiceException("stripe", f"Subscription creation failed: {str(e)}")
    
    @retry_async(max_attempts=3, backoff_factor=2.0)
    async def create_usage_based_invoice(
        self,
        client_id: str,
        customer_id: str,
        billing_period_start: datetime,
        billing_period_end: datetime,
        usage_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create usage-based invoice for overage charges
        
        Args:
            client_id: Client identifier
            customer_id: Stripe customer ID
            billing_period_start: Start of billing period
            billing_period_end: End of billing period
            usage_data: Pre-calculated usage data (optional)
            
        Returns:
            Invoice creation result
        """
        try:
            # Get usage data if not provided
            if not usage_data:
                usage_summary = await self.usage_service.get_usage_summary(
                    client_id=client_id,
                    period="custom",
                    start_date=billing_period_start,
                    end_date=billing_period_end
                )
                usage_data = usage_summary.get("services", {})
            
            # Calculate usage charges
            line_items = []
            total_usage_charges = Decimal("0.00")
            
            for service_name, service_data in usage_data.items():
                overage_cost = service_data.get("overage_cost", 0)
                if overage_cost > 0:
                    line_items.append({
                        "description": f"{service_name.replace('_', ' ').title()} Overage",
                        "quantity": service_data.get("overage_usage", 0),
                        "unit_price": service_data.get("overage_rate", 0),
                        "amount": overage_cost
                    })
                    total_usage_charges += Decimal(str(overage_cost))
            
            # Skip if no usage charges
            if total_usage_charges <= 0:
                return {
                    "success": True,
                    "invoice_created": False,
                    "message": "No usage charges for period",
                    "total_charges": 0.00
                }
            
            async with self.stripe_circuit_breaker:
                # Create invoice in Stripe
                loop = asyncio.get_event_loop()
                
                # Create invoice
                invoice = await loop.run_in_executor(
                    None,
                    lambda: stripe.Invoice.create(
                        customer=customer_id,
                        description=f"Usage charges for {billing_period_start.strftime('%B %Y')}",
                        metadata={
                            "client_id": client_id,
                            "billing_period_start": billing_period_start.isoformat(),
                            "billing_period_end": billing_period_end.isoformat(),
                            "invoice_type": "usage_based"
                        },
                        auto_advance=False,  # Don't auto-finalize
                        collection_method="charge_automatically"
                    )
                )
                
                # Add line items
                for item in line_items:
                    await loop.run_in_executor(
                        None,
                        lambda i=item: stripe.InvoiceItem.create(
                            customer=customer_id,
                            invoice=invoice.id,
                            description=i["description"],
                            quantity=int(i["quantity"]),
                            unit_amount=int(Decimal(str(i["unit_price"])) * 100),  # Convert to cents
                            currency="usd"
                        )
                    )
                
                # Calculate taxes
                tax_amount = await self._calculate_invoice_taxes(
                    customer_id, total_usage_charges
                )
                
                if tax_amount > 0:
                    await loop.run_in_executor(
                        None,
                        lambda: stripe.InvoiceItem.create(
                            customer=customer_id,
                            invoice=invoice.id,
                            description="Sales Tax",
                            unit_amount=int(tax_amount * 100),
                            currency="usd"
                        )
                    )
                
                # Finalize and send invoice
                final_invoice = await loop.run_in_executor(
                    None,
                    lambda: invoice.finalize_invoice()
                )
                
                logger.info(f"Usage invoice created: {final_invoice.id} for client {client_id}")
                
                return {
                    "success": True,
                    "invoice_created": True,
                    "invoice_id": final_invoice.id,
                    "client_id": client_id,
                    "customer_id": customer_id,
                    "total_charges": float(total_usage_charges),
                    "tax_amount": float(tax_amount),
                    "total_amount": float(total_usage_charges + tax_amount),
                    "line_items": line_items,
                    "due_date": datetime.fromtimestamp(final_invoice.due_date).isoformat() if final_invoice.due_date else None,
                    "invoice_url": final_invoice.hosted_invoice_url
                }
                
        except StripeError as e:
            logger.error(f"Stripe error creating usage invoice: {str(e)}")
            raise ExternalServiceException("stripe", f"Usage invoice creation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Usage invoice creation failed: {str(e)}")
            raise ExternalServiceException("stripe", f"Usage invoice creation failed: {str(e)}")
    
    async def _calculate_invoice_taxes(
        self,
        customer_id: str,
        subtotal: Decimal
    ) -> Decimal:
        """Calculate taxes for invoice based on customer location"""
        try:
            # Get customer details to determine tax location
            loop = asyncio.get_event_loop()
            customer = await loop.run_in_executor(
                None,
                lambda: stripe.Customer.retrieve(customer_id)
            )
            
            # Determine tax rate based on location
            tax_rate = Decimal("0.00")
            
            if customer.address:
                country = customer.address.country
                state = customer.address.state
                
                if country == "US":
                    if state:
                        tax_key = f"US_{state}"
                        tax_rate = self.tax_rates.get(tax_key, self.tax_rates["US_DEFAULT"])
                    else:
                        tax_rate = self.tax_rates["US_DEFAULT"]
                elif country == "CA":
                    tax_rate = self.tax_rates["CA"]
                elif country in ["GB", "DE", "FR", "IT", "ES", "NL"]:  # EU countries
                    tax_rate = self.tax_rates["EU"]
            else:
                # Default to US tax rate
                tax_rate = self.tax_rates["US_DEFAULT"]
            
            return (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            
        except Exception as e:
            logger.warning(f"Tax calculation failed: {str(e)}")
            # Return default tax rate on error
            return (subtotal * self.tax_rates["US_DEFAULT"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @retry_async(max_attempts=3, backoff_factor=2.0)
    async def update_subscription(
        self,
        subscription_id: str,
        new_plan_id: Optional[str] = None,
        billing_cycle: Optional[BillingCycle] = None,
        proration_behavior: str = "create_prorations"
    ) -> Dict[str, Any]:
        """
        Update existing subscription
        
        Args:
            subscription_id: Stripe subscription ID
            new_plan_id: New plan to change to
            billing_cycle: Change billing cycle
            proration_behavior: How to handle prorations
            
        Returns:
            Update result
        """
        try:
            async with self.stripe_circuit_breaker:
                loop = asyncio.get_event_loop()
                
                # Get current subscription
                subscription = await loop.run_in_executor(
                    None,
                    lambda: stripe.Subscription.retrieve(subscription_id)
                )
                
                update_data = {
                    "proration_behavior": proration_behavior
                }
                
                # Update plan if provided
                if new_plan_id:
                    plan = self.subscription_plans.get(new_plan_id)
                    if not plan:
                        raise BusinessLogicException(f"Invalid plan ID: {new_plan_id}")
                    
                    # Determine price ID
                    current_billing_cycle = billing_cycle or BillingCycle.MONTHLY
                    if current_billing_cycle == BillingCycle.ANNUAL:
                        new_price_id = plan.stripe_price_id_annual
                    else:
                        new_price_id = plan.stripe_price_id_monthly
                    
                    # Update subscription items
                    update_data["items"] = [
                        {
                            "id": subscription["items"]["data"][0]["id"],
                            "price": new_price_id
                        }
                    ]
                    
                    # Update metadata
                    update_data["metadata"] = {
                        **subscription.metadata,
                        "plan_id": new_plan_id,
                        "billing_cycle": current_billing_cycle.value,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                
                # Update subscription
                updated_subscription = await loop.run_in_executor(
                    None,
                    lambda: stripe.Subscription.modify(subscription_id, **update_data)
                )
                
                logger.info(f"Subscription updated: {subscription_id}")
                
                return {
                    "success": True,
                    "subscription_id": updated_subscription.id,
                    "status": updated_subscription.status,
                    "current_period_start": datetime.fromtimestamp(updated_subscription.current_period_start).isoformat(),
                    "current_period_end": datetime.fromtimestamp(updated_subscription.current_period_end).isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
        except BusinessLogicException:
            raise
        except StripeError as e:
            logger.error(f"Stripe error updating subscription: {str(e)}")
            raise ExternalServiceException("stripe", f"Subscription update failed: {str(e)}")
        except Exception as e:
            logger.error(f"Subscription update failed: {str(e)}")
            raise ExternalServiceException("stripe", f"Subscription update failed: {str(e)}")
    
    @retry_async(max_attempts=3, backoff_factor=2.0)
    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
        cancellation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel subscription
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Cancel at end of current period
            cancellation_reason: Reason for cancellation
            
        Returns:
            Cancellation result
        """
        try:
            async with self.stripe_circuit_breaker:
                loop = asyncio.get_event_loop()
                
                if at_period_end:
                    # Schedule cancellation at period end
                    subscription = await loop.run_in_executor(
                        None,
                        lambda: stripe.Subscription.modify(
                            subscription_id,
                            cancel_at_period_end=True,
                            metadata={
                                "cancellation_reason": cancellation_reason or "customer_request",
                                "cancellation_date": datetime.utcnow().isoformat()
                            }
                        )
                    )
                    
                    return {
                        "success": True,
                        "subscription_id": subscription.id,
                        "status": subscription.status,
                        "cancel_at_period_end": subscription.cancel_at_period_end,
                        "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                        "message": "Subscription will be canceled at the end of the current billing period"
                    }
                else:
                    # Cancel immediately
                    subscription = await loop.run_in_executor(
                        None,
                        lambda: stripe.Subscription.cancel(subscription_id)
                    )
                    
                    return {
                        "success": True,
                        "subscription_id": subscription.id,
                        "status": subscription.status,
                        "canceled_at": datetime.fromtimestamp(subscription.canceled_at).isoformat(),
                        "message": "Subscription canceled immediately"
                    }
                    
        except StripeError as e:
            logger.error(f"Stripe error canceling subscription: {str(e)}")
            raise ExternalServiceException("stripe", f"Subscription cancellation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Subscription cancellation failed: {str(e)}")
            raise ExternalServiceException("stripe", f"Subscription cancellation failed: {str(e)}")
    
    async def handle_webhook(
        self,
        payload: str,
        signature: str,
        webhook_secret: str
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook events
        
        Args:
            payload: Webhook payload
            signature: Stripe signature
            webhook_secret: Webhook endpoint secret
            
        Returns:
            Webhook handling result
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            
            event_type = event["type"]
            event_data = event["data"]["object"]
            
            logger.info(f"Processing Stripe webhook: {event_type}")
            
            # Handle different event types
            if event_type == "customer.subscription.created":
                await self._handle_subscription_created(event_data)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(event_data)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_canceled(event_data)
            elif event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(event_data)
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failed(event_data)
            elif event_type == "customer.subscription.trial_will_end":
                await self._handle_trial_ending(event_data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
            
            return {
                "success": True,
                "event_type": event_type,
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            raise ExternalServiceException("stripe", "Invalid webhook signature")
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            raise ExternalServiceException("stripe", f"Webhook processing failed: {str(e)}")
    
    async def _handle_subscription_created(self, subscription_data: Dict[str, Any]):
        """Handle subscription created webhook"""
        client_id = subscription_data.get("metadata", {}).get("client_id")
        if client_id:
            logger.info(f"Subscription created for client {client_id}: {subscription_data['id']}")
            # Update client subscription status in database
            # Send welcome email, etc.
    
    async def _handle_subscription_updated(self, subscription_data: Dict[str, Any]):
        """Handle subscription updated webhook"""
        client_id = subscription_data.get("metadata", {}).get("client_id")
        if client_id:
            logger.info(f"Subscription updated for client {client_id}: {subscription_data['id']}")
            # Update client subscription status in database
    
    async def _handle_subscription_canceled(self, subscription_data: Dict[str, Any]):
        """Handle subscription canceled webhook"""
        client_id = subscription_data.get("metadata", {}).get("client_id")
        if client_id:
            logger.info(f"Subscription canceled for client {client_id}: {subscription_data['id']}")
            # Update client status, disable services, send notification
    
    async def _handle_payment_succeeded(self, invoice_data: Dict[str, Any]):
        """Handle successful payment webhook"""
        customer_id = invoice_data.get("customer")
        if customer_id:
            logger.info(f"Payment succeeded for customer {customer_id}: {invoice_data['id']}")
            # Update payment status, send receipt, etc.
    
    async def _handle_payment_failed(self, invoice_data: Dict[str, Any]):
        """Handle failed payment webhook"""
        customer_id = invoice_data.get("customer")
        if customer_id:
            logger.warning(f"Payment failed for customer {customer_id}: {invoice_data['id']}")
            # Send notification, retry payment, etc.
    
    async def _handle_trial_ending(self, subscription_data: Dict[str, Any]):
        """Handle trial ending webhook"""
        client_id = subscription_data.get("metadata", {}).get("client_id")
        if client_id:
            logger.info(f"Trial ending for client {client_id}: {subscription_data['id']}")
            # Send trial ending notification
    
    async def get_billing_summary(
        self,
        client_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Get billing summary for client
        
        Args:
            client_id: Client identifier
            customer_id: Stripe customer ID
            
        Returns:
            Billing summary with subscription and usage details
        """
        try:
            async with self.stripe_circuit_breaker:
                loop = asyncio.get_event_loop()
                
                # Get customer details
                customer = await loop.run_in_executor(
                    None,
                    lambda: stripe.Customer.retrieve(customer_id)
                )
                
                # Get active subscriptions
                subscriptions = await loop.run_in_executor(
                    None,
                    lambda: stripe.Subscription.list(
                        customer=customer_id,
                        status="active",
                        limit=10
                    )
                )
                
                # Get recent invoices
                invoices = await loop.run_in_executor(
                    None,
                    lambda: stripe.Invoice.list(
                        customer=customer_id,
                        limit=10
                    )
                )
                
                # Get usage summary
                usage_summary = await self.usage_service.get_usage_summary(client_id)
                
                # Build billing summary
                subscription_info = None
                if subscriptions.data:
                    sub = subscriptions.data[0]  # Get first active subscription
                    plan_id = sub.metadata.get("plan_id", "unknown")
                    
                    subscription_info = {
                        "id": sub.id,
                        "status": sub.status,
                        "plan_id": plan_id,
                        "plan_name": self.subscription_plans.get(plan_id, {}).get("name", "Unknown Plan"),
                        "billing_cycle": sub.metadata.get("billing_cycle", "monthly"),
                        "current_period_start": datetime.fromtimestamp(sub.current_period_start).isoformat(),
                        "current_period_end": datetime.fromtimestamp(sub.current_period_end).isoformat(),
                        "trial_end": datetime.fromtimestamp(sub.trial_end).isoformat() if sub.trial_end else None,
                        "cancel_at_period_end": sub.cancel_at_period_end
                    }
                
                invoice_history = []
                for invoice in invoices.data:
                    invoice_history.append({
                        "id": invoice.id,
                        "amount_due": invoice.amount_due / 100,  # Convert from cents
                        "amount_paid": invoice.amount_paid / 100,
                        "status": invoice.status,
                        "created": datetime.fromtimestamp(invoice.created).isoformat(),
                        "due_date": datetime.fromtimestamp(invoice.due_date).isoformat() if invoice.due_date else None,
                        "invoice_url": invoice.hosted_invoice_url
                    })
                
                return {
                    "success": True,
                    "client_id": client_id,
                    "customer": {
                        "id": customer.id,
                        "email": customer.email,
                        "name": customer.name
                    },
                    "subscription": subscription_info,
                    "invoices": invoice_history,
                    "usage_summary": usage_summary,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
        except StripeError as e:
            logger.error(f"Stripe error getting billing summary: {str(e)}")
            raise ExternalServiceException("stripe", f"Billing summary failed: {str(e)}")
        except Exception as e:
            logger.error(f"Billing summary failed: {str(e)}")
            raise ExternalServiceException("stripe", f"Billing summary failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for billing service"""
        try:
            # Test Stripe API connectivity
            loop = asyncio.get_event_loop()
            
            start_time = time.time()
            account = await loop.run_in_executor(
                None,
                lambda: stripe.Account.retrieve()
            )
            response_time = time.time() - start_time
            
            return {
                "service": "billing",
                "status": "healthy",
                "stripe_account_id": account.id,
                "response_time": response_time,
                "circuit_breaker_state": self.stripe_circuit_breaker.state,
                "plans_configured": len(self.subscription_plans),
                "last_checked": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "service": "billing",
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker_state": self.stripe_circuit_breaker.state,
                "last_checked": datetime.utcnow().isoformat()
            }