"""
JWT Token Handler
Secure JWT token creation, validation, and management for multi-tenant authentication
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
import jwt
from jwt.exceptions import (
    InvalidTokenError, ExpiredSignatureError, 
    InvalidSignatureError, DecodeError
)
import secrets
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import settings
from app.core.cache import get_redis_client


logger = logging.getLogger(__name__)


class JWTHandler:
    """
    JWT Token Handler with advanced security features
    """
    
    def __init__(self):
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        
        # Key management
        self._private_key = None
        self._public_key = None
        self._secret_key = settings.SECRET_KEY
        
        # Token security
        self.issuer = "seiketsu-ai"
        self.audience = "seiketsu-ai-client"
        
        # Initialize keys for RS256 if needed
        if self.algorithm.startswith('RS'):
            self._initialize_rsa_keys()
    
    def _initialize_rsa_keys(self):
        """Initialize RSA key pair for RS256 algorithm"""
        
        try:
            # In production, these should be loaded from secure storage
            # For now, generate them (they would be persistent in real deployment)
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            self._private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_key = private_key.public_key()
            self._public_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
        except Exception as e:
            logger.error(f"Error initializing RSA keys: {e}")
            raise
    
    async def create_access_token(
        self,
        user_id: str,
        client_id: str,
        permissions: List[str],
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token with comprehensive claims
        
        Args:
            user_id: User identifier
            client_id: Client/tenant identifier
            permissions: List of user permissions
            additional_claims: Additional claims to include
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        # Generate unique token ID for tracking/revocation
        token_id = self._generate_token_id()
        
        # Standard JWT claims
        payload = {
            # Registered claims
            "iss": self.issuer,
            "aud": self.audience,
            "exp": expire.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
            "nbf": datetime.now(timezone.utc).timestamp(),
            "jti": token_id,
            
            # Custom claims
            "user_id": user_id,
            "client_id": client_id,
            "permissions": permissions,
            "token_type": "access",
            "token_version": 1
        }
        
        # Add additional claims
        if additional_claims:
            # Ensure we don't override critical claims
            safe_claims = {
                k: v for k, v in additional_claims.items()
                if k not in ["iss", "aud", "exp", "iat", "nbf", "jti", "user_id", "client_id", "token_type"]
            }
            payload.update(safe_claims)
        
        try:
            # Encode token
            if self.algorithm.startswith('RS'):
                token = jwt.encode(
                    payload, 
                    self._private_key, 
                    algorithm=self.algorithm,
                    headers={"kid": "default"}  # Key ID for key rotation
                )
            else:
                token = jwt.encode(
                    payload, 
                    self._secret_key, 
                    algorithm=self.algorithm
                )
            
            # Store token metadata for revocation tracking
            await self._store_token_metadata(token_id, {
                "user_id": user_id,
                "client_id": client_id,
                "token_type": "access",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expire.isoformat(),
                "permissions": permissions
            })
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise
    
    async def create_refresh_token(
        self,
        user_id: str,
        client_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token
        
        Args:
            user_id: User identifier
            client_id: Client/tenant identifier
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT refresh token
        """
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        token_id = self._generate_token_id()
        
        payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "exp": expire.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
            "nbf": datetime.now(timezone.utc).timestamp(),
            "jti": token_id,
            
            "user_id": user_id,
            "client_id": client_id,
            "token_type": "refresh",
            "token_version": 1
        }
        
        try:
            if self.algorithm.startswith('RS'):
                token = jwt.encode(
                    payload, 
                    self._private_key, 
                    algorithm=self.algorithm,
                    headers={"kid": "default"}
                )
            else:
                token = jwt.encode(
                    payload, 
                    self._secret_key, 
                    algorithm=self.algorithm
                )
            
            # Store token metadata
            await self._store_token_metadata(token_id, {
                "user_id": user_id,
                "client_id": client_id,
                "token_type": "refresh",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expire.isoformat()
            })
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise
    
    async def decode_token(
        self, 
        token: str, 
        token_type: Optional[str] = None,
        verify_exp: bool = True,
        verify_aud: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Decode and validate JWT token
        
        Args:
            token: JWT token to decode
            token_type: Expected token type ("access" or "refresh")
            verify_exp: Whether to verify expiration
            verify_aud: Whether to verify audience
            
        Returns:
            Decoded payload or None if invalid
        """
        
        try:
            # Decode options
            options = {
                "verify_signature": True,
                "verify_exp": verify_exp,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": verify_aud,
                "require_exp": True,
                "require_iat": True,
                "require_nbf": True
            }
            
            # Decode token
            if self.algorithm.startswith('RS'):
                payload = jwt.decode(
                    token,
                    self._public_key,
                    algorithms=[self.algorithm],
                    audience=self.audience if verify_aud else None,
                    issuer=self.issuer,
                    options=options
                )
            else:
                payload = jwt.decode(
                    token,
                    self._secret_key,
                    algorithms=[self.algorithm],
                    audience=self.audience if verify_aud else None,
                    issuer=self.issuer,
                    options=options
                )
            
            # Verify token type if specified
            if token_type and payload.get("token_type") != token_type:
                logger.warning(f"Token type mismatch. Expected: {token_type}, Got: {payload.get('token_type')}")
                return None
            
            # Check if token is revoked
            token_id = payload.get("jti")
            if token_id and await self._is_token_revoked(token_id):
                logger.warning(f"Token {token_id} has been revoked")
                return None
            
            return payload
            
        except ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except InvalidSignatureError:
            logger.warning("Token has invalid signature")
            return None
        except DecodeError:
            logger.warning("Token decode error")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error decoding token: {e}")
            return None
    
    async def revoke_token(self, token: str, reason: Optional[str] = None) -> bool:
        """
        Revoke a specific token
        
        Args:
            token: Token to revoke
            reason: Optional reason for revocation
            
        Returns:
            Success status
        """
        
        try:
            # Decode token to get ID
            payload = await self.decode_token(token, verify_exp=False)
            if not payload:
                logger.warning("Cannot revoke invalid token")
                return False
            
            token_id = payload.get("jti")
            if not token_id:
                logger.warning("Token has no JTI claim")
                return False
            
            # Add to revocation list
            await self._revoke_token_by_id(token_id, reason)
            
            logger.info(f"Token {token_id} revoked. Reason: {reason}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    async def revoke_user_tokens(
        self, 
        user_id: str, 
        client_id: Optional[str] = None,
        token_type: Optional[str] = None,
        reason: Optional[str] = None
    ) -> int:
        """
        Revoke all tokens for a user
        
        Args:
            user_id: User identifier
            client_id: Optional client identifier
            token_type: Optional token type filter
            reason: Optional reason for revocation
            
        Returns:
            Number of tokens revoked
        """
        
        try:
            # Get user's tokens
            token_metadata_list = await self._get_user_tokens(user_id, client_id, token_type)
            
            revoked_count = 0
            for token_metadata in token_metadata_list:
                token_id = token_metadata.get("token_id")
                if token_id:
                    await self._revoke_token_by_id(token_id, reason)
                    revoked_count += 1
            
            logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            
            return revoked_count
            
        except Exception as e:
            logger.error(f"Error revoking user tokens: {e}")
            return 0
    
    async def validate_token_claims(
        self, 
        payload: Dict[str, Any],
        required_claims: Optional[List[str]] = None,
        client_id: Optional[str] = None
    ) -> bool:
        """
        Validate token claims beyond standard JWT validation
        
        Args:
            payload: Decoded token payload
            required_claims: List of required claim names
            client_id: Expected client ID
            
        Returns:
            Validation result
        """
        
        try:
            # Check required claims
            if required_claims:
                missing_claims = [claim for claim in required_claims if claim not in payload]
                if missing_claims:
                    logger.warning(f"Missing required claims: {missing_claims}")
                    return False
            
            # Check client ID if provided
            if client_id and payload.get("client_id") != client_id:
                logger.warning(f"Client ID mismatch. Expected: {client_id}, Got: {payload.get('client_id')}")
                return False
            
            # Check token version compatibility
            token_version = payload.get("token_version", 0)
            if token_version < 1:
                logger.warning(f"Unsupported token version: {token_version}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating token claims: {e}")
            return False
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get token information without full validation (for debugging)
        """
        
        try:
            # Decode without verification
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            
            return {
                "user_id": payload.get("user_id"),
                "client_id": payload.get("client_id"),
                "token_type": payload.get("token_type"),
                "issued_at": datetime.fromtimestamp(payload.get("iat", 0), timezone.utc).isoformat(),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0), timezone.utc).isoformat(),
                "permissions": payload.get("permissions", []),
                "token_id": payload.get("jti")
            }
            
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return None
    
    # Private helper methods
    
    def _generate_token_id(self) -> str:
        """Generate unique token identifier"""
        
        # Combine timestamp with random data
        timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000000))
        random_data = secrets.token_hex(16)
        
        # Create hash
        token_data = f"{timestamp}:{random_data}"
        token_id = hashlib.sha256(token_data.encode()).hexdigest()[:32]
        
        return token_id
    
    async def _store_token_metadata(self, token_id: str, metadata: Dict[str, Any]):
        """Store token metadata for revocation tracking"""
        
        redis_client = await get_redis_client()
        if not redis_client:
            return
        
        try:
            import json
            key = f"token_metadata:{token_id}"
            
            # Set expiration based on token type
            if metadata.get("token_type") == "refresh":
                ttl = self.refresh_token_expire_days * 24 * 60 * 60
            else:
                ttl = self.access_token_expire_minutes * 60
            
            await redis_client.setex(key, ttl, json.dumps(metadata))
            
            # Also maintain user token list
            user_id = metadata.get("user_id")
            if user_id:
                user_tokens_key = f"user_tokens:{user_id}"
                await redis_client.sadd(user_tokens_key, token_id)
                await redis_client.expire(user_tokens_key, ttl)
                
        except Exception as e:
            logger.error(f"Error storing token metadata: {e}")
    
    async def _is_token_revoked(self, token_id: str) -> bool:
        """Check if token is revoked"""
        
        redis_client = await get_redis_client()
        if not redis_client:
            return False
        
        try:
            revoked_key = f"revoked_token:{token_id}"
            return bool(await redis_client.get(revoked_key))
            
        except Exception as e:
            logger.error(f"Error checking token revocation: {e}")
            return False
    
    async def _revoke_token_by_id(self, token_id: str, reason: Optional[str] = None):
        """Revoke token by ID"""
        
        redis_client = await get_redis_client()
        if not redis_client:
            return
        
        try:
            revoked_key = f"revoked_token:{token_id}"
            revocation_data = {
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason or "Manual revocation"
            }
            
            import json
            # Set long TTL for revocation list
            await redis_client.setex(revoked_key, 30 * 24 * 60 * 60, json.dumps(revocation_data))
            
        except Exception as e:
            logger.error(f"Error revoking token by ID: {e}")
    
    async def _get_user_tokens(
        self, 
        user_id: str, 
        client_id: Optional[str] = None,
        token_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all tokens for a user"""
        
        redis_client = await get_redis_client()
        if not redis_client:
            return []
        
        try:
            import json
            user_tokens_key = f"user_tokens:{user_id}"
            token_ids = await redis_client.smembers(user_tokens_key)
            
            tokens = []
            for token_id in token_ids:
                metadata_key = f"token_metadata:{token_id}"
                metadata_json = await redis_client.get(metadata_key)
                
                if metadata_json:
                    metadata = json.loads(metadata_json)
                    metadata["token_id"] = token_id
                    
                    # Apply filters
                    if client_id and metadata.get("client_id") != client_id:
                        continue
                    if token_type and metadata.get("token_type") != token_type:
                        continue
                    
                    tokens.append(metadata)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Error getting user tokens: {e}")
            return []