#!/usr/bin/env python3
"""panel_loading — edge-branch coverage (ADR-2606021200 / R1 maturation).

Covers the attestingRobots normalization + pallet arithmetic edges left
uncovered by test_cell.py:

  - _pallet_count(0, cap) → 0 (no modules → no pallets)
  - a supplied #robotSignature dict duplicating the loader DID / empty DID is skipped
  - a bare DID string in attestingRobots is promoted to a #robotSignature object
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "himawari_panel_loading_cell_e", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def _base(**over):
    base = {
        "loadingId": "load-2026-0602-001",
        "recordedAt": "2026-06-02T09:30:00Z",
        "moduleSerials": [f"HMW-MOD-{i:04d}" for i in range(1, 5)],
        "carrierDid": "did:web:etzhayyim.com:hikari#carrier-01",
        "carrierInternal": True,
        "loaderPhase": "Done",
        "palletCapacity": 36,
        "humanTasksRemoved": ["manual-pallet-stack", "forklift-drive"],
        "loaderRobotDid": "did:web:etzhayyim.com:sarutahiko#f10",
    }
    base.update(over)
    return base


def test_pallet_count_zero_modules():
    assert _mod.PanelLoadingCell._pallet_count(0, 60) == 0


def test_duplicate_and_empty_robot_dids_skipped():
    loader = "did:web:etzhayyim.com:sarutahiko#f10"
    out = _mod.PanelLoadingCell().solve(
        _base(
            loaderRobotDid=loader,
            attestingRobots=[
                {"robotDid": loader, "signature": "dup"},  # duplicate of mandatory loader → skip
                {"robotDid": "", "signature": "x"},          # empty DID → skip
                {"robotDid": "did:robot:mimi", "signature": "ok"},
            ],
        )
    )
    rec = out["loadingRecord"]
    dids = [r["robotDid"] for r in rec["attestingRobots"]]
    # loader present exactly once (the mandatory witness), the dup not doubled, empty gone
    assert dids.count(loader) == 1
    assert "did:robot:mimi" in dids
    assert "" not in dids


def test_bare_did_string_promoted_to_object():
    out = _mod.PanelLoadingCell().solve(_base(attestingRobots=["did:robot:otete"]))
    rec = out["loadingRecord"]
    promoted = [r for r in rec["attestingRobots"] if r["robotDid"] == "did:robot:otete"]
    assert len(promoted) == 1
    assert isinstance(promoted[0], dict) and "signature" in promoted[0]


if __name__ == "__main__":
    import sys

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
