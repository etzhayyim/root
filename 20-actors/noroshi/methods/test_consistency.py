"""SSoT-consistency tests for noroshi (烽) — ADR-2606051600 (items 1+3+4).

Locks the structural integrity of the actor's single-sources-of-truth so a future edit cannot silently
drift them apart:
  • manifest.edn cells/lex ↔ the actual files on disk
  • the canonical ontology (00-contracts) ↔ the deployable kotoba/schema.edn (attribute parity)
  • both seed files ↔ schema.edn (no seed entity uses an undeclared attribute)
  • manifest force-classes ↔ ontology force-classes (and :weaponizable absent — G3/N1)
"""

from __future__ import annotations

import pathlib

import pytest

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_ONTOLOGY = _ROOT.parents[1] / "00-contracts" / "schemas" / "photonic-convergence-ontology.kotoba.edn"


def _manifest() -> dict:
    return load_edn(_ROOT / "manifest.edn")


def _schema_idents() -> set:
    return {r[":db/ident"] for r in load_edn(_ROOT / "kotoba" / "schema.edn") if ":db/ident" in r}


def _seed_attr_keys(path: pathlib.Path) -> set:
    keys = set()
    for r in load_edn(path):
        if isinstance(r, dict):
            keys |= {k for k in r if isinstance(k, str) and k.startswith(":") and "/" in k}
    return keys


# ── manifest ↔ files ─────────────────────────────────────────────────────────
def test_every_manifest_lex_has_a_matching_lexicon_file():
    for lex in _manifest()[":actor/lex"]:
        lid = lex[":lex/id"]
        f = _ROOT / "lex" / f"{lid}.edn"
        assert f.exists(), f"missing lexicon file for {lid}"
        assert load_edn(f)[":id"] == f"com.etzhayyim.noroshi.{lid}"


def test_every_manifest_cell_exists_as_descriptor_or_coded_dir():
    for cell in _manifest()[":actor/cells"]:
        cid = cell[":cell/id"]
        flat = _ROOT / "cells" / f"{cid}.edn"
        coded = _ROOT / "cells" / cid / "cell.py"
        assert flat.exists() or coded.exists(), f"no cell descriptor/dir for {cid}"
        if cell.get(":cell/coded"):
            assert coded.exists(), f"cell {cid} marked coded but has no cell.py"


def test_exactly_one_coded_cell_and_it_is_active_alignment():
    coded = [c[":cell/id"] for c in _manifest()[":actor/cells"] if c.get(":cell/coded")]
    assert coded == ["active_alignment"]


# ── ontology ↔ deployable schema ─────────────────────────────────────────────
def test_ontology_attributes_equal_schema_idents():
    onto_attrs = set(load_edn(_ONTOLOGY)[":ontology/attributes"])
    assert onto_attrs == _schema_idents()   # exact parity, both directions


# ── seeds ↔ schema ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("seed", ["kotoba/seed.edn", "data/seed-photonic-fleet.kotoba.edn"])
def test_seed_uses_only_declared_attributes(seed):
    undeclared = _seed_attr_keys(_ROOT / seed) - _schema_idents()
    assert not undeclared, f"{seed} uses undeclared attributes: {sorted(undeclared)}"


# ── manifest ↔ ontology force classes (and N1) ───────────────────────────────
def test_manifest_force_classes_match_ontology():
    m_fc = set(_manifest()[":actor/force-classes"])
    o_fc = set(load_edn(_ONTOLOGY)[":ontology/force-classes"])
    assert m_fc == o_fc
    assert ":weaponizable" not in m_fc   # G3/N1


# ── seed VALUES obey the ontology enums (charter enforced on the data, not just the keys) ─────
def _seed_rows():
    rows = []
    for seed in ("kotoba/seed.edn", "data/seed-photonic-fleet.kotoba.edn"):
        rows += [r for r in load_edn(_ROOT / seed) if isinstance(r, dict)]
    return rows


@pytest.mark.parametrize("attr,onto_key,forbidden", [
    (":pdev/force-class", ":ontology/force-classes", ":weaponizable"),
    (":pdev/kind", ":ontology/device-kinds", None),
    (":probot/force-class", ":ontology/force-classes", ":weaponizable"),
    (":sense/target-class", ":ontology/target-classes", ":person"),
])
def test_seed_keyword_values_obey_ontology_enums(attr, onto_key, forbidden):
    allowed = set(load_edn(_ONTOLOGY)[onto_key])
    for r in _seed_rows():
        if attr in r:
            assert r[attr] in allowed, f"{attr}={r[attr]} not in {onto_key}"
            if forbidden:
                assert r[attr] != forbidden


def test_seed_const_invariants_hold_on_the_data():
    """Charter consts (G3/G7/G8) must hold on every seed datom that carries them."""
    for r in _seed_rows():
        if ":wave/civilian" in r:
            assert r[":wave/civilian"] is True            # G3/N1
        if ":pkg/server-held-key" in r:
            assert r[":pkg/server-held-key"] is False     # G7
        if ":pkg/dry-run" in r:
            assert r[":pkg/dry-run"] is True              # G8
        if ":pdev/process" in r:
            assert r[":pdev/process"] == ":open-pdk"      # G1
        if ":pdev/eda" in r:
            assert r[":pdev/eda"] in {":gdsfactory", ":meep", ":klayout", ":openlane"}  # G1 open-EDA
