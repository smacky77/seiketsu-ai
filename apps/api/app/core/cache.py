"""
Cache configuration for Seiketsu AI API
"""
import redis.asyncio as redis
import json
import pickle
from typing import Any, Optional, Union
import logging
from datetime import timedelta

from app.core.config import settings

logger = logging.getLogger("seiketsu.cache")

# Redis client instance
redis_client: Optional[redis.Redis] = None


async def init_cache():
    """Initialize Redis cache connection"""
    global redis_client
    
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False,  # We'll handle encoding manually
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis cache connection established successfully")
        
    except Exception as e:
        logger.warning(f"Redis cache initialization failed: {e}")
        logger.warning("Running without cache - performance may be reduced")
        redis_client = None


async def close_cache():
    """Close Redis cache connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis cache connection closed")


class CacheService:
    """Service for caching operations"""
    
    def __init__(self):
        self.client = redis_client
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if not self.client:
            return default
        
        try:
            value = await self.client.get(key)
            if value is None:
                return default
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache"""
        if not self.client:
            return False
        
        try:
            # Serialize value
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value)
            
            # Set with TTL
            if ttl:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                await self.client.setex(key, ttl, serialized_value)
            else:
                await self.client.set(key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.client:
            return False
        
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.client:
            return False
        
        try:
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration time for key"""
        if not self.client:
            return False
        
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            result = await self.client.expire(key, ttl)
            return result
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value in cache"""
        if not self.client:
            return None
        
        try:
            result = await self.client.incrby(key, amount)
            return result
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache"""
        if not self.client or not keys:
            return {}
        
        try:
            values = await self.client.mget(keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        result[key] = pickle.loads(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(
        self, 
        mapping: dict[str, Any], 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set multiple values in cache"""
        if not self.client or not mapping:
            return False
        
        try:
            # Serialize all values
            serialized_mapping = {}
            for key, value in mapping.items():
                try:
                    serialized_mapping[key] = json.dumps(value)
                except (TypeError, ValueError):
                    serialized_mapping[key] = pickle.dumps(value)
            
            # Set all values
            await self.client.mset(serialized_mapping)
            
            # Set TTL if specified
            if ttl:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                
                # Use pipeline for efficiency
                async with self.client.pipeline() as pipe:
                    for key in mapping.keys():
                        pipe.expire(key, ttl)
                    await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.client:
            return 0
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear_pattern error for pattern {pattern}: {e}")
            return 0


# Global cache service instance
cache_service = CacheService()


# Decorator functions for caching
def cache_result(ttl: Union[int, timedelta] = 300, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


async def get_cached_result(key: str, default: Any = None) -> Any:
    """Get cached result by key"""
    return await cache_service.get(key, default)


async def cache_analytics_data(organization_id: str, data_type: str, data: Any, ttl: int = 300) -> bool:
    """Cache analytics data with organization-specific key"""
    key = f"analytics:{organization_id}:{data_type}"
    return await cache_service.set(key, data, ttl)


async def get_cached_analytics_data(organization_id: str, data_type: str) -> Any:
    """Get cached analytics data"""
    key = f"analytics:{organization_id}:{data_type}"
    return await cache_service.get(key)


async def cache_conversation_state(conversation_id: str, state: Dict[str, Any], ttl: int = 3600) -> bool:
    """Cache conversation state for real-time updates"""
    key = f"conversation:{conversation_id}:state"
    return await cache_service.set(key, state, ttl)


async def get_conversation_state(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Get cached conversation state"""
    key = f"conversation:{conversation_id}:state"
    return await cache_service.get(key)


async def cache_lead_score(lead_id: str, score: float, ttl: int = 1800) -> bool:
    """Cache lead score to avoid recalculation"""
    key = f"lead:{lead_id}:score"
    return await cache_service.set(key, score, ttl)


async def get_cached_lead_score(lead_id: str) -> Optional[float]:
    """Get cached lead score"""
    key = f"lead:{lead_id}:score"
    return await cache_service.get(key)


async def cache_voice_agent_status(agent_id: str, status: Dict[str, Any], ttl: int = 60) -> bool:
    """Cache voice agent status for real-time monitoring"""
    key = f"voice_agent:{agent_id}:status"
    return await cache_service.set(key, status, ttl)


async def get_voice_agent_status(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get cached voice agent status"""
    key = f"voice_agent:{agent_id}:status"
    return await cache_service.get(key)


async def cache_ml_prediction(model_type: str, input_hash: str, prediction: Any, ttl: int = 7200) -> bool:
    """Cache ML prediction results"""
    key = f"ml:{model_type}:{input_hash}"
    return await cache_service.set(key, prediction, ttl)


async def get_cached_ml_prediction(model_type: str, input_hash: str) -> Any:
    """Get cached ML prediction"""
    key = f"ml:{model_type}:{input_hash}"
    return await cache_service.get(key)


async def invalidate_organization_cache(organization_id: str) -> int:
    """Invalidate all cache entries for an organization"""
    pattern = f"*:{organization_id}:*"
    return await cache_service.clear_pattern(pattern)


async def get_redis_client() -> Optional[redis.Redis]:
    """Get the Redis client instance"""
    return redis_client


class CacheManager:
    """Advanced cache management with namespace isolation"""
    
    def __init__(self, namespace: str):
        self.namespace = namespace
        self.service = cache_service
    
    def _make_key(self, key: str) -> str:
        """Create namespaced key"""
        return f"{self.namespace}:{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value with namespace"""
        return await self.service.get(self._make_key(key), default)
    
    async def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set value with namespace"""
        return await self.service.set(self._make_key(key), value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete value with namespace"""
        return await self.service.delete(self._make_key(key))
    
    async def clear_namespace(self) -> int:
        """Clear all keys in this namespace"""
        pattern = f"{self.namespace}:*"
        return await self.service.clear_pattern(pattern)
    
    async def get_keys(self, pattern: str = "*") -> list[str]:
        """Get all keys in namespace matching pattern"""
        if not redis_client:
            return []
        
        try:
            full_pattern = f"{self.namespace}:{pattern}"
            keys = await redis_client.keys(full_pattern)
            # Remove namespace prefix from keys
            return [key.decode('utf-8').replace(f"{self.namespace}:", "") for key in keys]
        except Exception as e:
            logger.error(f"Error getting keys for pattern {pattern}: {e}")
            return []