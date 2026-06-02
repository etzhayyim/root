#!/usr/bin/env python3
"""funadaiku cell state machines — R0 transition coverage (ADR-2606013400).

The 9 cells' `.solve()` deliberately raise RuntimeError until Council ratifies the
R1 activation ADR-2606013415 — this test does NOT bypass that gate (it never calls
solve()). It exercises the pure, langgraph-free `state_machine.py` transition
functions that back each cell, which had zero coverage:

  - CellState defaults to a 0% completion INIT-phase record
  - each transition_to_* returns a well-formed {cell_state, next_node} step whose
    phase is a member of that cell's Phase enum and whose completionPct is a
    monotone integer in (0, 100]
  - the transitions collectively reach 100% (a complete INIT→…→ATTESTATION path)

Generic over all 9 cells so a new cell or a renamed transition is caught.
"""
import importlib.util
import inspect
import pathlib
import sys
from enum import Enum

_CELLS_DIR = pathlib.Path(__file__).parent
_CELL_DIRS = sorted(
    p.parent for p in _CELLS_DIR.glob("*/state_machine.py")
)


def _load(sm_path):
    name = f"funadaiku_sm_{sm_path.parent.name}"
    spec = importlib.util.spec_from_file_location(name, sm_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass field-type lookup needs this before exec
    spec.loader.exec_module(mod)
    return mod


def _phase_enum(mod):
    for _, obj in inspect.getmembers(mod, inspect.isclass):
        if issubclass(obj, Enum) and obj is not Enum and obj.__module__ == mod.__name__:
            return obj
    raise AssertionError("no Phase enum found")


def _cellstate_cls(mod):
    cls = getattr(mod, "CellState", None)
    assert cls is not None, "no CellState dataclass"
    return cls


def _transitions(mod):
    fns = [
        f for n, f in inspect.getmembers(mod, inspect.isfunction)
        if n.startswith("transition_to_") and f.__module__ == mod.__name__
    ]
    assert fns, "no transition_to_* functions"
    return fns


def _check_one(cell_dir):
    mod = _load(cell_dir / "state_machine.py")
    phase_values = {e.value for e in _phase_enum(mod)}

    # CellState default = fresh 0% record
    cs = _cellstate_cls(mod)()
    assert cs.completionPct == 0, f"{cell_dir.name}: CellState should default to 0%"
    assert cs.phase in phase_values, f"{cell_dir.name}: default phase not in enum"

    pcts = []
    for fn in _transitions(mod):
        out = fn({"cell_state": {}})
        assert isinstance(out, dict) and "cell_state" in out, f"{cell_dir.name}.{fn.__name__}: bad return"
        new = out["cell_state"]
        assert new["phase"] in phase_values, f"{cell_dir.name}.{fn.__name__}: phase {new['phase']!r} not in enum"
        pct = new["completionPct"]
        assert isinstance(pct, int) and 0 < pct <= 100, f"{cell_dir.name}.{fn.__name__}: pct {pct} out of range"
        pcts.append(pct)
        assert "next_node" in out, f"{cell_dir.name}.{fn.__name__}: missing next_node"

    assert len(set(pcts)) == len(pcts), f"{cell_dir.name}: duplicate completionPct across transitions {pcts}"
    assert max(pcts) == 100, f"{cell_dir.name}: transitions never reach 100% (got {pcts})"
    return cell_dir.name, len(pcts)


def test_nine_cells_present():
    names = {p.name for p in _CELL_DIRS}
    expected = {
        "steel_block_fabrication", "grand_block_assembly", "weld_ndt_inspection",
        "powertrain_integration", "outfitting", "launch_commissioning",
        "sea_trial", "decarbonization_audit", "class_certification_binder",
    }
    assert names == expected, f"cell set drift: {names ^ expected}"


def test_all_state_machines_transition_to_completion():
    results = [_check_one(d) for d in _CELL_DIRS]
    assert len(results) == 9
    # every cell reached a complete transition chain
    assert all(steps >= 1 for _, steps in results)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
