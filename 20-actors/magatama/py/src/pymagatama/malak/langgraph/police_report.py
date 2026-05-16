"""police_report — LangGraph chain that produces a JP police-format packet.

Pipeline:

    assemble_facts → draft_higai → draft_kokuso → draft_sousa
                   → draft_shoukai → draft_shouko_mokuroku → draft_souchi
                   → pegel_relay → persist → END

Each `draft_*` node renders a markdown document via `police_report_templates`
and stores it in `state.documents[doc_type]`. `pegel_relay` fires
`run_langgraph_pipeline` (PEGEL) for each generated doc so the action is
captured as a `vertex_malak_investigation_tick` row (RW), then `persist`
writes the markdown to disk.

Public entrypoint:

    await run_police_report(case_id="case:takahashi-hiroyuki-20260512",
                            case_facts={...},
                            output_dir="/path/to/packet")

Returns:

    {
        "case_no": str,
        "documents": {doc_type: markdown_text},
        "files":    {doc_type: filesystem_path},
        "pegel_ticks": [tick_vertex_id, ...],
        "reporting_line": [{step, rank, post, name, agency}, ...],
        "error": str | None,
    }
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import pathlib
import re
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from .workflow import run_langgraph_pipeline
from .police_report_templates import (
    DOC_RENDERERS,
    DOC_TYPE_JP,
    JP_POLICE_REPORTING_LINE,
    render_higai_todoke,
    render_kokuso_jo,
    render_sousa_houkokusho,
    render_shoukai_sho,
    render_shouko_mokuroku,
    render_souchi_sho,
    render_soufu_sho,
)


DEFAULT_DOCS = (
    "higai_todoke",
    "kokuso_jo",
    "sousa_houkokusho",
    "shoukai_sho",
    "shouko_mokuroku",
    "souchi_sho",
)


class PoliceReportState(TypedDict, total=False):
    case_id: str
    case_no: str
    case_facts: dict[str, Any]
    doc_types: list[str]
    documents: dict[str, str]
    files: dict[str, str]
    pegel_ticks: list[str]
    reporting_line: list[dict[str, str]]
    output_dir: str
    error: str


def _slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]+", "-", s)[:80]


def _doc_no(case_no: str, doc_type: str) -> str:
    today = datetime.date.today().strftime("%Y%m%d")
    return f"磯刑知-{today}-{_slug(case_no)}-{doc_type}"


# ── Nodes ──────────────────────────────────────────────────────────────
def assemble_facts_node(state: PoliceReportState) -> dict:
    """Validate input + assign case_no + attach reporting line."""
    case_facts = state.get("case_facts") or {}
    if not case_facts:
        return {"error": "case_facts is required"}

    case_id = state.get("case_id") or case_facts.get("case_id", "")
    if not case_id:
        return {"error": "case_id is required"}

    # 県警 fraud case numbering convention: <署>-<年>-<連番>
    today_jp = datetime.date.today().strftime("%y")
    case_no = case_facts.get("case_no") or f"磯刑知第{today_jp}-{_slug(case_id)}号"

    return {
        "case_no": case_no,
        "doc_types": list(state.get("doc_types") or DEFAULT_DOCS),
        "documents": {},
        "files": {},
        "pegel_ticks": [],
        "reporting_line": JP_POLICE_REPORTING_LINE,
    }


def _ensure(state: PoliceReportState) -> tuple[dict[str, Any], str]:
    """Pull case_facts + case_no; raise if assemble_facts didn't run."""
    facts = state.get("case_facts") or {}
    case_no = state.get("case_no") or "(case_no unset)"
    # Inject case_no into facts so renderers can quote it
    facts = {**facts, "case_no": case_no}
    return facts, case_no


def draft_higai_node(state: PoliceReportState) -> dict:
    if "higai_todoke" not in (state.get("doc_types") or []):
        return {}
    facts, case_no = _ensure(state)
    md = render_higai_todoke(facts, _doc_no(case_no, "higai_todoke"))
    docs = dict(state.get("documents") or {})
    docs["higai_todoke"] = md
    return {"documents": docs}


def draft_kokuso_node(state: PoliceReportState) -> dict:
    if "kokuso_jo" not in (state.get("doc_types") or []):
        return {}
    facts, case_no = _ensure(state)
    md = render_kokuso_jo(facts, _doc_no(case_no, "kokuso_jo"))
    docs = dict(state.get("documents") or {})
    docs["kokuso_jo"] = md
    return {"documents": docs}


def draft_sousa_node(state: PoliceReportState) -> dict:
    if "sousa_houkokusho" not in (state.get("doc_types") or []):
        return {}
    facts, case_no = _ensure(state)
    md = render_sousa_houkokusho(facts, _doc_no(case_no, "sousa_houkokusho"))
    docs = dict(state.get("documents") or {})
    docs["sousa_houkokusho"] = md
    return {"documents": docs}


