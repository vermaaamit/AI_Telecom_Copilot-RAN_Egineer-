"""RBAC & Authentication module for AI Telecom Copilot – RAN Engineer.

Provides JWT token issuance/validation, role-based access control,
and FastAPI security dependencies.
"""
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel, Field

# Security settings
SECRET_KEY = os.getenv("JWT_SECRET", "ran-engineer-telecom-copilot-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8-hour shift


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    RAN_ENGINEER = "RAN_ENGINEER"
    VIEWER = "VIEWER"


# Role permission definitions
ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
    UserRole.VIEWER: [
        "read:datasets",
        "read:cells",
        "read:alarms",
        "read:incidents",
        "read:kpis",
        "read:knowledge",
        "read:reports",
        "read:oran",
    ],
    UserRole.RAN_ENGINEER: [
        "read:datasets",
        "read:cells",
        "read:alarms",
        "read:incidents",
        "read:kpis",
        "read:knowledge",
        "read:reports",
        "read:oran",
        "write:datasets",
        "write:alarms",
        "write:incidents",
        "investigate:agents",
        "write:oran",
        "approve:oran",
        "generate:reports",
    ],
    UserRole.ADMIN: [
        "read:datasets",
        "read:cells",
        "read:alarms",
        "read:incidents",
        "read:kpis",
        "read:knowledge",
        "read:reports",
        "read:oran",
        "write:datasets",
        "write:alarms",
        "write:incidents",
        "investigate:agents",
        "write:oran",
        "approve:oran",
        "generate:reports",
        "admin:system",
        "admin:users",
        "admin:config",
    ],
}


class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool = True
    permissions: List[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: User


class LoginRequest(BaseModel):
    email: str
    password: str


# Deterministic simulated user registry for RAN operations
def _hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


# Default password for demo accounts: "telecom123!"
DEFAULT_PWD_HASH = _hash_password("telecom123!")

DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "admin@telecom.ai": {
        "id": "usr-admin-01",
        "username": "noc_architect",
        "email": "admin@telecom.ai",
        "full_name": "Lead NOC Architect",
        "role": UserRole.ADMIN,
        "password_hash": DEFAULT_PWD_HASH,
        "is_active": True,
    },
    "engineer@telecom.ai": {
        "id": "usr-eng-01",
        "username": "ran_lead",
        "email": "engineer@telecom.ai",
        "full_name": "Senior RAN Optimization Engineer",
        "role": UserRole.RAN_ENGINEER,
        "password_hash": DEFAULT_PWD_HASH,
        "is_active": True,
    },
    "viewer@telecom.ai": {
        "id": "usr-view-01",
        "username": "field_observer",
        "email": "viewer@telecom.ai",
        "full_name": "Field Ops Technician",
        "role": UserRole.VIEWER,
        "password_hash": DEFAULT_PWD_HASH,
        "is_active": True,
    },
}


def create_access_token(user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Issues a cryptographically signed HS256 JWT access token."""
    to_encode = user_data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "TOKEN_EXPIRED", "message": "Authentication token has expired.", "details": []}},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid authentication token signature or format.", "details": []}},
        )


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticates against the demo user store."""
    user_record = DEMO_USERS.get(email.lower().strip())
    if not user_record:
        return None
    if _hash_password(password) != user_record["password_hash"]:
        return None
    role = user_record["role"]
    return User(
        id=user_record["id"],
        username=user_record["username"],
        email=user_record["email"],
        full_name=user_record["full_name"],
        role=role,
        is_active=user_record["is_active"],
        permissions=ROLE_PERMISSIONS.get(role, []),
    )


# Bearer token extractor (auto_error=False allows dev fallback)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> User:
    """Resolves authenticated user from JWT Bearer token or provides dev-fallback."""
    if credentials and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        email = payload.get("sub") or payload.get("email")
        if email and email in DEMO_USERS:
            rec = DEMO_USERS[email]
            role = rec["role"]
            return User(
                id=rec["id"],
                username=rec["username"],
                email=rec["email"],
                full_name=rec["full_name"],
                role=role,
                is_active=rec["is_active"],
                permissions=ROLE_PERMISSIONS.get(role, []),
            )
        # Fallback if arbitrary payload
        role = UserRole(payload.get("role", UserRole.RAN_ENGINEER.value))
        return User(
            id=payload.get("user_id", "usr-jwt"),
            username=payload.get("username", "ran_user"),
            email=email or "engineer@telecom.ai",
            full_name=payload.get("full_name", "RAN Engineer"),
            role=role,
            is_active=True,
            permissions=ROLE_PERMISSIONS.get(role, []),
        )

    # In development/test mode, fall back to default RAN Engineer
    rec = DEMO_USERS["engineer@telecom.ai"]
    role = rec["role"]
    return User(
        id=rec["id"],
        username=rec["username"],
        email=rec["email"],
        full_name=rec["full_name"],
        role=role,
        is_active=rec["is_active"],
        permissions=ROLE_PERMISSIONS.get(role, []),
    )


def require_role(*allowed_roles: UserRole):
    """FastAPI dependency factory enforcing specified roles."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN_ROLE",
                        "message": (
                            f"Action requires one of {[r.value for r in allowed_roles]} roles. "
                            f"Current role: {current_user.role.value}"
                        ),
                        "details": [],
                    }
                },
            )
        return current_user

    return role_checker

