from typing import Any

from fastapi import HTTPException, status


class ConfigurationError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


class AppError(HTTPException):
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
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_failed",
            "Authentication failed.",
        )


class AuthorizationError(AppError):
    def __init__(self, action: str | None = None) -> None:
        super().__init__(
            status.HTTP_403_FORBIDDEN,
            "authorization_failed",
            "You are not allowed to perform this action.",
            {"action": action} if action else {},
        )


class DuplicateResourceError(AppError):
    def __init__(self, resource: str) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "duplicate_resource",
            f"{resource} already exists.",
        )


class NotFoundError(AppError):
    def __init__(self, resource: str) -> None:
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "not_found",
            f"{resource} was not found.",
        )

