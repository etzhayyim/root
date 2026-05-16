"""LangGraph StateGraph for manimani (ADR-2605080800).

7-node Pregel pipeline:

    parse_input
        ↓
    classify_project
        ↓
    route_processor
       ┌────────────┬────────┴───────┬────────────────────┐
       ▼            ▼                ▼                    ▼
    extract_facts  expand_todo   summarize     defer_for_user_review
       └────────────┴────────────────┴────────────────────┘
                                ▼
                       persist_artifact
                                ▼
                           emit_audit
                                ▼
                              END

Per ADR-2605080600 the graph runs inside Granian/LangGraph Server.
Phase 1 (this file): in-process state only. Phase 2 will plug a custom
``BaseCheckpointSaver`` writing to ``vertex_manimani_run.checkpoint_json``.
HITL via ``interrupt()`` is not used in Phase 1.
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Any

from pymagatama.manimani.classifier import classify_project as _classify_project
from pymagatama.manimani.persistence import (
    get_project_by_slug,
    get_project_by_vertex_id,
    insert_artifacts,
    insert_belongs_to_edge,
    insert_intake,
    insert_project,
    list_active_projects_for_actor,
)
from pymagatama.manimani.processors import (
    PROCESSOR_BY_KIND,
    PROCESSOR_DEFAULT_TIER,
    defer_for_user_review as defer_for_user_review_fn,
    expand_todo as expand_todo_fn,
    extract_facts as extract_facts_fn,
    summarize as summarize_fn,
)
from pymagatama.manimani.state import (
    Artifact,
    ArtifactKind,
    ManimaniState,
    NewProjectProposal,
    ProjectKind,
    SourceKind,
)

try:  # langgraph 0.2.x
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover — runtime image always has it
    StateGraph = None  # type: ignore[assignment]
    END = "__END__"


# ── node implementations ─────────────────────────────────────────────


def parse_input(state: ManimaniState) -> dict[str, Any]:
    """Normalize raw input to ``parsed_text`` + ``intake_hash``.

    Phase 3 behavior:
      - ``text``     → use raw_text verbatim
      - ``url``      → HTTP GET + readable-text extraction (sources.fetch_url)
      - ``file_ref`` → b2:// SigV4 GET + content-type sniff (sources.fetch_b2_file_ref)

    Fetch failures do NOT raise. They store the URI as ``parsed_text``
    and continue (the intake row + a deferred artifact still land), so
    a transient upstream outage cannot lose user input.
    """

    inp = state.input
    parsed: str = ""
    raw_byte_size: int | None = None

    if inp.source_kind is SourceKind.TEXT:
        if not inp.raw_text:
            return {"error_text": "rawText required when sourceKind=text", "current_node": "parse_input"}
        parsed = inp.raw_text
        raw_byte_size = len(parsed.encode("utf-8"))

    elif inp.source_kind is SourceKind.URL:
        if not inp.source_uri:
            return {"error_text": "sourceUri required when sourceKind=url", "current_node": "parse_input"}
        from pymagatama.manimani.sources import fetch_url
        result = fetch_url(inp.source_uri)
        # Always advance: on fetch error keep the URI as parsed_text so
        # downstream nodes still produce an artifact (defer_for_user_review).
        parsed = result.parsed_text or inp.source_uri
        raw_byte_size = result.raw_byte_size

    elif inp.source_kind is SourceKind.FILE_REF:
        if not inp.source_uri:
            return {"error_text": "sourceUri required when sourceKind=file_ref", "current_node": "parse_input"}
        from pymagatama.manimani.sources import fetch_b2_file_ref
        result = fetch_b2_file_ref(inp.source_uri)
        parsed = result.parsed_text or inp.source_uri
        raw_byte_size = result.raw_byte_size

    else:  # pragma: no cover
        return {"error_text": f"unknown sourceKind={inp.source_kind!r}", "current_node": "parse_input"}

    if raw_byte_size is None:
        raw_byte_size = len(parsed.encode("utf-8"))
    intake_hash = hashlib.sha256(parsed.encode("utf-8")).hexdigest()
    return {
        "parsed_text": parsed,
        "intake_hash": intake_hash,
        "detected_lang": inp.lang,  # Phase 3+: auto-detect when None
        "byte_size": raw_byte_size,
        "current_node": "parse_input",
    }


def classify_project(state: ManimaniState) -> dict[str, Any]:
    """LLM-driven classification with optional HITL gate (Phase 4).

    Loads top-N active projects for the actor, asks the classifier (stub
    in Phase 1, Anthropic in Phase 2), then either binds the intake to
    an existing project or emerges a new one.

    HITL (Phase 4, opt-in via ``MANIMANI_HITL_NEW_PROJECT=1``):
      When the classifier proposes a brand-new project (no slug match in
      RW), the node returns ``awaiting_human_review=True`` and a
      conditional edge routes the run to a terminal ``await_human_review``
      node. The user later calls ``ai.gftd.apps.manimani.resumeRun`` with
      a decision; the resume path re-invokes the graph with
      ``state.human_decision`` set, which short-circuits the HITL gate.
    """

    if state.error_text:
        return {"current_node": "classify_project"}

    parsed = state.parsed_text or ""

    # ── resume path: user already decided, apply and skip HITL ────────
    if state.human_decision:
        decision = state.human_decision
        if decision == "reject":
            return {
                "error_text": "user rejected new project emergence",
                "current_node": "classify_project",
            }
        if decision == "reassign":
            target = state.human_decision_target_project_id
            if not target:
                return {
                    "error_text": "human_decision=reassign requires target_project_id",
                    "current_node": "classify_project",
                }
            project = get_project_by_vertex_id(
                actor_did=state.actor_did, org_did=state.org_did, vertex_id=target,
            )
            try:
                project_kind = ProjectKind(str((project or {}).get("kind") or "unsorted"))
            except ValueError:
                project_kind = ProjectKind.UNSORTED
            return {
                "classification": state.classification,
                "project_vertex_id": target,
                "project_kind": project_kind,
                "project_emerged": False,
                "awaiting_human_review": False,
                "current_node": "classify_project",
            }
        # decision == "approve" → continue with whatever the classifier
        # had previously proposed (state.classification carries the
        # proposal across the resume).
        if not state.classification:
            return {
                "error_text": "human_decision=approve but classification missing on resume",
                "current_node": "classify_project",
            }
        classification = state.classification
        existing = []  # not needed on the approve path
    else:
        # ── normal path ────────────────────────────────────────────────
        existing = list_active_projects_for_actor(
            actor_did=state.actor_did, org_did=state.org_did, limit=20,
        )
        classification = _classify_project(
            parsed_text=parsed,
            actor_did=state.actor_did,
            existing_projects=existing,
            project_hint=state.input.project_hint,
        )

    project_vertex_id: str | None = None
    project_kind: ProjectKind = ProjectKind.UNSORTED
    project_emerged = False

    if classification.decision == "existing" and classification.existing_project_id:
        project_vertex_id = classification.existing_project_id
        for proj in existing:
            if proj.get("vertex_id") == project_vertex_id:
                try:
                    project_kind = ProjectKind(proj.get("kind") or "unsorted")
                except ValueError:
                    project_kind = ProjectKind.UNSORTED
                break
    else:
        # decision == "new" OR fallback
        proposal = classification.new_project_proposal or NewProjectProposal(
            slug="unsorted", title="Unsorted", kind=ProjectKind.UNSORTED
        )
        if classification.confidence < 0.5:
            proposal = proposal.model_copy(update={"kind": ProjectKind.UNSORTED})

        existing_match = get_project_by_slug(
            actor_did=state.actor_did,
            org_did=state.org_did,
            slug=proposal.slug,
        )
        if existing_match:
            project_vertex_id = str(existing_match.get("vertex_id") or "")
            try:
                project_kind = ProjectKind(existing_match.get("kind") or proposal.kind.value)
            except ValueError:
                project_kind = proposal.kind
        else:
            # ── HITL gate: about to emerge a brand-new project ──────────
            if _hitl_new_project_enabled() and not state.human_decision:
                return {
                    "classification": classification,
                    "project_vertex_id": None,
                    "project_kind": ProjectKind.UNSORTED,
                    "project_emerged": False,
                    "awaiting_human_review": True,
                    "current_node": "classify_project",
                }
            project_vertex_id = _make_project_vertex_id(state.actor_did, proposal.slug)
            project_did = _make_project_did(proposal.slug)
            project_kind = proposal.kind
            project_emerged = True
            insert_project(
                project_vertex_id=project_vertex_id,
                project_did=project_did,
                slug=proposal.slug,
                title=proposal.title,
                kind=project_kind.value,
                initial_tags_csv=",".join(proposal.initial_tags) if proposal.initial_tags else None,
                ts_ms=int(time.time() * 1000),
                actor_did=state.actor_did,
                org_did=state.org_did,
            )

    return {
        "classification": classification,
        "project_vertex_id": project_vertex_id,
        "project_kind": project_kind,
        "project_emerged": project_emerged,
        "awaiting_human_review": False,
        "current_node": "classify_project",
    }


def await_human_review(state: ManimaniState) -> dict[str, Any]:
    """Terminal node when the HITL gate fires.

    Phase 4: the run pauses here. The caller polls /runs/{run_id} (or
    the run row in vertex_manimani_run) to see ``status='interrupted'``,
    then issues ``ai.gftd.apps.manimani.resumeRun`` with a decision.
    The resume path re-invokes the graph from parse_input with
    ``state.human_decision`` set; the HITL gate short-circuits and the
    rest of the pipeline runs normally.
    """

    return {"current_node": "await_human_review"}


def _hitl_new_project_enabled() -> bool:
    return os.environ.get("MANIMANI_HITL_NEW_PROJECT", "").strip() in ("1", "true", "yes", "on")


def _post_classify_router(state: ManimaniState) -> str:
    """Conditional edge: classify_project → {await_human_review | route_processor}."""

    if state.awaiting_human_review:
        return "await_human_review"
    return "route_processor"


def route_processor(state: ManimaniState) -> dict[str, Any]:
    """Pick which processor node to run next based on ``project_kind``."""

    if state.error_text:
        return {"processor": "defer_for_user_review", "current_node": "route_processor"}
    kind = state.project_kind or ProjectKind.UNSORTED
    processor = PROCESSOR_BY_KIND.get(kind.value, "defer_for_user_review")
    return {
        "processor": processor,
        "model_tier": PROCESSOR_DEFAULT_TIER.get(processor, "fast"),
        "current_node": "route_processor",
    }


def _branch_router(state: ManimaniState) -> str:
    """Conditional edge: route_processor → one of 4 processor nodes."""

    if state.error_text:
        return "defer_for_user_review"
    return state.processor or "defer_for_user_review"


def _run_processor(state: ManimaniState, fn) -> dict[str, Any]:
    parsed = state.parsed_text or ""
    project_meta: dict[str, Any] = {
        "project_vertex_id": state.project_vertex_id,
        "project_kind": (state.project_kind or ProjectKind.UNSORTED).value,
    }
    out = fn(parsed_text=parsed, project_meta=project_meta, actor_did=state.actor_did)
    artifact = _build_artifact(state, out)
    return {"artifacts": [artifact], "current_node": fn.__name__}


def extract_facts(state: ManimaniState) -> dict[str, Any]:
    return _run_processor(state, extract_facts_fn)


def expand_todo(state: ManimaniState) -> dict[str, Any]:
    return _run_processor(state, expand_todo_fn)


def summarize(state: ManimaniState) -> dict[str, Any]:
    return _run_processor(state, summarize_fn)


def defer_for_user_review_node(state: ManimaniState) -> dict[str, Any]:
    return _run_processor(state, defer_for_user_review_fn)


def persist_artifact(state: ManimaniState) -> dict[str, Any]:
    """Hyperdrive direct INSERT (ADR-0036) into vertex_manimani_artifact +
    edge_manimani_belongs_to (primary edge intake → project)."""

    if state.error_text or not state.artifacts:
        return {"current_node": "persist_artifact"}
    if not state.project_vertex_id:
        return {"error_text": "project_vertex_id missing at persist", "current_node": "persist_artifact"}

    insert_artifacts(
        artifacts=state.artifacts,
        actor_did=state.actor_did,
        org_did=state.org_did,
    )
    classification = state.classification
    confidence = classification.confidence if classification else 0.0
    insert_belongs_to_edge(
        intake_vertex_id=state.intake_vertex_id,
        project_vertex_id=state.project_vertex_id,
        confidence=confidence,
        is_primary=True,
        classification_method="llm_structured",
        actor_did=state.actor_did,
        org_did=state.org_did,
    )
    return {"current_node": "persist_artifact"}


def emit_audit(state: ManimaniState) -> dict[str, Any]:
    """OCEL 2.0 audit hook (Phase 2 wires `generic.audit.emit`).

    Phase 1 stub: no-op + advance current_node so the run cache reflects
    the terminal state.
    """

    return {"current_node": "emit_audit"}


# ── helpers ──────────────────────────────────────────────────────────


def _make_project_vertex_id(actor_did: str, slug: str) -> str:
    digest = hashlib.sha256(f"{actor_did}|{slug}".encode("utf-8")).hexdigest()
    return f"at://{actor_did}/ai.gftd.apps.manimani.project/{digest[:16]}"


def _make_project_did(slug: str) -> str:
    return f"did:web:manimani.gftd.ai:project:{slug}"


def _build_artifact(state: ManimaniState, processor_out: dict[str, Any]) -> Artifact:
    ts_ms = int(time.time() * 1000)
    content = (processor_out.get("content") or "").encode("utf-8")
    sha = hashlib.sha256(content).hexdigest()
    processor_name = state.processor or "defer_for_user_review"
    vid = (
        f"at://{state.actor_did}/ai.gftd.apps.manimani.artifact/"
        f"{sha[:16]}-{processor_name[:8]}"
    )
    artifact_kind_str = str(processor_out.get("artifact_kind") or "raw_passthrough")
    try:
        artifact_kind = ArtifactKind(artifact_kind_str)
    except ValueError:
        artifact_kind = ArtifactKind.RAW_PASSTHROUGH
    return Artifact(
        vertex_id=vid,
        intake_vertex_id=state.intake_vertex_id,
        project_vertex_id=state.project_vertex_id or "",
        run_vertex_id=state.run_id,
        artifact_kind=artifact_kind,
        content=processor_out.get("content"),
        model_id=processor_out.get("model_id"),
        tokens_in=processor_out.get("tokens_in"),
        tokens_out=processor_out.get("tokens_out"),
        error_text=processor_out.get("error_text"),
        ts_ms=ts_ms,
    )


# ── graph factory ────────────────────────────────────────────────────


def build_graph(*, checkpointer: Any = None):
    """Compile the manimani StateGraph.

    Args:
      checkpointer: optional langgraph ``BaseCheckpointSaver``. When
        provided, every node transition writes a checkpoint row to the
        ``vertex_langgraph_checkpoint`` + ``vertex_langgraph_checkpoint_write``
        tables (ADR-2605080600). Pass ``RisingWaveCheckpointSaver`` from
        ``pymagatama.langgraph_checkpoint_rw`` for production (Phase 3).
        Pass ``None`` for unit tests / dry-run mode.

    Returns the compiled graph object (langgraph 0.2.x ``CompiledStateGraph``).
    """

    if StateGraph is None:  # pragma: no cover
        raise RuntimeError("langgraph not installed; pip install langgraph")

    g: Any = StateGraph(ManimaniState)
    g.add_node("parse_input", parse_input)
    g.add_node("classify_project", classify_project)
    g.add_node("await_human_review", await_human_review)
    g.add_node("route_processor", route_processor)
    g.add_node("extract_facts", extract_facts)
    g.add_node("expand_todo", expand_todo)
    g.add_node("summarize", summarize)
    g.add_node("defer_for_user_review", defer_for_user_review_node)
    g.add_node("persist_artifact", persist_artifact)
    g.add_node("emit_audit", emit_audit)

    g.set_entry_point("parse_input")
    g.add_edge("parse_input", "classify_project")
    # HITL gate (Phase 4): classify_project routes to await_human_review
    # when awaiting_human_review=True (env MANIMANI_HITL_NEW_PROJECT=1
    # AND classifier proposed a brand-new project AND not yet decided).
    g.add_conditional_edges(
        "classify_project",
        _post_classify_router,
        {
            "await_human_review": "await_human_review",
            "route_processor": "route_processor",
        },
    )
    g.add_edge("await_human_review", END)
    g.add_conditional_edges(
        "route_processor",
        _branch_router,
        {
            "extract_facts": "extract_facts",
            "expand_todo": "expand_todo",
            "summarize": "summarize",
            "defer_for_user_review": "defer_for_user_review",
        },
    )
    g.add_edge("extract_facts", "persist_artifact")
    g.add_edge("expand_todo", "persist_artifact")
    g.add_edge("summarize", "persist_artifact")
    g.add_edge("defer_for_user_review", "persist_artifact")
    g.add_edge("persist_artifact", "emit_audit")
    g.add_edge("emit_audit", END)

    return g.compile(checkpointer=checkpointer) if checkpointer is not None else g.compile()
