"""Tests for regen-registry.py (cycle 57).

The generator walks 90-docs/**/*.md, parses YAML-ish front-matter,
and emits 90-docs/_registry/docs.json. Tests cover:
  - parse_frontmatter happy path (flat keys + list values)
  - parse_frontmatter edge cases (empty list, quoted strings, bools)
  - parse_frontmatter rejects non-front-matter input
  - build_registry shape (version + updated_at + entries)
  - live-repo regression guard (cycle 48 baseline: in sync 659 entries)
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "regen-registry.py"


@pytest.fixture(scope="module")
def gen():
    spec = importlib.util.spec_from_file_location("regen_registry", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["regen_registry"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_script_exists():
    assert _SCRIPT.exists()


def test_imports_cleanly(gen):
    assert callable(gen.parse_frontmatter)
    assert callable(gen.scan_docs)
    assert callable(gen.build_registry)
    assert callable(gen.main)


def test_parse_frontmatter_minimal(gen):
    """Flat scalars + bool + quoted string parse correctly."""
    text = """---
id: test-1
title: "Test Doc"
status: active
doc_type: adr
topic: test
authoritative: true
last_verified: 2026-05-27
---
body"""
    out = gen.parse_frontmatter(text)
    assert out is not None
    assert out["id"] == "test-1"
    assert out["title"] == "Test Doc"
    assert out["status"] == "active"
    assert out["doc_type"] == "adr"
    assert out["topic"] == "test"
    assert out["authoritative"] is True
    assert out["last_verified"] == "2026-05-27"


def test_parse_frontmatter_lists(gen):
    """YAML list-of-strings parses to Python list."""
    text = """---
id: test-list
title: T
related:
  - foo-1
  - foo-2
authoritative_for:
  - thing-a
  - thing-b
supersedes: []
---"""
    out = gen.parse_frontmatter(text)
    assert out["related"] == ["foo-1", "foo-2"]
    assert out["authoritative_for"] == ["thing-a", "thing-b"]
    assert out["supersedes"] == []


def test_parse_frontmatter_no_yaml_returns_none(gen):
    """Text without leading `---` returns None."""
    assert gen.parse_frontmatter("just body text\nno frontmatter") is None
    assert gen.parse_frontmatter("") is None


def test_parse_frontmatter_unterminated_returns_none(gen):
    """Front-matter that starts with `---` but never closes returns None."""
    text = "---\nid: test\ntitle: never closed"
    assert gen.parse_frontmatter(text) is None


def test_parse_frontmatter_bool_false(gen):
    """`authoritative: false` parses as Python False (not string)."""
    text = """---
id: t
authoritative: false
---"""
    out = gen.parse_frontmatter(text)
    assert out["authoritative"] is False


def test_build_registry_shape(gen):
    """build_registry returns version 2 + updated_at + entries fields."""
    entries = [{"id": "a", "path": "90-docs/a.md", "title": "A"}]
    reg = gen.build_registry(entries)
    assert reg["version"] == 2
    assert "updated_at" in reg
    assert reg["entries"] == entries
    # updated_at is ISO date
    assert len(reg["updated_at"]) == 10  # YYYY-MM-DD


def test_live_repo_in_sync():
    """Live repo registry is in sync per cycle 55 baseline. Regression guard."""
    result = subprocess.run(
        ["python3", str(_SCRIPT), "--check"],
        capture_output=True,
        text=True,
    )
    # exit 0 = in sync; exit 1 = drift
    assert result.returncode == 0, f"registry drift detected: {result.stdout} {result.stderr}"
    assert "in sync" in result.stdout


def test_json_mode_emits_valid_json(gen):
    """`--json` mode produces parseable JSON output."""
    result = subprocess.run(
        ["python3", str(_SCRIPT), "--json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    # Has documented top-level shape
    assert payload["version"] == 2
    assert "updated_at" in payload
    assert "entries" in payload
    assert isinstance(payload["entries"], list)
    # Cycle 55 baseline: 659 entries
    assert len(payload["entries"]) >= 600  # broad lower bound


# ── EDN sidecar (babashka / Clojure consumers) ─────────────────────────────

def test_edn_encoder_primitives(gen):
    """EDN scalar/keyword/collection encoding is correct + injection-safe."""
    assert gen._edn_keyword("doc_type") == ":doc-type"
    assert gen._edn_keyword("authoritative_for") == ":authoritative-for"
    assert gen._edn_value(True) == "true"
    assert gen._edn_value(False) == "false"
    assert gen._edn_value(2) == "2"
    assert gen._edn_value(None) == "nil"
    assert gen._edn_value([]) == "[]"
    assert gen._edn_value(["a", "b"]) == '["a" "b"]'
    # strings: quotes/backslashes/newlines are escaped (no EDN injection)
    assert gen._edn_value('he said "hi"') == '"he said \\"hi\\""'
    assert gen._edn_value("a\\b") == '"a\\\\b"'
    assert gen._edn_value("line1\nline2") == '"line1\\nline2"'
    # nested map uses kebab keyword keys
    assert gen._edn_value({"a_b": 1}) == "{:a-b 1}"


def test_render_edn_shape(gen):
    """render_edn emits a top-level map with kebab keyword keys, one entry per line."""
    reg = gen.build_registry([
        {"path": "90-docs/a.md", "id": "a", "title": 'A "x"', "doc_type": "adr",
         "authoritative": True, "authoritative_for": ["x"]},
    ])
    out = gen.render_edn(reg)
    assert out.startswith("{:version 2\n :updated-at ")
    assert " :entries\n [{" in out
    assert ":doc-type \"adr\"" in out
    assert ":doc_type" not in out          # snake_case never leaks into EDN
    assert out.endswith("]}\n")


def test_edn_mode_emits_parseable_edn(gen):
    """`--edn` mode produces the same shape and round-trips via Python's reader-ish checks."""
    result = subprocess.run(
        ["python3", str(_SCRIPT), "--edn"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = result.stdout
    assert out.startswith("{:version 2\n :updated-at ")
    assert " :entries\n [" in out
    assert ":doc_type" not in out          # all keys kebab-cased
    # balanced delimiters (cheap structural sanity)
    assert out.count("{") == out.count("}")
    assert out.count("[") == out.count("]")
