"""
Multi-Tenant Authentication Service
Handles authentication with client/tenant context
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.models.user import User
from app.models.client import Client, ClientStatus
from app.models.audit import ClientAuditLog, AuditEventType, AuditSeverity
from app.auth.jwt_handler import JWTHandler
from app.auth.rbac import RBACService, Permission
from app.core.cache import get_redis_client


logger = logging.getLogger(__name__)


@dataclass
class AuthenticationResult:
    """Result of authentication attempt"""
    success: bool
    user: Optional[User] = None
    client: Optional[Client] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    permissions: Optional[List[str]] = None
    error_message: Optional[str] = None
    requires_mfa: bool = False
    lockout_until: Optional[datetime] = None


@dataclass
class TokenValidationResult:
    """Result of token validation"""
    valid: bool
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    permissions: Optional[List[str]] = None
    token_type: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class MultiTenantAuthService:
    """
    Multi-tenant authentication service with comprehensive security features
    """
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.jwt_handler = JWTHandler()
        self.rbac_service = RBACService()
        
        # Security configuration
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 15
        self.token_blacklist_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        # Rate limiting
        self.rate_limit_per_minute = 60
        self.rate_limit_burst = 10
    
    async def authenticate_user(
        self,
        session: AsyncSession,
        email: str,
        password: str,
        client_slug: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuthenticationResult:
        """
        Authenticate user with multi-tenant context
        
        Args:
            session: Database session
            email: User email
            password: User password
            client_slug: Client/tenant identifier
            ip_address: Request IP address
            user_agent: Request user agent
            request_id: Request ID for tracking
            
        Returns:
            AuthenticationResult with tokens and permissions
        """
        
        try:
            # Rate limiting check
            if await self._is_rate_limited(ip_address, email):
                await self._log_security_event(
                    session, None, None, AuditEventType.RATE_LIMIT_EXCEEDED,
                    f"Rate limit exceeded for {email}",
                    ip_address, user_agent, request_id,
                    severity=AuditSeverity.MEDIUM
                )
                return AuthenticationResult(
                    success=False,
                    error_message="Too many authentication attempts. Please try again later."
                )
            
            # Find user and client
            user, client = await self._find_user_and_client(session, email, client_slug)
            
            if not user:
                await self._log_failed_login(
                    session, email, client_slug, "User not found",
                    ip_address, user_agent, request_id
                )
                await self._increment_rate_limit_counter(ip_address, email)
                return AuthenticationResult(
                    success=False,
                    error_message="Invalid credentials"
                )
            
            if not client or client.status != ClientStatus.ACTIVE:
                await self._log_failed_login(
                    session, email, client_slug, "Client not active",
                    ip_address, user_agent, request_id
                )
                return AuthenticationResult(
                    success=False,
                    error_message="Account not available"
                )
            
            # Check account lockout
            if await self._is_account_locked(user.id):
                lockout_until = await self._get_lockout_expiry(user.id)
                await self._log_failed_login(
                    session, email, client_slug, "Account locked",
                    ip_address, user_agent, request_id
                )
                return AuthenticationResult(
                    success=False,
                    error_message="Account is temporarily locked",
                    lockout_until=lockout_until
                )
            
            # Verify password
            if not self._verify_password(password, user.hashed_password):
                await self._handle_failed_login_attempt(session, user, client, ip_address, user_agent, request_id)
                return AuthenticationResult(
                    success=False,
                    error_message="Invalid credentials"
                )
            
            # Check if user has access to client
            if not await self._user_has_client_access(user, client):
                await self._log_failed_login(
                    session, email, client_slug, "No client access",
                    ip_address, user_agent, request_id
                )
                return AuthenticationResult(
                    success=False,
                    error_message="Access denied"
                )
            
            # Check IP restrictions
            if not client.can_access_ip(ip_address):
                await self._log_security_event(
                    session, user.id, client.id, AuditEventType.ACCESS_DENIED,
                    f"IP {ip_address} not in allowed list",
                    ip_address, user_agent, request_id,
                    severity=AuditSeverity.HIGH
                )
                return AuthenticationResult(
                    success=False,
                    error_message="Access from this location is not permitted"
                )
            
            # Check if MFA is required
            if user.mfa_enabled and not await self._mfa_completed_recently(user.id):
                return AuthenticationResult(
                    success=False,
                    requires_mfa=True,
                    user=user,
                    client=client,
                    error_message="Multi-factor authentication required"
                )
            
            # Generate tokens
            permissions = await self.rbac_service.get_user_permissions(session, user.id, client.id)
            access_token = await self.jwt_handler.create_access_token(
                user_id=str(user.id),
                client_id=str(client.id),
                permissions=permissions,
                additional_claims={
                    "email": user.email,
                    "role": user.role,
                    "client_slug": client.slug
                }
            )
            
            refresh_token = await self.jwt_handler.create_refresh_token(
                user_id=str(user.id),
                client_id=str(client.id)
            )
            
            # Clear failed login attempts
            await self._clear_failed_login_attempts(user.id)
            
            # Update user login info
            user.last_login_at = datetime.now(timezone.utc)
            user.last_login_ip = ip_address
            
            # Log successful authentication
            await self._log_successful_login(
                session, user, client, ip_address, user_agent, request_id
            )
            
            await session.commit()
            
            return AuthenticationResult(
                success=True,
                user=user,
                client=client,
                access_token=access_token,
                refresh_token=refresh_token,
                permissions=permissions
            )
            
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            await session.rollback()
            
            return AuthenticationResult(
                success=False,
                error_message="Authentication service temporarily unavailable"
            )
    
    async def validate_token(
        self,
        session: AsyncSession,
        token: str,
        token_type: str = "access",
        required_permissions: Optional[List[str]] = None
    ) -> TokenValidationResult:
        """
        Validate JWT token and check permissions
        
        Args:
            session: Database session
            token: JWT token to validate
            token_type: Type of token ("access" or "refresh")
            required_permissions: List of required permissions
            
        Returns:
            TokenValidationResult with validation details
        """
        
        try:
            # Check token blacklist
            if await self._is_token_blacklisted(token):
                return TokenValidationResult(
                    valid=False,
                    error_message="Token has been revoked"
                )
            
            # Decode and validate token
            payload = await self.jwt_handler.decode_token(token, token_type)
            if not payload:
                return TokenValidationResult(
                    valid=False,
                    error_message="Invalid or expired token"
                )
            
            user_id = payload.get("user_id")
            client_id = payload.get("client_id")
            
            if not user_id or not client_id:
                return TokenValidationResult(
                    valid=False,
                    error_message="Invalid token claims"
                )
            
            # Verify user and client still exist and are active
            user = await session.get(User, user_id)
            client = await session.get(Client, client_id)
            
            if not user or not user.is_active:
                return TokenValidationResult(
                    valid=False,
                    error_message="User account not available"
                )
            
            if not client or client.status != ClientStatus.ACTIVE:
                return TokenValidationResult(
                    valid=False,
                    error_message="Client account not available"
                )
            
            # Get current permissions
            permissions = await self.rbac_service.get_user_permissions(
                session, user_id, client_id
            )
            
            # Check required permissions
            if required_permissions:
                missing_permissions = set(required_permissions) - set(permissions)
                if missing_permissions:
                    return TokenValidationResult(
                        valid=False,
                        error_message=f"Missing required permissions: {', '.join(missing_permissions)}"
                    )
            
            return TokenValidationResult(
                valid=True,
                user_id=user_id,
                client_id=client_id,
                permissions=permissions,
                token_type=token_type,
                expires_at=datetime.fromtimestamp(payload.get("exp", 0), timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Token validation error: {e}", exc_info=True)
            return TokenValidationResult(
                valid=False,
                error_message="Token validation failed"
            )
    
    async def refresh_access_token(
        self,
        session: AsyncSession,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuthenticationResult:
        """
        Refresh access token using refresh token
        """
        
        try:
            # Validate refresh token
            validation_result = await self.validate_token(
                session, refresh_token, "refresh"
            )
            
            if not validation_result.valid:
                return AuthenticationResult(
                    success=False,
                    error_message=validation_result.error_message
                )
            
            user_id = validation_result.user_id
            client_id = validation_result.client_id
            
            # Get user and client
            user = await session.get(User, user_id)
            client = await session.get(Client, client_id)
            
            # Generate new access token
            permissions = await self.rbac_service.get_user_permissions(
                session, user_id, client_id
            )
            
            access_token = await self.jwt_handler.create_access_token(
                user_id=user_id,
                client_id=client_id,
                permissions=permissions,
                additional_claims={
                    "email": user.email,
                    "role": user.role,
                    "client_slug": client.slug
                }
            )
            
            # Log token refresh
            await self._log_security_event(
                session, user_id, client_id, AuditEventType.TOKEN_REFRESH,
                "Access token refreshed",
                ip_address, user_agent,
                severity=AuditSeverity.INFO
            )
            
            return AuthenticationResult(
                success=True,
                user=user,
                client=client,
                access_token=access_token,
                refresh_token=refresh_token,  # Keep existing refresh token
                permissions=permissions
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}", exc_info=True)
            return AuthenticationResult(
                success=False,
                error_message="Token refresh failed"
            )
    
    async def logout_user(
        self,
        session: AsyncSession,
        access_token: str,
        refresh_token: Optional[str] = None,
        user_id: Optional[str] = None,
        client_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Logout user and blacklist tokens
        """
        
        try:
            # Blacklist tokens
            await self._blacklist_token(access_token)
            if refresh_token:
                await self._blacklist_token(refresh_token)
            
            # Log logout event
            if user_id and client_id:
                await self._log_security_event(
                    session, user_id, client_id, AuditEventType.LOGOUT,
                    "User logged out",
                    ip_address, user_agent,
                    severity=AuditSeverity.INFO
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    async def change_password(
        self,
        session: AsyncSession,
        user_id: str,
        current_password: str,
        new_password: str,
        client_id: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Change user password with security validation
        """
        
        try:
            user = await session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not self._verify_password(current_password, user.hashed_password):
                await self._log_security_event(
                    session, user_id, client_id, AuditEventType.PASSWORD_CHANGE,
                    "Password change failed - invalid current password",
                    ip_address, severity=AuditSeverity.MEDIUM
                )
                return False, "Current password is incorrect"
            
            # Validate new password strength
            if not self._validate_password_strength(new_password):
                return False, "New password does not meet security requirements"
            
            # Check password history
            if await self._is_password_recently_used(user_id, new_password):
                return False, "Cannot reuse a recent password"
            
            # Hash and update password
            hashed_password = self._hash_password(new_password)
            user.hashed_password = hashed_password
            user.password_changed_at = datetime.now(timezone.utc)
            
            # Store in password history
            await self._add_to_password_history(user_id, hashed_password)
            
            # Log successful password change
            await self._log_security_event(
                session, user_id, client_id, AuditEventType.PASSWORD_CHANGE,
                "Password changed successfully",
                ip_address, severity=AuditSeverity.INFO
            )
            
            await session.commit()
            
            return True, "Password changed successfully"
            
        except Exception as e:
            logger.error(f"Password change error: {e}")
            await session.rollback()
            return False, "Password change failed"
    
    # Private helper methods
    
    async def _find_user_and_client(
        self, 
        session: AsyncSession, 
        email: str, 
        client_slug: Optional[str]
    ) -> Tuple[Optional[User], Optional[Client]]:
        """Find user and associated client"""
        
        if client_slug:
            # Multi-tenant mode - find user within specific client
            query = select(User, Client).join(Client).where(
                and_(
                    User.email == email,
                    Client.slug == client_slug,
                    User.is_active == True,
                    Client.status == ClientStatus.ACTIVE
                )
            )
        else:
            # Single tenant mode or no client specified
            user_query = select(User).where(
                and_(User.email == email, User.is_active == True)
            )
            result = await session.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None, None
            
            # Get user's primary client
            client_query = select(Client).where(Client.id == user.client_id)
            client_result = await session.execute(client_query)
            client = client_result.scalar_one_or_none()
            
            return user, client
        
        result = await session.execute(query)
        row = result.first()
        
        if row:
            return row.User, row.Client
        
        return None, None
    
    async def _user_has_client_access(self, user: User, client: Client) -> bool:
        """Check if user has access to client"""
        # This would be based on your user-client relationship model
        # For now, assume user.client_id or user belongs to client
        return str(user.client_id) == str(client.id)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def _hash_password(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    async def _is_rate_limited(self, ip_address: Optional[str], email: str) -> bool:
        """Check if IP or email is rate limited"""
        if not ip_address:
            return False
        
        redis_client = await get_redis_client()
        if not redis_client:
            return False
        
        try:
            # Check IP-based rate limiting
            ip_key = f"rate_limit:ip:{ip_address}"
            ip_count = await redis_client.get(ip_key)
            
            if ip_count and int(ip_count) > self.rate_limit_per_minute:
                return True
            
            # Check email-based rate limiting
            email_key = f"rate_limit:email:{email}"
            email_count = await redis_client.get(email_key)
            
            if email_count and int(email_count) > self.rate_limit_per_minute:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Rate limiting check failed: {e}")
            return False
    
    async def _increment_rate_limit_counter(self, ip_address: Optional[str], email: str):
        """Increment rate limit counters"""
        if not ip_address:
            return
        
        redis_client = await get_redis_client()
        if not redis_client:
            return
        
        try:
            # Increment IP counter
            ip_key = f"rate_limit:ip:{ip_address}"
            await redis_client.incr(ip_key)
            await redis_client.expire(ip_key, 60)  # 1 minute TTL
            
            # Increment email counter
            email_key = f"rate_limit:email:{email}"
            await redis_client.incr(email_key)
            await redis_client.expire(email_key, 60)  # 1 minute TTL
            
        except Exception as e:
            logger.error(f"Rate limiting increment failed: {e}")
    
    async def _is_account_locked(self, user_id: str) -> bool:
        """Check if account is locked due to failed attempts"""
        redis_client = await get_redis_client()
        if not redis_client:
            return False
        
        try:
            lock_key = f"account_lock:{user_id}"
            is_locked = await redis_client.get(lock_key)
            return bool(is_locked)
            
        except Exception:
            return False
    
    async def _get_lockout_expiry(self, user_id: str) -> Optional[datetime]:
        """Get account lockout expiry time"""
        redis_client = await get_redis_client()
        if not redis_client:
            return None
        
        try:
            lock_key = f"account_lock:{user_id}"
            ttl = await redis_client.ttl(lock_key)
            if ttl > 0:
                return datetime.now(timezone.utc) + timedelta(seconds=ttl)
            
        except Exception:
            pass
        
        return None
    
    async def _handle_failed_login_attempt(
        self, 
        session: AsyncSession, 
        user: User, 
        client: Client,
        ip_address: Optional[str],
        user_agent: Optional[str],
        request_id: Optional[str]
    ):
        """Handle failed login attempt and potentially lock account"""
        
        redis_client = await get_redis_client()
        if not redis_client:
            return
        
        try:
            # Increment failed attempts counter
            attempts_key = f"failed_attempts:{user.id}"
            attempts = await redis_client.incr(attempts_key)
            await redis_client.expire(attempts_key, self.lockout_duration_minutes * 60)
            
            if attempts >= self.max_login_attempts:
                # Lock the account
                lock_key = f"account_lock:{user.id}"
                await redis_client.setex(
                    lock_key, 
                    self.lockout_duration_minutes * 60, 
                    "locked"
                )
                
                # Log account lockout
                await self._log_security_event(
                    session, str(user.id), str(client.id), 
                    AuditEventType.ACCOUNT_LOCKED,
                    f"Account locked after {attempts} failed attempts",
                    ip_address, user_agent, request_id,
                    severity=AuditSeverity.HIGH
                )
            else:
                # Log failed attempt
                await self._log_failed_login(
                    session, user.email, client.slug, 
                    f"Invalid password (attempt {attempts})",
                    ip_address, user_agent, request_id
                )
        
        except Exception as e:
            logger.error(f"Error handling failed login attempt: {e}")
    
    async def _clear_failed_login_attempts(self, user_id: str):
        """Clear failed login attempts counter"""
        redis_client = await get_redis_client()
        if redis_client:
            try:
                attempts_key = f"failed_attempts:{user_id}"
                await redis_client.delete(attempts_key)
            except Exception:
                pass
    
    async def _mfa_completed_recently(self, user_id: str) -> bool:
        """Check if MFA was completed recently"""
        redis_client = await get_redis_client()
        if not redis_client:
            return False
        
        try:
            mfa_key = f"mfa_completed:{user_id}"
            return bool(await redis_client.get(mfa_key))
        except Exception:
            return False
    
    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        redis_client = await get_redis_client()
        if not redis_client:
            return False
        
        try:
            blacklist_key = f"token_blacklist:{token}"
            return bool(await redis_client.get(blacklist_key))
        except Exception:
            return False
    
    async def _blacklist_token(self, token: str):
        """Add token to blacklist"""
        redis_client = await get_redis_client()
        if not redis_client:
            return
        
        try:
            blacklist_key = f"token_blacklist:{token}"
            await redis_client.setex(blacklist_key, self.token_blacklist_ttl, "blacklisted")
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
    
    async def _is_password_recently_used(self, user_id: str, password: str) -> bool:
        """Check if password was recently used"""
        # Implementation would check password history
        # For now, return False
        return False
    
    async def _add_to_password_history(self, user_id: str, hashed_password: str):
        """Add password to history"""
        # Implementation would store password in history table/cache
        pass
    
    async def _log_successful_login(
        self,
        session: AsyncSession,
        user: User,
        client: Client,
        ip_address: Optional[str],
        user_agent: Optional[str],
        request_id: Optional[str]
    ):
        """Log successful login event"""
        
        await self._log_security_event(
            session, str(user.id), str(client.id),
            AuditEventType.LOGIN,
            "User login successful",
            ip_address, user_agent, request_id,
            severity=AuditSeverity.INFO
        )
    
    async def _log_failed_login(
        self,
        session: AsyncSession,
        email: str,
        client_slug: Optional[str],
        reason: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        request_id: Optional[str]
    ):
        """Log failed login event"""
        
        audit_log = ClientAuditLog(
            client_id=None,  # May not have client context for failed logins
            event_type=AuditEventType.LOGIN_FAILED,
            severity=AuditSeverity.MEDIUM,
            event_name="Login Failed",
            event_description=f"Failed login for {email}: {reason}",
            event_outcome="failure",
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata={
                "email": email,
                "client_slug": client_slug,
                "reason": reason
            }
        )
        
        session.add(audit_log)
        await session.flush()
    
    async def _log_security_event(
        self,
        session: AsyncSession,
        user_id: Optional[str],
        client_id: Optional[str],
        event_type: AuditEventType,
        description: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        metadata: Optional[Dict] = None
    ):
        """Log security event"""
        
        audit_log = ClientAuditLog(
            client_id=client_id,
            event_type=event_type,
            severity=severity,
            event_name="Security Event",
            event_description=description,
            event_outcome="success",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata=metadata or {},
            security_alert=severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]
        )
        
        session.add(audit_log)
        await session.flush()