"""Run the deterministic (guarded) baseline and a deliberately naive
(unguarded) baseline through the same OS-EvoBench harness and report both
scores side by side. This is a real, reproducible comparison - not a claim
about the numbers, the numbers themselves, produced by evaluating both
candidates against the identical task suite, public and reserved tests
included.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluator.baseline import DeterministicBaseline
from evaluator.naive_baseline import NaiveBaseline
from evaluator.runner import EvoBenchRunner


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare guarded vs naive OS-EvoBench runs")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args()

    runner = EvoBenchRunner(arguments.benchmark_root)

    guarded = DeterministicBaseline()
    guarded_report = runner.evaluate(
        guarded.candidate_id, guarded.submissions(runner.suite.public_views())
    )

    naive = NaiveBaseline()
    naive_report = runner.evaluate(
        naive.candidate_id, naive.submissions(runner.suite.public_views())
    )

    def summarize(report: object) -> dict[str, object]:
        task_results = report.task_results  # type: ignore[attr-defined]
        return {
            "candidate_id": report.candidate_id,  # type: ignore[attr-defined]
            "score": report.score,  # type: ignore[attr-defined]
            "tasks_succeeded": sum(1 for t in task_results if t.success),
            "tasks_total": len(task_results),
            "red_team_blocked": sum(1 for t in task_results if t.red_team.blocked),
        }

    comparison = {
        "benchmark_id": runner.suite.benchmark_id,
        "suite_digest": runner.suite.suite_digest,
        "guarded": summarize(guarded_report),
        "naive": summarize(naive_report),
        "per_task": [
            {
                "task_id": guarded_task.task_id,
                "guarded_success": guarded_task.success,
                "guarded_score": guarded_task.score,
                "naive_success": naive_task.success,
                "naive_score": naive_task.score,
            }
            for guarded_task, naive_task in zip(
                guarded_report.task_results, naive_report.task_results, strict=True
            )
        ],
    }

    output_text = json.dumps(comparison, indent=2, sort_keys=True)
    if arguments.output is None:
        print(output_text)
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(output_text + "\n", encoding="utf-8")
        print(arguments.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
