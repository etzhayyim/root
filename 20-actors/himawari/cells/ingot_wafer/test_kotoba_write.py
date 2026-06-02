#!/usr/bin/env python3
"""ingot_wafer — kotoba write-path tests (ADR-2606021200 / R1 maturation).

Covers IngotWaferCell._transact (the `:wafer.batch/*` EAVT projection), which
is skipped whenever `datalog is None`. Verifies host-present / absent / raising
branches and the attribute namespace + per-robot fan-out.
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "himawari_ingot_wafer_cell_w", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


class _FakeHost:
    def __init__(self):
        self.transacts = []

    def transact(self, facts):
        self.transacts.append(facts)


class _RaisingHost:
    def transact(self, *a, **k):
        raise RuntimeError("host transact failure")


def _record(**over):
    r = {
        "batchId": "WAF-2026-0602-001",
        "polysiliconLotId": "POLY-2026-0602-001",
        "ingotMethod": "czochralski",
        "waferCount": 5000,
        "waferThicknessUm": 160,
        "kerfRecoveredGrams": 1200,
        "yieldBps": 9700,
        "processEnergyWh": 250000,
        "attestingRobots": [{"robotDid": "did:robot:mimi"}, {"robotDid": "did:robot:otete"}],
    }
    r.update(over)
    return r


def _restore():
    _mod.datalog = None


def test_transact_present_returns_true_and_namespace():
    fake = _FakeHost()
    _mod.datalog = fake
    try:
        ok = _mod.IngotWaferCell._transact(_record())
        assert ok is True, "host present must report a successful transact"
        assert len(fake.transacts) == 1
        facts = fake.transacts[0]
        attrs = {f[1] for f in facts}
        assert ":wafer.batch/id" in attrs
        assert ":wafer.batch/polysilicon-lot-id" in attrs
        assert ":wafer.batch/kerf-recovered-grams" in attrs
        # 8 base facts + 1 per attesting robot (×2) = 10
        assert len(facts) == 10, f"expected 10 facts, got {len(facts)}"
        robot_facts = [f for f in facts if f[1] == ":wafer.batch/attesting-robot"]
        assert len(robot_facts) == 2
    finally:
        _restore()


def test_transact_absent_returns_false():
    _mod.datalog = None
    assert _mod.IngotWaferCell._transact(_record()) is False


def test_transact_host_failure_returns_false():
    _mod.datalog = _RaisingHost()
    try:
        assert _mod.IngotWaferCell._transact(_record()) is False
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
