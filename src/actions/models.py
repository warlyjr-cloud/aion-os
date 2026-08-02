from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ResourceLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cpu_seconds: int = Field(default=30, ge=1, le=300)
    memory_mb: int = Field(default=256, ge=16, le=4096)
    output_bytes: int = Field(default=1_000_000, ge=1, le=100_000_000)


class SemanticAction(BaseModel):
    """A typed request that can be evaluated without executing model text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action_id: str = Field(min_length=8, max_length=128)
    action_type: str = Field(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
    target: str = Field(min_length=1, max_length=512)
    reason: str = Field(min_length=3, max_length=1_000)
    origin: str = Field(min_length=1, max_length=128)
    objective_id: str = Field(min_length=1, max_length=128)
    required_capability: str = Field(min_length=3, max_length=512)
    risk_tier: int = Field(ge=0, le=3)
    inputs: dict[str, Any] = Field(default_factory=dict)
    expected_result: str = Field(min_length=1, max_length=512)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    network_policy: Literal["deny", "allowlisted"] = "deny"
    rollback_action: str = Field(min_length=3, max_length=512)
