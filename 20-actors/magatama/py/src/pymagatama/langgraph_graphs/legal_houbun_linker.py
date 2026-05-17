"""
legal.houbunLinker — infer LEI / contract / Japanese law-article links.

Graph:
  START -> load_candidates -> infer_links -> persist_links -> emit_audit -> END

The graph writes hypotheses first. Promoted edge rows are still marked
`status='inferred'`; review/gate promotion can move them to verified later.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from typing import Any, TypedDict

from pymagatama import llm
from pymagatama.db_sync import sync_cursor


OWNER_DID = "did:web:legal-intel.etzhayyim.com"
RUN_COLLECTION = "ai.gftd.apps.legalHoubun.linkRun"
HYP_COLLECTION = "ai.gftd.apps.legalHoubun.linkHypothesis"


class LegalHoubunLinkerState(TypedDict, total=False):
    country: str
    jurisdiction: str
    maxEntities: int
    maxArticles: int
    minConfidence: float
    dryRun: bool
    legalEntityVid: str
    contractVid: str
    llmTier: str
    _entities: list[dict[str, Any]]
    _articles: list[dict[str, Any]]
    _contracts: list[dict[str, Any]]
    hypotheses: list[dict[str, Any]]
    runId: str
    runVertexId: str
    hypothesisRows: int
    edgeRows: int
    model: str
    ok: bool
    error: str | None


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _vid(collection: str) -> str:
    return f"at://{OWNER_DID}/{collection}/{int(time.time() * 1000)}-{uuid.uuid4().hex[:10]}"


def _safe_rows(sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
    try:
        with sync_cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() or []
    except Exception:
        return []


def _json_loads_maybe(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    return json.loads(raw)


def _fallback_hypotheses(
    entities: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    articles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Conservative deterministic fallback when the LLM is unavailable."""
    if not articles:
        return []
    out: list[dict[str, Any]] = []
    company_article = next(
        (
            a
            for a in articles
            if "companies" in str(a.get("lawId") or "")
            or "会社" in str(a.get("title") or "")
            or "法人" in str(a.get("text") or "")
        ),
        articles[0],
    )
    contract_article = next(
        (
            a
            for a in articles
            if "contract" in str(a.get("lawId") or "")
            or "契約" in str(a.get("title") or "")
            or "契約" in str(a.get("text") or "")
        ),
        articles[0],
    )
    for entity in entities[:5]:
        out.append(
            {
                "subjectVid": entity["vertexId"],
                "subjectKind": "legal_entity",
                "articleVid": company_article["vertexId"],
                "relationType": "governed_by",
                "confidence": 0.55,
                "rationale": "Fallback heuristic: Japanese legal entity links to corporate-law article candidate.",
                "evidence": [entity.get("name", ""), company_article.get("title", "")],
            }
        )
    for contract in contracts[:5]:
        out.append(
            {
                "subjectVid": contract["vertexId"],
                "subjectKind": "contract",
                "articleVid": contract_article["vertexId"],
                "relationType": "has_legal_basis",
                "confidence": 0.55,
                "rationale": "Fallback heuristic: contract-like record links to contract/labor article candidate.",
                "evidence": [contract.get("title", ""), contract_article.get("title", "")],
            }
        )
    return out


