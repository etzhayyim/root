from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
import uvicorn

OWNER_DID = "did:web:intel.etzhayyim.com"
ACTOR_ID = "sys.langserver.intel-dependency-worker"


def now_ms() -> int:
    return int(time.time() * 1000)


def stable_id(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"{prefix}-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def dict_row_factory() -> Any:
    pass


def is_missing_relation_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "table not found" in text
        or "table or source not found" in text
        or "relation" in text and "does not exist" in text
    )


@dataclass
class Candidate:
    src_vid: str
    dst_vid: str
    predicate: str
    dependency_kind: str
    confidence: float
    evidence: list[dict[str, Any]]
    reason: str


@dataclass
class TopologyNode:
    vertex_id: str
    vertex_kind: str
    display_name: str | None
    source_table: str


@dataclass
class TopologyEdge:
    edge_id: str
    src_vid: str
    dst_vid: str
    edge_table: str
    predicate: str
    dependency_direction: str
    confidence: float
    evidence: list[dict[str, Any]]
    reason: str


@dataclass
class TopologyOrderRow:
    graph_scope: str
    vertex_id: str
    display_name: str | None
    vertex_kind: str | None
    topo_rank: int
    reverse_topo_rank: int
    topo_level: int
    dependency_count: int
    dependent_count: int
    unresolved_dependency_count: int
    cycle_status: str
    payload_json: str


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def entity_match_score(query: str, name: str, *, lei: str | None = None, hints: dict[str, Any] | None = None) -> float:
    normalized_query = normalize_text(query)
    normalized_name = normalize_text(name)
    normalized_lei = normalize_text(lei)
    hint_lei = normalize_text((hints or {}).get("lei"))

    if hint_lei and normalized_lei and hint_lei == normalized_lei:
        return 0.98
    if normalized_query and normalized_lei and normalized_query == normalized_lei:
        return 0.97
    if normalized_query and normalized_name == normalized_query:
        return 0.94
    if normalized_query and normalized_name.startswith(normalized_query):
        return 0.86
    if normalized_query and normalized_query in normalized_name:
        return 0.78
    return 0.50


