from __future__ import annotations

import argparse
import json
import os
import signal
import time
from pathlib import Path

from audit import AuditLog


def _project_root() -> Path:
    return Path(os.environ.get("AION_PROJECT_ROOT", Path.cwd())).resolve()


def run_once(project_root: Path) -> dict[str, object]:
    state_root = project_root / ".aion-state"
    log = AuditLog(state_root / "audit.jsonl")
    stopped = (state_root / "STOP").exists()
    return {
        "service": "aiond",
        "healthy": not stopped,
        "mode": "simulation-only",
        "audit_valid": log.verify(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AION local control daemon")
    parser.add_argument("--once", action="store_true", help="perform one health check and exit")
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    root = _project_root()
    if args.once:
        print(json.dumps(run_once(root), sort_keys=True))
        return
    running = True

    def stop_handler(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)
    while running and not (root / ".aion-state" / "STOP").exists():
        run_once(root)
        time.sleep(max(args.interval, 0.1))


if __name__ == "__main__":
    main()