def load_candidates(state: LegalHoubunLinkerState) -> dict:
    country = (state.get("country") or "JP").upper()
    jurisdiction = (state.get("jurisdiction") or "JPN").upper()
    max_entities = int(state.get("maxEntities") or 24)
    max_articles = int(state.get("maxArticles") or 48)
    entity_vid = (state.get("legalEntityVid") or "").strip()
    contract_vid = (state.get("contractVid") or "").strip()

    entity_rows = _safe_rows(
        f"""
        SELECT vertex_id, lei, legal_name, country, legal_form, registration_authority
        FROM vertex_open_lei_entity
        WHERE (%s = '' OR vertex_id = %s)
          AND (UPPER(COALESCE(country, '')) IN (%s, %s))
          AND status = 'active'
        ORDER BY next_renewal_at DESC NULLS LAST
        LIMIT {max_entities}
        """,
        (entity_vid, entity_vid, country, jurisdiction),
    )
    entities = [
        {
            "vertexId": r[0],
            "lei": r[1],
            "name": r[2],
            "country": r[3],
            "legalForm": r[4],
            "registrationAuthority": r[5],
        }
        for r in entity_rows
    ]

    contract_rows = _safe_rows(
        """
        SELECT vertex_id, name, legal_basis, country_code, url
        FROM vertex_governance_contract
        WHERE (%s = '' OR vertex_id = %s)
          AND (UPPER(COALESCE(country_code, '')) IN (%s, %s, ''))
        ORDER BY effective_date DESC NULLS LAST
        LIMIT 12
        """,
        (contract_vid, contract_vid, country, jurisdiction),
    )
    contracts = [
        {
            "vertexId": r[0],
            "title": r[1],
            "legalBasis": r[2],
            "country": r[3],
            "url": r[4],
        }
        for r in contract_rows
    ]

    houbun_rows = _safe_rows(
        f"""
        SELECT vertex_id, 'houbun' AS source_kind, statute_ref, article_no, title,
               COALESCE(text, '') AS body
        FROM vertex_houbun_article
        WHERE UPPER(COALESCE(language, '')) IN ('JA', 'JPN', 'JAPANESE', '')
           OR statute_ref ILIKE '%%jpn%%'
        ORDER BY
          CASE
            WHEN text ILIKE '%%法人%%' OR title ILIKE '%%法人%%' THEN 0
            WHEN text ILIKE '%%会社%%' OR title ILIKE '%%会社%%' THEN 1
            WHEN text ILIKE '%%契約%%' OR title ILIKE '%%契約%%' THEN 2
            WHEN text ILIKE '%%登記%%' OR title ILIKE '%%登記%%' THEN 3
            ELSE 9
          END,
          article_no
        LIMIT {max_articles}
        """,
    )
    hourei_rows = _safe_rows(
        f"""
        SELECT vertex_id, 'hourei' AS source_kind, hourei_id, article_no, title,
               COALESCE(summary, text, '') AS body
        FROM vertex_hourei_jobun
        ORDER BY article_no
        LIMIT {max_articles}
        """,
    )
    article_rows = (houbun_rows + hourei_rows)[:max_articles]
    articles = [
        {
            "vertexId": r[0],
            "sourceKind": r[1],
            "lawId": r[2],
            "articleNo": r[3],
            "title": r[4],
            "text": (r[5] or "")[:700],
        }
        for r in article_rows
    ]

    return {
        "_entities": entities,
        "_contracts": contracts,
        "_articles": articles,
        "ok": True,
        "error": None,
    }


def infer_links(state: LegalHoubunLinkerState) -> dict:
    entities = state.get("_entities") or []
    contracts = state.get("_contracts") or []
    articles = state.get("_articles") or []
    if not entities and not contracts:
        return {"hypotheses": [], "ok": True, "error": "no legal entities or contracts to link"}
    if not articles:
        return {"hypotheses": [], "ok": False, "error": "no houbun/hourei articles available"}

    system = (
        "You infer legal graph links. Return strict JSON only. "
        "Use relationType governed_by for legal_entity -> article, "
        "has_legal_basis for contract -> article, and depends_on_contract only "
        "when an entity explicitly depends on a contract. Do not invent statutes. "
        "Low certainty is allowed; confidence must be 0..1."
    )
    user = json.dumps(
        {
            "task": "Infer Japanese legal-entity / contract links to law articles.",
            "legalEntities": entities[:20],
            "contracts": contracts[:10],
            "articles": articles[:40],
            "outputSchema": {
                "links": [
                    {
                        "subjectVid": "vertex id from legalEntities or contracts",
                        "subjectKind": "legal_entity|contract",
                        "articleVid": "vertex id from articles",
                        "relationType": "governed_by|has_legal_basis|regulated_by",
                        "confidence": 0.0,
                        "rationale": "short reason",
                        "evidence": ["short evidence strings"],
                    }
                ]
            },
        },
        ensure_ascii=False,
    )

    tier = state.get("llmTier") or "structured"
    try:
        resp = llm.call_tier(
            tier,
            system,
            user,
            max_tokens=900,
            temperature=0.1,
            timeout_sec=20.0,
            extra={"response_format": {"type": "json_object"}},
        )
        parsed = _json_loads_maybe(resp.get("content") or "")
        links = parsed.get("links") if isinstance(parsed, dict) else []
        model = resp.get("model") or tier
    except Exception as exc:
        links = _fallback_hypotheses(entities, contracts, articles)
        model = f"fallback:{type(exc).__name__}"
    if not links:
        links = _fallback_hypotheses(entities, contracts, articles)
        model = f"{model or tier}:fallback-empty"

    valid_subjects = {r["vertexId"] for r in entities} | {r["vertexId"] for r in contracts}
    valid_articles = {r["vertexId"] for r in articles}
    hypotheses: list[dict[str, Any]] = []
    for link in links or []:
        if not isinstance(link, dict):
            continue
        subject = str(link.get("subjectVid") or "")
        article = str(link.get("articleVid") or "")
        if subject not in valid_subjects or article not in valid_articles:
            continue
        try:
            confidence = max(0.0, min(1.0, float(link.get("confidence") or 0.0)))
        except (TypeError, ValueError):
            confidence = 0.0
        hypotheses.append(
            {
                "subjectVid": subject,
                "subjectKind": str(link.get("subjectKind") or "legal_entity"),
                "articleVid": article,
                "relationType": str(link.get("relationType") or "governed_by"),
                "confidence": confidence,
                "rationale": str(link.get("rationale") or "")[:1200],
                "evidence": link.get("evidence") if isinstance(link.get("evidence"), list) else [],
            }
        )

    return {"hypotheses": hypotheses, "model": model, "ok": True, "error": None}


