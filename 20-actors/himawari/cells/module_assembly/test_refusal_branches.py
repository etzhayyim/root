#!/usr/bin/env python3
"""module_assembly — G11/G12 refusal + provenance-query coverage (R1 maturation).

test_cell.py covers the happy path and the missing-lot/missing-batch refusals,
but left these constitutional branches uncovered:

  - G12 external destination refused / empty destination refused
  - G11 flash-bin when rated Wp <= 0
  - G11 `_lot_exists` live-host provenance query (the fail-closed Datom check):
        host confirms lot → accept; host returns empty → refuse (phantom lot);
        host query raises → fail-closed refuse (never silently passes provenance)
"""
import importlib.util
import pathlib
import sys

_MOD_NAME = "himawari_module_assembly_cell_r"
_spec = importlib.util.spec_from_file_location(
    _MOD_NAME, pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_MOD_NAME] = _mod
_spec.loader.exec_module(_mod)

_FLASH = {"isc": 11.2, "voc": 49.5, "pmax": 442, "ff": 0.79}
_EL = {"cid": "cid:el:sha256:cafe", "cracks": 0}


def _good(**over):
    base = {
        "moduleSerial": "HMW-2026-000123",
        "cellBatchId": "CELL-B-0042",
        "feedstockLotId": "POLY-LOT-0007",
        "bomCid": "cid:sbom:sha256:deadbeef",
        "ratedWp": 440,
        "measuredWp": 442,
        "recordedAt": "2026-06-02T12:00:00Z",
        "flashIv": _FLASH,
        "elImage": _EL,
        "destinationActorDid": "did:web:etzhayyim.com:hikari",
        "attestingRobots": ["otete", "mimi"],
        "epbtMonths": 14,
        "recyclabilityBps": 9200,
    }
    base.update(over)
    return base


class _Host:
    def __init__(self, rows):
        self._rows = rows

    def query(self, *a, **k):
        return self._rows


class _RaisingHost:
    def query(self, *a, **k):
        raise RuntimeError("datom query failure")


def _restore():
    _mod.datalog = None


def test_g12_external_destination_refused():
    out = _mod.ModuleAssemblyCell().solve(_good(destinationActorDid="did:web:commercial-buyer.com"))
    assert out["refused"] is True
    assert "G12" in out["reason"]


def test_g12_empty_destination_refused():
    out = _mod.ModuleAssemblyCell().solve(_good(destinationActorDid=""))
    assert out["refused"] is True
    assert "destination" in out["reason"]


def test_flash_bin_when_rated_wp_zero():
    out = _mod.ModuleAssemblyCell().solve(_good(ratedWp=0, measuredWp=0))
    # rated_wp <= 0 is itself a bin (G11) — module is binned, not a clean emit
    assert out.get("binned") is True


def test_lot_exists_host_confirms_accepts():
    _mod.datalog = _Host(rows=[["POLY-LOT-0007"]])
    try:
        out = _mod.ModuleAssemblyCell().solve(_good())
        assert out.get("refused") is not True, "host-confirmed lot must not be refused"
        assert out["provenance"]["complete"] is True
    finally:
        _restore()


def test_lot_exists_host_empty_refuses_phantom_lot():
    _mod.datalog = _Host(rows=[])
    try:
        out = _mod.ModuleAssemblyCell().solve(_good())
        assert out["refused"] is True
        assert "not found in provenance log" in out["reason"]
    finally:
        _restore()


def test_lot_exists_query_failure_is_fail_closed():
    _mod.datalog = _RaisingHost()
    try:
        out = _mod.ModuleAssemblyCell().solve(_good())
        # a query failure must refuse (fail-closed G11), never silently pass
        assert out["refused"] is True
        assert "not found in provenance log" in out["reason"]
    finally:
        _restore()


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
