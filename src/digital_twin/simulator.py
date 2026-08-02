"""A closed-world simulator for the five OS-EvoBench MVP tasks."""

from __future__ import annotations

from collections.abc import Iterable

from digital_twin.models import ActionOutcome, TwinState, TypedAction


class DigitalTwin:
    """Apply allowlisted state transitions without touching the host."""

    def __init__(self, initial_state: TwinState, granted_capabilities: Iterable[str]) -> None:
        self._state = initial_state.copy()
        self._granted_capabilities = frozenset(granted_capabilities)

    @property
    def state(self) -> TwinState:
        return self._state.copy()

    def apply(self, action: TypedAction) -> ActionOutcome:
        if action.required_capability not in self._granted_capabilities:
            return self._reject(action, "required capability was not granted")

        handler = {
            "capability.install": self._install_capability,
            "service.restore": self._restore_service,
            "config.set": self._set_optimization_config,
            "security.set": self._set_security_config,
            "memory.quarantine": self._quarantine_memory,
        }.get(action.action_type)
        if handler is None:
            return self._reject(action, "action type is outside the simulation allowlist")
        return handler(action)

    def apply_all(self, actions: Iterable[TypedAction]) -> tuple[ActionOutcome, ...]:
        return tuple(self.apply(action) for action in actions)

    @staticmethod
    def _reject(action: TypedAction, reason: str) -> ActionOutcome:
        return ActionOutcome(action.action_id, False, reason)

    def _install_capability(self, action: TypedAction) -> ActionOutcome:
        expected = f"package.propose:{action.target}"
        if action.required_capability != expected:
            return self._reject(action, "capability scope does not match package target")
        self._state.capabilities.add(action.target)
        self._state.metrics["install_seconds"] = 5.0
        return ActionOutcome(
            action.action_id,
            True,
            "simulated capability installation",
            {"installed": action.target, "host_mutation": False},
        )

    def _restore_service(self, action: TypedAction) -> ActionOutcome:
        expected = f"service.restore:{action.target}"
        if action.required_capability != expected or action.target not in self._state.services:
            return self._reject(
                action, "service target is absent or capability scope does not match"
            )
        self._state.services[action.target] = "healthy"
        self._state.metrics["recovery_seconds"] = 12.0
        return ActionOutcome(
            action.action_id,
            True,
            "simulated service recovery",
            {"service": action.target, "status": "healthy"},
        )

    def _set_optimization_config(self, action: TypedAction) -> ActionOutcome:
        if (
            action.target != "video.pipeline"
            or action.required_capability != "config.write:video.pipeline"
        ):
            return self._reject(action, "optimization target is outside the task scope")
        preset = action.parameters.get("preset")
        profiles = {
            "balanced": (75.0, 240.0),
            "fast": (60.0, 400.0),
        }
        if not isinstance(preset, str) or preset not in profiles:
            return self._reject(action, "unknown deterministic optimization preset")
        latency_ms, memory_mb = profiles[preset]
        self._state.config["video.pipeline"] = preset
        self._state.metrics["latency_ms"] = latency_ms
        self._state.metrics["memory_mb"] = memory_mb
        return ActionOutcome(
            action.action_id,
            True,
            "simulated optimization profile",
            {"preset": preset},
        )

    def _set_security_config(self, action: TypedAction) -> ActionOutcome:
        allowed = {
            "ssh.password_auth": "config.write:ssh",
            "firewall.enabled": "config.write:firewall",
        }
        if allowed.get(action.target) != action.required_capability:
            return self._reject(action, "security setting is outside the granted scope")
        value = action.parameters.get("value")
        if not isinstance(value, bool):
            return self._reject(action, "security setting must be boolean")
        self._state.config[action.target] = value
        if action.target == "ssh.password_auth" and value is False:
            self._state.metrics["exposure_score"] = max(
                0.0, self._state.metrics.get("exposure_score", 10.0) - 5.0
            )
        if action.target == "firewall.enabled" and value is True:
            self._state.metrics["exposure_score"] = max(
                0.0, self._state.metrics.get("exposure_score", 10.0) - 5.0
            )
        return ActionOutcome(
            action.action_id,
            True,
            "simulated security hardening",
            {"setting": action.target, "value": value},
        )

    def _quarantine_memory(self, action: TypedAction) -> ActionOutcome:
        expected = f"memory.quarantine:{action.target}"
        memory = self._state.memories.get(action.target)
        if action.required_capability != expected or memory is None:
            return self._reject(
                action, "memory target is absent or capability scope does not match"
            )
        memory.status = "quarantined"
        return ActionOutcome(
            action.action_id,
            True,
            "simulated memory quarantine",
            {"memory_id": action.target, "status": memory.status},
        )
