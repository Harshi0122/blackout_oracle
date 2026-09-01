"""
Blackout Oracle - Security Utilities.

Provides authentication and authorization utilities for the backend.

This module handles:

- Password hashing
- Password verification
- JWT access-token creation
- JWT access-token verification
- Bearer-token authentication
- Basic role-based authorization helpers

IMPORTANT
---------

This security layer protects the Blackout Oracle application.

It does NOT provide direct access to electrical-grid infrastructure.

Production deployments must use:

- HTTPS
- Strong secret keys
- Proper identity management
- Short-lived access tokens
- Role-based access control
- Secure secret storage
- Audit logging
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
)


# ============================================================
# JWT CONFIGURATION
# ============================================================

ALGORITHM = "HS256"


# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# ============================================================
# OAUTH2
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(password: str) -> str:
    """
    Hash a plain-text password.

    Passwords must never be stored directly.
    """

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    return pwd_context.hash(
        password
    )


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against its stored hash.
    """

    if not plain_password:
        return False

    if not hashed_password:
        return False

    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


# ============================================================
# JWT CREATION
# ============================================================

def create_access_token(
    subject: str,
    role: str = "user",
    expires_minutes: Optional[int] = None,
) -> str:
    """
    Create a signed JWT access token.

    Parameters
    ----------
    subject:
        Unique user identifier.

    role:
        User role.

    expires_minutes:
        Token lifetime in minutes.

    Returns
    -------
    str
        Encoded JWT token.
    """

    if not subject:
        raise ValueError(
            "Token subject cannot be empty."
        )

    if expires_minutes is None:
        expires_minutes = (
            settings.access_token_expire_minutes
        )

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            minutes=expires_minutes
        )
    )

    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


# ============================================================
# JWT VERIFICATION
# ============================================================

def decode_access_token(
    token: str,
) -> dict:
    """
    Decode and verify a JWT access token.

    Raises
    ------
    AuthenticationError
        If the token is invalid or expired.
    """

    if not token:
        raise AuthenticationError(
            "Access token is missing."
        )

    try:

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )

    except JWTError as exc:

        raise AuthenticationError(
            "Invalid or expired access token."
        ) from exc

    subject = payload.get(
        "sub"
    )

    if not subject:
        raise AuthenticationError(
            "Access token does not contain a valid subject."
        )

    return payload


# ============================================================
# CURRENT USER
# ============================================================

class AuthenticatedUser:
    """
    Represents an authenticated Blackout Oracle user.
    """

    def __init__(
        self,
        user_id: str,
        role: str,
    ) -> None:

        self.user_id = user_id
        self.role = role

    def __repr__(self) -> str:
        return (
            "AuthenticatedUser("
            f"user_id='{self.user_id}', "
            f"role='{self.role}'"
            ")"
        )


# ============================================================
# FASTAPI AUTHENTICATION DEPENDENCY
# ============================================================

async def get_authenticated_user(
    token: str = Depends(
        oauth2_scheme
    ),
) -> AuthenticatedUser:
    """
    FastAPI dependency that authenticates the current request.

    Usage:

        @router.get("/protected")
        async def protected_route(
            user: AuthenticatedUser = Depends(
                get_authenticated_user
            )
        ):
            ...
    """

    try:

        payload = decode_access_token(
            token
        )

    except AuthenticationError as exc:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={
                "WWW-Authenticate": "Bearer"
            },
        ) from exc

    subject = payload.get(
        "sub"
    )

    role = payload.get(
        "role",
        "user",
    )

    return AuthenticatedUser(
        user_id=str(subject),
        role=str(role),
    )


# ============================================================
# ROLE AUTHORIZATION
# ============================================================

def require_roles(
    *allowed_roles: str,
):
    """
    Create a FastAPI dependency requiring one of the specified roles.

    Example:

        require_roles("admin", "operator")
    """

    async def role_dependency(
        user: AuthenticatedUser = Depends(
            get_authenticated_user
        ),
    ) -> AuthenticatedUser:

        if user.role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to perform this operation."
                ),
            )

        return user

    return role_dependency


# ============================================================
# COMMON ROLE DEPENDENCIES
# ============================================================

async def require_admin(
    user: AuthenticatedUser = Depends(
        get_authenticated_user
    ),
) -> AuthenticatedUser:
    """
    Require administrator privileges.
    """

    if user.role != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required.",
        )

    return user


async def require_operator(
    user: AuthenticatedUser = Depends(
        get_authenticated_user
    ),
) -> AuthenticatedUser:
    """
    Require operator privileges.

    Operators may access operational analysis features,
    subject to the application's authorization policies.
    """

    allowed_roles = {
        "operator",
        "admin",
    }

    if user.role not in allowed_roles:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator privileges required.",
        )

    return user


async def require_engineer(
    user: AuthenticatedUser = Depends(
        get_authenticated_user
    ),
) -> AuthenticatedUser:
    """
    Require engineer-level privileges.
    """

    allowed_roles = {
        "engineer",
        "operator",
        "admin",
    }

    if user.role not in allowed_roles:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer privileges required.",
        )

    return user


# ============================================================
# TELEMETRY ACCESS
# ============================================================

async def require_telemetry_access(
    user: AuthenticatedUser = Depends(
        get_authenticated_user
    ),
) -> AuthenticatedUser:
    """
    Verify access to grid telemetry.
    """

    allowed_roles = {
        "analyst",
        "engineer",
        "operator",
        "admin",
    }

    if user.role not in allowed_roles:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to access telemetry."
            ),
        )

    return user


# ============================================================
# AI AGENT ACCESS
# ============================================================

async def require_agent_access(
    user: AuthenticatedUser = Depends(
        get_authenticated_user
    ),
) -> AuthenticatedUser:
    """
    Verify access to Blackout Oracle AI-agent operations.
    """

    allowed_roles = {
        "engineer",
        "operator",
        "admin",
    }

    if user.role not in allowed_roles:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to access AI-agent operations."
            ),
        )

    return user


# ============================================================
# HUMAN APPROVAL
# ============================================================

async def require_human_approval(
    user: AuthenticatedUser = Depends(
        get_authenticated_user
    ),
) -> AuthenticatedUser:
    """
    Require an authorized human user.

    This is particularly important for Blackout Oracle.

    AI-generated recommendations must not automatically become
    real-world operational commands.
    """

    allowed_roles = {
        "engineer",
        "operator",
        "admin",
    }

    if user.role not in allowed_roles:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Authorized human approval is required."
            ),
        )

    return user


# ============================================================
# TOKEN VALIDATION HELPER
# ============================================================

def validate_token(
    token: str,
) -> bool:
    """
    Return True if a JWT is valid.

    This helper is useful for services that need to perform
    a simple token validity check.
    """

    try:

        decode_access_token(
            token
        )

        return True

    except AuthenticationError:

        return False


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "ALGORITHM",
    "pwd_context",
    "oauth2_scheme",
    "AuthenticatedUser",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "validate_token",
    "get_authenticated_user",
    "require_roles",
    "require_admin",
    "require_operator",
    "require_engineer",
    "require_telemetry_access",
    "require_agent_access",
    "require_human_approval",
]