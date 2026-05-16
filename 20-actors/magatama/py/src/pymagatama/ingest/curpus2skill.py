"""curpus2skill handlers for BPMN + Zeebe.

Conservative corpus -> canonical ESCO skill evidence extraction. The task
writes edge_corpus_skill_evidence rows only; it does not create vertex_skill.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
import unicodedata
from typing import Any

from pymagatama.db_sync import sync_cursor

VERSION = "curpus2skill-langserver-v0.1.0"

SOURCES: dict[str, dict[str, str]] = {
    "legal-corpus": {
        "table": "vertex_legal_corpus_document",
        "actor_did": "did:web:legal-corpus.gftd.ai",
        "sql": """
            SELECT vertex_id, 'vertex_legal_corpus_document' AS corpus_table,
                   title, COALESCE(body_text, '') AS body,
                   COALESCE(topic_tags_csv, '') AS tags,
                   COALESCE(owner_did, 'did:web:legal-corpus.gftd.ai') AS owner_did,
                   COALESCE(source_id, 'unknown') AS source_license
            FROM vertex_legal_corpus_document
            WHERE body_text IS NOT NULL
              AND body_text NOT LIKE 'signal:v1:%%'
            LIMIT {limit}
        """,
    },
    "houbun-article": {
        "table": "vertex_houbun_article",
        "actor_did": "did:web:houbun.gftd.ai",
        "sql": """
            SELECT vertex_id, 'vertex_houbun_article' AS corpus_table,
                   title, COALESCE(text, '') AS body,
                   COALESCE(article_no, '') AS tags,
                   COALESCE(owner_did, 'did:web:houbun.gftd.ai') AS owner_did,
                   COALESCE(source_url, 'unknown') AS source_license
            FROM vertex_houbun_article
            WHERE text IS NOT NULL
              AND text NOT LIKE 'signal:v1:%%'
            LIMIT {limit}
        """,
    },
    "domain-knowledge": {
        "table": "vertex_domain_knowledge_chunk",
        "actor_did": "did:web:llm.gftd.ai",
        "sql": """
            SELECT c.vertex_id, 'vertex_domain_knowledge_chunk' AS corpus_table,
                   d.title, COALESCE(c.chunk_text, '') AS body,
                   COALESCE(c.keywords, '') AS tags,
                   COALESCE(d.owner_did, 'did:web:llm.gftd.ai') AS owner_did,
                   COALESCE(c.keywords, 'unknown') AS source_license
            FROM vertex_domain_knowledge_chunk c
            LEFT JOIN vertex_domain_knowledge_document d ON d.vertex_id = c.document_vid
            WHERE c.chunk_text IS NOT NULL
              AND c.chunk_text NOT LIKE 'signal:v1:%%'
            LIMIT {limit}
        """,
    },
}

STOPWORDS = {
    "and", "or", "the", "for", "with", "from", "that", "this", "into",
    "are", "was", "were", "have", "has", "not", "する", "こと", "ため",
    "及び", "また",
}

GENERIC_LABELS = {
    "assume responsibility",
    "communication",
    "delegate responsibilities",
    "manage data",
    "manage financial and material resources",
    "product comprehension",
    "provide membership service",
}


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "").lower())
    text = re.sub(r"[^\w+#.]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def tokens(value: str) -> list[str]:
    return [t for t in normalize(value).split(" ") if len(t) >= 2 and t not in STOPWORDS]


def label_usable(label: str) -> bool:
    ts = tokens(label)
    if label in GENERIC_LABELS:
        return False
    if len(ts) < 2 or len(label) < 14:
        return False
    if re.match(r"^(manage|provide|perform|carry out|execute|use|apply|follow)\s", label) and len(ts) < 4:
        return False
    return True


def parse_alt_labels(value: object) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(str(value))
        if isinstance(parsed, list):
            return [str(x) for x in parsed if x]
    except Exception:  # noqa: BLE001
        pass
    return [s.strip() for s in str(value).replace(";", "\n").splitlines() if s.strip()]


def stable_id(prefix: str, parts: list[object]) -> str:
    digest = hashlib.sha256("\x1f".join(str(p) for p in parts).encode()).hexdigest()[:24]
    return f"{prefix}:{digest}"


def load_skills(skill_limit: int) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT vertex_id, label, name, alt_labels, source_license
            FROM vertex_skill
            WHERE COALESCE(name, label, '') <> ''
            LIMIT {skill_limit}
            """
        )
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall() or []]
    out: list[dict[str, Any]] = []
    for row in rows:
        labels = [
            str(x) for x in [
                row.get("name"),
                row.get("label"),
                *parse_alt_labels(row.get("alt_labels")),
            ] if x
        ]
        norm_labels = sorted({normalize(label) for label in labels if len(label) >= 3})
        out.append({
            "skill_id": row.get("vertex_id"),
            "name": row.get("name") or row.get("label") or row.get("vertex_id"),
            "labels": norm_labels,
            "token_sets": [tokens(label) for label in norm_labels],
        })
    return out