def draft_shoukai_node(state: PoliceReportState) -> dict:
    """One 照会書 per target (= mule bank account)."""
    if "shoukai_sho" not in (state.get("doc_types") or []):
        return {}
    facts, case_no = _ensure(state)
    docs = dict(state.get("documents") or {})
    targets = facts.get("shoukai_targets") or [
        {
            "addressee": f"{m.get('bank', '')} {m.get('branch', '')} 御中",
            "account_or_contract": f"{m.get('account_type', '普')} {m.get('account_number', '')}",
            "holder": m.get("holder", ""),
            "period": facts.get("incident", {}).get("period", ""),
        }
        for m in facts.get("mule_accounts", [])
    ]
    if not targets:
        return {}
    # Concatenate per-target docs into a single shoukai_sho artefact (pandoc later splits)
    blocks = []
    for i, t in enumerate(targets, 1):
        blocks.append(render_shoukai_sho(facts, f"{_doc_no(case_no, 'shoukai_sho')}-{i:02d}", t))
        blocks.append("\n\n---\n\n")
    docs["shoukai_sho"] = "".join(blocks).rstrip()
    return {"documents": docs}


def draft_shouko_node(state: PoliceReportState) -> dict:
    if "shouko_mokuroku" not in (state.get("doc_types") or []):
        return {}
    facts, case_no = _ensure(state)
    md = render_shouko_mokuroku(facts, _doc_no(case_no, "shouko_mokuroku"))
    docs = dict(state.get("documents") or {})
    docs["shouko_mokuroku"] = md
    return {"documents": docs}


def draft_souchi_node(state: PoliceReportState) -> dict:
    if "souchi_sho" not in (state.get("doc_types") or []):
        return {}
    facts, case_no = _ensure(state)
    md = render_souchi_sho(facts, _doc_no(case_no, "souchi_sho"))
    docs = dict(state.get("documents") or {})
    docs["souchi_sho"] = md
    return {"documents": docs}


async def pegel_relay_node(state: PoliceReportState) -> dict:
    """Push each rendered doc through the existing PEGEL pipeline so a
    `vertex_malak_investigation_tick` row appears in RW per document.
    Failure here is non-fatal — drafts are already in `documents`.
    """
    case_no = state.get("case_no", "")
    docs = state.get("documents") or {}
    facts = state.get("case_facts") or {}
    victim = facts.get("victim", {}).get("name", "")
    ticks: list[str] = []
    for doc_type, md in docs.items():
        sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
        details = (
            f"case_no={case_no}\n"
            f"doc_type={doc_type} ({DOC_TYPE_JP.get(doc_type, '')})\n"
            f"victim={victim}\n"
            f"sha256={sha}\n"
            f"reporting_line_steps={len(JP_POLICE_REPORTING_LINE)}\n"
            f"---\n"
            f"{md[:1500]}"
        )
        try:
            pegel = await run_langgraph_pipeline(
                role_id="malak",
                params={
                    "tlp": "RED",
                    "action": f"police_report:{doc_type}",
                    "details": details,
                },
            )
            tid = (pegel or {}).get("tick_vertex_id") or ""
            if tid:
                ticks.append(tid)
        except Exception as e:  # noqa: BLE001
            return {"error": f"pegel_relay {doc_type}: {e}", "pegel_ticks": ticks}
    return {"pegel_ticks": ticks}


def draft_soufu_node(state: PoliceReportState) -> dict:
    """補充資料送付書 — depends on all other docs being rendered first."""
    facts, case_no = _ensure(state)
    docs = dict(state.get("documents") or {})
    if not docs:
        return {}
    doc_index = []
    for doc_type, md in docs.items():
        doc_index.append({
            "jp":     DOC_TYPE_JP.get(doc_type, doc_type),
            "doc_no": _doc_no(case_no, doc_type),
            "file":   f"{doc_type}.md / .docx / .pdf",
            "sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
        })
    docs["soufu_sho"] = render_soufu_sho(facts, _doc_no(case_no, "soufu_sho"), doc_index)
    return {"documents": docs}


