from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from actions import SemanticAction
from utils.file_lock import FileLock

from .manager import CapabilityError, CapabilityGrant


class StoredGrant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    grant: CapabilityGrant
    uses_consumed: int = 0
    revoked: bool = False
    revoked_by: str | None = None
    revoked_reason: str | None = None


class CapabilityStore:
    """Durable, file-backed capability grants - unlike `CapabilityManager`
    (in-memory, scoped to a single `plan()`/`promote()` call), grants here
    persist across processes and can be issued to a specific tenant/team
    ahead of time, checked for real wall-clock expiration, and explicitly
    revoked. This is what makes capability scoping real for more than one
    caller in the same Python process.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def issue(self, grant: CapabilityGrant) -> StoredGrant:
        with FileLock(self.path):
            records = self._read()
            if grant.grant_id in records:
                raise CapabilityError(f"duplicate capability grant: {grant.grant_id}")
            stored = StoredGrant(grant=grant)
            records[grant.grant_id] = stored
            self._write(records)
            return stored

    def revoke(self, grant_id: str, *, revoked_by: str, reason: str) -> StoredGrant:
        if not revoked_by.strip() or not reason.strip():
            raise ValueError("revoked_by and reason are required")
        with FileLock(self.path):
            records = self._read()
            existing = records.get(grant_id)
            if existing is None:
                raise CapabilityError(f"unknown capability grant: {grant_id}")
            updated = existing.model_copy(
                update={"revoked": True, "revoked_by": revoked_by, "revoked_reason": reason}
            )
            records[grant_id] = updated
            self._write(records)
            return updated

    def authorize(self, action: SemanticAction, *, grantee: str) -> CapabilityGrant:
        now = datetime.now(UTC)
        with FileLock(self.path):
            records = self._read()
            for grant_id, stored in records.items():
                grant = stored.grant
                if (
                    not stored.revoked
                    and grant.capability == action.required_capability
                    and grant.grantee == grantee
                    and grant.objective_id == action.objective_id
                    and grant.expires_at > now
                    and stored.uses_consumed < grant.remaining_uses
                ):
                    records[grant_id] = stored.model_copy(
                        update={"uses_consumed": stored.uses_consumed + 1}
                    )
                    self._write(records)
                    return grant
        raise CapabilityError(f"no valid grant for {action.required_capability!r}")

    def list_active(self, *, at: datetime | None = None) -> list[CapabilityGrant]:
        check_time = at or datetime.now(UTC)
        records = self._read()
        return [
            stored.grant
            for stored in records.values()
            if not stored.revoked
            and stored.grant.expires_at > check_time
            and stored.uses_consumed < stored.grant.remaining_uses
        ]

    def _read(self) -> dict[str, StoredGrant]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        return {grant_id: StoredGrant.model_validate(value) for grant_id, value in raw.items()}

    def _write(self, records: dict[str, StoredGrant]) -> None:
        payload = {grant_id: stored.model_dump(mode="json") for grant_id, stored in records.items()}
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)
