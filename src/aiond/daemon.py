from __future__ import annotations

import argparse
import json
import os
import signal
import time
from pathlib import Path

from audit import AuditLog
from vek.engine import EvolutionEngine
from immune_memory.monitor import SystemMonitor


def _project_root() -> Path:
    return Path(os.environ.get("AION_PROJECT_ROOT", Path.cwd())).resolve()


def run_once(project_root: Path) -> dict[str, object]:
    state_root = project_root / ".aion-state"
    log = AuditLog(state_root / "audit.jsonl")
    stopped = (state_root / "STOP").exists()
    
    # Process Inbox
    inbox_dir = state_root / "inbox"
    archive_dir = state_root / "archive"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Process Immune System Monitoring
    monitor = SystemMonitor(project_root)
    immune_reaction = monitor.check_health_and_react()
    
    processed_intents = []
    if not stopped:
        for intent_file in inbox_dir.glob("*.txt"):
            objective = intent_file.read_text(encoding="utf-8").strip()
            if objective:
                try:
                    engine = EvolutionEngine(project_root)
                    record = engine.plan(objective)
                    processed_intents.append({"file": intent_file.name, "status": "planned", "mutation_id": record.mutation_id})
                except Exception as e:
                    processed_intents.append({"file": intent_file.name, "status": "error", "error": str(e)})
            intent_file.rename(archive_dir / intent_file.name)
            
    return {
        "service": "aiond",
        "healthy": not stopped,
        "mode": "simulation-only" if os.getenv("AION_RUNTIME_MODE", "simulation") == "simulation" else "real",
        "audit_valid": log.verify(),
        "processed_intents": processed_intents,
        "immune_reaction": immune_reaction,
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
