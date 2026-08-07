from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - argv list, no shell, hardcoded caller commands
        cmd, cwd=ROOT, capture_output=True, text=True, check=check
    )


def require_success(cmd: list[str], description: str) -> str:
    result = run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(
            f"{description} failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout.strip()


def main() -> None:
    os.environ.setdefault("AION_PROJECT_ROOT", str(ROOT))

    cli_output = require_success(
        [sys.executable, "-m", "src.cli", "start", "--once"], "CLI smoke run"
    )
    if "service" not in cli_output or "aiond" not in cli_output:
        raise SystemExit(f"Unexpected CLI output:\n{cli_output}")

    health_output = require_success(
        [sys.executable, str(ROOT / "scripts" / "health_check.py")], "Health check script"
    )
    health_json = json.loads(health_output)
    if health_json.get("status") != "ready":
        raise SystemExit(f"Unexpected health check payload: {health_json}")

    smoke_output = require_success(
        [sys.executable, str(ROOT / "scripts" / "smoke_check.py")], "Smoke check script"
    )
    if "SMOKE_OK" not in smoke_output:
        raise SystemExit(f"Unexpected smoke output:\n{smoke_output}")

    console = shutil.which("aionctl")
    if not console:
        raise SystemExit("The 'aionctl' console script is not available on PATH")
    console_output = require_success([console, "status"], "aionctl status")
    console_json = json.loads(console_output)
    if console_json.get("status") != "ready":
        raise SystemExit(f"Unexpected aionctl output: {console_json}")

    print("README workflow verified successfully")


if __name__ == "__main__":
    main()
