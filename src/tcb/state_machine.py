from __future__ import annotations

from enum import StrEnum


class MutationState(StrEnum):
    DRAFT = "draft"
    INTENT_VALIDATED = "intent_validated"
    PLANNED = "planned"
    CANDIDATES_GENERATED = "candidates_generated"
    POLICY_CHECKED = "policy_checked"
    BUILDING = "building"
    BUILD_FAILED = "build_failed"
    TESTING = "testing"
    TEST_FAILED = "test_failed"
    ADVERSARIAL_TESTING = "adversarial_testing"
    EVALUATED = "evaluated"
    ARCHIVED = "archived"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROMOTING = "promoting"
    PROMOTED = "promoted"
    MONITORING = "monitoring"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class InvalidTransition(ValueError):
    pass


_TRANSITIONS: dict[MutationState, frozenset[MutationState]] = {
    MutationState.DRAFT: frozenset({MutationState.INTENT_VALIDATED, MutationState.FAILED}),
    MutationState.INTENT_VALIDATED: frozenset({MutationState.PLANNED, MutationState.FAILED}),
    MutationState.PLANNED: frozenset({MutationState.CANDIDATES_GENERATED, MutationState.FAILED}),
    MutationState.CANDIDATES_GENERATED: frozenset(
        {MutationState.POLICY_CHECKED, MutationState.ARCHIVED, MutationState.FAILED}
    ),
    MutationState.POLICY_CHECKED: frozenset(
        {MutationState.BUILDING, MutationState.ARCHIVED, MutationState.FAILED}
    ),
    MutationState.BUILDING: frozenset({MutationState.TESTING, MutationState.BUILD_FAILED}),
    MutationState.BUILD_FAILED: frozenset({MutationState.ARCHIVED, MutationState.FAILED}),
    MutationState.TESTING: frozenset(
        {MutationState.ADVERSARIAL_TESTING, MutationState.TEST_FAILED}
    ),
    MutationState.TEST_FAILED: frozenset({MutationState.ARCHIVED, MutationState.FAILED}),
    MutationState.ADVERSARIAL_TESTING: frozenset(
        {MutationState.EVALUATED, MutationState.ARCHIVED, MutationState.FAILED}
    ),
    MutationState.EVALUATED: frozenset(
        {MutationState.AWAITING_APPROVAL, MutationState.ARCHIVED, MutationState.REJECTED}
    ),
    MutationState.AWAITING_APPROVAL: frozenset(
        {MutationState.APPROVED, MutationState.REJECTED, MutationState.ARCHIVED}
    ),
    MutationState.APPROVED: frozenset({MutationState.PROMOTING, MutationState.ARCHIVED}),
    MutationState.PROMOTING: frozenset({MutationState.PROMOTED, MutationState.FAILED}),
    MutationState.PROMOTED: frozenset({MutationState.MONITORING, MutationState.ROLLED_BACK}),
    MutationState.MONITORING: frozenset({MutationState.ROLLED_BACK, MutationState.FAILED}),
    MutationState.ARCHIVED: frozenset(),
    MutationState.REJECTED: frozenset(),
    MutationState.ROLLED_BACK: frozenset(),
    MutationState.FAILED: frozenset(),
}


class StateMachine:
    @staticmethod
    def can_transition(current: MutationState, target: MutationState) -> bool:
        return target in _TRANSITIONS[current]

    @staticmethod
    def transition(current: MutationState, target: MutationState) -> MutationState:
        if not StateMachine.can_transition(current, target):
            raise InvalidTransition(f"invalid transition: {current.value} -> {target.value}")
        return target