def entity_candidate(
    *,
    vertex_id: str,
    name: str,
    entity_kind: str | None,
    source: str,
    query: str,
    did: str | None = None,
    lei: str | None = None,
    domain: str | None = None,
    status: str | None = None,
    hints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    score = entity_match_score(query, name, lei=lei, hints=hints)
    return {
        "entityId": vertex_id,
        "vertexId": vertex_id,
        "did": did,
        "name": name,
        "entityKind": entity_kind,
        "lei": lei,
        "domain": domain,
        "status": status,
        "source": source,
        "score": round(score, 4),
        "reason": "exact or strong identifier/name match" if score >= 0.9 else "candidate name/identifier match",
    }


def looks_like_lei(value: Any) -> bool:
    text = str(value or "").strip().upper()
    return len(text) == 20 and text.isalnum()


def canonical_lei(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text if looks_like_lei(text) else None


def utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def utc_date() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def int_env(name: str, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    value = max(minimum, value)
    if maximum is not None:
        value = min(value, maximum)
    return value


def sql_ident(name: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise ValueError(f"unsafe SQL identifier: {name}")
    return f'"{name}"'


def dependency_hint(edge_table: str, predicate: str | None = None) -> dict[str, Any]:
    text = f"{edge_table} {predicate or ''}".lower()
    if "depends_on" in text or "dependency" in text:
        return {"isDependency": True, "direction": "src_depends_on_dst", "confidence": 0.95, "reason": "explicit dependency relation"}
    if "requires" in text or "_uses_" in text or text.endswith("_uses") or "uses_" in text:
        return {"isDependency": True, "direction": "src_depends_on_dst", "confidence": 0.88, "reason": "requires/uses relation"}
    if "consumes" in text or "input" in text:
        return {"isDependency": True, "direction": "src_depends_on_dst", "confidence": 0.80, "reason": "consumer depends on consumed/input vertex"}
    if "produces" in text or "emits" in text or "generates" in text or "enables" in text:
        return {"isDependency": True, "direction": "dst_depends_on_src", "confidence": 0.72, "reason": "output/enabled vertex depends on producer/enabler"}
    if "parent" in text or "contains" in text or "member" in text or "part_of" in text:
        return {"isDependency": False, "direction": "topology_only", "confidence": 0.35, "reason": "containment/topology relation, not execution dependency"}
    return {"isDependency": False, "direction": "unknown", "confidence": 0.25, "reason": "no dependency keyword"}


def open_lei_vertex_id(lei: str) -> str:
    return f"at://did:web:open-lei.etzhayyim.com/com.etzhayyim.apps.openLei.entity/{lei}"


def flatten_gleif_lei_record(record: dict[str, Any]) -> dict[str, Any] | None:
    attributes = record.get("attributes") if isinstance(record.get("attributes"), dict) else {}
    if not attributes:
        return None
    lei = canonical_lei(attributes.get("lei") or record.get("id"))
    if not lei:
        return None

    entity = attributes.get("entity") if isinstance(attributes.get("entity"), dict) else {}
    registration = attributes.get("registration") if isinstance(attributes.get("registration"), dict) else {}
    legal_name = entity.get("legalName")
    if isinstance(legal_name, dict):
        legal_name = legal_name.get("name")
    legal_address = entity.get("legalAddress") if isinstance(entity.get("legalAddress"), dict) else {}
    legal_form = entity.get("legalForm")
    registered_at = entity.get("registeredAt")
    registration_status = str(registration.get("status") or attributes.get("registrationStatus") or "UNKNOWN")

    return {
        "vertex_id": open_lei_vertex_id(lei),
        "lei": lei,
        "legal_name": str(legal_name or attributes.get("legalName") or lei),
        "country": legal_address.get("country") or entity.get("legalJurisdiction"),
        "legal_form": legal_form.get("id") if isinstance(legal_form, dict) else legal_form,
        "registration_authority": registered_at.get("id") if isinstance(registered_at, dict) else registered_at,
        "registration_status": registration_status,
        "issued_at": registration.get("initialRegistrationDate") or attributes.get("issuedAt"),
        "next_renewal_at": registration.get("nextRenewalDate") or attributes.get("nextRenewalAt"),
        "status": "active" if registration_status == "ISSUED" else "lapsed",
        "created_at": utc_iso(),
    }


def fetch_gleif_lei_record(lei: str) -> dict[str, Any] | None:
    base = os.environ.get("INTEL_GLEIF_API_BASE", "https://api.gleif.org/api/v1/lei-records").rstrip("/")
    url = f"{base}/{urllib.parse.quote(lei)}"
    headers = {
        "Accept": "application/vnd.api+json, application/json",
        "User-Agent": os.environ.get("INTEL_GLEIF_USER_AGENT", "etzhayyim-intel-resolver/1.0"),
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    timeout = float(os.environ.get("INTEL_GLEIF_TIMEOUT_SEC", "8"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(512 * 1024)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return None
    data = parsed.get("data")
    if not isinstance(data, dict):
        return None
    return flatten_gleif_lei_record(data)


def llm_config() -> tuple[str, str, str | None]:
    url = (
        os.environ.get("INTEL_LLM_URL")
        or os.environ.get("RUNPOD_LLM_URL")
        or os.environ.get("LLM_BASE_URL")
        or "https://llm.etzhayyim.com/v1/chat/completions"
    ).strip()
    if url and not url.endswith("/chat/completions"):
        url = url.rstrip("/") + "/v1/chat/completions"
    model = (
        os.environ.get("INTEL_LLM_MODEL")
        or os.environ.get("RUNPOD_LLM_MODEL")
        or "qwen2.5:7b-instruct-q5_K_M"
    ).strip()
    key = (os.environ.get("INTEL_LLM_API_KEY") or os.environ.get("RUNPOD_API_KEY") or "").strip() or None
    return url, model, key


def llm_extra_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    credits_did = (os.environ.get("INTEL_LLM_CREDITS_DID") or os.environ.get("CREDITS_DID") or "").strip()
    if credits_did:
        headers["x-credits-did"] = credits_did
    if bool_env("INTEL_LLM_MAGATAMA_VERIFIED", False):
        headers["x-magatama-verified"] = "true"
    return headers


def litellm_api_base(url: str) -> str | None:
    if not url:
        return None
    base = url.rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    return base or None


def litellm_model_name(model: str, api_base: str | None) -> str:
    override = os.environ.get("INTEL_LITELLM_MODEL") or os.environ.get("RUNPOD_LITELLM_MODEL")
    if override:
        return override.strip()
    if "/" in model:
        return model
    provider = (os.environ.get("INTEL_LITELLM_PROVIDER") or os.environ.get("RUNPOD_LITELLM_PROVIDER") or "").strip()
    if provider:
        return f"{provider}/{model}"
    if api_base:
        return f"openai/{model}"
    return model


def extract_litellm_content(response: Any) -> str:
    try:
        return str(response.choices[0].message.content or "")
    except Exception:
        pass
    if isinstance(response, dict):
        return str(((response.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
    try:
        parsed = response.model_dump()
        return str(((parsed.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
    except Exception:
        return ""


def call_llm_json(system: str, user: str, *, max_tokens: int = 400) -> dict[str, Any] | None:
    url, model, api_key = llm_config()
    if not url:
        return None

    api_base = litellm_api_base(url)
    timeout = float(os.environ.get("INTEL_LLM_TIMEOUT_SEC", "90"))
    try:
        from litellm import completion

        extra_headers = llm_extra_headers()
        response = completion(
            model=litellm_model_name(model, api_base),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            api_base=api_base,
            api_key=api_key or "sk-no-key-required",
            temperature=0,
            max_tokens=max_tokens,
            timeout=timeout,
            num_retries=0,
            drop_params=True,
            extra_headers=extra_headers or None,
        )
        content = extract_litellm_content(response)
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        return json.loads(content[start : end + 1])
    except ImportError:
        pass
    except Exception:
        return None

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; etzhayyimIntelWorker/1.0)",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    headers.update(llm_extra_headers())

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return None

    try:
        parsed = json.loads(raw)
        content = ((parsed.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        return json.loads(content[start : end + 1])
    except Exception:
        return None


class IntelStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        from pymagatama.kotoba_datomic import get_kotoba_client
        self.client = get_kotoba_client()

    def create_run(self, scope: dict[str, Any], trigger_kind: str, dry_run: bool) -> dict[str, Any]:
        run_id = stable_id("intel-run", {"scope": scope, "trigger": trigger_kind, "ts": now_ms()})
        vertex_id = f"at://{OWNER_DID}/com.etzhayyim.apps.intel.inferenceRun/{run_id}"
        if True:
            try:
                return list(self.client.q("""
                    INSERT INTO vertex_intel_inference_run
                      (vertex_id, owner_did, run_id, trigger_kind, scope_json, status,
                       started_at, created_at, sensitivity_ord, org_id, user_id, actor_id)
                    SELECT %s, %s, %s, %s, %s, 'running', %s, %s, 1, %s, %s, %s
                    WHERE NOT EXISTS (
                      SELECT 1 FROM vertex_intel_inference_run WHERE vertex_id = %s
                    )
                    """,
                    (
                        vertex_id,
                        OWNER_DID,
                        run_id,
                        trigger_kind,
                        json_text({"scope": scope, "dryRun": dry_run}),
                        str(now_ms()),
                        str(now_ms()),
                        OWNER_DID,
                        OWNER_DID,
                        ACTOR_ID,
                        vertex_id,
                    ),
                ))
            except Exception as exc:
                if not is_missing_relation_error(exc):
                    raise
                legacy_vertex_id = f"at://{OWNER_DID}/com.etzhayyim.apps.intel.inferenceChain/{run_id}"
                rows = self.client.q(
                    """
                    INSERT INTO vertex_intel_inference_chain
                      (vertex_id, owner_did, status, chain_id, subject_name, subject_did,
                       industry, source_text, steps_count, cohorts_generated,
                       org_id, user_id, actor_id, created_at)
                    SELECT %s, %s, 'running', %s, %s, %s, %s, %s, 0, 0, %s, %s, %s, %s
                    WHERE NOT EXISTS (
                      SELECT 1 FROM vertex_intel_inference_chain WHERE vertex_id = %s
                    )
                    """,
                    (
                        legacy_vertex_id,
                        OWNER_DID,
                        run_id,
                        scope.get("subjectName") or "scheduled dependency inference",
                        scope.get("subjectDid"),
                        scope.get("industry"),
                        json_text({"scope": scope, "dryRun": dry_run, "triggerKind": trigger_kind}),
                        OWNER_DID,
                        OWNER_DID,
                        ACTOR_ID,
                        str(now_ms()),
                        legacy_vertex_id,
                    ),
                )
        return {"runId": run_id}

    def discover_vertex_tables(self) -> list[dict[str, Any]]:
        if True:
            rows = self.client.q(
                """
                SELECT c.table_name
                FROM information_schema.columns c
                JOIN information_schema.tables t
                  ON t.table_schema = c.table_schema AND t.table_name = c.table_name
                WHERE c.table_schema = 'public'
                  AND c.column_name = 'vertex_id'
                  AND (c.table_name LIKE 'vertex_%' OR c.table_name = 'actor_registry')
                  AND t.table_type IN ('BASE TABLE', 'MATERIALIZED VIEW', 'VIEW')
                ORDER BY c.table_name
                """)
            return list(rows)

    def discover_edge_tables(self) -> list[dict[str, Any]]:
        if True:
            return list(self.client.q("""
                SELECT table_name,
                       MAX(CASE WHEN column_name = 'edge_id' THEN 1 ELSE 0 END) AS has_edge_id
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name LIKE 'edge_%'
                  AND column_name IN ('src_vid', 'dst_vid', 'edge_id')
                GROUP BY table_name
                HAVING SUM(CASE WHEN column_name IN ('src_vid', 'dst_vid') THEN 1 ELSE 0 END) = 2
                ORDER BY table_name
                """))

    def scan_topology_nodes(self, graph_scope: str, max_nodes_per_table: int) -> list[TopologyNode]:
        _ = graph_scope
        nodes: list[TopologyNode] = []
        limit = max(1, min(int(max_nodes_per_table), 5000))
        table_filter = re.compile(os.environ.get("INTEL_TOPOLOGY_VERTEX_TABLE_REGEX", r"^(vertex_|actor_registry$)"))
        label_expr = (
            "COALESCE(CAST(display_name AS VARCHAR), CAST(name AS VARCHAR), CAST(label AS VARCHAR), CAST(title AS VARCHAR), vertex_id)"
        )

        for row in self.discover_vertex_tables():
            table = str(row["table_name"])
            if not table_filter.search(table):
                continue
            table_ident = sql_ident(table)
            query = f"""
                SELECT vertex_id,
                       '{table}' AS source_table,
                       '{table.removeprefix("vertex_")}' AS vertex_kind,
                       {label_expr} AS display_name
                FROM {table_ident}
                WHERE vertex_id IS NOT NULL AND vertex_id <> ''
                LIMIT {limit}
            """
            if True:
                try:
                    self.client.q(query)
                except Exception:
                    # Some vertex tables do not expose all common label columns;
                    # fall back to vertex_id-only projection.
                    rows = self.client.q(
                        f"""
                        SELECT vertex_id,
                               '{table}' AS source_table,
                               '{table.removeprefix("vertex_")}' AS vertex_kind,
                               vertex_id AS display_name
                        FROM {table_ident}
                        WHERE vertex_id IS NOT NULL AND vertex_id <> ''
                        LIMIT {limit}
                        """
                    )
            for item in rows:
                nodes.append(TopologyNode(
                    vertex_id=str(item["vertex_id"]),
                    vertex_kind=str(item.get("vertex_kind") or table),
                    display_name=item.get("display_name"),
                    source_table=table,
                ))
        if table_filter.search("actor_registry"):
            if True:
                try:
                    rows = self.client.q(
                        f"""
                        SELECT did AS vertex_id,
                               'actor_registry' AS source_table,
                               'actor' AS vertex_kind,
                               COALESCE(handle, did) AS display_name
                        FROM actor_registry
                        WHERE did IS NOT NULL AND did <> ''
                        LIMIT {limit}
                        """
                    )
                except Exception as exc:
                    if not is_missing_relation_error(exc):
                        raise
                    rows = []
            for item in rows:
                nodes.append(TopologyNode(
                    vertex_id=str(item["vertex_id"]),
                    vertex_kind="actor",
                    display_name=item.get("display_name"),
                    source_table="actor_registry",
                ))
        return nodes

    def scan_topology_edges(self, graph_scope: str, max_edges_per_table: int) -> list[TopologyEdge]:
        _ = graph_scope
        edges: list[TopologyEdge] = []
        limit = max(1, min(int(max_edges_per_table), 20000))
        table_filter = re.compile(os.environ.get("INTEL_TOPOLOGY_EDGE_TABLE_REGEX", r"^edge_"))
        min_confidence = float(os.environ.get("INTEL_TOPOLOGY_MIN_DEP_CONFIDENCE", "0.70"))

        for row in self.discover_edge_tables():
            table = str(row["table_name"])
            if not table_filter.search(table):
                continue
            hint = dependency_hint(table)
            table_ident = sql_ident(table)
            edge_id_expr = "edge_id" if int(row.get("has_edge_id") or 0) == 1 else f"CONCAT('{table}:', src_vid, ':', dst_vid)"
            if True:
                rows = self.client.q(
                    f"""
                    SELECT {edge_id_expr} AS edge_id,
                           src_vid,
                           dst_vid
                    FROM {table_ident}
                    WHERE src_vid IS NOT NULL AND dst_vid IS NOT NULL
                      AND src_vid <> '' AND dst_vid <> ''
                    LIMIT {limit}
                    """
                )
            for item in rows:
                dependency = bool(hint["isDependency"]) and float(hint["confidence"]) >= min_confidence
                direction = str(hint["direction"])
                if direction == "dst_depends_on_src":
                    src_vid = str(item["dst_vid"])
                    dst_vid = str(item["src_vid"])
                else:
                    src_vid = str(item["src_vid"])
                    dst_vid = str(item["dst_vid"])
                predicate = "depends_on" if dependency else table.removeprefix("edge_")
                edges.append(TopologyEdge(
                    edge_id=str(item.get("edge_id") or stable_id("topo-edge", item)),
                    src_vid=src_vid,
                    dst_vid=dst_vid,
                    edge_table=table,
                    predicate=predicate,
                    dependency_direction=direction,
                    confidence=float(hint["confidence"]),
                    evidence=[{"sourceTable": table, "sourceEdgeId": item.get("edge_id"), "hint": hint}],
                    reason=str(hint["reason"]),
                ))
        return edges

    def infer_topology_dependencies_with_llm(
        self,
        edges: list[TopologyEdge],
        max_edges: int,
    ) -> list[TopologyEdge]:
        if not bool_env("INTEL_TOPOLOGY_LLM_RESOLVE", False):
            return [edge for edge in edges if edge.predicate == "depends_on"]
        candidates = [edge for edge in edges if edge.confidence >= 0.20][: max(1, min(max_edges, 200))]
        if not candidates:
            return []
        decision = call_llm_json(
            "You classify graph edges as dependency edges. "
            "Input direction is src_vid -> dst_vid after deterministic normalization. "
            "Return JSON only: {\"edges\":[{\"edge_id\":\"...\",\"isDependency\":true,\"confidence\":0.0,\"reason\":\"...\"}]}",
            json_text({"edges": [topology_edge_to_dict(edge) for edge in candidates]}),
            max_tokens=1800,
        )
        decisions = decision.get("edges") if isinstance(decision, dict) else None
        by_id = {edge.edge_id: edge for edge in candidates}
        if not isinstance(decisions, list):
            return [edge for edge in edges if edge.predicate == "depends_on"]
        resolved: list[TopologyEdge] = []
        for item in decisions:
            if not isinstance(item, dict) or not item.get("isDependency"):
                continue
            edge = by_id.get(str(item.get("edge_id") or ""))
            if not edge:
                continue
            try:
                edge.confidence = max(edge.confidence, max(0.0, min(1.0, float(item.get("confidence")))))
            except (TypeError, ValueError):
                pass
            reason = str(item.get("reason") or "").strip()
            if reason:
                edge.reason = f"{edge.reason}; LLM topology resolver: {reason}"
            edge.predicate = "depends_on"
            resolved.append(edge)
        deterministic = [edge for edge in edges if edge.predicate == "depends_on"]
        by_edge_id = {edge.edge_id: edge for edge in deterministic}
        for edge in resolved:
            by_edge_id[edge.edge_id] = edge
        return list(by_edge_id.values())

    def materialize_topology_dependencies(
        self,
        graph_scope: str,
        run_id: str,
        edges: list[TopologyEdge],
        dry_run: bool,
    ) -> dict[str, Any]:
        if dry_run:
            return {"dependencyEdgeCount": len(edges), "dryRun": True}
        if True:
            for edge in edges:
                edge_id = stable_id("topology-dep", {
                    "scope": graph_scope,
                    "src": edge.src_vid,
                    "dst": edge.dst_vid,
                    "source": edge.edge_table,
                })
                rows = self.client.q(
                    """
                    INSERT INTO edge_intel_dependency
                      (edge_id, owner_did, src_vid, dst_vid, predicate, dependency_kind,
                       confidence, evidence_count, evidence_json, inference_run_id,
                       reason, model_version, status, created_at, sensitivity_ord,
                       org_id, user_id, actor_id)
                    SELECT %s, %s, %s, %s, 'depends_on', %s,
                           %s, %s, %s, %s,
                           %s, 'topology-daemon-v1', %s, %s, 1,
                           %s, %s, %s
                    WHERE NOT EXISTS (
                      SELECT 1 FROM edge_intel_dependency WHERE edge_id = %s
                    )
                    """,
                    (
                        edge_id,
                        OWNER_DID,
                        edge.src_vid,
                        edge.dst_vid,
                        f"topology:{edge.edge_table}",
                        edge.confidence,
                        len(edge.evidence),
                        json_text(edge.evidence),
                        run_id,
                        edge.reason,
                        "active" if edge.confidence >= 0.75 else "candidate",
                        str(now_ms()),
                        OWNER_DID,
                        OWNER_DID,
                        ACTOR_ID,
                        edge_id,
                    ),
                )
        return {"dependencyEdgeCount": len(edges), "dryRun": False}

    def materialize_topology_order(
        self,
        graph_scope: str,
        rows: list[TopologyOrderRow],
        dry_run: bool,
    ) -> dict[str, Any]:
        if dry_run:
            return {"topologyOrderCount": len(rows), "dryRun": True}
        if True:
            for row in rows:
                self.client.q(
                    "DELETE FROM vertex_dependency_topology_order WHERE graph_scope = %s AND vertex_id = %s",
                    (graph_scope, row.vertex_id),
                )
                cur.execute(
                    """
                    INSERT INTO vertex_dependency_topology_order
                      (graph_scope, vertex_id, owner_did, display_name, vertex_kind,
                       topo_rank, reverse_topo_rank, topo_level,
                       dependency_count, dependent_count, unresolved_dependency_count,
                       cycle_status, computed_at, algorithm, payload_json,
                       sensitivity_ord, created_date)
                    VALUES (%s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, 'kahn-v1-python', %s,
                            1, CAST(%s AS DATE))
                    """,
                    (
                        graph_scope,
                        row.vertex_id,
                        OWNER_DID,
                        row.display_name,
                        row.vertex_kind,
                        row.topo_rank,
                        row.reverse_topo_rank,
                        row.topo_level,
                        row.dependency_count,
                        row.dependent_count,
                        row.unresolved_dependency_count,
                        row.cycle_status,
                        utc_iso(),
                        row.payload_json,
                        utc_date(),
                    ),
                )
        return {"topologyOrderCount": len(rows), "dryRun": False}

    def scan_candidates(self, scope: dict[str, Any], max_candidates: int) -> list[Candidate]:
        building_vid = scope.get("buildingVertexId") or scope.get("buildingVid")
        lei = scope.get("lei")
        limit = max(1, min(int(max_candidates or 500), 5000))

        where = ["sp.label = 'Building'"]
        params: list[Any] = []
        if building_vid:
            where.append("sp.vertex_id = %s")
            params.append(building_vid)
        if lei:
            where.append("le.lei = %s")
            params.append(lei)

        sql = f"""
            SELECT
              sp.vertex_id AS building_vid,
              COALESCE(le.vertex_id, own.dst_vid) AS owner_vid,
              COALESCE(le.lei, '') AS lei,
              COALESCE(le.legal_name, le.name, '') AS owner_name,
              COALESCE(own.share_pct, 0.0) AS share_pct,
              COALESCE(own.registry_ref, '') AS registry_ref
            FROM vertex_spatial sp
            JOIN edge_ownership own ON own.dst_vid = sp.vertex_id
            LEFT JOIN vertex_legal_entity le ON le.vertex_id = own.src_vid
            WHERE {" AND ".join(where)}
            LIMIT {limit}
        """

        candidates: list[Candidate] = []
        if True:
            try:
                self.client.q(sql, params)
            except Exception:
                rows = []

        for row in rows:
            if not row.get("owner_vid"):
                continue
            evidence = [{
                "source": "maps.edge_ownership",
                "registryRef": row.get("registry_ref"),
                "sharePct": float(row.get("share_pct") or 0.0),
                "lei": row.get("lei") or None,
            }]
            confidence = 0.86 if row.get("lei") else 0.72
            candidates.append(Candidate(
                src_vid=row["building_vid"],
                dst_vid=row["owner_vid"],
                predicate="owned_by",
                dependency_kind="building_owner_lei" if row.get("lei") else "building_owner",
                confidence=confidence,
                evidence=evidence,
                reason="edge_ownership links a Building to a legal entity; LEI presence raises confidence." if row.get("lei") else "edge_ownership links a Building to an owner vertex.",
            ))
        return candidates

    def materialize(self, run_id: str, candidates: list[Candidate], dry_run: bool) -> dict[str, Any]:
        active = 0
        review = 0
        if dry_run:
            return {
                "candidateCount": len(candidates),
                "activeCount": sum(1 for c in candidates if c.confidence >= 0.85),
                "reviewCount": sum(1 for c in candidates if c.confidence < 0.85),
                "dryRun": True,
            }

        if True:
            try:
                for c in candidates:
                    status = "active" if c.confidence >= 0.85 else "candidate"
                    active += int(status == "active")
                    review += int(status == "candidate")
                    edge_id = stable_id("intel-edge", {
                        "src": c.src_vid,
                        "dst": c.dst_vid,
                        "predicate": c.predicate,
                        "kind": c.dependency_kind,
                    })
                    rows = self.client.q(
                        """
                        INSERT INTO edge_intel_dependency
                          (edge_id, owner_did, src_vid, dst_vid, predicate, dependency_kind,
                           confidence, evidence_count, evidence_json, inference_run_id,
                           reason, model_version, status, created_at, sensitivity_ord,
                           org_id, user_id, actor_id)
                        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s
                        WHERE NOT EXISTS (
                          SELECT 1 FROM edge_intel_dependency WHERE edge_id = %s
                        )
                        """,
                        (
                            edge_id,
                            OWNER_DID,
                            c.src_vid,
                            c.dst_vid,
                            c.predicate,
                            c.dependency_kind,
                            c.confidence,
                            len(c.evidence),
                            json_text(c.evidence),
                            run_id,
                            c.reason,
                            "intel-dependency-worker-v1",
                            status,
                            str(now_ms()),
                            OWNER_DID,
                            OWNER_DID,
                            ACTOR_ID,
                            edge_id,
                        ),
                    )
                run_vertex_id = f"at://{OWNER_DID}/com.etzhayyim.apps.intel.inferenceRun/{run_id}"
                cur.execute(
                    """
                    UPDATE vertex_intel_inference_run
                    SET candidate_count = %s, active_count = %s, review_count = %s,
                        status = 'completed', completed_at = %s
                    WHERE vertex_id = %s
                    """,
                    (len(candidates), active, review, str(now_ms()), run_vertex_id),
                )
            except Exception as exc:
                if not is_missing_relation_error(exc):
                    raise
                active, review = self.materialize_legacy(run_id, candidates)
        return {
            "candidateCount": len(candidates),
            "activeCount": active,
            "reviewCount": review,
            "dryRun": False,
        }

    def materialize_legacy(self, run_id: str, candidates: list[Candidate]) -> tuple[int, int]:
        active = 0
        review = 0
        for c in candidates:
            status = "active" if c.confidence >= 0.85 else "candidate"
            active += int(status == "active")
            review += int(status == "candidate")
            cohort_id = stable_id("intel-cohort", {
                "src": c.src_vid,
                "dst": c.dst_vid,
                "predicate": c.predicate,
                "kind": c.dependency_kind,
            })
            vertex_id = f"at://{OWNER_DID}/com.etzhayyim.apps.intel.inferredCohort/{cohort_id}"
            cur.execute(
                """
                INSERT INTO vertex_intel_inferred_cohort
                  (vertex_id, owner_did, status, cohort_id, chain_id, target_domain,
                   entity_type, layer, estimated_count, confidence, methodology,
                   inference_rule, input_fact, assumptions, cohort_hash,
                   subject_did, subject_name, org_id, user_id, actor_id, created_at)
                SELECT %s, %s, %s, %s, %s, 'dependency', %s, 1, 1, %s,
                       'maps-ownership-lei', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                WHERE NOT EXISTS (
                  SELECT 1 FROM vertex_intel_inferred_cohort WHERE vertex_id = %s
                )
                """,
                (
                    vertex_id,
                    OWNER_DID,
                    status,
                    cohort_id,
                    run_id,
                    c.dependency_kind,
                    c.confidence,
                    c.predicate,
                    c.src_vid,
                    json_text({"dst": c.dst_vid, "evidence": c.evidence, "reason": c.reason}),
                    stable_id("hash", candidate_to_dict(c)),
                    c.dst_vid,
                    c.dst_vid,
                    OWNER_DID,
                    OWNER_DID,
                    ACTOR_ID,
                    str(now_ms()),
                    vertex_id,
                ),
            )
        chain_vertex_id = f"at://{OWNER_DID}/com.etzhayyim.apps.intel.inferenceChain/{run_id}"
        cur.execute(
            """
            UPDATE vertex_intel_inference_chain
            SET status = 'completed', steps_count = 4, cohorts_generated = %s
            WHERE vertex_id = %s
            """,
            (len(candidates), chain_vertex_id),
        )
        return active, review

    def explain_dependency(
        self,
        edge_id: str | None,
        from_vertex_id: str | None,
        to_vertex_id: str | None,
        predicate: str | None,
    ) -> dict[str, Any]:
        where: list[str] = []
        params: list[Any] = []
        if edge_id:
            where.append("edge_id = %s")
            params.append(edge_id)
        if from_vertex_id:
            where.append("src_vid = %s")
            params.append(from_vertex_id)
        if to_vertex_id:
            where.append("dst_vid = %s")
            params.append(to_vertex_id)
        if predicate:
            where.append("predicate = %s")
            params.append(predicate)
        if not where:
            return {"error": "edgeId or fromVertexId/toVertexId/predicate is required"}

        query = f"""
            SELECT edge_id, src_vid, dst_vid, predicate, dependency_kind,
                   confidence, evidence_count, evidence_json, inference_run_id,
                   reason, model_version, status, reviewed_by, reviewed_at, review_note,
                   created_at
            FROM edge_intel_dependency
            WHERE {" AND ".join(where)}
            LIMIT 1
        """
        if True:
            self.client.q(query, params)
            row = rows[0] if rows else None
        if not row:
            return {"error": "not found"}
        item = dependency_row_to_dict(row)
        explanation = item.get("reason") or (
            f"{item['src_vid']} {item['predicate']} {item['dst_vid']} "
            f"with confidence {item.get('confidence', 0):.2f}."
        )
        return {**item, "explanation": explanation}

    def list_dependency_candidates(
        self,
        status: str | None,
        predicate: str | None,
        limit: int | None,
        offset: int | None,
    ) -> dict[str, Any]:
        safe_limit = max(1, min(int(limit or 50), 200))
        safe_offset = max(0, int(offset or 0))
        where: list[str] = []
        params: list[Any] = []
        if status:
            where.append("status = %s")
            params.append(status)
        if predicate:
            where.append("predicate = %s")
            params.append(predicate)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        # RisingWave rejects parameterized LIMIT/OFFSET ($N placeholders) —
        # inline as integer literals (safe: values are clamped to ints above).
        query = f"""
            SELECT edge_id, src_vid, dst_vid, predicate, dependency_kind,
                   confidence, evidence_count, evidence_json, inference_run_id,
                   reason, model_version, status, reviewed_by, reviewed_at, review_note,
                   created_at
            FROM edge_intel_dependency
            {where_sql}
            ORDER BY created_at DESC
            LIMIT {safe_limit} OFFSET {safe_offset}
        """
        if True:
            self.client.q(query, params)
        return {
            "items": [dependency_row_to_dict(r) for r in rows],
            "limit": safe_limit,
            "offset": safe_offset,
        }

    def get_building_ownership_graph(
        self,
        building_vertex_id: str | None,
        lei: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        safe_limit = max(1, min(int(limit or 50), 200))
        where = ["d.predicate IN ('owned_by', 'constructed_by', 'operated_by')"]
        params: list[Any] = []
        if building_vertex_id:
            where.append("d.src_vid = %s")
            params.append(building_vertex_id)
        if lei:
            where.append("s.lei = %s")
            params.append(lei)
        query = f"""
            SELECT d.edge_id, d.src_vid, d.dst_vid, d.predicate, d.dependency_kind,
                   d.confidence, d.evidence_count, d.evidence_json, d.inference_run_id,
                   d.reason, d.model_version, d.status, d.created_at,
                   s.label AS dst_label, s.subject_kind AS dst_kind, s.lei AS dst_lei
            FROM edge_intel_dependency d
            LEFT JOIN vertex_intel_subject s ON s.vertex_id = d.dst_vid
            WHERE {" AND ".join(where)}
            ORDER BY d.confidence DESC
            LIMIT {safe_limit}
        """
        if True:
            rows = self.client.q(query, params)
        return rows_to_graph(rows)

    def get_counterparty_graph(
        self,
        subject_vertex_id: str | None,
        lei: str | None,
        relation_kinds: list[str] | None,
        limit: int | None,
    ) -> dict[str, Any]:
        safe_limit = max(1, min(int(limit or 50), 200))
        where: list[str] = []
        params: list[Any] = []
        if subject_vertex_id:
            where.append("(d.src_vid = %s OR d.dst_vid = %s)")
            params.extend([subject_vertex_id, subject_vertex_id])
        if lei:
            where.append("(src.lei = %s OR dst.lei = %s)")
            params.extend([lei, lei])
        if relation_kinds:
            placeholders = ", ".join(["%s"] * len(relation_kinds))
            where.append(f"d.dependency_kind IN ({placeholders})")
            params.extend(relation_kinds)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        query = f"""
            SELECT d.edge_id, d.src_vid, d.dst_vid, d.predicate, d.dependency_kind,
                   d.confidence, d.evidence_count, d.evidence_json, d.inference_run_id,
                   d.reason, d.model_version, d.status, d.created_at,
                   src.label AS src_label, src.subject_kind AS src_kind, src.lei AS src_lei,
                   dst.label AS dst_label, dst.subject_kind AS dst_kind, dst.lei AS dst_lei
            FROM edge_intel_dependency d
            LEFT JOIN vertex_intel_subject src ON src.vertex_id = d.src_vid
            LEFT JOIN vertex_intel_subject dst ON dst.vertex_id = d.dst_vid
            {where_sql}
            ORDER BY d.confidence DESC
            LIMIT {safe_limit}
        """
        if True:
            rows = self.client.q(query, params)
        return rows_to_graph(rows)

    def resolve_entity(
        self,
        run_id: str | None,
        query: str | None,
        entity_kind: str | None,
        hints: dict[str, Any] | None,
        max_candidates: int | None,
    ) -> dict[str, Any]:
        q = str(query or "").strip()
        if not q and not (hints or {}).get("lei"):
            return {"runId": run_id, "query": q, "candidateCount": 0, "candidates": [], "error": "query or hints.lei is required"}

        safe_limit = max(1, min(int(max_candidates or 20), 100))
        candidates: list[dict[str, Any]] = []
        candidates.extend(self.resolve_entity_from_contracts_organizations(q, entity_kind, hints or {}, safe_limit))
        if len(candidates) < safe_limit:
            candidates.extend(self.resolve_entity_from_open_lei_entities(q, entity_kind, hints or {}, safe_limit - len(candidates)))
        if len(candidates) < safe_limit:
            candidates.extend(self.resolve_entity_from_gleif_exact_lookup(q, entity_kind, hints or {}, safe_limit - len(candidates)))
        if len(candidates) < safe_limit:
            candidates.extend(self.resolve_entity_from_entity_dids(q, entity_kind, hints or {}, safe_limit - len(candidates)))
        if len(candidates) < safe_limit:
            candidates.extend(self.resolve_entity_from_subjects(q, entity_kind, hints or {}, safe_limit - len(candidates)))
        if len(candidates) < safe_limit:
            candidates.extend(self.resolve_entity_from_legal_entities(q, entity_kind, hints or {}, safe_limit - len(candidates)))

        deduped: dict[str, dict[str, Any]] = {}
        for item in candidates:
            key = item.get("entityId") or item.get("vertexId") or item.get("did") or item.get("name")
            if not key:
                continue
            existing = deduped.get(str(key))
            if not existing or float(item.get("score") or 0.0) > float(existing.get("score") or 0.0):
                deduped[str(key)] = item

        ranked = sorted(deduped.values(), key=lambda c: float(c.get("score") or 0.0), reverse=True)[:safe_limit]
        ranked = maybe_rerank_entities_with_llm(q, ranked, hints or {})
        return {
            "runId": run_id,
            "query": q,
            "entityKind": entity_kind,
            "candidateCount": len(ranked),
            "candidates": ranked,
        }

    def resolve_entity_from_subjects(
        self,
        query: str,
        entity_kind: str | None,
        hints: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        if os.environ.get("INTEL_ENABLE_SUBJECT_RESOLVE", "false").lower() != "true":
            return []
        where = ["1 = 1"]
        params: list[Any] = []
        if entity_kind:
            where.append("subject_kind = %s")
            params.append(entity_kind)
        if hints.get("lei"):
            where.append("lei = %s")
            params.append(hints["lei"])
        elif query:
            where.append("(lower(label) LIKE %s OR lower(canonical_key) LIKE %s OR lower(coalesce(lei, '')) = %s)")
            like = f"%{normalize_text(query)}%"
            params.extend([like, like, normalize_text(query)])
        safe_limit = max(1, min(int(limit), 100))
        sql = f"""
            SELECT vertex_id, label, subject_kind, lei, status, source_did
            FROM vertex_intel_subject
            WHERE {" AND ".join(where)}
            ORDER BY created_at DESC
            LIMIT {safe_limit}
        """
        if True:
            try:
                rows = self.client.q(sql, params)
            except Exception as exc:
                if not is_missing_relation_error(exc):
                    raise
                rows = []
        return [
            entity_candidate(
                vertex_id=row.get("vertex_id") or "",
                name=row.get("label") or row.get("vertex_id") or "",
                entity_kind=row.get("subject_kind"),
                source="vertex_intel_subject",
                query=query,
                lei=row.get("lei"),
                status=row.get("status"),
                hints=hints,
            )
            for row in rows
        ]

    def resolve_entity_from_entity_dids(
        self,
        query: str,
        entity_kind: str | None,
        hints: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        _ = hints
        if not query:
            return []
        where = ["1 = 1"]
        params: list[Any] = []
        if entity_kind:
            where.append("entity_type = %s")
            params.append(entity_kind)
        if query:
            where.append("(lower(name) LIKE %s OR lower(entity_id) = %s OR lower(coalesce(did, '')) = %s)")
            normalized = normalize_text(query)
            params.extend([f"%{normalized}%", normalized, normalized])
        safe_limit = max(1, min(int(limit), 100))
        sql = f"""
            SELECT vertex_id, name, entity_type, did, domain, status
            FROM vertex_intel_entity_did
            WHERE {" AND ".join(where)}
            ORDER BY created_at DESC
            LIMIT {safe_limit}
        """
        if True:
            try:
                rows = self.client.q(sql, params)
            except Exception as exc:
                if not is_missing_relation_error(exc):
                    raise
                rows = []
        return [
            entity_candidate(
                vertex_id=row.get("vertex_id") or "",
                name=row.get("name") or row.get("did") or row.get("vertex_id") or "",
                entity_kind=row.get("entity_type"),
                source="vertex_intel_entity_did",
                query=query,
                did=row.get("did"),
                domain=row.get("domain"),
                status=row.get("status"),
                hints=hints,
            )
            for row in rows
        ]

    def resolve_entity_from_contracts_organizations(
        self,
        query: str,
        entity_kind: str | None,
        hints: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        _ = entity_kind
        where = ["1 = 1"]
        params: list[Any] = []
        if hints.get("lei"):
            where.append("lei = %s")
            params.append(hints["lei"])
        elif query:
            normalized = normalize_text(query)
            # Keep broad name search opt-in. The live table is much smaller
            # than vertex_legal_entity, but identifier lookups are the default
            # hot path and have indexes.
            if os.environ.get("INTEL_ENABLE_NAME_SCAN", "false").lower() == "true":
                where.append("(lower(coalesce(name, legal_name, '')) LIKE %s OR lower(coalesce(lei, '')) = %s)")
                params.extend([f"%{normalized}%", normalized])
            else:
                where.append("(lower(coalesce(lei, '')) = %s OR lower(coalesce(did, '')) = %s OR lower(coalesce(national_id, '')) = %s)")
                params.extend([normalized, normalized, normalized])
        safe_limit = max(1, min(int(limit), 100))
        sql = f"""
            SELECT vertex_id, COALESCE(name, legal_name, vertex_id) AS name,
                   lei, did, country, status
            FROM vertex_contracts_organization
            WHERE {" AND ".join(where)}
            LIMIT {safe_limit}
        """
        if True:
            try:
                rows = self.client.q(sql, params)
            except Exception as exc:
                if not is_missing_relation_error(exc):
                    raise
                rows = []
        return [
            entity_candidate(
                vertex_id=row.get("vertex_id") or "",
                name=row.get("name") or row.get("vertex_id") or "",
                entity_kind="legal_entity",
                source="vertex_contracts_organization",
                query=query,
                did=row.get("did"),
                lei=row.get("lei"),
                domain=row.get("country"),
                status=row.get("status"),
                hints=hints,
            )
            for row in rows
        ]

    def resolve_entity_from_open_lei_entities(
        self,
        query: str,
        entity_kind: str | None,
        hints: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        _ = entity_kind
        where = ["1 = 1"]
        params: list[Any] = []
        if hints.get("lei"):
            where.append("lei = %s")
            params.append(hints["lei"])
        elif query:
            normalized = normalize_text(query)
            # Keep name search opt-in. The indexed hot path is LEI equality.
            if os.environ.get("INTEL_ENABLE_OPEN_LEI_NAME_SCAN", "false").lower() == "true":
                where.append("(lower(coalesce(legal_name, '')) LIKE %s OR lower(coalesce(lei, '')) = %s)")
                params.extend([f"%{normalized}%", normalized])
            else:
                where.append("lower(coalesce(lei, '')) = %s")
                params.append(normalized)
        safe_limit = max(1, min(int(limit), 100))
        sql = f"""
            SELECT vertex_id, legal_name AS name, lei, country, status, registration_status
            FROM vertex_open_lei_entity
            WHERE {" AND ".join(where)}
            LIMIT {safe_limit}
        """
        if True:
            try:
                rows = self.client.q(sql, params)
            except Exception as exc:
                if not is_missing_relation_error(exc):
                    raise
                rows = []
        return [
            entity_candidate(
                vertex_id=row.get("vertex_id") or "",
                name=row.get("name") or row.get("lei") or row.get("vertex_id") or "",
                entity_kind="legal_entity",
                source="vertex_open_lei_entity",
                query=query,
                lei=row.get("lei"),
                domain=row.get("country"),
                status=row.get("registration_status") or row.get("status"),
                hints=hints,
            )
            for row in rows
        ]

    def resolve_entity_from_gleif_exact_lookup(
        self,
        query: str,
        entity_kind: str | None,
        hints: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        _ = entity_kind
        if limit <= 0:
            return []
        if os.environ.get("INTEL_ENABLE_GLEIF_LOOKUP", "true").lower() != "true":
            return []
        lei = canonical_lei(hints.get("lei")) or canonical_lei(query)
        if not lei:
            return []

        row = fetch_gleif_lei_record(lei)
        if not row:
            return []
        self.insert_open_lei_entity(row)
        return [
            entity_candidate(
                vertex_id=row["vertex_id"],
                name=row["legal_name"],
                entity_kind="legal_entity",
                source="vertex_open_lei_entity",
                query=query,
                lei=row["lei"],
                domain=row.get("country"),
                status=row.get("registration_status") or row.get("status"),
                hints=hints,
            )
        ]

    def insert_open_lei_entity(self, row: dict[str, Any]) -> None:
        if True:
            try:
                rows = self.client.q(
                    """
                    INSERT INTO vertex_open_lei_entity
                      (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                       lei, legal_name, country, legal_form, registration_authority,
                       registration_status, issued_at, next_renewal_at, status,
                       created_at, org_id, user_id, actor_id)
                    SELECT %s, CAST(NULL AS BIGINT), CAST(%s AS DATE), 1, %s,
                           %s, %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s, %s
                    WHERE NOT EXISTS (
                      SELECT 1 FROM vertex_open_lei_entity WHERE vertex_id = %s
                    )
                    """,
                    (
                        row["vertex_id"],
                        utc_date(),
                        "did:web:open-lei.etzhayyim.com",
                        row["lei"],
                        row["legal_name"],
                        row.get("country"),
                        row.get("legal_form"),
                        row.get("registration_authority"),
                        row.get("registration_status") or "UNKNOWN",
                        row.get("issued_at"),
                        row.get("next_renewal_at"),
                        row.get("status") or "active",
                        row.get("created_at") or utc_iso(),
                        "did:web:open-lei.etzhayyim.com",
                        "did:web:open-lei.etzhayyim.com",
                        "sys.langserver.intel.gleif",
                        row["vertex_id"],
                    ),
                )
            except Exception as exc:
                if not is_missing_relation_error(exc):
                    raise

    def resolve_entity_from_legal_entities(
        self,
        query: str,
        entity_kind: str | None,
        hints: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        _ = entity_kind
        if os.environ.get("INTEL_ENABLE_LEGAL_ENTITY_SCAN", "false").lower() != "true":
            return []
        where = ["1 = 1"]
        params: list[Any] = []
        if hints.get("lei"):
            where.append("lei = %s")
            params.append(hints["lei"])
        elif query:
            normalized = normalize_text(query)
            where.append("(lower(coalesce(name, display_name, label, '')) LIKE %s OR lower(coalesce(lei, '')) = %s)")
            params.extend([f"%{normalized}%", normalized])
        safe_limit = max(1, min(int(limit), 100))
        sql = f"""
            SELECT vertex_id, COALESCE(name, display_name, label, vertex_id) AS name, lei, status
            FROM vertex_legal_entity
            WHERE {" AND ".join(where)}
            LIMIT {safe_limit}
        """
        if True:
            try:
                self.client.q(sql, params)
            except Exception:
                rows = []
        return [
            entity_candidate(
                vertex_id=row.get("vertex_id") or "",
                name=row.get("name") or row.get("vertex_id") or "",
                entity_kind="legal_entity",
                source="vertex_legal_entity",
                query=query,
                lei=row.get("lei"),
                status=row.get("status"),
                hints=hints,
            )
            for row in rows
        ]


def _parse_allowed_predicates(ontology_path: Path) -> frozenset[str]:
    # constructed_by is in the first-slice design but not yet in the TTL; include as supplement.
    _FIRST_SLICE_SUPPLEMENT: frozenset[str] = frozenset({"constructed_by"})
    _FALLBACK: frozenset[str] = frozenset({"owned_by", "operated_by", "constructed_by"})
    try:
        from rdflib import Graph, Namespace
        SH = Namespace("http://www.w3.org/ns/shacl#")
        g = Graph()
        g.parse(str(ontology_path), format="turtle")
        predicates: set[str] = set()
        for _shape, _prop, path_node in g.triples((None, SH.path, None)):
            local = str(path_node).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
            if local:
                predicates.add(local)
        if not predicates:
            return _FALLBACK
        return frozenset(predicates) | _FIRST_SLICE_SUPPLEMENT
    except Exception:
        return _FALLBACK


def validate_candidates(candidates: list[Candidate]) -> list[Candidate]:
    ontology_path = Path(os.environ.get("INTEL_ONTOLOGY_PATH", "/app/ontology.ttl"))
    if not ontology_path.exists():
        ontology_path = Path(__file__).with_name("ontology.ttl")
    allowed = _parse_allowed_predicates(ontology_path)
    return [
        c for c in candidates
        if c.src_vid and c.dst_vid and c.predicate in allowed
    ]


def resolve_with_langgraph(candidates: list[Candidate]) -> list[Candidate]:
    if os.environ.get("INTEL_LLM_RESOLVE", "false").lower() != "true" or not candidates:
        return candidates
    prompt_candidates = [candidate_to_dict(c) for c in candidates[:20]]
    decision = call_llm_json(
        "You resolve dependency graph candidates. Return JSON only: "
        '{"decisions":[{"src_vid":"...","dst_vid":"...","predicate":"...","confidence":0.0,"reason":"..."}]}.',
        json_text({"candidates": prompt_candidates}),
        max_tokens=900,
    )
    decisions = decision.get("decisions") if isinstance(decision, dict) else None
    if not isinstance(decisions, list):
        return candidates

    by_key = {(c.src_vid, c.dst_vid, c.predicate): c for c in candidates}
    for item in decisions:
        if not isinstance(item, dict):
            continue
        key = (str(item.get("src_vid", "")), str(item.get("dst_vid", "")), str(item.get("predicate", "")))
        candidate = by_key.get(key)
        if not candidate:
            continue
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence"))))
            candidate.confidence = round((candidate.confidence + confidence) / 2.0, 4)
        except (TypeError, ValueError):
            pass
        reason = str(item.get("reason") or "").strip()
        if reason:
            candidate.reason = f"{candidate.reason} LLM resolver: {reason}"
    return candidates


def maybe_rerank_entities_with_llm(query: str, candidates: list[dict[str, Any]], hints: dict[str, Any]) -> list[dict[str, Any]]:
    if os.environ.get("INTEL_LLM_ENTITY_RESOLVE", "false").lower() != "true" or not candidates:
        return candidates
    decision = call_llm_json(
        "You rerank entity-resolution candidates. Return JSON only: "
        '{"ranked":[{"entityId":"...","score":0.0,"reason":"..."}]}.',
        json_text({"query": query, "hints": hints, "candidates": candidates[:20]}),
        max_tokens=700,
    )
    ranked = decision.get("ranked") if isinstance(decision, dict) else None
    if not isinstance(ranked, list):
        return candidates
    by_id = {str(c.get("entityId")): dict(c) for c in candidates}
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in ranked:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("entityId") or "")
        candidate = by_id.get(entity_id)
        if not candidate:
            continue
        try:
            candidate["score"] = round(max(0.0, min(1.0, float(item.get("score")))), 4)
        except (TypeError, ValueError):
            pass
        reason = str(item.get("reason") or "").strip()
        if reason:
            candidate["reason"] = f"{candidate.get('reason')}; LLM resolver: {reason}"
        output.append(candidate)
        seen.add(entity_id)
    output.extend(c for c in candidates if str(c.get("entityId")) not in seen)
    return sorted(output, key=lambda c: float(c.get("score") or 0.0), reverse=True)


def parse_json_maybe(raw: Any, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(str(raw))
    except Exception:
        return fallback


def dependency_row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "edgeId": row.get("edge_id"),
        "src_vid": row.get("src_vid"),
        "dst_vid": row.get("dst_vid"),
        "fromVertexId": row.get("src_vid"),
        "toVertexId": row.get("dst_vid"),
        "predicate": row.get("predicate"),
        "dependencyKind": row.get("dependency_kind"),
        "confidence": float(row.get("confidence") or 0.0),
        "evidenceCount": int(row.get("evidence_count") or 0),
        "evidence": parse_json_maybe(row.get("evidence_json"), []),
        "inferenceRunId": row.get("inference_run_id"),
        "reason": row.get("reason"),
        "modelVersion": row.get("model_version"),
        "status": row.get("status"),
        "reviewedBy": row.get("reviewed_by"),
        "reviewedAt": row.get("reviewed_at"),
        "reviewNote": row.get("review_note"),
        "createdAt": row.get("created_at"),
    }


def rows_to_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    for row in rows:
        src = row.get("src_vid")
        dst = row.get("dst_vid")
        if src and src not in nodes:
            nodes[src] = {
                "vertexId": src,
                "label": row.get("src_label") or src,
                "kind": row.get("src_kind"),
                "lei": row.get("src_lei"),
            }
        if dst and dst not in nodes:
            nodes[dst] = {
                "vertexId": dst,
                "label": row.get("dst_label") or dst,
                "kind": row.get("dst_kind"),
                "lei": row.get("dst_lei"),
            }
        edges.append(dependency_row_to_dict(row))
    return {"nodes": list(nodes.values()), "edges": edges}


def topology_edge_to_dict(edge: TopologyEdge) -> dict[str, Any]:
    return {
        "edge_id": edge.edge_id,
        "src_vid": edge.src_vid,
        "dst_vid": edge.dst_vid,
        "edge_table": edge.edge_table,
        "predicate": edge.predicate,
        "dependency_direction": edge.dependency_direction,
        "confidence": edge.confidence,
        "evidence": edge.evidence,
        "reason": edge.reason,
    }


def compute_topology_order(
    graph_scope: str,
    nodes: list[TopologyNode],
    dependency_edges: list[TopologyEdge],
) -> list[TopologyOrderRow]:
    node_by_id: dict[str, TopologyNode] = {node.vertex_id: node for node in nodes}
    explicit_ids = set(node_by_id)
    for edge in dependency_edges:
        node_by_id.setdefault(edge.src_vid, TopologyNode(edge.src_vid, "unknown", edge.src_vid, "edge_only"))
        node_by_id.setdefault(edge.dst_vid, TopologyNode(edge.dst_vid, "unknown", edge.dst_vid, "edge_only"))

    ids = sorted(node_by_id)
    dependency_count = {vertex_id: 0 for vertex_id in ids}
    dependent_count = {vertex_id: 0 for vertex_id in ids}
    unresolved_count = {vertex_id: 0 for vertex_id in ids}
    indegree = {vertex_id: 0 for vertex_id in ids}
    dependents_by_prereq = {vertex_id: [] for vertex_id in ids}
    topo_level = {vertex_id: 0 for vertex_id in ids}
    seen: set[tuple[str, str]] = set()

    for edge in dependency_edges:
        key = (edge.src_vid, edge.dst_vid)
        if key in seen:
            continue
        seen.add(key)
        dependency_count[edge.src_vid] += 1
        dependent_count[edge.dst_vid] += 1
        if edge.dst_vid not in explicit_ids:
            unresolved_count[edge.src_vid] += 1
        indegree[edge.src_vid] += 1
        dependents_by_prereq[edge.dst_vid].append(edge.src_vid)

    for dependents in dependents_by_prereq.values():
        dependents.sort()

    ready = sorted(vertex_id for vertex_id in ids if indegree[vertex_id] == 0)
    topo: list[str] = []
    while ready:
        vertex_id = ready.pop(0)
        topo.append(vertex_id)
        for dependent in dependents_by_prereq[vertex_id]:
            topo_level[dependent] = max(topo_level[dependent], topo_level[vertex_id] + 1)
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort()

    topo_set = set(topo)
    cycle_members = sorted(vertex_id for vertex_id in ids if vertex_id not in topo_set)
    ordered = topo + cycle_members
    total = len(ordered)
    output: list[TopologyOrderRow] = []
    for topo_rank, vertex_id in enumerate(ordered):
        node = node_by_id[vertex_id]
        cycle_status = "acyclic" if vertex_id in topo_set else "cycle_member"
        payload = {
            "graphScope": graph_scope,
            "vertexId": vertex_id,
            "vertexKind": node.vertex_kind or "unknown",
            "displayName": node.display_name or "",
            "dependencyCount": dependency_count[vertex_id],
            "dependentCount": dependent_count[vertex_id],
            "topoRank": topo_rank,
            "reverseTopoRank": total - topo_rank - 1,
            "topoLevel": topo_level[vertex_id],
            "unresolvedDependencyCount": unresolved_count[vertex_id],
            "cycleStatus": cycle_status,
        }
        output.append(TopologyOrderRow(
            graph_scope=graph_scope,
            vertex_id=vertex_id,
            display_name=node.display_name,
            vertex_kind=node.vertex_kind,
            topo_rank=topo_rank,
            reverse_topo_rank=total - topo_rank - 1,
            topo_level=topo_level[vertex_id],
            dependency_count=dependency_count[vertex_id],
            dependent_count=dependent_count[vertex_id],
            unresolved_dependency_count=unresolved_count[vertex_id],
            cycle_status=cycle_status,
            payload_json=json_text(payload),
        ))
    return output


def run_topology_analysis_pipeline(
    store: IntelStore,
    scope: dict[str, Any],
    trigger_kind: str,
    dry_run: bool,
) -> dict[str, Any]:
    graph_scope = str(scope.get("graphScope") or os.environ.get("INTEL_TOPOLOGY_GRAPH_SCOPE", "global"))
    max_nodes_per_table = int(scope.get("maxNodesPerTable") or int_env("INTEL_TOPOLOGY_MAX_NODES_PER_TABLE", 1000, minimum=1, maximum=20000))
    max_edges_per_table = int(scope.get("maxEdgesPerTable") or int_env("INTEL_TOPOLOGY_MAX_EDGES_PER_TABLE", 5000, minimum=1, maximum=50000))
    llm_edge_limit = int(scope.get("llmEdgeLimit") or int_env("INTEL_TOPOLOGY_LLM_EDGE_LIMIT", 100, minimum=1, maximum=500))

    run = store.create_run({"topology": scope, "graphScope": graph_scope}, trigger_kind, dry_run)
    nodes = store.scan_topology_nodes(graph_scope, max_nodes_per_table)
    scanned_edges = store.scan_topology_edges(graph_scope, max_edges_per_table)
    dependency_edges = store.infer_topology_dependencies_with_llm(scanned_edges, llm_edge_limit)
    order_rows = compute_topology_order(graph_scope, nodes, dependency_edges)
    edge_result = store.materialize_topology_dependencies(graph_scope, run["runId"], dependency_edges, dry_run)
    order_result = store.materialize_topology_order(graph_scope, order_rows, dry_run)
    cycle_count = sum(1 for row in order_rows if row.cycle_status != "acyclic")
    return {
        "runId": run["runId"],
        "graphScope": graph_scope,
        "nodeCount": len(nodes),
        "scannedEdgeCount": len(scanned_edges),
        "dependencyEdgeCount": edge_result["dependencyEdgeCount"],
        "topologyOrderCount": order_result["topologyOrderCount"],
        "cycleMemberCount": cycle_count,
        "dryRun": dry_run,
    }


def run_topology_analysis_with_langgraph(
    store: IntelStore,
    scope: dict[str, Any],
    trigger_kind: str,
    dry_run: bool,
) -> dict[str, Any]:
    if not bool_env("INTEL_TOPOLOGY_USE_LANGGRAPH", True):
        return run_topology_analysis_pipeline(store, scope, trigger_kind, dry_run)
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return run_topology_analysis_pipeline(store, scope, trigger_kind, dry_run)

    graph_scope = str(scope.get("graphScope") or os.environ.get("INTEL_TOPOLOGY_GRAPH_SCOPE", "global"))
    max_nodes_per_table = int(scope.get("maxNodesPerTable") or int_env("INTEL_TOPOLOGY_MAX_NODES_PER_TABLE", 1000, minimum=1, maximum=20000))
    max_edges_per_table = int(scope.get("maxEdgesPerTable") or int_env("INTEL_TOPOLOGY_MAX_EDGES_PER_TABLE", 5000, minimum=1, maximum=50000))
    llm_edge_limit = int(scope.get("llmEdgeLimit") or int_env("INTEL_TOPOLOGY_LLM_EDGE_LIMIT", 100, minimum=1, maximum=500))

    def create_run_node(state: dict[str, Any]) -> dict[str, Any]:
        run = store.create_run({"topology": scope, "graphScope": graph_scope}, trigger_kind, dry_run)
        return {**state, "runId": run["runId"]}

    def scan_node(state: dict[str, Any]) -> dict[str, Any]:
        return {
            **state,
            "nodes": store.scan_topology_nodes(graph_scope, max_nodes_per_table),
            "scannedEdges": store.scan_topology_edges(graph_scope, max_edges_per_table),
        }

    def infer_node(state: dict[str, Any]) -> dict[str, Any]:
        return {
            **state,
            "dependencyEdges": store.infer_topology_dependencies_with_llm(state["scannedEdges"], llm_edge_limit),
        }

    def order_node(state: dict[str, Any]) -> dict[str, Any]:
        return {
            **state,
            "orderRows": compute_topology_order(graph_scope, state["nodes"], state["dependencyEdges"]),
        }

    def materialize_node(state: dict[str, Any]) -> dict[str, Any]:
        edge_result = store.materialize_topology_dependencies(graph_scope, state["runId"], state["dependencyEdges"], dry_run)
        order_result = store.materialize_topology_order(graph_scope, state["orderRows"], dry_run)
        return {**state, "edgeResult": edge_result, "orderResult": order_result}

    builder = StateGraph(dict)
    builder.add_node("create_run", create_run_node)
    builder.add_node("scan", scan_node)
    builder.add_node("infer", infer_node)
    builder.add_node("order", order_node)
    builder.add_node("materialize", materialize_node)
    builder.set_entry_point("create_run")
    builder.add_edge("create_run", "scan")
    builder.add_edge("scan", "infer")
    builder.add_edge("infer", "order")
    builder.add_edge("order", "materialize")
    builder.add_edge("materialize", END)
    result = builder.compile().invoke({})
    return {
        "runId": result["runId"],
        "graphScope": graph_scope,
        "nodeCount": len(result["nodes"]),
        "scannedEdgeCount": len(result["scannedEdges"]),
        "dependencyEdgeCount": result["edgeResult"]["dependencyEdgeCount"],
        "topologyOrderCount": result["orderResult"]["topologyOrderCount"],
        "cycleMemberCount": sum(1 for row in result["orderRows"] if row.cycle_status != "acyclic"),
        "dryRun": dry_run,
        "engine": "langgraph",
    }


def run_pipeline(
    store: IntelStore,
    scope: dict[str, Any],
    trigger_kind: str,
    max_candidates: int,
    dry_run: bool,
) -> dict[str, Any]:
    run = store.create_run(scope, trigger_kind, dry_run)
    candidates = store.scan_candidates(scope, max_candidates)
    valid = validate_candidates(candidates)
    resolved = resolve_with_langgraph(valid)
    result = store.materialize(run["runId"], resolved, dry_run)
    return {"runId": run["runId"], **result}


async def run_once_from_env() -> None:
    store = IntelStore(os.environ["RW_DSN"])
    scope = json.loads(os.environ.get("INTEL_SCOPE_JSON", "{}"))
    if bool_env("INTEL_TOPOLOGY_ANALYZE", False):
        result = run_topology_analysis_with_langgraph(
            store=store,
            scope=scope,
            trigger_kind=os.environ.get("INTEL_TRIGGER_KIND", "scheduled_topology"),
            dry_run=os.environ.get("INTEL_DRY_RUN", "false").lower() == "true",
        )
        print(json.dumps(result, sort_keys=True))
        return
    result = run_pipeline(
        store=store,
        scope=scope,
        trigger_kind=os.environ.get("INTEL_TRIGGER_KIND", "scheduled"),
        max_candidates=int(os.environ.get("INTEL_MAX_CANDIDATES", "500")),
        dry_run=os.environ.get("INTEL_DRY_RUN", "false").lower() == "true",
    )
    print(json.dumps(result, sort_keys=True))


class LangServerWorker:
    def __init__(self, *, name: str = "intel-dependency-worker") -> None:
        self.name = name
        self.handlers: dict[str, Any] = {}

    def task(self, *, task_type: str, **_: Any) -> Any:
        def decorator(fn: Any) -> Any:
            self.handlers[task_type] = fn
            return fn

        return decorator

    async def work(self) -> None:
        port = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8080")))
        agentgateway_mcp_url = os.environ.get(
            "AGENTGATEWAY_MCP_URL",
            "http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080",
        )
        app = FastAPI(title=self.name, version="1.0.0")

        @app.get("/healthz")
        async def healthz() -> dict[str, Any]:
            return {
                "ok": True,
                "runtimeKind": "k8s-langserver",
                "agentGatewayMcpUrl": agentgateway_mcp_url,
                "tools": sorted(self.handlers),
            }

        @app.get("/tools")
        async def tools() -> dict[str, Any]:
            return {"tools": [{"name": name, "runtime": "langserver"} for name in sorted(self.handlers)]}

        async def invoke_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            handler = self.handlers.get(name)
            if handler is None:
                raise HTTPException(status_code=404, detail=f"unknown tool: {name}")
            return await handler(**arguments)

        @app.post("/invoke")
        async def invoke(payload: dict[str, Any]) -> dict[str, Any]:
            name = str(payload.get("name") or payload.get("tool") or "")
            arguments = payload.get("arguments") or payload.get("input") or {}
            if not isinstance(arguments, dict):
                raise HTTPException(status_code=400, detail="arguments must be an object")
            return {"ok": True, "name": name, "result": await invoke_tool(name, arguments)}

        @app.post("/runs")
        async def runs(payload: dict[str, Any]) -> dict[str, Any]:
            assistant_id = str(payload.get("assistant_id") or "")
            arguments = payload.get("input") or payload.get("arguments") or {}
            if not isinstance(arguments, dict):
                raise HTTPException(status_code=400, detail="input must be an object")
            return {"status": "completed", "assistant_id": assistant_id, "output": await invoke_tool(assistant_id, arguments)}

        await uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")).serve()


async def run_langserver_worker() -> None:
    worker = LangServerWorker()
    store = IntelStore(os.environ["RW_DSN"])

    async def topology_daemon_loop() -> None:
        interval_sec = int_env("INTEL_TOPOLOGY_INTERVAL_SEC", 900, minimum=60)
        while True:
            try:
                scope = json.loads(os.environ.get("INTEL_TOPOLOGY_SCOPE_JSON", "{}"))
                result = await asyncio.to_thread(
                    run_topology_analysis_with_langgraph,
                    store,
                    scope,
                    "daemon_topology",
                    bool_env("INTEL_TOPOLOGY_DRY_RUN", False),
                )
                print(json.dumps({"topologyDaemon": result}, sort_keys=True), flush=True)
            except Exception as exc:
                print(json.dumps({
                    "topologyDaemonError": type(exc).__name__,
                    "message": str(exc),
                }, sort_keys=True), flush=True)
            await asyncio.sleep(interval_sec)

    @worker.task(task_type="intel.run.create")
    async def task_run_create(
        scope: dict[str, Any] | None = None,
        triggerKind: str | None = None,
        dryRun: bool | None = None,
    ) -> dict[str, Any]:
        return store.create_run(scope or {}, triggerKind or "mcp_call", bool(dryRun))

    @worker.task(task_type="intel.candidate.scan")
    async def task_candidate_scan(
        scope: dict[str, Any] | None = None,
        maxCandidates: int | None = None,
    ) -> dict[str, Any]:
        candidates = store.scan_candidates(scope or {}, maxCandidates or 500)
        return {
            "candidates": [candidate_to_dict(c) for c in candidates],
            "candidateCount": len(candidates),
        }

    @worker.task(task_type="intel.owl.validate")
    async def task_owl_validate(candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        valid = validate_candidates([candidate_from_dict(c) for c in candidates or []])
        return {"validCandidates": [candidate_to_dict(c) for c in valid]}

    @worker.task(task_type="intel.langgraph.resolve")
    async def task_langgraph_resolve(
        validCandidates: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        resolved = resolve_with_langgraph([candidate_from_dict(c) for c in validCandidates or []])
        return {"resolvedEdges": [candidate_to_dict(c) for c in resolved]}

    @worker.task(task_type="intel.edge.materialize")
    async def task_edge_materialize(
        runId: str,
        resolvedEdges: list[dict[str, Any]] | None = None,
        dryRun: bool | None = None,
    ) -> dict[str, Any]:
        result = store.materialize(
            runId,
            [candidate_from_dict(c) for c in resolvedEdges or []],
            bool(dryRun),
        )
        return {"runId": runId, **result}

    @worker.task(task_type="intel.dependency.explain")
    async def task_dependency_explain(
        edgeId: str | None = None,
        fromVertexId: str | None = None,
        toVertexId: str | None = None,
        predicate: str | None = None,
    ) -> dict[str, Any]:
        return store.explain_dependency(edgeId, fromVertexId, toVertexId, predicate)

    @worker.task(task_type="intel.dependency.list")
    async def task_dependency_list(
        status: str | None = None,
        predicate: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        return store.list_dependency_candidates(status or "candidate", predicate, limit, offset)

    @worker.task(task_type="intel.entity.resolve")
    async def task_entity_resolve(
        runId: str | None = None,
        query: str | None = None,
        entityKind: str | None = None,
        hints: dict[str, Any] | None = None,
        maxCandidates: int | None = None,
    ) -> dict[str, Any]:
        return store.resolve_entity(runId, query, entityKind, hints, maxCandidates)

    @worker.task(task_type="intel.graph.buildingOwnership")
    async def task_graph_building_ownership(
        buildingVertexId: str | None = None,
        lei: str | None = None,
        bbox: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        # bbox is retained in the contract; current materialized intel edges are
        # keyed by vertex ids / LEI and can add spatial filtering once the
        # building subject mirror is populated with geometry.
        _ = bbox
        return store.get_building_ownership_graph(buildingVertexId, lei, limit)

    @worker.task(task_type="intel.graph.counterparty")
    async def task_graph_counterparty(
        subjectVertexId: str | None = None,
        lei: str | None = None,
        relationKinds: list[str] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return store.get_counterparty_graph(subjectVertexId, lei, relationKinds, limit)

    @worker.task(task_type="intel.topology.analyze")
    async def task_topology_analyze(
        scope: dict[str, Any] | None = None,
        dryRun: bool | None = None,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            run_topology_analysis_with_langgraph,
            store,
            scope or {},
            "langserver_topology",
            bool(dryRun),
        )

    @worker.task(task_type="intel.topology.update")
    async def task_topology_update(
        graphScope: str | None = None,
        maxNodesPerTable: int | None = None,
        maxEdgesPerTable: int | None = None,
        dryRun: bool | None = None,
    ) -> dict[str, Any]:
        scope = {
            "graphScope": graphScope or "global",
            "maxNodesPerTable": maxNodesPerTable,
            "maxEdgesPerTable": maxEdgesPerTable,
        }
        return await asyncio.to_thread(
            run_topology_analysis_with_langgraph,
            store,
            scope,
            "langserver_topology_update",
            bool(dryRun),
        )

    if bool_env("INTEL_TOPOLOGY_DAEMON", False):
        asyncio.create_task(topology_daemon_loop())

    await worker.work()


async def run_langserver_worker_forever() -> None:
    restart_delay_sec = int_env("LANGSERVER_WORKER_RESTART_DELAY_SEC", 15, minimum=1, maximum=300)
    while True:
        try:
            await run_langserver_worker()
            print(json.dumps({
                "langserverWorkerStopped": True,
                "restartDelaySec": restart_delay_sec,
            }, sort_keys=True), flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(json.dumps({
                "langserverWorkerError": type(exc).__name__,
                "message": str(exc),
                "restartDelaySec": restart_delay_sec,
            }, sort_keys=True), flush=True)
        await asyncio.sleep(restart_delay_sec)


def candidate_to_dict(c: Candidate) -> dict[str, Any]:
    return {
        "src_vid": c.src_vid,
        "dst_vid": c.dst_vid,
        "predicate": c.predicate,
        "dependency_kind": c.dependency_kind,
        "confidence": c.confidence,
        "evidence": c.evidence,
        "reason": c.reason,
    }


def candidate_from_dict(raw: dict[str, Any]) -> Candidate:
    return Candidate(
        src_vid=str(raw.get("src_vid", "")),
        dst_vid=str(raw.get("dst_vid", "")),
        predicate=str(raw.get("predicate", "")),
        dependency_kind=str(raw.get("dependency_kind", "")),
        confidence=float(raw.get("confidence") or 0.0),
        evidence=list(raw.get("evidence") or []),
        reason=str(raw.get("reason", "")),
    )


async def main() -> None:
    # The container is useful both as a scheduled K8s worker and as a
    # LangServer task worker image.
    if os.environ.get("RUN_ONCE", "true").lower() == "true":
        await run_once_from_env()
        return
    await run_langserver_worker_forever()


if __name__ == "__main__":
    asyncio.run(main())
