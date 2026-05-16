"""briefing — LangGraph chain that produces a graph-native agency briefing.

Pipeline:

    assemble_facts → render_sections → extract_entities → resolve_entities
                   → write_graph → pegel_relay → persist → export → END

Inputs (state):
    briefing_id, briefing_type, target_agency_path, requester_did, title,
    briefing_facts (executiveSummary, useCasePitch, designAdrs, ...),
    source_docs, output_dir, language, tlp

Outputs:
    briefing_id, version, files (paths), section_shas, pegel_ticks,
    entity_counts, graph_vertex_ids, error

Phase 0 caveat: `write_graph` runs in DRY-RUN mode by default; INSERT
statements are *generated* but not executed against live RW until law
clearance (PHASE-1-LAUNCH-READINESS.md G1+G2 GREEN). To enable live
INSERTs set `state["live_write"] = True`.

Mirrors `police_report.py` pattern (same code shape, briefing-specific
templates + entity extraction).
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import pathlib
import re
import uuid
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END

from .briefing_entity_extractor import extract as extract_entities_from_text
from .briefing_templates import (
    DEFAULT_SECTIONS,
    DOC_RENDERERS as DOC_RENDERERS_JP,
    SECTION_TITLE_JP,
)
from .briefing_templates_en import (
    DOC_RENDERERS as DOC_RENDERERS_EN,
    SECTION_TITLE_EN,
)
from .workflow import run_langgraph_pipeline


def _pick_renderers(language: str):
    """Select renderer dict + section-title dict by language."""
    lang = (language or "ja").lower()
    if lang.startswith("en"):
        return DOC_RENDERERS_EN, SECTION_TITLE_EN
    return DOC_RENDERERS_JP, SECTION_TITLE_JP

logger = logging.getLogger(__name__)


class BriefingState(TypedDict, total=False):
    # input
    briefing_id: str
    briefing_type: str
    target_agency_path: str
    target_agency_did: str
    target_agency_name: str
    requester_did: str
    title: str
    version: int
    language: str
    tlp: str
    briefing_facts: Dict[str, Any]
    source_docs: List[Dict[str, Any]]
    output_dir: str
    section_keys: List[str]
    live_write: bool
    # internal
    rendered_md: Dict[str, str]
    section_shas: List[Dict[str, str]]
    raw_entities: List[Dict[str, Any]]
    raw_date_events: List[Dict[str, Any]]
    raw_dependencies: List[Dict[str, Any]]
    raw_url_citations: List[Dict[str, Any]]
    resolved_entities: List[Dict[str, Any]]
    org_mentions: List[Dict[str, Any]]
    graph_rows: Dict[str, List[Dict[str, Any]]]
    # output
    files: Dict[str, str]
    pegel_ticks: List[str]
    entity_counts: Dict[str, int]
    graph_vertex_ids: Dict[str, Any]
    document_sha256: str
    error: str


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _malak_did(suffix: str = "") -> str:
    return f"did:web:malak.gftd.ai{(':' + suffix) if suffix else ''}"


def _vid(prefix: str, *parts: str) -> str:
    body = "/".join(p.replace("/", "-") for p in parts if p)
    return f"at://{_malak_did('surveillance')}/{prefix}/{body}"


# ── Nodes ──────────────────────────────────────────────────────────────


def assemble_facts_node(state: BriefingState) -> Dict[str, Any]:
    facts = state.get("briefing_facts") or {}
    if not facts:
        return {"error": "briefing_facts is required"}
    if not state.get("briefing_type"):
        return {"error": "briefing_type is required"}
    if not state.get("target_agency_path"):
        return {"error": "target_agency_path is required"}
    if not state.get("title"):
        return {"error": "title is required"}

    briefing_id = state.get("briefing_id") or _id_briefing(state)
    return {
        "briefing_id":  briefing_id,
        "version":      state.get("version") or 1,
        "language":     state.get("language") or "ja",
        "tlp":          state.get("tlp") or "AMBER",
        "section_keys": list(state.get("section_keys") or DEFAULT_SECTIONS),
        "rendered_md":  {},
        "section_shas": [],
        "raw_entities": [],
        "raw_date_events": [],
        "raw_dependencies": [],
        "raw_url_citations": [],
        "resolved_entities": [],
        "org_mentions": [],
        "graph_rows": {
            "vertex_malak_briefing":            [],
            "vertex_malak_briefing_section":    [],
            "vertex_malak_briefing_entity":     [],
            "vertex_malak_briefing_date_event": [],
            "edge_briefing_has_section":        [],
            "edge_briefing_mentions_entity":    [],
            "edge_briefing_mentions_org":       [],
            "edge_briefing_cites_record":       [],
            "edge_briefing_depends_on":         [],
            "edge_briefing_event":              [],
        },
        "files":         {},
        "pegel_ticks":   [],
    }


def _id_briefing(state: BriefingState) -> str:
    today = _dt.date.today().strftime("%Y%m%d")
    bt = (state.get("briefing_type") or "generic").replace("_", "-")
    agency = (state.get("target_agency_path") or "unknown").replace(":", "-").replace("/", "-")
    return f"brf-{bt}-{agency}-{today}"


def render_sections_node(state: BriefingState) -> Dict[str, Any]:
    facts = dict(state.get("briefing_facts") or {})
    facts.setdefault("title", state.get("title", ""))
    facts.setdefault("targetAgencyName", state.get("target_agency_name", ""))
    facts.setdefault("targetAgencyPath", state.get("target_agency_path", ""))
    facts.setdefault("operatingEntity", facts.get("operatingEntity") or "amanomibashira")
    facts.setdefault("vendor", facts.get("vendor") or "Gftd Japan株式会社")
    facts.setdefault("tlp", state.get("tlp", "AMBER"))
    facts.setdefault("language", state.get("language", "ja"))
    facts.setdefault("version", state.get("version", 1))

    rendered: Dict[str, str] = {}
    shas: List[Dict[str, str]] = []
    section_keys = state.get("section_keys") or DEFAULT_SECTIONS
    briefing_no = f"{state.get('briefing_id')}-v{state.get('version', 1)}"
    renderers, _ = _pick_renderers(state.get("language") or facts.get("language") or "ja")

    for idx, key in enumerate(section_keys):
        renderer = renderers.get(key)
        if renderer is None:
            logger.warning("no renderer for section %s; skipping", key)
            continue
        md = renderer(facts, briefing_no)
        rendered[key] = md
        sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
        shas.append({"sectionNo": str(idx + 1), "sha256": sha})

    return {"rendered_md": rendered, "section_shas": shas}


def extract_entities_node(state: BriefingState) -> Dict[str, Any]:
    rendered = state.get("rendered_md") or {}
    all_entities: List[Dict[str, Any]] = []
    all_dates: List[Dict[str, Any]] = []
    all_deps: List[Dict[str, Any]] = []
    all_urls: List[Dict[str, Any]] = []
    for idx, (key, md) in enumerate(rendered.items()):
        section_no = str(idx + 1)
        out = extract_entities_from_text(md, section_no=section_no)
        all_entities.extend(out["entities"])
        all_dates.extend(out["date_events"])
        all_deps.extend(out["dependencies"])
        all_urls.extend(out["url_citations"])

    # Dedupe entities by entity_id (keep earliest first_seen_in)
    by_id: Dict[str, Dict[str, Any]] = {}
    for e in all_entities:
        if e["entity_id"] not in by_id:
            by_id[e["entity_id"]] = e
    uniq_entities = list(by_id.values())

    # Dedupe date_events by event_id
    by_id_d: Dict[str, Dict[str, Any]] = {}
    for d in all_dates:
        if d["event_id"] not in by_id_d:
            by_id_d[d["event_id"]] = d
    uniq_dates = list(by_id_d.values())

    return {
        "raw_entities":      uniq_entities,
        "raw_date_events":   uniq_dates,
        "raw_dependencies":  all_deps,
        "raw_url_citations": all_urls,
    }


def resolve_entities_node(state: BriefingState) -> Dict[str, Any]:
    """Match extracted persons/orgs/ADRs to known DIDs / vertex_gov_org paths.

    Phase 0: heuristic only (string match against a known list). Phase 1
    will query RW (vertex_gov_org / vertex_malak_surveillance_lea_branch /
    vertex_did) for canonical resolution.
    """
    entities = list(state.get("raw_entities") or [])
    target_path = state.get("target_agency_path", "")

    # Known DID/path mapping for common entities
    DID_HINTS = {
        "Kunal Bakshi":             "did:web:k-bakshi.gftd.ai",
        "Jun Kawasaki":             "did:web:j-kawasaki.gftd.ai",
        "amanomibashira":           "did:web:amanomibashira.gftd.ai",
        "Gftd Japan株式会社":         "did:web:gftd-japan.gftd.ai",
    }
    PATH_HINTS = {
        "警察庁サイバー警察局":        "npa:cyber",
        "警察庁生活安全局":           "npa:seian",
        "警察庁刑事局":              "npa:keiji",
        "INTERPOL":                  "intl:interpol",
        "Europol":                   "intl:europol",
        "FBI":                       "usa:doj:fbi",
        "NCA":                       "gbr:nca",
        "BKA":                       "deu:bka",
    }

    for e in entities:
        name = e.get("display_name", "")
        if e.get("entity_kind") == "person":
            e["resolved_did"] = DID_HINTS.get(name, "")
        elif name in PATH_HINTS:
            e["identifier"] = PATH_HINTS[name]

    # org_mentions = explicit target_agency + any PATH_HINTS matches
    org_mentions: List[Dict[str, Any]] = [{
        "path": target_path,
        "role": "addressee",
        "first_seen_in": "1",
    }]
    seen_paths = {target_path}
    for e in entities:
        ident = e.get("identifier", "")
        if ident in PATH_HINTS.values() and ident not in seen_paths:
            org_mentions.append({
                "path": ident,
                "role": "referenced",
                "first_seen_in": e.get("first_seen_in", ""),
            })
            seen_paths.add(ident)

    return {"resolved_entities": entities, "org_mentions": org_mentions}


def write_graph_node(state: BriefingState) -> Dict[str, Any]:
    """Build INSERT-shaped row dicts for each table; in Phase 0 just stage them."""
    rows = dict(state.get("graph_rows") or {})
    briefing_id = state.get("briefing_id", "")
    now = _now_iso()
    actor_did = _malak_did("surveillance")

    # 1) vertex_malak_briefing root
    md_concat = "\n\n---\n\n".join(state.get("rendered_md", {}).values())
    doc_sha = hashlib.sha256(md_concat.encode("utf-8")).hexdigest()
    briefing_vid = _vid("ai.gftd.apps.malak.briefing", briefing_id)
    rows["vertex_malak_briefing"].append({
        "vertex_id": briefing_vid,
        "briefing_id": briefing_id,
        "briefing_type": state.get("briefing_type", ""),
        "target_agency_path": state.get("target_agency_path", ""),
        "target_agency_did": state.get("target_agency_did", ""),
        "title": state.get("title", ""),
        "version": state.get("version", 1),
        "language": state.get("language", "ja"),
        "tlp": state.get("tlp", "AMBER"),
        "doc_sha256": doc_sha,
        "generated_at": now,
        "generated_by_did": state.get("requester_did", ""),
        "status": "drafted",
        "sensitivity_ord": 50,
        "owner_did": actor_did,
        "actor_did": actor_did,
        "org_did": _malak_did(),
        "created_at": now,
    })

    # 2) vertex_malak_briefing_section
    section_ids: List[str] = []
    _, section_titles = _pick_renderers(state.get("language") or "ja")
    for idx, (key, md) in enumerate(state.get("rendered_md", {}).items()):
        section_no = str(idx + 1)
        section_vid = _vid("ai.gftd.apps.malak.briefingSection", briefing_id, key)
        section_ids.append(section_vid)
        rows["vertex_malak_briefing_section"].append({
            "vertex_id": section_vid,
            "briefing_id": briefing_id,
            "section_no": section_no,
            "section_title": section_titles.get(key, key),
            "section_order": idx + 1,
            "body_md": md,
            "body_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
            "word_count": len(md.split()),
            "sensitivity_ord": 50,
            "owner_did": actor_did,
            "actor_did": actor_did,
            "org_did": _malak_did(),
            "created_at": now,
        })
        # edge_briefing_has_section
        rows["edge_briefing_has_section"].append({
            "edge_id": _vid("edge.brf.hs", briefing_id, section_no),
            "src_vid": briefing_vid,
            "dst_vid": section_vid,
            "ord": idx + 1,
            "sensitivity_ord": 50, "owner_did": actor_did,
            "actor_did": actor_did, "org_did": _malak_did(),
            "created_at": now,
        })

    # 3) vertex_malak_briefing_entity + edge_briefing_mentions_entity
    entity_vid_by_eid: Dict[str, str] = {}
    for e in state.get("resolved_entities") or []:
        eid = e["entity_id"]
        evid = _vid("ai.gftd.apps.malak.briefingEntity", briefing_id, eid)
        entity_vid_by_eid[eid] = evid
        rows["vertex_malak_briefing_entity"].append({
            "vertex_id": evid,
            "entity_id": eid,
            "entity_kind": e.get("entity_kind", "concept"),
            "display_name": e.get("display_name", ""),
            "identifier": e.get("identifier", ""),
            "resolved_did": e.get("resolved_did", ""),
            "external_url": e.get("external_url", ""),
            "confidence": e.get("confidence", 0.5),
            "extraction_source": e.get("extraction_source", "regex"),
            "first_seen_in": e.get("first_seen_in", ""),
            "sensitivity_ord": 100 if e.get("entity_kind") == "person" else 50,
            "owner_did": actor_did,
            "actor_did": actor_did, "org_did": _malak_did(),
            "created_at": now,
        })
        rows["edge_briefing_mentions_entity"].append({
            "edge_id": _vid("edge.brf.me", briefing_id, eid),
            "src_vid": briefing_vid,
            "dst_vid": evid,
            "mention_kind": "inline",
            "mention_count": 1,
            "first_offset": 0,
            "sensitivity_ord": 50, "owner_did": actor_did,
            "actor_did": actor_did, "org_did": _malak_did(),
            "created_at": now,
        })

    # 4) vertex_malak_briefing_date_event + edge_briefing_event
    for d in state.get("raw_date_events") or []:
        dvid = _vid("ai.gftd.apps.malak.briefingDateEvent", briefing_id, d["event_id"])
        rows["vertex_malak_briefing_date_event"].append({
            "vertex_id": dvid,
            "event_id": d["event_id"],
            "event_kind": d.get("event_kind", "milestone"),
            "event_label": d.get("event_label", ""),
            "event_date": d.get("event_date", ""),
            "iso_date": d.get("iso_date", ""),
            "precision": d.get("precision", "day"),
            "confidence": d.get("confidence", 0.7),
            "sensitivity_ord": 20, "owner_did": actor_did,
            "actor_did": actor_did, "org_did": _malak_did(),
            "created_at": now,
        })
        rows["edge_briefing_event"].append({
            "edge_id": _vid("edge.brf.ev", briefing_id, d["event_id"]),
            "src_vid": briefing_vid,
            "dst_vid": dvid,
            "role": "scheduled_for",
            "sensitivity_ord": 20, "owner_did": actor_did,
            "actor_did": actor_did, "org_did": _malak_did(),
            "created_at": now,
        })

    # 5) edge_briefing_mentions_org (links to existing vertex_gov_org)
    for org in state.get("org_mentions") or []:
        org_vid = f"at://did:web:gov-jpn.gftd.ai/ai.gftd.apps.gov.org/{org['path']}"
        rows["edge_briefing_mentions_org"].append({
            "edge_id": _vid("edge.brf.mo", briefing_id, org["path"]),
            "src_vid": briefing_vid,
            "dst_vid": org_vid,
            "mention_kind": "inline",
            "role": org.get("role", "referenced"),
            "sensitivity_ord": 20, "owner_did": actor_did,
            "actor_did": actor_did, "org_did": _malak_did(),
            "created_at": now,
        })

    # 6) edge_briefing_cites_record (URLs as external citations)
    for idx, url_cite in enumerate(state.get("raw_url_citations") or []):
        rows["edge_briefing_cites_record"].append({
            "edge_id": _vid("edge.brf.cr", briefing_id, str(idx)),
            "src_vid": briefing_vid,
            "dst_vid": "",
            "cite_kind": url_cite.get("cite_kind", "external"),
            "external_url": url_cite.get("url", ""),
            "label": url_cite.get("label", ""),
            "ord": idx + 1,
            "sensitivity_ord": 20, "owner_did": actor_did,
            "actor_did": actor_did, "org_did": _malak_did(),
            "created_at": now,
        })

    # 7) edge_briefing_depends_on (heuristic, low confidence)
    for dep in state.get("raw_dependencies") or []:
        rows["edge_briefing_depends_on"].append({
            "edge_id": _vid("edge.brf.do", briefing_id, dep.get("dst", "")),
            "src_vid": briefing_vid,
            "dst_vid": f"heuristic:{dep.get('dst', '')}",
            "dep_kind": dep.get("dep_kind", "requires"),
            "required_status": dep.get("required_status", ""),
            "sensitivity_ord": 20, "owner_did": actor_did,
            "actor_did": actor_did, "org_did": _malak_did(),
            "created_at": now,
        })

    counts = {
        "person":     sum(1 for e in state.get("resolved_entities") or [] if e.get("entity_kind") == "person"),
        "project":    sum(1 for e in state.get("resolved_entities") or [] if e.get("entity_kind") == "project"),
        "adr":        sum(1 for e in state.get("resolved_entities") or [] if e.get("entity_kind") == "adr"),
        "url":        sum(1 for e in state.get("resolved_entities") or [] if e.get("entity_kind") == "url"),
        "law":        sum(1 for e in state.get("resolved_entities") or [] if e.get("entity_kind") == "law"),
        "concept":    sum(1 for e in state.get("resolved_entities") or [] if e.get("entity_kind") == "concept"),
        "org":        len(state.get("org_mentions") or []),
        "dateEvent":  len(state.get("raw_date_events") or []),
        "dependency": len(state.get("raw_dependencies") or []),
    }
    graph_ids = {
        "briefing":     briefing_vid,
        "sectionIds":   section_ids,
        "entityIds":    list(entity_vid_by_eid.values()),
        "dateEventIds": [r["vertex_id"] for r in rows["vertex_malak_briefing_date_event"]],
    }

    # Live write hook: when state["live_write"] is True AND Phase 1 cleared,
    # the orchestrator (briefing.py caller) would dispatch these rows via
    # bpmn-dispatcher → LangServer → RW INSERT. Phase 0 dry-run keeps them
    # staged in graph_rows for inspection.
    if state.get("live_write"):
        logger.warning(
            "live_write=True but Phase 0 — no RW INSERT executed. Rows staged: "
            "%d vertex + %d edge entries.",
            sum(1 for k in rows if k.startswith("vertex_")),
            sum(1 for k in rows if k.startswith("edge_")),
        )

    return {
        "graph_rows":      rows,
        "entity_counts":   counts,
        "graph_vertex_ids": graph_ids,
        "document_sha256": doc_sha,
    }


async def pegel_relay_node(state: BriefingState) -> Dict[str, Any]:
    """Emit one tick per briefing draft so RW vertex_malak_investigation_tick
    has a record. Mirrors police_report.pegel_relay_node."""
    facts = state.get("briefing_facts") or {}
    counts = state.get("entity_counts") or {}
    ticks: List[str] = []
    details = (
        f"briefing_id={state.get('briefing_id', '')}\n"
        f"briefing_type={state.get('briefing_type', '')}\n"
        f"target={state.get('target_agency_path', '')}\n"
        f"version={state.get('version', 1)}\n"
        f"language={state.get('language', 'ja')}\n"
        f"tlp={state.get('tlp', 'AMBER')}\n"
        f"doc_sha256={state.get('document_sha256', '')}\n"
        f"sections={len(state.get('rendered_md', {}) or {})}\n"
        f"entities={sum(counts.values())}\n"
        f"---\n"
        f"counts={json.dumps(counts, ensure_ascii=False)}"
    )
    try:
        pegel = await run_langgraph_pipeline(
            role_id="malak",
            params={
                "tlp": state.get("tlp", "AMBER"),
                "action": f"agency_briefing:{state.get('briefing_type', 'generic')}",
                "details": details,
            },
        )
        tid = (pegel or {}).get("tick_vertex_id") or ""
        if tid:
            ticks.append(tid)
    except Exception as e:  # noqa: BLE001
        return {"error": f"pegel_relay: {e}", "pegel_ticks": ticks}
    return {"pegel_ticks": ticks}


def persist_node(state: BriefingState) -> Dict[str, Any]:
    out_dir = state.get("output_dir") or ""
    rendered = state.get("rendered_md") or {}
    if not out_dir or not rendered:
        return {}
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    files: Dict[str, str] = {}
    concat_lines: List[str] = []
    for key, md in rendered.items():
        fp = p / f"{key}.md"
        fp.write_text(md, encoding="utf-8")
        files[f"section_{key}"] = str(fp)
        concat_lines.append(md)
    # Concatenated full briefing
    full_md = p / "briefing.md"
    full_text = "\n\n---\n\n".join(concat_lines)
    full_md.write_text(full_text, encoding="utf-8")
    files["briefing_md"] = str(full_md)
    # FAQ split (already exists as a section, also write standalone)
    faq_md = rendered.get("faq")
    if faq_md:
        faq_path = p / "faq.md"
        faq_path.write_text(faq_md, encoding="utf-8")
        files["faq_md"] = str(faq_path)
    # Manifest with graph row counts + entity tallies
    manifest_path = p / "MANIFEST.txt"
    counts = state.get("entity_counts") or {}
    graph_rows = state.get("graph_rows") or {}
    lines = [
        f"briefing_id: {state.get('briefing_id', '')}",
        f"briefing_type: {state.get('briefing_type', '')}",
        f"target_agency_path: {state.get('target_agency_path', '')}",
        f"version: {state.get('version', 1)}",
        f"tlp: {state.get('tlp', 'AMBER')}",
        f"language: {state.get('language', 'ja')}",
        f"generated_at: {_now_iso()}",
        f"document_sha256: {state.get('document_sha256', '')}",
        "",
        "section_counts: " + str(len(rendered)),
        "entity_counts: " + json.dumps(counts, ensure_ascii=False),
        "",
        "graph_rows:",
    ]
    for table, table_rows in graph_rows.items():
        lines.append(f"  {table}: {len(table_rows)} rows")
    lines.append("")
    lines.append("pegel_ticks:")
    for t in state.get("pegel_ticks") or []:
        lines.append(f"  - {t}")
    manifest_path.write_text("\n".join(lines), encoding="utf-8")
    files["manifest"] = str(manifest_path)
    return {"files": files}


def export_node(state: BriefingState) -> Dict[str, Any]:
    """Optional pandoc DOCX + PDF export. Failures are silent."""
    import shutil
    import subprocess
    files = dict(state.get("files") or {})
    src = files.get("briefing_md")
    if not src:
        return {}
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return {}
    src_p = pathlib.Path(src)
    docx = src_p.with_suffix(".docx")
    try:
        subprocess.run(
            [pandoc, str(src_p), "-o", str(docx), "-V", "geometry:margin=20mm"],
            check=True, timeout=60, capture_output=True,
        )
        files["briefing_docx"] = str(docx)
    except Exception:  # noqa: BLE001
        pass
    xelatex = shutil.which("xelatex")
    if xelatex:
        pdf = src_p.with_suffix(".pdf")
        try:
            subprocess.run(
                [pandoc, str(src_p), "-o", str(pdf), "--pdf-engine=xelatex",
                 "-V", "mainfont=Hiragino Mincho ProN", "-V", "geometry:margin=20mm"],
                check=True, timeout=120, capture_output=True,
            )
            files["briefing_pdf"] = str(pdf)
        except Exception:  # noqa: BLE001
            pass
    return {"files": files}


# ── Graph ──────────────────────────────────────────────────────────────


def build_briefing_graph():
    g = StateGraph(BriefingState)
    g.add_node("assemble_facts",      assemble_facts_node)
    g.add_node("render_sections",     render_sections_node)
    g.add_node("extract_entities",    extract_entities_node)
    g.add_node("resolve_entities",    resolve_entities_node)
    g.add_node("write_graph",         write_graph_node)
    g.add_node("pegel_relay",         pegel_relay_node)
    g.add_node("persist",             persist_node)
    g.add_node("export",              export_node)

    g.set_entry_point("assemble_facts")
    g.add_edge("assemble_facts",   "render_sections")
    g.add_edge("render_sections",  "extract_entities")
    g.add_edge("extract_entities", "resolve_entities")
    g.add_edge("resolve_entities", "write_graph")
    g.add_edge("write_graph",      "pegel_relay")
    g.add_edge("pegel_relay",      "persist")
    g.add_edge("persist",          "export")
    g.add_edge("export",           END)
    return g.compile()


async def run_briefing(
    *,
    briefing_type: str,
    target_agency_path: str,
    requester_did: str,
    title: str,
    briefing_facts: Dict[str, Any],
    target_agency_name: str = "",
    target_agency_did: str = "",
    output_dir: str = "",
    language: str = "ja",
    tlp: str = "AMBER",
    version: int = 1,
    section_keys: Optional[List[str]] = None,
    source_docs: Optional[List[Dict[str, Any]]] = None,
    live_write: bool = False,
) -> Dict[str, Any]:
    graph = build_briefing_graph()
    initial: BriefingState = {
        "briefing_type":      briefing_type,
        "target_agency_path": target_agency_path,
        "target_agency_name": target_agency_name,
        "target_agency_did":  target_agency_did,
        "requester_did":      requester_did,
        "title":              title,
        "language":           language,
        "tlp":                tlp,
        "version":            version,
        "briefing_facts":     briefing_facts,
        "source_docs":        source_docs or [],
        "output_dir":         output_dir,
        "section_keys":       section_keys or list(DEFAULT_SECTIONS),
        "live_write":         live_write,
    }
    return await graph.ainvoke(initial)
