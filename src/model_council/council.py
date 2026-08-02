from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CouncilDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    approved: bool
    proposer: str
    verifier: str
    reason: str


class ModelCouncil:
    @staticmethod
    def evaluate(
        *, proposer: str, verifier: str, critical: bool, accepted: bool
    ) -> CouncilDecision:
        if critical and proposer == verifier:
            return CouncilDecision(
                approved=False,
                proposer=proposer,
                verifier=verifier,
                reason="critical changes require an independent verifier",
            )
        return CouncilDecision(
            approved=accepted,
            proposer=proposer,
            verifier=verifier,
            reason="independent evaluation recorded" if accepted else "verifier rejected candidate",
        )
