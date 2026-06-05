"""Tests for kamado 竈 legacy→kotoba migration bridge (ADR-2606051500).

Run in isolation:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_ingest.py
"""
from __future__ import annotations

import json
import pathlib

import pytest

import ingest

SAMPLE = pathlib.Path(__file__).resolve().parent.parent / "data" / "ingest" / "legacy-oil-refining-export.sample.json"


def _export():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_sample_export_migrates_to_kotoba_eavt():
    ref, unit, outage = ingest.migrate(_export())
    assert len(ref) == 5 and len(unit) == 5 and len(outage) == 2
    assert ref["rf.jp.negishi"][":refinery/operator"] == "org.corp.eneos"
    assert ref["rf.jp.negishi"][":refinery/status"] == ":active"


def test_g4_observed_assets_are_never_operated():
    """G1/G4: migrated assets are :observed-fossil — observation, not a :synthesis record."""
    ref, _, _ = ingest.migrate(_export())
    for r in ref.values():
        assert r[":refinery/feedstock-class"] == ":observed-fossil"
        assert r[":refinery/sourcing"] == ":representative"  # G7 migrated, not authoritative


def test_g4_refuses_a_person_field():
    bad = {"Refinery": [{"refinery_code": "X-1", "country_code": "JP", "owner_person": "山田太郎"}]}
    with pytest.raises(ValueError, match="G4 violation"):
        ingest.migrate(bad)


def test_g4_refuses_non_org_operator():
    bad = {"Refinery": [{"refinery_code": "X-1", "country_code": "JP", "operator_org": "alice"}]}
    with pytest.raises(ValueError, match="G4 violation"):
        ingest.migrate(bad)


def test_kg_batch_shape_matches_live_kotobase_contract():
    """ai.gftd.apps.kotobase.kg.ingest {id, type?, label_*, claims?, relations?}."""
    ref, unit, outage = ingest.migrate(_export())
    batch = ingest.to_kg_batch(ref, unit, outage)
    assert len(batch["entities"]) == 12
    e0 = batch["entities"][0]
    assert set(e0) == {"id", "type", "label_en", "claims", "relations"}
    assert all("pred" in c and "value" in c for c in e0["claims"])
    # units carry a relation back to their refinery
    units = [e for e in batch["entities"] if e["type"] == "refinery-unit"]
    assert units and units[0]["relations"][0]["pred"] == "unit/refinery"


def test_push_refuses_without_jwt(monkeypatch):
    monkeypatch.delenv("KOTOBA_JWT", raising=False)
    with pytest.raises(SystemExit, match="G8"):
        ingest.main(["ingest.py", "--push"])


def test_live_migration_is_outward_gated(monkeypatch):
    monkeypatch.delenv("KAMADO_OPERATOR_GATE", raising=False)
    with pytest.raises(SystemExit, match="G8"):
        ingest.main(["ingest.py", "--live"])
