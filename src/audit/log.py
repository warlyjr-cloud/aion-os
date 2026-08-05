from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from utils.file_lock import FileLock


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
        self._verified_up_to = 0
        self._last_verified_hash = "0" * 64

    def append(
        self,
        event_type: str,
        *,
        actor: str,
        objective_id: str | None = None,
        mutation_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        with FileLock(self.path):
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
        if not self.path.exists():
            return True
        with FileLock(self.path):
            previous_hash = self._last_verified_hash
            current_line = 0
            with self.path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    current_line = line_number
                    if line_number <= self._verified_up_to:
                        continue
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
            self._verified_up_to = current_line
            self._last_verified_hash = previous_hash
        return True

    def _last_hash(self) -> str:
        if not self.path.exists():
            return "0" * 64
        with self.path.open("rb") as f:
            f.seek(0, 2)
            filesize = f.tell()
            if filesize == 0:
                return "0" * 64
            block_size = min(4096, filesize)
            f.seek(filesize - block_size)
            lines = f.read().splitlines()
            if not lines:
                return "0" * 64
            last_line = lines[-1].decode("utf-8")
            if not last_line and len(lines) > 1:
                last_line = lines[-2].decode("utf-8")
            return AuditEvent.model_validate_json(last_line).event_hash if last_line else "0" * 64

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
