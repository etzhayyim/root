"""Tests for the cold-path assembler row-cap feature (ADR-2605262400 §4).

Covers the `--max-rows-per-source` CLI flag + per-source `max_rows`
recipe field added in commit a28db5b48. The cap lets operators
assemble partial corpora from huge sources (e.g. RIPE-RIS bview
NDJSON with 5-10M rows) without iterating the full file.

Precedence: ``src.max_rows > 0 ? src.max_rows : max_rows_per_source``;
``0`` = no cap (full iteration, the pre-cap default).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
ASSEMBLER_PATH = (
    REPO_ROOT
    / "70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py"
)
PYMAGATAMA_SRC = REPO_ROOT / "20-actors/magatama/py/src"


def _load_assembler():
    import sys as _sys
    spec = importlib.util.spec_from_file_location(
        "_assembler_under_test_caps", ASSEMBLER_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    _sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def assembler(monkeypatch):
    monkeypatch.setenv("ETZ_PYMAGATAMA_SRC", str(PYMAGATAMA_SRC))
    return _load_assembler()


def _write_recipe(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "recipe.toml"
    p.write_text(body, encoding="utf-8")
    return p


def _stage_iana_ndjson(annex_root: Path, n_rows: int) -> None:
    subdir = annex_root / "netreg" / "iana-root" / "iana-snap-260526"
    subdir.mkdir(parents=True, exist_ok=True)
    nd = subdir / "root.zone.ndjson"
    with nd.open("w", encoding="utf-8") as f:
        for i in range(n_rows):
            f.write(json.dumps({
                "tld": f"tld{i:04d}",
                "ns": [f"a.nic.tld{i:04d}."],
                "ds": [],
                "glue": [],
            }) + "\n")


def _read_ndjson(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                out.append(json.loads(s))
    return out


_RECIPE_BASE = """
target_artifact = "baien-server-iana-cap-v1"
output_subdataset = "iana-cap-v1"
max_tier_cap = "A"

