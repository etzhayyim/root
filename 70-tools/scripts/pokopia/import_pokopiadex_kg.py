#!/usr/bin/env python3
"""Import PokopiaDex entities into the etzhayyim domain knowledge graph.

The importer keeps one document/chunk per entity so chat retrieval can answer
specific Pokemon, item, habitat/area, and building questions directly.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg


OWNER_DID = "did:web:llm.etzhayyim.com"
AGENT_DID = "did:etzhayyim:agent:codex"
ACTOR_DID = "did:web:media-gamers.etzhayyim.com"
DOMAIN = "media_gamers"
WORK_ID = "game:work:pokemon-pokopia"
GAME_SLUG = "pokemon-pokopia"
SOURCE_BASE = "https://pokopiadex.com"
UA = "Mozilla/5.0 (compatible; etzhayyim-pokopia-kg-import/1.0)"


@dataclass(frozen=True)
class Entity:
    kind: str
    slug: str
    name: str
    description: str
    source_url: str
    props: dict[str, Any]
    number: str | None = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "unknown"


def fetch(url: str) -> str:
    return subprocess.check_output(
        ["curl", "-L", "-s", "-A", UA, url],
        text=True,
    )


def loose_decode(raw: str) -> str:
    text = html.unescape(raw)
    for _ in range(2):
        text = (
            text.replace('\\"', '"')
            .replace("\\/", "/")
            .replace("\\n", "\n")
            .replace("\\u0026", "&")
        )
    return text


def extract_array(text: str, key: str, start_at: int = 0) -> list[dict[str, Any]]:
    idx = text.find(f'"{key}":[', start_at)
    if idx < 0:
        raise ValueError(f"Could not find array key {key!r}")
    start = text.find("[", idx)
    depth = 0
    in_string = False
    escaped = False
    for pos, ch in enumerate(text[start:], start):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : pos + 1])
    raise ValueError(f"Could not close array key {key!r}")


def summarize_pairs(label: str, values: list[Any]) -> str:
    cleaned = [str(v) for v in values if v not in (None, "", [])]
    return f"{label}: {', '.join(cleaned)}" if cleaned else ""


def pokemon_entities(page: str) -> list[Entity]:
    text = loose_decode(page)
    data_start = text.find('"totalBase":300')
    if data_start < 0:
        raise ValueError("Could not find Pokédex totalBase marker")
    items = extract_array(text, "items", max(0, data_start - 120_000))
    entities: list[Entity] = []
    for item in items:
        specialties = [s.get("name") for s in item.get("specialties", [])]
        siblings = [s.get("name") for s in item.get("siblings", [])]
        parts = [
            f"{item.get('name')} is listed in Pokemon Pokopia Pokédex as #{item.get('pokedex_number')}.",
            summarize_pairs("Species", [item.get("species")]),
            summarize_pairs("Specialties", specialties),
            summarize_pairs("Forms / related forms", siblings),
        ]
        body = " ".join(part for part in parts if part)
        entities.append(
            Entity(
                kind="pokemon",
                slug=item["slug"],
                name=item["name"],
                number=item.get("pokedex_number"),
                description=body,
                source_url=f"{SOURCE_BASE}/pokedex/{item['slug']}",
                props=item,
            )
        )
    return entities


def item_entities(page: str) -> list[Entity]:
    items = extract_array(loose_decode(page), "allItems")
    entities: list[Entity] = []
    for item in items:
        parts = [
            f"{item.get('name')} is an item in Pokemon Pokopia.",
            item.get("description"),
            summarize_pairs("Category", [item.get("menu_category")]),
            summarize_pairs("Sources", item.get("sources", [])),
            summarize_pairs("Tags", item.get("tags", [])),
            summarize_pairs("Sell value", [item.get("trade_sell_value")]),
            summarize_pairs("Mosslax effect", [item.get("mosslax")]),
        ]
        body = " ".join(part for part in parts if part)
        entities.append(
            Entity(
                kind="item",
                slug=item["slug"],
                name=item["name"],
                description=body,
                source_url=f"{SOURCE_BASE}/items/{item['slug']}",
                props=item,
            )
        )
    return entities


def habitat_entities(page: str) -> list[Entity]:
    habitats = extract_array(loose_decode(page), "allHabitats")
    entities: list[Entity] = []
    for habitat in habitats:
        pokemon = [p.get("name") for p in habitat.get("pokemon", [])]
        items = [
            f"{i.get('name')} x{i.get('quantity')}"
            for i in habitat.get("items", [])
            if i.get("name")
        ]
        parts = [
            f"{habitat.get('name')} is habitat/area #{habitat.get('number')} in Pokemon Pokopia.",
            summarize_pairs("Pokemon", pokemon),
            summarize_pairs("Required items", items),
            summarize_pairs("Biome", [habitat.get("biome") or habitat.get("zone")]),
        ]
        body = " ".join(part for part in parts if part)
        entities.append(
            Entity(
                kind="habitat",
                slug=habitat["slug"],
                name=habitat["name"],
                number=habitat.get("number"),
                description=body,
                source_url=f"{SOURCE_BASE}/habitats/{habitat['slug']}",
                props=habitat,
            )
        )
    return entities


def building_entities(page: str) -> list[Entity]:
    text = loose_decode(page)
    slugs = sorted(
        s
        for s in set(re.findall(r"/buildings/([a-z0-9-]+)", text))
        if s not in {"building", "buildings", "screenshots"}
    )
    entities: list[Entity] = []
    for slug in slugs:
        matches = [m.start() for m in re.finditer(re.escape(f"/buildings/{slug}"), text)]
        best_name = ""
        best_desc = ""
        for start in matches:
            snippet = text[start : start + 1800]
            name_match = (
                re.search(r'aria-label="([^"]+)"', snippet)
                or re.search(r'alt="([^"]+)"', snippet)
                or re.search(r'"card-name".*?"children":"([^"]+)"', snippet)
            )
            desc_match = (
                re.search(r'class="card-description"[^>]*>(.*?)</div>', snippet)
                or re.search(r'"card-description".*?"children":"([^"]+)"', snippet)
            )
            name = name_match.group(1) if name_match else ""
            desc = re.sub("<.*?>", "", desc_match.group(1)) if desc_match else ""
            if name and name.lower() not in {"pagination"}:
                best_name = name
            if desc:
                best_desc = desc
            if best_name and best_desc:
                break
        name = best_name or slug.replace("-", " ").title()
        body = f"{name} is a building in Pokemon Pokopia. {best_desc}".strip()
        entities.append(
            Entity(
                kind="building",
                slug=slug,
                name=name,
                description=body,
                source_url=f"{SOURCE_BASE}/buildings/{slug}",
                props={"slug": slug, "name": name, "description": best_desc},
            )
        )
    return entities


def get_rw_url() -> str:
    return subprocess.check_output(
        ["security", "find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"],
        text=True,
    ).strip()


def body_hash(body: str) -> str:
    return hashlib.sha256(body.encode()).hexdigest()


def chunk_keywords(entity: Entity) -> list[str]:
    keys = [entity.name, entity.slug, entity.kind, "Pokemon Pokopia", "PokopiaDex"]
    if entity.number:
        keys.append(entity.number)
    return keys


def rows_for_entity(entity: Entity, run_id: str, source_vid: str) -> dict[str, tuple[Any, ...]]:
    suffix = f"{entity.kind}-{entity.slug}"
    doc_vid = f"at://{OWNER_DID}/com.etzhayyim.apps.llm.domainKnowledge/pokemon-pokopia-{suffix}"
    chunk_vid = f"{doc_vid}/chunk/000"
    game_item_vid = f"did:etzhayyim:gameitem:pokemon-pokopia:{suffix}"
    edge_id = f"edge:etzhayyim:domain-knowledge-cites:{suffix}:pokopiadex"
    created = now_iso()
    created_date = today_iso()
    props = dict(entity.props)
    props.update(
        {
            "source_url": entity.source_url,
            "import_run_id": run_id,
            "import_agent_did": AGENT_DID,
            "provenance": {
                "vertex": [game_item_vid, doc_vid, chunk_vid],
                "edge": [edge_id],
                "mv": ["mv_domain_knowledge_search"],
                "idx": {
                    "document": doc_vid,
                    "chunk": chunk_vid,
                    "source": source_vid,
                    "kind": entity.kind,
                    "slug": entity.slug,
                },
            },
        }
    )
    return {
        "item": (
            game_item_vid,
            created_date,
            1,
            OWNER_DID,
            game_item_vid,
            None,
            entity.name,
            game_item_vid,
            entity.name,
            entity.name,
            entity.description,
            entity.kind,
            None,
            None,
            None,
            json.dumps(props, ensure_ascii=False),
            ACTOR_DID,
            OWNER_DID,
        ),
        "document": (
            doc_vid,
            created_date,
            1,
            OWNER_DID,
            AGENT_DID,
            DOMAIN,
            WORK_ID,
            GAME_SLUG,
            f"Pokemon Pokopia {entity.kind}: {entity.name}",
            "en",
            entity.description,
            body_hash(entity.description),
            entity.source_url,
            0.82,
            "active",
            created,
            created,
            OWNER_DID,
            None,
            AGENT_DID,
            json.dumps(props, ensure_ascii=False),
        ),
        "chunk": (
            chunk_vid,
            created_date,
            1,
            OWNER_DID,
            doc_vid,
            0,
            entity.description,
            chunk_keywords(entity),
            max(1, len(entity.description.split())),
            "en",
            None,
            None,
            None,
            None,
            created,
            OWNER_DID,
            None,
            AGENT_DID,
        ),
        "edge": (
            edge_id,
            doc_vid,
            source_vid,
            created_date,
            1,
            OWNER_DID,
            "source",
            0.82,
            created,
        ),
    }


def source_row(kind: str, url: str, run_id: str) -> tuple[Any, ...]:
    created = now_iso()
    created_date = today_iso()
    return (
        f"did:etzhayyim:source:pokemon-pokopia:pokopiadex:{kind}",
        created_date,
        1,
        OWNER_DID,
        url,
        f"PokopiaDex {kind}",
        "web_page",
        "PokopiaDex",
        0.82,
        created,
        created,
        OWNER_DID,
        None,
        AGENT_DID,
    )


def delete_existing(cur: psycopg.Cursor[Any], entities: list[Entity]) -> None:
    doc_ids = [
        f"at://{OWNER_DID}/com.etzhayyim.apps.llm.domainKnowledge/pokemon-pokopia-{e.kind}-{e.slug}"
        for e in entities
    ]
    chunk_ids = [f"{doc}/chunk/000" for doc in doc_ids]
    item_ids = [f"did:etzhayyim:gameitem:pokemon-pokopia:{e.kind}-{e.slug}" for e in entities]
    edge_ids = [
        f"edge:etzhayyim:domain-knowledge-cites:{e.kind}-{e.slug}:pokopiadex"
        for e in entities
    ]
    for table, column, ids in [
        ("edge_domain_knowledge_cites", "edge_id", edge_ids),
        ("vertex_domain_knowledge_chunk", "vertex_id", chunk_ids),
        ("vertex_domain_knowledge_document", "vertex_id", doc_ids),
        ("vertex_game_item", "vertex_id", item_ids),
    ]:
        for batch in batched(ids, 500):
            cur.execute(f"delete from {table} where {column} = any(%s)", (batch,))


def batched(values: list[Any], size: int) -> list[list[Any]]:
    return [values[i : i + size] for i in range(0, len(values), size)]


def executemany_batched(
    conn: psycopg.Connection[Any],
    cur: psycopg.Cursor[Any],
    sql: str,
    rows: list[tuple[Any, ...]],
    batch_size: int = 100,
) -> None:
    for batch in batched(rows, batch_size):
        cur.executemany(sql, batch)
        conn.commit()


def filter_missing(
    cur: psycopg.Cursor[Any],
    table: str,
    column: str,
    rows: list[tuple[Any, ...]],
    id_index: int = 0,
) -> list[tuple[Any, ...]]:
    ids = [row[id_index] for row in rows]
    existing: set[str] = set()
    for batch in batched(ids, 500):
        cur.execute(f"select {column} from {table} where {column} = any(%s)", (batch,))
        existing.update(row[0] for row in cur.fetchall())
    return [row for row in rows if row[id_index] not in existing]


def insert_all(
    conn: psycopg.Connection[Any],
    run_id: str,
    entities_by_kind: dict[str, list[Entity]],
    replace: bool,
) -> None:
    all_entities = [entity for values in entities_by_kind.values() for entity in values]
    with conn.cursor() as cur:
        if replace:
            cur.execute(
                "delete from vertex_agent_observation where agent_did = %s and source_ref like %s",
                (AGENT_DID, f"pokopiadex:{run_id}:%"),
            )
            cur.execute(
                "delete from vertex_agent_action_log where vertex_id = %s",
                (f"did:etzhayyim:agent-action:{run_id}",),
            )
            cur.execute(
                "delete from vertex_domain_knowledge_source where vertex_id like %s",
                ("did:etzhayyim:source:pokemon-pokopia:pokopiadex:%",),
            )
            delete_existing(cur, all_entities)

        sources = {
            "pokemon": source_row("pokemon", f"{SOURCE_BASE}/pokedex", run_id),
            "item": source_row("item", f"{SOURCE_BASE}/items", run_id),
            "habitat": source_row("habitat", f"{SOURCE_BASE}/habitats", run_id),
            "building": source_row("building", f"{SOURCE_BASE}/buildings", run_id),
        }
        source_rows = filter_missing(
            cur,
            "vertex_domain_knowledge_source",
            "vertex_id",
            list(sources.values()),
        )
        cur.executemany(
            """
            insert into vertex_domain_knowledge_source
            (vertex_id, created_date, sensitivity_ord, owner_did, url, title,
             source_kind, publisher, confidence, retrieved_at, created_at,
             org_id, user_id, actor_id)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            source_rows,
        )
        conn.commit()

        item_rows: list[tuple[Any, ...]] = []
        doc_rows: list[tuple[Any, ...]] = []
        chunk_rows: list[tuple[Any, ...]] = []
        edge_rows: list[tuple[Any, ...]] = []
        for kind, entities in entities_by_kind.items():
            source_vid = sources[kind][0]
            for entity in entities:
                rows = rows_for_entity(entity, run_id, source_vid)
                item_rows.append(rows["item"])
                doc_rows.append(rows["document"])
                chunk_rows.append(rows["chunk"])
                edge_rows.append(rows["edge"])

        item_rows = filter_missing(cur, "vertex_game_item", "vertex_id", item_rows)
        doc_rows = filter_missing(cur, "vertex_domain_knowledge_document", "vertex_id", doc_rows)
        chunk_rows = filter_missing(cur, "vertex_domain_knowledge_chunk", "vertex_id", chunk_rows)
        edge_rows = filter_missing(cur, "edge_domain_knowledge_cites", "edge_id", edge_rows)

        executemany_batched(
            conn,
            cur,
            """
            insert into vertex_game_item
            (vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo,
             label, did, name, display_name, description, item_type, rarity,
             level, effect, props, actor_did, org_did)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            item_rows,
        )
        executemany_batched(
            conn,
            cur,
            """
            insert into vertex_domain_knowledge_document
            (vertex_id, created_date, sensitivity_ord, owner_did, actor_did,
             domain, canonical_work_id, game_slug, title, lang, body, body_hash,
             source_record_uri, confidence, status, created_at, updated_at,
             org_id, user_id, actor_id, props)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            doc_rows,
        )
        executemany_batched(
            conn,
            cur,
            """
            insert into vertex_domain_knowledge_chunk
            (vertex_id, created_date, sensitivity_ord, owner_did, document_vid,
             chunk_index, chunk_text, keywords, token_count, lang, embedding,
             embedding_norm, embedding_model, embedded_at, created_at,
             org_id, user_id, actor_id)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            chunk_rows,
        )
        executemany_batched(
            conn,
            cur,
            """
            insert into edge_domain_knowledge_cites
            (edge_id, src_vid, dst_vid, created_date, sensitivity_ord,
             owner_did, relation_kind, confidence, created_at)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            edge_rows,
        )

        created = now_iso()
        created_date = today_iso()
        counts = {kind: len(entities) for kind, entities in entities_by_kind.items()}
        action_id = f"did:etzhayyim:agent-action:{run_id}"
        action_rows = filter_missing(
            cur,
            "vertex_agent_action_log",
            "vertex_id",
            [
                (
                    action_id,
                    created_date,
                    1,
                    OWNER_DID,
                    AGENT_DID,
                    "pokopia_kg_bulk_import",
                    "Imported Pokemon Pokopia Pokemon, items, habitats/areas, and buildings from PokopiaDex with provenance.",
                    "pokemon-pokopia",
                    json.dumps(
                        {
                            "sources": {kind: row[4] for kind, row in sources.items()},
                            "agent_session": run_id,
                            "tools": ["curl", "psycopg", "codex"],
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "counts": counts,
                            "vertex_tables": [
                                "vertex_game_item",
                                "vertex_domain_knowledge_document",
                                "vertex_domain_knowledge_chunk",
                                "vertex_domain_knowledge_source",
                            ],
                            "edge_tables": ["edge_domain_knowledge_cites"],
                            "mv": ["mv_domain_knowledge_search"],
                            "idx": ["entity slug", "document_vid", "chunk_vid", "source_vid"],
                        },
                        ensure_ascii=False,
                    ),
                    None,
                    "success",
                    created,
                    ACTOR_DID,
                    OWNER_DID,
                )
            ],
        )
        cur.executemany(
            """
            insert into vertex_agent_action_log
            (vertex_id, created_date, sensitivity_ord, owner_did, agent_did,
             action_type, description, target_entity, input_summary,
             output_summary, duration_ms, status, created_at, actor_did, org_did)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            action_rows,
        )
        observations = []
        for kind, entities in entities_by_kind.items():
            observations.append(
                (
                    f"did:etzhayyim:agent-observation:{run_id}:{kind}",
                    AGENT_DID,
                    "web_page",
                    f"pokopiadex:{run_id}:{kind}",
                    created,
                    json.dumps(
                        {
                            "source_url": sources[kind][4],
                            "count": len(entities),
                            "sample": [e.name for e in entities[:5]],
                            "agent_session": run_id,
                            "provenance_model": {
                                "veretx": "vertex_* rows store entity, document, chunk, source, action, observation",
                                "edge": "edge_domain_knowledge_cites links document to source",
                                "mv": "mv_domain_knowledge_search exposes chunks to chat retrieval",
                                "idx": "props.provenance.idx stores document/chunk/source IDs per entity",
                            },
                        },
                        ensure_ascii=False,
                    ),
                    0.82,
                    0.0,
                    1,
                    AGENT_DID,
                    OWNER_DID,
                    OWNER_DID,
                    None,
                )
            )
        observations = filter_missing(cur, "vertex_agent_observation", "vertex_id", observations)
        cur.executemany(
            """
            insert into vertex_agent_observation
            (vertex_id, agent_did, source_kind, source_ref, observed_at,
             payload_json, confidence, uncertainty, sensitivity_ord, actor_id,
             owner_did, org_id, user_id)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            observations,
        )
    conn.commit()


