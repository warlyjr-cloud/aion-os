import json
from pathlib import Path
from typing import Any, cast

import pytest
from typer.testing import CliRunner

from aionctl import app
from aiond.daemon import run_once


def payload(output: str) -> Any:
    return json.loads(output)


def test_cli_full_simulated_decision_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AION_PROJECT_ROOT", str(tmp_path))
    runner = CliRunner()

    assert runner.invoke(app, ["status"]).exit_code == 0
    assert payload(runner.invoke(app, ["capabilities"]).stdout) == []
    assert payload(runner.invoke(app, ["memory", "list"]).stdout) == []
    assert payload(runner.invoke(app, ["autonomy", "show"]).stdout)["level"] == 2
    assert payload(runner.invoke(app, ["doctor"]).stdout)["host_mutation_enabled"] is False

    planned = runner.invoke(app, ["plan", "Process and reduce video files"])
    assert planned.exit_code == 0, planned.stdout
    record = cast(dict[str, Any], payload(planned.stdout))
    mutation_id = cast(str, record["mutation_id"])
    objective_id = cast(str, record["objective_id"])

    assert runner.invoke(app, ["mutations", "show", mutation_id]).exit_code == 0
    assert runner.invoke(app, ["mutations", "evidence", mutation_id]).exit_code == 0
    assert runner.invoke(app, ["population", "show", objective_id]).exit_code == 0
    verified = runner.invoke(app, ["proof", "verify", mutation_id])
    assert payload(verified.stdout)["valid"] is True

    approved = runner.invoke(app, ["mutations", "approve", mutation_id, "--actor", "human"])
    assert approved.exit_code == 0, approved.stdout
    promoted = runner.invoke(app, ["mutations", "promote", mutation_id])
    assert promoted.exit_code == 0, promoted.stdout

    generations = cast(
        list[dict[str, Any]], payload(runner.invoke(app, ["generations", "list"]).stdout)
    )
    generation_id = cast(str, generations[0]["generation_id"])
    assert runner.invoke(app, ["genome", "show"]).exit_code == 0
    assert runner.invoke(app, ["genome", "export", "--output", "genome/export.json"]).exit_code == 0
    assert (tmp_path / "genome" / "export.json").is_file()
    assert runner.invoke(app, ["lineage", "show", generation_id]).exit_code == 0

    rolled_back = runner.invoke(app, ["rollback", "--mutation-id", mutation_id])
    assert rolled_back.exit_code == 0, rolled_back.stdout
    assert runner.invoke(app, ["stop"]).exit_code == 0
    assert run_once(tmp_path)["healthy"] is False
