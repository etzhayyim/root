"""export_surveillance_evidence — Pregel-style LangGraph chain replacing BPMN.

Architecture (per ADR-2605080600 LangGraph Server + Granian L3 + ADR-2605082200
LangServer Handler Thin Dispatcher):

  Graph topology (Pregel super-steps in parentheses):

    Start
      │ (super-step 1) sequential
      ▼
    assemble_facts
      │
      ▼
    [Conditional: two_stage_approval gate]
      │ approve              │ deny
      ▼                      ▼
    load_query              END (status=denied, error=TWO_STAGE_APPROVAL_REQUIRED)
      │
      ▼
    fan_out_to_renderers ────────────────────────────────────────────┐
      │  (super-step 2) BSP parallel via langgraph.constants.Send    │
      ├─► render_kanshi_houkokusho                                   │
      ├─► render_shouko_mokuroku                                     │
      ├─► render_souchi_sho                                          │
      └─► render_chain_of_custody                                    │
                                                                     ▼
      │  (super-step 3) implicit barrier — all 4 renderers complete before next step
      ▼
    emit_pegel_per_doc  (writes 4× vertex_malak_surveillance_investigation_tick)
      │
      ▼
    persist_fs  (writes .md + MANIFEST.txt + sha256 to output_dir)
      │
      ▼
    audit_emit (malak.surveillance.evidence.exported)
      │
      ▼
    End (status=exported)

Replaces:
    00-contracts/bpmn/ai/gftd/malak/exportSurveillanceEvidence.bpmn (archived)

Phase 0 caveat: write_graph stays in dry-run; RW INSERT only after G1+G2 GREEN
per PHASE-1-LAUNCH-READINESS.md.
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import hashlib
import json
import logging
import pathlib
import uuid
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.constants import Send
from langgraph.graph import StateGraph, END

from .workflow import run_langgraph_pipeline

logger = logging.getLogger(__name__)


# ── Reducers (Pregel parallel write merge) ─────────────────────────────


def _merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer for dict channels — used when parallel render_doc Sends
    each write a single (doc_type → markdown) pair. LangGraph applies
    this reducer to combine values from a single super-step.
    """
    if not a:
        return dict(b or {})
    if not b:
        return dict(a)
    out = dict(a)
    out.update(b)
    return out


# ── State ─────────────────────────────────────────────────────────────


class ExportEvidenceState(TypedDict, total=False):
    # input
    query_id: str
    supervisor_did: str
    section_chief_did: str
    case_no: str
    output_dir: str
    doc_types: List[str]   # subset of ["kanshi_houkokusho","shouko_mokuroku","souchi_sho","chain_of_custody"]
    live_write: bool       # default False; Phase 0 keeps it False
    # internal — parallel writers (Pregel super-step) need merge reducer
    case_id: str
    query_record: Dict[str, Any]
    rendered_docs: Annotated[Dict[str, str], _merge_dict]   # 4 doc_types written in parallel
    doc_sha256:    Annotated[Dict[str, str], _merge_dict]
    written_files: Dict[str, str]
    # output
    pegel_tick_ids: List[str]
    document_sha256: str  # sha256 of concat of all docs
    status: str           # exported | denied | error
    error: str


ALL_DOC_TYPES = ("kanshi_houkokusho", "shouko_mokuroku", "souchi_sho", "chain_of_custody")

DOC_TITLE_JP: Dict[str, str] = {
    "kanshi_houkokusho": "監視カメラ捜査報告書",
    "shouko_mokuroku":   "証拠資料目録",
    "souchi_sho":        "送致書",
    "chain_of_custody":  "Chain of Custody (yaml)",
}


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _malak_did(suffix: str = "") -> str:
    return f"did:web:malak.gftd.ai{(':' + suffix) if suffix else ''}"


# ── Nodes ─────────────────────────────────────────────────────────────


def assemble_facts_node(state: ExportEvidenceState) -> Dict[str, Any]:
    """Validate inputs + assign case_id. No I/O."""
    if not state.get("query_id"):
        return {"status": "error", "error": "query_id is required"}
    case_id = state.get("case_no") or f"case-{state['query_id']}-{_dt.date.today().strftime('%Y%m%d')}"
    doc_types = list(state.get("doc_types") or ALL_DOC_TYPES)
    # Pre-init result containers (so parallel super-step doesn't see KeyError)
    return {
        "case_id":         case_id,
        "rendered_docs":   {},
        "doc_sha256":      {},
        "written_files":   {},
        "pegel_tick_ids":  [],
        "doc_types":       doc_types,
    }