def load_or_fetch(cache_dir: Path, name: str, url: str, refresh: bool) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{name}.html"
    if refresh or not path.exists():
        path.write_text(fetch(url))
    return path.read_text(errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--run-id", default=f"codex-session-20260509-pokopiadex-bulk")
    parser.add_argument("--cache-dir", default="/tmp/pokopiadex-import")
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    pages = {
        "pokemon": load_or_fetch(cache_dir, "pokedex", f"{SOURCE_BASE}/pokedex", args.refresh),
        "item": load_or_fetch(cache_dir, "items", f"{SOURCE_BASE}/items", args.refresh),
        "habitat": load_or_fetch(cache_dir, "habitats", f"{SOURCE_BASE}/habitats", args.refresh),
        "building": load_or_fetch(cache_dir, "buildings", f"{SOURCE_BASE}/buildings", args.refresh),
    }
    entities_by_kind = {
        "pokemon": pokemon_entities(pages["pokemon"]),
        "item": item_entities(pages["item"]),
        "habitat": habitat_entities(pages["habitat"]),
        "building": building_entities(pages["building"]),
    }
    counts = {kind: len(entities) for kind, entities in entities_by_kind.items()}
    print(json.dumps({"run_id": args.run_id, "counts": counts}, ensure_ascii=False, indent=2))
    if args.dry_run:
        for kind, entities in entities_by_kind.items():
            print(kind, [entity.name for entity in entities[:3]])
        return 0

    with psycopg.connect(get_rw_url()) as conn:
        insert_all(conn, args.run_id, entities_by_kind, args.replace)
    print("import complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
