#!/usr/bin/env python3
"""business-manager — test harness (stdlib unittest; no kotoba host needed).

Verifies the structural invariants of ADR-2606072000:
  G2 double-entry-balanced — unbalanced entry rejected; balanced entry staged
  G6 approval-thresholds    — `approved` derived from amount (journal >1M JPY, PO >5M JPY)
  G4 no-server-key          — only a member signature posts
  G7 append-only            — postings carry appendOnly; trial balance nets to 0
  fiscal year               — JP Apr 1 - Mar 31 derivation
"""
import unittest

import agent


def _balanced_entry(debit, credit, **kw):
    base = dict(entryId="je-1", postedBy="did:plc:cfo",
                lines=[{"account": "5000", "debitMinor": debit, "creditMinor": 0},
                       {"account": "1000", "debitMinor": 0, "creditMinor": credit}])
    base.update(kw)
    return base


class FiscalYear(unittest.TestCase):
    def test_april_starts_new_fy(self):
        self.assertEqual(agent.fiscal_year_of("2026-04-01"), "FY2026")

    def test_march_is_prior_fy(self):
        self.assertEqual(agent.fiscal_year_of("2027-03-31"), "FY2026")


class DoubleEntry(unittest.TestCase):
    def test_balanced_true(self):
        self.assertTrue(agent.is_balanced([
            {"debitMinor": 500, "creditMinor": 0}, {"debitMinor": 0, "creditMinor": 500}]))

    def test_unbalanced_false(self):
        self.assertFalse(agent.is_balanced([
            {"debitMinor": 500, "creditMinor": 0}, {"debitMinor": 0, "creditMinor": 400}]))

    def test_single_line_false(self):
        self.assertFalse(agent.is_balanced([{"debitMinor": 500, "creditMinor": 0}]))

    def test_unbalanced_entry_rejected(self):
        e = _balanced_entry(50_000_00, 40_000_00)  # mismatched
        out = agent.post_journal_entry(e, "2026-05-01")
        self.assertEqual(out["state"], "rejected")
        self.assertIn("G2", out["reason"])


class Approval(unittest.TestCase):
    def test_journal_auto_approved_below_1m(self):
        e = _balanced_entry(500_000 * 100, 500_000 * 100)  # 500k JPY
        out = agent.post_journal_entry(e, "2026-05-01")
        self.assertEqual(out["state"], "staged")
        self.assertEqual(out["approved"], "auto-approved")

    def test_journal_approval_required_above_1m(self):
        e = _balanced_entry(2_000_000 * 100, 2_000_000 * 100)  # 2M JPY
        out = agent.post_journal_entry(e, "2026-05-01")
        self.assertEqual(out["approved"], "approval-required")

    def test_caller_cannot_self_approve(self):
        # approved is derived; any caller-supplied "approved" is ignored/overwritten
        e = _balanced_entry(2_000_000 * 100, 2_000_000 * 100, approved="auto-approved")
        out = agent.post_journal_entry(e, "2026-05-01")
        self.assertEqual(out["approved"], "approval-required")  # G6 derived, not trusted

    def test_po_threshold_5m(self):
        below = agent.post_purchase_order(
            {"poId": "po1", "vendor": "mitsuho", "amountMinor": 4_000_000 * 100, "postedBy": "did:plc:buyer"}, "2026-05-01")
        above = agent.post_purchase_order(
            {"poId": "po2", "vendor": "x", "amountMinor": 6_000_000 * 100, "postedBy": "did:plc:buyer"}, "2026-05-01")
        self.assertEqual(below["approved"], "auto-approved")
        self.assertEqual(above["approved"], "approval-required")


class Posting(unittest.TestCase):
    def setUp(self):
        self.staged = agent.post_journal_entry(_balanced_entry(100_000, 100_000), "2026-05-01")

    def test_member_signature_posts(self):
        out = agent.authorize_posting(self.staged, {"origin": "member", "ref": "sig-1"})
        self.assertEqual(out["state"], "posted")
        self.assertEqual(out["postedSig"], "sig-1")

    def test_server_signature_refused(self):
        out = agent.authorize_posting(self.staged, {"origin": "server", "ref": "x"})
        self.assertTrue(out["refused"])
        self.assertIn("G4", out["reason"])

    def test_missing_poster_rejected(self):
        e = _balanced_entry(100, 100, postedBy="")
        self.assertEqual(agent.post_journal_entry(e, "2026-05-01")["state"], "rejected")

    def test_append_only_flag(self):
        self.assertTrue(self.staged["appendOnly"])


class TrialBalance(unittest.TestCase):
    def test_ledger_nets_to_zero(self):
        es = [_balanced_entry(100, 100), _balanced_entry(250, 250)]
        tb = agent.trial_balance(es)
        self.assertTrue(tb["balanced"])
        self.assertEqual(tb["totalDebitMinor"], tb["totalCreditMinor"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
