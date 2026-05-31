#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Regenerate `90-docs/_registry/graph.jsonld` from `90-docs/_registry/docs.json`.

`docs.json` is the canonical machine sidecar (generated from .md
front-matter by `regen-registry.py`). `graph.jsonld` is the JSON-LD
relation-graph projection of the same data with typed predicates
(schema.org / dc:terms / etzhayyim ontology) suitable for SPARQL +
linked-data consumers.

Per 90-docs/CLAUDE.md "Documentation System Rules":
  - Markdown 本文が canonical source
  - docs.json is the normalized JSON sidecar
  - graph.jsonld is the typed relation graph (this file generates it)

Chain: .md → docs.json → graph.jsonld (single source of truth flows
left-to-right; both sidecars regen idempotently from canonical source).

Idempotent. Sorted by id. The @context preserves the existing
ontology mapping; only the @graph array is regenerated.

Usage:
    70-tools/scripts/docs/regen-graph-jsonld.py
    70-tools/scripts/docs/regen-graph-jsonld.py --check   # exit 1 on drift
    70-tools/scripts/docs/regen-graph-jsonld.py --json    # plan-only stdout
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DOCS_JSON = REPO / "90-docs" / "_registry" / "docs.json"
GRAPH_JSONLD = REPO / "90-docs" / "_registry" / "graph.jsonld"

# JSON-LD @context preserved verbatim from the existing graph.jsonld so
# downstream consumers' SPARQL queries / IRI mappings stay stable.
CONTEXT = {
    "id": "@id",
    "type": "@type",
    "title": "http://purl.org/dc/terms/title",
    "status": "https://schema.org/creativeWorkStatus",
    "topic": "https://schema.org/about",
    "authoritative": "https://schema.org/authoritativeLegalValue",
    "authoritativeFor": "https://etzhayyim.com/docs/authoritativeFor",
    "related": {
        "@id": "https://schema.org/isRelatedTo",
        "@type": "@id",
    },
    "supersedes": {
        "@id": "https://schema.org/supersedes",
        "@type": "@id",
    },
    "supersededBy": {
        "@id": "https://schema.org/supersededBy",
        "@type": "@id",
    },
    "amends": {
        "@id": "https://etzhayyim.com/docs/amends",
        "@type": "@id",
    },
    "amendedBy": {
        "@id": "https://etzhayyim.com/docs/amendedBy",
        "@type": "@id",
    },
    "lastVerified": "https://schema.org/dateModified",
}

# Map docs.json doc_type values to schema.org types. Default = TechArticle.
DOC_TYPE_TO_SCHEMA = {
    "adr": "TechArticle",
    "explanation": "Article",
    "reference": "TechArticle",
    "how-to": "TechArticle",
    "tutorial": "Article",
}


def _doc_iri(entry_id: str) -> str:
    """Map a doc id to its IRI (id used as @id in the graph)."""
    return f"doc:{entry_id}"


def _project_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Convert one docs.json entry to a JSON-LD @graph node.

    Returns None for entries without an id (defensive — every md doc
    should have an id; surfaces a generator-side anomaly).
    """
    entry_id = entry.get("id")
    if not entry_id:
        return None

    node: dict[str, Any] = {
        "id": _doc_iri(entry_id),
        "type": DOC_TYPE_TO_SCHEMA.get(entry.get("doc_type", ""), "TechArticle"),
    }
    title = entry.get("title")
    if title:
        node["title"] = title
    status = entry.get("status")
    if status:
        node["status"] = status
    topic = entry.get("topic")
    if topic:
        node["topic"] = topic
    if entry.get("authoritative") is not None:
        node["authoritative"] = bool(entry["authoritative"])
    auth_for = entry.get("authoritative_for") or []
    if auth_for:
        node["authoritativeFor"] = list(auth_for)

    # Typed relations — emit only if target list is non-empty. Each
    # target is mapped through _doc_iri so JSON-LD consumers can resolve
    # the reference within the @graph.
    for src_key, ld_key in (
        ("related", "related"),
        ("supersedes", "supersedes"),
        ("superseded_by", "supersededBy"),
        ("amends", "amends"),
        ("amended_by", "amendedBy"),
    ):
        targets = entry.get(src_key) or []
        if not targets:
            continue
        iris = [_doc_iri(t) for t in targets if t]
        if not iris:
            continue
        # Single target → string; multiple → list (consistent with
        # existing graph.jsonld style)
        node[ld_key] = iris[0] if len(iris) == 1 else iris

    last_verified = entry.get("last_verified")
    if last_verified:
        node["lastVerified"] = last_verified

    return node


def build_graph() -> dict[str, Any]:
    """Read docs.json, project every entry, return the full JSON-LD doc."""
    if not DOCS_JSON.exists():
        print(
            f"regen-graph-jsonld: source not found at {DOCS_JSON.relative_to(REPO)}; "
            "run regen-registry.py first",
            file=sys.stderr,
        )
        sys.exit(2)

    docs = json.loads(DOCS_JSON.read_text(encoding="utf-8"))
    entries = docs.get("entries", [])

    nodes = [_project_entry(e) for e in entries]
    nodes = [n for n in nodes if n is not None]
    nodes.sort(key=lambda n: n["id"])

    return {
        "@context": CONTEXT,
        "@graph": nodes,
    }


def load_existing_graph() -> dict[str, Any] | None:
    if not GRAPH_JSONLD.exists():
        return None
    try:
        return json.loads(GRAPH_JSONLD.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if on-disk graph.jsonld differs from what we'd regenerate",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="emit the planned graph as JSON-LD (stdout) instead of writing",
    )
    args = ap.parse_args()

    new_graph = build_graph()

    if args.json:
        print(json.dumps(new_graph, indent=2, ensure_ascii=False))
        return 0

    if args.check:
        old = load_existing_graph() or {}
        old_graph = old.get("@graph", [])
        new_graph_nodes = new_graph["@graph"]
        if json.dumps(old_graph, sort_keys=True, ensure_ascii=False) != json.dumps(
            new_graph_nodes, sort_keys=True, ensure_ascii=False
        ):
            print(
                f"graph.jsonld drift detected: disk={len(new_graph_nodes)} nodes, "
                f"file={len(old_graph)} nodes",
                file=sys.stderr,
            )
            print("run: 70-tools/scripts/docs/regen-graph-jsonld.py", file=sys.stderr)
            return 1
        print(f"graph.jsonld in sync ({len(new_graph_nodes)} nodes)")
        return 0

    # write
    GRAPH_JSONLD.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_JSONLD.write_text(
        json.dumps(new_graph, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {GRAPH_JSONLD.relative_to(REPO)} with {len(new_graph['@graph'])} nodes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
