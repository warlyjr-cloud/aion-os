from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import signal
import sys
import time
import traceback
from pathlib import Path

from audit import AuditLog
from vek.engine import EvolutionEngine
from immune_memory.monitor import SystemMonitor
from evolution.polymorph import polymorph_system
from quantum_fs.fuse_driver import mount_quantum_fs
from relativity.scheduler import TimeDilationEngine
from aiond.genesis_lock import verify_dead_mans_switch
import random

def _project_root() -> Path:
    return Path(os.environ.get("AION_PROJECT_ROOT", Path.cwd())).resolve()


def run_once(project_root: Path, log: AuditLog) -> dict[str, object]:
    state_root = project_root / ".aion-state"
    stopped = (state_root / "STOP").exists()
    
    # Process Inbox
    inbox_dir = state_root / "inbox"
    archive_dir = state_root / "archive"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 0. The Dead Man's Switch Verification (Security Hardening)
    verify_dead_mans_switch(project_root)

    # 1. Start Immune System Monitor
    monitor = SystemMonitor(project_root)
    immune_reaction = monitor.check_health_and_react()
    
    processed_intents = []
    if not stopped:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for intent_file in inbox_dir.glob("*.txt"):
                objective = intent_file.read_text(encoding="utf-8").strip()
                if objective:
                    engine = EvolutionEngine(project_root)
                    future = executor.submit(engine.plan, objective)
                    futures[future] = intent_file
                else:
                    intent_file.rename(archive_dir / intent_file.name)
            
            for future in concurrent.futures.as_completed(futures):
                intent_file = futures[future]
                try:
                    record = future.result()
                    processed_intents.append({"file": intent_file.name, "status": "planned", "mutation_id": record.mutation_id})
                except Exception as e:
                    processed_intents.append({"file": intent_file.name, "status": "error", "error": str(e)})
                intent_file.rename(archive_dir / intent_file.name)
            
    # Probabilistic Polymorphism (10% chance per run for MVP demonstration)
    polymorph_target = None
    if not stopped and random.random() < 0.1:
        polymorph_target = polymorph_system(project_root)
        
    return {
        "service": "aiond",
        "healthy": not stopped,
        "mode": "simulation-only" if os.getenv("AION_RUNTIME_MODE", "simulation") == "simulation" else "real",
        "audit_valid": log.verify(),
        "processed_intents": processed_intents,
        "immune_reaction": immune_reaction,
        "polymorphism_target": str(polymorph_target) if polymorph_target else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AION local control daemon")
    parser.add_argument("--once", action="store_true", help="perform one health check and exit")
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    root = _project_root()
    if args.once:
        state_root = root / ".aion-state"
        print(json.dumps(run_once(root, AuditLog(state_root / "audit.jsonl")), sort_keys=True))
        return
        
    quantum_mount = root / ".aion-state" / "quantum"
    mount_quantum_fs(str(quantum_mount))
    
    dilation_engine = TimeDilationEngine(threshold_percent=60.0)
    dilation_engine.start()
    
    state_root = root / ".aion-state"
    log = AuditLog(state_root / "audit.jsonl")
    
    running = True

    def stop_handler(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False
        dilation_engine.stop()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)
    while running and not (root / ".aion-state" / "STOP").exists():
        try:
            run_once(root, log)
        except Exception as e:
            print(f"CRITICAL ERROR in daemon heartbeat: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        time.sleep(max(args.interval, 0.1))


if __name__ == "__main__":
    main()
