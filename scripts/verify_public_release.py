from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=check)


def require_success(cmd: list[str], description: str) -> tuple[bool, str]:
    result = run(cmd, check=False)
    if result.returncode != 0:
        return False, f"{description} failed with exit code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    return True, result.stdout.strip()


def main() -> None:
    os.environ.setdefault("AION_PROJECT_ROOT", str(ROOT))
    os.environ.setdefault("AION_RUNTIME_MODE", "simulation")
    os.environ.setdefault("AION_ALLOW_HOST_MUTATION", "0")

    checks: list[dict[str, Any]] = []

    pytest_ok, pytest_output = require_success([sys.executable, "-m", "pytest", "-q"], "pytest")
    checks.append({"name": "pytest", "passed": pytest_ok, "output": pytest_output})

    readme_ok, readme_output = require_success([sys.executable, str(ROOT / "scripts" / "verify_readme.py")], "README workflow")
    checks.append({"name": "README workflow", "passed": readme_ok, "output": readme_output})

    cli_ok, cli_output = require_success([sys.executable, "-m", "src.cli", "start", "--once"], "CLI smoke run")
    checks.append({"name": "CLI smoke run", "passed": cli_ok, "output": cli_output})

    health_ok, health_output = require_success([sys.executable, str(ROOT / "scripts" / "health_check.py")], "Health check")
    checks.append({"name": "Health check", "passed": health_ok, "output": health_output})

    secret_ok, secret_output = require_success([sys.executable, str(ROOT / "scripts" / "secret_safety_check.py")], "Secret safety scan")
    checks.append({"name": "Secret safety scan", "passed": secret_ok, "output": secret_output})

    console_path = shutil.which("aionctl")
    if console_path:
        status_ok, status_output = require_success([console_path, "status"], "aionctl status")
        checks.append({"name": "aionctl status", "passed": status_ok, "output": status_output})
    else:
        checks.append({"name": "aionctl status", "passed": False, "output": "aionctl console entrypoint not found"})

    payload = {
        "project": "aion-os",
        "status": "ok" if all(item["passed"] for item in checks) else "failed",
        "checks": checks,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    if not all(item["passed"] for item in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
