from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class SystemGenome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    generation_id: str
    parent_generation_id: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    configuration_hash: str
    mutation_id: str
    simulated: bool = True

    def export(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")
