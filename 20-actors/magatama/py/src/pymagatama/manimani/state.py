"""Pydantic v2 state contract for the manimani LangGraph (ADR-2605080800).

All boundary IO (XRPC body, LangGraph state, Anthropic tool_use) is
type-checked here. Internal hot-path code consumes only validated
``BaseModel``-derived structs (per ADR-2605080200).
"""

from __future__ import annotations

import enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class SourceKind(str, enum.Enum):
    TEXT = "text"
    URL = "url"
    FILE_REF = "file_ref"


class ProjectKind(str, enum.Enum):
    KNOWLEDGE = "knowledge"
    TASK = "task"
    MEMO = "memo"
    UNSORTED = "unsorted"


class ArtifactKind(str, enum.Enum):
    FACTS_JSONL = "facts_jsonl"
    TODOS_JSONL = "todos_jsonl"
    SUMMARY_TEXT = "summary_text"
    RAW_PASSTHROUGH = "raw_passthrough"
    ERROR = "error"


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    COMPLETED_WITH_ERROR = "completed_with_error"
    FAILED = "failed"


# ── XRPC body shapes ─────────────────────────────────────────────────


class IngestInput(BaseModel):
    """Body of `ai.gftd.apps.manimani.ingest` (Pydantic-validated).

    The CF Worker forwards the parsed JSON body verbatim; this model is
    the canonical wire-format contract.
    """

    source_kind: SourceKind = Field(alias="sourceKind")
    raw_text: Optional[str] = Field(default=None, alias="rawText", max_length=32_000)
    source_uri: Optional[str] = Field(default=None, alias="sourceUri")
    lang: Optional[str] = Field(default=None, max_length=16)
    sensitivity_ord: int = Field(default=2, ge=0, le=3, alias="sensitivityOrd")
    project_hint: Optional[str] = Field(default=None, alias="projectHint", max_length=64)

    model_config = {"populate_by_name": True}


# ── classifier structured output ─────────────────────────────────────


class NewProjectProposal(BaseModel):
    """LLM proposal for a brand-new project bucket."""

    slug: str = Field(max_length=64)
    title: str = Field(max_length=200)
    kind: ProjectKind
    initial_tags: list[str] = Field(default_factory=list, max_length=20)


class ProjectClassification(BaseModel):
    """Classifier (Anthropic structured output) decision payload.

    `confidence < 0.5` is treated as "force new + kind=unsorted" by the
    `classify_project` node (silent mis-classification is worse than
    explicit deferral; user can always re-classify via the
    `ai.gftd.apps.manimani.classify` XRPC).
    """

    decision: str  # "existing" | "new"
    existing_project_id: Optional[str] = None  # vertex_manimani_project.vertex_id
    confidence: float = Field(ge=0.0, le=1.0)
    new_project_proposal: Optional[NewProjectProposal] = None
    rationale: str = Field(max_length=400)


# ── artifact (matches `vertex_manimani_artifact`) ────────────────────


class Artifact(BaseModel):
    """One materialized artifact record."""

    vertex_id: str
    intake_vertex_id: str
    project_vertex_id: str
    run_vertex_id: str
    artifact_kind: ArtifactKind
    content: Optional[str] = None
    model_id: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    error_text: Optional[str] = None
    ts_ms: int


def _merge_artifacts(left: list[Artifact], right: list[Artifact]) -> list[Artifact]:
    """LangGraph reducer: append-only, dedupe by ``vertex_id``."""

    seen: set[str] = {a.vertex_id for a in left}
    out = list(left)
    for a in right:
        if a.vertex_id not in seen:
            out.append(a)
            seen.add(a.vertex_id)
    return out


# ── LangGraph Pregel state ───────────────────────────────────────────


class ManimaniState(BaseModel):
    """LangGraph Pregel state for the manimani 7-node graph.

    Single-step nodes mutate this in-place via ``return {"field": value}``
    (LangGraph merge semantics).  ``artifacts`` uses a custom reducer to
    accumulate across nodes.
    """

    # ── input (set once at START) ──
    input: IngestInput
    actor_did: str
    org_did: str
    intake_vertex_id: str
    run_id: str
    started_at: str  # ISO 8601

    # ── parsed/normalized after parse_input ──
    parsed_text: Optional[str] = None
    intake_hash: Optional[str] = None
    detected_lang: Optional[str] = None
    byte_size: Optional[int] = None

    # ── project classification ──
    classification: Optional[ProjectClassification] = None
    project_vertex_id: Optional[str] = None
    project_kind: Optional[ProjectKind] = None
    project_emerged: bool = False  # true if this run created a new project row

    # ── processor selection ──
    processor: Optional[str] = None  # "extract_facts" | "expand_todo" | "summarize" | "defer_for_user_review"
    model_tier: Optional[str] = None  # "fast" | "balanced" | "deep"

    # ── final artifact records ──
    artifacts: Annotated[list[Artifact], _merge_artifacts] = Field(default_factory=list)

    # ── status / error ──
    current_node: Optional[str] = None
    error_text: Optional[str] = None

    # ── HITL (Phase 4) ──
    awaiting_human_review: bool = False
    human_decision: Optional[str] = None  # "approve" | "reject" | "reassign"
    human_decision_target_project_id: Optional[str] = None
    parent_run_id: Optional[str] = None  # set when this run resumes another

    # ── cost accounting ──
    llm_tokens_in: int = 0
    llm_tokens_out: int = 0
    cost_jpy_micro: int = 0
    classifier_model_id: Optional[str] = None
    processor_model_id: Optional[str] = None
