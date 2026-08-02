from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from intent import IntentContract
from providers import CandidateProposal
from tcb import MutationState, StateMachine


def _candidate_list() -> list[CandidateProposal]:
    return []


class MutationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mutation_id: str
    objective_id: str
    objective: str
    state: MutationState = MutationState.DRAFT
    state_history: list[MutationState] = Field(default_factory=lambda: [MutationState.DRAFT])
    intent: IntentContract
    candidates: list[CandidateProposal] = Field(default_factory=_candidate_list)
    selected_candidate_id: str | None = None
    proof_path: str | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    generation_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    simulated: bool = True

    def transition(self, target: MutationState) -> None:
        self.state = StateMachine.transition(self.state, target)
        self.state_history.append(target)


class MutationStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, record: MutationRecord) -> Path:
        path = self._path(record.mutation_id)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        return path

    def load(self, mutation_id: str) -> MutationRecord:
        path = self._path(mutation_id)
        if not path.is_file():
            raise KeyError(f"unknown mutation: {mutation_id}")
        return MutationRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list_all(self) -> list[MutationRecord]:
        return [
            MutationRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root.glob("mut-*.json"))
        ]

    def _path(self, mutation_id: str) -> Path:
        if not mutation_id.startswith("mut-") or not mutation_id.replace("-", "").isalnum():
            raise ValueError("invalid mutation id")
        return self.root / f"{mutation_id}.json"
