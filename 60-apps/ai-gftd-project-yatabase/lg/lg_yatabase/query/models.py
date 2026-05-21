"""Pydantic models for deploy-first query pattern spec."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator


class VertexStep(BaseModel):
    model_config = ConfigDict(strict=True)
    kind: Literal["vertex"]
    label: str  # maps to graphar.vertex_{label}
    alias: str  # required — caller must name it


class EdgeStep(BaseModel):
    model_config = ConfigDict(strict=True)
    kind: Literal["edge"]
    label: str  # maps to graphar.edge_{label}
    direction: Literal["out", "in", "both"] = "out"


Step = VertexStep | EdgeStep


class PatternSpec(BaseModel):
    """Validated graph traversal pattern."""
    model_config = ConfigDict(strict=False)

    steps: list[Step]
    select: list[str]        # ["a.vertex_id", "b.name", ...]
    index_on: list[str]      # ["a.vertex_id"]
    static_where: dict | None = None  # {"field": "a.status", "op": "eq", "value": "active"}

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: list[Step]) -> list[Step]:
        if len(v) < 3:
            raise ValueError("steps must have at least 3 elements (1 hop: vertex-edge-vertex)")
        if len(v) > 9:
            raise ValueError("steps must have at most 9 elements (4 hops)")
        if len(v) % 2 == 0:
            raise ValueError("steps length must be odd (must start and end with vertex)")
        for i, step in enumerate(v):
            expected = "vertex" if i % 2 == 0 else "edge"
            if step.kind != expected:
                raise ValueError(f"step[{i}] must be kind='{expected}', got '{step.kind}'")
        return v


class DeployQueryInput(BaseModel):
    model_config = ConfigDict(strict=False)
    queryId: str
    stepsJson: str
    selectJson: str | None = None
    indexOnJson: str | None = None
    staticWhereJson: str | None = None


class ExecuteQueryInput(BaseModel):
    model_config = ConfigDict(strict=False)
    queryId: str
    bindJson: str | None = None
    limit: int = 1000
    offset: int = 0
    timeoutMs: int = 25000


class DeleteQueryInput(BaseModel):
    model_config = ConfigDict(strict=False)
    queryId: str


class ListQueriesInput(BaseModel):
    model_config = ConfigDict(strict=False)
    limit: int = 50
    cursor: str | None = None
