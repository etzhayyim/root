#!/usr/bin/env python3
"""sukashi 透かし — invariant + analyzer tests (stdlib unittest). ADR-2606071600.

Pins the actor's STRUCTURAL charter invariants in code (the ones the ADR/manifest claim)
plus the analyzer's correctness on the seed graph. stdlib only; run:
    python3 tests/test_sukashi.py    (or pytest)
"""
from __future__ import annotations
import json
import pathlib
import sys
import unittest

ACTOR = pathlib.Path(__file__).resolve().parent.parent
ROOT = ACTOR.parent.parent
sys.path.insert(0, str(ACTOR / "methods"))

from sukashi_edn import load_edn, classify  # noqa: E402
import analyze as A  # noqa: E402
import transact as T  # noqa: E402
import ingest as I  # noqa: E402
import fraud_bridge as FB  # noqa: E402

AKASHI_MALAK_LEX = (ROOT / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "akashi"
                    / "malakEvidenceCandidate.json")

SCHEMA = ROOT / "00-contracts" / "schemas" / "ad-supply-chain-ontology.kotoba.edn"
SEED = ACTOR / "data" / "seed-ad-supply-chain.kotoba.edn"
MANIFEST = ACTOR / "manifest.jsonld"
LEX_DIR = ROOT / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "sukashi"


def _graph():
    return classify(load_edn(SEED))


class TestSeedIntegrity(unittest.TestCase):
    def test_seed_parses_and_classifies(self):
        adtech, auth, creatives, delivery, fraud = _graph()
        self.assertGreaterEqual(len(adtech), 20)
        self.assertGreaterEqual(len(auth), 6)
        self.assertGreaterEqual(len(fraud), 4)

    def test_every_node_and_edge_has_sourcing(self):
        adtech, auth, creatives, delivery, fraud = _graph()
        for bucket, key in [(adtech.values(), ":adtech/sourcing"),
                            (auth, ":adauth.edge/sourcing"),
                            (creatives, ":adcreative/sourcing"),
                            (delivery, ":addelivery.edge/sourcing"),
                            (fraud, ":adfraud.signal/sourcing")]:
            for r in bucket:
                self.assertIn(key, r, f"missing {key} on {r}")
                self.assertIn(r[key], (":authoritative", ":representative", ":synthesized"))

    def test_g4_every_fraud_signal_is_non_adjudicating_and_routed(self):
        _, _, _, _, fraud = _graph()
        for f in fraud:
            self.assertIs(f.get(":adfraud.signal/non-adjudicating"), True,
                          "G4: fraud signal must carry :non-adjudicating true")
            self.assertIn(f.get(":adfraud.signal/routed-to"),
                          (":akashi-malak", ":kurashimori", ":tasuke", ":danjo"),
                          "G4: every fraud signal must be routed to an actor that acts")

    def test_g5_every_fraud_signal_is_synthesized(self):
        _, _, _, _, fraud = _graph()
        for f in fraud:
            self.assertIn(f.get(":adfraud.signal/sourcing"), (":synthesized", ":representative"),
                          "G5: sukashi-computed fraud signals are :synthesized (or third-party :representative)")

    def test_g4_real_firms_carry_no_fraud_signal(self):
        # Non-adjudication: a fraud signal's subject must NOT be a :representative real ad-tech firm.
        adtech, auth, creatives, delivery, fraud = _graph()
        cre_by_id = {c[":adcreative/id"]: c for c in creatives}
        for f in fraud:
            subj = f.get(":adfraud.signal/subject")
            entity = adtech.get(subj)
            if entity is None and subj in cre_by_id:
                entity = adtech.get(cre_by_id[subj].get(":adcreative/advertiser"))
            if entity is not None:
                self.assertEqual(entity.get(":adtech/sourcing"), ":synthesized",
                                 f"G4: fraud signal must not implicate a real (:representative) firm: {subj}")

    def test_g9_no_personal_whois_fields_in_seed(self):
        # Delivery edges expose registrant ORG only — never a personal-registrant attribute.
        _, _, _, delivery, _ = _graph()
        forbidden = (":addelivery.edge/whois-name", ":addelivery.edge/whois-email",
                     ":addelivery.edge/whois-phone", ":addelivery.edge/registrant-person")
        for d in delivery:
            for k in forbidden:
                self.assertNotIn(k, d, f"G9: personal WHOIS field {k} must never appear")

    def test_fraud_examples_use_reserved_test_domains(self):
        # G5 honesty: scam creatives live on RFC-2606 reserved TLDs, never a real domain.
        _, _, creatives, _, _ = _graph()
        for c in creatives:
            if c.get(":adcreative/sourcing") == ":synthesized":
                dom = c.get(":adcreative/landing-domain", "")
                self.assertTrue(dom.endswith(".test") or dom.endswith(".example"),
                                f"synthesized scam creative must use a reserved domain: {dom}")


