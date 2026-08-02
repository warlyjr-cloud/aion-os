from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from actions import SemanticAction


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action_id: str
    status: str
    simulated: bool
    output: str


class SafeExecutor:
    """MVP executor: validates an allowlist and only simulates host effects."""

    ALLOWLIST = frozenset(
        {
            "package.propose",
            "file.propose",
            "generation.build",
            "benchmark.run",
            "memory.quarantine",
        }
    )

    def execute(self, action: SemanticAction) -> ExecutionResult:
        if action.action_type not in self.ALLOWLIST:
            raise PermissionError(f"action is outside executor allowlist: {action.action_type}")
        return ExecutionResult(
            action_id=action.action_id,
            status="simulated",
            simulated=True,
            output=f"validated simulation for {action.action_type} on {action.target}",
        )
