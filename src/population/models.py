from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from providers import CandidateProposal


class EvolutionPopulation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective_id: str
    candidates: list[CandidateProposal] = Field(min_length=2)


class CandidateArchive:
    def __init__(self) -> None:
        self._items: dict[str, CandidateProposal] = {}

    def add(self, candidate: CandidateProposal) -> None:
        self._items[candidate.candidate_id] = candidate

    def get(self, candidate_id: str) -> CandidateProposal:
        return self._items[candidate_id]

    def list(self) -> list[CandidateProposal]:
        return list(self._items.values())


class LineageGraph:
    def __init__(self) -> None:
        self._parents: dict[str, str | None] = {}

    def add(self, candidate: CandidateProposal) -> None:
        if candidate.parent_id == candidate.candidate_id:
            raise ValueError("candidate cannot be its own parent")
        self._parents[candidate.candidate_id] = candidate.parent_id

    def ancestors(self, candidate_id: str) -> list[str]:
        result: list[str] = []
        seen = {candidate_id}
        current = self._parents.get(candidate_id)
        while current is not None:
            if current in seen:
                raise ValueError("lineage cycle detected")
            seen.add(current)
            result.append(current)
            current = self._parents.get(current)
        return result


class ParetoSelector:
    MAXIMIZE = ("success", "security", "novelty")
    MINIMIZE = ("cost",)

    @classmethod
    def frontier(cls, candidates: list[CandidateProposal]) -> list[CandidateProposal]:
        return [
            candidate
            for candidate in candidates
            if not any(
                cls._dominates(other, candidate)
                for other in candidates
                if other.candidate_id != candidate.candidate_id
            )
        ]

    @classmethod
    def select(cls, candidates: list[CandidateProposal]) -> CandidateProposal:
        frontier = cls.frontier(candidates)
        if not frontier:
            raise ValueError("cannot select from an empty population")
        return sorted(
            frontier,
            key=lambda item: (
                -item.metrics.get("security", 0.0),
                -item.metrics.get("success", 0.0),
                item.metrics.get("cost", float("inf")),
                item.candidate_id,
            ),
        )[0]

    @classmethod
    def _dominates(cls, left: CandidateProposal, right: CandidateProposal) -> bool:
        at_least_as_good = all(
            left.metrics.get(metric, 0.0) >= right.metrics.get(metric, 0.0)
            for metric in cls.MAXIMIZE
        ) and all(
            left.metrics.get(metric, float("inf")) <= right.metrics.get(metric, float("inf"))
            for metric in cls.MINIMIZE
        )
        strictly_better = any(
            left.metrics.get(metric, 0.0) > right.metrics.get(metric, 0.0)
            for metric in cls.MAXIMIZE
        ) or any(
            left.metrics.get(metric, float("inf")) < right.metrics.get(metric, float("inf"))
            for metric in cls.MINIMIZE
        )
        return at_least_as_good and strictly_better