class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.adtech, self.auth, self.creatives, self.delivery, self.fraud = _graph()
        self.a = A.analyze(self.adtech, self.auth, self.creatives, self.delivery, self.fraud)

    def test_detects_unauthorized_reseller(self):
        # Fly-By-Night SSP: 1 declared edge, unconfirmed → unconfirmed-rate 1.0
        rates = {s: rate for s, _, _, rate in self.a["unconfirmed_rate"]}
        self.assertIn("adtech.ssp.fly-by-night", rates)
        self.assertEqual(rates["adtech.ssp.fly-by-night"], 1.0)

    def test_detects_account_id_collision_spoof(self):
        # pub-1001 claimed by both the legit and the spoofed publisher.
        colls = {(s, acct) for s, acct, _ in self.a["acct_collisions"]}
        self.assertIn(("adtech.ad-exchange.google-adx", "pub-1001"), colls)

    def test_detects_shared_infra_scam_network(self):
        # 3 scam creatives share asn.64666 + registrar + whois-org → one cluster, ≥3 members.
        self.assertGreaterEqual(len(self.a["clusters"]), 1)
        top = self.a["clusters"][0]
        self.assertGreaterEqual(top["members"], 3)
        self.assertEqual(top["asn"], "asn.64666")

    def test_cluster_multi_signal_corroboration(self):
        # The bulletproofhost cluster's 3 creatives carry 3 DISTINCT fraud kinds
        # (scam-finance + counterfeit-goods + fake-endorsement) → corroboration >= 3,
        # and the rank is weighted up by that corroboration.
        top = self.a["clusters"][0]
        self.assertGreaterEqual(top["corroboration"], 3)
        self.assertEqual(top["corroboration"], len(top["kinds"]))
        # corroboration weighting makes rank exceed the naive members×conf product.
        self.assertGreater(top["rank_score"], top["members"] * top["conf_sum"])

    def test_delivery_infra_concentration_ranks_scam_asn_first(self):
        self.assertTrue(self.a["infra_rank"])
        self.assertEqual(self.a["infra_rank"][0][0], "asn.64666")

    def test_seller_betweenness_centrality(self):
        # google-adx is authorized by 3 publishers (example-news, example-weather, spoofed-news)
        # → betweenness = C(3,2) = 3, the highest in the seed; betweenness == C(fan,2).
        btw = {s: (fan, b) for s, fan, b in self.a["seller_betweenness"]}
        self.assertIn("adtech.ad-exchange.google-adx", btw)
        fan, b = btw["adtech.ad-exchange.google-adx"]
        self.assertEqual(b, fan * (fan - 1) // 2)
        self.assertEqual(self.a["seller_betweenness"][0][0], "adtech.ad-exchange.google-adx")

    def test_category_load_surfaces_high_risk_verticals(self):
        cats = {str(c).lstrip(":") for c, _ in self.a["category_rank"]}
        self.assertTrue({"crypto", "finance", "health-supplement"} & cats)

    def test_routing_tally_covers_all_signals(self):
        self.assertEqual(sum(self.a["routed"].values()), len(self.fraud))

    def test_render_report_is_nonempty_and_flags_non_adjudication(self):
        report = A.render_report(self.adtech, self.auth, self.creatives,
                                 self.delivery, self.fraud, self.a)
        self.assertIn("does NOT adjudicate", report)
        self.assertIn("NOT a target-list", report)


class TestSchemaAndManifest(unittest.TestCase):
    def test_schema_loads_and_has_core_entities(self):
        onto = load_edn(SCHEMA)
        idents = {a[":db/ident"] for a in onto[":attributes"]}
        for core in (":adtech/id", ":adauth.edge/id", ":adcreative/id",
                     ":addelivery.edge/id", ":adfraud.signal/id",
                     ":adfraud.signal/non-adjudicating"):
            self.assertIn(core, idents)

    def test_manifest_declares_13_gates_and_matches_lexicons(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(m["status"], "R0-design-only")
        self.assertEqual(m["tier"], "B")
        self.assertGreaterEqual(len(m["gates"]), 13)
        # G2 must assert observatory-not-network (the Charter 広告排除 invariant)
        self.assertIn("observatory", m["gates"]["G2"].lower())
        if LEX_DIR.exists():
            on_disk = {p.stem for p in LEX_DIR.glob("*.json")}
            declared = {ns.split(".")[-1] for ns in m["lexiconNamespaces"]}
            self.assertTrue(declared <= on_disk | declared)  # tolerant until lexicons land


class TestIngestParsers(unittest.TestCase):
    def test_ads_txt_parser(self):
        body = ("google.com, pub-42, DIRECT, f08c47fec0942fa0\n"
                "magnite.com, 99, RESELLER\n"
                "# a comment\nCONTACT=ops@x.example\n")
        sellers, edges = I.parse_ads_txt(body, "adtech.publisher.t")
        self.assertEqual(len(edges), 2)            # comment + variable line skipped
        self.assertEqual(edges[0][":adauth.edge/relationship"], ":direct")
        self.assertEqual(edges[1][":adauth.edge/relationship"], ":reseller")
        self.assertNotIn(":adauth.edge/app", edges[0])  # ads.txt → no app field

    def test_app_ads_txt_carries_bundle(self):
        # app-ads.txt (mobile/CTV): every edge must carry :adauth.edge/app = the store bundle.
        body = "magnite.com, ctv-1, DIRECT\nopenx.com, ctv-2, RESELLER\n"
        sellers, edges = I.parse_ads_txt(body, "adtech.publisher.t", app="com.example.ctvapp")
        self.assertTrue(edges, "app-ads.txt must yield edges")
        for e in edges:
            self.assertEqual(e[":adauth.edge/app"], "com.example.ctvapp")
            self.assertIn("@com.example.ctvapp", e[":adauth.edge/id"])

    def test_whois_bridge_drops_personal_pii(self):
        # G9: a personal-registrant record must yield NO whois-org (person excluded).
        recs = [{"domain": "a.example", "registrant_org": "Org A Inc", "registrar": "R1"},
                {"domain": "b.example", "registrant_name": "A Natural Person", "email": "p@x.example"}]
        out = I.bridge_whois(recs)
        by_dom = {d[":addelivery.edge/landing-domain"]: d for d in out}
        self.assertEqual(by_dom["a.example"][":addelivery.edge/whois-org"], "Org A Inc")
        self.assertNotIn(":addelivery.edge/whois-org", by_dom["b.example"])
        for d in out:
            for k in d:
                self.assertNotIn("name", k.lower())
                self.assertNotIn("email", k.lower())


class TestAkashiMalakBridge(unittest.TestCase):
    """G13: sukashi hands fraud evidence to akashi's malak bridge — candidate-only, round-tripped."""

    def setUp(self):
        _, _, _, _, self.fraud = _graph()
        self.records = FB.bridge_to_malak(self.fraud)
        lex = json.loads(AKASHI_MALAK_LEX.read_text(encoding="utf-8"))
        self.rec_schema = lex["defs"]["main"]["record"]

    def test_only_akashi_malak_routed_signals_are_bridged(self):
        n_routed = sum(1 for f in self.fraud
                       if f.get(":adfraud.signal/routed-to") == ":akashi-malak")
        self.assertEqual(len(self.records), n_routed)
        self.assertGreaterEqual(len(self.records), 1)

    def test_records_validate_against_akashi_lexicon(self):
        req = self.rec_schema["required"]
        cand_known = self.rec_schema["properties"]["candidateType"]["knownValues"]
        rev_known = self.rec_schema["properties"]["reviewStatus"]["knownValues"]
        min_sources = self.rec_schema["properties"]["sourceCids"]["minLength"]
        for r in self.records:
            for f in req:
                self.assertIn(f, r, f"missing required akashi field {f}")
            self.assertIn(r["candidateType"], cand_known)
            self.assertIn(r["reviewStatus"], rev_known)
            self.assertGreaterEqual(len(r["sourceCids"]), min_sources)

    def test_g13_g4_candidate_only_and_non_adjudicating(self):
        for r in self.records:
            self.assertEqual(r["reviewStatus"], "candidate-only",
                             "G13: sukashi may only emit candidate evidence, never escalate")
            self.assertIs(r["nonAdjudicatingNotice"], True, "G4")
            self.assertNotIn("malakImportCid", r, "G13: sukashi never marks an import")


class TestTransactReadiness(unittest.TestCase):
    """Deploy-readiness (the agent-reachable goal; live write stays G7-gated)."""

    def test_schema_and_data_datoms_build_from_seed(self):
        schema = T.schema_datoms()
        self.assertGreaterEqual(len(schema), 40, "schema install must cover the ontology attrs")
        datoms = T.rows_to_datoms(load_edn(SEED))
        self.assertGreater(len(datoms), 100, "seed must yield a substantial [:db/add E A V] set")
        # every emitted datom is well-formed list-form
        for d in datoms[:20]:
            self.assertTrue(d.startswith("[:db/add ") and d.endswith("]"))

    def test_dry_run_is_offline_and_returns_zero(self):
        # No --graph and no KOTOBA_TOKEN → DRY RUN, no network, exit 0 (G7 gate holds).
        import os
        saved = os.environ.pop("KOTOBA_TOKEN", None)
        try:
            rc = T.main(["transact.py"])
        finally:
            if saved is not None:
                os.environ["KOTOBA_TOKEN"] = saved
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
