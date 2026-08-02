"""Red-team result models with stable, JSON-compatible serialization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FindingSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Finding:
    code: str
    severity: FindingSeverity
    message: str
    action_id: str | None = None

    @property
    def blocks_scoring(self) -> bool:
        return self.severity in {FindingSeverity.HIGH, FindingSeverity.CRITICAL}

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "action_id": self.action_id,
            "blocks_scoring": self.blocks_scoring,
        }


@dataclass(frozen=True, slots=True)
class RedTeamReport:
    findings: tuple[Finding, ...]

    @property
    def blocked(self) -> bool:
        return any(finding.blocks_scoring for finding in self.findings)

    def has_code(self, code: str) -> bool:
        return any(finding.code == code for finding in self.findings)

    def to_dict(self) -> dict[str, object]:
        return {
            "blocked": self.blocked,
            "findings": [finding.to_dict() for finding in self.findings],
        }
