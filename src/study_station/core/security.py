"""Security utilities for kiosk mode and password management."""

from __future__ import annotations
import hashlib
import secrets


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a cryptographically secure random salt.

    Returns:
        Formatted string: '{salt_hex}:{key_hex}' or empty string if password is empty.
    """
    if not password:
        return ""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"{salt}:{key.hex()}"


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify a plain-text password against a stored 'salt:hex' PBKDF2 hash.

    Uses secrets.compare_digest to prevent timing attacks.
    """
    if not stored_hash or not password:
        return False
    try:
        parts = stored_hash.split(":")
        if len(parts) != 2:
            return False
        salt, expected_hex = parts
        check_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return secrets.compare_digest(check_key.hex(), expected_hex)
    except Exception:
        return False
