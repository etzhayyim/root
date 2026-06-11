#!/usr/bin/env python3
"""organism-viz — aliveness metric tests (coverage loop iteration 10).

aliveness.py computes the M/D/C/P/G "aliveness tuple" from repo artefacts
(observation cycle markdown, cell dirs, LANDS/MEMBERS). 309 LoC of pure
math (Shannon entropy, Pearson correlation, axis-delta motion, tended-cell
ratio) with zero tests. Driven here through tmp-repo fixtures.

Run: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
"""
import math
import pathlib
import sys

import pytest

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from etzhayyim_organism_viz import aliveness as av  # noqa: E402


# ── fixture builders ─────────────────────────────────────────────────────────

def write_cycle(obs_dir: pathlib.Path, n: int, axes: dict[str, int]) -> None:
    """Write an observation cycle markdown whose axis table matches _AXIS_ROW."""
    rows = "\n".join(f"| {i + 1} | {name} | {score}/10 | note |"
                     for i, (name, score) in enumerate(axes.items()))
    body = f"# observation cycle {n}\n\n| # | Axis | Score | Notes |\n|---|---|---|---|\n{rows}\n"
    (obs_dir / f"obs-cycle-{n}.md").write_text(body, encoding="utf-8")


def make_cell(repo: pathlib.Path, name: str, *, body: str | None) -> None:
    d = repo / "20-actors" / "kotodama" / "cells" / name
    d.mkdir(parents=True, exist_ok=True)
    if body is not None:
        (d / "cell.py").write_text(body, encoding="utf-8")


# ── _read_cycles + AliveTuple ────────────────────────────────────────────────

def test_read_cycles_parses_axis_tables_in_order(tmp_path):
    obs = tmp_path / "_observations"; obs.mkdir()
    write_cycle(obs, 2, {"Motion": 7, "Diversity": 5})
    write_cycle(obs, 1, {"Motion": 6})
    cycles = av._read_cycles(obs)
    assert [n for n, _ in cycles] == [1, 2]              # sorted by filename
    assert cycles[1][1] == {"motion": 7, "diversity": 5}  # names lowercased


def test_alive_tuple_as_dict_rounds_to_4dp():
    a = av.AliveTuple(M=1.234567, D=2.0, C=0.5, P=0.75, G=1.1, timestamp="t", notes=["x"])
    d = a.as_dict()
    assert d["M_motion"] == 1.2346
    assert d["G_generational"] == 1.1
    assert d["notes"] == ["x"]


# ── D diversity: Shannon entropy over distinct cells ─────────────────────────

def test_diversity_is_log_n_for_n_distinct_cells(tmp_path):
    for nm in ("a", "b", "c", "d"):
        make_cell(tmp_path, nm, body="x")
    H, notes = av.diversity(tmp_path)
    assert H == pytest.approx(math.log(4))               # each count 1 → H = ln N
    assert "distinct cells" in notes[0]


def test_diversity_zero_when_cells_dir_missing(tmp_path):
    H, notes = av.diversity(tmp_path)
    assert H == 0.0
    assert "missing" in notes[0]


# ── C coupling: Pearson correlation ──────────────────────────────────────────

def test_coupling_perfect_positive_correlation_is_one(tmp_path):
    obs = tmp_path / "_observations"; obs.mkdir()
    # two axes moving identically across 3 cycles → r = 1
    for n, v in enumerate([3, 6, 9], start=1):
        write_cycle(obs, n, {"Alpha": v, "Beta": v})
    C, _ = av.coupling(obs)
    assert C == pytest.approx(1.0)


def test_coupling_perfect_negative_correlation_is_minus_one(tmp_path):
    obs = tmp_path / "_observations"; obs.mkdir()
    for n, (a, b) in enumerate([(1, 9), (5, 5), (9, 1)], start=1):
        write_cycle(obs, n, {"Alpha": a, "Beta": b})
    C, _ = av.coupling(obs)
    assert C == pytest.approx(-1.0)


