#!/usr/bin/env python3
"""organizer — test harness (stdlib unittest; no kotoba host needed).

Verifies the structural invariants of ADR-2606072400:
  G4 content-addressed dedup — identical Blake3 in a vault → one item (deduped)
  G3 vault-isolation         — cross-vault read refused
  G2 no-mining               — classification has no profile/ad field; labels owner-facing
  G6 no-server-key           — only a member signature finalizes upload
  auto-organize              — organize-rule maps category → collection
"""
import unittest

import agent

VA = "did:web:organizer.etzhayyim.com:vault:alice"
VB = "did:web:organizer.etzhayyim.com:vault:bob"


def _ingest(vault, blake3, fn="doc.pdf", ct="application/pdf", existing=None):
    return agent.ingest_item(vault, blake3, "com.etzhayyim.encrypted:blob1", fn, ct, 1024,
                             "did:plc:alice", existing or [])


class Dedup(unittest.TestCase):
    def test_content_addressed_id(self):
        self.assertEqual(agent.content_item_id("abcdef0123456789ff"), "cid.abcdef0123456789")

    def test_new_item_staged(self):
        out = _ingest(VA, "a" * 40)
        self.assertEqual(out["state"], "staged")
        self.assertFalse(out["deduped"])

    def test_identical_content_dedups(self):
        existing = [{"vaultDid": VA, "blake3": "a" * 40, "itemId": "cid.aaaaaaaaaaaaaaaa"}]
        out = _ingest(VA, "a" * 40, existing=existing)
        self.assertTrue(out["deduped"])
        self.assertEqual(out["item"]["itemId"], "cid.aaaaaaaaaaaaaaaa")

    def test_same_content_different_vault_not_deduped(self):
        existing = [{"vaultDid": VB, "blake3": "a" * 40, "itemId": "x"}]
        out = _ingest(VA, "a" * 40, existing=existing)   # different vault → own copy (G3)
        self.assertFalse(out["deduped"])


class Upload(unittest.TestCase):
    def test_member_finalizes(self):
        staged = _ingest(VA, "b" * 40)
        out = agent.authorize_upload(staged, {"origin": "member", "ref": "sig-1"})
        self.assertEqual(out["state"], "stored")
        self.assertEqual(out["item"]["postedSig"], "sig-1")

    def test_server_signature_refused(self):
        staged = _ingest(VA, "b" * 40)
        out = agent.authorize_upload(staged, {"origin": "server", "ref": "x"})
        self.assertTrue(out["refused"])
        self.assertIn("G6", out["reason"])


class Classify(unittest.TestCase):
    def test_pdf_is_document(self):
        c = agent.classify({"itemId": "i", "vaultDid": VA, "filename": "a.pdf", "contentType": "application/pdf"})
        self.assertEqual(c["category"], "document")
        self.assertEqual(c["source"], "rule")

    def test_extension_fallback(self):
        c = agent.classify({"itemId": "i", "vaultDid": VA, "filename": "pic.png", "contentType": "application/octet-stream"})
        self.assertEqual(c["category"], "image")

    def test_receipt_label(self):
        c = agent.classify({"itemId": "i", "vaultDid": VA, "filename": "receipt-202605.pdf", "contentType": "application/pdf"})
        self.assertIn("receipt", c["labels"])

    def test_no_profile_or_ad_field(self):
        c = agent.classify({"itemId": "i", "vaultDid": VA, "filename": "a.pdf", "contentType": "application/pdf"})
        for k in c:
            self.assertNotIn("profile", k.lower())
            self.assertNotIn("ad", k.lower().replace("addr", ""))
        self.assertEqual(c["vaultDid"], VA)   # stays in owner's vault (G2/G3)


class Organize(unittest.TestCase):
    def test_rule_assigns_collection(self):
        cls = {"itemId": "i", "vaultDid": VA, "category": "image", "labels": ["image"]}
        rules = [{"id": "r1", "condition": {"category": "image"}, "collection": "Photos", "priority": 5}]
        out = agent.apply_rules(cls, rules)
        self.assertEqual(out["collection"], "Photos")

    def test_no_rule_no_force(self):
        cls = {"itemId": "i", "vaultDid": VA, "category": "archive", "labels": ["archive"]}
        self.assertIsNone(agent.apply_rules(cls, [{"id": "r1", "condition": {"category": "image"}, "collection": "Photos"}]))


class VaultIsolation(unittest.TestCase):
    def test_owner_reads(self):
        self.assertEqual(agent.read_item({"vaultDid": VA}, VA)["state"], "ok")

    def test_cross_vault_refused(self):
        out = agent.read_item({"vaultDid": VA}, VB)
        self.assertEqual(out["state"], "refused")
        self.assertIn("G3", out["reason"])


class CollectionMembership(unittest.TestCase):
    def _coll(self, vault=VA):
        return {"collectionId": "c1", "vaultDid": vault, "name": "Docs", "members": []}

    def _item(self, vault=VA, iid="cid.x"):
        return {"itemId": iid, "vaultDid": vault}

    def test_add_same_vault(self):
        out = agent.add_to_collection(self._coll(), self._item())
        self.assertEqual(out["state"], "ok")
        self.assertIn("cid.x", out["collection"]["members"])

    def test_add_cross_vault_refused(self):
        out = agent.add_to_collection(self._coll(VA), self._item(VB))
        self.assertEqual(out["state"], "refused")
        self.assertIn("G3", out["reason"])

    def test_add_idempotent(self):
        c = agent.add_to_collection(self._coll(), self._item())["collection"]
        c2 = agent.add_to_collection(c, self._item())["collection"]
        self.assertEqual(c2["members"].count("cid.x"), 1)

    def test_remove_is_noop_for_nonmember(self):
        out = agent.remove_from_collection(self._coll(), "cid.absent")
        self.assertEqual(out["collection"]["members"], [])

    def test_remove_member(self):
        c = agent.add_to_collection(self._coll(), self._item())["collection"]
        out = agent.remove_from_collection(c, "cid.x")
        self.assertEqual(out["collection"]["members"], [])


class AutoOrganize(unittest.TestCase):
    def test_batch_assigns_by_vault_rule(self):
        items = [
            {"itemId": "cid.1", "vaultDid": VA, "filename": "a.pdf", "contentType": "application/pdf"},
            {"itemId": "cid.2", "vaultDid": VA, "filename": "p.png", "contentType": "image/png"},
        ]
        collections = [
            {"collectionId": "Docs", "vaultDid": VA, "autoRules": [{"id": "r1", "condition": {"category": "document"}}]},
            {"collectionId": "Photos", "vaultDid": VA, "autoRules": [{"id": "r2", "condition": {"category": "image"}}]},
        ]
        out = agent.auto_organize(items, collections)
        got = {a["itemId"]: a["collection"] for a in out}
        self.assertEqual(got, {"cid.1": "Docs", "cid.2": "Photos"})

    def test_does_not_cross_vault(self):
        items = [{"itemId": "cid.1", "vaultDid": VA, "filename": "a.pdf", "contentType": "application/pdf"}]
        collections = [{"collectionId": "Docs", "vaultDid": VB, "autoRules": [{"id": "r1", "condition": {"category": "document"}}]}]
        self.assertEqual(agent.auto_organize(items, collections), [])   # VB collection not used for VA item (G3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
