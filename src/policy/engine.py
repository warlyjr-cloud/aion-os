from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from actions import SemanticAction
from tcb import ActionValidator, ValidationOutcome


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_CLARIFICATION = "require_clarification"
    REQUIRE_ISOLATION = "require_isolation"


class PolicyResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: PolicyDecision
    reason: str


_OUTCOME_MAP = {
    ValidationOutcome.PERMITTED: PolicyDecision.ALLOW,
    ValidationOutcome.DENIED: PolicyDecision.DENY,
    ValidationOutcome.REQUIRES_APPROVAL: PolicyDecision.REQUIRE_APPROVAL,
    ValidationOutcome.REQUIRES_CLARIFICATION: PolicyDecision.REQUIRE_CLARIFICATION,
    ValidationOutcome.REQUIRES_ISOLATION: PolicyDecision.REQUIRE_ISOLATION,
}


class PolicyEngine:
    def __init__(self, validator: ActionValidator) -> None:
        self._validator = validator

    def evaluate(self, action: SemanticAction, *, actor: str) -> PolicyResult:
        validation = self._validator.validate(action, grantee=actor)
        return PolicyResult(decision=_OUTCOME_MAP[validation.outcome], reason=validation.reason)
