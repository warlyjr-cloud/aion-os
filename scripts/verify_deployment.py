from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from src.dashboard.app import app

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> str:
    result = subprocess.run(  # noqa: S603 - argv list, no shell, hardcoded caller commands
        cmd, cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise SystemExit(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout.strip()


def main() -> None:
    os.environ.setdefault("AION_PROJECT_ROOT", str(ROOT))
    os.environ.setdefault("AION_RUNTIME_MODE", "simulation")
    os.environ.setdefault("AION_ALLOW_HOST_MUTATION", "0")

    health = run([sys.executable, "scripts/health_check.py"])
    smoke = run([sys.executable, "scripts/smoke_check.py"])
    verify = run([sys.executable, "scripts/verify_public_release.py"])

    with TestClient(app) as client:
        dashboard_health = client.get("/healthz")
        dashboard_ready = client.get("/readyz")

    payload = {
        "project": "aion-os",
        "status": "ok",
        "checks": {
            "health": health,
            "smoke": smoke,
            "public_release": verify,
            "dashboard_health": dashboard_health.json(),
            "dashboard_ready": dashboard_ready.json(),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
