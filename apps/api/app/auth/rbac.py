"""
Role-Based Access Control (RBAC) System
Comprehensive permission and role management for multi-tenant architecture
"""
import enum
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.client import Client
from app.core.cache import get_redis_client


logger = logging.getLogger(__name__)


class Permission(str, enum.Enum):
    """System permissions"""
    
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    USER_INVITE = "user:invite"
    USER_ROLES_MANAGE = "user:roles:manage"
    
    # Organization/Client management
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_SETTINGS = "org:settings"
    ORG_BILLING = "org:billing"
    ORG_INTEGRATIONS = "org:integrations"
    ORG_AUDIT_LOGS = "org:audit_logs"
    
    # Voice Agents
    VOICE_AGENT_CREATE = "voice_agent:create"
    VOICE_AGENT_READ = "voice_agent:read"
    VOICE_AGENT_UPDATE = "voice_agent:update"
    VOICE_AGENT_DELETE = "voice_agent:delete"
    VOICE_AGENT_DEPLOY = "voice_agent:deploy"
    VOICE_AGENT_TRAIN = "voice_agent:train"
    
    # Conversations
    CONVERSATION_READ = "conversation:read"
    CONVERSATION_UPDATE = "conversation:update"
    CONVERSATION_DELETE = "conversation:delete"
    CONVERSATION_LIST = "conversation:list"
    CONVERSATION_EXPORT = "conversation:export"
    
    # Properties
    PROPERTY_CREATE = "property:create"
    PROPERTY_READ = "property:read"
    PROPERTY_UPDATE = "property:update"
    PROPERTY_DELETE = "property:delete"
    PROPERTY_LIST = "property:list"
    PROPERTY_IMPORT = "property:import"
    PROPERTY_EXPORT = "property:export"
    
    # Leads
    LEAD_CREATE = "lead:create"
    LEAD_READ = "lead:read"
    LEAD_UPDATE = "lead:update"
    LEAD_DELETE = "lead:delete"
    LEAD_LIST = "lead:list"
    LEAD_ASSIGN = "lead:assign"
    LEAD_EXPORT = "lead:export"
    
    # Analytics
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"
    ANALYTICS_ADVANCED = "analytics:advanced"
    
    # API Access
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"
    API_KEYS_MANAGE = "api:keys:manage"
    
    # Webhooks
    WEBHOOK_CREATE = "webhook:create"
    WEBHOOK_READ = "webhook:read"
    WEBHOOK_UPDATE = "webhook:update"
    WEBHOOK_DELETE = "webhook:delete"
    WEBHOOK_TEST = "webhook:test"
    
    # Third-party integrations
    INTEGRATION_READ = "integration:read"
    INTEGRATION_CREATE = "integration:create"
    INTEGRATION_UPDATE = "integration:update"
    INTEGRATION_DELETE = "integration:delete"
    INTEGRATION_CREDENTIALS = "integration:credentials"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_ROLES = "admin:roles"
    ADMIN_PERMISSIONS = "admin:permissions"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_BILLING = "admin:billing"
    ADMIN_COMPLIANCE = "admin:compliance"
    ADMIN_AUDIT = "admin:audit"
    
    # Super Admin (platform-wide)
    SUPER_ADMIN = "super:admin"
    SUPER_CLIENT_MANAGE = "super:client:manage"
    SUPER_SYSTEM = "super:system"


class Role(str, enum.Enum):
    """Predefined system roles"""
    
    # Client-level roles
    CLIENT_ADMIN = "client_admin"
    CLIENT_MANAGER = "client_manager"
    CLIENT_USER = "client_user"
    CLIENT_VIEWER = "client_viewer"
    
    # Specialized roles
    VOICE_AGENT_MANAGER = "voice_agent_manager"
    LEAD_MANAGER = "lead_manager"
    PROPERTY_MANAGER = "property_manager"
    ANALYTICS_VIEWER = "analytics_viewer"
    API_USER = "api_user"
    
    # Platform roles (cross-client)
    SUPER_ADMIN = "super_admin"
    PLATFORM_ADMIN = "platform_admin"
    SUPPORT_AGENT = "support_agent"


