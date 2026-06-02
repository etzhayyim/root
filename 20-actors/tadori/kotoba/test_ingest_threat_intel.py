#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import unittest

HERE = os.path.dirname(__file__)
SPEC = importlib.util.spec_from_file_location(
    "ingest_threat_intel", os.path.join(HERE, "ingest_threat_intel.py")
)
ingest = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ingest)


class TadoriThreatIntelIngestTest(unittest.TestCase):
    def test_seed_generates_lookup_ref_for_source_ref(self) -> None:
        records = ingest.load_jsonl(os.path.join(HERE, "seed.threat-intel.jsonl"))
        ingest.validate_records(records, allow_tier_d=False, live=False, case_id=None)
        datoms = [
            datom
            for record in records
            for datom in ingest.record_to_datoms(record, case_id="case:test")
        ]
        tx_edn = ingest.datoms_to_tx_edn(datoms)

        self.assertIn(
            '[:db/add "dns:sample.invalid:A:2026-06-02" :tadori.obs/source '
            '[:tadori.source/id "source:public-archive:ct-example"]]',
            tx_edn,
        )
        self.assertIn('[:db/add "indicator:domain:sample.invalid" :tadori.obs/source ', tx_edn)
        self.assertIn('[:db/add "dns:sample.invalid:A:2026-06-02" :tadori.obs/case-id "case:test"]', tx_edn)

    def test_live_write_requires_case_id(self) -> None:
        records = ingest.load_jsonl(os.path.join(HERE, "seed.threat-intel.jsonl"))
        for record in records:
            record.pop("case_id", None)

        with self.assertRaisesRegex(ingest.ValidationError, "live write requires case_id"):
            ingest.validate_records(records, allow_tier_d=False, live=True, case_id=None)

        ingest.validate_records(records, allow_tier_d=False, live=True, case_id="case:test")

    def test_vendor_compatible_source_cannot_be_system_of_record(self) -> None:
        records = [
            {
                "kind": "intel-source",
                "id": "source:vendor-compatible:securitytrails",
                "name": "SecurityTrails-shaped compatibility feed",
                "vendor_family": "securitytrails-compatible",
                "source_role": "system-of-record",
                "license_tier": "C",
            }
        ]

        with self.assertRaisesRegex(ingest.ValidationError, "vendor-compatible source cannot be system-of-record"):
            ingest.validate_records(records, allow_tier_d=False, live=False, case_id=None)

    def test_readback_checks_cover_all_record_kinds(self) -> None:
        records = ingest.load_jsonl(os.path.join(HERE, "seed.threat-intel.jsonl"))

        self.assertEqual(
            ingest.readback_checks(records),
            [
                ("source:public-archive:ct-example", "tadori.source/id"),
                ("source:vendor-compatible:securitytrails", "tadori.source/id"),
                ("dns:sample.invalid:A:2026-06-02", "tadori.dns/domain"),
                ("ip:192.0.2.10:2026-06-02", "tadori.ip/address"),
                ("indicator:domain:sample.invalid", "tadori.indicator/value"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