def persist_links(state: LegalHoubunLinkerState) -> dict:
    hypotheses = state.get("hypotheses") or []
    now = _now_iso()
    today = now[:10]
    run_id = f"legal-houbun-link-{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
    run_vid = _vid(RUN_COLLECTION)
    min_conf = float(state.get("minConfidence") or 0.55)
    dry_run = bool(state.get("dryRun") or False)
    if dry_run:
        return {
            "runId": run_id,
            "runVertexId": run_vid,
            "hypothesisRows": 0,
            "edgeRows": 0,
            "ok": True,
        }

    hyp_rows = 0
    edge_rows = 0
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_legal_houbun_link_run
              (vertex_id, run_id, country, jurisdiction, entity_count, contract_count,
               article_count, hypothesis_count, model, status, started_at, completed_at,
               created_date, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s)
            """,
            (
                run_vid,
                run_id,
                state.get("country") or "JP",
                state.get("jurisdiction") or "JPN",
                len(state.get("_entities") or []),
                len(state.get("_contracts") or []),
                len(state.get("_articles") or []),
                len(hypotheses),
                state.get("model") or "",
                "completed",
                now,
                now,
                today,
                OWNER_DID,
            ),
        )
        for hyp in hypotheses:
            hyp_vid = _vid(HYP_COLLECTION)
            status = "pending_review"
            cur.execute(
                """
                INSERT INTO vertex_legal_houbun_link_hypothesis
                  (vertex_id, run_id, subject_vid, subject_kind, article_vid,
                   relation_type, confidence, rationale, evidence_json, status,
                   model, created_at, created_date, sensitivity_ord, owner_did)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s)
                """,
                (
                    hyp_vid,
                    run_id,
                    hyp["subjectVid"],
                    hyp["subjectKind"],
                    hyp["articleVid"],
                    hyp["relationType"],
                    hyp["confidence"],
                    hyp["rationale"],
                    json.dumps(hyp.get("evidence") or [], ensure_ascii=False),
                    status,
                    state.get("model") or "",
                    now,
                    today,
                    OWNER_DID,
                ),
            )
            hyp_rows += 1
            if float(hyp["confidence"]) < min_conf:
                continue
            table = (
                "edge_contract_houbun_article"
                if hyp["subjectKind"] == "contract"
                else "edge_legal_entity_houbun_article"
            )
            edge_id = "edge:" + uuid.uuid4().hex
            cur.execute(
                f"""
                INSERT INTO {table}
                  (edge_id, src_vid, dst_vid, relation_type, confidence,
                   hypothesis_vid, status, created_at, created_date,
                   sensitivity_ord, owner_did)
                VALUES (%s,%s,%s,%s,%s,%s,'inferred',%s,%s,0,%s)
                """,
                (
                    edge_id,
                    hyp["subjectVid"],
                    hyp["articleVid"],
                    hyp["relationType"],
                    hyp["confidence"],
                    hyp_vid,
                    now,
                    today,
                    OWNER_DID,
                ),
            )
            edge_rows += 1

    return {
        "runId": run_id,
        "runVertexId": run_vid,
        "hypothesisRows": hyp_rows,
        "edgeRows": edge_rows,
        "ok": True,
        "error": None,
    }


def emit_audit(state: LegalHoubunLinkerState) -> dict:
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_repo_commit
                  (vertex_id, repo, collection, rkey, action, ts_ms, record_json)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    str(uuid.uuid4()),
                    OWNER_DID,
                    RUN_COLLECTION,
                    f"lg-{int(time.time() * 1000)}",
                    "create",
                    int(time.time() * 1000),
                    json.dumps(
                        {
                            "runId": state.get("runId"),
                            "hypothesisRows": state.get("hypothesisRows", 0),
                            "edgeRows": state.get("edgeRows", 0),
                            "ok": state.get("ok", False),
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
    except Exception:
        pass
    return {}


def build_graph():
    from langgraph.graph import END, StateGraph

    builder = StateGraph(LegalHoubunLinkerState)
    builder.add_node("load_candidates", load_candidates)
    builder.add_node("infer_links", infer_links)
    builder.add_node("persist_links", persist_links)
    builder.add_node("emit_audit", emit_audit)
    builder.set_entry_point("load_candidates")
    builder.add_edge("load_candidates", "infer_links")
    builder.add_edge("infer_links", "persist_links")
    builder.add_edge("persist_links", "emit_audit")
    builder.add_edge("emit_audit", END)
    return builder.compile()
