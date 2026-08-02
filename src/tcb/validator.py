from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath

from pydantic import BaseModel, ConfigDict

from actions import SemanticAction
from capabilities import CapabilityError, CapabilityManager


class ValidationOutcome(StrEnum):
    PERMITTED = "permitted"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_CLARIFICATION = "requires_clarification"
    REQUIRES_ISOLATION = "requires_isolation"


class ActionValidation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: ValidationOutcome
    reason: str


class ActionValidator:
    PROTECTED_PREFIXES = (
        "docs/SAFETY_CONSTITUTION.md",
        "docs/TCB_SPECIFICATION.md",
        "src/tcb",
        "policies",
        ".github/workflows",
        "benchmarks/os_evobench/reserved",
    )
    FORBIDDEN_ACTIONS = frozenset(
        {
            "shell.execute",
            "privilege.escalate",
            "audit.disable",
            "sandbox.disable",
            "rollback.disable",
            "benchmark.modify_reserved",
            "network.exfiltrate",
            "agent.self_replicate",
        }
    )

    def __init__(self, capability_manager: CapabilityManager) -> None:
        self._capabilities = capability_manager
        self._emergency_stopped = False

    def emergency_stop(self) -> None:
        self._emergency_stopped = True

    def validate(self, action: SemanticAction, *, grantee: str) -> ActionValidation:
        if self._emergency_stopped:
            return ActionValidation(
                outcome=ValidationOutcome.DENIED, reason="emergency stop active"
            )
        if action.action_type in self.FORBIDDEN_ACTIONS:
            return ActionValidation(outcome=ValidationOutcome.DENIED, reason="action is forbidden")
        normalized_target = str(PurePosixPath(action.target.replace("\\", "/")))
        if (
            PurePosixPath(normalized_target).is_absolute()
            or PureWindowsPath(action.target).is_absolute()
        ):
            return ActionValidation(
                outcome=ValidationOutcome.DENIED,
                reason="absolute host targets are forbidden",
            )
        if normalized_target == ".." or normalized_target.startswith("../"):
            return ActionValidation(
                outcome=ValidationOutcome.DENIED, reason="target escapes project"
            )
        if any(
            normalized_target == prefix or normalized_target.startswith(f"{prefix}/")
            for prefix in self.PROTECTED_PREFIXES
        ):
            return ActionValidation(outcome=ValidationOutcome.DENIED, reason="protected target")
        if action.network_policy != "deny":
            return ActionValidation(
                outcome=ValidationOutcome.REQUIRES_ISOLATION,
                reason="network access requires isolated allowlist enforcement",
            )
        try:
            self._capabilities.authorize(action, grantee=grantee)
        except CapabilityError as exc:
            return ActionValidation(outcome=ValidationOutcome.DENIED, reason=str(exc))
        if action.risk_tier >= 2:
            return ActionValidation(
                outcome=ValidationOutcome.REQUIRES_APPROVAL,
                reason="risk tier requires independent human approval",
            )
        return ActionValidation(
            outcome=ValidationOutcome.PERMITTED, reason="policy and capability valid"
        )
