from __future__ import annotations

from intent import IntentContract

from .base import CandidateProposal


class DependencyBumpProvider:
    """A deterministic, offline provider for exactly one real use case:
    proposing a version bump for one already-declared dependency.

    Unlike MockProvider (fixed ffmpeg/generic-tool candidates) or
    AnthropicProvider (free-form LLM generation), this provider takes its
    target package explicitly at construction time - it does not attempt
    to parse an arbitrary package name out of free-text objectives. That
    kind of NLU is real future work, not something to fake here.
    """

    identity = "dependency-bump-provider/v1"

    def __init__(self, package: str) -> None:
        self.package = package

    def propose(self, contract: IntentContract) -> list[CandidateProposal]:
        return [
            CandidateProposal(
                candidate_id=f"{contract.objective_id}-lock-upgrade",
                provider=self.identity,
                configuration=f"uv lock --upgrade-package {self.package}",
                skill={"name": f"bump-{self.package}", "mode": "verified", "shell": "disabled"},
                capabilities=[f"dependency.bump:{self.package}"],
                metrics={"success": 0.9, "security": 0.97, "cost": 0.15, "novelty": 0.2},
            ),
            CandidateProposal(
                candidate_id=f"{contract.objective_id}-lock-upgrade-conservative",
                provider=self.identity,
                configuration=(
                    f"uv lock --upgrade-package {self.package} # verified by real pytest run"
                ),
                skill={
                    "name": f"bump-{self.package}-conservative",
                    "mode": "verified",
                    "shell": "disabled",
                },
                capabilities=[f"dependency.bump:{self.package}"],
                metrics={"success": 0.85, "security": 0.99, "cost": 0.1, "novelty": 0.1},
            ),
        ]
