"""Intel dependency-graph inference primitives (ADR-0056 BPMN-as-actor).

Implements 10 Zeebe task types for the intel.etzhayyim.com actor:
  intel.run.create           — create vertex_intel_inference_run row
  intel.candidate.scan       — scan vertex_intel_subject for infer candidates
  intel.owl.validate         — ontology consistency check on candidates
  intel.langgraph.resolve    — LLM-backed edge proposal from valid candidates
  intel.edge.materialize     — write resolved edges to edge_intel_dependency
  intel.entity.resolve       — fuzzy entity lookup across vertex_intel_subject
  intel.dependency.list      — paginated edge list by status/predicate
  intel.dependency.explain   — narrative explanation for a specific edge
  intel.graph.counterparty   — counterparty relationship subgraph
  intel.graph.buildingOwnership — building ownership chain

All DB writes use sync_cursor (psycopg3 sync pool, RisingWave PG :4566).
LLM calls use pymagatama.llm.call_tier_json (Murakumo → LiteLLM fleet).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pymagatama.kotoba_datomic import get_kotoba_client
from pymagatama import llm as _llm


def _run_vid(run_id: str) -> str:
    return f"at://{_OWNER_DID}/{_COLLECTION_RUN}/{run_id}"


def _edge_id(src: str, dst: str, predicate: str) -> str:
    h = __import__("hashlib").sha256(f"{src}:{dst}:{predicate}".encode()).hexdigest()[:24]
    return f"at://{_OWNER_DID}/{_COLLECTION_EDGE}/{h}"


# ---------------------------------------------------------------------------
# intel.run.create
# ---------------------------------------------------------------------------

def task_intel_run_create(
    scope: dict | None = None,
    triggerKind: str = "scheduled",
    dryRun: bool = False,
) -> dict:
    run_id = uuid.uuid4().hex[:16]
    vid = _run_vid(run_id)
    now = _utc_now()
    scope_json = json.dumps(scope or {}, separators=(",", ":"), ensure_ascii=False)
    if not dryRun:
        try:
            with sync_cursor() as cur:
                cur.execute(
                    "INSERT INTO vertex_intel_inference_run "
                    "(vertex_id, run_id, trigger_kind, scope_json, status, started_at, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (vid, run_id, str(triggerKind), scope_json, "running", now, now),
                )
        except Exception as e:  # noqa: BLE001
            return {"error": f"intel.run.create failed: {e}", "runId": run_id, "vertexId": vid}
    return {"runId": run_id, "vertexId": vid, "status": "running", "dryRun": bool(dryRun)}


# ---------------------------------------------------------------------------
# intel.candidate.scan
# ---------------------------------------------------------------------------

def task_intel_candidate_scan(
    runId: str = "",
    scope: dict | None = None,
    maxCandidates: int = 50,
) -> dict:
    s = scope or {}
    subject_kind = str(s.get("subjectKind") or s.get("entityKind") or "")
    limit = max(1, min(int(maxCandidates or 50), 200))
    where_clauses = ["status IS DISTINCT FROM 'archived'"]
    args: list[Any] = []
    if subject_kind:
        where_clauses.append("subject_kind = %s")
        args.append(subject_kind)
    lei_filter = str(s.get("lei") or "").strip()
    if lei_filter:
        where_clauses.append("lei = %s")
        args.append(lei_filter)
    sql = (
        "SELECT vertex_id, subject_kind, canonical_key, label, lei, "
        "jurisdiction, attributes_json "
        "FROM vertex_intel_subject "
        "WHERE " + " AND ".join(where_clauses) +
        f" ORDER BY created_at DESC LIMIT {limit}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, tuple(args))
            rows = cur.fetchall() or []
        candidates = [
            {
                "vertexId": r[0], "subjectKind": r[1], "canonicalKey": r[2],
                "label": r[3], "lei": r[4], "jurisdiction": r[5],
                "attributes": json.loads(r[6] or "{}"),
            }
            for r in rows
        ]
    except Exception as e:  # noqa: BLE001
        return {"error": f"intel.candidate.scan failed: {e}", "candidates": [], "count": 0}
    return {"candidates": candidates, "count": len(candidates), "runId": runId}


# ---------------------------------------------------------------------------
# intel.owl.validate
# ---------------------------------------------------------------------------

_VALID_SUBJECT_KINDS = {
    "organization", "company", "person", "building", "property",
    "fund", "government", "exchange", "blockchain_address",
}
_VALID_PREDICATES = {
    "OWNS", "CONTROLS", "SUPPLIES_TO", "CONTRACTS_WITH", "EMPLOYS",
    "SUBSIDIARY_OF", "MEMBER_OF", "LEASES", "AUDITS", "INVESTS_IN",
}


def task_intel_owl_validate(
    runId: str = "",
    candidates: list | None = None,
) -> dict:
    cands = candidates if isinstance(candidates, list) else []
    valid: list[dict] = []
    invalid_count = 0
    for c in cands:
        if not isinstance(c, dict):
            invalid_count += 1
            continue
        kind = str(c.get("subjectKind") or "")
        if not kind or kind.lower() not in _VALID_SUBJECT_KINDS:
            invalid_count += 1
            continue
        if not str(c.get("vertexId") or "").strip():
            invalid_count += 1
            continue
        valid.append(c)
    return {
        "validCandidates": valid,
        "validCount": len(valid),
        "invalidCount": invalid_count,
        "runId": runId,
    }


# ---------------------------------------------------------------------------
# intel.langgraph.resolve
# ---------------------------------------------------------------------------

_RESOLVE_PROMPT = (
    "You are an intelligence analyst. Given a list of subject entities, "
    "identify likely dependency edges between them. "
    "Return a JSON array of edges, each with keys: "
    "srcVertexId, dstVertexId, predicate (one of: OWNS|CONTROLS|SUPPLIES_TO|"
    "CONTRACTS_WITH|EMPLOYS|SUBSIDIARY_OF|MEMBER_OF|LEASES|AUDITS|INVESTS_IN), "
    "confidence (0.0-1.0), evidenceSummary (1 sentence). "
    "Only include edges with confidence >= 0.5. "
    "Return only the JSON array, no explanation.\n\nEntities:\n"
)


def task_intel_langgraph_resolve(
    runId: str = "",
    validCandidates: list | None = None,
) -> dict:
    cands = validCandidates if isinstance(validCandidates, list) else []
    if not cands:
        return {"resolvedEdges": [], "runId": runId}

    entity_lines = "\n".join(
        f"- {c.get('label') or c.get('canonicalKey') or c.get('vertexId')} "
        f"({c.get('subjectKind')}, lei={c.get('lei') or 'unknown'}, "
        f"jurisdiction={c.get('jurisdiction') or 'unknown'})"
        for c in cands[:20]
    )
    prompt = _RESOLVE_PROMPT + entity_lines

    try:
        result = _llm.call_tier_json(
            tier="standard",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            timeout_sec=45.0,
        )
        if isinstance(result, list):
            edges = [e for e in result if isinstance(e, dict) and e.get("srcVertexId")]
        elif isinstance(result, dict) and isinstance(result.get("edges"), list):
            edges = result["edges"]
        else:
            edges = []
    except Exception as e:  # noqa: BLE001
        return {"error": f"intel.langgraph.resolve LLM failed: {e}", "resolvedEdges": [], "runId": runId}

    return {"resolvedEdges": edges, "count": len(edges), "runId": runId}


# ---------------------------------------------------------------------------
# intel.edge.materialize
# ---------------------------------------------------------------------------

def task_intel_edge_materialize(
    runId: str = "",
    resolvedEdges: list | None = None,
    dryRun: bool = False,
) -> dict:
    edges = resolvedEdges if isinstance(resolvedEdges, list) else []
    active_count = 0
    review_count = 0
    now = _utc_now()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        src = str(edge.get("srcVertexId") or "").strip()
        dst = str(edge.get("dstVertexId") or "").strip()
        predicate = str(edge.get("predicate") or "").strip().upper()
        confidence = float(edge.get("confidence") or 0.5)
        if not src or not dst or not predicate:
            continue
        status = "active" if confidence >= 0.75 else "review"
        edge_id = _edge_id(src, dst, predicate)
        evidence = json.dumps(
            {"summary": str(edge.get("evidenceSummary") or ""), "runId": runId},
            separators=(",", ":"), ensure_ascii=False,
        )
        if not dryRun:
            try:
                with sync_cursor() as cur:
                    cur.execute(
                        "INSERT INTO edge_intel_dependency "
                        "(edge_id, src_vid, dst_vid, predicate, confidence, "
                        "evidence_count, evidence_json, inference_run_id, status, "
                        "valid_from, created_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (edge_id, src, dst, predicate, confidence,
                         1, evidence, runId, status, now, now),
                    )
            except Exception:  # noqa: BLE001
                pass
        if status == "active":
            active_count += 1
        else:
            review_count += 1
    candidate_count = active_count + review_count
    if runId and not dryRun:
        try:
            with sync_cursor() as cur:
                cur.execute(
                    "UPDATE vertex_intel_inference_run "
                    "SET status = %s, candidate_count = %s, active_count = %s, "
                    "review_count = %s, completed_at = %s "
                    "WHERE run_id = %s",
                    ("completed", candidate_count, active_count, review_count, now, runId),
                )
        except Exception:  # noqa: BLE001
            pass
    return {
        "candidateCount": candidate_count,
        "activeCount": active_count,
        "reviewCount": review_count,
        "runId": runId,
    }


# ---------------------------------------------------------------------------
# intel.entity.resolve
# ---------------------------------------------------------------------------

def task_intel_entity_resolve(
    runId: str = "",
    query: str = "",
    entityKind: str = "",
    hints: dict | None = None,
    maxCandidates: int = 10,
) -> dict:
    limit = max(1, min(int(maxCandidates or 10), 50))
    q = str(query or "").strip()
    if not q:
        return {"candidates": [], "count": 0, "runId": runId}

    where_clauses: list[str] = []
    args: list[Any] = []
    if entityKind:
        where_clauses.append("subject_kind = %s")
        args.append(str(entityKind))
    h = hints or {}
    if h.get("lei"):
        where_clauses.append("lei = %s")
        args.append(str(h["lei"]))
    if h.get("jurisdiction"):
        where_clauses.append("jurisdiction = %s")
        args.append(str(h["jurisdiction"]))
    # Text match on label or canonical_key
    where_clauses.append("(label ILIKE %s OR canonical_key ILIKE %s)")
    pattern = f"%{q}%"
    args.extend([pattern, pattern])

    sql = (
        "SELECT vertex_id, subject_kind, canonical_key, label, lei, jurisdiction "
        "FROM vertex_intel_subject "
        + ("WHERE " + " AND ".join(where_clauses) if where_clauses else "") +
        f" ORDER BY label ASC LIMIT {limit}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, tuple(args))
            rows = cur.fetchall() or []
        candidates = [
            {"vertexId": r[0], "subjectKind": r[1], "canonicalKey": r[2],
             "label": r[3], "lei": r[4], "jurisdiction": r[5]}
            for r in rows
        ]
    except Exception as e:  # noqa: BLE001
        return {"error": f"intel.entity.resolve failed: {e}", "candidates": [], "count": 0}
    return {"candidates": candidates, "count": len(candidates), "runId": runId}


# ---------------------------------------------------------------------------
# intel.dependency.list
# ---------------------------------------------------------------------------

def task_intel_dependency_list(
    status: str = "",
    predicate: str = "",
    limit: int = 20,
    offset: int = 0,
) -> dict:
    lim = max(1, min(int(limit or 20), 100))
    off = max(0, int(offset or 0))
    where: list[str] = []
    args: list[Any] = []
    if status:
        where.append("status = %s")
        args.append(str(status))
    if predicate:
        where.append("predicate = %s")
        args.append(str(predicate).upper())
    sql = (
        "SELECT edge_id, src_vid, dst_vid, predicate, confidence, status, "
        "evidence_count, evidence_json, inference_run_id, valid_from "
        "FROM edge_intel_dependency "
        + ("WHERE " + " AND ".join(where) if where else "") +
        f" ORDER BY confidence DESC LIMIT {lim} OFFSET {off}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, tuple(args))
            rows = cur.fetchall() or []
        edges = [
            {"edgeId": r[0], "srcVid": r[1], "dstVid": r[2], "predicate": r[3],
             "confidence": r[4], "status": r[5], "evidenceCount": r[6],
             "evidence": json.loads(r[7] or "{}"), "inferenceRunId": r[8],
             "validFrom": r[9]}
            for r in rows
        ]
    except Exception as e:  # noqa: BLE001
        return {"error": f"intel.dependency.list failed: {e}", "edges": [], "count": 0}
    return {"edges": edges, "count": len(edges)}


# ---------------------------------------------------------------------------
# intel.dependency.explain
# ---------------------------------------------------------------------------

def task_intel_dependency_explain(
    edgeId: str = "",
    fromVertexId: str = "",
    toVertexId: str = "",
    predicate: str = "",
) -> dict:
    # Fetch the edge
    edge: dict[str, Any] = {}
    try:
        with sync_cursor() as cur:
            if edgeId:
                cur.execute(
                    "SELECT edge_id, src_vid, dst_vid, predicate, confidence, "
                    "status, evidence_json, inference_run_id "
                    "FROM edge_intel_dependency WHERE edge_id = %s LIMIT 1",
                    (edgeId,),
                )
            else:
                cur.execute(
                    "SELECT edge_id, src_vid, dst_vid, predicate, confidence, "
                    "status, evidence_json, inference_run_id "
                    "FROM edge_intel_dependency "
                    "WHERE src_vid = %s AND dst_vid = %s AND predicate = %s LIMIT 1",
                    (fromVertexId, toVertexId, str(predicate).upper()),
                )
            row = cur.fetchone()
            if row:
                edge = {
                    "edgeId": row[0], "srcVid": row[1], "dstVid": row[2],
                    "predicate": row[3], "confidence": row[4], "status": row[5],
                    "evidence": json.loads(row[6] or "{}"),
                    "inferenceRunId": row[7],
                }
    except Exception as e:  # noqa: BLE001
        return {"error": f"intel.dependency.explain failed: {e}", "edge": {}, "explanation": ""}

    if not edge:
        return {"edge": {}, "explanation": "Edge not found.", "found": False}

    explanation = (
        f"Entity {edge['srcVid']} {edge['predicate']} entity {edge['dstVid']} "
        f"(confidence={edge['confidence']:.2f}, status={edge['status']}). "
        f"{edge['evidence'].get('summary', 'No evidence summary available.')}"
    )
    return {"edge": edge, "explanation": explanation, "found": True}


# ---------------------------------------------------------------------------
# intel.graph.counterparty
# ---------------------------------------------------------------------------

def task_intel_graph_counterparty(
    subjectVertexId: str = "",
    lei: str = "",
    relationKinds: list | None = None,
    limit: int = 20,
) -> dict:
    lim = max(1, min(int(limit or 20), 100))
    subject_vid = str(subjectVertexId or "").strip()
    subject_lei = str(lei or "").strip()
    if not subject_vid and not subject_lei:
        return {"error": "subjectVertexId or lei required", "nodes": [], "edges": [], "count": 0}

    kinds = [str(k).upper() for k in (relationKinds or []) if isinstance(k, str)]
    where_parts = []
    args: list[Any] = []
    if subject_vid:
        where_parts.append("(e.src_vid = %s OR e.dst_vid = %s)")
        args.extend([subject_vid, subject_vid])
    if subject_lei:
        where_parts.append("(s.lei = %s OR t.lei = %s)")
        args.extend([subject_lei, subject_lei])
    if kinds:
        placeholders = ",".join(["%s"] * len(kinds))
        where_parts.append(f"e.predicate IN ({placeholders})")
        args.extend(kinds)

    sql = (
        "SELECT e.edge_id, e.src_vid, e.dst_vid, e.predicate, e.confidence, "
        "s.label AS src_label, t.label AS dst_label "
        "FROM edge_intel_dependency e "
        "LEFT JOIN vertex_intel_subject s ON s.vertex_id = e.src_vid "
        "LEFT JOIN vertex_intel_subject t ON t.vertex_id = e.dst_vid "
        + ("WHERE " + " AND ".join(where_parts) if where_parts else "") +
        f" ORDER BY e.confidence DESC LIMIT {lim}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, tuple(args))
            rows = cur.fetchall() or []
    except Exception as e:  # noqa: BLE001
        return {"error": f"intel.graph.counterparty failed: {e}", "nodes": [], "edges": [], "count": 0}

    node_map: dict[str, dict] = {}
    edges: list[dict] = []
    for r in rows:
        edge_id, src_vid, dst_vid, predicate, confidence, src_label, dst_label = r
        if src_vid:
            node_map[src_vid] = {"vertexId": src_vid, "label": src_label or src_vid}
        if dst_vid:
            node_map[dst_vid] = {"vertexId": dst_vid, "label": dst_label or dst_vid}
        edges.append({"edgeId": edge_id, "srcVid": src_vid, "dstVid": dst_vid,
                      "predicate": predicate, "confidence": confidence})
    return {"nodes": list(node_map.values()), "edges": edges, "count": len(edges)}


# ---------------------------------------------------------------------------
# intel.graph.buildingOwnership
# ---------------------------------------------------------------------------

def task_intel_graph_building_ownership(
    buildingVertexId: str = "",
    lei: str = "",
    bbox: list | None = None,
    limit: int = 10,
) -> dict:
    lim = max(1, min(int(limit or 10), 50))
    building_vid = str(buildingVertexId or "").strip()
    owner_lei = str(lei or "").strip()
    if not building_vid and not owner_lei:
        return {"error": "buildingVertexId or lei required", "chain": [], "count": 0}

    where_parts = ["e.predicate IN ('OWNS', 'LEASES', 'CONTROLS')"]
    args: list[Any] = []
    if building_vid:
        where_parts.append("e.dst_vid = %s")
        args.append(building_vid)
    if owner_lei:
        where_parts.append("s.lei = %s")
        args.append(owner_lei)

    sql = (
        "SELECT e.edge_id, e.src_vid, e.dst_vid, e.predicate, e.confidence, "
        "s.label AS owner_label, s.lei AS owner_lei "
        "FROM edge_intel_dependency e "
        "LEFT JOIN vertex_intel_subject s ON s.vertex_id = e.src_vid "
        "WHERE " + " AND ".join(where_parts) +
        f" ORDER BY e.confidence DESC LIMIT {lim}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, tuple(args))
            rows = cur.fetchall() or []
    except Exception as e:  # noqa: BLE001
        return {"error": f"intel.graph.buildingOwnership failed: {e}", "chain": [], "count": 0}

    chain = [
        {"edgeId": r[0], "ownerVid": r[1], "buildingVid": r[2], "relation": r[3],
         "confidence": r[4], "ownerLabel": r[5], "ownerLei": r[6]}
        for r in rows
    ]
    return {"chain": chain, "count": len(chain)}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(worker: Any, *, timeout_ms: int) -> None:
    """Wire intel primitives onto the shared LangServer worker."""

    def t(name: str, fn: Any, *, timeout: int | None = None) -> None:
        worker.task(
            task_type=name,
            single_value=False,
            timeout_ms=timeout if timeout is not None else timeout_ms,
        )(fn)

    t("intel.run.create", task_intel_run_create)
    t("intel.candidate.scan", task_intel_candidate_scan)
    t("intel.owl.validate", task_intel_owl_validate)
    t("intel.langgraph.resolve", task_intel_langgraph_resolve,
      timeout=max(timeout_ms, 60_000))
    t("intel.edge.materialize", task_intel_edge_materialize)
    t("intel.entity.resolve", task_intel_entity_resolve)
    t("intel.dependency.list", task_intel_dependency_list)
    t("intel.dependency.explain", task_intel_dependency_explain)
    t("intel.graph.counterparty", task_intel_graph_counterparty)
    t("intel.graph.buildingOwnership", task_intel_graph_building_ownership)


__all__ = [
    "register",
    "task_intel_run_create",
    "task_intel_candidate_scan",
    "task_intel_owl_validate",
    "task_intel_langgraph_resolve",
    "task_intel_edge_materialize",
    "task_intel_entity_resolve",
    "task_intel_dependency_list",
    "task_intel_dependency_explain",
    "task_intel_graph_counterparty",
    "task_intel_graph_building_ownership",
]
