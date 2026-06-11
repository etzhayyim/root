#!/usr/bin/env python3
"""sarutahiko cell state machines — R0 transition + G7 gate coverage (ADR-2605252500).

The 9 cells' `.solve()` deliberately raise RuntimeError (R0 scaffold) — this test
NEVER calls solve(), so it does not bypass the activation gate. It exercises the
pure, langgraph-free `state_machine.py` transition functions (each cell uses its
own <X>State dataclass + `<x>_state` key + enum Phase), which had zero coverage,
plus the constitutional G7 powertrain fuel-guard.

Generic over all 9 cells: a new cell / renamed transition / phase-set drift is caught.
"""
import dataclasses
import importlib.util
import inspect
import pathlib
import sys
from enum import Enum

_CELLS_DIR = pathlib.Path(__file__).parent
_CELL_DIRS = sorted(p.parent for p in _CELLS_DIR.glob("*/state_machine.py"))


def _camel_to_snake(name):
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def _load(sm_path):
    name = f"sarutahiko_sm_{sm_path.parent.name}"
    spec = importlib.util.spec_from_file_location(name, sm_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass field-type lookup needs this before exec
    spec.loader.exec_module(mod)
    return mod


def _phase_enum(mod):
    for _, obj in inspect.getmembers(mod, inspect.isclass):
        if issubclass(obj, Enum) and obj is not Enum and obj.__module__ == mod.__name__:
            return obj
    raise AssertionError("no Phase enum")


def _state_dataclass(mod):
    for _, obj in inspect.getmembers(mod, inspect.isclass):
        if dataclasses.is_dataclass(obj) and obj.__name__.endswith("State") \
                and obj.__module__ == mod.__name__:
            return obj
    raise AssertionError("no <X>State dataclass")


def _seed(dc, phase_enum):
    """Build a minimal valid initial state dict for the required fields."""
    seed = {}
    init_phase = next(iter(phase_enum))
    for f in dataclasses.fields(dc):
        required = f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
        if not required:
            continue
        if f.name == "phase":
            seed[f.name] = init_phase
        elif "pct" in f.name.lower():
            seed[f.name] = 0
        else:
            seed[f.name] = "SEED"
    return seed


def _phase_value(p):
    return p.value if isinstance(p, Enum) else p


def _check_one(cell_dir):
    mod = _load(cell_dir / "state_machine.py")
    phase_enum = _phase_enum(mod)
    dc = _state_dataclass(mod)
    state_key = _camel_to_snake(dc.__name__)
    valid_phase_values = {e.value for e in phase_enum}

    seed = _seed(dc, phase_enum)
    transitions = [
        f for n, f in inspect.getmembers(mod, inspect.isfunction)
        if n.startswith("transition_to_") and f.__module__ == mod.__name__
    ]
    assert transitions, f"{cell_dir.name}: no transition_to_* functions"

    pcts = []
    for fn in transitions:
        out = fn({state_key: dict(seed)})
        assert state_key in out, f"{cell_dir.name}.{fn.__name__}: missing {state_key!r} in return"
        new = out[state_key]
        assert _phase_value(new["phase"]) in valid_phase_values, \
            f"{cell_dir.name}.{fn.__name__}: phase {new['phase']!r} not in enum"
        pct = new["completionPct"]
        assert isinstance(pct, int) and 0 < pct <= 100, \
            f"{cell_dir.name}.{fn.__name__}: pct {pct} out of range"
        pcts.append(pct)
        assert "next_node" in out, f"{cell_dir.name}.{fn.__name__}: missing next_node"

    assert len(set(pcts)) == len(pcts), f"{cell_dir.name}: duplicate completionPct {pcts}"
    assert max(pcts) == 100, f"{cell_dir.name}: transitions never reach 100% ({pcts})"
    return cell_dir.name


def test_nine_cells_present():
    names = {p.name for p in _CELL_DIRS}
    expected = {
        "cab_body_forming", "electrical_integration", "emissions_audit",
        "final_marriage", "frame_fabrication", "paint_finishing",
        "powertrain_assembly", "quality_road_test", "vin_attestation_binder",
    }
    assert names == expected, f"cell set drift: {names ^ expected}"


def test_all_state_machines_transition_to_completion():
    done = [_check_one(d) for d in _CELL_DIRS]
    assert len(done) == 9


def test_g7_powertrain_fuel_guard_accepts_clean_rejects_fossil():
    mod = _load(_CELLS_DIR / "powertrain_assembly" / "state_machine.py")
    fn = mod.transition_to_fuel_guard_checked
    seed = _seed(mod.PowertrainState, _phase_enum(mod))

    clean = fn({"powertrain_state": dict(seed), "powerTrainType": "H2-fuel-cell"})
    assert clean["powertrain_state"]["fuelGuard"]["accept"] is True

    fossil = fn({"powertrain_state": dict(seed), "powerTrainType": "pure-diesel"})
    assert fossil["powertrain_state"]["fuelGuard"]["accept"] is False, \
        "G7: a pure-fossil powertrain must be rejected by the fuel guard"


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