def persist_node(state: PoliceReportState) -> dict:
    """Write markdown docs to `output_dir`. No-op if `output_dir` unset."""
    out_dir = state.get("output_dir") or ""
    docs = state.get("documents") or {}
    if not out_dir or not docs:
        return {}
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    # Write 補充資料送付書 first so it stays at the top in directory listings
    ordered = ["soufu_sho"] + [d for d in docs.keys() if d != "soufu_sho"]
    for doc_type in ordered:
        if doc_type not in docs:
            continue
        fp = p / f"{doc_type}.md"
        fp.write_text(docs[doc_type], encoding="utf-8")
        files[doc_type] = str(fp)
    # Sidecar manifest
    manifest = p / "MANIFEST.txt"
    lines = [
        f"case_no: {state.get('case_no', '')}",
        f"case_id: {state.get('case_id', '')}",
        f"generated_at: {datetime.datetime.now().isoformat()}",
        "documents:",
    ]
    for doc_type, fp in files.items():
        sha = hashlib.sha256(pathlib.Path(fp).read_bytes()).hexdigest()
        lines.append(f"  - {doc_type} ({DOC_TYPE_JP.get(doc_type, '')}): {fp}  sha256={sha}")
    lines += ["pegel_ticks:"]
    for t in state.get("pegel_ticks") or []:
        lines.append(f"  - {t}")
    lines += ["reporting_line:"]
    for s in JP_POLICE_REPORTING_LINE:
        lines.append(f"  - {s['step']:>6} | {s['rank']:<6} | {s['post']:<30} | {s['agency']}")
    manifest.write_text("\n".join(lines), encoding="utf-8")
    return {"files": files}


def export_node(state: PoliceReportState) -> dict:
    """Convert each .md → .docx + .pdf via pandoc, if pandoc is on PATH.

    DOCX uses pandoc defaults (works without LaTeX). PDF uses xelatex with
    `Hiragino Mincho ProN` for Japanese glyphs. Failures are silent: the
    markdown packet remains usable even when pandoc / xelatex is missing.
    """
    import shutil
    import subprocess
    files = state.get("files") or {}
    if not files:
        return {}
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return {}
    xelatex = shutil.which("xelatex")
    extras: dict[str, str] = {}
    for doc_type, md_path in files.items():
        md = pathlib.Path(md_path)
        docx = md.with_suffix(".docx")
        try:
            subprocess.run([pandoc, str(md), "-o", str(docx),
                            "-V", "geometry:margin=20mm"],
                           check=True, timeout=60, capture_output=True)
            extras[f"{doc_type}_docx"] = str(docx)
        except Exception:  # noqa: BLE001
            pass
        if xelatex:
            pdf = md.with_suffix(".pdf")
            try:
                subprocess.run([pandoc, str(md), "-o", str(pdf),
                                "--pdf-engine=xelatex",
                                "-V", "mainfont=Hiragino Mincho ProN",
                                "-V", "geometry:margin=20mm"],
                               check=True, timeout=120, capture_output=True)
                extras[f"{doc_type}_pdf"] = str(pdf)
            except Exception:  # noqa: BLE001
                pass
    return {"files": {**files, **extras}}


def build_police_report_graph():
    g = StateGraph(PoliceReportState)
    g.add_node("assemble_facts",      assemble_facts_node)
    g.add_node("draft_higai",         draft_higai_node)
    g.add_node("draft_kokuso",        draft_kokuso_node)
    g.add_node("draft_sousa",         draft_sousa_node)
    g.add_node("draft_shoukai",       draft_shoukai_node)
    g.add_node("draft_shouko",        draft_shouko_node)
    g.add_node("draft_souchi",        draft_souchi_node)
    g.add_node("draft_soufu",         draft_soufu_node)
    g.add_node("pegel_relay",         pegel_relay_node)
    g.add_node("persist",             persist_node)
    g.add_node("export",              export_node)
    g.set_entry_point("assemble_facts")
    g.add_edge("assemble_facts", "draft_higai")
    g.add_edge("draft_higai",    "draft_kokuso")
    g.add_edge("draft_kokuso",   "draft_sousa")
    g.add_edge("draft_sousa",    "draft_shoukai")
    g.add_edge("draft_shoukai",  "draft_shouko")
    g.add_edge("draft_shouko",   "draft_souchi")
    g.add_edge("draft_souchi",   "draft_soufu")
    g.add_edge("draft_soufu",    "pegel_relay")
    g.add_edge("pegel_relay",    "persist")
    g.add_edge("persist",        "export")
    g.add_edge("export",         END)
    return g.compile()


async def run_police_report(
    case_id: str,
    case_facts: dict[str, Any],
    output_dir: str = "",
    doc_types: list[str] | None = None,
) -> dict[str, Any]:
    """Public entrypoint. Render 6-doc JP police packet + fire PEGEL ticks.

    Returns the final LangGraph state dict (documents, files, pegel_ticks,
    reporting_line, case_no, error).
    """
    graph = build_police_report_graph()
    initial: PoliceReportState = {
        "case_id": case_id,
        "case_facts": case_facts,
        "output_dir": output_dir,
        "doc_types": list(doc_types) if doc_types else list(DEFAULT_DOCS),
    }
    return await graph.ainvoke(initial)
