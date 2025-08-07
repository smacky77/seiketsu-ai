"""
Advanced Security Middleware
Multi-tenant isolation, rate limiting, and threat protection
"""
import logging
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, Callable
import asyncio
import re

from app.core.config import settings
from app.core.cache import get_redis_client

logger = logging.getLogger("seiketsu.security_middleware")


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting with Redis backend and different limits per endpoint"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis_client = None
        self.rate_limits = {
            "/api/v1/voice/process": {"requests": 10, "window": 60},  # Voice processing
            "/api/v1/voice/initiate": {"requests": 20, "window": 60},  # Voice initiation
            "/api/v1/leads": {"requests": 100, "window": 60},  # Lead operations
            "/api/v1/analytics": {"requests": 50, "window": 60},  # Analytics
            "default": {"requests": settings.RATE_LIMIT_PER_MINUTE, "window": 60}
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks and static files
        if (request.url.path.startswith("/api/health") or 
            request.url.path.startswith("/static") or
            request.method == "OPTIONS"):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Get rate limit for this endpoint
        rate_limit = self._get_rate_limit_for_path(request.url.path)
        
        # Check rate limit
        is_limited, retry_after = await self._check_rate_limit(
            client_id, request.url.path, rate_limit
        )
        
        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path}",
                extra={
                    "client_id": client_id,
                    "path": request.url.path,
                    "rate_limit": rate_limit
                }
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "limit": rate_limit["requests"],
                    "window": rate_limit["window"]
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Record successful request
        await self._record_request(client_id, request.url.path, rate_limit)
        
        return await call_next(request)
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        # Try to get authenticated user ID first
        if hasattr(request.state, 'user_id') and request.state.user_id:
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Consider X-Forwarded-For header for load balancers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def _get_rate_limit_for_path(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for specific path"""
        for pattern, limit in self.rate_limits.items():
            if pattern == "default":
                continue
            if path.startswith(pattern):
                return limit
        return self.rate_limits["default"]
    
    async def _check_rate_limit(
        self, 
        client_id: str, 
        path: str, 
        rate_limit: Dict[str, int]
    ) -> tuple[bool, int]:
        """Check if client has exceeded rate limit"""
        try:
            if not self.redis_client:
                self.redis_client = await get_redis_client()
            
            if not self.redis_client:
                # Fallback to in-memory rate limiting
                return await self._check_rate_limit_memory(client_id, path, rate_limit)
            
            key = f"rate_limit:{client_id}:{path}"
            current_time = int(time.time())
            window_start = current_time - rate_limit["window"]
            
            # Remove old entries
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            current_requests = await self.redis_client.zcard(key)
            
            if current_requests >= rate_limit["requests"]:
                # Get time of earliest request in current window
                earliest = await self.redis_client.zrange(key, 0, 0, withscores=True)
                if earliest:
                    retry_after = int(earliest[0][1]) + rate_limit["window"] - current_time
                    return True, max(retry_after, 1)
                return True, rate_limit["window"]
            
            return False, 0
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Allow request on error to avoid blocking legitimate traffic
            return False, 0
    
    async def _record_request(
        self, 
        client_id: str, 
        path: str, 
        rate_limit: Dict[str, int]
    ):
        """Record successful request"""
        try:
            if not self.redis_client:
                return
            
            key = f"rate_limit:{client_id}:{path}"
            current_time = time.time()
            
            # Add current request
            await self.redis_client.zadd(key, {str(uuid.uuid4()): current_time})
            
            # Set expiration on key
            await self.redis_client.expire(key, rate_limit["window"] + 60)
            
        except Exception as e:
            logger.error(f"Failed to record request: {e}")
    
    async def _check_rate_limit_memory(
        self, 
        client_id: str, 
        path: str, 
        rate_limit: Dict[str, int]
    ) -> tuple[bool, int]:
        """Fallback in-memory rate limiting"""
        # This is a simplified version - in production you'd want a more sophisticated implementation
        return False, 0


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """Multi-tenant data isolation middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.bypass_paths = {"/api/health", "/docs", "/redoc", "/openapi.json"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tenant isolation for bypass paths
        if any(request.url.path.startswith(path) for path in self.bypass_paths):
            return await call_next(request)
        
        # Extract and validate tenant context
        tenant_context = await self._extract_tenant_context(request)
        
        if tenant_context:
            # Set tenant context in request state
            request.state.tenant_id = tenant_context["tenant_id"]
            request.state.organization_id = tenant_context["organization_id"]
            
            # Add tenant headers to response
            response = await call_next(request)
            response.headers["X-Tenant-ID"] = tenant_context["tenant_id"]
            
            return response
        else:
            # No valid tenant context found
            if request.url.path.startswith("/api/v1/auth"):
                # Allow auth endpoints without tenant context
                return await call_next(request)
            else:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid or missing tenant context"}
                )
    
    async def _extract_tenant_context(self, request: Request) -> Optional[Dict[str, str]]:
        """Extract tenant context from request"""
        try:
            # Method 1: From custom header
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                return {
                    "tenant_id": tenant_id,
                    "organization_id": tenant_id  # In this case, they're the same
                }
            
            # Method 2: From subdomain
            host = request.headers.get("host", "")
            if "." in host:
                subdomain = host.split(".")[0]
                if subdomain not in ["api", "www", "app", "admin"]:
                    return {
                        "tenant_id": subdomain,
                        "organization_id": subdomain
                    }
            
            # Method 3: From JWT token (if already authenticated)
            if hasattr(request.state, 'organization_id') and request.state.organization_id:
                return {
                    "tenant_id": request.state.organization_id,
                    "organization_id": request.state.organization_id
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract tenant context: {e}")
            return None


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced security headers middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Basic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://api.elevenlabs.io https://api.21dev.ai; "
            "media-src 'self' blob:; "
            "object-src 'none'; "
            "base-uri 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Additional security headers
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # HSTS for production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # API-specific headers
        if request.url.path.startswith("/api"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response


class ThreatDetectionMiddleware(BaseHTTPMiddleware):
    """Advanced threat detection and prevention"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.suspicious_patterns = [
            r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",  # XSS
            r"(?i)(union\s+select|drop\s+table|insert\s+into|delete\s+from)",  # SQL injection
            r"(?i)(exec\s*\(|eval\s*\(|system\s*\(|shell_exec)",  # Code injection
            r"\.\./",  # Path traversal
            r"(?i)(script|javascript|vbscript|onload|onerror)",  # XSS variants
        ]
        self.compiled_patterns = [re.compile(pattern) for pattern in self.suspicious_patterns]
        self.blocked_ips: Set[str] = set()
        self.suspicious_requests: Dict[str, int] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked request from {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # Analyze request for threats
        threat_level = await self._analyze_request(request)
        
        if threat_level >= 0.8:  # High threat
            logger.warning(
                f"High threat request blocked from {client_ip}",
                extra={
                    "threat_level": threat_level,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            self._record_suspicious_activity(client_ip)
            return JSONResponse(
                status_code=403,
                content={"detail": "Request blocked by security policy"}
            )
        elif threat_level >= 0.5:  # Medium threat
            logger.info(f"Suspicious request from {client_ip} (threat level: {threat_level})")
            self._record_suspicious_activity(client_ip)
        
        # Add security context to request
        request.state.threat_level = threat_level
        request.state.client_ip = client_ip
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check X-Forwarded-For header first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to client IP
        return request.client.host if request.client else "unknown"
    
    async def _analyze_request(self, request: Request) -> float:
        """Analyze request for potential threats"""
        threat_score = 0.0
        
        try:
            # Analyze URL parameters
            query_params = str(request.url.query)
            threat_score += self._scan_for_patterns(query_params) * 0.3
            
            # Analyze headers
            user_agent = request.headers.get("User-Agent", "")
            if self._is_suspicious_user_agent(user_agent):
                threat_score += 0.2
            
            # Analyze request body for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    if request.headers.get("content-type", "").startswith("application/json"):
                        body = await request.body()
                        if body:
                            body_str = body.decode("utf-8", errors="ignore")
                            threat_score += self._scan_for_patterns(body_str) * 0.4
                except Exception:
                    # If we can't read the body, don't fail the request
                    pass
            
            # Check for rapid successive requests (potential DoS)
            client_ip = self._get_client_ip(request)
            if self._is_rapid_requests(client_ip):
                threat_score += 0.3
            
        except Exception as e:
            logger.error(f"Error analyzing request: {e}")
        
        return min(threat_score, 1.0)  # Cap at 1.0
    
    def _scan_for_patterns(self, text: str) -> float:
        """Scan text for suspicious patterns"""
        if not text:
            return 0.0
        
        matches = 0
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                matches += 1
        
        return min(matches * 0.3, 1.0)  # Each match adds 0.3, cap at 1.0
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        suspicious_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zap",
            "burp", "w3af", "acunetix", "nessus", "openvas"
        ]
        user_agent_lower = user_agent.lower()
        return any(agent in user_agent_lower for agent in suspicious_agents)
    
    def _is_rapid_requests(self, client_ip: str) -> bool:
        """Check for rapid successive requests"""
        current_time = time.time()
        
        # Clean old entries
        cutoff_time = current_time - 60  # 1 minute window
        for ip in list(self.suspicious_requests.keys()):
            if self.suspicious_requests[ip] < cutoff_time:
                del self.suspicious_requests[ip]
        
        # Check current rate
        if client_ip in self.suspicious_requests:
            time_diff = current_time - self.suspicious_requests[client_ip]
            if time_diff < 1:  # More than 1 request per second
                return True
        
        self.suspicious_requests[client_ip] = current_time
        return False
    
    def _record_suspicious_activity(self, client_ip: str):
        """Record suspicious activity and potentially block IP"""
        if client_ip not in self.suspicious_requests:
            self.suspicious_requests[client_ip] = 0
        
        self.suspicious_requests[client_ip] += 1
        
        # Block IP after 5 suspicious requests
        if self.suspicious_requests[client_ip] >= 5:
            self.blocked_ips.add(client_ip)
            logger.warning(f"Blocked IP {client_ip} due to repeated suspicious activity")


class DataValidationMiddleware(BaseHTTPMiddleware):
    """Input validation and sanitization middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > 50 * 1024 * 1024:  # 50MB limit
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request too large"}
                    )
            except ValueError:
                pass
        
        # Validate content type for API endpoints
        if (request.url.path.startswith("/api") and 
            request.method in ["POST", "PUT", "PATCH"]):
            content_type = request.headers.get("content-type", "")
            
            if not content_type:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Content-Type header required"}
                )
            
            allowed_types = [
                "application/json",
                "multipart/form-data",
                "application/x-www-form-urlencoded",
                "audio/mpeg",
                "audio/wav",
                "audio/mp3"
            ]
            
            if not any(content_type.startswith(allowed) for allowed in allowed_types):
                return JSONResponse(
                    status_code=415,
                    content={"detail": "Unsupported media type"}
                )
        
        return await call_next(request)