from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from actions import SemanticAction
from capabilities import CapabilityGrant, CapabilityManager
from immune_memory import MemoryClass, MemoryEntry, MemoryTrust
from tcb import InvalidTransition, MutationState, StateMachine


@given(st.sampled_from(list(MutationState)))
def test_rolled_back_generation_is_terminal(target: MutationState) -> None:
    with pytest.raises(InvalidTransition):
        StateMachine.transition(MutationState.ROLLED_BACK, target)


@given(st.text(min_size=3, max_size=40).filter(lambda value: value != "package.propose:ffmpeg"))
def test_wrong_capability_never_authorizes(capability: str) -> None:
    manager = CapabilityManager(
        [
            CapabilityGrant(
                grant_id="grant-1",
                capability=capability,
                grantee="agent",
                objective_id="obj-1",
                expires_at=datetime.now(UTC) + timedelta(minutes=1),
            )
        ]
    )
    action = SemanticAction(
        action_id="action-0001",
        action_type="package.propose",
        target="ffmpeg",
        reason="validated capability gap",
        origin="agent",
        objective_id="obj-1",
        required_capability="package.propose:ffmpeg",
        risk_tier=1,
        expected_result="proposal",
        rollback_action="generation.restore_parent",
    )
    with pytest.raises(PermissionError):
        manager.authorize(action, grantee="agent")


@given(st.text(min_size=1, max_size=100))
def test_untrusted_memory_has_no_automatic_authority(content: str) -> None:
    memory = MemoryEntry(
        memory_id="mem-1",
        origin="external",
        provenance=["fixture"],
        memory_class=MemoryClass.EXTERNAL_CONTENT,
        trust=MemoryTrust.UNTRUSTED,
        content=content,
        context="test",
        scope="objective",
        reversal="delete",
    )
    assert not memory.action_authority
