"""Tests for validate-id-filename-consistency.py (cycle 61).

Covers categorization + permissive matching invariants.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "validate-id-filename-consistency.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("validate_id_filename_consistency", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["validate_id_filename_consistency"] = m
    spec.loader.exec_module(m)
    return m


def test_script_exists():
    assert _SCRIPT.exists()


def test_categorize_uppercase_prefix(mod):
    assert mod.categorize_mismatch(
        "90-docs/adr/2605250630-foo.md", "ADR-2605250630"
    ) == "uppercase-ADR-prefix"


def test_categorize_pre_cutover_etzhayyimcojp(mod):
    assert mod.categorize_mismatch(
        "90-docs/adr/2604251215-etzhayyimcojp-agent-authority-bounds.md",
        "adr-2604251215-etzhayyim-agent-authority-bounds",
    ) == "pre-cutover-rename"


def test_categorize_pre_cutover_amanomibashira(mod):
    assert mod.categorize_mismatch(
        "90-docs/adr/2605102200-operating-entity-amanomibashira-rename.md",
        "adr-2605102200-operating-entity-etzhayyim-rename",
    ) == "pre-cutover-rename"


def test_categorize_short_id(mod):
    assert mod.categorize_mismatch(
        "90-docs/adr/0087-magatama-mcp-tool-facade.md", "adr-0042"
    ) == "short-id-missing-slug"


def test_categorize_engineering_policy(mod):
    assert mod.categorize_mismatch(
        "90-docs/engineering/repo-error-visibility-policy.md",
        "adr-0007-repo-error-visibility-policy",
    ) == "engineering-policy-old-style"


def test_categorize_other(mod):
    assert mod.categorize_mismatch(
        "90-docs/260405-actor-cypher-mcp-capability-architecture.md",
        "actor-cypher-mcp",
    ) == "other-rename-related"


def test_find_mismatches_clean(mod):
    """Matching basename + id → 0 mismatches."""
    entries = [
        {"id": "adr-2605262500-foo", "path": "90-docs/adr/2605262500-foo.md"},
        {"id": "2605262500", "path": "90-docs/adr/2605262500-bar.md"},  # timestamp-only
    ]
    result = mod.find_mismatches(entries)
    assert result["total"] == 0


def test_find_mismatches_basename_prefix_match(mod):
    """Permissive matching: id timestamp prefix matches basename."""
    entries = [
        {"id": "2605262500", "path": "90-docs/adr/2605262500-anything.md"},
        {"id": "adr-2605262500", "path": "90-docs/adr/2605262500-anything-else.md"},
    ]
    result = mod.find_mismatches(entries)
    # Both should be permissively accepted
    assert result["total"] == 0


def test_find_mismatches_genuine(mod):
    """Non-matching id is flagged."""
    entries = [
        {"id": "ADR-2605262500", "path": "90-docs/adr/2605262500-foo.md"},
    ]
    result = mod.find_mismatches(entries)
    assert result["total"] == 1
    assert "uppercase-ADR-prefix" in result["by_category"]


def test_default_mode_exits_0_with_baseline():
    """Default tracker mode exits 0 even when issues exist."""
    result = subprocess.run(
        ["python3", str(_SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_strict_mode_exits_1_with_baseline():
    """--strict exits 1 against live baseline (57 known mismatches)."""
    result = subprocess.run(
        ["python3", str(_SCRIPT), "--strict"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_json_output_schema():
    """--json output has total + by_category + categories."""
    result = subprocess.run(
        ["python3", str(_SCRIPT), "--json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    for k in ("total", "by_category", "categories"):
        assert k in payload
    assert isinstance(payload["by_category"], dict)
