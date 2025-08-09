"""
Custom exception classes for Seiketsu AI API
Provides structured error handling with proper HTTP status codes and error tracking
"""

from typing import Any, Dict, Optional, List
from fastapi import HTTPException


class APIException(HTTPException):
    """
    Base API exception class with enhanced error information
    """
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message, headers=headers)


class ValidationException(APIException):
    """
    Raised when request validation fails
    """
    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[List[Dict[str, Any]]] = None,
        field: Optional[str] = None
    ):
        self.errors = errors or []
        self.field = field
        super().__init__(
            status_code=422,
            message=message,
            error_code="VALIDATION_ERROR",
            details={"errors": self.errors, "field": field}
        )


class AuthenticationException(APIException):
    """
    Raised when authentication fails
    """
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=401,
            message=message,
            error_code="AUTHENTICATION_ERROR",
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationException(APIException):
    """
    Raised when authorization fails (user authenticated but lacks permission)
    """
    def __init__(self, message: str = "Insufficient permissions", required_permission: Optional[str] = None):
        super().__init__(
            status_code=403,
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details={"required_permission": required_permission}
        )


class ResourceNotFoundException(APIException):
    """
    Raised when a requested resource is not found
    """
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        super().__init__(
            status_code=404,
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


class ConflictException(APIException):
    """
    Raised when a request conflicts with current resource state
    """
    def __init__(self, message: str, resource: Optional[str] = None):
        super().__init__(
            status_code=409,
            message=message,
            error_code="RESOURCE_CONFLICT",
            details={"resource": resource}
        )


class RateLimitException(APIException):
    """
    Raised when rate limit is exceeded
    """
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        super().__init__(
            status_code=429,
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
            headers=headers
        )


class ServiceUnavailableException(APIException):
    """
    Raised when an external service is unavailable
    """
    def __init__(self, service_name: str, message: Optional[str] = None):
        message = message or f"{service_name} service is currently unavailable"
        super().__init__(
            status_code=503,
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service_name}
        )


class ExternalServiceException(APIException):
    """
    Raised when an external service returns an error
    """
    def __init__(
        self,
        service_name: str,
        message: str,
        service_error_code: Optional[str] = None,
        status_code: int = 502
    ):
        super().__init__(
            status_code=status_code,
            message=f"{service_name} error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={
                "service": service_name,
                "service_error_code": service_error_code,
                "original_message": message
            }
        )


class DatabaseException(APIException):
    """
    Raised when database operations fail
    """
    def __init__(self, message: str = "Database operation failed", operation: Optional[str] = None):
        super().__init__(
            status_code=500,
            message=message,
            error_code="DATABASE_ERROR",
            details={"operation": operation}
        )


class CacheException(APIException):
    """
    Raised when cache operations fail
    """
    def __init__(self, message: str = "Cache operation failed", operation: Optional[str] = None):
        super().__init__(
            status_code=500,
            message=message,
            error_code="CACHE_ERROR",
            details={"operation": operation}
        )


class BusinessLogicException(APIException):
    """
    Raised when business logic constraints are violated
    """
    def __init__(self, message: str, rule: Optional[str] = None):
        super().__init__(
            status_code=400,
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            details={"rule": rule}
        )


class VoiceProcessingException(APIException):
    """
    Raised when voice processing operations fail
    """
    def __init__(
        self,
        message: str = "Voice processing failed",
        operation: Optional[str] = None,
        provider: Optional[str] = None
    ):
        super().__init__(
            status_code=422,
            message=message,
            error_code="VOICE_PROCESSING_ERROR",
            details={"operation": operation, "provider": provider}
        )


class AIServiceException(APIException):
    """
    Raised when AI service operations fail
    """
    def __init__(
        self,
        message: str = "AI service error",
        service: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__(
            status_code=502,
            message=message,
            error_code="AI_SERVICE_ERROR",
            details={"service": service, "model": model}
        )


class UsageLimitException(APIException):
    """
    Raised when usage limits are exceeded
    """
    def __init__(
        self,
        message: str = "Usage limit exceeded",
        limit_type: Optional[str] = None,
        current_usage: Optional[int] = None,
        limit: Optional[int] = None
    ):
        super().__init__(
            status_code=429,
            message=message,
            error_code="USAGE_LIMIT_EXCEEDED",
            details={
                "limit_type": limit_type,
                "current_usage": current_usage,
                "limit": limit
            }
        )


class TenantException(APIException):
    """
    Raised when tenant-related operations fail
    """
    def __init__(self, message: str, tenant_id: Optional[str] = None):
        super().__init__(
            status_code=400,
            message=message,
            error_code="TENANT_ERROR",
            details={"tenant_id": tenant_id}
        )


class WebhookException(APIException):
    """
    Raised when webhook operations fail
    """
    def __init__(
        self,
        message: str = "Webhook operation failed",
        webhook_url: Optional[str] = None,
        response_code: Optional[int] = None
    ):
        super().__init__(
            status_code=502,
            message=message,
            error_code="WEBHOOK_ERROR",
            details={
                "webhook_url": webhook_url,
                "response_code": response_code
            }
        )


class ClientProvisioningException(APIException):
    """
    Raised when client provisioning operations fail
    """
    def __init__(
        self,
        message: str = "Client provisioning failed",
        client_id: Optional[str] = None,
        stage: Optional[str] = None
    ):
        super().__init__(
            status_code=500,
            message=message,
            error_code="CLIENT_PROVISIONING_ERROR",
            details={"client_id": client_id, "stage": stage}
        )


# Exception mapping for common HTTP status codes
STATUS_CODE_EXCEPTIONS = {
    400: BusinessLogicException,
    401: AuthenticationException,
    403: AuthorizationException,
    404: ResourceNotFoundException,
    409: ConflictException,
    422: ValidationException,
    429: RateLimitException,
    500: APIException,
    502: ExternalServiceException,
    503: ServiceUnavailableException,
}


def create_exception_from_status_code(
    status_code: int,
    message: str,
    **kwargs
) -> APIException:
    """
    Create appropriate exception based on HTTP status code
    """
    exception_class = STATUS_CODE_EXCEPTIONS.get(status_code, APIException)
    return exception_class(message=message, **kwargs)