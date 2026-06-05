#!/usr/bin/env python3
"""SSoT-consistency / drift-lock tests for 朱 (ake) — ADR-2606052100 (noroshi test_consistency pattern).

These bind the manifest, the cell tree, the lexicons, the ontology, the code, the seed, and the
registry to ONE source of truth, so a future edit that adds a cell but forgets the manifest (or
renames a lexicon, or drifts the route vocab) fails loudly here instead of silently shipping.
"""
from __future__ import annotations

import json
import pathlib

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_REPO = _ROOT.parents[1]
_LEX = _ROOT / "lex"
_CELLS = _ROOT / "cells"
_ONTOLOGY = _REPO / "00-contracts" / "schemas" / "community-edit-ontology.kotoba.edn"
_PROFILE_SEED = _REPO / "00-contracts" / "schemas" / "actor-profile-seed.kotoba.edn"


def _manifest() -> dict:
    return json.loads((_ROOT / "manifest.jsonld").read_text(encoding="utf-8"))


# ── manifest cells ↔ cell tree ──────────────────────────────────────────────
def test_manifest_cells_have_dirs_and_state_machines():
    for cell in _manifest()["cells"]:
        d = _CELLS / cell["name"]
        assert (d / "cell.py").is_file(), f"missing {cell['name']}/cell.py"
        assert (d / "state_machine.py").is_file(), f"missing {cell['name']}/state_machine.py"


def test_every_cell_dir_is_in_the_manifest():
    declared = {c["name"] for c in _manifest()["cells"]}
    on_disk = {p.name for p in _CELLS.iterdir()
               if p.is_dir() and (p / "cell.py").is_file()}
    assert on_disk == declared, f"cell tree {on_disk} != manifest {declared}"


# ── manifest lexicons ↔ lex/*.edn ───────────────────────────────────────────
def test_manifest_lexicons_resolve_to_files_with_matching_id():
    for ns in _manifest()["lexiconNamespaces"]:
        lid = ns["id"]
        last = lid.split(".")[-1]
        f = _LEX / f"{last}.edn"
        assert f.is_file(), f"missing lexicon file for {lid}"
        assert load_edn(f)[":id"] == lid


def test_every_lex_file_is_declared_in_manifest():
    declared = {ns["id"] for ns in _manifest()["lexiconNamespaces"]}
    on_disk = {load_edn(f)[":id"] for f in _LEX.glob("*.edn")}
    assert on_disk == declared


# ── manifest gate/non-goal counts (the stated 9 + 7) ────────────────────────
def test_manifest_declares_nine_gates_and_seven_nongoals():
    m = _manifest()
    assert len(m["constitutionalGates"]["gates"]) == 9
    assert len(m["nonGoals"]["goals"]) == 7


# ── ontology ≡ code route vocab ─────────────────────────────────────────────
def test_ontology_routes_equal_code_routes():
    from triage import ROUTES
    onto = {r.lstrip(":") for r in load_edn(_ONTOLOGY)[":ontology/triage-routes"]}
    assert set(ROUTES) == onto


# ── seed ↔ ontology (no seed edit uses an out-of-vocab target-kind/op) ───────
def test_seed_edits_use_only_ontology_vocab():
    onto = load_edn(_ONTOLOGY)
    kinds = set(onto[":ontology/target-kinds"])
    ops = set(onto[":ontology/edit-ops"])
    for e in load_edn(_ROOT / "data" / "seed-edit-graph.kotoba.edn")[":edit/batch"]:
        assert e[":edit/target-kind"] in kinds, e[":edit/target-kind"]
        assert e[":edit/op"] in ops, e[":edit/op"]


# ── actor-profile seed registration ─────────────────────────────────────────
def test_committed_fixture_registers_ake_with_its_lexicon():
    # hermetic: ake's own committed fixture carries its DID + lexicon
    fblob = (_ROOT / "data" / "sample-profile-seed.kotoba.edn").read_text(encoding="utf-8")
    assert "did:web:etzhayyim.com:actor:ake" in fblob
    assert "com.etzhayyim.ake" in fblob


def test_real_profile_seed_matches_manifest_when_ake_registered():
    # soft: the SHARED repo seed registers ake by coordination, committed separately from ake's
    # own commits — its absence is not an ake-suite failure (this test never hard-fails on it).
    blob = _PROFILE_SEED.read_text(encoding="utf-8")
    if "did:web:etzhayyim.com:actor:ake" not in blob:
        return
    m = _manifest()
    assert m["references"]["schema"].lstrip("/").replace('"', "") in blob.replace('"', "")
    assert "com.etzhayyim.ake" in blob


# ── ADR file referenced by the manifest exists ──────────────────────────────
def test_adr_file_exists():
    adr = _REPO / _manifest()["references"]["adr"]["master"].lstrip("/")
    assert adr.is_file(), f"ADR not found: {adr}"


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_consistency.py")
    sys.exit(1 if failed else 0)
