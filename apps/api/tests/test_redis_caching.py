"""
Redis Caching Functionality Tests
Tests for Redis caching, session management, and performance optimization
"""
import pytest
import asyncio
import json
import time
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch
import redis.asyncio as redis
from datetime import datetime, timedelta

from app.core.cache import get_redis_client, cache_key, cache_get, cache_set, cache_delete


@pytest.mark.integration
@pytest.mark.redis
class TestRedisCaching:
    """Test Redis caching functionality"""
    
    @pytest.fixture
    async def redis_client(self):
        """Get Redis client for testing"""
        client = await get_redis_client()
        await client.flushdb()  # Clean test database
        yield client
        await client.flushdb()  # Cleanup
        await client.close()
    
    @pytest.mark.asyncio
    async def test_basic_cache_operations(self, redis_client):
        """Test basic Redis cache operations"""
        # Test set and get
        key = "test:basic:key"
        value = {"data": "test_value", "timestamp": datetime.utcnow().isoformat()}
        
        await cache_set(key, value, ttl=300)
        
        retrieved_value = await cache_get(key)
        assert retrieved_value is not None
        assert retrieved_value["data"] == "test_value"
        
        # Test key exists
        exists = await redis_client.exists(key)
        assert exists == 1
        
        # Test TTL
        ttl = await redis_client.ttl(key)
        assert 250 < ttl <= 300  # Should be close to 300 seconds
        
        # Test delete
        await cache_delete(key)
        retrieved_after_delete = await cache_get(key)
        assert retrieved_after_delete is None
    
    @pytest.mark.asyncio
    async def test_voice_audio_caching(self, redis_client, elevenlabs_service, test_voice_agent):
        """Test voice audio caching functionality"""
        text = "Hello, this is a test message for audio caching"
        voice_profile = elevenlabs_service.voice_profiles["professional_male"]
        
        # Mock audio synthesis
        mock_audio_data = b"mock_audio_content_for_testing"
        elevenlabs_service._synthesize_audio = AsyncMock(return_value=mock_audio_data)
        elevenlabs_service._get_voice_profile_for_agent = Mock(return_value=voice_profile)
        elevenlabs_service._send_analytics_event = AsyncMock()
        
        # First synthesis - should cache result
        start_time = time.time()
        result1 = await elevenlabs_service.synthesize_speech(
            text=text,
            voice_agent=test_voice_agent,
            enable_caching=True
        )
        first_synthesis_time = time.time() - start_time
        
        assert not result1.cached
        assert result1.audio_data == mock_audio_data
        
        # Second synthesis - should use cached result
        start_time = time.time()
        result2 = await elevenlabs_service.synthesize_speech(
            text=text,
            voice_agent=test_voice_agent,
            enable_caching=True
        )
        second_synthesis_time = time.time() - start_time
        
        # Second call should be much faster due to caching
        assert second_synthesis_time < first_synthesis_time * 0.5
        assert result2.audio_data is not None
    
    @pytest.mark.asyncio
    async def test_session_caching(self, redis_client):
        """Test user session caching"""
        user_id = "test_user_123"
        session_data = {
            "user_id": user_id,
            "organization_id": "test_org_456",
            "role": "agent",
            "permissions": ["read_leads", "create_conversations"],
            "last_activity": datetime.utcnow().isoformat()
        }
        
        session_key = cache_key("session", user_id)
        
        # Cache session with 1 hour TTL
        await cache_set(session_key, session_data, ttl=3600)
        
        # Retrieve session
        retrieved_session = await cache_get(session_key)
        assert retrieved_session is not None
        assert retrieved_session["user_id"] == user_id
        assert retrieved_session["organization_id"] == "test_org_456"
        assert retrieved_session["role"] == "agent"
        
        # Update session activity
        session_data["last_activity"] = datetime.utcnow().isoformat()
        session_data["request_count"] = 5
        
        await cache_set(session_key, session_data, ttl=3600)
        
        # Verify update
        updated_session = await cache_get(session_key)
        assert updated_session["request_count"] == 5
    
    @pytest.mark.asyncio
    async def test_api_response_caching(self, redis_client):
        """Test API response caching"""
        # Simulate API response caching
        endpoint = "/api/v1/leads"
        params_hash = "hash_of_query_parameters"
        organization_id = "test_org_123"
        
        api_response = {
            "items": [
                {"id": "lead1", "name": "John Doe", "email": "john@example.com"},
                {"id": "lead2", "name": "Jane Smith", "email": "jane@example.com"}
            ],
            "total": 2,
            "page": 1,
            "page_size": 10
        }
        
        cache_key_name = cache_key("api_response", organization_id, endpoint, params_hash)
        
        # Cache API response with 5 minute TTL
        await cache_set(cache_key_name, api_response, ttl=300)
        
        # Retrieve cached response
        cached_response = await cache_get(cache_key_name)
        assert cached_response is not None
        assert cached_response["total"] == 2
        assert len(cached_response["items"]) == 2
        assert cached_response["items"][0]["name"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_conversation_state_caching(self, redis_client):
        """Test conversation state caching for real-time features"""
        conversation_id = "conv_123"
        conversation_state = {
            "id": conversation_id,
            "lead_id": "lead_456",
            "agent_id": "agent_789",
            "status": "active",
            "current_context": {
                "last_message": "What's your budget range?",
                "conversation_stage": "qualification",
                "lead_responses": ["Looking for a 3BR house", "Budget around 400k"]
            },
            "ai_insights": {
                "sentiment": "positive",
                "buying_signals": ["mentioned_budget", "specific_requirements"],
                "next_suggested_questions": ["Location preference?", "Timeline?"]
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
        conversation_key = cache_key("conversation_state", conversation_id)
        
        # Cache conversation state with 30 minute TTL
        await cache_set(conversation_key, conversation_state, ttl=1800)
        
        # Retrieve and verify
        cached_state = await cache_get(conversation_key)
        assert cached_state is not None
        assert cached_state["status"] == "active"
        assert cached_state["current_context"]["conversation_stage"] == "qualification"
        assert len(cached_state["ai_insights"]["buying_signals"]) == 2
        
        # Update conversation state
        conversation_state["current_context"]["lead_responses"].append("Prefer downtown area")
        conversation_state["ai_insights"]["buying_signals"].append("location_preference")
        conversation_state["last_updated"] = datetime.utcnow().isoformat()
        
        await cache_set(conversation_key, conversation_state, ttl=1800)
        
        # Verify update
        updated_state = await cache_get(conversation_key)
        assert len(updated_state["current_context"]["lead_responses"]) == 3
        assert "location_preference" in updated_state["ai_insights"]["buying_signals"]
    
    @pytest.mark.asyncio
    async def test_analytics_caching(self, redis_client):
        """Test analytics data caching"""
        organization_id = "org_123"
        date_range = "2024-01-01_to_2024-01-31"
        
        analytics_data = {
            "total_leads": 150,
            "qualified_leads": 45,
            "conversion_rate": 0.30,
            "average_response_time_ms": 1250,
            "voice_synthesis_metrics": {
                "total_syntheses": 1200,
                "average_processing_time_ms": 850,
                "cache_hit_rate": 0.75,
                "sub_2s_compliance_rate": 0.95
            },
            "agent_performance": {
                "avg_call_duration": 280,
                "avg_quality_score": 0.87
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        analytics_key = cache_key("analytics", organization_id, date_range)
        
        # Cache analytics with 1 hour TTL (since data doesn't change frequently)
        await cache_set(analytics_key, analytics_data, ttl=3600)
        
        # Retrieve cached analytics
        cached_analytics = await cache_get(analytics_key)
        assert cached_analytics is not None
        assert cached_analytics["total_leads"] == 150
        assert cached_analytics["conversion_rate"] == 0.30
        assert cached_analytics["voice_synthesis_metrics"]["cache_hit_rate"] == 0.75
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, redis_client):
        """Test cache expiration functionality"""
        key = "test:expiration:key"
        value = {"data": "expires_soon"}
        
        # Set with very short TTL
        await cache_set(key, value, ttl=2)  # 2 seconds
        
        # Verify it exists immediately
        retrieved = await cache_get(key)
        assert retrieved is not None
        assert retrieved["data"] == "expires_soon"
        
        # Wait for expiration
        await asyncio.sleep(3)
        
        # Verify it's expired
        expired_value = await cache_get(key)
        assert expired_value is None
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation utility"""
        # Test simple key
        key1 = cache_key("user", "123")
        assert key1 == "seiketsu:user:123"
        
        # Test complex key
        key2 = cache_key("api_response", "org_456", "/api/v1/leads", "filter_hash_789")
        assert key2 == "seiketsu:api_response:org_456:/api/v1/leads:filter_hash_789"
        
        # Test key with special characters (should be sanitized)
        key3 = cache_key("search", "query with spaces", "special@chars#")
        assert ":" not in key3.replace("seiketsu:", "").replace("search:", "")
    
    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self, redis_client, performance_monitor):
        """Test cache performance under concurrent load"""
        import asyncio
        
        async def cache_operation(i):
            key = f"load_test:key_{i}"
            value = {"data": f"value_{i}", "timestamp": time.time()}
            
            # Set value
            await cache_set(key, value, ttl=300)
            
            # Get value
            retrieved = await cache_get(key)
            assert retrieved is not None
            assert retrieved["data"] == f"value_{i}"
            
            return True
        
        performance_monitor.start()
        
        # Perform 100 concurrent cache operations
        tasks = [cache_operation(i) for i in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics = performance_monitor.get_metrics()
        
        # Verify all operations completed successfully
        successful_operations = sum(1 for r in results if r is True)
        assert successful_operations == 100
        
        # Verify performance (should handle 100 operations quickly)
        assert metrics["elapsed_time"] < 5.0  # Should complete in under 5 seconds
        
        # Test cache hit performance
        performance_monitor.start()
        
        # Retrieve all cached values (should be very fast)
        get_tasks = [cache_get(f"load_test:key_{i}") for i in range(100)]
        get_results = await asyncio.gather(*get_tasks)
        
        get_metrics = performance_monitor.get_metrics()
        
        # Cache hits should be very fast
        assert get_metrics["elapsed_time"] < 1.0  # Should complete in under 1 second
        assert all(result is not None for result in get_results)


@pytest.mark.integration
@pytest.mark.redis
class TestRedisConnectionHandling:
    """Test Redis connection handling and resilience"""
    
    @pytest.mark.asyncio
    async def test_connection_pool_management(self):
        """Test Redis connection pool management"""
        # Test multiple concurrent connections
        clients = []
        for i in range(10):
            client = await get_redis_client()
            clients.append(client)
        
        # Test that all clients can perform operations
        for i, client in enumerate(clients):
            await client.set(f"pool_test:{i}", f"value_{i}")
            value = await client.get(f"pool_test:{i}")
            assert value.decode() == f"value_{i}"
        
        # Clean up connections
        for client in clients:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_redis_failover_handling(self, mock_redis_client):
        """Test handling of Redis connection failures"""
        # Mock Redis connection failure
        with patch('app.core.cache.get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.side_effect = redis.ConnectionError("Connection failed")
            mock_client.set.side_effect = redis.ConnectionError("Connection failed")
            mock_get_client.return_value = mock_client
            
            # Test graceful handling of connection failures
            result = await cache_get("test:key")
            assert result is None  # Should return None on connection failure
            
            # Test that set operations don't crash
            try:
                await cache_set("test:key", {"data": "test"}, ttl=300)
                # Should not raise exception, might log error
            except Exception as e:
                # If exception is raised, it should be handled gracefully
                assert "Connection failed" in str(e)
    
    @pytest.mark.asyncio
    async def test_redis_memory_management(self, redis_client):
        """Test Redis memory usage and cleanup"""
        # Create many cache entries
        for i in range(1000):
            key = f"memory_test:key_{i}"
            value = {"data": "x" * 1000, "index": i}  # 1KB per entry
            await cache_set(key, value, ttl=60)
        
        # Check that entries exist
        sample_key = "memory_test:key_100"
        sample_value = await cache_get(sample_key)
        assert sample_value is not None
        assert sample_value["index"] == 100
        
        # Test cleanup of expired entries
        # Set some entries with very short TTL
        for i in range(10):
            key = f"expire_test:key_{i}"
            value = {"data": "temporary"}
            await cache_set(key, value, ttl=1)  # 1 second TTL
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Verify entries are expired
        expired_value = await cache_get("expire_test:key_0")
        assert expired_value is None


@pytest.mark.integration
@pytest.mark.redis
class TestCacheInvalidation:
    """Test cache invalidation strategies"""
    
    @pytest.mark.asyncio
    async def test_pattern_based_invalidation(self, redis_client):
        """Test invalidating cache entries by pattern"""
        organization_id = "org_123"
        
        # Create multiple cache entries for the organization
        cache_entries = {
            f"leads:{organization_id}:page_1": {"leads": ["lead1", "lead2"]},
            f"leads:{organization_id}:page_2": {"leads": ["lead3", "lead4"]},
            f"analytics:{organization_id}:daily": {"metrics": "daily_data"},
            f"analytics:{organization_id}:weekly": {"metrics": "weekly_data"},
            f"users:{organization_id}:active": {"users": ["user1", "user2"]}
        }
        
        # Set all cache entries
        for key, value in cache_entries.items():
            full_key = f"seiketsu:{key}"
            await redis_client.set(full_key, json.dumps(value))
        
        # Verify entries exist
        for key in cache_entries.keys():
            full_key = f"seiketsu:{key}"
            exists = await redis_client.exists(full_key)
            assert exists == 1
        
        # Invalidate all leads cache for the organization
        pattern = f"seiketsu:leads:{organization_id}:*"
        keys_to_delete = []
        
        # Get keys matching pattern
        async for key in redis_client.scan_iter(match=pattern):
            keys_to_delete.append(key)
        
        # Delete matching keys
        if keys_to_delete:
            await redis_client.delete(*keys_to_delete)
        
        # Verify leads cache is invalidated
        leads_key1 = f"seiketsu:leads:{organization_id}:page_1"
        leads_key2 = f"seiketsu:leads:{organization_id}:page_2"
        assert await redis_client.exists(leads_key1) == 0
        assert await redis_client.exists(leads_key2) == 0
        
        # Verify other caches still exist
        analytics_key = f"seiketsu:analytics:{organization_id}:daily"
        users_key = f"seiketsu:users:{organization_id}:active"
        assert await redis_client.exists(analytics_key) == 1
        assert await redis_client.exists(users_key) == 1
    
    @pytest.mark.asyncio
    async def test_time_based_invalidation(self, redis_client):
        """Test time-based cache invalidation"""
        # Create cache entries with different TTLs
        short_lived_key = "seiketsu:short_lived:data"
        medium_lived_key = "seiketsu:medium_lived:data"
        long_lived_key = "seiketsu:long_lived:data"
        
        await redis_client.setex(short_lived_key, 1, json.dumps({"type": "short"}))  # 1 second
        await redis_client.setex(medium_lived_key, 5, json.dumps({"type": "medium"}))  # 5 seconds
        await redis_client.setex(long_lived_key, 10, json.dumps({"type": "long"}))  # 10 seconds
        
        # Verify all exist initially
        assert await redis_client.exists(short_lived_key) == 1
        assert await redis_client.exists(medium_lived_key) == 1
        assert await redis_client.exists(long_lived_key) == 1
        
        # Wait for short-lived to expire
        await asyncio.sleep(2)
        
        assert await redis_client.exists(short_lived_key) == 0
        assert await redis_client.exists(medium_lived_key) == 1
        assert await redis_client.exists(long_lived_key) == 1
        
        # Wait for medium-lived to expire
        await asyncio.sleep(4)
        
        assert await redis_client.exists(short_lived_key) == 0
        assert await redis_client.exists(medium_lived_key) == 0
        assert await redis_client.exists(long_lived_key) == 1
    
    @pytest.mark.asyncio
    async def test_event_based_invalidation(self, redis_client):
        """Test event-based cache invalidation"""
        organization_id = "org_123"
        lead_id = "lead_456"
        
        # Cache lead data and related analytics
        lead_cache_key = f"seiketsu:lead:{lead_id}"
        org_analytics_key = f"seiketsu:analytics:{organization_id}:leads"
        org_dashboard_key = f"seiketsu:dashboard:{organization_id}"
        
        lead_data = {"id": lead_id, "name": "John Doe", "status": "new"}
        analytics_data = {"total_leads": 100, "qualified_leads": 30}
        dashboard_data = {"active_leads": 50, "recent_activity": []}
        
        await redis_client.set(lead_cache_key, json.dumps(lead_data))
        await redis_client.set(org_analytics_key, json.dumps(analytics_data))
        await redis_client.set(org_dashboard_key, json.dumps(dashboard_data))
        
        # Simulate lead update event - should invalidate related caches
        def invalidate_lead_related_caches(lead_id: str, organization_id: str):
            """Simulate cache invalidation on lead update"""
            keys_to_invalidate = [
                f"seiketsu:lead:{lead_id}",
                f"seiketsu:analytics:{organization_id}:leads",
                f"seiketsu:dashboard:{organization_id}"
            ]
            return keys_to_invalidate
        
        # Get keys to invalidate
        keys_to_delete = invalidate_lead_related_caches(lead_id, organization_id)
        
        # Delete the keys
        await redis_client.delete(*keys_to_delete)
        
        # Verify invalidation
        assert await redis_client.exists(lead_cache_key) == 0
        assert await redis_client.exists(org_analytics_key) == 0
        assert await redis_client.exists(org_dashboard_key) == 0