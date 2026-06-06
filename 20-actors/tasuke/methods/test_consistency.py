#!/usr/bin/env python3
"""SSoT-consistency / drift-lock tests for 助 (tasuke) — ADR-2606060900.

Bind the manifest, cell tree, lexicons, ontology, code, seed, and registry to ONE source of truth.
"""
from __future__ import annotations

import json
import pathlib

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_REPO = _ROOT.parents[1]
_LEX = _ROOT / "lex"
_CELLS = _ROOT / "cells"
_ONTOLOGY = _REPO / "00-contracts" / "schemas" / "cybercrime-victim-support-ontology.kotoba.edn"
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
    on_disk = {p.name for p in _CELLS.iterdir() if p.is_dir() and (p / "cell.py").is_file()}
    assert on_disk == declared, f"cell tree {on_disk} != manifest {declared}"


# ── manifest lexicons ↔ lex/*.edn ───────────────────────────────────────────
def test_manifest_lexicons_resolve_to_files_with_matching_id():
    for ns in _manifest()["lexiconNamespaces"]:
        last = ns["id"].split(".")[-1]
        f = _LEX / f"{last}.edn"
        assert f.is_file(), f"missing lexicon file for {ns['id']}"
        assert load_edn(f)[":id"] == ns["id"]


def test_every_lex_file_is_declared_in_manifest():
    declared = {ns["id"] for ns in _manifest()["lexiconNamespaces"]}
    on_disk = {load_edn(f)[":id"] for f in _LEX.glob("*.edn")}
    assert on_disk == declared


# ── manifest gate/non-goal counts ───────────────────────────────────────────
def test_manifest_declares_ten_gates_and_seven_nongoals():
    m = _manifest()
    assert len(m["constitutionalGates"]["gates"]) == 10
    assert len(m["nonGoals"]["goals"]) == 7


# ── ontology ≡ code scam-kind vocab ─────────────────────────────────────────
def test_ontology_scam_kinds_equal_code():
    from triage import SCAM_KINDS
    onto = {k.lstrip(":") for k in load_edn(_ONTOLOGY)[":ontology/scam-kinds"]}
    assert set(SCAM_KINDS) == onto


# ── seed ↔ ontology (no seed case uses an out-of-vocab scam-kind) ────────────
def test_seed_cases_use_only_ontology_vocab():
    onto = load_edn(_ONTOLOGY)
    kinds = {k for k in onto[":ontology/scam-kinds"]}
    for c in load_edn(_ROOT / "data" / "seed-cybercrime-cases.kotoba.edn")[":case/batch"]:
        assert c[":case/scam-kind"] in kinds, c[":case/scam-kind"]
        assert int(c[":case/support-cost-jpy"]) == 0  # G1 — every seed case is free
        assert c[":case/consent"] is True             # G7


# ── seed registry is reachable + within ontology vocab (the stray-brace guard) ─
def test_seed_registry_windows_reachable_and_in_vocab():
    onto = load_edn(_ONTOLOGY)
    allowed = set(onto[":ontology/referral-windows"])
    seed = load_edn(_ROOT / "data" / "seed-cybercrime-cases.kotoba.edn")
    windows = seed.get(":registry/windows", [])
    assert windows, "seed :registry/windows is unreachable (top-map brace bug?)"
    for w in windows:
        assert w[":registry/window"] in allowed, w[":registry/window"]
        assert w[":registry/sourcing"] in (":representative", ":authoritative")


# ── actor-profile seed registration matches the manifest ────────────────────
def test_actor_profile_seed_has_tasuke():
    blob = _PROFILE_SEED.read_text(encoding="utf-8")
    assert "did:web:etzhayyim.com:actor:tasuke" in blob
    m = _manifest()
    assert m["references"]["schema"].lstrip("/") in blob.replace('"', "")
    assert "com.etzhayyim.tasuke" in blob


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
