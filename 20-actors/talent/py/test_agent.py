#!/usr/bin/env python3
"""talent — test harness (stdlib unittest; no kotoba host needed).

Verifies the structural invariants of ADR-2606072600:
  G1 self-sovereign       — third-party register refused; prohibited source ingest refused
  G3 signal-e2e           — plaintext identifying field refused; ciphertext accepted
  G2 cohort-first k-anon  — cohort below k suppressed; ≥k returns aggregate only
  G4 hard-delete          — forget_self removes the profile entirely (no soft-delete flag)
"""
import unittest

import agent

ALICE = "did:plc:alice"
BOB = "did:plc:bob"


def _profile(**kw):
    base = dict(isco="2512", country="JP", skills=["python", "rust"])
    base.update(kw)
    return base


class SelfSovereign(unittest.TestCase):
    def test_self_register_ok(self):
        out = agent.register_self(ALICE, ALICE, _profile())
        self.assertEqual(out["state"], "registered")
        self.assertEqual(out["profile"]["registeredBy"], ALICE)
        self.assertEqual(out["profile"]["subjectDidHash"], agent.subject_hash(ALICE))

    def test_third_party_refused(self):
        out = agent.register_self(BOB, ALICE, _profile())  # caller != subject
        self.assertEqual(out["state"], "refused")
        self.assertIn("G1", out["reason"])

    def test_prohibited_source_ingest_refused(self):
        for src in ("linkedin", "indeed", "scraped-db", "purchased-list"):
            self.assertEqual(agent.ingest_external(src)["state"], "refused")

    def test_allowed_enrichment(self):
        self.assertEqual(agent.ingest_external("orcid")["state"], "allowed")

    def test_prohibited_enrichment_on_profile_refused(self):
        out = agent.register_self(ALICE, ALICE, _profile(enrichmentSource="linkedin"))
        self.assertEqual(out["state"], "refused")


class SignalE2E(unittest.TestCase):
    def test_plaintext_pii_refused(self):
        out = agent.register_self(ALICE, ALICE, _profile(email="alice@example.com"))
        self.assertEqual(out["state"], "refused")
        self.assertIn("G3", out["reason"])

    def test_ciphertext_pii_ok(self):
        out = agent.register_self(ALICE, ALICE, _profile(email="signal:v1:deadbeef"))
        self.assertEqual(out["state"], "registered")

    def test_is_encrypted(self):
        self.assertTrue(agent.is_encrypted("signal:v1:abc"))
        self.assertFalse(agent.is_encrypted("plain"))


class CohortKAnon(unittest.TestCase):
    def test_below_k_suppressed(self):
        profiles = [_profile() for _ in range(3)]  # k default 5
        out = agent.cohort_stats("2512", "JP", profiles)
        self.assertTrue(out["suppressed"])
        self.assertIsNone(out["count"])

    def test_at_or_above_k_aggregate(self):
        profiles = [_profile() for _ in range(5)]
        out = agent.cohort_stats("2512", "JP", profiles)
        self.assertFalse(out["suppressed"])
        self.assertEqual(out["count"], 5)
        self.assertIn("python", out["topSkills"])

    def test_no_individual_field_in_output(self):
        profiles = [_profile(email="signal:v1:x") for _ in range(6)]
        out = agent.cohort_stats("2512", "JP", profiles)
        for k in out:
            self.assertNotIn("email", k.lower())
            self.assertNotIn("profile", k.lower())
            self.assertNotIn("name", k.lower())


class HardDelete(unittest.TestCase):
    def setUp(self):
        self.store = [
            {"subjectDidHash": agent.subject_hash(ALICE), "isco": "2512"},
            {"subjectDidHash": agent.subject_hash(BOB), "isco": "2512"},
        ]

    def test_forget_removes_entirely(self):
        out = agent.forget_self(ALICE, ALICE, self.store)
        self.assertEqual(out["state"], "forgotten")
        self.assertEqual(out["hardDeleted"], 1)
        hashes = [p["subjectDidHash"] for p in out["store"]]
        self.assertNotIn(agent.subject_hash(ALICE), hashes)         # gone, not flagged
        for p in out["store"]:
            self.assertNotIn("_alive", p)                           # no soft-delete flag (G4)

    def test_forget_others_refused(self):
        out = agent.forget_self(BOB, ALICE, self.store)
        self.assertEqual(out["state"], "refused")


class Enrichment(unittest.TestCase):
    def _prof(self):
        return {"isco": "2512", "country": "JP", "skills": ["python"]}

    def test_self_enrich_merges_skills(self):
        out = agent.attach_enrichment(ALICE, ALICE, self._prof(), "github-public", {"skills": ["rust", "python"]})
        self.assertEqual(out["state"], "enriched")
        self.assertEqual(sorted(out["profile"]["skills"]), ["python", "rust"])  # deduped union
        self.assertEqual(out["profile"]["enrichmentProvenance"], ["github-public"])

    def test_third_party_enrich_refused(self):
        out = agent.attach_enrichment(BOB, ALICE, self._prof(), "orcid", {"skills": ["x"]})
        self.assertEqual(out["state"], "refused")
        self.assertIn("G1", out["reason"])

    def test_prohibited_source_refused(self):
        out = agent.attach_enrichment(ALICE, ALICE, self._prof(), "linkedin", {"skills": ["x"]})
        self.assertEqual(out["state"], "refused")

    def test_plaintext_pii_enrichment_refused(self):
        out = agent.attach_enrichment(ALICE, ALICE, self._prof(), "orcid", {"email": "a@b.com"})
        self.assertEqual(out["state"], "refused")
        self.assertIn("G3", out["reason"])


class ListOccupations(unittest.TestCase):
    def test_below_k_cohort_not_listed(self):
        profiles = [{"isco": "2512", "country": "JP", "skills": []} for _ in range(3)]  # k=5
        self.assertEqual(agent.list_occupations(profiles), [])   # not even disclosed (G2)

    def test_at_or_above_k_listed(self):
        profiles = ([{"isco": "2512", "country": "JP"} for _ in range(5)] +
                    [{"isco": "2512", "country": "US"} for _ in range(2)])  # US below k
        out = agent.list_occupations(profiles)
        self.assertEqual(out, [{"isco": "2512", "country": "JP", "count": 5}])  # only JP


if __name__ == "__main__":
    unittest.main(verbosity=2)
