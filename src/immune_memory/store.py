from __future__ import annotations

import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from utils.file_lock import FileLock


class MemoryTrust(StrEnum):
    UNTRUSTED = "untrusted"
    OBSERVED = "observed"
    VERIFIED = "verified"
    APPROVED = "approved"


class MemoryClass(StrEnum):
    EXTERNAL_CONTENT = "external_content"
    OBSERVATION = "observation"
    PREFERENCE = "preference"
    VERIFIED_FACT = "verified_fact"
    APPROVED_DECISION = "approved_decision"
    CANDIDATE_EXPERIENCE = "candidate_experience"
    VALIDATED_EXPERIENCE = "validated_experience"
    SAFETY_RULE = "safety_rule"


class MemoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory_id: str
    origin: str
    provenance: list[str]
    memory_class: MemoryClass
    trust: MemoryTrust
    content: str
    context: str
    evidence: list[str] = Field(default_factory=list)
    scope: str
    expires_at: datetime | None = None
    generation_id: str | None = None
    history: list[str] = Field(default_factory=list)
    quarantined: bool = False
    action_authority: bool = False
    reversal: str


class MemoryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, entry: MemoryEntry) -> None:
        if entry.memory_class is MemoryClass.SAFETY_RULE:
            raise ValueError(
                "safety rules belong to the immutable constitution, not evolving memory"
            )
        if entry.trust is MemoryTrust.UNTRUSTED and entry.action_authority:
            raise ValueError("untrusted memory cannot carry action authority")

        with FileLock(self.path):
            entries = {item.memory_id: item for item in self._read_all()}
            if entry.memory_id in entries:
                raise ValueError(f"duplicate memory id: {entry.memory_id}")
            self._append(entry)

    def promote(self, memory_id: str, *, evidence: str, approved_by: str) -> MemoryEntry:
        with FileLock(self.path):
            entries = {item.memory_id: item for item in self._read_all()}
            entry = entries[memory_id]
            if entry.quarantined:
                raise ValueError("quarantined memory cannot be promoted")
            if not evidence.strip() or not approved_by.strip():
                raise ValueError("promotion requires evidence and an approver")
            entry.trust = MemoryTrust.VERIFIED
            entry.evidence.append(evidence)
            entry.history.append(f"verified by {approved_by} at {datetime.now(UTC).isoformat()}")
            self._append(entry)
            return entry

    def quarantine(self, memory_id: str, *, reason: str) -> MemoryEntry:
        with FileLock(self.path):
            entries = {item.memory_id: item for item in self._read_all()}
            entry = entries[memory_id]
            entry.quarantined = True
            entry.action_authority = False
            entry.history.append(f"quarantined: {reason}")
            self._append(entry)
            return entry

    def list_all(self) -> list[MemoryEntry]:
        with FileLock(self.path):
            entries = {item.memory_id: item for item in self._read_all()}
            return list(entries.values())

    def _read_all(self) -> list[MemoryEntry]:
        if not self.path.exists():
            return []
        return [
            MemoryEntry.model_validate_json(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def _append(self, entry: MemoryEntry) -> None:
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(entry.model_dump_json() + "\n")
            handle.flush()
            os.fsync(handle.fileno())
