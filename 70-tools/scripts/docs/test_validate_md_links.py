"""Tests for validate-md-links.py (cycle 67)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "validate-md-links.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("validate_md_links", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["validate_md_links"] = m
    spec.loader.exec_module(m)
    return m


def test_script_exists():
    assert _SCRIPT.exists()


def test_imports_cleanly(mod):
    assert callable(mod.find_broken_links)
    assert callable(mod.main)


def test_url_prefixes_skipped(mod):
    """URL_PREFIXES list covers expected schemes."""
    assert "http://" in mod.URL_PREFIXES
    assert "https://" in mod.URL_PREFIXES
    assert "mailto:" in mod.URL_PREFIXES


def test_link_regex_matches_basic(mod):
    """LINK_RE matches standard markdown links."""
    matches = list(mod.LINK_RE.finditer("See [doc](path.md) and [other](#anchor)"))
    assert len(matches) == 2
    assert matches[0].group(2) == "path.md"
    assert matches[1].group(2) == "#anchor"


def test_find_broken_links_returns_list(mod):
    """find_broken_links runs against live repo."""
    result = mod.find_broken_links()
    assert isinstance(result, list)
    # Each result has source/target/link_text
    if result:
        for b in result[:3]:
            assert "source" in b
            assert "target" in b
            assert "link_text" in b


def test_default_mode_exits_0_with_baseline():
    """Default tracker mode exits 0 even when broken links exist."""
    result = subprocess.run(
        ["python3", str(_SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_strict_mode_exits_1_with_baseline():
    """--strict exits 1 against live baseline (33 known broken)."""
    result = subprocess.run(
        ["python3", str(_SCRIPT), "--strict"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_json_output_schema():
    """--json output has total_broken + broken[] structure."""
    result = subprocess.run(
        ["python3", str(_SCRIPT), "--json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "total_broken" in payload
    assert "broken" in payload
    assert isinstance(payload["broken"], list)
    assert isinstance(payload["total_broken"], int)
