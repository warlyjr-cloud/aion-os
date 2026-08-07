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


def _durable_grant(**overrides: object) -> CapabilityGrant:
    values: dict[str, object] = {
        "grant_id": "grant-durable-1",
        "capability": "package.propose:ffmpeg",
        "grantee": "team-video",
        "objective_id": "obj-1",
        "expires_at": datetime.now(UTC) + timedelta(minutes=5),
        "remaining_uses": 2,
    }
    values.update(overrides)
    return CapabilityGrant.model_validate(values)


def test_capability_store_persists_and_authorizes_across_instances(tmp_path) -> None:
    from capabilities import CapabilityStore

    store_path = tmp_path / "capabilities.json"
    CapabilityStore(store_path).issue(_durable_grant())

    # A fresh instance (simulating a different process/request) must see it.
    reloaded = CapabilityStore(store_path)
    granted = reloaded.authorize(action(), grantee="team-video")
    assert granted.grant_id == "grant-durable-1"


def test_capability_store_enforces_real_expiration(tmp_path) -> None:
    from capabilities import CapabilityError, CapabilityStore

    store_path = tmp_path / "capabilities.json"
    store = CapabilityStore(store_path)
    store.issue(_durable_grant(expires_at=datetime.now(UTC) - timedelta(seconds=1)))

    with pytest.raises(CapabilityError):
        store.authorize(action(), grantee="team-video")


def test_capability_store_enforces_remaining_uses(tmp_path) -> None:
    from capabilities import CapabilityError, CapabilityStore

    store_path = tmp_path / "capabilities.json"
    store = CapabilityStore(store_path)
    store.issue(_durable_grant(remaining_uses=1))

    store.authorize(action(), grantee="team-video")
    with pytest.raises(CapabilityError):
        store.authorize(action(), grantee="team-video")


def test_capability_store_revocation_blocks_future_authorization(tmp_path) -> None:
    from capabilities import CapabilityError, CapabilityStore

    store_path = tmp_path / "capabilities.json"
    store = CapabilityStore(store_path)
    store.issue(_durable_grant())

    store.authorize(action(), grantee="team-video")
    store.revoke("grant-durable-1", revoked_by="security-team", reason="incident response")

    with pytest.raises(CapabilityError):
        store.authorize(action(), grantee="team-video")

    assert store.list_active() == []
