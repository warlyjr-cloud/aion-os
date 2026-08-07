from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from src.dashboard.app import app

os.environ.setdefault("AION_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))


def test_dashboard_health_and_status() -> None:
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
