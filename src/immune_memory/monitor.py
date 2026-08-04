import os
from pathlib import Path
from typing import Optional
from vek.engine import EvolutionEngine
from audit import AuditLog

class SystemMonitor:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_root = project_root / ".aion-state"
        self.symptoms_file = self.state_root / "symptoms.txt"
        self.log = AuditLog(self.state_root / "audit.jsonl")

    def check_health_and_react(self) -> Optional[dict]:
        # Em um sistema real, veriamos journalctl -p err
        if not self.symptoms_file.exists():
            return None
            
        symptoms = self.symptoms_file.read_text(encoding="utf-8").strip()
        if not symptoms:
            return None
            
        self.log.append("immune_system.threat_detected", actor="monitor", details={"symptoms": symptoms})
        
        try:
            engine = EvolutionEngine(self.project_root)
            current_gen = engine.current_generation()
            
            if current_gen:
                self.log.append("immune_system.rolling_back", actor="monitor", details={"generation": current_gen.generation_id})
                record = engine.rollback()
                self.symptoms_file.unlink() # Cleanup symptoms after rollback
                return {"status": "rolled_back", "mutation_id": record.mutation_id, "reason": symptoms}
            else:
                self.symptoms_file.unlink()
                return {"status": "ignored", "reason": "no active generation to rollback"}
        except Exception as e:
            self.log.append("immune_system.rollback_failed", actor="monitor", details={"error": str(e)})
            return {"status": "error", "error": str(e)}
