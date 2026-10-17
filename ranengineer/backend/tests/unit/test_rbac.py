"""Unit tests for RBAC & Authentication module."""
from datetime import timedelta
import pytest
from fastapi import HTTPException

from app.security.auth import (
    DEMO_USERS,
    ROLE_PERMISSIONS,
    UserRole,
    authenticate_user,
    create_access_token,
    decode_access_token,
    require_role,
)


def test_authenticate_user_valid_credentials():
    user = authenticate_user("engineer@telecom.ai", "telecom123!")
    assert user is not None
    assert user.email == "engineer@telecom.ai"
    assert user.role == UserRole.RAN_ENGINEER
    assert "write:oran" in user.permissions
    assert "write:datasets" in user.permissions


def test_authenticate_user_invalid_password():
    user = authenticate_user("engineer@telecom.ai", "wrongpassword")
    assert user is None


def test_authenticate_user_nonexistent():
    user = authenticate_user("unknown@telecom.ai", "telecom123!")
    assert user is None


def test_jwt_token_creation_and_decoding():
    payload = {"sub": "engineer@telecom.ai", "role": "RAN_ENGINEER"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=5))
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded["sub"] == "engineer@telecom.ai"
    assert decoded["role"] == "RAN_ENGINEER"


def test_jwt_expired_token():
    payload = {"sub": "engineer@telecom.ai"}
    token = create_access_token(payload, expires_delta=timedelta(seconds=-10))
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token(token)
    assert excinfo.value.status_code == 401
    assert "TOKEN_EXPIRED" in str(excinfo.value.detail)


def test_jwt_invalid_token():
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token("invalid.token.structure")
    assert excinfo.value.status_code == 401
    assert "INVALID_TOKEN" in str(excinfo.value.detail)


def test_role_permissions_hierarchy():
    viewer_perms = set(ROLE_PERMISSIONS[UserRole.VIEWER])
    engineer_perms = set(ROLE_PERMISSIONS[UserRole.RAN_ENGINEER])
    admin_perms = set(ROLE_PERMISSIONS[UserRole.ADMIN])

    # Engineer superset of Viewer
    assert viewer_perms.issubset(engineer_perms)
    # Admin superset of Engineer
    assert engineer_perms.issubset(admin_perms)
    # Admin has admin-level controls
    assert "admin:system" in admin_perms
    assert "admin:system" not in engineer_perms

