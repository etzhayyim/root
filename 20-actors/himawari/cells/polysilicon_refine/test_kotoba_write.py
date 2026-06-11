#!/usr/bin/env python3
"""polysilicon_refine — kotoba write-path tests (ADR-2606021200 / R1 maturation).

The existing test_cell.py exercises solve() with `datalog is None`, so the
`_write_provenance` EAVT projection (the G2/G8 on-chain provenance write) was
entirely uncovered. These tests inject a fake kotoba host and verify the three
branches of the write path that the substrate boundary depends on:

  - host present  → genuine EAVT datoms transacted, returns datom count,
                    attribute namespace matches the himawari kotoba schema,
                    chain-of-custody hops + robot-quorum fan out correctly
  - host absent   → no-op (returns 0, never a fake success)
  - host raises   → swallowed, returns 0 (never fabricates a write — honesty gate)
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "himawari_polysilicon_refine_cell_w", pathlib.Path(__file__).parent / "cell.py"
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


def _provenance(**over):
    p = {
        "lotId": "POLY-2026-0602-001",
        "recordedAt": "2026-06-02T00:00:00Z",
        "feedstockGrade": "solar-grade-6N",
        "process": "siemens",
        "declaredOrigin": "Norway",
        "supplierDid": "did:web:example.com:supplier",
        "originRegionAttestationCid": "bafy-origin",
        "sourcingAuditCid": "bafy-audit",
        "attestingEngineerDid": "did:web:etzhayyim.com:himawari#eng-01",
        "embodiedEnergyWhPerKg": 70000,
        "qaVerdict": "accepted",
        "chainOfCustodyCid": "bafy-chain",
        "chainOfCustody": [
            {"stage": "quarry", "custodianDid": "did:q", "regionCode": "NO", "evidenceCid": "bafy-q"}
        ],
        "attestingRobots": [
            {"robotDid": "did:robot:mimi", "signature": "sig-a"},
            {"robotDid": "did:robot:otete", "signature": "sig-b"},
        ],
    }
    p.update(over)
    return p


def _restore():
    # tests mutate the module global; leave it None (local-dev default) on exit
    _mod.datalog = None


def test_write_present_returns_datom_count_and_namespace():
    fake = _FakeHost()
    _mod.datalog = fake
    try:
        n = _mod.PolysiliconRefineCell()._write_provenance(_provenance())
        # 12 base + 5 per custody hop (×1) + 2 per robot sig (×2) = 21
        assert n == 21, f"expected 21 datoms, got {n}"
        assert len(fake.transacts) == 1, "transact must be called exactly once"
        datoms = fake.transacts[0]
        assert isinstance(datoms, list) and len(datoms) == 21
        attrs = {d[1] for d in datoms}
        assert ":himawari.polysilicon/lot-id" in attrs
        assert ":himawari.polysilicon/qa-verdict" in attrs
        assert ":himawari.polysilicon/custody-hop" in attrs
        assert ":himawari.custody-hop/stage" in attrs
        assert ":himawari.polysilicon/attesting-robot-signature" in attrs
        # every datom is a well-formed [entity, attr, value] triple
        for d in datoms:
            assert len(d) == 3 and all(isinstance(d[i], str) for i in (0, 1))
    finally:
        _restore()


def test_write_absent_is_noop():
    _mod.datalog = None
    n = _mod.PolysiliconRefineCell()._write_provenance(_provenance())
    assert n == 0, "no host binding must be a no-op returning 0 (no fake success)"


def test_write_host_failure_swallowed():
    _mod.datalog = _RaisingHost()
    try:
        n = _mod.PolysiliconRefineCell()._write_provenance(_provenance())
        assert n == 0, "a raising host must not fabricate a successful write"
    finally:
        _restore()


def test_write_scales_with_hops_and_robots():
    fake = _FakeHost()
    _mod.datalog = fake
    try:
        prov = _provenance(
            chainOfCustody=[
                {"stage": "quarry", "custodianDid": "did:q", "regionCode": "NO", "evidenceCid": "c1"},
                {"stage": "refine", "custodianDid": "did:r", "regionCode": "NO", "evidenceCid": "c2"},
            ],
            attestingRobots=[{"robotDid": "did:robot:mimi", "signature": "s"}],
        )
        n = _mod.PolysiliconRefineCell()._write_provenance(prov)
        # 12 base + 5×2 hops + 2×1 robot = 24
        assert n == 24, f"expected 24 datoms, got {n}"
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
