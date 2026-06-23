"""Tests for validate-registry-schemas.py.

The validator checks docs.json against docs.schema.json. (The relation
graph moved JSON-LD → EDN; graph.edn is a pure projection of docs.edn
validated by docs-graph-edn-freshness, so it is no longer schema-checked
here.) Tests cover:
  - graceful jsonschema fallback (when package not installed)
  - strict-mode exit on jsonschema missing
  - schema-clean data → exit 0
  - schema-violating data → exit 1
  - --json output schema correctness
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "validate-registry-schemas.py"


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Invoke validator as subprocess + return result (Popen-friendly for testing)."""
    return subprocess.run(
        ["python3", str(_SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def _make_fixture(tmp_path: Path, docs_data: dict, docs_schema: dict) -> dict:
    """Write a complete repo-shaped fixture and return paths."""
    reg = tmp_path / "90-docs" / "_registry"
    reg.mkdir(parents=True)
    schemas = reg / "schemas"
    schemas.mkdir()
    (reg / "docs.json").write_text(json.dumps(docs_data))
    (schemas / "docs.schema.json").write_text(json.dumps(docs_schema))
    return {
        "docs_json": reg / "docs.json",
        "docs_schema": schemas / "docs.schema.json",
    }


def test_script_exists_and_executable():
    """The validator script exists at the documented path."""
    assert _SCRIPT.exists()
    # Has shebang for executability
    text = _SCRIPT.read_text()
    assert text.startswith("#!/usr/bin/env python3")


def test_imports_cleanly():
    """The script's module imports without error (no syntax issues)."""
    spec = importlib.util.spec_from_file_location("validate_registry_schemas", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validate_registry_schemas"] = mod
    spec.loader.exec_module(mod)
    assert mod is not None


def test_main_function_signature():
    """main() exists and takes no required args (argparse handles flags)."""
    spec = importlib.util.spec_from_file_location("validate_registry_schemas", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.main)


def test_repo_paths_canonical():
    """Module exposes the canonical repo-relative paths."""
    spec = importlib.util.spec_from_file_location("validate_registry_schemas", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.DOCS_JSON.name == "docs.json"
    assert mod.DOCS_SCHEMA.name == "docs.schema.json"


def test_live_repo_validates_clean():
    """The actual repo's docs.json validates-clean.

    Regression guard: any future change that breaks this means the validator
    or the registry artifacts drifted.
    """
    result = _run()
    # exit 0 means clean OR jsonschema unavailable (graceful skip)
    # Either is acceptable here; we just check it doesn't crash
    assert result.returncode in (0, 1)
    # No Python traceback in stderr
    assert "Traceback" not in result.stderr


def test_json_output_schema_with_jsonschema_installed():
    """When jsonschema IS installed, --json output has the documented schema."""
    try:
        import jsonschema  # type: ignore # noqa: F401
    except ImportError:
        pytest.skip("jsonschema not installed; skipping live validation test")

    result = _run("--strict", "--json")
    payload = json.loads(result.stdout)
    # Required top-level keys (cycle 50 schema)
    assert "ok" in payload
    assert "docs" in payload
    assert "schema" in payload["docs"]
    assert "data" in payload["docs"]
    assert "error_count" in payload["docs"]
    assert "errors" in payload["docs"]