def gate_two_stage_approval(state: ExportEvidenceState) -> str:
    """Conditional edge: two-stage approval gate.

    Returns next node name. Defense-in-depth — edge layer + LangServer layer +
    LangGraph layer all enforce this.
    """
    sup = state.get("supervisor_did") or ""
    chief = state.get("section_chief_did") or ""
    if not sup or not chief:
        return "deny_two_stage"
    return "load_query"


def deny_two_stage_node(state: ExportEvidenceState) -> Dict[str, Any]:
    return {
        "status": "denied",
        "error":  "TWO_STAGE_APPROVAL_REQUIRED: supervisor_did + section_chief_did both required",
    }


async def load_query_node(state: ExportEvidenceState) -> Dict[str, Any]:
    """Mock: in real impl, SELECT from vertex_malak_surveillance_query +
    join with reviewSurveillanceMatches record. Returns canonical
    query_record dict.
    """
    return {
        "query_record": {
            "queryId":    state["query_id"],
            "queryKind":  "person",   # or "scene"
            "completedAt": _now_iso(),
            "approver":   state.get("supervisor_did", ""),
            "reviewed":   True,       # mock; real check looks at reviewSurveillanceMatches
            "topMatches": [],
        },
    }


def fan_out_to_renderers(state: ExportEvidenceState):
    """Pregel super-step 2: dispatch parallel render tasks via Send.

    `langgraph.constants.Send` is the BSP fan-out primitive — each Send is
    a (node_name, partial_state) tuple, and LangGraph runs them in
    parallel super-steps with a barrier before the next sequential node.
    """
    doc_types = state.get("doc_types") or list(ALL_DOC_TYPES)
    return [Send("render_doc", {**state, "_doc_type": dt}) for dt in doc_types]


def render_doc_node(state: ExportEvidenceState) -> Dict[str, Any]:
    """Renders ONE doc per Send. Result merged into `rendered_docs` dict
    (LangGraph dict-channel reducer combines parallel writes safely).
    """
    doc_type = state.get("_doc_type") or ""
    qr = state.get("query_record") or {}
    if doc_type == "kanshi_houkokusho":
        body = _render_kanshi(state, qr)
    elif doc_type == "shouko_mokuroku":
        body = _render_shouko_mokuroku(state, qr)
    elif doc_type == "souchi_sho":
        body = _render_souchi_sho(state, qr)
    elif doc_type == "chain_of_custody":
        body = _render_chain_of_custody(state, qr)
    else:
        body = f"# {doc_type}\n\n(renderer not implemented)\n"
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return {
        "rendered_docs": {doc_type: body},
        "doc_sha256":    {doc_type: sha},
    }


def _render_kanshi(state: ExportEvidenceState, qr: Dict[str, Any]) -> str:
    return (
        f"# 監視カメラ捜査報告書\n"
        f"## case_no: {state.get('case_no', state.get('case_id', ''))}\n\n"
        f"| 項目 | 値 |\n|---|---|\n"
        f"| 照会日 | {_now_iso()[:10]} |\n"
        f"| 照会者 (起案) | {state.get('supervisor_did', '')} |\n"
        f"| 課長級承認 | {state.get('section_chief_did', '')} |\n"
        f"| 照会対象 query_id | {qr.get('queryId', '')} |\n"
        f"| クエリ種別 | {qr.get('queryKind', '')} |\n"
        f"| 完了日時 | {qr.get('completedAt', '')} |\n\n"
        f"## クエリ条件 (要約)\n\n"
        f"クエリ ID `{qr.get('queryId', '')}` に基づく {qr.get('queryKind', '')} 検索の結果について、"
        f"reviewSurveillanceMatches 記録 (人間判定介在) を経た上で、"
        f"以下の関連クリップ及び関連資料を識別した。\n\n"
        f"(top matches は `shouko_mokuroku` を参照)\n"
    )


