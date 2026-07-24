"""Tests for validate-kotodama-manifests.py (cycle 56).

The validator checks every 60-apps/<app>/kotodama.jsonld against the
canonical kotodama.schema.json. Tests cover:
  - script exists + clean imports
  - graceful jsonschema fallback
  - --strict mode exit semantics
  - --json output structure
  - root-retained multirepo baseline (0/0 clean)
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "validate-kotodama-manifests.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(_SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_script_exists():
    assert _SCRIPT.exists()
    assert _SCRIPT.read_text().startswith("#!/usr/bin/env python3")


def test_imports_cleanly():
    spec = importlib.util.spec_from_file_location("validate_kotodama_manifests", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.main)


def test_canonical_paths():
    """Module exposes canonical glob + schema paths."""
    spec = importlib.util.spec_from_file_location("validate_kotodama_manifests", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "60-apps" in str(mod.APPS_GLOB)
    assert "kotodama.jsonld" in str(mod.APPS_GLOB)
    assert mod.SCHEMA.name == "kotodama.schema.json"


def test_no_traceback_on_default_run():
    """Default invocation does not crash regardless of jsonschema availability."""
    result = _run()
    assert "Traceback" not in result.stderr


def test_live_repo_root_retained_baseline_0_0_valid():
    """Extracted multirepo baseline: root retains 0/0 kotodama manifests."""
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        pytest.skip("jsonschema not installed; skipping live validation")

    result = _run("--strict", "--json")
    payload = json.loads(result.stdout)
    # Application manifests live in their independent repositories.
    assert payload["ok"] is True, f"baseline broken: {payload}"
    assert payload["total"] == 0
    assert payload["clean"] == 0
    assert payload["broken"] == 0
    assert payload["errors"] == {}


def test_json_output_schema():
    """--json output has documented top-level keys."""
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        pytest.skip("jsonschema not installed; skipping JSON schema test")

    result = _run("--strict", "--json")
    payload = json.loads(result.stdout)
    for k in ("ok", "total", "clean", "broken", "errors"):
        assert k in payload, f"missing key {k} in --json output"
    # Errors is per-app dict
    assert isinstance(payload["errors"], dict)


def test_strict_exits_2_on_missing_jsonschema():
    """If jsonschema is unavailable, --strict exits 2."""
    # Hide jsonschema by adding nonexistent path before site-packages.
    # On dev box where jsonschema IS installed via --break-system-packages,
    # this test would actually find jsonschema, so we skip if installed.
    try:
        import jsonschema  # noqa: F401
        pytest.skip("jsonschema is installed; cannot test missing-package path")
    except ImportError:
        result = _run("--strict")
        assert result.returncode == 2
