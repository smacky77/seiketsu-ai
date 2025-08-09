"""
Client Isolation Middleware
Ensures complete data isolation between clients/tenants
"""
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.models.client import Client, ClientStatus
from app.models.audit import ClientAuditLog, AuditEventType, AuditSeverity
from app.auth.jwt_handler import JWTHandler
from app.core.config import settings


logger = logging.getLogger(__name__)


class TenantContext:
    """
    Tenant context for request processing
    Stores client/tenant information for the current request
    """
    
    def __init__(
        self,
        client_id: str,
        client_slug: str,
        client_tier: str,
        user_id: Optional[str] = None,
        permissions: Optional[list] = None
    ):
        self.client_id = client_id
        self.client_slug = client_slug
        self.client_tier = client_tier
        self.user_id = user_id
        self.permissions = permissions or []
        
        # Database context
        self.database_schema = f"client_{client_slug}"
        
        # Request metadata
        self.request_id: Optional[str] = None
        self.ip_address: Optional[str] = None
        self.user_agent: Optional[str] = None
        self.api_key_used: bool = False
    
    def has_permission(self, permission: str) -> bool:
        """Check if current context has specific permission"""
        return permission in self.permissions
    
    def is_enterprise(self) -> bool:
        """Check if client is enterprise tier"""
        return self.client_tier == "enterprise"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "client_id": self.client_id,
            "client_slug": self.client_slug,
            "client_tier": self.client_tier,
            "user_id": self.user_id,
            "permissions": self.permissions,
            "database_schema": self.database_schema,
            "request_id": self.request_id,
            "api_key_used": self.api_key_used
        }


class ClientIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce client isolation and set tenant context
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.jwt_handler = JWTHandler()
        
        # Endpoints that don't require client context
        self.public_endpoints = {
            "/docs", "/redoc", "/openapi.json",
            "/api/health", "/api/health/live", "/api/health/ready",
            "/", "/favicon.ico"
        }
        
        # Auth endpoints that handle client resolution internally
        self.auth_endpoints = {
            "/api/v1/auth/login", "/api/v1/auth/register",
            "/api/v1/auth/refresh", "/api/v1/auth/forgot-password"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with client isolation"""
        
        try:
            # Skip public endpoints
            if self._is_public_endpoint(request.url.path):
                return await call_next(request)
            
            # Extract client context
            tenant_context = await self._extract_tenant_context(request)
            
            if not tenant_context and not self._is_auth_endpoint(request.url.path):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Authentication required",
                        "error_code": "MISSING_AUTHENTICATION"
                    }
                )
            
            # Set tenant context in request state
            if tenant_context:
                request.state.tenant_context = tenant_context
                
                # Set database context for queries
                await self._set_database_context(request, tenant_context)
                
                # Validate client access
                validation_result = await self._validate_client_access(request, tenant_context)
                if not validation_result["valid"]:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "detail": validation_result["reason"],
                            "error_code": "CLIENT_ACCESS_DENIED"
                        }
                    )
                
                # Log API access
                await self._log_api_access(request, tenant_context)
            
            # Process request
            response = await call_next(request)
            
            # Add tenant context to response headers (for debugging)
            if tenant_context and settings.ENVIRONMENT != "production":
                response.headers["X-Tenant-ID"] = tenant_context.client_id
                response.headers["X-Tenant-Slug"] = tenant_context.client_slug
            
            return response
            
        except Exception as e:
            logger.error(f"Client isolation middleware error: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "error_code": "MIDDLEWARE_ERROR"
                }
            )
    
    async def _extract_tenant_context(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant context from request"""
        
        try:
            # Method 1: JWT Token in Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                
                payload = await self.jwt_handler.decode_token(token, "access")
                if payload:
                    return await self._create_context_from_jwt(request, payload)
            
            # Method 2: API Key in header
            api_key = request.headers.get("X-API-Key")
            if api_key:
                context = await self._create_context_from_api_key(request, api_key)
                if context:
                    context.api_key_used = True
                    return context
            
            # Method 3: Client slug in subdomain or path
            context = await self._extract_context_from_request(request)
            if context:
                return context
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting tenant context: {e}")
            return None
    
    async def _create_context_from_jwt(
        self, 
        request: Request, 
        payload: Dict[str, Any]
    ) -> Optional[TenantContext]:
        """Create tenant context from JWT payload"""
        
        try:
            user_id = payload.get("user_id")
            client_id = payload.get("client_id")
            permissions = payload.get("permissions", [])
            
            if not client_id:
                return None
            
            # Get client details
            session = await get_db_session()
            try:
                client = await session.get(Client, client_id)
                if not client or client.status != ClientStatus.ACTIVE:
                    return None
                
                context = TenantContext(
                    client_id=client_id,
                    client_slug=client.slug,
                    client_tier=client.tier.value,
                    user_id=user_id,
                    permissions=permissions
                )
                
                # Set request metadata
                context.request_id = request.state.request_id if hasattr(request.state, 'request_id') else None
                context.ip_address = self._get_client_ip(request)
                context.user_agent = request.headers.get("User-Agent")
                
                return context
                
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"Error creating context from JWT: {e}")
            return None
    
    async def _create_context_from_api_key(
        self, 
        request: Request, 
        api_key: str
    ) -> Optional[TenantContext]:
        """Create tenant context from API key"""
        
        # Implementation would depend on your API key model
        # This is a placeholder
        
        try:
            # Validate API key and get associated client
            session = await get_db_session()
            try:
                # Query API key table (not implemented in this example)
                # api_key_record = await session.execute(
                #     select(APIKey).where(APIKey.key == api_key, APIKey.is_active == True)
                # )
                # api_key_obj = api_key_record.scalar_one_or_none()
                
                # For now, return None (API key auth not fully implemented)
                return None
                
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"Error creating context from API key: {e}")
            return None
    
    async def _extract_context_from_request(self, request: Request) -> Optional[TenantContext]:
        """Extract context from request URL/headers"""
        
        try:
            # Method 1: Client slug in subdomain
            host = request.headers.get("Host", "")
            if host and "." in host:
                subdomain = host.split(".")[0]
                if subdomain not in ["www", "api", "app"]:
                    # Treat as client slug
                    context = await self._get_context_by_slug(subdomain, request)
                    if context:
                        return context
            
            # Method 2: Client slug in path
            path_parts = request.url.path.strip("/").split("/")
            if len(path_parts) >= 3 and path_parts[0] == "api" and path_parts[1] == "client":
                client_slug = path_parts[2]
                context = await self._get_context_by_slug(client_slug, request)
                if context:
                    return context
            
            # Method 3: Client header
            client_slug = request.headers.get("X-Client-Slug")
            if client_slug:
                context = await self._get_context_by_slug(client_slug, request)
                if context:
                    return context
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting context from request: {e}")
            return None
    
    async def _get_context_by_slug(
        self, 
        client_slug: str, 
        request: Request
    ) -> Optional[TenantContext]:
        """Get tenant context by client slug"""
        
        try:
            session = await get_db_session()
            try:
                query = select(Client).where(
                    Client.slug == client_slug,
                    Client.status == ClientStatus.ACTIVE
                )
                result = await session.execute(query)
                client = result.scalar_one_or_none()
                
                if not client:
                    return None
                
                context = TenantContext(
                    client_id=str(client.id),
                    client_slug=client.slug,
                    client_tier=client.tier.value
                )
                
                # Set request metadata
                context.request_id = getattr(request.state, 'request_id', None)
                context.ip_address = self._get_client_ip(request)
                context.user_agent = request.headers.get("User-Agent")
                
                return context
                
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"Error getting context by slug: {e}")
            return None
    
    async def _validate_client_access(
        self, 
        request: Request, 
        context: TenantContext
    ) -> Dict[str, Any]:
        """Validate client access permissions"""
        
        try:
            session = await get_db_session()
            try:
                client = await session.get(Client, context.client_id)
                if not client:
                    return {"valid": False, "reason": "Client not found"}
                
                if client.status != ClientStatus.ACTIVE:
                    return {"valid": False, "reason": "Client account is not active"}
                
                # Check IP restrictions
                client_ip = context.ip_address
                if client_ip and not client.can_access_ip(client_ip):
                    await self._log_security_event(
                        session, context, AuditEventType.ACCESS_DENIED,
                        f"Access denied from IP {client_ip}",
                        severity=AuditSeverity.HIGH
                    )
                    return {"valid": False, "reason": "Access from this IP address is not permitted"}
                
                # Check client-specific constraints
                if hasattr(client, 'maintenance_mode') and client.maintenance_mode:
                    return {"valid": False, "reason": "Client is in maintenance mode"}
                
                return {"valid": True}
                
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"Error validating client access: {e}")
            return {"valid": False, "reason": "Access validation failed"}
    
    async def _set_database_context(self, request: Request, context: TenantContext):
        """Set database context for tenant isolation"""
        
        # This would set the database search path or connection context
        # Implementation depends on your database isolation strategy
        
        # For PostgreSQL schema-based isolation:
        # SET search_path TO client_schema, public;
        
        # For now, just store in request state for use by database queries
        request.state.database_schema = context.database_schema
    
    async def _log_api_access(self, request: Request, context: TenantContext):
        """Log API access for audit trail"""
        
        try:
            # Only log for non-health check endpoints
            if "/health" in request.url.path:
                return
            
            session = await get_db_session()
            try:
                audit_log = ClientAuditLog(
                    client_id=context.client_id,
                    event_type=AuditEventType.API_CALL,
                    event_name="API Access",
                    event_description=f"{request.method} {request.url.path}",
                    event_outcome="success",
                    user_id=context.user_id,
                    ip_address=context.ip_address,
                    user_agent=context.user_agent,
                    request_id=context.request_id,
                    api_endpoint=str(request.url.path),
                    http_method=request.method,
                    metadata={
                        "client_slug": context.client_slug,
                        "api_key_used": context.api_key_used,
                        "query_params": dict(request.query_params)
                    }
                )
                
                session.add(audit_log)
                await session.commit()
                
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"Error logging API access: {e}")
    
    async def _log_security_event(
        self,
        session: AsyncSession,
        context: TenantContext,
        event_type: AuditEventType,
        description: str,
        severity: AuditSeverity = AuditSeverity.INFO
    ):
        """Log security event"""
        
        try:
            audit_log = ClientAuditLog(
                client_id=context.client_id,
                event_type=event_type,
                event_name="Security Event",
                event_description=description,
                event_outcome="failure" if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL] else "success",
                severity=severity,
                user_id=context.user_id,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                request_id=context.request_id,
                security_alert=severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL],
                metadata=context.to_dict()
            )
            
            session.add(audit_log)
            await session.flush()
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        return any(path.startswith(endpoint) for endpoint in self.public_endpoints)
    
    def _is_auth_endpoint(self, path: str) -> bool:
        """Check if endpoint is auth-related"""
        return any(path.startswith(endpoint) for endpoint in self.auth_endpoints)
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Get client IP address from request"""
        
        # Check for forwarded headers (from load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct connection
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None


# Dependency to get current tenant context
async def get_tenant_context(request: Request) -> Optional[TenantContext]:
    """Get tenant context from request state"""
    return getattr(request.state, 'tenant_context', None)


# Dependency to require tenant context
async def require_tenant_context(request: Request) -> TenantContext:
    """Require tenant context (raises HTTPException if not available)"""
    
    context = getattr(request.state, 'tenant_context', None)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return context