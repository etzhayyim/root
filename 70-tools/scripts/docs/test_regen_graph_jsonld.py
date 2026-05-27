"""Tests for regen-graph-jsonld.py (cycle 56).

The generator projects 90-docs/_registry/docs.json → graph.jsonld
with typed JSON-LD predicates. Tests cover:
  - happy path (1-entry minimal projection)
  - empty docs.json (no entries → empty @graph)
  - relation predicate mapping (related/supersedes/etc.)
  - schema.org type mapping (adr → TechArticle / explanation → Article)
  - doc: IRI prefixing on relations
  - @context preserved across regen
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "regen-graph-jsonld.py"


@pytest.fixture(scope="module")
def gen():
    spec = importlib.util.spec_from_file_location("regen_graph_jsonld", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["regen_graph_jsonld"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_doc_iri_helper(gen):
    """_doc_iri prefixes an entry id with 'doc:'."""
    assert gen._doc_iri("adr-2605262500") == "doc:adr-2605262500"


def test_project_entry_minimal(gen):
    """An entry with only required keys produces minimal JSON-LD node."""
    entry = {
        "id": "test-1",
        "path": "90-docs/foo.md",
        "title": "Test 1",
        "status": "active",
        "doc_type": "explanation",
        "topic": "test",
        "authoritative": False,
    }
    node = gen._project_entry(entry)
    assert node is not None
    assert node["id"] == "doc:test-1"
    assert node["type"] == "Article"  # explanation → Article
    assert node["title"] == "Test 1"
    assert node["status"] == "active"
    assert node["topic"] == "test"
    assert node["authoritative"] is False


def test_project_entry_with_relations(gen):
    """Relation fields are mapped to camelCase + doc: IRI prefix."""
    entry = {
        "id": "test-2",
        "path": "90-docs/bar.md",
        "title": "Test 2",
        "status": "active",
        "doc_type": "adr",
        "topic": "rel-test",
        "authoritative": True,
        "related": ["test-1", "test-3"],
        "supersedes": ["old-1"],
        "superseded_by": ["new-1"],
        "amends": ["amend-1"],
        "amended_by": ["amender-1"],
    }
    node = gen._project_entry(entry)
    assert node is not None
    assert node["type"] == "TechArticle"  # adr → TechArticle
    assert node["related"] == ["doc:test-1", "doc:test-3"]
    # Single-element relations collapse to string per generator convention
    assert node["supersedes"] == "doc:old-1"
    assert node["supersededBy"] == "doc:new-1"
    assert node["amends"] == "doc:amend-1"
    assert node["amendedBy"] == "doc:amender-1"


def test_project_entry_no_id_returns_none(gen):
    """An entry without an id is defensive-skipped (returns None)."""
    entry = {"path": "90-docs/no-id.md", "title": "headless"}
    assert gen._project_entry(entry) is None


def test_doc_type_to_schema_default(gen):
    """Unknown doc_type defaults to TechArticle."""
    entry = {
        "id": "test-unknown-type",
        "path": "90-docs/foo.md",
        "title": "Test",
        "status": "active",
        "doc_type": "snapshot",  # not in DOC_TYPE_TO_SCHEMA
        "topic": "test",
        "authoritative": True,
    }
    node = gen._project_entry(entry)
    assert node["type"] == "TechArticle"


def test_build_graph_with_temp_docs_json(gen, tmp_path, monkeypatch):
    """build_graph reads docs.json from disk + produces sorted @graph."""
    # Write a minimal docs.json to a temp location
    docs = {
        "version": 2,
        "updated_at": "2026-05-27",
        "entries": [
            {
                "id": "z-last",
                "path": "90-docs/z.md",
                "title": "Z",
                "status": "active",
                "doc_type": "adr",
                "topic": "z",
                "authoritative": True,
            },
            {
                "id": "a-first",
                "path": "90-docs/a.md",
                "title": "A",
                "status": "active",
                "doc_type": "explanation",
                "topic": "a",
                "authoritative": False,
            },
        ],
    }
    fake_docs_json = tmp_path / "docs.json"
    fake_docs_json.write_text(json.dumps(docs))
    monkeypatch.setattr(gen, "DOCS_JSON", fake_docs_json)

    result = gen.build_graph()
    assert "@context" in result
    assert "@graph" in result
    nodes = result["@graph"]
    assert len(nodes) == 2
    # Sorted by id → a-first comes before z-last
    assert nodes[0]["id"] == "doc:a-first"
    assert nodes[1]["id"] == "doc:z-last"


def test_build_graph_empty_docs_json(gen, tmp_path, monkeypatch):
    """Empty docs.json produces an empty @graph (not an error)."""
    fake_docs_json = tmp_path / "docs.json"
    fake_docs_json.write_text(
        json.dumps({"version": 2, "updated_at": "2026-05-27", "entries": []})
    )
    monkeypatch.setattr(gen, "DOCS_JSON", fake_docs_json)

    result = gen.build_graph()
    assert result["@graph"] == []
    assert "@context" in result


def test_context_preserved(gen):
    """The @context constant carries the expected JSON-LD predicates."""
    ctx = gen.CONTEXT
    assert ctx["id"] == "@id"
    assert ctx["type"] == "@type"
    # Relation predicates
    assert ctx["related"]["@type"] == "@id"
    assert ctx["supersedes"]["@type"] == "@id"
    assert ctx["supersededBy"]["@type"] == "@id"
    assert ctx["amends"]["@type"] == "@id"
    assert ctx["amendedBy"]["@type"] == "@id"
