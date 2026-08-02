"""Schemas represented as typed Python models for the offline benchmark."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from digital_twin.models import ActionOutcome, JsonValue, TwinState, TypedAction
from red_team.models import RedTeamReport


def _empty_bool_dict() -> dict[str, bool]:
    return {}


def _empty_float_dict() -> dict[str, float]:
    return {}


def _as_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    return float(value)


class BenchmarkCategory(StrEnum):
    CAPABILITY_INSTALL = "capability_install"
    RECOVERY = "recovery"
    OPTIMIZATION = "optimization"
    SECURITY = "security"
    MEMORY_POISONING = "memory_poisoning"


@dataclass(frozen=True, slots=True)
class CheckSpec:
    name: str
    state_path: str
    operator: str
    expected: JsonValue

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> CheckSpec:
        return cls(
            name=str(value["name"]),
            state_path=str(value["state_path"]),
            operator=str(value["operator"]),
            expected=value.get("expected"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "state_path": self.state_path,
            "operator": self.operator,
            "expected": self.expected,
        }


@dataclass(frozen=True, slots=True)
class MetricSpec:
    name: str
    direction: str
    threshold: float
    unit: str

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> MetricSpec:
        return cls(
            name=str(value["name"]),
            direction=str(value["direction"]),
            threshold=_as_float(value["threshold"], "metric.threshold"),
            unit=str(value.get("unit", "count")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "direction": self.direction,
            "threshold": self.threshold,
            "unit": self.unit,
        }


@dataclass(frozen=True, slots=True)
class TaskView:
    """The complete candidate-facing surface. Reserved checks cannot appear here."""

    task_id: str
    category: BenchmarkCategory
    objective: str
    constraints: tuple[str, ...]
    initial_state: dict[str, JsonValue]
    metrics: tuple[MetricSpec, ...]
    public_tests: tuple[CheckSpec, ...]
    granted_capabilities: tuple[str, ...]
    resource_limits: dict[str, float]
    success_criteria: tuple[str, ...]
    safety_criteria: tuple[str, ...]
    expected_artifacts: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "category": self.category.value,
            "objective": self.objective,
            "constraints": list(self.constraints),
            "initial_state": self.initial_state,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "public_tests": [check.to_dict() for check in self.public_tests],
            "granted_capabilities": list(self.granted_capabilities),
            "resource_limits": dict(sorted(self.resource_limits.items())),
            "success_criteria": list(self.success_criteria),
            "safety_criteria": list(self.safety_criteria),
            "expected_artifacts": list(self.expected_artifacts),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkTask:
    task_id: str
    category: BenchmarkCategory
    objective: str
    constraints: tuple[str, ...]
    initial_state: TwinState
    metrics: tuple[MetricSpec, ...]
    public_tests: tuple[CheckSpec, ...]
    reserved_tests: tuple[CheckSpec, ...]
    granted_capabilities: tuple[str, ...]
    resource_limits: dict[str, float]
    success_criteria: tuple[str, ...]
    safety_criteria: tuple[str, ...]
    expected_artifacts: tuple[str, ...]

    def public_view(self) -> TaskView:
        return TaskView(
            task_id=self.task_id,
            category=self.category,
            objective=self.objective,
            constraints=self.constraints,
            initial_state=self.initial_state.to_dict(),
            metrics=self.metrics,
            public_tests=self.public_tests,
            granted_capabilities=self.granted_capabilities,
            resource_limits=dict(self.resource_limits),
            success_criteria=self.success_criteria,
            safety_criteria=self.safety_criteria,
            expected_artifacts=self.expected_artifacts,
        )


@dataclass(frozen=True, slots=True)
class BenchmarkSuite:
    benchmark_id: str
    format_version: str
    tasks: tuple[BenchmarkTask, ...]
    suite_digest: str

    def task(self, task_id: str) -> BenchmarkTask:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"unknown benchmark task: {task_id}")

    def public_views(self) -> tuple[TaskView, ...]:
        return tuple(task.public_view() for task in self.tasks)


@dataclass(frozen=True, slots=True)
class CandidateSubmission:
    task_id: str
    actions: tuple[TypedAction, ...] = ()
    artifacts: tuple[str, ...] = ()
    claimed_tests: dict[str, bool] = field(default_factory=_empty_bool_dict)
    reported_failures: tuple[str, ...] = ()
    claimed_metrics: dict[str, float] = field(default_factory=_empty_float_dict)
    claimed_score: float | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> CandidateSubmission:
        raw_score = value.get("claimed_score")
        return cls(
            task_id=str(value["task_id"]),
            actions=tuple(TypedAction.from_dict(dict(item)) for item in value.get("actions", [])),
            artifacts=tuple(str(item) for item in value.get("artifacts", [])),
            claimed_tests={
                str(key): bool(item) for key, item in value.get("claimed_tests", {}).items()
            },
            reported_failures=tuple(str(item) for item in value.get("reported_failures", [])),
            claimed_metrics={
                str(key): float(item) for key, item in value.get("claimed_metrics", {}).items()
            },
            claimed_score=None if raw_score is None else float(raw_score),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "actions": [action.to_dict() for action in self.actions],
            "artifacts": sorted(self.artifacts),
            "claimed_tests": dict(sorted(self.claimed_tests.items())),
            "reported_failures": sorted(self.reported_failures),
            "claimed_metrics": dict(sorted(self.claimed_metrics.items())),
            "claimed_score": self.claimed_score,
        }


@dataclass(frozen=True, slots=True)
class TaskResult:
    task_id: str
    category: BenchmarkCategory
    success: bool
    score: float
    functional_score: float
    public_results: dict[str, bool]
    reserved_results: dict[str, bool]
    missing_artifacts: tuple[str, ...]
    measured_metrics: dict[str, float]
    action_outcomes: tuple[ActionOutcome, ...]
    red_team: RedTeamReport

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "category": self.category.value,
            "success": self.success,
            "score": self.score,
            "functional_score": self.functional_score,
            "public_results": dict(sorted(self.public_results.items())),
            "reserved_summary": {
                "passed": sum(self.reserved_results.values()),
                "total": len(self.reserved_results),
            },
            "missing_artifacts": list(self.missing_artifacts),
            "measured_metrics": dict(sorted(self.measured_metrics.items())),
            "action_outcomes": [outcome.to_dict() for outcome in self.action_outcomes],
            "red_team": self.red_team.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    benchmark_id: str
    format_version: str
    suite_digest: str
    run_id: str
    candidate_id: str
    baseline_id: str
    task_results: tuple[TaskResult, ...]

    @property
    def score(self) -> float:
        if not self.task_results:
            return 0.0
        return sum(result.score for result in self.task_results) / len(self.task_results)

    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_id": self.benchmark_id,
            "format_version": self.format_version,
            "suite_digest": self.suite_digest,
            "run_id": self.run_id,
            "candidate_id": self.candidate_id,
            "baseline_id": self.baseline_id,
            "offline": True,
            "aggregate": {
                "tasks_total": len(self.task_results),
                "tasks_succeeded": sum(result.success for result in self.task_results),
                "guarded_failures": sum(result.red_team.blocked for result in self.task_results),
                "score": self.score,
            },
            "task_results": [result.to_dict() for result in self.task_results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    def model_dump(self, *, mode: str = "python") -> dict[str, object]:
        """Provide the Pydantic-compatible boundary used by the existing CLI."""

        if mode not in {"python", "json"}:
            raise ValueError(f"unsupported serialization mode: {mode}")
        return self.to_dict()
