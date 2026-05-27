"""Tests for assemble_diagnose.py operator CLI."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


_THIS = Path(__file__).resolve()
_E7M_SIM = _THIS.parent.parent
_SCRIPT = _E7M_SIM / "scripts" / "assemble_diagnose.py"
_WADACHI_SCENE = _E7M_SIM / "scenes" / "wadachi-r1-shibuya-1km" / "scene.yaml"


@pytest.fixture(scope="module")
def diag_mod():
    spec = importlib.util.spec_from_file_location("assemble_diagnose", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["assemble_diagnose"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── check ──────────────────────────────────────────────────────────


def test_check_reports_deps_and_scenes(diag_mod, capsys):
    rc = diag_mod.main(["check"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "yaml" in captured.out
    assert "Scene schema" in captured.out
    assert "Scenes registered" in captured.out
    assert "wadachi-r1-shibuya-1km" in captured.out


def test_check_json_output(diag_mod, capsys):
    rc = diag_mod.main(["check", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["required"]["yaml"]["available"] is True
    assert payload["scene_schema"]["exists"] is True
    assert isinstance(payload["scenes_dir"]["scenes"], list)
    assert "wadachi-r1-shibuya-1km" in payload["scenes_dir"]["scenes"]


# ─── inspect ────────────────────────────────────────────────────────


def test_inspect_wadachi_scene(diag_mod, capsys):
    rc = diag_mod.main(["inspect", str(_WADACHI_SCENE)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "wadachi-r1-shibuya-1km" in captured.out
    assert "ADR-2605262500" in captured.out
    assert "Layers (4)" in captured.out
    assert "Max tier   : A" in captured.out


def test_inspect_json_output(diag_mod, capsys):
    rc = diag_mod.main(["inspect", str(_WADACHI_SCENE), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["scene_name"] == "wadachi-r1-shibuya-1km"
    assert payload["adr"] == "ADR-2605262500"
    assert payload["max_tier"] == "A"
    assert len(payload["layers"]) == 4
    assert payload["layers"][0]["kind"] == "terrain"


def test_inspect_missing_scene_returns_2(diag_mod, tmp_path, capsys):
    rc = diag_mod.main(["inspect", str(tmp_path / "no-such-scene.yaml")])
    assert rc == 2


def test_inspect_invalid_scene_returns_1(diag_mod, tmp_path, capsys):
    """A scene.yaml without `world:` section fails build_plan."""
    bad = tmp_path / "bad-scene"
    bad.mkdir()
    (bad / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: R1.1\nscene:\n  num_envs: 1\n",
        encoding="utf-8",
    )
    rc = diag_mod.main(["inspect", str(bad / "scene.yaml")])
    assert rc == 1
    captured = capsys.readouterr()
    assert "no `world:` section" in captured.err


# ─── dry-run ────────────────────────────────────────────────────────


def test_dry_run_wadachi(diag_mod, capsys):
    rc = diag_mod.main(["dry-run", str(_WADACHI_SCENE)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "wadachi-r1-shibuya-1km" in captured.out
    assert "layers=4" in captured.out
    assert "sha256=" in captured.out
    assert "(no files written)" in captured.out


def test_dry_run_json(diag_mod, capsys):
    rc = diag_mod.main(["dry-run", str(_WADACHI_SCENE), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["scene_name"] == "wadachi-r1-shibuya-1km"
    assert payload["layers"] == 4
    assert payload["max_tier"] == "A"
    assert len(payload["usda_sha256"]) == 64
    assert len(payload["usda_sha256_prefix"]) == 12


def test_dry_run_writes_no_files(diag_mod, tmp_path, capsys):
    """Verify nothing is created in tmp/cwd by dry-run."""
    import os
    before = set(os.listdir(tmp_path))
    cwd_before = set(os.listdir(_WADACHI_SCENE.parent))
    rc = diag_mod.main(["dry-run", str(_WADACHI_SCENE)])
    assert rc == 0
    after = set(os.listdir(tmp_path))
    cwd_after = set(os.listdir(_WADACHI_SCENE.parent))
    assert after == before        # no files in tmp
    assert cwd_after == cwd_before  # no files in scene dir
