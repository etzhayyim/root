#!/usr/bin/env python3
"""SSoT drift-lock tests for 扶持 (fuchi) — manifest ↔ files ↔ ontology ↔ seed.

Standalone-runnable: python3 test_consistency.py
"""
from __future__ import annotations

import json
import pathlib
import sys

from _edn import load_edn

_ACTOR = pathlib.Path(__file__).resolve().parents[1]
_ROOT = _ACTOR.parents[1]
_SCHEMA = _ROOT / "00-contracts" / "schemas" / "maintainer-sustenance-ontology.kotoba.edn"
_MANIFEST = _ACTOR / "manifest.jsonld"
_SEED = _ACTOR / "data" / "seed-sustenance-graph.kotoba.edn"


def _manifest():
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))


def test_manifest_cells_match_cell_dirs():
    declared = {c["name"] for c in _manifest()["cells"]}
    dirs = {p.name for p in (_ACTOR / "cells").iterdir()
            if p.is_dir() and not p.name.startswith("__")}
    assert declared == dirs, f"manifest {declared} != dirs {dirs}"


def test_manifest_lexicons_match_lex_files():
    declared = {l["id"] for l in _manifest()["lexiconNamespaces"]}
    files = {load_edn(p)[":id"] for p in (_ACTOR / "lex").glob("*.edn")}
    assert declared == files, f"manifest {declared} != files {files}"


def test_manifest_adr_matches_ontology():
    onto = load_edn(_SCHEMA)
    assert onto[":ontology/adr"] == "2606052300"
    assert _manifest()["adr"]["master"].endswith("2606052300")


def test_manifest_schema_pointer_exists():
    p = _ROOT / _manifest()["references"]["schema"].lstrip("/")
    assert p.exists(), p


def test_every_seed_maintainer_has_envelope_or_is_excluded():
    seed = load_edn(_SEED)
    env_dids = {e[":envelope/maintainer"] for e in seed[":envelope/batch"]}
    for m in seed[":maintainer/batch"]:
        assert m[":maintainer/did"] in env_dids, m[":maintainer/did"]


def test_seed_cash_is_zero_everywhere():
    seed = load_edn(_SEED)
    for e in seed[":envelope/batch"]:
        assert e[":envelope/cash-usd-micros"] == 0


def test_seed_no_maintainer_owns_payoff():
    seed = load_edn(_SEED)
    for m in seed[":maintainer/batch"]:
        assert m.get(":maintainer/owns-payoff", False) is False


def test_seed_covenants_are_valid_vocab():
    seed = load_edn(_SEED)
    vocab = set(load_edn(_SCHEMA)[":ontology/covenants"])
    for m in seed[":maintainer/batch"]:
        assert m[":maintainer/covenant"] in vocab


def test_seed_envelope_lines_are_valid_vocab():
    seed = load_edn(_SEED)
    vocab = set(load_edn(_SCHEMA)[":ontology/envelope-lines"])
    for e in seed[":envelope/batch"]:
        assert e[":envelope/line"] in vocab


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_consistency.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
