from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.dashboard.app import app

os.environ.setdefault("AION_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))


def test_dashboard_health_and_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Isolated on purpose: /readyz requires .aion-state/mutations to exist,
    # which is gitignored and therefore absent on a clean checkout (this
    # test used to rely on AION_PROJECT_ROOT pointing at the real repo
    # root, which only had that directory by accident on a dev machine
    # that had already run other AION commands locally - it silently
    # passed there and failed on every clean CI checkout).
    monkeypatch.setenv("AION_PROJECT_ROOT", str(tmp_path))
    client = TestClient(app)

    health = client.get("/healthz")
    assert health.status_code == 200
    payload = health.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "aion-dashboard"

    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["ready"] is True

    status = client.get("/api/status")
    assert status.status_code == 200
    body = status.json()
    assert body["project"] == "aion-os"
    assert "status" in body


def test_api_mutation_detail_exposes_real_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AION_PROJECT_ROOT", str(tmp_path))
    mutations_dir = tmp_path / ".aion-state" / "mutations"
    mutations_dir.mkdir(parents=True)
    (mutations_dir / "mut-demo000001.json").write_text(
        json.dumps({"mutation_id": "mut-demo000001", "state": "monitoring"}),
        encoding="utf-8",
    )
    audit_file = tmp_path / ".aion-state" / "audit.jsonl"
    audit_file.write_text(
        json.dumps({"mutation_id": "mut-demo000001", "event_type": "generation.promoted"})
        + "\n"
        + json.dumps({"mutation_id": "mut-other", "event_type": "generation.promoted"})
        + "\n",
        encoding="utf-8",
    )
    proof_dir = tmp_path / "proofs" / "mut-demo000001"
    proof_dir.mkdir(parents=True)
    (proof_dir / "security-report.json").write_text(
        json.dumps({"status": "pass", "deterministic_verifier": {"approved": True}}),
        encoding="utf-8",
    )

    client = TestClient(app)

    listing = client.get("/api/mutations")
    assert listing.status_code == 200
    assert any(m["mutation_id"] == "mut-demo000001" for m in listing.json())

    detail = client.get("/api/mutations/mut-demo000001")
    assert detail.status_code == 200
    body = detail.json()
    assert body["record"]["state"] == "monitoring"
    assert body["proof"]["security-report.json"]["deterministic_verifier"]["approved"] is True
    assert len(body["audit_events"]) == 1
    assert body["audit_events"][0]["event_type"] == "generation.promoted"

    missing = client.get("/api/mutations/mut-does-not-exist")
    assert missing.status_code == 404
