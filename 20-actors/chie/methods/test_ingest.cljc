(ns chie.methods.test-ingest
  "chie 智慧 — DISCLOSED-source ingest + G7 gate tests (ADR-2606171200). Verifies:
    - the fixture parses into disclosed records
    - ingest UPGRADES the representative round stubs to :authoritative + attaches the
      disclosed :ai/round-amount-usd, with :en/disclosed-src provenance on edges
    - idempotent: re-ingesting the same fixture adds nothing (no node/edge growth)
    - G7: ingest-live REFUSES without CHIE_INGEST_LIVE + operator DID (g7-violation?)
    - DISCLOSED amount is recorded as a fact (no valuation/score attr introduced)"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            #?(:clj [clojure.java.io :as io])
            [chie.methods.analyze :as analyze]
            [chie.methods.ingest :as ingest]))

#?(:clj (def actor-dir (-> *file* io/file .getParentFile .getParentFile)))
#?(:clj (def seed (io/file actor-dir "data" "seed-ai-ecosystem.kotoba.edn")))
#?(:clj (def fixture (io/file actor-dir "data" "ingest" "disclosed-rounds.fixture.edn")))

#?(:clj
   (deftest test-fixture-parses
     (let [recs (ingest/parse-disclosed (slurp fixture))]
       (is (= 4 (count recs)))
       (is (every? #(get % ":disclosed/round-id") recs))
       (is (every? #(get % ":disclosed/src") recs)))))

#?(:clj
   (deftest test-ingest-upgrades-rounds-to-authoritative
     (let [{:keys [graph upgraded]} (ingest/ingest-file seed fixture)
           openai-round (get-in graph [:nodes "ai.round.openai-2024"])]
       (is (= 4 upgraded) "all four representative round stubs upgraded")
       (is (= ":authoritative" (get openai-round ":organism/sourcing")))
       (is (= 6600000000 (get openai-round ":ai/round-amount-usd")))
       (testing "disclosed-src provenance lands on the round's structural edges"
         (let [prov (some #(when (and (= "ai.round.openai-2024" (get % ":en/from"))
                                      (get % ":en/disclosed-src"))
                             (get % ":en/disclosed-src"))
                          (:edges graph))]
           (is (string? prov)))))))

#?(:clj
   (deftest test-ingest-idempotent
     (let [g1 (:graph (ingest/ingest-file seed fixture))
           recs (ingest/parse-disclosed (slurp fixture))
           g2 (:graph (ingest/merge-graph g1 recs))]
       (is (= (count (:nodes g1)) (count (:nodes g2))) "re-ingest adds no nodes")
       (is (= (count (:edges g1)) (count (:edges g2))) "re-ingest adds no edges"))))

#?(:clj
   (deftest test-ingest-does-not-distort-concentration
     (testing "upgrading sourcing + amount leaves the edge-primary integrals unchanged"
       (let [base (analyze/analyze (:nodes (analyze/load-file* seed))
                                   (:edges (analyze/load-file* seed)))
             merged (:graph (ingest/ingest-file seed fixture))
             after (analyze/analyze (:nodes merged) (:edges merged))]
         ;; rounds connect via :partners (no axis) → OpenAI capital integral is identical
         (is (= (get-in base [:concentration "ai.lab.openai" :capital])
                (get-in after [:concentration "ai.lab.openai" :capital])))))))

#?(:clj
   (deftest test-g7-live-refused
     (testing "G7 — live ingest refused without the operator gate"
       (is (ingest/g7-violation?
            (try (ingest/ingest-live {:operator-did nil}) (catch Exception e e)))))))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'chie.methods.test-ingest)]
       (System/exit (if (pos? (+ (:fail r) (:error r))) 1 0)))))
