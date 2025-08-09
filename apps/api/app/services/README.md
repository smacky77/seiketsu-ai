# Seiketsu AI Third-Party Service Integrations

This directory contains comprehensive, production-ready integrations for all third-party services used by the Seiketsu AI platform.

## Services Implemented

### 1. ElevenLabs Voice Service (`elevenlabs_service.py`)
**Real-time voice synthesis with streaming support**

**Features:**
- ✅ Voice synthesis with sub-2s response times
- ✅ Real-time streaming for live conversations
- ✅ Voice cloning capabilities
- ✅ Multiple voice models (Turbo V2, Multilingual V2, Monolingual V1)
- ✅ Comprehensive error handling and retry logic
- ✅ Rate limiting and circuit breaker protection
- ✅ Usage tracking integration
- ✅ Caching for performance optimization

**Key Methods:**
- `synthesize_speech()` - Standard voice synthesis
- `synthesize_speech_streaming()` - Real-time streaming synthesis
- `clone_voice()` - Create custom voice profiles
- `get_voices()` - Retrieve available voices with caching

### 2. Twilio Service (`twilio_service.py`)
**SMS, Voice, and Phone Number Management**

**Features:**
- ✅ SMS message sending with delivery tracking
- ✅ Voice call initiation and management
- ✅ Phone number provisioning and configuration
- ✅ Webhook handling for incoming communications
- ✅ Call recording and transcription support
- ✅ Usage tracking per tenant
- ✅ Cost tracking and billing integration
- ✅ Comprehensive error handling

**Key Methods:**
- `send_sms()` - Send SMS messages
- `make_call()` - Initiate voice calls
- `purchase_phone_number()` - Buy and configure phone numbers
- `handle_webhook()` - Process incoming webhooks
- `get_call_details()` - Retrieve call information
- `get_message_details()` - Retrieve message information

### 3. MLS Service (`mls_service.py`)
**Real Estate Listing Data Integration**

**Features:**
- ✅ Property search with advanced filtering
- ✅ Individual property detail lookup
- ✅ Market statistics and analytics
- ✅ Photo and media management
- ✅ Data caching for performance
- ✅ Rate limit handling
- ✅ Usage tracking integration
- ✅ Comprehensive error handling

**Key Methods:**
- `search_properties()` - Search listings with filters
- `get_property_by_id()` - Get detailed property information
- `get_market_statistics()` - Generate market analytics
- `clear_cache()` - Cache management

### 4. Usage Tracking Service (`usage_service.py`)
**Real-time Usage Monitoring and Billing Automation**

**Features:**
- ✅ Real-time usage tracking per service
- ✅ Multi-tier limit enforcement (daily, monthly, total)
- ✅ Cost calculation with tier-based pricing
- ✅ Overage detection and billing
- ✅ Usage analytics and trending
- ✅ Alert system for limit warnings
- ✅ Redis-backed real-time counters
- ✅ Comprehensive usage reporting

**Key Methods:**
- `track_usage()` - Record service usage
- `track_api_usage()` - Track third-party API usage
- `get_usage_summary()` - Generate usage reports
- `get_usage_analytics()` - Usage trends and insights

### 5. Billing Service (`billing_service.py`)
**Stripe Payment Processing and Subscription Management**

**Features:**
- ✅ Stripe customer management
- ✅ Subscription creation and updates
- ✅ Usage-based invoice generation
- ✅ Multiple subscription tiers (Bronze, Silver, Gold, Enterprise)
- ✅ Tax calculation by location
- ✅ Webhook event handling
- ✅ Payment method management
- ✅ Comprehensive billing analytics

**Key Methods:**
- `create_customer()` - Create Stripe customers
- `create_subscription()` - Set up subscriptions
- `create_usage_based_invoice()` - Generate usage invoices
- `handle_webhook()` - Process Stripe webhooks
- `get_billing_summary()` - Complete billing overview

## Utility Classes

### Circuit Breaker (`utils/circuit_breaker.py`)
- Fault tolerance for external service calls
- Automatic failure detection and recovery
- Configurable thresholds and timeouts

### Rate Limiter (`utils/rate_limiter.py`)
- Token bucket and sliding window algorithms
- Per-key rate limiting
- Burst capacity handling

### Retry Decorator (`utils/retry_decorator.py`)
- Exponential backoff retry logic
- Configurable attempt limits
- Exception-specific retry rules

## Configuration

All services are configured through environment variables in `core/config.py`:

```python
# ElevenLabs
ELEVEN_LABS_API_KEY = "your_elevenlabs_key"
ELEVEN_LABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Twilio  
TWILIO_ACCOUNT_SID = "your_twilio_sid"
TWILIO_AUTH_TOKEN = "your_twilio_token"

# Stripe
STRIPE_SECRET_KEY = "your_stripe_secret"
STRIPE_WEBHOOK_SECRET = "your_webhook_secret"

# MLS
MLS_API_KEY = "your_mls_key"
MLS_BASE_URL = "https://api.mlsgrid.com/v2"

# Redis for caching and counters
REDIS_URL = "redis://localhost:6379/0"
```

## Usage Examples

### Voice Synthesis
```python
from app.services import service_manager

# Initialize services
await service_manager.initialize_services()

# Synthesize speech
result = await service_manager.elevenlabs.synthesize_speech(
    text="Hello, this is your AI real estate agent",
    voice_id="21m00Tcm4TlvDq8ikWAM",
    client_id="client_123"
)
```

### SMS Sending
```python
# Send SMS
result = await service_manager.twilio.send_sms(
    to="+1234567890",
    message="Your property showing is confirmed for 3 PM",
    from_number="+1987654321",
    client_id="client_123"
)
```

### Property Search
```python
from app.services.mls_service import PropertySearchFilters

# Search properties
filters = PropertySearchFilters(
    min_price=300000,
    max_price=500000,
    min_beds=3,
    cities=["Austin", "Dallas"]
)

results = await service_manager.mls.search_properties(
    filters=filters,
    client_id="client_123",
    limit=20
)
```

### Usage Tracking
```python
# Track voice synthesis usage
await service_manager.usage.track_usage(
    client_id="client_123",
    service_type=ServiceType.VOICE_SYNTHESIS,
    quantity=150.0  # characters
)

# Get usage summary
summary = await service_manager.usage.get_usage_summary(
    client_id="client_123"
)
```

## Production Considerations

### Monitoring & Health Checks
All services implement health checks:
```python
# Check all service health
health_status = await service_manager.health_check_all()
```

### Error Handling
- Circuit breakers prevent cascading failures
- Retry logic handles transient errors
- Comprehensive exception types for different failure modes

### Performance
- Redis caching for frequently accessed data
- Connection pooling for HTTP clients
- Rate limiting to prevent API overuse

### Security
- API key management through environment variables
- Request validation and sanitization
- Webhook signature verification

### Scalability
- Async/await throughout for non-blocking operations
- Connection reuse and pooling
- Efficient data structures and algorithms

## Testing

Each service includes comprehensive error handling and can be tested individually:

```python
# Test ElevenLabs connectivity
health = await elevenlabs_service.health_check()
assert health["status"] == "healthy"

# Test Twilio SMS
result = await twilio_service.send_sms(...)
assert result["success"] == True
```

## Deployment

1. Set all required environment variables
2. Install dependencies: `pip install -r requirements.txt`
3. Initialize services: `await service_manager.initialize_services()`
4. Services are ready for production use

This implementation provides enterprise-grade reliability, monitoring, and scalability for all third-party integrations in the Seiketsu AI platform.