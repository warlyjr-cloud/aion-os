from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from immune_memory import MemoryStore
from tcb import EvidenceVerifier
from vek import EvolutionEngine

app = typer.Typer(help="AION safe evolution control plane", no_args_is_help=True)
genome_app = typer.Typer(help="Inspect the system genome")
memory_app = typer.Typer(help="Inspect governed memory")
mutations_app = typer.Typer(help="Inspect and decide mutations")
population_app = typer.Typer(help="Inspect candidate populations")
lineage_app = typer.Typer(help="Inspect generation ancestry")
generations_app = typer.Typer(help="Inspect generations")
proof_app = typer.Typer(help="Verify proof-carrying mutations")
benchmark_app = typer.Typer(help="Run OS-EvoBench")
autonomy_app = typer.Typer(help="Inspect autonomy controls")

app.add_typer(genome_app, name="genome")
app.add_typer(memory_app, name="memory")
app.add_typer(mutations_app, name="mutations")
app.add_typer(population_app, name="population")
app.add_typer(lineage_app, name="lineage")
app.add_typer(generations_app, name="generations")
app.add_typer(proof_app, name="proof")
app.add_typer(benchmark_app, name="benchmark")
app.add_typer(autonomy_app, name="autonomy")


def _root() -> Path:
    return Path(os.environ.get("AION_PROJECT_ROOT", Path.cwd())).resolve()


def _engine() -> EvolutionEngine:
    return EvolutionEngine(_root())


def _emit(value: Any) -> None:
    typer.echo(json.dumps(value, indent=2, sort_keys=True, default=str))


@app.command()
def status() -> None:
    """Show local control-plane status without contacting a provider."""
    engine = _engine()
    current = engine.current_generation()
    _emit(
        {
            "status": "stopped" if (engine.state_root / "STOP").exists() else "ready",
            "autonomy_level": 2,
            "execution_mode": "simulation-only",
            "current_generation": current.model_dump(mode="json") if current else None,
            "mutations": len(engine.mutations.list_all()),
            "audit_valid": engine.audit.verify(),
        }
    )


@app.command()
def ask(objective: str) -> None:
    """Create a proof-carrying plan for an objective."""
    plan(objective)


@app.command()
def plan(objective: str) -> None:
    record = _engine().plan(objective)
    _emit(record.model_dump(mode="json"))


@app.command()
def doctor() -> None:
    engine = _engine()
    tools = {
        name: shutil.which(name)
        for name in ("git", "gh", "uv", "qemu-system-x86_64", "podman")
    }
    _emit(
        {
            "python": sys.version.split()[0],
            "required_python": ">=3.12",
            "tools": tools,
            "audit_valid": engine.audit.verify(),
            "host_mutation_enabled": False,
        }
    )


