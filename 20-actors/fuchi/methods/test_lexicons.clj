;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/fuchi/methods/test_lexicons.py (unit_refactor stage 0)
;; Lexicon well-formedness tests for 扶持 (fuchi) — all 5 com.etzhayyim.fuchi.* lexicons.
(ns root.fuchi.methods.test-lexicons
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare lex test-all-five-lexicons-present test-each-lexicon-well-formed test-namespace-prefix-is-fuchi run)

;; TODO: port-failed unit _LEX (bb-compile error)
;; _LEX = pathlib.Path(__file__).resolve().parents[1] / "lex"
;; EXPECTED = {
;;     "maintainerCovenant.edn": "com.etzhayyim.fuchi.maintainerCovenant",
;;     "sustenanceEnvelope.edn": "com.etzhayyim.fuchi.sustenanceEnvelope",
;;     "allocationIntent.edn":   "com.etzhayyim.fuchi.allocationIntent",
;;     "routingPlan.edn":        "com.etzhayyim.fuchi.routingPlan",
;;     "governanceDecision.edn": "com.etzhayyim.fuchi.governanceDecision",
;;     "provisioningIntent.edn": "com.etzhayyim.fuchi.provisioningIntent",
;;     "voteBallot.edn":         "com.etzhayyim.fuchi.voteBallot",
;;     "sustenanceBooking.edn":  "com.etzhayyim.fuchi.sustenanceBooking",
;;     "cohortEarmark.edn":      "com.etzhayyim.fuchi.cohortEarmark",
;; }
(def lex nil) ;; TODO: port-failed const

;; TODO: port-failed unit test_all_five_lexicons_present (asher: timed out)
;; def test_all_five_lexicons_present():
;;     files = {p.name for p in _LEX.glob("*.edn")}
;;     assert set(EXPECTED) <= files, f"missing: {set(EXPECTED) - files}"
(defn test-all-five-lexicons-present [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_all_five_lexicons_present"})))

;; TODO: port-failed unit test_each_lexicon_well_formed (assembled-lint error)
;; def test_each_lexicon_well_formed():
;;     for fname, lid in EXPECTED.items():
;;         lex = load_edn(_LEX / fname)
;;         assert lex[":lexicon"] == 1, fname
;;         assert lex[":id"] == lid, fname
;;         rec = lex[":defs"][":main"]
;;         assert rec[":type"] == "record", fname
;;         assert ":record" in rec, fname
;;         assert rec[":record"][":type"] == "object", fname
;;         assert rec[":record"][":required"], fname
(defn test-each-lexicon-well-formed [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_each_lexicon_well_formed"})))

;; TODO: port-failed unit test_namespace_prefix_is_fuchi (bb-compile error)
;; def test_namespace_prefix_is_fuchi():
;;     for lid in EXPECTED.values():
;;         assert lid.startswith("com.etzhayyim.fuchi."), lid
(defn test-namespace-prefix-is-fuchi [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_namespace_prefix_is_fuchi"})))

(defn _run []
  (throw (ex-info "TODO: port" {:from "_run"})))

