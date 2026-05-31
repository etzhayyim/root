"""Tests for validate-relation-integrity.py (cycle 60).

Covers 4 relation-drift classes the schema validator does NOT catch:
  - dangling targets (related/supersedes/etc. point to non-existent id)
  - self-references (entry's related includes its own id)
  - circular related pairs (A↔B mutual)
  - --strict vs default tracker mode exit codes
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "validate-relation-integrity.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("validate_relation_integrity", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["validate_relation_integrity"] = m
    spec.loader.exec_module(m)
    return m


def test_script_exists():
    assert _SCRIPT.exists()
    assert _SCRIPT.read_text().startswith("#!/usr/bin/env python3")


def test_find_relation_issues_clean(mod):
    """Empty entries → 0 issues."""
    issues = mod.find_relation_issues([])
    assert issues["dangling_count"] == 0
    assert issues["self_reference_count"] == 0
    assert issues["circular_count"] == 0


def test_find_relation_issues_dangling(mod):
    """`related: [nonexistent]` flagged as dangling."""
    entries = [
        {"id": "a", "related": ["nonexistent-x"]},
        {"id": "b", "supersedes": ["nonexistent-y"]},
    ]
    issues = mod.find_relation_issues(entries)
    assert issues["dangling_count"] == 2
    assert len(issues["dangling"]["related"]) == 1
    assert len(issues["dangling"]["supersedes"]) == 1
    assert issues["dangling"]["related"][0] == {"src": "a", "target": "nonexistent-x"}


def test_find_relation_issues_resolved(mod):
    """`related: [existing-id]` is NOT dangling."""
    entries = [
        {"id": "a", "related": ["b"]},
        {"id": "b"},
    ]
    issues = mod.find_relation_issues(entries)
    assert issues["dangling_count"] == 0


def test_find_relation_issues_self_reference(mod):
    """`related: [own-id]` is flagged as self-reference."""
    entries = [{"id": "self-referer", "related": ["self-referer"]}]
    issues = mod.find_relation_issues(entries)
    assert issues["self_reference_count"] == 1
    assert issues["self_references"][0]["src"] == "self-referer"


def test_find_relation_issues_circular(mod):
    """A↔B mutual `related` is flagged as one circular pair."""
    entries = [
        {"id": "a", "related": ["b"]},
        {"id": "b", "related": ["a"]},
    ]
    issues = mod.find_relation_issues(entries)
    assert issues["circular_count"] == 1
    # Sorted to canonicalize order
    pair = issues["circular"][0]
    assert {pair["a"], pair["b"]} == {"a", "b"}


def test_find_relation_issues_depends_on(mod):
    """Cycle 64 added depends_on coverage. Dangling depends_on flagged."""
    entries = [
        {"id": "a", "depends_on": ["nonexistent-foundation"]},
        {"id": "b", "depends_on": ["a"]},  # resolves
    ]
    issues = mod.find_relation_issues(entries)
    # Dangling depends_on counted in total dangling
    assert "depends_on" in issues["dangling"]
    assert len(issues["dangling"]["depends_on"]) == 1
    assert issues["dangling"]["depends_on"][0] == {"src": "a", "target": "nonexistent-foundation"}
    # Resolved depends_on NOT flagged
    assert all(d["src"] != "b" for d in issues["dangling"]["depends_on"])


def test_find_relation_issues_depends_on_self_ref(mod):
    """depends_on self-reference flagged like other fields."""
    entries = [{"id": "self-dep", "depends_on": ["self-dep"]}]
    issues = mod.find_relation_issues(entries)
    assert issues["self_reference_count"] == 1
    assert issues["self_references"][0] == {"src": "self-dep", "field": "depends_on"}


def test_find_relation_issues_no_circular_flag(mod):
    """skip_circular=True suppresses circular detection."""
    entries = [
        {"id": "a", "related": ["b"]},
        {"id": "b", "related": ["a"]},
    ]
    issues = mod.find_relation_issues(entries, skip_circular=True)
    assert issues["circular_count"] == 0


def test_default_mode_exits_0_even_with_issues():
    """Default tracker mode exits 0 even when issues exist."""
    result = subprocess.run(
        ["python3", str(_SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_strict_mode_exits_1_with_baseline_issues():
    """--strict exits 1 because live repo has 1461 known issues (cycle 60 baseline)."""
    result = subprocess.run(
        ["python3", str(_SCRIPT), "--strict"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_json_output_schema():
    """--json output has documented top-level keys."""
    result = subprocess.run(
        ["python3", str(_SCRIPT), "--json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    for k in ("total_entries", "dangling_count", "dangling", "self_reference_count",
              "self_references", "circular_count", "circular"):
        assert k in payload
