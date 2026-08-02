from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from actions import SemanticAction


class CapabilityError(PermissionError):
    pass


class CapabilityGrant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    grant_id: str
    capability: str = Field(min_length=3, max_length=512)
    grantee: str
    objective_id: str
    expires_at: datetime
    remaining_uses: int = Field(default=1, ge=1, le=100)
    delegable: bool = False


class CapabilityManager:
    """In-memory, fail-closed capability checker for a single evolution run."""

    def __init__(self, grants: list[CapabilityGrant] | None = None) -> None:
        self._grants = {grant.grant_id: grant for grant in grants or []}
        self._uses = {grant.grant_id: 0 for grant in grants or []}

    def add(self, grant: CapabilityGrant) -> None:
        if grant.grant_id in self._grants:
            raise CapabilityError(f"duplicate capability grant: {grant.grant_id}")
        self._grants[grant.grant_id] = grant
        self._uses[grant.grant_id] = 0

    def authorize(self, action: SemanticAction, *, grantee: str) -> CapabilityGrant:
        now = datetime.now(UTC)
        for grant in self._grants.values():
            if (
                grant.capability == action.required_capability
                and grant.grantee == grantee
                and grant.objective_id == action.objective_id
                and grant.expires_at > now
                and self._uses[grant.grant_id] < grant.remaining_uses
            ):
                self._uses[grant.grant_id] += 1
                return grant
        raise CapabilityError(f"no valid grant for {action.required_capability!r}")

    def list_active(self, *, at: datetime | None = None) -> list[CapabilityGrant]:
        check_time = at or datetime.now(UTC)
        return [grant for grant in self._grants.values() if grant.expires_at > check_time]