@dataclass
class RoleDefinition:
    """Role definition with permissions and constraints"""
    name: str
    display_name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    inherits_from: Optional[List[str]] = None
    is_system_role: bool = True
    client_scoped: bool = True
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionCheck:
    """Result of permission check"""
    allowed: bool
    reason: Optional[str] = None
    required_permissions: Optional[List[str]] = None
    user_permissions: Optional[List[str]] = None


class RBACService:
    """
    Role-Based Access Control Service
    Manages permissions, roles, and access control for multi-tenant system
    """
    
    def __init__(self):
        self._role_definitions = self._initialize_role_definitions()
        self._permission_cache_ttl = 300  # 5 minutes
    
    def _initialize_role_definitions(self) -> Dict[str, RoleDefinition]:
        """Initialize predefined role definitions"""
        
        roles = {
            # Client Admin - Full access to client resources
            Role.CLIENT_ADMIN.value: RoleDefinition(
                name=Role.CLIENT_ADMIN.value,
                display_name="Client Administrator",
                description="Full administrative access to client resources",
                permissions={
                    # User management
                    Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE,
                    Permission.USER_DELETE, Permission.USER_LIST, Permission.USER_INVITE,
                    Permission.USER_ROLES_MANAGE,
                    
                    # Organization management
                    Permission.ORG_READ, Permission.ORG_UPDATE, Permission.ORG_SETTINGS,
                    Permission.ORG_BILLING, Permission.ORG_INTEGRATIONS, Permission.ORG_AUDIT_LOGS,
                    
                    # Voice agents
                    Permission.VOICE_AGENT_CREATE, Permission.VOICE_AGENT_READ,
                    Permission.VOICE_AGENT_UPDATE, Permission.VOICE_AGENT_DELETE,
                    Permission.VOICE_AGENT_DEPLOY, Permission.VOICE_AGENT_TRAIN,
                    
                    # All data access
                    Permission.CONVERSATION_READ, Permission.CONVERSATION_UPDATE,
                    Permission.CONVERSATION_DELETE, Permission.CONVERSATION_LIST,
                    Permission.CONVERSATION_EXPORT,
                    
                    Permission.PROPERTY_CREATE, Permission.PROPERTY_READ,
                    Permission.PROPERTY_UPDATE, Permission.PROPERTY_DELETE,
                    Permission.PROPERTY_LIST, Permission.PROPERTY_IMPORT,
                    Permission.PROPERTY_EXPORT,
                    
                    Permission.LEAD_CREATE, Permission.LEAD_READ, Permission.LEAD_UPDATE,
                    Permission.LEAD_DELETE, Permission.LEAD_LIST, Permission.LEAD_ASSIGN,
                    Permission.LEAD_EXPORT,
                    
                    # Analytics and reporting
                    Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT,
                    Permission.ANALYTICS_ADVANCED,
                    
                    # API and integrations
                    Permission.API_READ, Permission.API_WRITE, Permission.API_KEYS_MANAGE,
                    Permission.WEBHOOK_CREATE, Permission.WEBHOOK_READ,
                    Permission.WEBHOOK_UPDATE, Permission.WEBHOOK_DELETE, Permission.WEBHOOK_TEST,
                    Permission.INTEGRATION_READ, Permission.INTEGRATION_CREATE,
                    Permission.INTEGRATION_UPDATE, Permission.INTEGRATION_DELETE,
                    Permission.INTEGRATION_CREDENTIALS,
                    
                    # Admin functions
                    Permission.ADMIN_USERS, Permission.ADMIN_ROLES, Permission.ADMIN_BILLING,
                    Permission.ADMIN_COMPLIANCE, Permission.ADMIN_AUDIT
                }
            ),
            
            # Client Manager - Management without user admin
            Role.CLIENT_MANAGER.value: RoleDefinition(
                name=Role.CLIENT_MANAGER.value,
                display_name="Client Manager",
                description="Management access to client resources without user administration",
                permissions={
                    Permission.USER_READ, Permission.USER_LIST,
                    Permission.ORG_READ, Permission.ORG_SETTINGS,
                    
                    Permission.VOICE_AGENT_CREATE, Permission.VOICE_AGENT_READ,
                    Permission.VOICE_AGENT_UPDATE, Permission.VOICE_AGENT_DEPLOY,
                    Permission.VOICE_AGENT_TRAIN,
                    
                    Permission.CONVERSATION_READ, Permission.CONVERSATION_UPDATE,
                    Permission.CONVERSATION_LIST, Permission.CONVERSATION_EXPORT,
                    
                    Permission.PROPERTY_CREATE, Permission.PROPERTY_READ,
                    Permission.PROPERTY_UPDATE, Permission.PROPERTY_LIST,
                    Permission.PROPERTY_IMPORT, Permission.PROPERTY_EXPORT,
                    
                    Permission.LEAD_CREATE, Permission.LEAD_READ, Permission.LEAD_UPDATE,
                    Permission.LEAD_LIST, Permission.LEAD_ASSIGN, Permission.LEAD_EXPORT,
                    
                    Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT,
                    Permission.API_READ, Permission.API_WRITE,
                    
                    Permission.WEBHOOK_CREATE, Permission.WEBHOOK_READ,
                    Permission.WEBHOOK_UPDATE, Permission.WEBHOOK_TEST,
                    
                    Permission.INTEGRATION_READ, Permission.INTEGRATION_UPDATE
                }
            ),
            
            # Client User - Standard user access
            Role.CLIENT_USER.value: RoleDefinition(
                name=Role.CLIENT_USER.value,
                display_name="Client User",
                description="Standard user access to client resources",
                permissions={
                    Permission.USER_READ,
                    Permission.ORG_READ,
                    
                    Permission.VOICE_AGENT_READ,
                    
                    Permission.CONVERSATION_READ, Permission.CONVERSATION_LIST,
                    
                    Permission.PROPERTY_READ, Permission.PROPERTY_LIST,
                    
                    Permission.LEAD_CREATE, Permission.LEAD_READ, Permission.LEAD_UPDATE,
                    Permission.LEAD_LIST,
                    
                    Permission.ANALYTICS_READ,
                    Permission.API_READ,
                    
                    Permission.WEBHOOK_READ,
                    Permission.INTEGRATION_READ
                }
            ),
            
            # Client Viewer - Read-only access
            Role.CLIENT_VIEWER.value: RoleDefinition(
                name=Role.CLIENT_VIEWER.value,
                display_name="Client Viewer",
                description="Read-only access to client resources",
                permissions={
                    Permission.USER_READ,
                    Permission.ORG_READ,
                    Permission.VOICE_AGENT_READ,
                    Permission.CONVERSATION_READ, Permission.CONVERSATION_LIST,
                    Permission.PROPERTY_READ, Permission.PROPERTY_LIST,
                    Permission.LEAD_READ, Permission.LEAD_LIST,
                    Permission.ANALYTICS_READ,
                    Permission.API_READ,
                    Permission.WEBHOOK_READ,
                    Permission.INTEGRATION_READ
                }
            ),
            
            # Specialized roles
            Role.VOICE_AGENT_MANAGER.value: RoleDefinition(
                name=Role.VOICE_AGENT_MANAGER.value,
                display_name="Voice Agent Manager",
                description="Specialized role for voice agent management",
                permissions={
                    Permission.USER_READ, Permission.ORG_READ,
                    Permission.VOICE_AGENT_CREATE, Permission.VOICE_AGENT_READ,
                    Permission.VOICE_AGENT_UPDATE, Permission.VOICE_AGENT_DELETE,
                    Permission.VOICE_AGENT_DEPLOY, Permission.VOICE_AGENT_TRAIN,
                    Permission.CONVERSATION_READ, Permission.CONVERSATION_LIST,
                    Permission.ANALYTICS_READ,
                    Permission.INTEGRATION_READ, Permission.INTEGRATION_UPDATE
                }
            ),
            
            Role.LEAD_MANAGER.value: RoleDefinition(
                name=Role.LEAD_MANAGER.value,
                display_name="Lead Manager",
                description="Specialized role for lead management",
                permissions={
                    Permission.USER_READ, Permission.ORG_READ,
                    Permission.LEAD_CREATE, Permission.LEAD_READ, Permission.LEAD_UPDATE,
                    Permission.LEAD_DELETE, Permission.LEAD_LIST, Permission.LEAD_ASSIGN,
                    Permission.LEAD_EXPORT,
                    Permission.CONVERSATION_READ, Permission.CONVERSATION_LIST,
                    Permission.PROPERTY_READ, Permission.PROPERTY_LIST,
                    Permission.ANALYTICS_READ,
                    Permission.INTEGRATION_READ
                }
            ),
            
            Role.PROPERTY_MANAGER.value: RoleDefinition(
                name=Role.PROPERTY_MANAGER.value,
                display_name="Property Manager",
                description="Specialized role for property management",
                permissions={
                    Permission.USER_READ, Permission.ORG_READ,
                    Permission.PROPERTY_CREATE, Permission.PROPERTY_READ,
                    Permission.PROPERTY_UPDATE, Permission.PROPERTY_DELETE,
                    Permission.PROPERTY_LIST, Permission.PROPERTY_IMPORT,
                    Permission.PROPERTY_EXPORT,
                    Permission.LEAD_READ, Permission.LEAD_LIST,
                    Permission.ANALYTICS_READ,
                    Permission.INTEGRATION_READ
                }
            ),
            
            Role.ANALYTICS_VIEWER.value: RoleDefinition(
                name=Role.ANALYTICS_VIEWER.value,
                display_name="Analytics Viewer",
                description="Specialized role for analytics and reporting",
                permissions={
                    Permission.USER_READ, Permission.ORG_READ,
                    Permission.CONVERSATION_READ, Permission.CONVERSATION_LIST,
                    Permission.PROPERTY_READ, Permission.PROPERTY_LIST,
                    Permission.LEAD_READ, Permission.LEAD_LIST,
                    Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT,
                    Permission.ANALYTICS_ADVANCED
                }
            ),
            
            Role.API_USER.value: RoleDefinition(
                name=Role.API_USER.value,
                display_name="API User",
                description="API access role for programmatic integration",
                permissions={
                    Permission.API_READ, Permission.API_WRITE,
                    Permission.VOICE_AGENT_READ,
                    Permission.CONVERSATION_READ, Permission.CONVERSATION_LIST,
                    Permission.PROPERTY_READ, Permission.PROPERTY_LIST,
                    Permission.LEAD_READ, Permission.LEAD_LIST,
                    Permission.WEBHOOK_READ, Permission.WEBHOOK_TEST,
                    Permission.INTEGRATION_READ
                }
            ),
            
            # Platform-wide roles
            Role.SUPER_ADMIN.value: RoleDefinition(
                name=Role.SUPER_ADMIN.value,
                display_name="Super Administrator",
                description="Platform-wide administrative access",
                client_scoped=False,
                permissions={Permission.SUPER_ADMIN, Permission.SUPER_CLIENT_MANAGE, Permission.SUPER_SYSTEM}
            ),
            
            Role.PLATFORM_ADMIN.value: RoleDefinition(
                name=Role.PLATFORM_ADMIN.value,
                display_name="Platform Administrator",
                description="Platform administration without client management",
                client_scoped=False,
                permissions={Permission.ADMIN_SYSTEM, Permission.ADMIN_COMPLIANCE, Permission.ADMIN_AUDIT}
            ),
            
            Role.SUPPORT_AGENT.value: RoleDefinition(
                name=Role.SUPPORT_AGENT.value,
                display_name="Support Agent",
                description="Customer support access across clients",
                client_scoped=False,
                permissions={
                    Permission.USER_READ, Permission.ORG_READ, Permission.ORG_AUDIT_LOGS,
                    Permission.CONVERSATION_READ, Permission.CONVERSATION_LIST,
                    Permission.ANALYTICS_READ
                }
            )
        }
        
        return roles
    
    async def get_user_permissions(
        self, 
        session: AsyncSession, 
        user_id: str, 
        client_id: str
    ) -> List[str]:
        """
        Get all permissions for a user within a client context
        
        Args:
            session: Database session
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            List of permission strings
        """
        
        try:
            # Check cache first
            cache_key = f"user_permissions:{user_id}:{client_id}"
            cached_permissions = await self._get_cached_permissions(cache_key)
            if cached_permissions is not None:
                return cached_permissions
            
            # Get user with roles
            user_query = select(User).where(User.id == user_id)
            result = await session.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                return []
            
            # Get user's roles for this client
            user_roles = await self._get_user_roles(session, user_id, client_id)
            
            # Collect permissions from roles
            permissions = set()
            
            for role in user_roles:
                role_definition = self._role_definitions.get(role)
                if role_definition:
                    permissions.update(role_definition.permissions)
            
            # Add any direct permissions (if implemented)
            # direct_permissions = await self._get_user_direct_permissions(session, user_id, client_id)
            # permissions.update(direct_permissions)
            
            permission_list = [p.value for p in permissions]
            
            # Cache the permissions
            await self._cache_permissions(cache_key, permission_list)
            
            return permission_list
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}", exc_info=True)
            return []
    
    async def check_permission(
        self,
        session: AsyncSession,
        user_id: str,
        client_id: str,
        required_permission: str,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PermissionCheck:
        """
        Check if user has specific permission
        
        Args:
            session: Database session
            user_id: User identifier
            client_id: Client identifier
            required_permission: Permission to check
            resource_id: Optional resource identifier
            context: Additional context for permission check
            
        Returns:
            PermissionCheck result
        """
        
        try:
            user_permissions = await self.get_user_permissions(session, user_id, client_id)
            
            # Check for super admin permission (bypasses all checks)
            if Permission.SUPER_ADMIN.value in user_permissions:
                return PermissionCheck(allowed=True, reason="Super admin access")
            
            # Check direct permission
            if required_permission in user_permissions:
                # Additional resource-level checks could be added here
                return PermissionCheck(allowed=True)
            
            # Check for wildcard permissions (if implemented)
            permission_parts = required_permission.split(":")
            if len(permission_parts) > 1:
                wildcard_permission = f"{permission_parts[0]}:*"
                if wildcard_permission in user_permissions:
                    return PermissionCheck(allowed=True, reason="Wildcard permission match")
            
            return PermissionCheck(
                allowed=False,
                reason="Insufficient permissions",
                required_permissions=[required_permission],
                user_permissions=user_permissions
            )
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}", exc_info=True)
            return PermissionCheck(
                allowed=False,
                reason=f"Permission check failed: {str(e)}"
            )
    
    async def check_multiple_permissions(
        self,
        session: AsyncSession,
        user_id: str,
        client_id: str,
        required_permissions: List[str],
        require_all: bool = True
    ) -> PermissionCheck:
        """
        Check multiple permissions at once
        
        Args:
            session: Database session
            user_id: User identifier
            client_id: Client identifier
            required_permissions: List of permissions to check
            require_all: If True, user must have ALL permissions. If False, ANY permission is sufficient.
            
        Returns:
            PermissionCheck result
        """
        
        try:
            user_permissions = await self.get_user_permissions(session, user_id, client_id)
            user_perm_set = set(user_permissions)
            required_perm_set = set(required_permissions)
            
            # Super admin bypass
            if Permission.SUPER_ADMIN.value in user_permissions:
                return PermissionCheck(allowed=True, reason="Super admin access")
            
            if require_all:
                missing_permissions = required_perm_set - user_perm_set
                if not missing_permissions:
                    return PermissionCheck(allowed=True)
                else:
                    return PermissionCheck(
                        allowed=False,
                        reason="Missing required permissions",
                        required_permissions=list(missing_permissions),
                        user_permissions=user_permissions
                    )
            else:
                # ANY permission is sufficient
                if required_perm_set & user_perm_set:
                    return PermissionCheck(allowed=True)
                else:
                    return PermissionCheck(
                        allowed=False,
                        reason="No matching permissions found",
                        required_permissions=required_permissions,
                        user_permissions=user_permissions
                    )
                    
        except Exception as e:
            logger.error(f"Error checking multiple permissions: {e}")
            return PermissionCheck(
                allowed=False,
                reason=f"Permission check failed: {str(e)}"
            )
    
    async def assign_role_to_user(
        self,
        session: AsyncSession,
        user_id: str,
        client_id: str,
        role: str,
        assigned_by: Optional[str] = None
    ) -> bool:
        """
        Assign role to user within client context
        
        Args:
            session: Database session
            user_id: User identifier
            client_id: Client identifier
            role: Role to assign
            assigned_by: User who performed the assignment
            
        Returns:
            Success status
        """
        
        try:
            # Validate role exists
            if role not in self._role_definitions:
                logger.error(f"Unknown role: {role}")
                return False
            
            # Check if role is client-scoped
            role_def = self._role_definitions[role]
            if role_def.client_scoped and not client_id:
                logger.error(f"Client-scoped role {role} requires client_id")
                return False
            
            # Get user
            user = await session.get(User, user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Implementation would depend on your user-role relationship model
            # For now, assume user.role is a simple string field
            user.role = role
            await session.commit()
            
            # Clear permissions cache
            await self._invalidate_permissions_cache(user_id, client_id)
            
            logger.info(f"Assigned role {role} to user {user_id} in client {client_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error assigning role: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def remove_role_from_user(
        self,
        session: AsyncSession,
        user_id: str,
        client_id: str,
        role: str,
        removed_by: Optional[str] = None
    ) -> bool:
        """
        Remove role from user within client context
        """
        
        try:
            # Get user
            user = await session.get(User, user_id)
            if not user:
                return False
            
            # Remove role (implementation depends on your data model)
            if user.role == role:
                user.role = Role.CLIENT_USER.value  # Default role
                await session.commit()
                
                # Clear permissions cache
                await self._invalidate_permissions_cache(user_id, client_id)
                
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error removing role: {e}")
            await session.rollback()
            return False
    
    def get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a specific role"""
        
        role_def = self._role_definitions.get(role)
        if not role_def:
            return []
        
        return [p.value for p in role_def.permissions]
    
    def get_available_roles(self, client_scoped_only: bool = True) -> List[Dict[str, Any]]:
        """Get list of available roles"""
        
        roles = []
        for role_name, role_def in self._role_definitions.items():
            if client_scoped_only and not role_def.client_scoped:
                continue
                
            roles.append({
                "name": role_def.name,
                "display_name": role_def.display_name,
                "description": role_def.description,
                "permissions_count": len(role_def.permissions),
                "is_system_role": role_def.is_system_role,
                "client_scoped": role_def.client_scoped
            })
        
        return sorted(roles, key=lambda x: x["display_name"])
    
    def validate_permission(self, permission: str) -> bool:
        """Validate that a permission string is valid"""
        
        try:
            Permission(permission)
            return True
        except ValueError:
            return False
    
    # Private helper methods
    
    async def _get_user_roles(
        self, 
        session: AsyncSession, 
        user_id: str, 
        client_id: str
    ) -> List[str]:
        """Get roles for user in client context"""
        
        # This is a simplified implementation
        # In a real system, you might have a user_roles table with client context
        
        user = await session.get(User, user_id)
        if not user or not user.role:
            return [Role.CLIENT_USER.value]  # Default role
        
        return [user.role]
    
    async def _get_cached_permissions(self, cache_key: str) -> Optional[List[str]]:
        """Get permissions from cache"""
        
        redis_client = await get_redis_client()
        if not redis_client:
            return None
        
        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                import json
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error getting cached permissions: {e}")
        
        return None
    
    async def _cache_permissions(self, cache_key: str, permissions: List[str]):
        """Cache permissions"""
        
        redis_client = await get_redis_client()
        if not redis_client:
            return
        
        try:
            import json
            await redis_client.setex(
                cache_key, 
                self._permission_cache_ttl, 
                json.dumps(permissions)
            )
        except Exception as e:
            logger.error(f"Error caching permissions: {e}")
    
    async def _invalidate_permissions_cache(self, user_id: str, client_id: str):
        """Invalidate cached permissions for user"""
        
        redis_client = await get_redis_client()
        if not redis_client:
            return
        
        try:
            cache_key = f"user_permissions:{user_id}:{client_id}"
            await redis_client.delete(cache_key)
        except Exception as e:
            logger.error(f"Error invalidating permissions cache: {e}")


# Permission decorator for FastAPI routes
def require_permission(permission: str):
    """Decorator to require specific permission for route access"""
    
    def decorator(func):
        func._required_permission = permission
        return func
    
    return decorator


def require_any_permission(*permissions: str):
    """Decorator to require any of the specified permissions"""
    
    def decorator(func):
        func._required_permissions = list(permissions)
        func._require_all_permissions = False
        return func
    
    return decorator


def require_all_permissions(*permissions: str):
    """Decorator to require all of the specified permissions"""
    
    def decorator(func):
        func._required_permissions = list(permissions)
        func._require_all_permissions = True
        return func
    
    return decorator


def require_role(role: str):
    """Decorator to require specific role"""
    
    def decorator(func):
        func._required_role = role
        return func
    
    return decorator