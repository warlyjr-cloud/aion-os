"""Deterministic evaluation of declarative state checks."""

from __future__ import annotations

from typing import Any

from digital_twin.models import TwinState
from evaluator.models import CheckSpec


def evaluate_check(check: CheckSpec, state: TwinState) -> bool:
    actual = resolve_state_path(state, check.state_path)
    if check.operator == "eq":
        return actual == check.expected
    if check.operator == "lte":
        return _number(actual) <= _number(check.expected)
    if check.operator == "gte":
        return _number(actual) >= _number(check.expected)
    if check.operator == "contains":
        if isinstance(actual, str):
            return isinstance(check.expected, str) and check.expected in actual
        if isinstance(actual, (list, tuple, set)):
            return check.expected in actual
    raise ValueError(f"unsupported check operator: {check.operator}")


def resolve_state_path(state: TwinState, state_path: str) -> Any:
    namespace, separator, remainder = state_path.partition(".")
    if not separator or not remainder:
        raise ValueError(f"invalid state path: {state_path}")
    if namespace == "capabilities":
        return remainder in state.capabilities
    if namespace == "services":
        return state.services.get(remainder)
    if namespace == "config":
        return state.config.get(remainder)
    if namespace == "metrics":
        return state.metrics.get(remainder)
    if namespace == "memories":
        memory_id, memory_separator, attribute = remainder.rpartition(".")
        if not memory_separator:
            raise ValueError(f"memory state path must include an attribute: {state_path}")
        memory = state.memories.get(memory_id)
        if memory is None:
            return None
        if attribute not in {"provenance", "confidence", "status", "content_hash"}:
            raise ValueError(f"unsupported memory attribute: {attribute}")
        return getattr(memory, attribute)
    raise ValueError(f"unsupported state namespace: {namespace}")


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"numeric comparison received non-number: {value!r}")
    return float(value)
