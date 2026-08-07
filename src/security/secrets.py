from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

REDACTED = "[REDACTED]"


@dataclass(frozen=True)
class SecretConfig:
    provider_api_key: str | None = None
    fleet_manager_endpoint: str | None = None
    oracle_endpoint: str | None = None
    oracle_api_key: str | None = None

    @classmethod
    def from_environment(cls) -> SecretConfig:
        return cls(
            provider_api_key=os.getenv("AION_PROVIDER_API_KEY"),
            fleet_manager_endpoint=os.getenv("AION_FLEET_MANAGER_ENDPOINT"),
            oracle_endpoint=os.getenv("AION_ORACLE_ENDPOINT"),
            oracle_api_key=os.getenv("AION_ORACLE_API_KEY"),
        )


def load_secret(name: str, *, default: str | None = None, env_var: str | None = None) -> str | None:
    if env_var is not None:
        value = os.getenv(env_var)
    else:
        value = os.getenv(name)
    if value is None:
        return default
    if not value.strip():
        return default
    return value


def redact_sensitive_text(text: str) -> str:
    patterns = [
        r"(?i)(api[_-]?key(?:\s*[:=]\s*)['\"]?)([^'\"\s,;]+)",
        r"(?i)(secret(?:\s*[:=]\s*)['\"]?)([^'\"\s,;]+)",
        r"(?i)(token(?:\s*[:=]\s*)['\"]?)([^'\"\s,;]+)",
        r"(?i)(password(?:\s*[:=]\s*)['\"]?)([^'\"\s,;]+)",
    ]
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, r"\1" + REDACTED, redacted)
    return redacted


def ensure_public_safe_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return redact_sensitive_text(payload)
    if isinstance(payload, dict):
        return {key: ensure_public_safe_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [ensure_public_safe_payload(item) for item in payload]
    return payload
