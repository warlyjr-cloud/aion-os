import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_cli_start_forwards_once_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.cli as cli_module
    calls: list[list[str]] = []

    def fake_start(argv: list[str] | None = None) -> None:
        calls.append(argv or [])

    monkeypatch.setattr(cli_module, "start_daemon", fake_start)
    monkeypatch.setattr(sys, "argv", ["aion-cli", "start", "--once", "--interval", "3.5"])

    cli_module.main()

    assert calls == [["--interval", "3.5", "--once"]]


def test_apply_polymorphism_mutates_python_file(tmp_path: Path) -> None:
    from evolution.polymorph import apply_polymorphism

    project_root = tmp_path
    executor_dir = project_root / "src" / "executor"
    executor_dir.mkdir(parents=True)
    target_file = executor_dir / "sample.py"
    original = "def hello():\n    return 'world'\n"
    target_file.write_text(original, encoding="utf-8")

    mutated = apply_polymorphism(project_root)

    assert mutated is True
    content = target_file.read_text(encoding="utf-8")
    assert content != original
    assert content.strip() != ""
    assert "hello" in content or "_aion_entropy_salt" in content


def test_schrodinger_executor_returns_successful_reality() -> None:
    from evolution.schrodinger import SchrodingerExecutor

    executor = SchrodingerExecutor(dimensions=2)

    def reducer(value: int) -> int:
        if value == 0:
            raise RuntimeError("boom")
        return value

    assert executor.execute_in_superposition(reducer, [(0,), (3,)]) == 3


def test_system_monitor_rolls_back_when_symptoms_are_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from immune_memory.monitor import SystemMonitor

    project_root = tmp_path
    state_root = project_root / ".aion-state"
    state_root.mkdir(parents=True)
    symptoms_path = state_root / "symptoms.txt"
    symptoms_path.write_text("cpu spike", encoding="utf-8")

    class DummyEngine:
        def __init__(self, root: Path) -> None:
            self.root = root

        def current_generation(self) -> SimpleNamespace:
            return SimpleNamespace(generation_id="gen-1")

        def rollback(self) -> SimpleNamespace:
            return SimpleNamespace(mutation_id="mut-1")

    monkeypatch.setattr("immune_memory.monitor.EvolutionEngine", DummyEngine)

    result = SystemMonitor(project_root).check_health_and_react()

    assert result == {"status": "rolled_back", "mutation_id": "mut-1", "reason": "cpu spike"}
    assert not symptoms_path.exists()


def test_model_council_rejects_critical_change_without_independent_verifier() -> None:
    from model_council.council import ModelCouncil

    decision = ModelCouncil.evaluate(
        proposer="alice",
        verifier="alice",
        critical=True,
        accepted=True,
    )

    assert decision.approved is False
    assert decision.reason == "critical changes require an independent verifier"


def test_policy_engine_maps_validation_outcomes() -> None:
    from policy.engine import PolicyEngine, PolicyResult
    from tcb import ValidationOutcome

    class StubValidator:
        def validate(self, action, *, grantee: str):
            return SimpleNamespace(outcome=ValidationOutcome.PERMITTED, reason="ok")

    engine = PolicyEngine(StubValidator())
    result = engine.evaluate(SimpleNamespace(), actor="alice")

    assert isinstance(result, PolicyResult)
    assert result.decision == "allow"
    assert result.reason == "ok"


def test_anthropic_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from providers.llm import AnthropicProvider

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        AnthropicProvider()


def test_mount_quantum_fs_skips_when_fuse_is_unavailable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from quantum_fs import fuse_driver

    monkeypatch.setattr(fuse_driver, "FUSE", None)
    mountpoint = tmp_path / "quantum"

    fuse_driver.mount_quantum_fs(str(mountpoint))

    assert mountpoint.exists()


def test_time_dilation_engine_starts_and_stops() -> None:
    from relativity.scheduler import TimeDilationEngine

    engine = TimeDilationEngine(threshold_percent=90.0, tick_interval=0.01)

    engine.start()
    assert engine.running is True

    engine.stop()
    assert engine.running is False
