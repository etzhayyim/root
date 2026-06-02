#!/usr/bin/env python3
"""supply_procurement — kotoba write-path tests (ADR-2606021200 / R1 maturation).

Covers SupplyProcurementCell._persist (the G6/G8 kotoba `kg.ingest_batch` of the
SBOM + provenance entities), skipped when datalog is None OR entities is empty.
Verifies host-present / empty / absent / raising branches + the ingest payload
shape (`{"entities": [...]}` JSON, never RW/SQL).
"""
import importlib.util
import json
import pathlib

_spec = importlib.util.spec_from_file_location(
    "himawari_supply_procurement_cell_w", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


class _FakeHost:
    def __init__(self):
        self.ingests = []

    def ingest_batch(self, payload):
        self.ingests.append(payload)


class _RaisingHost:
    def ingest_batch(self, *a, **k):
        raise RuntimeError("host ingest failure")


_ENTITIES = [
    {"id": "provenance/POLY-1", "type": "PolysiliconProvenanceAttestation", "claims": []},
    {"id": "sbom/COMP-1", "type": "SbomComponent", "claims": []},
]


def _restore():
    _mod.datalog = None


def test_persist_present_ingests_entities_payload():
    fake = _FakeHost()
    _mod.datalog = fake
    try:
        _mod.SupplyProcurementCell()._persist(_ENTITIES)
        assert len(fake.ingests) == 1, "host present + entities must ingest exactly once"
        payload = json.loads(fake.ingests[0])
        assert "entities" in payload and len(payload["entities"]) == 2
        assert payload["entities"][0]["id"] == "provenance/POLY-1"
    finally:
        _restore()


def test_persist_empty_entities_is_noop():
    fake = _FakeHost()
    _mod.datalog = fake
    try:
        _mod.SupplyProcurementCell()._persist([])
        assert fake.ingests == [], "empty entities must short-circuit before ingest"
    finally:
        _restore()


def test_persist_absent_is_noop():
    _mod.datalog = None
    assert _mod.SupplyProcurementCell()._persist(_ENTITIES) is None


def test_persist_host_failure_swallowed():
    _mod.datalog = _RaisingHost()
    try:
        assert _mod.SupplyProcurementCell()._persist(_ENTITIES) is None
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
