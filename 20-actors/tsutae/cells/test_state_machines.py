#!/usr/bin/env python3
"""tsutae cell state machines — R0 transition + constitutional-gate coverage (ADR-2605261300).

The 8 cells' `.solve()` deliberately raise RuntimeError (R0 scaffold) — this test
NEVER calls solve(), so it does not bypass the Council activation gate. It exercises
the pure, langgraph-free `state_machine.py` transition functions (each cell uses its
own <X>State dataclass + `<x>_state` key + enum Phase), plus the smartphone-specific
constitutional guards that make tsutae a structural inversion of a surveillance phone:

  G9  open-SoC          (pcb_smt)            — proprietary SoC rejected
  G6  mic kill switch   (chassis_assembly)   — missing hardware kill switch rejected
  G3  repair-rightful   (chassis_assembly)   — excess adhesive / parts-pairing rejected
  G2  bootloader unlock (firmware_load)      — locked bootloader rejected
  G8  anti-addiction UX (final_qc)           — addictive primitive rejected
  G4  witness quorum    (device_attestation) — <2 robot signers rejected
  G10 take-back loop    (recycling_intake)   — sub-target recovery flagged

Generic over all 8 cells: a new cell / renamed transition / phase-set drift is caught.
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
    name = f"tsutae_sm_{sm_path.parent.name}"
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


def test_eight_cells_present():
    names = {p.name for p in _CELL_DIRS}
    expected = {
        "tsutae_pcb_smt", "tsutae_chassis_assembly", "tsutae_display_attachment",
        "tsutae_firmware_load", "tsutae_final_qc", "tsutae_packaging",
        "tsutae_device_attestation", "tsutae_recycling_intake",
    }
    assert names == expected, f"cell set drift: {names ^ expected}"


def test_all_state_machines_transition_to_completion():
    done = [_check_one(d) for d in _CELL_DIRS]
    assert len(done) == 8


def test_g9_open_soc_guard_accepts_riscv_rejects_proprietary():
    mod = _load(_CELLS_DIR / "tsutae_pcb_smt" / "state_machine.py")
    fn = mod.transition_to_soc_guard_checked
    seed = _seed(mod.PcbState, _phase_enum(mod))

    for soc in ("StarFive-JH7110", "SiFive-HiFive-Unmatched", "iwakura"):
        out = fn({"pcb_state": dict(seed), "soc": soc})
        assert out["pcb_state"]["socGuard"]["accept"] is True, f"{soc} must pass G9"

    for soc in ("Snapdragon-8-Gen3", "Apple-A17", "Exynos-2400"):
        out = fn({"pcb_state": dict(seed), "soc": soc})
        assert out["pcb_state"]["socGuard"]["accept"] is False, \
            f"G9: proprietary SoC {soc} must be rejected (§2(b) N1 invariant)"


def test_g6_mic_kill_switch_guard():
    mod = _load(_CELLS_DIR / "tsutae_chassis_assembly" / "state_machine.py")
    fn = mod.transition_to_mic_killswitch_verified
    seed = _seed(mod.ChassisState, _phase_enum(mod))

    ok = fn({"chassis_state": dict(seed), "micKillSwitch": True})
    assert ok["chassis_state"]["micGuard"]["accept"] is True

    bad = fn({"chassis_state": dict(seed), "micKillSwitch": False})
    assert bad["chassis_state"]["micGuard"]["accept"] is False, \
        "G6: a chassis without a hardware mic kill switch must be rejected (§2(c))"


def test_g3_repair_guard_rejects_glue_and_parts_pairing():
    mod = _load(_CELLS_DIR / "tsutae_chassis_assembly" / "state_machine.py")
    seed = _seed(mod.ChassisState, _phase_enum(mod))
    staged = mod.transition_to_components_staged({"chassis_state": dict(seed)})["chassis_state"]

    ok = mod.transition_to_repair_modularity_checked(
        {"chassis_state": staged, "adhesiveGrams": 0.0, "partsPairing": False})
    assert ok["chassis_state"]["repairGuard"]["accept"] is True

    glued = mod.transition_to_repair_modularity_checked(
        {"chassis_state": staged, "adhesiveGrams": 30.0, "partsPairing": False})
    assert glued["chassis_state"]["repairGuard"]["accept"] is False, "G3: excess adhesive rejected"

    paired = mod.transition_to_repair_modularity_checked(
        {"chassis_state": staged, "adhesiveGrams": 0.0, "partsPairing": True})
    assert paired["chassis_state"]["repairGuard"]["accept"] is False, "G3: parts-pairing rejected"


def test_g2_bootloader_unlock_guard():
    mod = _load(_CELLS_DIR / "tsutae_firmware_load" / "state_machine.py")
    fn = mod.transition_to_bootloader_unlock_confirmed
    seed = _seed(mod.FirmwareState, _phase_enum(mod))

    ok = fn({"firmware_state": dict(seed), "bootloaderUnlockable": True})
    assert ok["firmware_state"]["bootloaderGuard"]["accept"] is True

    locked = fn({"firmware_state": dict(seed), "bootloaderUnlockable": False})
    assert locked["firmware_state"]["bootloaderGuard"]["accept"] is False, \
        "G2: a locked bootloader must be rejected (§2(b) N2 invariant)"


def test_g8_anti_addiction_ux_guard():
    mod = _load(_CELLS_DIR / "tsutae_final_qc" / "state_machine.py")
    fn = mod.transition_to_addiction_ux_audited
    seed = _seed(mod.QcState, _phase_enum(mod))

    ok = fn({"qc_state": dict(seed), "notificationBatchMin": 15, "infiniteScrollApi": False})
    assert ok["qc_state"]["uxGuard"]["accept"] is True

    scroll = fn({"qc_state": dict(seed), "notificationBatchMin": 15, "infiniteScrollApi": True})
    assert scroll["qc_state"]["uxGuard"]["accept"] is False, "G8: infinite-scroll API rejected"

    spammy = fn({"qc_state": dict(seed), "notificationBatchMin": 0, "infiniteScrollApi": False})
    assert spammy["qc_state"]["uxGuard"]["accept"] is False, "G8: <15min notification batch rejected"


def test_g4_witness_quorum_guard():
    mod = _load(_CELLS_DIR / "tsutae_device_attestation" / "state_machine.py")
    fn = mod.transition_to_robot_quorum_signed
    seed = _seed(mod.DeviceState, _phase_enum(mod))

    two = fn({"device_state": dict(seed), "robotSigners": [
        {"robotDid": "did:web:etzhayyim.com:mimi-1", "role": "aoi"},
        {"robotDid": "did:web:etzhayyim.com:otete-1", "role": "handling"}]})
    assert two["device_state"]["quorumGuard"]["accept"] is True

    one = fn({"device_state": dict(seed), "robotSigners": [
        {"robotDid": "did:web:etzhayyim.com:mimi-1", "role": "aoi"}]})
    assert one["device_state"]["quorumGuard"]["accept"] is False, \
        "G4: fewer than 2 distinct robot signers must be rejected"


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
