"""Test the `e7m-dataset assemble-corpus` CLI verb.

Smokes the wiring: --help mentions the verb, --dry-run on a valid
recipe exits 0 with a JSON summary, --dry-run on a G5-violating
recipe exits 2.
"""

from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest

from e7m_dataset import cli


REPO_ROOT = Path(__file__).resolve().parents[3]
ANCHOR_RECIPE = (
    REPO_ROOT
    / "70-tools/baien-moemoekyun-train/recipes/tier-a-netreg-foundations.toml"
)


def test_help_mentions_assemble_corpus(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    captured = capsys.readouterr()
    assert "assemble-corpus" in captured.out


def test_dry_run_on_tier_a_recipe(monkeypatch, capsys):
    if not ANCHOR_RECIPE.is_file():
        pytest.skip("anchor recipe not present in this checkout")
    # The script-locator walks from cwd up; pin cwd to repo root.
    monkeypatch.chdir(REPO_ROOT)
    rc = cli.main([
        "assemble-corpus",
        "--recipe", str(ANCHOR_RECIPE),
        "--dry-run",
    ])
    captured = capsys.readouterr()
    assert rc == 0, captured.err
    summary = json.loads(captured.out)
    assert summary["targetArtifact"] == "baien-server-netreg-foundations-v1"
    assert summary["computedMaxTier"] == "A"


def test_dry_run_g5_fail_closed(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(REPO_ROOT)
    bad_recipe = tmp_path / "bad.toml"
    bad_recipe.write_text(
        'target_artifact = "baien-server-routing-v1"\n'
        'output_subdataset = "x/"\n'
        'max_tier_cap = "C"\n'
        '\n'
        '[[source]]\n'
        'subdataset    = "dns/rapid7-sonar-fdns"\n'
        'datasetPin_at = "at://did:web:dataset-pinner.etzhayyim.com/com.etzhayyim.substrate.datasetPin/3kxxxxxxxxxx"\n'
        'shard_glob    = "*.ndjson"\n'
        'tier          = "C"\n'
        'license       = "rapid7-research-use"\n'
        'weight        = 1.0\n',
        encoding="utf-8",
    )
    rc = cli.main([
        "assemble-corpus",
        "--recipe", str(bad_recipe),
        "--dry-run",
    ])
    captured = capsys.readouterr()
    assert rc == 2
    assert "standalone '-nc-'" in captured.err
