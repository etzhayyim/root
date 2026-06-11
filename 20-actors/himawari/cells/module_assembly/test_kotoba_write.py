#!/usr/bin/env python3
"""module_assembly — kotoba write-path tests (ADR-2606021200 / R1 maturation).

Covers ModuleAssemblyCell._write_attestation (the `:himawari.module/*` write of
the finished-module attestation to canonical state), skipped when datalog is
None. Verifies host-present / absent / raising branches + the module-datom map.
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "himawari_module_assembly_cell_w", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


class _FakeHost:
    def __init__(self):
        self.transacts = []

    def transact(self, rows):
        self.transacts.append(rows)


class _RaisingHost:
    def transact(self, *a, **k):
        raise RuntimeError("host transact failure")


def _record(**over):
    r = {
        "moduleSerial": "HMW-MOD-0001",
        "cellBatchId": "CELL-2026-0602-001",
        "feedstockLotId": "POLY-2026-0602-001",
        "bomCid": "bafy-bom",
        "flashIvCid": "bafy-iv",
        "elImageCid": "bafy-el",
        "ratedWp": 420,
        "destinationActorDid": "did:web:etzhayyim.com:hikari",
        "provenanceChainDigest": "deadbeef",
        "signature": {"signedDigest": "sig-digest"},
        "recordedAt": "2026-06-02T00:00:00Z",
        "attestingNode": "asher",
    }
    r.update(over)
    return r


def _restore():
    _mod.datalog = None


def test_write_present_returns_true_and_module_map():
    fake = _FakeHost()
    _mod.datalog = fake
    try:
        ok = _mod.ModuleAssemblyCell._write_attestation(_record())
        assert ok is True
        assert len(fake.transacts) == 1
        rows = fake.transacts[0]
        assert isinstance(rows, list) and len(rows) == 1
        row = rows[0]
        assert row[":himawari.module/serial"] == "HMW-MOD-0001"
        assert row[":himawari.module/destination-did"] == "did:web:etzhayyim.com:hikari"
        assert row[":himawari.module/signed-digest"] == "sig-digest"
        assert row[":himawari.module/rated-wp"] == 420
    finally:
        _restore()


def test_write_absent_returns_false():
    _mod.datalog = None
    assert _mod.ModuleAssemblyCell._write_attestation(_record()) is False


def test_write_host_failure_returns_false():
    _mod.datalog = _RaisingHost()
    try:
        assert _mod.ModuleAssemblyCell._write_attestation(_record()) is False
    finally:
        _restore()


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
