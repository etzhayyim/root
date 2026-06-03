#!/usr/bin/env python3
"""Backfill exact alias and token lookup rows for Pokemon Pokopia KG."""

from __future__ import annotations

import hashlib
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from typing import Any

import psycopg


OWNER_DID = "did:web:llm.etzhayyim.com"
GAME_SLUG = "pokemon-pokopia"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def stable_id(prefix: str, parts: list[object]) -> str:
    digest = hashlib.sha256("\x1f".join(str(p) for p in parts).encode()).hexdigest()[:24]
    return f"{prefix}:{digest}"


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[\s、。,.!?！？/・:：()（）「」『』\\[\\]{}]+", " ", text)
    text = re.sub(r"[^0-9a-zぁ-んァ-ン一-龥ーéÉ' -]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(value: object) -> list[str]:
    stop = {
        "pokemon", "pokopia", "pokemon-pokopia", "ポケモン", "ポコピア",
        "ぽこあ", "ココアポケモン", "in", "is", "the", "and",
    }
    out = []
    for token in normalize(value).replace("-", " ").split():
        if len(token) >= 2 and token not in stop:
            out.append(token)
    return list(dict.fromkeys(out))


def get_rw_url() -> str:
    return subprocess.check_output(
        ["security", "find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"],
        text=True,
    ).strip()


def insert_values_batched(
    cur: psycopg.Cursor[Any],
    table: str,
    columns: list[str],
    rows: list[tuple[Any, ...]],
    size: int = 200,
) -> None:
    if not rows:
        return
    width = len(columns)
    row_placeholders = "(" + ",".join(["%s"] * width) + ")"
    for i in range(0, len(rows), size):
        batch = rows[i : i + size]
        params = [value for row in batch for value in row]
        sql = (
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES "
            + ",".join([row_placeholders] * len(batch))
        )
        cur.execute(sql, params)
        cur.connection.commit()


def kind_from_vid(vertex_id: str) -> str:
    tail = vertex_id.rsplit(":", 1)[-1]
    return tail.split("-", 1)[0] if "-" in tail else "entity"


def build_aliases(row: dict[str, Any]) -> list[tuple[str, float, str]]:
    name = str(row.get("name") or "")
    display = str(row.get("display_name") or "")
    vertex_id = str(row.get("vertex_id") or "")
    slug = vertex_id.rsplit(":", 1)[-1]
    aliases: list[tuple[str, float, str]] = []
    for value, score, source in [
        (name, 1.0, "name"),
        (display, 0.98, "display_name"),
        (slug, 0.92, "slug"),
        (slug.split("-", 1)[-1], 0.9, "slug_without_kind"),
        (name.replace("Pokémon", "Pokemon"), 0.95, "ascii_name"),
    ]:
        if value and normalize(value):
            aliases.append((value, score, source))
    lower = name.casefold()
    if "lapras" in lower or "ラプラス" in name:
        aliases.extend([
            ("ラプラス", 1.0, "ja_manual"),
            ("Lapras", 1.0, "en_manual"),
        ])
    if "rawst berry" in lower or "チーゴ" in name or "rawst-berry" in slug:
        aliases.extend([
            ("チーゴ", 1.0, "ja_manual"),
            ("チーゴのみ", 1.0, "ja_manual"),
            ("チーゴの実", 1.0, "ja_manual"),
            ("Rawst Berry", 1.0, "en_manual"),
            ("rawst berry", 1.0, "en_manual"),
        ])
    dedup: dict[str, tuple[str, float, str]] = {}
    for alias, score, source in aliases:
        key = normalize(alias)
        if key and (key not in dedup or score > dedup[key][1]):
            dedup[key] = (alias, score, source)
    return list(dedup.values())


def main() -> int:
    with psycopg.connect(get_rw_url()) as conn:
        with conn.cursor() as cur:
            for path in [
                "30-graph/graph-schema/sql_migrations/20260509550000_domain_knowledge_alias_lookup.up.sql",
            ]:
                cur.execute(open(path, encoding="utf-8").read())
            conn.commit()

            cur.execute(
                """
                SELECT vertex_id, name, display_name, item_type
                FROM vertex_game_item
                WHERE vertex_id LIKE 'did:etzhayyim:gameitem:pokemon-pokopia:%'
                """
            )
            cols = [d[0] for d in cur.description]
            entities = [dict(zip(cols, r)) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT vertex_id, document_vid
                FROM vertex_domain_knowledge_chunk
                WHERE document_vid LIKE 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/pokemon-pokopia-%'
                """
            )
            chunk_by_doc = {str(doc): str(chunk) for chunk, doc in cur.fetchall()}

            alias_rows = []
            edge_rows = []
            token_rows = []
            created = now_iso()
            created_date = today_iso()
            for entity in entities:
                entity_vid = str(entity["vertex_id"])
                kind = str(entity.get("item_type") or kind_from_vid(entity_vid))
                slug_tail = entity_vid.rsplit(":", 1)[-1]
                if slug_tail.startswith(("pokemon-", "item-", "habitat-", "building-")):
                    doc_suffix = slug_tail
                elif slug_tail == "chigo-berry":
                    doc_vid = f"at://{OWNER_DID}/com.etzhayyim.apps.llm.domainKnowledge/pokemon-pokopia-chigo-berry"
                    chunk_vid = chunk_by_doc.get(doc_vid, f"{doc_vid}/chunk-1")
                    doc_suffix = ""
                else:
                    doc_suffix = f"{kind}-{slug_tail}"
                if doc_suffix:
                    doc_vid = f"at://{OWNER_DID}/com.etzhayyim.apps.llm.domainKnowledge/pokemon-pokopia-{doc_suffix}"
                    chunk_vid = chunk_by_doc.get(doc_vid, f"{doc_vid}/chunk/000")
                for alias, score, source in build_aliases(entity):
                    norm = normalize(alias)
                    alias_vid = stable_id("did:etzhayyim:domain-knowledge-alias", [GAME_SLUG, entity_vid, norm])
                    alias_rows.append((
                        alias_vid, created_date, 1, OWNER_DID, GAME_SLUG, kind,
                        entity_vid, doc_vid, chunk_vid, alias, norm, source, score, created,
                    ))
                    edge_rows.append((
                        stable_id("edge:etzhayyim:domain-knowledge-alias-of", [alias_vid, doc_vid]),
                        alias_vid, doc_vid, created_date, 1, OWNER_DID, "alias_of", score, created,
                    ))
                    for token in tokens(alias):
                        token_rows.append((
                            stable_id("did:etzhayyim:domain-knowledge-token", [GAME_SLUG, entity_vid, norm, token]),
                            created_date, 1, OWNER_DID, GAME_SLUG, kind, entity_vid,
                            doc_vid, chunk_vid, token, source, score, created,
                        ))

            for table in [
                "edge_domain_knowledge_alias_of",
                "vertex_domain_knowledge_token_index",
                "vertex_domain_knowledge_alias",
            ]:
                cur.execute(f"DELETE FROM {table} WHERE game_slug = %s" if table != "edge_domain_knowledge_alias_of" else "DELETE FROM edge_domain_knowledge_alias_of WHERE edge_id LIKE %s",
                            (GAME_SLUG,) if table != "edge_domain_knowledge_alias_of" else ("edge:etzhayyim:domain-knowledge-alias-of:%",))
            conn.commit()

            insert_values_batched(
                cur,
                "vertex_domain_knowledge_alias",
                [
                    "vertex_id", "created_date", "sensitivity_ord", "owner_did",
                    "game_slug", "entity_kind", "entity_vid", "document_vid",
                    "chunk_vid", "alias", "normalized_alias", "source", "score",
                    "created_at",
                ],
                alias_rows,
            )
            insert_values_batched(
                cur,
                "edge_domain_knowledge_alias_of",
                [
                    "edge_id", "src_vid", "dst_vid", "created_date",
                    "sensitivity_ord", "owner_did", "relation_kind",
                    "confidence", "created_at",
                ],
                edge_rows,
            )
            insert_values_batched(
                cur,
                "vertex_domain_knowledge_token_index",
                [
                    "vertex_id", "created_date", "sensitivity_ord", "owner_did",
                    "game_slug", "entity_kind", "entity_vid", "document_vid",
                    "chunk_vid", "token", "token_kind", "score", "created_at",
                ],
                token_rows,
            )
        conn.commit()
    print({"entities": len(entities), "aliases": len(alias_rows), "tokens": len(token_rows), "edges": len(edge_rows)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