@app.command()
def capabilities() -> None:
    manifests: list[dict[str, Any]] = []
    for path in sorted((_root() / "capabilities").glob("*.json")):
        manifests.append(cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8"))))
    _emit(manifests)


@genome_app.command("show")
def genome_show() -> None:
    current = _engine().current_generation()
    _emit(current.model_dump(mode="json") if current else {"generation": None})


@genome_app.command("export")
def genome_export(
    output: Annotated[Path, typer.Option("--output")] = Path("genome/export.json"),
) -> None:
    current = _engine().current_generation()
    if current is None:
        raise typer.BadParameter("no active generation")
    target = output if output.is_absolute() else _root() / output
    current.export(target)
    _emit({"exported": str(target)})


@memory_app.command("list")
def memory_list() -> None:
    entries = MemoryStore(_engine().state_root / "memory.jsonl").list_all()
    _emit([entry.model_dump(mode="json") for entry in entries])


@memory_app.command("quarantine")
def memory_quarantine(
    memory_id: str, reason: str = typer.Option("human quarantine", "--reason")
) -> None:
    entry = MemoryStore(_engine().state_root / "memory.jsonl").quarantine(memory_id, reason=reason)
    _emit(entry.model_dump(mode="json"))


@mutations_app.command("list")
def mutations_list() -> None:
    _emit([item.model_dump(mode="json") for item in _engine().mutations.list_all()])


@mutations_app.command("show")
def mutations_show(mutation_id: str) -> None:
    _emit(_engine().mutations.load(mutation_id).model_dump(mode="json"))


@mutations_app.command("evidence")
def mutations_evidence(mutation_id: str) -> None:
    record = _engine().mutations.load(mutation_id)
    if not record.proof_path:
        raise typer.BadParameter("mutation has no proof")
    _emit({"mutation_id": mutation_id, "proof_path": record.proof_path})


@mutations_app.command("approve")
def mutations_approve(mutation_id: str, actor: str = typer.Option(..., "--actor")) -> None:
    _emit(_engine().approve(mutation_id, approved_by=actor).model_dump(mode="json"))


@mutations_app.command("reject")
def mutations_reject(
    mutation_id: str,
    reason: str = typer.Option(..., "--reason"),
    actor: str = typer.Option(..., "--actor"),
) -> None:
    _emit(_engine().reject(mutation_id, reason=reason, rejected_by=actor).model_dump(mode="json"))


@mutations_app.command("promote")
def mutations_promote(mutation_id: str) -> None:
    _emit(_engine().promote(mutation_id).model_dump(mode="json"))


@population_app.command("show")
def population_show(objective_id: str) -> None:
    matches = [item for item in _engine().mutations.list_all() if item.objective_id == objective_id]
    _emit(
        [
            {
                "mutation_id": item.mutation_id,
                "candidates": [candidate.model_dump(mode="json") for candidate in item.candidates],
                "selected": item.selected_candidate_id,
            }
            for item in matches
        ]
    )


@lineage_app.command("show")
def lineage_show(generation_id: str) -> None:
    root = _engine().generations_root
    lineage: list[dict[str, Any]] = []
    current: str | None = generation_id
    seen: set[str] = set()
    while current:
        if current in seen:
            raise typer.BadParameter("generation lineage contains a cycle")
        seen.add(current)
        path = root / f"{current}.json"
        if not path.is_file():
            raise typer.BadParameter(f"unknown generation: {current}")
        item = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        lineage.append(item)
        current = item.get("parent_generation_id")
    _emit(lineage)


@generations_app.command("list")
def generations_list() -> None:
    root = _engine().generations_root
    _emit(
        [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("gen-*.json"))]
    )


@proof_app.command("verify")
def proof_verify(mutation_id: str) -> None:
    proof_dir = _root() / "proofs" / mutation_id
    _emit({"mutation_id": mutation_id, "valid": EvidenceVerifier().verify(proof_dir)})


@benchmark_app.command("list")
def benchmark_list() -> None:
    tasks: list[dict[str, Any]] = []
    for path in sorted((_root() / "benchmarks" / "os_evobench" / "public").glob("*.json")):
        tasks.append(cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8"))))
    _emit(tasks)


@benchmark_app.command("run")
def benchmark_run(task_id: str) -> None:
    from evaluator import EvoBenchRunner

    runner = EvoBenchRunner(_root())
    report = runner.run(task_id)
    runner.write_report(
        report,
        _root() / "benchmarks" / "os_evobench" / "reports" / f"{report.run_id}.json",
    )
    _emit(report.model_dump(mode="json"))


@benchmark_app.command("report")
def benchmark_report() -> None:
    reports: list[dict[str, Any]] = []
    for path in sorted((_root() / "benchmarks" / "os_evobench" / "reports").glob("*.json")):
        reports.append(cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8"))))
    _emit(reports)


@autonomy_app.command("show")
def autonomy_show() -> None:
    _emit(
        {
            "level": 2,
            "meaning": "construct and test in simulation",
            "human_approval": "required for every promotion",
            "budgets": {"network_requests": 0, "host_mutations": 0, "risk_tier": 1},
        }
    )


@app.command()
def rollback(mutation_id: str | None = typer.Option(None, "--mutation-id")) -> None:
    _emit(_engine().rollback(mutation_id).model_dump(mode="json"))


@app.command()
def stop() -> None:
    marker = _engine().state_root / "STOP"
    marker.write_text("human-requested\n", encoding="utf-8")
    _emit({"status": "stopped", "marker": str(marker)})


if __name__ == "__main__":
    app()
