"""Lexicon + cell-descriptor well-formedness tests for noroshi (烽) — ADR-2606051600 (items 1+3+4).

Catches authoring bugs in the 5 lexicons and 5 flat cell descriptors, and locks two charter rails:
cell gates must reference real manifest gates (referential integrity), and any LLM-using cell must be
Murakumo-only (G6 — no commercial endpoint).
"""

from __future__ import annotations

import pathlib

import pytest

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_LEX = sorted((_ROOT / "lex").glob("*.edn"))
_CELLS = sorted((_ROOT / "cells").glob("*.edn"))
_FACES = {":chip", ":isac", ":packaging", ":operation", ":learning"}


def _gate_ids() -> set:
    return {g[":gate/id"] for g in load_edn(_ROOT / "manifest.edn")[":actor/gates"]}


# ── lexicons ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("lf", _LEX, ids=[p.stem for p in _LEX])
def test_lexicon_well_formed(lf):
    d = load_edn(lf)
    assert d[":lexicon"] == 1
    assert d[":id"] == f"com.etzhayyim.noroshi.{lf.stem}"
    main = d[":defs"][":main"]
    assert main[":type"] == "record"
    assert isinstance(main.get(":key"), str) and main[":key"]      # a key strategy is declared
    rec = main[":record"]
    assert rec[":type"] == "object"
    req = set(rec.get(":required", []))
    props = {p.lstrip(":") for p in rec.get(":properties", {})}
    assert req <= props, f"{lf.stem}: required not in properties: {sorted(req - props)}"
    for pname, pdef in rec[":properties"].items():
        assert ":type" in pdef, f"{lf.stem}.{pname} has no :type"


def test_all_five_lexicons_present():
    assert {p.stem for p in _LEX} == {
        "photonicDevice", "opticalLinkBudget", "isacWaveform", "senseEstimate", "packagingJob",
    }


# ── cell descriptors ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("cf", _CELLS, ids=[p.stem for p in _CELLS])
def test_cell_descriptor_well_formed(cf):
    c = load_edn(cf)
    assert c[":cell/id"] == cf.stem
    assert c[":cell/face"] in _FACES
    assert c[":cell/kind"] == ":langgraph"
    assert c[":cell/runtime"] == ":wasm"
    assert isinstance(c.get(":cell/node"), str) and c[":cell/node"]
    assert set(c.get(":cell/gates", [])) <= _gate_ids()       # referential integrity


def test_llm_cells_are_murakumo_only():
    """G6 — any cell that declares an LLM must route to the loopback Murakumo gateway, never a vendor."""
    for cf in _CELLS:
        llm = load_edn(cf).get(":cell/llm")
        if llm:
            assert llm.get(":provider") == ":murakumo"
            assert llm.get(":endpoint") == "127.0.0.1:4000"
            assert llm.get(":charter-rider") is True
