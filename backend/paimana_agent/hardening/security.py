"""Production Security, Input Sanitization, and Redaction Subsystem.

Defines defenses against prompt injection, path traversal, and SQL injection,
alongside log field redaction and HMAC-SHA256 cryptographic signature verification.
"""
from __future__ import annotations
import hashlib
import hmac
import html
import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger("paimana_agent.hardening.security")


class SecuritySanitizer:
    """Sanitizes external user inputs to prevent injection and traversal attacks."""

    _PROMPT_INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
        re.compile(r"disregard\s+(the\s+)?system\s+prompt", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
        re.compile(r"override\s+governance\s+policy", re.IGNORECASE),
        re.compile(r"bypass\s+approval", re.IGNORECASE),
    ]

    _PATH_TRAVERSAL_PATTERN = re.compile(r"(\.\./|\.\.\\|/etc/|/root/|[a-zA-Z]:\\windows)", re.IGNORECASE)

    @classmethod
    def sanitize_text(cls, text: Optional[str], max_length: int = 500) -> str:
        """Cleans strings, escapes HTML, strips control characters, and blocks prompt injection."""
        if text is None:
            return ""
        s = str(text).strip()
        # Truncate
        if len(s) > max_length:
            s = s[:max_length]
        # Remove control characters (except space/tab)
        s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
        # Escape HTML entities
        s = html.escape(s)
        # Check and neutralize prompt injection attempts
        for pattern in cls._PROMPT_INJECTION_PATTERNS:
            if pattern.search(s):
                logger.warning(f"Detected and neutralized prompt injection pattern in input: '{s[:40]}...'")
                s = pattern.sub("[POTENTIAL_INJECTION_FILTERED]", s)
        return s

    @classmethod
    def validate_project_code(cls, code: str) -> str:
        """Validates that project code matches safe pattern (alphanumeric, -, _, .)."""
        if not code or not isinstance(code, str):
            raise ValueError("project_code must be a non-empty string.")
        s = code.strip()
        if cls._PATH_TRAVERSAL_PATTERN.search(s):
            raise ValueError(f"Illegal path traversal characters in project_code: {code}")
        if not re.match(r"^[A-Za-z0-9_.-]+$", s):
            raise ValueError(f"Invalid characters in project_code: '{code}'. Allowed: letters, numbers, '-', '_', '.'")
        return s


class SecurityRedactor:
    """Redacts sensitive information (passwords, tokens, API keys) from logs and outputs."""

    @classmethod
    def redact(cls, text: str) -> str:
        """Redacts sensitive tokens in text."""
        if not text:
            return ""
        result = text
        # Key-value sensitive pairs
        result = re.sub(
            r"(api[_-]?key|secret|password|token|bearer)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?",
            r"\1: [REDACTED]",
            result,
            flags=re.IGNORECASE
        )
        # Standalone secret tokens (sk-..., ey...)
        result = re.sub(r"sk-[A-Za-z0-9]{20,}", "[REDACTED]", result, flags=re.IGNORECASE)
        result = re.sub(r"ey[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}", "[REDACTED]", result, flags=re.IGNORECASE)
        return result


class GovernanceSignatureManager:
    """Cryptographic HMAC-SHA256 signature generator and validator for governance approval records."""

    @staticmethod
    def sign_payload(payload_bytes: bytes, secret_key: str) -> str:
        h = hmac.new(secret_key.encode("utf-8"), payload_bytes, hashlib.sha256)
        return h.hexdigest()

    @classmethod
    def verify_signature(cls, payload_bytes: bytes, signature: str, secret_key: str) -> bool:
        expected = cls.sign_payload(payload_bytes, secret_key)
        return hmac.compare_digest(expected, signature)