def load_corpus(source: dict[str, str], limit: int) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(source["sql"].format(limit=limit))
        cols = [d[0] for d in cur.description] if cur.description else []
        return [dict(zip(cols, r)) for r in cur.fetchall() or []]


def evidence(normalized_doc: str, label: str) -> dict[str, Any]:
    idx = normalized_doc.find(label)
    if idx < 0:
        first = label.split(" ")[0]
        idx = normalized_doc.find(first)
        end = idx + len(first) if idx >= 0 else 0
    else:
        end = idx + len(label)
    if idx < 0:
        return {"text": normalized_doc[:220], "start": 0, "end": 0}
    return {"text": normalized_doc[max(0, idx - 80): end + 180], "start": idx, "end": end}


def score_skill(normalized_doc: str, skill: dict[str, Any], min_score: float) -> dict[str, Any] | None:
    if normalize(skill.get("name")) in GENERIC_LABELS:
        return None
    best: dict[str, Any] | None = None
    labels: list[str] = skill.get("labels") or []
    token_sets: list[list[str]] = skill.get("token_sets") or []
    for i, label in enumerate(labels):
        if not label_usable(label):
            continue
        if label in normalized_doc:
            best = {"score": min(0.99, 0.9 + min(0.09, len(label) / 180)), "match_kind": "exact_label", "label": label}
            continue
        ts = token_sets[i] if i < len(token_sets) else []
        if len(ts) >= 4 and all(t in normalized_doc for t in ts):
            score = 0.82 + min(0.07, len(ts) / 100)
            if best is None or score > float(best["score"]):
                best = {"score": score, "match_kind": "token_overlap", "label": label}
    if best is None or float(best["score"]) < min_score:
        return None
    best["evidence"] = evidence(normalized_doc, str(best["label"]))
    return best


def insert_run(run: dict[str, Any]) -> None:
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_corpus_skill_extraction_run (
              vertex_id, sensitivity_ord, owner_did, rkey, repo, label,
              source_table, source_actor_did, extractor_version, model_id,
              params_json, corpus_limit, skill_limit, min_score,
              matched_documents, emitted_edges, status, started_at, finished_at
            )
            SELECT %s,%s::BIGINT,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::BIGINT,
                   %s::BIGINT,%s::DOUBLE PRECISION,%s::BIGINT,%s::BIGINT,
                   %s,%s,%s
            WHERE NOT EXISTS (
              SELECT 1 FROM vertex_corpus_skill_extraction_run WHERE vertex_id = %s
            )
            """,
            (
                run["vertex_id"], 1, "did:web:recruit.gftd.ai", run["rkey"],
                "did:web:recruit.gftd.ai", run["label"], run["source_table"],
                run["source_actor_did"], VERSION, "lexical-v0",
                json.dumps(run["params"], ensure_ascii=False), run["corpus_limit"],
                run["skill_limit"], run["min_score"], run["matched_documents"],
                run["emitted_edges"], run["status"], run["started_at"],
                run["finished_at"], run["vertex_id"],
            ),
        )


def insert_edge(run_id: str, edge: dict[str, Any]) -> None:
    edge_id = stable_id(
        "edge:corpus-skill",
        [edge["corpus_table"], edge["corpus_vertex_id"], edge["skill_id"], edge["match_kind"]],
    )
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO edge_corpus_skill_evidence (
              edge_id, corpus_vertex_id, corpus_table, skill_id,
              extraction_run_id, source_actor_did, match_kind, score,
              evidence_text, evidence_start, evidence_end, source,
              source_license, ingested_at, props
            )
            SELECT %s,%s,%s,%s,%s,%s,%s,%s::DOUBLE PRECISION,%s,
                   %s::BIGINT,%s::BIGINT,%s,%s,%s,%s
            WHERE NOT EXISTS (
              SELECT 1 FROM edge_corpus_skill_evidence WHERE edge_id = %s
            )
            """,
            (
                edge_id, edge["corpus_vertex_id"], edge["corpus_table"],
                edge["skill_id"], run_id, edge["source_actor_did"],
                edge["match_kind"], edge["score"], edge["evidence_text"],
                edge["evidence_start"], edge["evidence_end"], "curpus2skill",
                edge.get("source_license"), edge["ingested_at"],
                json.dumps({"skillName": edge.get("skill_name")}, ensure_ascii=False),
                edge_id,
            ),
        )


