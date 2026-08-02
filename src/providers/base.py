from __future__ import annotations

import unicodedata
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from intent import IntentContract


class CandidateProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str
    parent_id: str | None = None
    provider: str
    configuration: str
    skill: dict[str, str]
    capabilities: list[str]
    metrics: dict[str, float] = Field(default_factory=dict)
    simulated: bool = True


class Provider(Protocol):
    identity: str

    def propose(self, contract: IntentContract) -> list[CandidateProposal]: ...


class MockProvider:
    identity = "mock-provider/offline-v1"

    def propose(self, contract: IntentContract) -> list[CandidateProposal]:
        normalized_objective = "".join(
            character
            for character in unicodedata.normalize("NFKD", contract.objective.casefold())
            if not unicodedata.combining(character)
        )
        if "video" not in normalized_objective:
            capability = "package.propose:generic-tool"
            package = "generic-tool"
        else:
            capability = "package.propose:ffmpeg"
            package = "ffmpeg"
        return [
            CandidateProposal(
                candidate_id=f"{contract.objective_id}-balanced",
                provider=self.identity,
                configuration=f"environment.systemPackages = [ pkgs.{package} ];",
                skill={"name": f"use-{package}", "mode": "balanced", "shell": "disabled"},
                capabilities=[capability],
                metrics={"success": 0.93, "security": 0.99, "cost": 0.20, "novelty": 0.35},
            ),
            CandidateProposal(
                candidate_id=f"{contract.objective_id}-minimal",
                provider=self.identity,
                configuration=f"users.users.aion.packages = [ pkgs.{package} ];",
                skill={"name": f"use-{package}", "mode": "minimal", "shell": "disabled"},
                capabilities=[capability],
                metrics={"success": 0.88, "security": 0.995, "cost": 0.10, "novelty": 0.55},
            ),
        ]
