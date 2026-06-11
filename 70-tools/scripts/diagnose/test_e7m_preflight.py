"""Tests for the unified e7m_preflight operator CLI."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "e7m_preflight.py"


@pytest.fixture(scope="module")
def preflight_mod():
    spec = importlib.util.spec_from_file_location("e7m_preflight", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["e7m_preflight"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_run_preflight_returns_4_results(preflight_mod):
    """The preflight always runs exactly 4 checks; some may fail in this env."""
    report = preflight_mod.run_preflight(skip_pds_network=True)
    assert report["n_checks"] == 4
    assert len(report["results"]) == 4
    labels = {r["label"] for r in report["results"]}
    assert "vision_pii_diagnose" in labels
    assert "pds_diagnose" in labels
    assert "assemble_diagnose" in labels
    assert any("verify_deps_toml_paths" in label for label in labels)


def test_run_preflight_pds_check_passes_with_skip_network(preflight_mod):
    """--skip-pds-network avoids the HEAD reachability probe."""
    report = preflight_mod.run_preflight(skip_pds_network=True)
    pds_check = next(r for r in report["results"] if r["label"] == "pds_diagnose")
    assert pds_check["passed"] is True


def test_run_preflight_assemble_check_passes(preflight_mod):
    """assemble_diagnose check has no env deps → always passes in clean env."""
    report = preflight_mod.run_preflight(skip_pds_network=True)
    asm_check = next(r for r in report["results"] if r["label"] == "assemble_diagnose")
    assert asm_check["passed"] is True


def test_run_preflight_verifier_check_passes_for_adr_filter(preflight_mod):
    """ADR-2605262500 scope is 100% clean (per cycle 27+) → always passes."""
    report = preflight_mod.run_preflight(skip_pds_network=True)
    ver_check = next(r for r in report["results"]
                     if "verify_deps_toml_paths" in r["label"])
    assert ver_check["passed"] is True


def test_main_cli_exit_code_matches_pass_status(preflight_mod, monkeypatch):
    """main() returns 0 if all pass, 1 if any fails."""
    # No ETZ_VISION_PII_FACE_MODEL → vision check fails → preflight fails.
    monkeypatch.delenv("ETZ_VISION_PII_FACE_MODEL", raising=False)
    monkeypatch.delenv("ETZ_VISION_PII_BACKEND", raising=False)
    rc = preflight_mod.main(["--skip-pds-network", "--json"])
    # Without FACE_MODEL, vision_pii_diagnose check returns 1, preflight=1.
    assert rc == 1


def test_main_json_output_shape(preflight_mod, capsys):
    rc = preflight_mod.main(["--skip-pds-network", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "all_passed" in payload
    assert "n_checks" in payload
    assert payload["n_checks"] == 4
    assert "results" in payload
    for r in payload["results"]:
        assert "label" in r
        assert "exit_code" in r
        assert "passed" in r


def test_main_human_output_includes_action_items_when_failing(preflight_mod, capsys, monkeypatch):
    monkeypatch.delenv("ETZ_VISION_PII_FACE_MODEL", raising=False)
    rc = preflight_mod.main(["--skip-pds-network"])
    captured = capsys.readouterr()
    assert "PREFLIGHT: FAIL" in captured.out or "PREFLIGHT: PASS" in captured.out
    # If failing, action items appear.
    if rc == 1:
        assert "review failing check(s)" in captured.out
        assert "vision_pii_diagnose" in captured.out