def test_coupling_undefined_under_three_cycles(tmp_path):
    obs = tmp_path / "_observations"; obs.mkdir()
    write_cycle(obs, 1, {"Alpha": 1, "Beta": 2})
    write_cycle(obs, 2, {"Alpha": 2, "Beta": 3})
    C, notes = av.coupling(obs)
    assert C == 0.0
    assert "<3 cycles" in notes[0]


# ── M motion: mean absolute axis delta per cycle ─────────────────────────────

def test_motion_axis_delta_mean(tmp_path):
    obs = tmp_path / "_observations"; obs.mkdir()
    # deltas: cycle1→2 |Δ|=2, cycle2→3 |Δ|=3 → mean 2.5; repo=None → no creation term
    write_cycle(obs, 1, {"Motion": 4})
    write_cycle(obs, 2, {"Motion": 6})
    write_cycle(obs, 3, {"Motion": 9})
    M, _ = av.motion(obs, repo=None)
    assert M == pytest.approx(2.5)


# ── P pruning: tended-cell ratio ─────────────────────────────────────────────

def test_pruning_ratio_counts_documented_nontrivial_cells(tmp_path):
    make_cell(tmp_path, "tended1", body='"""doc"""\n' + "x = 1\n" * 100)   # >200B + docstring
    make_cell(tmp_path, "tended2", body='"""doc"""\n' + "y = 2\n" * 100)
    make_cell(tmp_path, "stub", body='x = 1\n')                            # no docstring/short
    make_cell(tmp_path, "empty", body=None)                               # no cell.py
    P, notes = av.pruning(tmp_path)
    assert P == pytest.approx(2 / 4)
    assert "2/4" in notes[0]


# ── G generational: LANDS/MEMBERS proxy + gen-mark lift ──────────────────────

def test_generational_base_one_with_lands_present(tmp_path):
    (tmp_path / "LANDS.md").write_text("inalienable", encoding="utf-8")
    G, _ = av.generational(tmp_path)
    assert G == pytest.approx(1.0)


def test_generational_lifts_005_per_ten_gen_marks(tmp_path):
    (tmp_path / "LANDS.md").write_text("x", encoding="utf-8")
    obs = tmp_path / "_observations"; obs.mkdir()
    # 20 "Gen 0" mentions → lift = 0.05 * (20 // 10) = 0.10
    (obs / "marks-cycle-1.md").write_text("Gen 0 " * 20, encoding="utf-8")
    G, _ = av.generational(tmp_path)
    assert G == pytest.approx(1.10)


def test_generational_zero_when_lands_missing(tmp_path):
    G, notes = av.generational(tmp_path)
    assert G == 0.0
    assert "missing" in notes[0]


# ── healthy-band classification ──────────────────────────────────────────────

def test_in_healthy_band_thresholds():
    healthy = av.AliveTuple(M=0.6, D=1.6, C=0.5, P=0.7, G=1.1)
    assert av.in_healthy_band(healthy) == {"M": True, "D": True, "C": True, "P": True, "G": True}
    # boundary failures: M not > 0.5, C above 0.7, P below 0.5, G not > 1.0
    edge = av.AliveTuple(M=0.5, D=1.5, C=0.71, P=0.49, G=1.0)
    band = av.in_healthy_band(edge)
    assert band == {"M": False, "D": False, "C": False, "P": False, "G": False}


# ── compose: compute() assembles all five axes + notes ───────────────────────

def test_compute_assembles_full_tuple(tmp_path):
    (tmp_path / "LANDS.md").write_text("x", encoding="utf-8")
    obs = tmp_path / "_observations"; obs.mkdir()
    for n, v in enumerate([3, 6, 9], start=1):
        write_cycle(obs, n, {"Alpha": v, "Beta": v})
    make_cell(tmp_path, "c1", body='"""d"""\n' + "x=1\n" * 100)
    make_cell(tmp_path, "c2", body='"""d"""\n' + "x=1\n" * 100)
    a = av.compute(tmp_path)
    assert a.C == pytest.approx(1.0)         # coupling from the cycles above
    assert a.D == pytest.approx(math.log(2)) # two cells
    assert a.G == pytest.approx(1.0)
    assert a.timestamp and a.notes           # populated
