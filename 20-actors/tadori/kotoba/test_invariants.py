#!/usr/bin/env python3
"""tadori 辿 — gate / charter-invariant tests for the threat-intel ingest.

    python3 test_invariants.py
    python3 -m pytest test_invariants.py

Complements test_ingest_threat_intel.py (seed round-trip + SoR/case-id gates) with the
remaining load-bearing gates: tadori ingests ONLY operator-staged passive archives
(authorized, non-probing), Tier-D vendor data is gated and never system-of-record,
observations must reference a declared source, confidence is bounded, EDN is
injection-safe, and the encrypted-PII flag survives to the Datom log (ADR-2605181100).
"""
from __future__ import annotations

import importlib.util
import os
import unittest

HERE = os.path.dirname(__file__)
SPEC = importlib.util.spec_from_file_location(
    "ingest_threat_intel", os.path.join(HERE, "ingest_threat_intel.py"))
ingest = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ingest)


def _source(tier="A", role="enrichment", family="public-archive"):
    return {"kind": "intel-source", "id": f"source:{family}:x", "name": "X",
            "vendor_family": family, "source_role": role, "license_tier": tier}


def _dns(source="source:public-archive:x", **over):
    rec = {"kind": "dns-obs", "id": "dns:sample.invalid:A:2026-06-02", "source": source,
           "collection_mode": "operator-staged-passive-archive",
           "domain": "sample.invalid", "rrtype": "A", "rrdata": "192.0.2.10"}
    rec.update(over)
    return rec


class TadoriGateTest(unittest.TestCase):
    def test_invalid_kind_rejected(self):
        with self.assertRaisesRegex(ingest.ValidationError, "invalid kind"):
            ingest.validate_records([{"kind": "wallet-trace", "id": "x"}],
                                    allow_tier_d=False, live=False, case_id=None)

    def test_collection_must_be_passive_archive(self):
        # the anti-active-probing invariant: only operator-staged passive archives ingest
        bad = _dns(collection_mode="active-scan")
        with self.assertRaisesRegex(ingest.ValidationError, "operator-staged-passive-archive"):
            ingest.validate_records([_source(), bad], allow_tier_d=False, live=False, case_id=None)

    def test_tier_d_requires_explicit_flag_and_stays_non_sor(self):
        recs = [_source(tier="D")]
        with self.assertRaisesRegex(ingest.ValidationError, "Tier-D"):
            ingest.validate_records(recs, allow_tier_d=False, live=False, case_id=None)
        # with the flag it validates (and the source is enrichment, never SoR)
        ingest.validate_records(recs, allow_tier_d=True, live=False, case_id=None)

    def test_observation_must_reference_declared_source(self):
        orphan = _dns(source="source:public-archive:undeclared")
        with self.assertRaisesRegex(ingest.ValidationError, "undeclared source"):
            ingest.validate_records([orphan], allow_tier_d=False, live=False, case_id=None)

    def test_confidence_is_bounded(self):
        with self.assertRaisesRegex(ingest.ValidationError, "confidence"):
            ingest.validate_records([_source(), _dns(confidence=2000)],
                                    allow_tier_d=False, live=False, case_id=None)
        ingest.validate_records([_source(), _dns(confidence=750)],
                                allow_tier_d=False, live=False, case_id=None)

    def test_edn_string_is_injection_safe(self):
        # a value containing a quote/backslash must be escaped, not break the tx EDN
        s = ingest.edn_string('evil" :db/add hax \\ end')
        assert s.startswith('"') and s.endswith('"')
        assert '\\"' in s and '\\\\' in s

    def test_encrypted_pii_flag_survives_to_datoms(self):
        datoms = ingest.record_to_datoms(_dns(encrypted=True), case_id="case:t")
        assert any("tadori.obs/encrypted" in d and "true" in d for d in datoms)

    def test_case_id_binds_observation_for_audit(self):
        # every observation carries its case-id (consent/authorization audit anchor)
        datoms = ingest.record_to_datoms(_dns(), case_id="case:authz-123")
        assert any('tadori.obs/case-id "case:authz-123"' in d for d in datoms)


if __name__ == "__main__":
    unittest.main()
