from datetime import UTC, datetime, timedelta

import pytest

from actions import SemanticAction
from capabilities import CapabilityGrant, CapabilityManager
from executor import SafeExecutor
from policy import PolicyDecision, PolicyEngine
from tcb import ActionValidator


def action(**overrides: object) -> SemanticAction:
    values: dict[str, object] = {
        "action_id": "action-0001",
        "action_type": "package.propose",
        "target": "ffmpeg",
        "reason": "validated capability gap",
        "origin": "mock",
        "objective_id": "obj-1",
        "required_capability": "package.propose:ffmpeg",
        "risk_tier": 1,
        "expected_result": "proposal",
        "rollback_action": "generation.restore_parent",
    }
    values.update(overrides)
    return SemanticAction.model_validate(values)


def manager() -> CapabilityManager:
    return CapabilityManager(
        [
            CapabilityGrant(
                grant_id="grant-1",
                capability="package.propose:ffmpeg",
                grantee="mock",
                objective_id="obj-1",
                expires_at=datetime.now(UTC) + timedelta(minutes=1),
            )
        ]
    )


def test_valid_capability_allows_typed_action() -> None:
    result = PolicyEngine(ActionValidator(manager())).evaluate(action(), actor="mock")
    assert result.decision is PolicyDecision.ALLOW


def test_missing_capability_is_denied() -> None:
    result = PolicyEngine(ActionValidator(CapabilityManager())).evaluate(action(), actor="mock")
    assert result.decision is PolicyDecision.DENY


def test_protected_tcb_target_is_denied_before_execution() -> None:
    result = PolicyEngine(ActionValidator(manager())).evaluate(
        action(action_type="file.propose", target="src/tcb/validator.py"), actor="mock"
    )
    assert result.decision is PolicyDecision.DENY
    assert "protected" in result.reason


@pytest.mark.parametrize("target", ["C:\\Windows\\System32", "/etc/shadow", "../outside"])
def test_targets_outside_project_are_denied(target: str) -> None:
    result = PolicyEngine(ActionValidator(manager())).evaluate(
        action(action_type="file.propose", target=target), actor="mock"
    )
    assert result.decision is PolicyDecision.DENY


def test_free_shell_and_root_are_denied() -> None:
    result = PolicyEngine(ActionValidator(manager())).evaluate(
        action(
            action_type="shell.execute", target="host", required_capability="shell.execute:root"
        ),
        actor="mock",
    )
    assert result.decision is PolicyDecision.DENY


def test_network_action_requires_more_isolation() -> None:
    result = PolicyEngine(ActionValidator(manager())).evaluate(
        action(network_policy="allowlisted"), actor="mock"
    )
    assert result.decision is PolicyDecision.REQUIRE_ISOLATION


def test_emergency_stop_fails_closed() -> None:
    validator = ActionValidator(manager())
    validator.emergency_stop()
    result = PolicyEngine(validator).evaluate(action(), actor="mock")
    assert result.decision is PolicyDecision.DENY


def test_executor_never_accepts_free_shell() -> None:
    with pytest.raises(PermissionError, match="allowlist"):
        SafeExecutor().execute(action(action_type="shell.execute"))
