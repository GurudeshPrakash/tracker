"""Tests for authentication service."""

import pytest
from services import auth as auth_svc


def test_hash_and_verify_password():
    password = "supersecret123"
    hashed = auth_svc.hash_password(password)
    assert hashed != password
    assert auth_svc.verify_password(password, hashed) is True
    assert auth_svc.verify_password("wrongpassword", hashed) is False


def test_jwt_token_roundtrip():
    token = auth_svc.create_access_token(user_id=42, email="user@example.com")
    payload = auth_svc.decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["email"] == "user@example.com"


def test_jwt_invalid_token():
    assert auth_svc.decode_access_token("invalid.token.here") is None


def test_create_and_authenticate_user(db_conn):
    user = auth_svc.create_user(
        db_conn,
        email="test@example.com",
        password="password123",
        name="Test User",
    )
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"

    # Authenticate valid
    auth_user = auth_svc.authenticate_user(db_conn, "test@example.com", "password123")
    assert auth_user is not None
    assert auth_user.id == user.id

    # Authenticate invalid password
    assert auth_svc.authenticate_user(db_conn, "test@example.com", "wrong") is None

    # Authenticate invalid email
    assert auth_svc.authenticate_user(db_conn, "nobody@example.com", "password123") is None


def test_duplicate_email_rejected(db_conn):
    auth_svc.create_user(db_conn, email="dup@example.com", password="password123")
    with pytest.raises(ValueError, match="already exists"):
        auth_svc.create_user(db_conn, email="dup@example.com", password="password456")


def test_short_password_rejected(db_conn):
    with pytest.raises(ValueError, match="at least 6 characters"):
        auth_svc.create_user(db_conn, email="short@example.com", password="123")


def test_invalid_email_rejected(db_conn):
    with pytest.raises(ValueError, match="valid email"):
        auth_svc.create_user(db_conn, email="invalid-email", password="password123")
