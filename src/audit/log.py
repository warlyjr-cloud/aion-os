from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: str
    actor: str
    objective_id: str | None = None
    mutation_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    previous_hash: str
    event_hash: str


class AuditLog:
    """Append-only JSONL audit log with a deterministic hash chain."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        event_type: str,
        *,
        actor: str,
        objective_id: str | None = None,
        mutation_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        previous_hash = self._last_hash()
        timestamp = datetime.now(UTC)
        unsigned = self._unsigned_payload(
            timestamp=timestamp,
            event_type=event_type,
            actor=actor,
            objective_id=objective_id,
            mutation_id=mutation_id,
            details=details or {},
            previous_hash=previous_hash,
        )
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
        event_hash = hashlib.sha256(canonical.encode()).hexdigest()
        event = AuditEvent(**unsigned, event_hash=event_hash)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(event.model_dump_json() + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def verify(self) -> bool:
        previous_hash = "0" * 64
        if not self.path.exists():
            return True
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            event = AuditEvent.model_validate_json(line)
            if event.previous_hash != previous_hash:
                raise ValueError(f"broken audit chain at line {line_number}")
            unsigned = self._unsigned_payload(
                timestamp=event.timestamp,
                event_type=event.event_type,
                actor=event.actor,
                objective_id=event.objective_id,
                mutation_id=event.mutation_id,
                details=event.details,
                previous_hash=event.previous_hash,
            )
            canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
            actual = hashlib.sha256(canonical.encode()).hexdigest()
            if actual != event.event_hash:
                raise ValueError(f"tampered audit event at line {line_number}")
            previous_hash = event.event_hash
        return True

    def _last_hash(self) -> str:
        if not self.path.exists():
            return "0" * 64
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return AuditEvent.model_validate_json(lines[-1]).event_hash if lines else "0" * 64

    @staticmethod
    def _unsigned_payload(
        *,
        timestamp: datetime,
        event_type: str,
        actor: str,
        objective_id: str | None,
        mutation_id: str | None,
        details: dict[str, Any],
        previous_hash: str,
    ) -> dict[str, Any]:
        return {
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "actor": actor,
            "objective_id": objective_id,
            "mutation_id": mutation_id,
            "details": details,
            "previous_hash": previous_hash,
        }
