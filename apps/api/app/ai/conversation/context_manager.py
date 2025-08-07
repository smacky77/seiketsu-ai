"""
Conversation Context Manager
Manages conversation history and context across turns
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ...core.cache import get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Conversation context data"""
    conversation_id: str
    user_id: str
    tenant_id: Optional[str]
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: float
    updated_at: float


class ConversationContextManager:
    """Manages conversation context and history"""
    
    def __init__(self):
        self.redis_client = None
        self.max_context_turns = 10
        self.context_ttl = 1800  # 30 minutes
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = await get_redis_client()
        
    async def get_context(
        self,
        conversation_id: str,
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get conversation context"""
        try:
            if not self.redis_client:
                return {"messages": [], "metadata": {}}
                
            cache_key = f"conversation:{tenant_id or 'default'}:{conversation_id}"
            data = await self.redis_client.get(cache_key)
            
            if data:
                context_data = json.loads(data)
                return context_data
            
            return {"messages": [], "metadata": {}}
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return {"messages": [], "metadata": {}}
    
    async def add_turn(
        self,
        conversation_id: str,
        user_message: Any,
        assistant_message: Any,
        user_id: str,
        tenant_id: Optional[str] = None
    ):
        """Add conversation turn to context"""
        try:
            context = await self.get_context(conversation_id, user_id, tenant_id)
            
            # Add messages
            context["messages"].extend([
                {
                    "role": user_message.role,
                    "content": user_message.content,
                    "timestamp": user_message.timestamp
                },
                {
                    "role": assistant_message.role,
                    "content": assistant_message.content,
                    "timestamp": assistant_message.timestamp
                }
            ])
            
            # Keep only recent messages
            if len(context["messages"]) > self.max_context_turns * 2:
                context["messages"] = context["messages"][-self.max_context_turns * 2:]
            
            # Store updated context
            cache_key = f"conversation:{tenant_id or 'default'}:{conversation_id}"
            await self.redis_client.setex(
                cache_key, 
                self.context_ttl, 
                json.dumps(context)
            )
            
        except Exception as e:
            logger.error(f"Context update failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            "status": "healthy",
            "service": "conversation_context_manager",
            "redis_connected": self.redis_client is not None,
            "timestamp": time.time()
        }