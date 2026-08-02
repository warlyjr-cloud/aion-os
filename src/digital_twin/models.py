"""Small value models shared by the offline evaluator and red team."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

JsonValue = object


def _empty_json_dict() -> dict[str, JsonValue]:
    return {}


def _empty_string_set() -> set[str]:
    return set()


def _empty_string_dict() -> dict[str, str]:
    return {}


def _empty_float_dict() -> dict[str, float]:
    return {}


def _empty_memory_dict() -> dict[str, MemoryRecord]:
    return {}


def _as_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    return float(value)


@dataclass(frozen=True, slots=True)
class TypedAction:
    """A declarative action; it is data and is never executed as host shell."""

    action_id: str
    action_type: str
    target: str
    required_capability: str
    parameters: dict[str, JsonValue] = field(default_factory=_empty_json_dict)
    timeout_seconds: int = 30
    reversible: bool = True

    def __post_init__(self) -> None:
        if not self.action_id.strip():
            raise ValueError("action_id must not be empty")
        if not self.action_type.strip():
            raise ValueError("action_type must not be empty")
        if not self.target.strip():
            raise ValueError("target must not be empty")
        if not self.required_capability.strip():
            raise ValueError("required_capability must not be empty")
        if not 1 <= self.timeout_seconds <= 300:
            raise ValueError("timeout_seconds must be between 1 and 300")

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> TypedAction:
        raw_parameters = value.get("parameters", {})
        if not isinstance(raw_parameters, dict):
            raise ValueError("action parameters must be an object")
        parameters = cast(dict[object, object], raw_parameters)
        return cls(
            action_id=str(value["action_id"]),
            action_type=str(value["action_type"]),
            target=str(value["target"]),
            required_capability=str(value["required_capability"]),
            parameters={str(key): item for key, item in parameters.items()},
            timeout_seconds=int(_as_float(value.get("timeout_seconds", 30), "timeout_seconds")),
            reversible=bool(value.get("reversible", True)),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "target": self.target,
            "required_capability": self.required_capability,
            "parameters": dict(self.parameters),
            "timeout_seconds": self.timeout_seconds,
            "reversible": self.reversible,
        }


@dataclass(slots=True)
class MemoryRecord:
    memory_id: str
    provenance: str
    confidence: float
    status: str = "active"
    content_hash: str = ""

    @classmethod
    def from_dict(cls, memory_id: str, value: Mapping[str, object]) -> MemoryRecord:
        return cls(
            memory_id=memory_id,
            provenance=str(value.get("provenance", "unknown")),
            confidence=_as_float(value.get("confidence", 0.0), "memory.confidence"),
            status=str(value.get("status", "active")),
            content_hash=str(value.get("content_hash", "")),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "provenance": self.provenance,
            "confidence": self.confidence,
            "status": self.status,
            "content_hash": self.content_hash,
        }


@dataclass(slots=True)
class TwinState:
    """State owned by a simulation; callers receive copies in reports."""

    capabilities: set[str] = field(default_factory=_empty_string_set)
    services: dict[str, str] = field(default_factory=_empty_string_dict)
    config: dict[str, JsonValue] = field(default_factory=_empty_json_dict)
    metrics: dict[str, float] = field(default_factory=_empty_float_dict)
    memories: dict[str, MemoryRecord] = field(default_factory=_empty_memory_dict)

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> TwinState:
        raw_capabilities = value.get("capabilities", [])
        raw_services = value.get("services", {})
        raw_config = value.get("config", {})
        raw_metrics = value.get("metrics", {})
        raw_memories = value.get("memories", {})
        if not isinstance(raw_capabilities, list):
            raise ValueError("initial_state.capabilities must be an array")
        if not isinstance(raw_services, dict):
            raise ValueError("initial_state.services must be an object")
        if not isinstance(raw_config, dict):
            raise ValueError("initial_state.config must be an object")
        if not isinstance(raw_metrics, dict):
            raise ValueError("initial_state.metrics must be an object")
        if not isinstance(raw_memories, dict):
            raise ValueError("initial_state.memories must be an object")
        capabilities = cast(list[object], raw_capabilities)
        services = cast(dict[object, object], raw_services)
        config = cast(dict[object, object], raw_config)
        metrics = cast(dict[object, object], raw_metrics)
        memory_values = cast(dict[object, object], raw_memories)
        memories: dict[str, MemoryRecord] = {}
        for key, item in memory_values.items():
            if not isinstance(item, dict):
                raise ValueError("each initial memory must be an object")
            memories[str(key)] = MemoryRecord.from_dict(str(key), cast(dict[str, object], item))
        return cls(
            capabilities={str(item) for item in capabilities},
            services={str(key): str(item) for key, item in services.items()},
            config={str(key): item for key, item in config.items()},
            metrics={
                str(key): _as_float(item, f"initial_state.metrics.{key}")
                for key, item in metrics.items()
            },
            memories=memories,
        )

    def copy(self) -> TwinState:
        return TwinState.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "capabilities": sorted(self.capabilities),
            "services": dict(sorted(self.services.items())),
            "config": dict(sorted(self.config.items())),
            "metrics": dict(sorted(self.metrics.items())),
            "memories": {key: memory.to_dict() for key, memory in sorted(self.memories.items())},
        }


@dataclass(frozen=True, slots=True)
class ActionOutcome:
    action_id: str
    accepted: bool
    reason: str
    evidence: dict[str, JsonValue] = field(default_factory=_empty_json_dict)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "action_id": self.action_id,
            "accepted": self.accepted,
            "reason": self.reason,
            "evidence": dict(self.evidence),
        }