def _render_shouko_mokuroku(state: ExportEvidenceState, qr: Dict[str, Any]) -> str:
    matches = qr.get("topMatches") or []
    lines = [
        f"# 証拠資料目録",
        f"## case_no: {state.get('case_no', state.get('case_id', ''))}",
        "",
        "| # | 種別 | 識別子 | sha256 | R2 path |",
        "|---|---|---|---|---|",
    ]
    if matches:
        for i, m in enumerate(matches, 1):
            lines.append(
                f"| {i} | clip | {m.get('clipId','')} | {m.get('sha256','')} | "
                f"{m.get('r2Key','')} |"
            )
    else:
        lines.append("| - | - | (no matches reviewed) | - | - |")
    lines.append("")
    return "\n".join(lines)


def _render_souchi_sho(state: ExportEvidenceState, qr: Dict[str, Any]) -> str:
    return (
        f"# 送致書\n"
        f"## case_no: {state.get('case_no', state.get('case_id', ''))}\n\n"
        f"報告ライン:\n\n"
        f"  1. 起案 (supervisor) — {state.get('supervisor_did', '')}\n"
        f"  2. 課長級承認 (section chief) — {state.get('section_chief_did', '')}\n"
        f"  3. 都道府県警捜査主任\n"
        f"  4. 都道府県警サイバー犯罪対策課課長\n"
        f"  5. 都道府県警捜査第二課課長 (特殊詐欺事案の場合)\n"
        f"  6. 県警本部\n"
        f"  7. 警察庁刑事局 / 警察庁サイバー警察局\n"
        f"  8. JC3 (日本サイバー犯罪対策センター)\n"
        f"  9. INTERPOL IPSG (国際協力時)\n\n"
        f"以上、報告事項として送致する。\n"
    )


def _render_chain_of_custody(state: ExportEvidenceState, qr: Dict[str, Any]) -> str:
    case_id = state.get("case_id", "")
    sup = state.get("supervisor_did", "")
    chief = state.get("section_chief_did", "")
    return (
        f"# chain_of_custody.yaml\n\n"
        f"```yaml\n"
        f"case_id: {case_id}\n"
        f"query_id: {qr.get('queryId', '')}\n"
        f"chain:\n"
        f"  - step: ingestion\n"
        f"    when: {_now_iso()}\n"
        f"    actor: did:web:malak.gftd.ai:surveillance\n"
        f"    artefact: vertex_malak_surveillance_clip\n"
        f"  - step: search\n"
        f"    when: {qr.get('completedAt', '')}\n"
        f"    actor: {sup}\n"
        f"    artefact: vertex_malak_surveillance_query/{qr.get('queryId', '')}\n"
        f"  - step: review\n"
        f"    when: {_now_iso()}\n"
        f"    actor: {sup}\n"
        f"    artefact: vertex_malak_surveillance_query_result (reviewed=true)\n"
        f"  - step: approve_export\n"
        f"    when: {_now_iso()}\n"
        f"    actor: {chief}\n"
        f"    artefact: section_chief two-stage approval\n"
        f"  - step: export\n"
        f"    when: {_now_iso()}\n"
        f"    actor: did:web:malak.gftd.ai:surveillance\n"
        f"    artefact: this packet\n"
        f"```\n"
    )


async def emit_pegel_per_doc_node(state: ExportEvidenceState) -> Dict[str, Any]:
    """Pregel super-step 4: emit one pegel tick per rendered doc.

    Sequential (not parallel) to keep tick ordering deterministic. Could be
    parallelised in Phase 1 via another Send fan-out if tick volume warrants.
    """
    ticks: List[str] = []
    for doc_type, body in (state.get("rendered_docs") or {}).items():
        details = (
            f"doc_type={doc_type} ({DOC_TITLE_JP.get(doc_type, doc_type)})\n"
            f"case_id={state.get('case_id', '')}\n"
            f"query_id={state.get('query_id', '')}\n"
            f"sha256={state.get('doc_sha256', {}).get(doc_type, '')}\n"
            f"supervisor_did={state.get('supervisor_did', '')}\n"
            f"section_chief_did={state.get('section_chief_did', '')}\n"
            f"---\n{body[:1500]}"
        )
        try:
            pegel = await run_langgraph_pipeline(
                role_id="malak",
                params={
                    "tlp": "RED",
                    "action": f"surveillance_evidence_export:{doc_type}",
                    "details": details,
                },
            )
            tid = (pegel or {}).get("tick_vertex_id") or ""
            if tid:
                ticks.append(tid)
        except Exception as e:  # noqa: BLE001
            return {"error": f"pegel emit failed for {doc_type}: {e}", "pegel_tick_ids": ticks}
    return {"pegel_tick_ids": ticks}