async def task_curpus2skill_extract_evidence(
    source: str = "legal-corpus",
    limit: int = 10,
    skillLimit: int = 2000,
    minScore: float = 0.97,
    topK: int = 5,
    dryRun: bool = False,
) -> dict:
    source_key = source or "legal-corpus"
    if source_key not in SOURCES:
        return {"error": f"unknown source: {source_key}", "knownSources": sorted(SOURCES)}
    limit_i = max(1, min(int(limit or 10), 500))
    skill_limit_i = max(1, min(int(skillLimit or 2000), 20000))
    top_k_i = max(1, min(int(topK or 5), 20))
    min_score_f = max(0.0, min(float(minScore or 0.97), 1.0))
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    src = SOURCES[source_key]

    try:
        skills = await asyncio.to_thread(load_skills, skill_limit_i)
        docs = await asyncio.to_thread(load_corpus, src, limit_i)
    except Exception as e:  # noqa: BLE001
        return {"error": f"load failed: {e}", "source": source_key}

    edges: list[dict[str, Any]] = []
    for doc in docs:
        normalized_doc = normalize("\n".join(str(x or "") for x in [doc.get("title"), doc.get("tags"), doc.get("body")]))
        matches: list[dict[str, Any]] = []
        for skill in skills:
            scored = score_skill(normalized_doc, skill, min_score_f)
            if not scored:
                continue
            ev = scored["evidence"]
            matches.append({
                "corpus_vertex_id": doc.get("vertex_id"),
                "corpus_table": doc.get("corpus_table"),
                "skill_id": skill.get("skill_id"),
                "skill_name": skill.get("name"),
                "score": round(float(scored["score"]), 4),
                "match_kind": scored["match_kind"],
                "evidence_text": str(ev["text"])[:900],
                "evidence_start": int(ev["start"]),
                "evidence_end": int(ev["end"]),
                "source_actor_did": doc.get("owner_did") or src["actor_did"],
                "source_license": doc.get("source_license"),
                "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
        matches.sort(key=lambda e: e["score"], reverse=True)
        edges.extend(matches[:top_k_i])

    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    run_id = stable_id("run:curpus2skill", [source_key, started, limit_i, skill_limit_i, min_score_f])
    run = {
        "vertex_id": run_id,
        "rkey": re.sub(r"[^a-zA-Z0-9-]", "-", run_id)[:63],
        "label": f"curpus2skill {source_key} {started}",
        "source_table": src["table"],
        "source_actor_did": src["actor_did"],
        "params": {"source": source_key, "topK": top_k_i, "dryRun": bool(dryRun)},
        "corpus_limit": limit_i,
        "skill_limit": skill_limit_i,
        "min_score": min_score_f,
        "matched_documents": len({e["corpus_vertex_id"] for e in edges}),
        "emitted_edges": len(edges),
        "status": "dry_run" if dryRun else "completed",
        "started_at": started,
        "finished_at": finished,
    }
    if not dryRun:
        try:
            await asyncio.to_thread(insert_run, run)
            for edge in edges:
                await asyncio.to_thread(insert_edge, run_id, edge)
        except Exception as e:  # noqa: BLE001
            return {"error": f"write failed: {e}", "runId": run_id, "edgeCount": len(edges)}

    return {
        "runId": run_id,
        "source": source_key,
        "sourceTable": src["table"],
        "dryRun": bool(dryRun),
        "documentsScanned": len(docs),
        "skillsLoaded": len(skills),
        "matchedDocuments": run["matched_documents"],
        "emittedEdges": run["emitted_edges"],
        "sample": edges[:10],
    }
