"""suji (筋) — kami-genesis/Isaac bridge + SSoT-consistency tests."""

from __future__ import annotations

import pathlib

from _edn import load_edn
from kami_biomech_bridge import solve_static, to_articulation
from load import solve_posture_loads
from posture import LAPTOP_ON_LAP, posture_from_workstation
from segment import build_body

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_articulation_spec_well_formed() -> None:
    body = build_body(70.0, 1.70)
    posture = posture_from_workstation(LAPTOP_ON_LAP)
    art = to_articulation(body, posture)
    names = {l.name for l in art.links}
    assert {"head_neck", "thorax_abdomen", "upper_arm", "forearm"} <= names
    # every joint references existing links
    for j in art.joints:
        assert j.parent_link in names or j.parent_link == "pelvis"
        assert j.child_link in names
    assert art.gravity_mps2 > 9.0


def test_bridge_static_matches_load_solver() -> None:
    """The bridge's solve_static must equal the closed-form load.py moments (one solver)."""
    body = build_body(70.0, 1.70)
    posture = posture_from_workstation(LAPTOP_ON_LAP)
    bridge = {d["joint"]: d["moment_nm"] for d in solve_static(body, posture)}
    loads = solve_posture_loads(body, posture)
    assert abs(bridge["cervicothoracic"] - round(loads.cervical.extensor_moment_nm, 4)) < 1e-6
    for j in loads.joints:
        if j.joint == "cervicothoracic":
            continue
        assert abs(bridge[j.joint] - round(j.moment_nm, 4)) < 1e-6


def test_manifest_cells_match_cell_files() -> None:
    manifest = load_edn(_ROOT / "manifest.edn")
    declared = {c[":cell/id"] for c in manifest[":actor/cells"]}
    on_disk = {p.stem for p in (_ROOT / "cells").glob("*.edn")}
    assert declared == on_disk, f"manifest cells {declared} != disk {on_disk}"


def test_manifest_lexicons_match_lex_files() -> None:
    manifest = load_edn(_ROOT / "manifest.edn")
    declared = set(manifest[":actor/lexicons"])
    on_disk = {f"com.etzhayyim.suji.{p.stem}" for p in (_ROOT / "lex").glob("*.edn")}
    assert declared == on_disk


def test_seed_references_resolve() -> None:
    """Every posture/load/muscle/strain in the seed points at a defined body/posture."""
    seed = load_edn(_ROOT / "kotoba" / "seed.edn")
    bodies = {e[":body/id"] for e in seed if ":body/id" in e}
    postures = {e[":posture/id"] for e in seed if ":posture/id" in e}
    for e in seed:
        if ":posture/body" in e:
            assert e[":posture/body"] in bodies
        for ref in (":load/posture", ":muscle/posture", ":strain/posture"):
            if ref in e:
                assert e[ref] in postures, f"dangling {ref}={e[ref]}"