def persist_fs_node(state: ExportEvidenceState) -> Dict[str, Any]:
    out_dir = state.get("output_dir") or ""
    docs = state.get("rendered_docs") or {}
    if not out_dir or not docs:
        return {}
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    files: Dict[str, str] = {}
    concat_parts: List[str] = []
    for doc_type, body in docs.items():
        fp = p / f"{doc_type}.md"
        fp.write_text(body, encoding="utf-8")
        files[doc_type] = str(fp)
        concat_parts.append(body)
    # MANIFEST.txt
    manifest_path = p / "MANIFEST.txt"
    lines = [
        f"case_id: {state.get('case_id', '')}",
        f"query_id: {state.get('query_id', '')}",
        f"supervisor_did: {state.get('supervisor_did', '')}",
        f"section_chief_did: {state.get('section_chief_did', '')}",
        f"generated_at: {_now_iso()}",
        "documents:",
    ]
    for doc_type, fp in files.items():
        sha = state.get("doc_sha256", {}).get(doc_type, "")
        lines.append(f"  - {doc_type}: {fp} sha256={sha}")
    lines.append("pegel_ticks:")
    for t in state.get("pegel_tick_ids") or []:
        lines.append(f"  - {t}")
    manifest_path.write_text("\n".join(lines), encoding="utf-8")
    files["manifest"] = str(manifest_path)
    # Concat sha
    concat = "\n\n---\n\n".join(concat_parts)
    document_sha256 = hashlib.sha256(concat.encode("utf-8")).hexdigest()
    return {"written_files": files, "document_sha256": document_sha256}


def audit_emit_node(state: ExportEvidenceState) -> Dict[str, Any]:
    """Final audit log entry. In production this is an OCEL emit + RW
    INSERT into vertex_malak_surveillance_audit_event."""
    if state.get("status", "").startswith(("denied", "error")):
        return {}
    logger.info(
        "malak.surveillance.evidence.exported case_id=%s query_id=%s docs=%d ticks=%d sha=%s",
        state.get("case_id", ""),
        state.get("query_id", ""),
        len(state.get("rendered_docs") or {}),
        len(state.get("pegel_tick_ids") or []),
        (state.get("document_sha256") or "")[:16],
    )
    return {"status": "exported"}


# ── Graph ──────────────────────────────────────────────────────────────


def build_export_evidence_graph():
    g = StateGraph(ExportEvidenceState)

    g.add_node("assemble_facts",     assemble_facts_node)
    g.add_node("deny_two_stage",     deny_two_stage_node)
    g.add_node("load_query",         load_query_node)
    g.add_node("render_doc",         render_doc_node)
    g.add_node("emit_pegel_per_doc", emit_pegel_per_doc_node)
    g.add_node("persist_fs",         persist_fs_node)
    g.add_node("audit_emit",         audit_emit_node)

    g.set_entry_point("assemble_facts")
    g.add_conditional_edges(
        "assemble_facts",
        gate_two_stage_approval,
        {"load_query": "load_query", "deny_two_stage": "deny_two_stage"},
    )
    g.add_edge("deny_two_stage", END)
    # Pregel super-step 2: parallel fan-out via Send
    g.add_conditional_edges("load_query", fan_out_to_renderers, ["render_doc"])
    # Implicit barrier after super-step: all render_doc instances finish before emit_pegel
    g.add_edge("render_doc", "emit_pegel_per_doc")
    g.add_edge("emit_pegel_per_doc", "persist_fs")
    g.add_edge("persist_fs", "audit_emit")
    g.add_edge("audit_emit", END)
    return g.compile()


async def run_export_evidence(
    *,
    query_id: str,
    supervisor_did: str,
    section_chief_did: str,
    case_no: str = "",
    output_dir: str = "",
    doc_types: Optional[List[str]] = None,
    live_write: bool = False,
) -> Dict[str, Any]:
    graph = build_export_evidence_graph()
    initial: ExportEvidenceState = {
        "query_id":         query_id,
        "supervisor_did":   supervisor_did,
        "section_chief_did": section_chief_did,
        "case_no":          case_no,
        "output_dir":       output_dir,
        "doc_types":        list(doc_types) if doc_types else list(ALL_DOC_TYPES),
        "live_write":       live_write,
    }
    return await graph.ainvoke(initial)
