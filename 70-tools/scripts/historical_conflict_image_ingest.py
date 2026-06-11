#!/usr/bin/env python3
"""Backfill historical conflicts, treaty actors, and public image artifacts.

Sources:
- Wikidata SPARQL for conflict/treaty/person/organization metadata.
- Wikimedia Commons Special:FilePath URLs for source image references.
- Existing `vertex_houbun_treaty` rows for UNTC treaty seeds.

This intentionally stores image references and provenance first. It does not
download image bytes by default; `ipfs_cid` stays NULL until a pinning worker
materializes the object into B2/IPFS and computes a CID.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError as exc:  # pragma: no cover
    raise SystemExit("psycopg2 is required: pip install psycopg2-binary") from exc


ACTOR_DID = "did:web:history.etzhayyim.com"
HOUBUN_DID = "did:web:houbun.etzhayyim.com"
SPARQL_URL = "https://query.wikidata.org/sparql"
USER_AGENT = "etzhayyim-historical-conflict-ingest/0.1 (+https://etzhayyim.com)"
NON_ALNUM = re.compile(r"[^a-z0-9]+")
WS = re.compile(r"\s+")


@dataclass(frozen=True)
class ActorRef:
    did: str
    name: str
    kind: str
    qid: str
    vertex_id: str


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return now_iso()[:10]


def clean(value: Any, max_len: int = 512) -> str:
    return WS.sub(" ", str(value or "")).strip()[:max_len]


def slug(value: str, max_len: int = 80) -> str:
    out = NON_ALNUM.sub("-", clean(value).lower()).strip("-")
    return (out or "unknown")[:max_len]


def digest(*parts: Any, size: int = 8) -> str:
    payload = "|".join(clean(x, 2000) for x in parts)
    return hashlib.blake2b(payload.encode("utf-8"), digest_size=size).hexdigest()


def did_for(kind: str, qid: str, label: str) -> str:
    return f"{ACTOR_DID}:{kind}:{slug(qid or label, 48)}"


def actor_ref(kind: str, qid: str, label: str) -> ActorRef:
    did = did_for(kind, qid, label)
    return ActorRef(did=did, name=clean(label) or qid, kind=kind, qid=qid, vertex_id=did)


def sparql(query: str, *, retries: int = 4) -> list[dict[str, dict[str, str]]]:
    url = f"{SPARQL_URL}?{urllib.parse.urlencode({'format': 'json', 'query': query})}"
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            rows = payload.get("results", {}).get("bindings", [])
            return rows if isinstance(rows, list) else []
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            wait = 2 + attempt * 3
            print(f"[sparql] retry {attempt + 1}/{retries}: {exc}; sleep={wait}s", file=sys.stderr)
            time.sleep(wait)
    return []


def binding(row: dict[str, dict[str, str]], key: str) -> str:
    return clean((row.get(key) or {}).get("value"))


def qid_from_uri(uri: str) -> str:
    return uri.rsplit("/", 1)[-1] if uri else ""


def commons_url(file_name: str, width: int | None = None) -> str:
    base = "https://commons.wikimedia.org/wiki/Special:FilePath/"
    path = urllib.parse.quote(file_name.replace(" ", "_"), safe="")
    if width:
        return f"{base}{path}?width={width}"
    return f"{base}{path}"


def conflict_query(limit: int, offset: int) -> str:
    # Q198 = war. The subclass path also captures narrower war/conflict classes.
    return f"""
    SELECT ?item ?itemLabel ?start ?end ?image ?participant ?participantLabel ?treaty ?treatyLabel WHERE {{
      ?item wdt:P31/wdt:P279* wd:Q198.
      OPTIONAL {{ ?item wdt:P580 ?start. }}
      OPTIONAL {{ ?item wdt:P582 ?end. }}
      OPTIONAL {{ ?item wdt:P18 ?image. }}
      OPTIONAL {{ ?item wdt:P710 ?participant. }}
      OPTIONAL {{
        ?item ?rel ?treaty.
        VALUES ?rel {{ wdt:P1343 wdt:P1441 wdt:P1552 wdt:P361 wdt:P527 }}
        ?treaty wdt:P31/wdt:P279* wd:Q131569.
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ja". }}
    }}
    ORDER BY ?item
    LIMIT {max(1, min(limit, 500))}
    OFFSET {max(0, offset)}
    """


def treaty_actor_query(limit: int, offset: int) -> str:
    return f"""
    SELECT ?item ?itemLabel ?image ?participant ?participantLabel WHERE {{
      ?item wdt:P31/wdt:P279* wd:Q131569.
      OPTIONAL {{ ?item wdt:P18 ?image. }}
      OPTIONAL {{ ?item wdt:P710 ?participant. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ja". }}
    }}
    ORDER BY ?item
    LIMIT {max(1, min(limit, 500))}
    OFFSET {max(0, offset)}
    """


def houbun_treaty_rows(conn: Any, limit: int) -> list[dict[str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT vertex_id, title, source_record_id, source_url
              FROM vertex_houbun_treaty
             ORDER BY created_at DESC
             LIMIT %s
            """,
            (max(1, limit),),
        )
        return [
            {"vertex_id": r[0], "title": r[1], "source_record_id": r[2], "source_url": r[3]}
            for r in cur.fetchall()
        ]


def insert_ignore(conn: Any, table: str, id_col: str, rows: list[tuple[Any, ...]], cols: list[str], page_size: int = 200) -> int:
    if not rows:
        return 0
    with conn.cursor() as cur:
        cur.execute(f"SELECT {id_col} FROM {table} WHERE {id_col} = ANY(%s)", ([r[0] for r in rows],))
        existing = {r[0] for r in cur.fetchall()}
        todo = [r for r in rows if r[0] not in existing]
        if not todo:
            return 0
        execute_values(cur, f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s", todo, page_size=max(1, min(page_size, 200)))
    return len(todo)


def count_existing(conn: Any, table: str, id_col: str, rows: list[tuple[Any, ...]]) -> int:
    if not rows:
        return 0
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {id_col} = ANY(%s)", ([r[0] for r in rows],))
        return int(cur.fetchone()[0])


def build_actor_rows(actors: dict[str, ActorRef], current: str) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []
    for actor in actors.values():
        rows.append(
            (
                actor.vertex_id,
                int(time.time() * 1000),
                today(),
                1,
                ACTOR_DID,
                actor.did,
                f"hist-{digest(actor.did, size=4)}",
                actor.did.replace("did:web:", ""),
                actor.name,
                "T3",
                "active",
                "com.etzhayyim.apps.history.actor",
                slug(actor.qid or actor.name, 64),
                actor.did,
                current,
                actor.name,
                "history",
                "logical",
                "database",
                "yoro",
                "knowledge",
                actor.kind,
                "wikidata",
                "history",
                json.dumps({"qid": actor.qid, "kind": actor.kind}, ensure_ascii=False, sort_keys=True),
            )
        )
    return rows


def build_follow_edge(src: ActorRef, dst: ActorRef, current: str, relation: str) -> tuple[Any, ...]:
    rkey = f"follow-{slug(relation, 12)}-{digest(src.did, dst.did, relation, size=4)}"
    return (
        f"at://{src.did}/app.bsky.graph.follow/{rkey}",
        src.did,
        dst.did,
        int(time.time() * 1000),
        today(),
        1,
        src.did,
        rkey,
        src.did,
        current,
    )


def collect(limit_conflicts: int, limit_treaties: int, offset: int) -> dict[str, Any]:
    current = now_iso()
    actors: dict[str, ActorRef] = {}
    conflicts: dict[str, tuple[Any, ...]] = {}
    images: dict[str, tuple[Any, ...]] = {}
    edge_conflict_actor: dict[str, tuple[Any, ...]] = {}
    edge_conflict_treaty: dict[str, tuple[Any, ...]] = {}
    edge_treaty_actor: dict[str, tuple[Any, ...]] = {}
    edge_image_subject: dict[str, tuple[Any, ...]] = {}
    follows: dict[str, tuple[Any, ...]] = {}

    def remember_actor(kind: str, qid: str, label: str) -> ActorRef:
        actor = actor_ref(kind, qid, label)
        actors[actor.did] = actor
        return actor

    for row in sparql(conflict_query(limit_conflicts, offset)):
        item_uri = binding(row, "item")
        qid = qid_from_uri(item_uri)
        name = binding(row, "itemLabel") or qid
        conflict_actor = remember_actor("conflict", qid, name)
        conflict_vid = f"at://{conflict_actor.did}/com.etzhayyim.apps.history.conflict/{slug(qid, 64)}"
        participants: list[str] = []
        participant_uri = binding(row, "participant")
        participant_qid = qid_from_uri(participant_uri)
        participant_label = binding(row, "participantLabel")
        if participant_qid:
            kind = "organization"
            participant_actor = remember_actor(kind, participant_qid, participant_label or participant_qid)
            participants.append(participant_qid)
            edge_id = f"{conflict_vid}::{participant_actor.did}::participant"
            edge_conflict_actor[edge_id] = (
                edge_id,
                conflict_vid,
                participant_actor.did,
                int(time.time() * 1000),
                today(),
                1,
                ACTOR_DID,
                "participant",
                0.75,
                "wikidata",
                current,
                "etzhayyim",
                "system",
                "sys.history",
                json.dumps({"participantQid": participant_qid}, sort_keys=True),
            )
            follows[edge_id] = build_follow_edge(conflict_actor, participant_actor, current, "participant")

        treaty_uri = binding(row, "treaty")
        treaty_qid = qid_from_uri(treaty_uri)
        treaty_label = binding(row, "treatyLabel")
        if treaty_qid:
            treaty_actor = remember_actor("treaty", treaty_qid, treaty_label or treaty_qid)
            treaty_vid = f"at://{treaty_actor.did}/com.etzhayyim.apps.houbun.treaty/{slug(treaty_qid, 64)}"
            edge_id = f"{conflict_vid}::{treaty_vid}::related-treaty"
            edge_conflict_treaty[edge_id] = (
                edge_id,
                conflict_vid,
                treaty_vid,
                int(time.time() * 1000),
                today(),
                1,
                ACTOR_DID,
                "related_treaty",
                0.45,
                "wikidata",
                current,
                "etzhayyim",
                "system",
                "sys.history",
                json.dumps({"treatyQid": treaty_qid}, sort_keys=True),
            )
            follows[edge_id] = build_follow_edge(conflict_actor, treaty_actor, current, "related-treaty")

        image = binding(row, "image")
        if image:
            file_name = urllib.parse.unquote(image.rsplit("/", 1)[-1]).replace("_", " ")
            image_id = digest(qid, file_name)
            image_vid = f"at://{ACTOR_DID}/com.etzhayyim.apps.history.sourceImage/{image_id}"
            images[image_vid] = (
                image_vid,
                int(time.time() * 1000),
                today(),
                1,
                ACTOR_DID,
                image_id,
                "wikidata-commons",
                qid,
                conflict_vid,
                "conflict",
                file_name,
                file_name,
                commons_url(file_name),
                image,
                commons_url(file_name, width=1024),
                None,
                None,
                None,
                "Wikimedia Commons",
                None,
                current,
                current,
                "etzhayyim",
                "system",
                "sys.history",
                json.dumps({"wikidataQid": qid}, sort_keys=True),
            )
            edge_id = f"{image_vid}::{conflict_vid}"
            edge_image_subject[edge_id] = (
                edge_id,
                image_vid,
                conflict_vid,
                int(time.time() * 1000),
                today(),
                1,
                ACTOR_DID,
                "depicts",
                0.80,
                "wikidata",
                current,
                "etzhayyim",
                "system",
                "sys.history",
                json.dumps({"wikidataQid": qid}, sort_keys=True),
            )

        conflicts[conflict_vid] = (
            conflict_vid,
            int(time.time() * 1000),
            today(),
            1,
            ACTOR_DID,
            qid,
            name,
            qid,
            binding(row, "start"),
            binding(row, "end"),
            None,
            json.dumps(sorted(set(participants)), ensure_ascii=False),
            item_uri,
            None,
            current,
            current,
            "etzhayyim",
            "system",
            "sys.history",
            json.dumps({"wikidataQid": qid}, sort_keys=True),
        )

    for row in sparql(treaty_actor_query(limit_treaties, offset)):
        item_uri = binding(row, "item")
        qid = qid_from_uri(item_uri)
        label = binding(row, "itemLabel") or qid
        treaty_actor = remember_actor("treaty", qid, label)
        participant_qid = qid_from_uri(binding(row, "participant"))
        if participant_qid:
            participant = remember_actor("organization", participant_qid, binding(row, "participantLabel") or participant_qid)
            treaty_vid = f"at://{treaty_actor.did}/com.etzhayyim.apps.houbun.treaty/{slug(qid, 64)}"
            edge_id = f"{treaty_vid}::{participant.did}::party"
            edge_treaty_actor[edge_id] = (
                edge_id,
                treaty_vid,
                participant.did,
                int(time.time() * 1000),
                today(),
                1,
                ACTOR_DID,
                "party",
                0.75,
                "wikidata",
                current,
                "etzhayyim",
                "system",
                "sys.history",
                json.dumps({"participantQid": participant_qid}, sort_keys=True),
            )
            follows[edge_id] = build_follow_edge(treaty_actor, participant, current, "party")

        image = binding(row, "image")
        if image:
            file_name = urllib.parse.unquote(image.rsplit("/", 1)[-1]).replace("_", " ")
            treaty_vid = f"at://{treaty_actor.did}/com.etzhayyim.apps.houbun.treaty/{slug(qid, 64)}"
            image_id = digest(qid, file_name)
            image_vid = f"at://{ACTOR_DID}/com.etzhayyim.apps.history.sourceImage/{image_id}"
            images[image_vid] = (
                image_vid,
                int(time.time() * 1000),
                today(),
                1,
                ACTOR_DID,
                image_id,
                "wikidata-commons",
                qid,
                treaty_vid,
                "treaty",
                file_name,
                file_name,
                commons_url(file_name),
                image,
                commons_url(file_name, width=1024),
                None,
                None,
                None,
                "Wikimedia Commons",
                None,
                current,
                current,
                "etzhayyim",
                "system",
                "sys.history",
                json.dumps({"wikidataQid": qid}, sort_keys=True),
            )
            edge_id = f"{image_vid}::{treaty_vid}"
            edge_image_subject[edge_id] = (
                edge_id,
                image_vid,
                treaty_vid,
                int(time.time() * 1000),
                today(),
                1,
                ACTOR_DID,
                "depicts",
                0.80,
                "wikidata",
                current,
                "etzhayyim",
                "system",
                "sys.history",
                json.dumps({"wikidataQid": qid}, sort_keys=True),
            )

    return {
        "actors": actors,
        "actor_rows": build_actor_rows(actors, current),
        "conflict_rows": list(conflicts.values()),
        "image_rows": list(images.values()),
        "edge_conflict_actor_rows": list(edge_conflict_actor.values()),
        "edge_conflict_treaty_rows": list(edge_conflict_treaty.values()),
        "edge_treaty_actor_rows": list(edge_treaty_actor.values()),
        "edge_image_subject_rows": list(edge_image_subject.values()),
        "follow_rows": list(follows.values()),
    }


def configure_session(conn: Any, *, dml_rate_limit: int | None, backfill_rate_limit: int | None, statement_timeout: str | None) -> None:
    with conn.cursor() as cur:
        if statement_timeout:
            cur.execute("SET statement_timeout = %s", (statement_timeout,))
        if dml_rate_limit is not None:
            cur.execute("SET dml_rate_limit = %s", (dml_rate_limit,))
        if backfill_rate_limit is not None:
            cur.execute("SET backfill_rate_limit = %s", (backfill_rate_limit,))


def write_rows(conn: Any, data: dict[str, Any], *, page_size: int = 50) -> dict[str, int]:
    actor_cols = [
        "vertex_id",
        "_seq",
        "created_date",
        "sensitivity_ord",
        "owner_did",
        "did",
        "nanoid",
        "handle",
        "display_name",
        "execution_tier",
        "status",
        "collection",
        "rkey",
        "repo",
        "created_at",
        "name",
        "project",
        "performer_type",
        "runtime_type",
        "ui_type",
        "agent_type",
        "classification",
        "operator",
        "category",
        "val",
    ]
    conflict_cols = [
        "vertex_id",
        "_seq",
        "created_date",
        "sensitivity_ord",
        "owner_did",
        "conflict_id",
        "name",
        "wikidata_qid",
        "start_time",
        "end_time",
        "location_json",
        "participant_qids_json",
        "source_url",
        "summary",
        "created_at",
        "updated_at",
        "org_id",
        "user_id",
        "actor_id",
        "props",
    ]
    image_cols = [
        "vertex_id",
        "_seq",
        "created_date",
        "sensitivity_ord",
        "owner_did",
        "image_id",
        "source",
        "source_record_id",
        "subject_vid",
        "subject_kind",
        "title",
        "commons_file",
        "commons_url",
        "original_url",
        "thumb_url",
        "ipfs_cid",
        "sha256",
        "mime_type",
        "license",
        "llm_analysis_json",
        "created_at",
        "updated_at",
        "org_id",
        "user_id",
        "actor_id",
        "props",
    ]
    edge_cols = [
        "edge_id",
        "src_vid",
        "dst_vid",
        "_seq",
        "created_date",
        "sensitivity_ord",
        "owner_did",
        "relation",
        "confidence",
        "source",
        "created_at",
        "org_id",
        "user_id",
        "actor_id",
        "props",
    ]
    follow_cols = ["edge_id", "src_vid", "dst_vid", "_seq", "created_date", "sensitivity_ord", "owner_did", "rkey", "repo", "created_at"]
    existing_tables = list_tables(conn)
    counts: dict[str, int] = {}
    if "vertex_actor" in existing_tables:
        counts["vertex_actor"] = insert_ignore(conn, "vertex_actor", "vertex_id", data["actor_rows"], actor_cols, page_size)
    if "vertex_historical_conflict" in existing_tables:
        counts["vertex_historical_conflict"] = insert_ignore(conn, "vertex_historical_conflict", "vertex_id", data["conflict_rows"], conflict_cols, page_size)
    if "vertex_historical_source_image" in existing_tables:
        counts["vertex_historical_source_image"] = insert_ignore(conn, "vertex_historical_source_image", "vertex_id", data["image_rows"], image_cols, page_size)
    elif "vertex_ingest_artifact" in existing_tables:
        counts["vertex_ingest_artifact:image.raw_reference"] = insert_ignore(
            conn,
            "vertex_ingest_artifact",
            "vertex_id",
            image_artifact_rows(data["image_rows"]),
            [
                "vertex_id",
                "_seq",
                "created_date",
                "sensitivity_ord",
                "owner_did",
                "run_id",
                "artifact_kind",
                "source_id",
                "uri",
                "sha256",
                "byte_size",
                "record_count",
                "created_at",
                "props",
            ],
            page_size,
        )
    if "edge_historical_conflict_actor" in existing_tables:
        counts["edge_historical_conflict_actor"] = insert_ignore(conn, "edge_historical_conflict_actor", "edge_id", data["edge_conflict_actor_rows"], edge_cols, page_size)
    if "edge_historical_conflict_treaty" in existing_tables:
        counts["edge_historical_conflict_treaty"] = insert_ignore(conn, "edge_historical_conflict_treaty", "edge_id", data["edge_conflict_treaty_rows"], edge_cols, page_size)
    if "edge_historical_treaty_actor" in existing_tables:
        counts["edge_historical_treaty_actor"] = insert_ignore(conn, "edge_historical_treaty_actor", "edge_id", data["edge_treaty_actor_rows"], edge_cols, page_size)
    if "edge_historical_image_subject" in existing_tables:
        counts["edge_historical_image_subject"] = insert_ignore(conn, "edge_historical_image_subject", "edge_id", data["edge_image_subject_rows"], edge_cols, page_size)
    if "edge_follows" in existing_tables:
        counts["edge_follows"] = insert_ignore(conn, "edge_follows", "edge_id", data["follow_rows"], follow_cols, page_size)
    conn.commit()
    if os.environ.get("RW_ALLOW_FLUSH", "0").lower() in {"1", "true", "on", "yes"}:
        with conn.cursor() as cur:
            cur.execute("FLUSH")
    return counts


def verify_rows(conn: Any, data: dict[str, Any]) -> dict[str, int]:
    existing_tables = list_tables(conn)
    counts: dict[str, int] = {}
    if "vertex_actor" in existing_tables:
        counts["vertex_actor"] = count_existing(conn, "vertex_actor", "vertex_id", data["actor_rows"])
    if "vertex_historical_conflict" in existing_tables:
        counts["vertex_historical_conflict"] = count_existing(conn, "vertex_historical_conflict", "vertex_id", data["conflict_rows"])
    if "vertex_historical_source_image" in existing_tables:
        counts["vertex_historical_source_image"] = count_existing(conn, "vertex_historical_source_image", "vertex_id", data["image_rows"])
    elif "vertex_ingest_artifact" in existing_tables:
        counts["vertex_ingest_artifact:image.raw_reference"] = count_existing(
            conn,
            "vertex_ingest_artifact",
            "vertex_id",
            image_artifact_rows(data["image_rows"]),
        )
    if "edge_historical_conflict_actor" in existing_tables:
        counts["edge_historical_conflict_actor"] = count_existing(conn, "edge_historical_conflict_actor", "edge_id", data["edge_conflict_actor_rows"])
    if "edge_historical_conflict_treaty" in existing_tables:
        counts["edge_historical_conflict_treaty"] = count_existing(conn, "edge_historical_conflict_treaty", "edge_id", data["edge_conflict_treaty_rows"])
    if "edge_historical_treaty_actor" in existing_tables:
        counts["edge_historical_treaty_actor"] = count_existing(conn, "edge_historical_treaty_actor", "edge_id", data["edge_treaty_actor_rows"])
    if "edge_historical_image_subject" in existing_tables:
        counts["edge_historical_image_subject"] = count_existing(conn, "edge_historical_image_subject", "edge_id", data["edge_image_subject_rows"])
    if "edge_follows" in existing_tables:
        counts["edge_follows"] = count_existing(conn, "edge_follows", "edge_id", data["follow_rows"])
    return counts


def list_tables(conn: Any) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
              FROM information_schema.tables
             WHERE table_schema IN ('public', current_schema())
            """
        )
        return {str(r[0]) for r in cur.fetchall()}


def image_artifact_rows(image_rows: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []
    current = now_iso()
    for row in image_rows:
        vertex_id = str(row[0])
        subject_vid = row[8]
        subject_kind = row[9]
        title = row[10]
        commons_url_value = row[12]
        original_url = row[13]
        props = {
            "sourceImageVertexId": vertex_id,
            "subjectVid": subject_vid,
            "subjectKind": subject_kind,
            "title": title,
            "commonsFile": row[11],
            "commonsUrl": commons_url_value,
            "originalUrl": original_url,
            "thumbUrl": row[14],
            "license": row[18],
            "llmAnalysisJson": row[19],
            "props": json.loads(row[25]) if row[25] else {},
        }
        uri = str(original_url or commons_url_value or vertex_id)
        rows.append(
            (
                f"at://{ACTOR_DID}/com.etzhayyim.apps.ingest.artifact/{digest('image', uri, size=6)}",
                int(time.time() * 1000),
                today(),
                1,
                ACTOR_DID,
                "historical-conflict-image-backfill",
                "image.raw_reference",
                "wikidata-commons",
                uri,
                digest(uri, size=16),
                None,
                1,
                current,
                json.dumps(props, ensure_ascii=False, sort_keys=True),
            )
        )
    return rows


def apply_migration(conn: Any) -> None:
    path = "30-graph/graph-schema/migrations/20260426170000_vertex_historical_conflict_image_graph.ts"
    text = open(path, encoding="utf-8").read()
    statements = []
    for match in re.finditer(r"sql`\s*(CREATE TABLE IF NOT EXISTS)(.*?)`\.", text, flags=re.S):
        statements.append(match.group(1) + match.group(2))
    old_autocommit = conn.autocommit
    conn.autocommit = True
    with conn.cursor() as cur:
        for stmt in statements:
            try:
                cur.execute(stmt)
            except Exception:  # noqa: BLE001
                raise
    conn.autocommit = old_autocommit


def resolve_rw_url() -> str:
    if os.environ.get("KOTOBA_URL"):
        return os.environ["KOTOBA_URL"]
    if shutil.which("security"):
        proc = subprocess.run(
            ["security", "find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    raise SystemExit("KOTOBA_URL is required or etzhayyim.rw/ROOT_URL must exist in macOS Keychain")


def write_jsonl(path: str, data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    sections = {
        "vertex_actor": data["actor_rows"],
        "vertex_historical_conflict": data["conflict_rows"],
        "vertex_historical_source_image": data["image_rows"],
        "vertex_ingest_artifact_image_reference": image_artifact_rows(data["image_rows"]),
        "edge_historical_conflict_actor": data["edge_conflict_actor_rows"],
        "edge_historical_conflict_treaty": data["edge_conflict_treaty_rows"],
        "edge_historical_treaty_actor": data["edge_treaty_actor_rows"],
        "edge_historical_image_subject": data["edge_image_subject_rows"],
        "edge_follows": data["follow_rows"],
    }
    with open(path, "w", encoding="utf-8") as fh:
        for table, rows in sections.items():
            for row in rows:
                fh.write(json.dumps({"table": table, "row": row}, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-conflicts", type=int, default=100)
    ap.add_argument("--limit-treaties", type=int, default=100)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--apply-migration", action="store_true")
    ap.add_argument("--out", default="", help="Write collected rows as JSONL for replay/staging")
    ap.add_argument("--dml-rate-limit", type=int, default=25, help="RisingWave session DML rows/sec per parallelism")
    ap.add_argument("--backfill-rate-limit", type=int, default=25, help="RisingWave session backfill rows/sec per parallelism")
    ap.add_argument("--statement-timeout", default="5min", help="RisingWave statement_timeout for writes")
    ap.add_argument("--page-size", type=int, default=25, help="execute_values page size for each insert")
    args = ap.parse_args()

    data = collect(args.limit_conflicts, args.limit_treaties, args.offset)
    summary = {
        "actors": len(data["actor_rows"]),
        "conflicts": len(data["conflict_rows"]),
        "images": len(data["image_rows"]),
        "conflictActorEdges": len(data["edge_conflict_actor_rows"]),
        "conflictTreatyEdges": len(data["edge_conflict_treaty_rows"]),
        "treatyActorEdges": len(data["edge_treaty_actor_rows"]),
        "imageSubjectEdges": len(data["edge_image_subject_rows"]),
        "followEdges": len(data["follow_rows"]),
    }
    print(json.dumps({"planned": summary}, ensure_ascii=False, indent=2, sort_keys=True))

    if args.out:
        write_jsonl(args.out, data)
        print(json.dumps({"staged": args.out}, ensure_ascii=False, sort_keys=True))

    if not args.write and not args.apply_migration:
        return

    conn = psycopg2.connect(resolve_rw_url())
    try:
        configure_session(
            conn,
            dml_rate_limit=args.dml_rate_limit,
            backfill_rate_limit=args.backfill_rate_limit,
            statement_timeout=args.statement_timeout,
        )
        if args.apply_migration:
            apply_migration(conn)
        if args.write:
            counts = write_rows(conn, data, page_size=args.page_size)
            verified = verify_rows(conn, data)
            print(json.dumps({"inserted": counts, "verified": verified}, ensure_ascii=False, indent=2, sort_keys=True))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
