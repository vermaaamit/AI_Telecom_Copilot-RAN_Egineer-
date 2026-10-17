"""Authentication and RBAC API routes."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.security.auth import (
    DEMO_USERS,
    LoginRequest,
    ROLE_PERMISSIONS,
    TokenResponse,
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
)

from app.security.auditor import get_security_auditor
from app.security.counters import get_security_counter_store

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """Authenticate with email and password to receive a Bearer JWT token."""
    counters = get_security_counter_store()
    auditor = get_security_auditor()

    if counters.is_user_locked(credentials.email):
        auditor.record_event(
            event_type="LOGIN_LOCKED_ATTEMPT",
            severity="WARNING",
            actor=credentials.email,
            description="Attempt to log into temporarily locked account due to brute-force threshold.",
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={"error": {"code": "ACCOUNT_LOCKED", "message": "Account temporarily locked due to excessive failed attempts. Please retry later.", "details": []}},
        )

    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        attempts = counters.record_failed_login(credentials.email)
        auditor.record_event(
            event_type="LOGIN_FAILED",
            severity="WARNING" if attempts >= 5 else "INFO",
            actor=credentials.email,
            description=f"Failed authentication attempt (attempt #{attempts}).",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password.", "details": []}},
        )

    # Successful login: reset counter
    counters.reset_failed_login(credentials.email)
    auditor.record_event(
        event_type="LOGIN_SUCCESS",
        severity="INFO",
        actor=user.email,
        description=f"User '{user.username}' logged in successfully with role '{user.role.value}'.",
    )

    token = create_access_token(
        {
            "sub": user.email,
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "full_name": user.full_name,
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=8 * 3600,
        user=user,
    )


@router.get("/me", response_model=User)
async def get_current_user_profile(user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user profile and permissions."""
    return user


@router.get("/users", response_model=List[User])
async def list_available_users():
    """List available demo users for NOC role selection and testing."""
    users = []
    for rec in DEMO_USERS.values():
        role = rec["role"]
        users.append(
            User(
                id=rec["id"],
                username=rec["username"],
                email=rec["email"],
                full_name=rec["full_name"],
                role=role,
                is_active=rec["is_active"],
                permissions=ROLE_PERMISSIONS.get(role, []),
            )
        )
    return users

