"""Authentication service.

Provides secure password hashing via bcrypt, JWT token creation/verification,
and user CRUD operations.
"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
import jwt

from db.models import User

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "flux-tracker-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with a salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: int, email: str) -> str:
    """Create a signed JWT token valid for ACCESS_TOKEN_EXPIRE_DAYS."""
    expires = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expires,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        password_hash=row["password_hash"],
        name=row["name"] if "name" in row.keys() else None,
        created_at=row["created_at"] if "created_at" in row.keys() else None,
    )


def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[User]:
    """Look up a user by email (case-insensitive)."""
    norm_email = email.strip().lower()
    row = conn.execute("SELECT * FROM user WHERE email = ? COLLATE NOCASE", (norm_email,)).fetchone()
    return _row_to_user(row) if row else None


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[User]:
    """Look up a user by id."""
    row = conn.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row) if row else None


def create_user(
    conn: sqlite3.Connection,
    email: str,
    password: str,
    name: Optional[str] = None,
) -> User:
    """Create a new user.

    If this is the first user registered in the system, adopt any unassigned
    existing data rows (from pre-auth single-user state) so the primary owner's
    data is seamlessly preserved.
    """
    norm_email = email.strip().lower()
    if not norm_email or not EMAIL_REGEX.match(norm_email):
        raise ValueError("A valid email address is required")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")

    existing = get_user_by_email(conn, norm_email)
    if existing:
        raise ValueError("An account with this email already exists")

    user_count_row = conn.execute("SELECT COUNT(*) FROM user").fetchone()
    is_first_user = (user_count_row[0] == 0) if user_count_row else False

    pw_hash = hash_password(password)
    clean_name = name.strip() if name and name.strip() else None

    cur = conn.execute(
        "INSERT INTO user (email, password_hash, name) VALUES (?, ?, ?)",
        (norm_email, pw_hash, clean_name),
    )
    user_id = cur.lastrowid

    # If first user, link existing data that has user_id = 1 or NULL
    if is_first_user:
        for tbl in ["task", "goal", "learning_item", "recurring_task", "learning_session", "daily_update", "review"]:
            try:
                conn.execute(f"UPDATE {tbl} SET user_id = ? WHERE user_id IS NULL OR user_id = 1", (user_id,))
            except sqlite3.OperationalError:
                pass

    conn.commit()
    user = get_user_by_id(conn, user_id)
    if not user:
        raise RuntimeError("Failed to retrieve created user")
    return user


def authenticate_user(
    conn: sqlite3.Connection,
    email: str,
    password: str,
) -> Optional[User]:
    """Authenticate email and password. Returns User if valid, else None."""
    user = get_user_by_email(conn, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
