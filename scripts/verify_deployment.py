from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Command failed ({result.returncode}): {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return result.stdout.strip()


def main() -> None:
    os.environ.setdefault("AION_PROJECT_ROOT", str(ROOT))
    os.environ.setdefault("AION_RUNTIME_MODE", "simulation")
    os.environ.setdefault("AION_ALLOW_HOST_MUTATION", "0")

    health = run([sys.executable, "scripts/health_check.py"])
    smoke = run([sys.executable, "scripts/smoke_check.py"])
    verify = run([sys.executable, "scripts/verify_public_release.py"])

    payload = {
        "project": "aion-os",
        "status": "ok",
        "checks": {
            "health": health,
            "smoke": smoke,
            "public_release": verify,
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
