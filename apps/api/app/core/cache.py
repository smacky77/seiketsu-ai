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