[[source]]
subdataset    = "netreg/iana-root"
datasetPin_at = "at://did:web:dataset-pinner.etzhayyim.com/app.etzhayyim.substrate.datasetPin/3kdqcyhxreal"
shard_glob    = "root.zone.ndjson"
tier          = "A"
license       = "public-domain"
weight        = 1.0
"""


# ── No cap (regression: default unbounded) ──────────────────────────────


def test_no_cap_emits_all_rows(assembler, tmp_path):
    annex = tmp_path / "annex"
    out_dir = tmp_path / "out"
    _stage_iana_ndjson(annex, 50)

    recipe_path = _write_recipe(tmp_path, _RECIPE_BASE)
    recipe = assembler.load_recipe(recipe_path)
    manifest = assembler.assemble(recipe, annex_root=annex, out_dir=out_dir)

    src = manifest["sources"][0]
    assert src["rowsEmitted"] == 50
    assert src["effectiveRowCap"] == 0
    assert src["capHit"] is False
    assert len(_read_ndjson(Path(src["outShard"]))) == 50


# ── CLI flag (max_rows_per_source kwarg) ────────────────────────────────


def test_max_rows_per_source_caps_row_emission(assembler, tmp_path):
    annex = tmp_path / "annex"
    out_dir = tmp_path / "out"
    _stage_iana_ndjson(annex, 100)

    recipe_path = _write_recipe(tmp_path, _RECIPE_BASE)
    recipe = assembler.load_recipe(recipe_path)
    manifest = assembler.assemble(
        recipe, annex_root=annex, out_dir=out_dir, max_rows_per_source=10,
    )

    src = manifest["sources"][0]
    assert src["rowsEmitted"] == 10
    assert src["effectiveRowCap"] == 10
    assert src["capHit"] is True

    rows = _read_ndjson(Path(src["outShard"]))
    assert len(rows) == 10
    # First-10 ordering preserved (no shuffling at this layer).
    assert rows[0]["payload"]["tld"] == "tld0000"
    assert rows[-1]["payload"]["tld"] == "tld0009"


def test_cap_above_file_size_does_not_truncate(assembler, tmp_path):
    """Cap > actual rows ⇒ all rows emitted, capHit=False."""
    annex = tmp_path / "annex"
    out_dir = tmp_path / "out"
    _stage_iana_ndjson(annex, 5)

    recipe_path = _write_recipe(tmp_path, _RECIPE_BASE)
    recipe = assembler.load_recipe(recipe_path)
    manifest = assembler.assemble(
        recipe, annex_root=annex, out_dir=out_dir, max_rows_per_source=1000,
    )

    src = manifest["sources"][0]
    assert src["rowsEmitted"] == 5
    assert src["effectiveRowCap"] == 1000
    assert src["capHit"] is False


# ── Per-source override (recipe max_rows takes precedence) ──────────────


def test_per_source_max_rows_overrides_cli_cap(assembler, tmp_path):
    """Recipe-level ``max_rows`` overrides the CLI flag for that source."""
    annex = tmp_path / "annex"
    out_dir = tmp_path / "out"
    _stage_iana_ndjson(annex, 100)

    recipe_body = _RECIPE_BASE + "max_rows      = 7\n"
    recipe_path = _write_recipe(tmp_path, recipe_body)
    recipe = assembler.load_recipe(recipe_path)

    # CLI says 99 but the per-source override wins.
    manifest = assembler.assemble(
        recipe, annex_root=annex, out_dir=out_dir, max_rows_per_source=99,
    )

    src = manifest["sources"][0]
    assert src["rowsEmitted"] == 7
    assert src["effectiveRowCap"] == 7
    assert src["capHit"] is True


def test_per_source_max_rows_without_cli_flag(assembler, tmp_path):
    """Recipe-level ``max_rows`` works even when no CLI cap was set."""
    annex = tmp_path / "annex"
    out_dir = tmp_path / "out"
    _stage_iana_ndjson(annex, 100)

    recipe_body = _RECIPE_BASE + "max_rows      = 3\n"
    recipe_path = _write_recipe(tmp_path, recipe_body)
    recipe = assembler.load_recipe(recipe_path)
    manifest = assembler.assemble(recipe, annex_root=annex, out_dir=out_dir)

    src = manifest["sources"][0]
    assert src["rowsEmitted"] == 3
    assert src["effectiveRowCap"] == 3
    assert src["capHit"] is True


# ── load_recipe reads max_rows ──────────────────────────────────────────


def test_load_recipe_parses_max_rows_field(assembler, tmp_path):
    recipe_body = _RECIPE_BASE + "max_rows      = 42\n"
    recipe_path = _write_recipe(tmp_path, recipe_body)
    recipe = assembler.load_recipe(recipe_path)
    assert recipe.sources[0].max_rows == 42


def test_load_recipe_max_rows_defaults_to_zero(assembler, tmp_path):
    recipe_path = _write_recipe(tmp_path, _RECIPE_BASE)
    recipe = assembler.load_recipe(recipe_path)
    assert recipe.sources[0].max_rows == 0


# ── Cap fires BEFORE pii/charter overhead ───────────────────────────────


def test_cap_skips_charter_scan_on_excluded_rows(assembler, tmp_path):
    """Charter scanner samples every 100 rows. A cap of 5 + 200 input
    rows should produce ``rowsScannedForCharter`` == 1 (only row index 0
    is sampled before the cap fires)."""
    annex = tmp_path / "annex"
    out_dir = tmp_path / "out"
    _stage_iana_ndjson(annex, 200)

    recipe_path = _write_recipe(tmp_path, _RECIPE_BASE)
    recipe = assembler.load_recipe(recipe_path)
    manifest = assembler.assemble(
        recipe, annex_root=annex, out_dir=out_dir, max_rows_per_source=5,
    )

    src = manifest["sources"][0]
    assert src["rowsEmitted"] == 5
    # Row 0 is sampled (i % 100 == 0 hits at i=0); row 100 would be next
    # sample but we capped at 5 so it never runs.
    assert src["rowsScannedForCharter"] == 1
