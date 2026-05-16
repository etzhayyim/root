"""Pydantic v2 state contract for the SES 案件・状況 LangGraph (ADR-2605120000)."""

from __future__ import annotations

import enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceKind(str, enum.Enum):
    EMAIL = "email"
    MANUAL = "manual"
    EMAIL_CRON = "email_cron"  # Phase 3: Outlook 15-min cron pull


class Jokyo(str, enum.Enum):
    TEIAN = "提案中"
    SENKOCHUU = "選考中"
    KEIYAKU = "契約"
    KADOCHUU = "稼働中"
    SHURYO = "終了"
    MIMOKURI = "見送り"
    CHUTO_SHURYO = "中途終了"


# Forbidden transitions: forward-only, no reactivation from terminal states.
# Key = current jokyo, Value = set of jokyo values that are NOT reachable from current.
FORBIDDEN_TRANSITIONS: dict[str, set[str]] = {
    Jokyo.TEIAN.value: set(),
    Jokyo.SENKOCHUU.value: {Jokyo.TEIAN.value},
    Jokyo.KEIYAKU.value: {Jokyo.TEIAN.value, Jokyo.SENKOCHUU.value},
    Jokyo.KADOCHUU.value: {Jokyo.TEIAN.value, Jokyo.SENKOCHUU.value, Jokyo.KEIYAKU.value},
    Jokyo.SHURYO.value: {
        Jokyo.TEIAN.value, Jokyo.SENKOCHUU.value,
        Jokyo.KEIYAKU.value, Jokyo.KADOCHUU.value,
    },
    Jokyo.MIMOKURI.value: {
        Jokyo.TEIAN.value, Jokyo.SENKOCHUU.value,
        Jokyo.KEIYAKU.value, Jokyo.KADOCHUU.value,
    },
    Jokyo.CHUTO_SHURYO.value: {
        Jokyo.TEIAN.value, Jokyo.SENKOCHUU.value,
        Jokyo.KEIYAKU.value, Jokyo.KADOCHUU.value,
    },
}


def is_forbidden_transition(current: str | None, next_: str) -> bool:
    """Return True if transitioning from *current* to *next_* is forbidden.

    None current means no prior jokyo — always allowed (new anken).
    """
    if current is None:
        return False
    forbidden = FORBIDDEN_TRANSITIONS.get(current, set())
    return next_ in forbidden


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERROR = "completed_with_error"
    FAILED = "failed"


# ── LLM structured-output contract ───────────────────────────────────


class AnkenExtraction(BaseModel):
    """Anthropic structured-output shape for SES案件 email extraction.

    confidence < 0.6 → discard (not a genuine SES案件 email).
    All yen amounts are integer (AT Protocol lexicon has no float type).
    """

    client_name: str
    client_company: Optional[str] = None
    skill_requirements: list[str] = Field(default_factory=list)
    jokyo: Jokyo
    start_month: Optional[str] = None  # YYYY-MM
    end_month: Optional[str] = None    # YYYY-MM
    rate_lower_yen: Optional[int] = None
    rate_upper_yen: Optional[int] = None
    work_location: Optional[str] = None
    remote_ok: Optional[bool] = None
    engineer_name: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=400)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(max_length=200)


# ── LangGraph Pregel state ────────────────────────────────────────────


class SesIngestState(BaseModel):
    """LangGraph Pregel state for the SES 6-node graph.

    Nodes return ``{"field": value}`` dicts; LangGraph merges them into
    this state object per transition.
    """

    # ── input (set once at START) ──
    source_kind: SourceKind
    raw_text: str
    actor_did: str
    org_did: str
    run_id: str
    started_at: str  # ISO 8601
    source_email_subject: Optional[str] = None
    source_email_from: Optional[str] = None

    # ── parse_source output ──
    parsed_text: Optional[str] = None

    # ── classify_anken output ──
    anken_decision: Optional[str] = None  # "new" | "existing" | "discard"
    existing_anken_id: Optional[str] = None
    existing_jokyo_current: Optional[str] = None  # jokyo of matched anken

    # ── extract_details output ──
    extraction: Optional[AnkenExtraction] = None

    # ── update_jokyo output ──
    jokyo_appended: bool = False
    jokyo_skipped: bool = False

    # ── persist output ──
    anken_vertex_id: Optional[str] = None
    jokyo_vertex_id: Optional[str] = None

    # ── run metadata ──
    status: RunStatus = RunStatus.PENDING
    current_node: Optional[str] = None
    error_text: Optional[str] = None
    model_ids_used: list[str] = Field(default_factory=list)
    tokens_total: int = 0
