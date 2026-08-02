"""Load the public and reserved parts of OS-EvoBench into separate models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from digital_twin.models import TwinState
from evaluator.integrity import BenchmarkIntegrityGuard
from evaluator.models import (
    BenchmarkCategory,
    BenchmarkSuite,
    BenchmarkTask,
    CheckSpec,
    MetricSpec,
)


def default_benchmark_root() -> Path:
    return Path(__file__).resolve().parents[2] / "benchmarks" / "os_evobench"


def _read_object(path: Path) -> dict[str, object]:
    try:
        value = cast(object, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"unable to load benchmark asset {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"benchmark asset must contain a JSON object: {path}")
    return cast(dict[str, object], value)


def _object(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return cast(dict[str, object], value)


def _objects(value: object, field_name: str) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
    items: list[dict[str, object]] = []
    for item in cast(list[object], value):
        items.append(_object(item, f"{field_name} item"))
    return tuple(items)


def _strings(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
    return tuple(str(item) for item in cast(list[object], value))


def _float_mapping(value: object, field_name: str) -> dict[str, float]:
    raw = _object(value, field_name)
    result: dict[str, float] = {}
    for key, item in raw.items():
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{field_name}.{key} must be numeric")
        result[key] = float(item)
    return result


def load_suite(root: Path | None = None) -> tuple[BenchmarkSuite, BenchmarkIntegrityGuard]:
    benchmark_root = (root or default_benchmark_root()).resolve()
    guard = BenchmarkIntegrityGuard.capture(benchmark_root)
    public_data = _read_object(benchmark_root / "public" / "tasks.json")
    reserved_data = _read_object(benchmark_root / "reserved" / "tests.json")
    raw_reserved = _object(reserved_data.get("tasks"), "reserved tests.tasks")

    tasks: list[BenchmarkTask] = []
    raw_tasks = _objects(public_data.get("tasks"), "public tasks")
    for raw_task in raw_tasks:
        task_id = str(raw_task["task_id"])
        reserved_for_task = _objects(raw_reserved.get(task_id), f"reserved tests for {task_id}")
        if not reserved_for_task:
            raise ValueError(f"task has no reserved tests: {task_id}")
        tasks.append(
            BenchmarkTask(
                task_id=task_id,
                category=BenchmarkCategory(str(raw_task["category"])),
                objective=str(raw_task["objective"]),
                constraints=_strings(raw_task.get("constraints"), "constraints"),
                initial_state=TwinState.from_dict(
                    _object(raw_task.get("initial_state"), "initial_state")
                ),
                metrics=tuple(
                    MetricSpec.from_dict(item)
                    for item in _objects(raw_task.get("metrics"), "metrics")
                ),
                public_tests=tuple(
                    CheckSpec.from_dict(item)
                    for item in _objects(raw_task.get("public_tests"), "public_tests")
                ),
                reserved_tests=tuple(CheckSpec.from_dict(item) for item in reserved_for_task),
                granted_capabilities=_strings(
                    raw_task.get("granted_capabilities"), "granted_capabilities"
                ),
                resource_limits=_float_mapping(raw_task.get("resource_limits"), "resource_limits"),
                success_criteria=_strings(raw_task.get("success_criteria"), "success_criteria"),
                safety_criteria=_strings(raw_task.get("safety_criteria"), "safety_criteria"),
                expected_artifacts=_strings(
                    raw_task.get("expected_artifacts"), "expected_artifacts"
                ),
            )
        )

    task_ids = [task.task_id for task in tasks]
    if len(tasks) != 5 or len(set(task_ids)) != 5:
        raise ValueError("OS-EvoBench MVP must contain exactly five uniquely identified tasks")
    suite = BenchmarkSuite(
        benchmark_id=str(public_data.get("benchmark_id", "aion-os-evobench")),
        format_version=str(public_data.get("format_version", "1.0")),
        tasks=tuple(tasks),
        suite_digest=guard.suite_digest,
    )
    guard.verify()
    return suite, guard
