from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IntentContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    objective_id: str
    objective: str = Field(min_length=5, max_length=2_000)
    context: str
    expected_result: str
    constraints: list[str]
    authorized_data: list[str]
    prohibited_data: list[str]
    acceptable_risk: Literal[0, 1, 2, 3]
    resources: dict[str, int]
    priority: Literal["low", "normal", "high"] = "normal"
    metrics: dict[str, float]
    stop_criteria: list[str]
    permissions: list[str]
    approval_required: bool = True
    reversal: str
    assumptions: list[str]
