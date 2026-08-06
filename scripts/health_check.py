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
    status = run([sys.executable, "-m", "aionctl.cli", "status"])
    print(status)


if __name__ == "__main__":
    main()
