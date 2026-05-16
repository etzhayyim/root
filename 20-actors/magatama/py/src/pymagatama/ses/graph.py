"""LangGraph StateGraph for the SES 案件・状況 ingest pipeline (ADR-2605120000).

6-node Pregel pipeline:

    parse_source
        ↓
    classify_anken
        ↓
    extract_details
        ↓
    update_jokyo
        ↓
    persist
        ↓
    emit_audit
        ↓
       END
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from pymagatama.ses.state import (
    AnkenExtraction,
    Jokyo,
    RunStatus,
    SesIngestState,
    SourceKind,
    is_forbidden_transition,
)

try:  # langgraph 0.2.x
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover — runtime image always has it
    StateGraph = None  # type: ignore[assignment]
    END = "__END__"

_log = logging.getLogger(__name__)


# ── node implementations ──────────────────────────────────────────────


def parse_source(state: SesIngestState) -> dict[str, Any]:
    """Normalize raw input to ``parsed_text``."""
    raw = state.raw_text
    if not raw:
        return {
            "error_text": "raw_text is empty",
            "status": RunStatus.FAILED,
            "current_node": "parse_source",
        }

    return {
        "parsed_text": raw.strip(),
        "status": RunStatus.RUNNING,
        "current_node": "parse_source",
    }


def classify_anken(state: SesIngestState) -> dict[str, Any]:
    """Determine whether this text is a new 案件, update to existing, or discard."""
    if state.error_text:
        return {"current_node": "classify_anken"}

    parsed = state.parsed_text or ""
    if not parsed:
        return {
            "anken_decision": "discard",
            "current_node": "classify_anken",
        }

    try:
        from pymagatama.ses.classifier import classify_anken as _classify
        decision, existing_id, existing_jokyo = _classify(
            state.actor_did,
            "",  # client_name unknown until extract_details; use empty for now
            parsed,
        )
    except Exception as exc:
        _log.warning("[ses][classify_anken] failed: %s", exc)
        # Fall back to "new" — extraction will set confidence
        decision, existing_id, existing_jokyo = "new", None, None

    return {
        "anken_decision": decision,
        "existing_anken_id": existing_id,
        "existing_jokyo_current": existing_jokyo,
        "current_node": "classify_anken",
    }


def extract_details(state: SesIngestState) -> dict[str, Any]:
    """Extract structured AnkenExtraction from parsed_text via LLM."""
    if state.error_text or state.anken_decision == "discard":
        return {"current_node": "extract_details"}

    try:
        from pymagatama.ses.extractor import extract_anken_with_meta
        extraction, model_id, tokens = extract_anken_with_meta(
            state.parsed_text or ""
        )
    except Exception as exc:
        _log.warning("[ses][extract_details] failed: %s", exc)
        return {
            "extraction": None,
            "current_node": "extract_details",
        }

    if extraction is None:
        return {
            "extraction": None,
            "current_node": "extract_details",
        }

    model_ids = list(state.model_ids_used)
    if model_id:
        model_ids.append(model_id)

    # Refine classify decision using extracted client_name
    if state.anken_decision == "new" and extraction.client_name:
        try:
            from pymagatama.ses.classifier import classify_anken as _classify
            decision, existing_id, existing_jokyo = _classify(
                state.actor_did,
                extraction.client_name,
                state.parsed_text or "",
            )
        except Exception:
            decision = "new"
            existing_id = None
            existing_jokyo = None

        return {
            "extraction": extraction,
            "anken_decision": decision,
            "existing_anken_id": existing_id,
            "existing_jokyo_current": existing_jokyo,
            "model_ids_used": model_ids,
            "tokens_total": state.tokens_total + tokens,
            "current_node": "extract_details",
        }

    return {
        "extraction": extraction,
        "model_ids_used": model_ids,
        "tokens_total": state.tokens_total + tokens,
        "current_node": "extract_details",
    }


def update_jokyo(state: SesIngestState) -> dict[str, Any]:
    """Validate state transition and set jokyo_appended / jokyo_skipped."""
    if state.error_text or state.anken_decision == "discard":
        return {"current_node": "update_jokyo"}

    extraction = state.extraction
    if not extraction or extraction.confidence < 0.6:
        return {
            "jokyo_appended": False,
            "jokyo_skipped": True,
            "current_node": "update_jokyo",
        }

    current_jokyo = state.existing_jokyo_current
    next_jokyo = extraction.jokyo.value

    if is_forbidden_transition(current_jokyo, next_jokyo):
        _log.info(
            "[ses][update_jokyo] forbidden transition %s→%s for anken %s",
            current_jokyo, next_jokyo, state.existing_anken_id,
        )
        return {
            "jokyo_appended": False,
            "jokyo_skipped": True,
            "current_node": "update_jokyo",
        }

    return {
        "jokyo_appended": True,
        "jokyo_skipped": False,
        "current_node": "update_jokyo",
    }


def persist(state: SesIngestState) -> dict[str, Any]:
    """INSERT into vertex_ses_* via persistence.py."""
    if state.error_text or state.anken_decision == "discard":
        return {
            "status": RunStatus.COMPLETED_WITH_ERROR if state.error_text else RunStatus.COMPLETED,
            "current_node": "persist",
        }

    if not state.jokyo_appended:
        return {
            "status": RunStatus.COMPLETED,
            "current_node": "persist",
        }

    extraction = state.extraction
    if not extraction:
        return {
            "error_text": "extraction missing at persist",
            "status": RunStatus.FAILED,
            "current_node": "persist",
        }

    from pymagatama.ses import persistence as _p

    try:
        # Anken: insert new or use existing
        if state.anken_decision == "new":
            anken_vid = _p.insert_anken(
                state.actor_did,
                state.org_did,
                extraction,
                source_kind=state.source_kind.value,
            )
        else:
            anken_vid = state.existing_anken_id or _p.insert_anken(
                state.actor_did,
                state.org_did,
                extraction,
                source_kind=state.source_kind.value,
            )

        # Jokyo: always append
        jokyo_vid = _p.insert_jokyo(
            state.actor_did,
            state.org_did,
            anken_vid,
            extraction.jokyo.value,
            state.run_id,
            extraction.rationale,
        )

        # Optional client edge
        if extraction.client_company:
            client_vid = _p.upsert_client(
                state.actor_did, state.org_did, extraction.client_company
            )
            _p.insert_edge_anken_client(
                state.actor_did, state.org_did, anken_vid, client_vid
            )

        # Optional engineer edge
        if extraction.engineer_name:
            eng_vid = _p.upsert_engineer(
                state.actor_did, state.org_did, extraction.engineer_name
            )
            _p.insert_edge_anken_engineer(
                state.actor_did, state.org_did, anken_vid, eng_vid,
                confidence=extraction.confidence,
            )

    except Exception as exc:
        _log.exception("[ses][persist] failed")
        return {
            "error_text": str(exc)[:200],
            "status": RunStatus.FAILED,
            "current_node": "persist",
        }

    return {
        "anken_vertex_id": anken_vid,
        "jokyo_vertex_id": jokyo_vid,
        "status": RunStatus.COMPLETED,
        "current_node": "persist",
    }


def emit_audit(state: SesIngestState) -> dict[str, Any]:
    """Persist vertex_ses_run and emit audit record."""
    from pymagatama.ses import persistence as _p

    try:
        _p.insert_run(
            state.actor_did,
            state.org_did,
            state.run_id,
            source_kind=state.source_kind.value,
            anken_decision=state.anken_decision,
            anken_vertex_id=state.anken_vertex_id,
            jokyo_vertex_id=state.jokyo_vertex_id,
            jokyo_appended=state.jokyo_appended,
            jokyo_skipped=state.jokyo_skipped,
            status=state.status.value,
            error_text=state.error_text,
            model_ids=list(state.model_ids_used),
            tokens_total=state.tokens_total,
            started_at=state.started_at,
        )
    except Exception as exc:
        _log.warning("[ses][emit_audit] run record insert failed: %s", exc)

    return {"current_node": "emit_audit"}


# ── graph factory ─────────────────────────────────────────────────────


def build_graph(*, checkpointer: Any = None):
    """Compile the SES ingest StateGraph.

    Args:
      checkpointer: optional ``BaseCheckpointSaver``. Pass
        ``RisingWaveCheckpointSaver`` for production (Phase 3).
        Pass ``None`` for unit tests.
    """
    if StateGraph is None:  # pragma: no cover
        raise RuntimeError("langgraph not installed; pip install langgraph")

    g: Any = StateGraph(SesIngestState)
    g.add_node("parse_source", parse_source)
    g.add_node("classify_anken", classify_anken)
    g.add_node("extract_details", extract_details)
    g.add_node("update_jokyo", update_jokyo)
    g.add_node("persist", persist)
    g.add_node("emit_audit", emit_audit)

    g.set_entry_point("parse_source")
    g.add_edge("parse_source", "classify_anken")
    g.add_edge("classify_anken", "extract_details")
    g.add_edge("extract_details", "update_jokyo")
    g.add_edge("update_jokyo", "persist")
    g.add_edge("persist", "emit_audit")
    g.add_edge("emit_audit", END)

    return g.compile(checkpointer=checkpointer) if checkpointer is not None else g.compile()
