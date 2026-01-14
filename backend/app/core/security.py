"""
Security utilities for the MyAshes.ai backend.

Phase 1: Minimal session-based security.
Phase 2 (future): OAuth integration with Discord.
"""
import secrets
import hashlib
from typing import Optional


def generate_session_id() -> str:
    """
    Generate a secure random session ID.

    Returns a 64-character hex string.
    """
    return secrets.token_hex(32)


def generate_build_id() -> str:
    """
    Generate a short, URL-friendly build ID.

    Format: b_XXXXXXX (12 characters total)
    """
    random_part = secrets.token_hex(4)  # 8 hex chars
    return f"b_{random_part}"


def generate_feedback_id() -> str:
    """
    Generate a short feedback ID.

    Format: f_XXXXXXX (12 characters total)
    """
    random_part = secrets.token_hex(4)
    return f"f_{random_part}"


def hash_session_for_storage(session_id: str) -> str:
    """
    Hash a session ID for secure storage/comparison.

    Uses SHA-256 for fast, secure hashing.
    """
    return hashlib.sha256(session_id.encode()).hexdigest()
