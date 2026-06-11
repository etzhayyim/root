#!/usr/bin/env python3
"""panel_loading — kotoba write-path tests (ADR-2606021200 / R1 maturation).

Covers PanelLoadingCell._write_kotoba (the `:loading/*` EAVT projection of the
loadingRecord), skipped when datalog is None. Verifies host-present / absent /
raising branches + per-serial and per-robot fan-out.
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "himawari_panel_loading_cell_w", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


class _FakeHost:
    def __init__(self):
        self.transacts = []

    def transact(self, datoms):
        self.transacts.append(datoms)


class _RaisingHost:
    def transact(self, *a, **k):
        raise RuntimeError("host transact failure")


def _record(**over):
    r = {
        "loadingId": "load-2026-0602-001",
        "recordedAt": "2026-06-02T00:00:00Z",
        "palletCount": 3,
        "carrierDid": "did:web:etzhayyim.com:hikari#carrier-01",
        "loaderRobotDid": "did:web:etzhayyim.com:sarutahiko#f10",
        "humanTasksRemovedCid": "bafy-liberation",
        "cycleStateLogCid": "bafy-cycle",
        "moduleSerials": ["HMW-MOD-0001", "HMW-MOD-0002", "HMW-MOD-0003"],
        "attestingRobots": [{"robotDid": "did:robot:mimi"}, {"robotDid": "did:robot:otete"}],
    }
    r.update(over)
    return r


def _restore():
    _mod.datalog = None


def test_write_present_namespace_and_fanout():
    fake = _FakeHost()
    _mod.datalog = fake
    try:
        _mod.PanelLoadingCell._write_kotoba(_record())
        assert len(fake.transacts) == 1
        datoms = fake.transacts[0]
        attrs = {d[1] for d in datoms}
        assert ":loading/id" in attrs
        assert ":loading/carrier-did" in attrs
        assert ":loading/human-tasks-removed-cid" in attrs
        serial_datoms = [d for d in datoms if d[1] == ":loading/module-serial"]
        robot_datoms = [d for d in datoms if d[1] == ":loading/attesting-robot-did"]
        assert len(serial_datoms) == 3, "one datom per module serial"
        assert len(robot_datoms) == 2, "one datom per attesting robot"
        # entity id is namespaced by the loading id
        assert all(d[0] == "loading:load-2026-0602-001" for d in datoms)
    finally:
        _restore()


def test_write_absent_is_noop():
    _mod.datalog = None
    # returns None and must not raise
    assert _mod.PanelLoadingCell._write_kotoba(_record()) is None


def test_write_host_failure_swallowed():
    _mod.datalog = _RaisingHost()
    try:
        # a raising host must be swallowed (no exception escapes), returns None
        assert _mod.PanelLoadingCell._write_kotoba(_record()) is None
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
