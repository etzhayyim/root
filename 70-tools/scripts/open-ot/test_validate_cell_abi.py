"""Tests for `validate-cell-abi.py`.

Run from this directory:
    python3 -m pytest test_validate_cell_abi.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

THIS_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = THIS_DIR / "validate-cell-abi.py"

# Import the validator module despite the hyphen in its filename.
spec = importlib.util.spec_from_file_location("validate_cell_abi", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


# ---------------------------------------------------------------------------
# Smoke: real repo content passes
# ---------------------------------------------------------------------------


def test_real_repo_content_passes():
    rc = validator.main(["--quiet"])
    assert rc == 0


# ---------------------------------------------------------------------------
# Lexicon checks — synthetic broken files
# ---------------------------------------------------------------------------


def _write_lex(tmp: Path, name: str, body: dict) -> Path:
    p = tmp / f"{name}.json"
    p.write_text(json.dumps(body))
    return p


def test_lexicon_id_mismatch(tmp_path):
    _write_lex(tmp_path, "defineCell", {"id": "wrong.nsid", "lexicon": 1, "defs": {}})
    errs = validator.check_lexicon(tmp_path / "defineCell.json")
    assert any("id=" in e for e in errs)


def test_lexicon_type_number_forbidden(tmp_path):
    _write_lex(
        tmp_path,
        "defineCell",
        {
            "id": "com.etzhayyim.apps.openOt.defineCell",
            "lexicon": 1,
            "defs": {
                "main": {
                    "type": "procedure",
                    "input": {
                        "encoding": "application/json",
                        "schema": {
                            "type": "object",
                            "properties": {"capacityKw": {"type": "number"}},
                        },
                    },
                }
            },
        },
    )
    errs = validator.check_lexicon(tmp_path / "defineCell.json")
    assert any("type: \"number\"" in e for e in errs)


def test_lexicon_inline_object_array_forbidden(tmp_path):
    _write_lex(
        tmp_path,
        "defineCell",
        {
            "id": "com.etzhayyim.apps.openOt.defineCell",
            "lexicon": 1,
            "defs": {
                "main": {
                    "type": "procedure",
                    "input": {
                        "encoding": "application/json",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "samples": {
                                    "type": "array",
                                    "items": {"type": "object", "properties": {}},
                                }
                            },
                        },
                    },
                }
            },
        },
    )
    errs = validator.check_lexicon(tmp_path / "defineCell.json")
    assert any("items must use ref" in e or "array-of-inline-object" in e for e in errs)


def test_lexicon_invalid_json(tmp_path):
    p = tmp_path / "defineCell.json"
    p.write_text("{ not valid json")
    errs = validator.check_lexicon(p)
    assert any("invalid JSON" in e for e in errs)


# ---------------------------------------------------------------------------
# Manifest checks
# ---------------------------------------------------------------------------


def _write_manifest(tmp: Path, cell_dir: str, body: dict) -> Path:
    cdir = tmp / cell_dir
    cdir.mkdir(parents=True, exist_ok=True)
    p = cdir / "manifest.json"
    p.write_text(json.dumps(body))
    return p


def _valid_manifest_body() -> dict:
    return {
        "iec61499_fbtype": "TEST_FB",
        "abi": {"init_export": "test_init", "tick_export": "test_tick"},
        "tick_max_emitted": 1,
        "ecc": {"states": ["Idle", "Running"], "initial": "Idle"},
        "data_in_schema": [
            {"name": "x", "rust_type": "i32", "wire": "valueMicroUnit"}
        ],
        "data_out_schema": [
            {"name": "y", "rust_type": "i32", "wire": "valueMicroUnit"}
        ],
    }


def test_manifest_passes_when_well_formed(tmp_path):
    p = _write_manifest(tmp_path, "test-cell", _valid_manifest_body())
    assert validator.check_manifest(p) == []


def test_manifest_missing_required_keys(tmp_path):
    body = _valid_manifest_body()
    del body["iec61499_fbtype"]
    p = _write_manifest(tmp_path, "test-cell", body)
    errs = validator.check_manifest(p)
    assert any("missing keys" in e and "iec61499_fbtype" in e for e in errs)


def test_manifest_ecc_initial_not_in_states(tmp_path):
    body = _valid_manifest_body()
    body["ecc"]["initial"] = "NotARealState"
    p = _write_manifest(tmp_path, "test-cell", body)
    errs = validator.check_manifest(p)
    assert any("ecc.initial" in e for e in errs)


def test_manifest_unknown_wire_type(tmp_path):
    body = _valid_manifest_body()
    body["data_in_schema"][0]["wire"] = "valueRandomGarbage"
    p = _write_manifest(tmp_path, "test-cell", body)
    errs = validator.check_manifest(p)
    assert any("unknown wire" in e for e in errs)


def test_manifest_tick_max_emitted_must_be_int(tmp_path):
    body = _valid_manifest_body()
    body["tick_max_emitted"] = "many"
    p = _write_manifest(tmp_path, "test-cell", body)
    errs = validator.check_manifest(p)
    assert any("tick_max_emitted" in e for e in errs)


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------


def test_main_returns_nonzero_on_synthetic_broken_lexicon(tmp_path):
    bad_lex_dir = tmp_path / "lex"
    bad_lex_dir.mkdir()
    bad_cells_dir = tmp_path / "cells"
    bad_cells_dir.mkdir()
    _write_lex(bad_lex_dir, "defineCell", {"id": "wrong"})  # id mismatch
    rc = validator.main(
        ["--lexicon-dir", str(bad_lex_dir), "--cells-dir", str(bad_cells_dir), "--quiet"]
    )
    assert rc == 1


def test_main_returns_zero_on_empty_dirs(tmp_path):
    (tmp_path / "lex").mkdir()
    (tmp_path / "cells").mkdir()
    rc = validator.main(
        [
            "--lexicon-dir",
            str(tmp_path / "lex"),
            "--cells-dir",
            str(tmp_path / "cells"),
            "--quiet",
        ]
    )
    assert rc == 0
