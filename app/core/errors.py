from typing import Any

from fastapi import HTTPException, status


class ConfigurationError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


class AppError(HTTPException):
    """Base HTTP error that carries the project's structured error envelope."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or {},
                }
            },
        )


class AuthenticationError(AppError):
    """Raised when access credentials are missing or invalid."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_failed",
            "Authentication failed.",
        )


class AuthorizationError(AppError):
    """Raised when a role lacks permission for an action."""

    def __init__(self, action: str | None = None) -> None:
        super().__init__(
            status.HTTP_403_FORBIDDEN,
            "authorization_failed",
            "You are not allowed to perform this action.",
            {"action": action} if action else {},
        )


class DuplicateResourceError(AppError):
    """Raised when a generic unique resource constraint is violated."""

    def __init__(self, resource: str) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "duplicate_resource",
            f"{resource} already exists.",
        )


class NotFoundError(AppError):
    """Raised when a generic resource lookup returns no row."""

    def __init__(self, resource: str) -> None:
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "not_found",
            f"{resource} was not found.",
        )


class AssetNotFoundError(AppError):
    """Raised when an asset is missing or outside the user's organization."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "ASSET_NOT_FOUND",
            "Asset was not found.",
        )


class DuplicateAssetError(AppError):
    """Raised when an asset type and value already exist in the organization."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "DUPLICATE_ASSET",
            "Asset already exists.",
        )


class DuplicateRelationshipError(AppError):
    """Raised when a relationship already exists in an organization."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "DUPLICATE_RELATIONSHIP",
            "Relationship already exists.",
        )


class RateLimitExceededError(AppError):
    """Raised when an operation exceeds its configured request threshold."""

    def __init__(self, operation: str, retry_after_seconds: int) -> None:
        super().__init__(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "rate_limited",
            "Too many requests. Try again later.",
            {
                "operation": operation,
                "retry_after_seconds": retry_after_seconds,
            },
        )


class AnalysisUnavailableError(AppError):
    """Raised when analysis is configured as unavailable for this runtime."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "analysis_unavailable",
            "Analysis provider is not configured.",
        )


class AnalysisFailedError(AppError):
    """Raised when a provider call fails without exposing provider internals."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_502_BAD_GATEWAY,
            "analysis_failed",
            "Analysis provider failed to generate a report.",
        )


class AnalysisGroundingError(AppError):
    """Raised when provider output references assets outside selected evidence."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_502_BAD_GATEWAY,
            "analysis_grounding_failed",
            "Analysis provider returned ungrounded evidence.",
        )
