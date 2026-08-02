from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from digital_twin import TypedAction
from evaluator import (
    BenchmarkIntegrityError,
    CandidateSubmission,
    EvoBenchRunner,
    default_benchmark_root,
)


def test_baseline_runs_all_five_tasks_reproducibly_offline() -> None:
    runner = EvoBenchRunner()

    first = runner.run_baseline()
    second = runner.run_baseline()

    assert first.to_json() == second.to_json()
    assert first.score == 1.0
    assert len(first.task_results) == 5
    assert all(result.success for result in first.task_results)
    assert {result.category.value for result in first.task_results} == {
        "capability_install",
        "recovery",
        "optimization",
        "security",
        "memory_poisoning",
    }
    serialized = first.to_json()
    assert json.loads(serialized)["offline"] is True
    assert "no_host_package_mutation" not in serialized
    assert "memory_guardrail" not in serialized


def test_cli_contract_accepts_project_root_and_returns_model_dump() -> None:
    project_root = default_benchmark_root().parents[1]
    report = EvoBenchRunner(project_root).run("capability-install-ffmpeg")

    payload = report.model_dump(mode="json")
    assert payload["aggregate"] == {
        "tasks_total": 1,
        "tasks_succeeded": 1,
        "guarded_failures": 0,
        "score": 1.0,
    }
    assert payload["task_results"][0]["task_id"] == "capability-install-ffmpeg"


def test_candidate_task_views_do_not_expose_reserved_tests() -> None:
    runner = EvoBenchRunner()

    for task_view in runner.suite.public_views():
        assert not hasattr(task_view, "reserved_tests")
        serialized = json.dumps(task_view.to_dict(), sort_keys=True)
        assert "reserved_tests" not in serialized
        assert "no_host_package_mutation" not in serialized
        assert "memory_guardrail" not in serialized


def test_digital_twin_rejects_capability_scope_mismatch() -> None:
    runner = EvoBenchRunner()
    submission = CandidateSubmission(
        task_id="capability-install-ffmpeg",
        actions=(
            TypedAction(
                "install-curl-with-wrong-scope",
                "capability.install",
                "curl",
                "package.propose:ffmpeg",
            ),
        ),
        artifacts=("capability-manifest",),
        reported_failures=("ffmpeg_registered", "install_within_limit"),
    )

    report = runner.evaluate("scope-mismatch", (submission,))
    result = next(
        item for item in report.task_results if item.task_id == "capability-install-ffmpeg"
    )

    assert result.red_team.has_code("ACTION_REJECTED")
    assert result.score == 0.0
    assert not result.success


def test_integrity_guard_detects_real_asset_change(tmp_path: Path) -> None:
    copied_root = tmp_path / "os_evobench"
    shutil.copytree(default_benchmark_root(), copied_root)
    runner = EvoBenchRunner(copied_root)
    task_manifest = copied_root / "public" / "tasks.json"
    original = task_manifest.read_text(encoding="utf-8")
    task_manifest.write_text(original.replace("ffmpeg", "tampered", 1), encoding="utf-8")

    with pytest.raises(BenchmarkIntegrityError, match=r"public/tasks\.json"):
        runner.run_baseline()


def test_report_writer_is_confined_to_reports_directory(tmp_path: Path) -> None:
    copied_root = tmp_path / "os_evobench"
    shutil.copytree(default_benchmark_root(), copied_root)
    runner = EvoBenchRunner(copied_root)
    report = runner.run_baseline()

    output = runner.write_report(report, copied_root / "reports" / "baseline.json")
    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8"))["aggregate"]["score"] == 1.0

    with pytest.raises(ValueError, match="reports directory"):
        runner.write_report(report, tmp_path / "outside.json")
