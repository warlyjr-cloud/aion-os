"""Offline, deterministic OS-EvoBench runner."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

from digital_twin import DigitalTwin
from evaluator.baseline import DeterministicBaseline
from evaluator.checks import evaluate_check
from evaluator.integrity import BenchmarkIntegrityGuard
from evaluator.loader import load_suite
from evaluator.models import (
    BenchmarkReport,
    BenchmarkTask,
    CandidateSubmission,
    TaskResult,
)
from red_team import RedTeamEngine


class EvoBenchRunner:
    """Evaluate typed submissions in a simulation; never execute candidate code."""

    def __init__(self, benchmark_root: Path | None = None) -> None:
        resolved_root = benchmark_root
        if resolved_root is not None:
            project_benchmark_root = resolved_root / "benchmarks" / "os_evobench"
            if project_benchmark_root.is_dir():
                resolved_root = project_benchmark_root
        self.suite, self._integrity = load_suite(resolved_root)
        self._red_team = RedTeamEngine()

    @property
    def integrity(self) -> BenchmarkIntegrityGuard:
        return self._integrity

    def run_baseline(self) -> BenchmarkReport:
        baseline = DeterministicBaseline()
        submissions = baseline.submissions(self.suite.public_views())
        return self.evaluate(baseline.candidate_id, submissions)

    def run(self, task_id: str) -> BenchmarkReport:
        """Run one built-in baseline task for the ``aionctl benchmark run`` API."""

        self._integrity.verify()
        task = self.suite.task(task_id)
        baseline = DeterministicBaseline()
        submissions = baseline.submissions((task.public_view(),))
        result = self._evaluate_task(task, submissions[0])
        self._integrity.verify()
        return BenchmarkReport(
            benchmark_id=self.suite.benchmark_id,
            format_version=self.suite.format_version,
            suite_digest=self.suite.suite_digest,
            run_id=self._run_id(baseline.candidate_id, list(submissions)),
            candidate_id=baseline.candidate_id,
            baseline_id=baseline.candidate_id,
            task_results=(result,),
        )

    def evaluate(
        self, candidate_id: str, submissions: Iterable[CandidateSubmission]
    ) -> BenchmarkReport:
        if not candidate_id.strip():
            raise ValueError("candidate_id must not be empty")
        self._integrity.verify()
        indexed: dict[str, CandidateSubmission] = {}
        for submission in submissions:
            if submission.task_id in indexed:
                raise ValueError(f"duplicate submission for task: {submission.task_id}")
            self.suite.task(submission.task_id)
            indexed[submission.task_id] = submission

        canonical_submissions: list[CandidateSubmission] = []
        task_results: list[TaskResult] = []
        for task in self.suite.tasks:
            submission = indexed.get(task.task_id, CandidateSubmission(task_id=task.task_id))
            canonical_submissions.append(submission)
            task_results.append(self._evaluate_task(task, submission))
            self._integrity.verify()

        run_id = self._run_id(candidate_id, canonical_submissions)
        return BenchmarkReport(
            benchmark_id=self.suite.benchmark_id,
            format_version=self.suite.format_version,
            suite_digest=self.suite.suite_digest,
            run_id=run_id,
            candidate_id=candidate_id,
            baseline_id=DeterministicBaseline.candidate_id,
            task_results=tuple(task_results),
        )

    def write_report(self, report: BenchmarkReport, path: Path) -> Path:
        self._integrity.verify()
        resolved_path = path.resolve()
        reports_root = (self._integrity.root / "reports").resolve()
        if reports_root not in resolved_path.parents:
            raise ValueError("benchmark reports must be written under the reports directory")
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(report.to_json(), encoding="utf-8", newline="\n")
        self._integrity.verify()
        return resolved_path

    def _evaluate_task(self, task: BenchmarkTask, submission: CandidateSubmission) -> TaskResult:
        twin = DigitalTwin(task.initial_state, task.granted_capabilities)
        outcomes = twin.apply_all(submission.actions)
        final_state = twin.state
        public_results = {
            check.name: evaluate_check(check, final_state) for check in task.public_tests
        }
        reserved_results = {
            check.name: evaluate_check(check, final_state) for check in task.reserved_tests
        }
        missing_artifacts = tuple(sorted(set(task.expected_artifacts) - set(submission.artifacts)))
        actual_tests = {**public_results, **reserved_results}
        actual_tests.update({f"artifact:{name}": False for name in missing_artifacts})
        total_checks = len(actual_tests) + len(task.expected_artifacts) - len(missing_artifacts)
        passed_checks = sum(actual_tests.values()) + (
            len(task.expected_artifacts) - len(missing_artifacts)
        )
        functional_score = passed_checks / total_checks if total_checks else 0.0
        red_team = self._red_team.analyze(
            actions=submission.actions,
            outcomes=outcomes,
            actual_tests=actual_tests,
            reserved_test_names=tuple(reserved_results),
            claimed_tests=submission.claimed_tests,
            reported_failures=submission.reported_failures,
            measured_metrics=final_state.metrics,
            claimed_metrics=submission.claimed_metrics,
            functional_score=functional_score,
            claimed_score=submission.claimed_score,
        )
        score = 0.0 if red_team.blocked else functional_score
        success = score == 1.0 and all(outcome.accepted for outcome in outcomes)
        return TaskResult(
            task_id=task.task_id,
            category=task.category,
            success=success,
            score=score,
            functional_score=functional_score,
            public_results=public_results,
            reserved_results=reserved_results,
            missing_artifacts=missing_artifacts,
            measured_metrics=final_state.metrics,
            action_outcomes=outcomes,
            red_team=red_team,
        )

    def _run_id(self, candidate_id: str, submissions: list[CandidateSubmission]) -> str:
        payload = {
            "suite_digest": self.suite.suite_digest,
            "candidate_id": candidate_id,
            "submissions": [submission.to_dict() for submission in submissions],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
