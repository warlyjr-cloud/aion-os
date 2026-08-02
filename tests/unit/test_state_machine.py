import pytest

from tcb import InvalidTransition, MutationState, StateMachine


def test_valid_transition_is_returned() -> None:
    assert (
        StateMachine.transition(MutationState.DRAFT, MutationState.INTENT_VALIDATED)
        is MutationState.INTENT_VALIDATED
    )


def test_invalid_transition_is_rejected() -> None:
    with pytest.raises(InvalidTransition, match="draft -> promoted"):
        StateMachine.transition(MutationState.DRAFT, MutationState.PROMOTED)


def test_terminal_state_has_no_outgoing_transitions() -> None:
    for target in MutationState:
        assert not StateMachine.can_transition(MutationState.ROLLED_BACK, target)
