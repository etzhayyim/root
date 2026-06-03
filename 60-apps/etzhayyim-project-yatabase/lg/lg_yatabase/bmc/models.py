"""Pydantic v2 schemas matching the BMC Lexicon JSON shapes.

threshold / baseline / measured_value travel on the wire as decimal
strings (AT Lexicon does not support float per root CLAUDE.md §"AT
Lexicon で `type: number` を使用 禁止"). We convert to float at the
repository boundary.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

BlockKey = Literal[
    "customerSegments",
    "valuePropositions",
    "channels",
    "customerRelationships",
    "revenueStreams",
    "keyResources",
    "keyActivities",
    "keyPartnerships",
    "costStructure",
]

BMC_BLOCK_KEYS: tuple[BlockKey, ...] = (
    "customerSegments",
    "valuePropositions",
    "channels",
    "customerRelationships",
    "revenueStreams",
    "keyResources",
    "keyActivities",
    "keyPartnerships",
    "costStructure",
)

HypothesisStatus = Literal["pending", "active", "completed", "killed"]
DecisionAction = Literal["persevere", "pivot", "kill", "extend"]


def _decimal_str(v: str) -> float:
    try:
        return float(v)
    except (TypeError, ValueError) as e:
        raise ValueError(f"expected decimal string, got {v!r}") from e


# ── Inputs ─────────────────────────────────────────────────────────────


class AppendStateInput(BaseModel):
    canvas_json: str = Field(alias="canvasJson", max_length=65536)
    rationale: str = Field(max_length=4096)
    source: str = Field(max_length=128)
    created_by: str | None = Field(default=None, alias="createdBy", max_length=256)

    model_config = {"populate_by_name": True}


class AddHypothesisInput(BaseModel):
    slug: str = Field(max_length=256)
    block: BlockKey
    statement: str = Field(max_length=1024)
    metric: str = Field(max_length=256)
    metric_query: str = Field(alias="metricQuery", max_length=4096)
    threshold: str
    baseline: str
    deadline_iso: str = Field(alias="deadlineIso")
    min_sample: int = Field(alias="minSample", ge=0)
    authored_by: str | None = Field(default=None, alias="authoredBy", max_length=256)
    auto_apply_pivot: bool = Field(default=False, alias="autoApplyPivot")

    model_config = {"populate_by_name": True}

    @field_validator("threshold", "baseline")
    @classmethod
    def _check_decimal(cls, v: str) -> str:
        _decimal_str(v)
        return v


class SetHypothesisStatusInput(BaseModel):
    slug: str
    next_status: HypothesisStatus = Field(alias="nextStatus")
    reason: str | None = Field(default=None, max_length=1024)
    iteration_vertex_id: str | None = Field(default=None, alias="iterationVertexId")
    authored_by: str | None = Field(default=None, alias="authoredBy", max_length=256)

    model_config = {"populate_by_name": True}


class IterateInput(BaseModel):
    hypothesis_slug: str | None = Field(default=None, alias="hypothesisSlug")
    dry_run: bool = Field(default=False, alias="dryRun")

    model_config = {"populate_by_name": True}


# ── Output rows ────────────────────────────────────────────────────────


class StateHeadRow(BaseModel):
    vertex_id: str
    version: int
    canvas_json: str
    rationale: str | None
    source: str
    created_by: str
    created_at: str


class HypothesisRow(BaseModel):
    vertex_id: str
    slug: str
    block: str
    statement: str
    metric: str
    metric_query: str
    threshold: float
    baseline: float
    deadline_iso: str
    min_sample: int
    authored_by: str
    auto_apply_pivot: bool
    status: HypothesisStatus
    status_at: str | None
    created_at: str


class IterationRow(BaseModel):
    vertex_id: str
    hypothesis_slug: str
    iteration_no: int
    bmc_version_in: int
    bmc_version_out: int
    measured_value: float
    measured_at: str
    measurement_source: str
    passed: bool
    notes: str | None
    created_at: str


class DecisionRow(BaseModel):
    vertex_id: str
    iteration_vertex_id: str
    hypothesis_slug: str
    action: DecisionAction
    rationale: str
    authored_by: str
    applied_at: str
    created_at: str


class BlockHealthRow(BaseModel):
    block: BlockKey
    hyp_total: int
    hyp_active: int
    hyp_completed: int
    hyp_killed: int
    avg_measured: float | None
    last_iter_at: str | None
