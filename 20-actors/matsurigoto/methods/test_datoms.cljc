(ns matsurigoto.methods.test-datoms
  "test_datoms.py — tests for the R1.B datom-persistence layer.
  1:1 Clojure port (stdlib unittest-style → clojure.test).

  Drives the REAL modules to produce outputs, then verifies the EAVT conversion + structural
  invariants (G1 unsigned, G3 authority, G5 append-only, G8 gated). The __main__ runner is
  omitted. The Python kwargs dict TX is modelled as a string-keyed option map."
  (:require [clojure.test :refer [deftest is run-tests]]
            [matsurigoto.methods.datoms :as D]
            [matsurigoto.methods.modules.tax-assess :as T]
            [matsurigoto.methods.modules.civil-registry :as C]
            [matsurigoto.methods.modules.corp-registry :as R]
            [matsurigoto.methods.modules.credential-issue :as P]))

(def TX {"operated_by" ":etzhayyim-council" "authority_mode" ":sovereign-governance"
         "as_of" "2026-06-06T00:00:00Z" "spec_basis" "spec"})

(defn- vals-of [datoms attr]
  (vec (for [[_e a v] datoms :when (= a attr)] v)))

(deftest test-tax-assessment-datoms-roundtrip
  (let [out (T/assess-from-return 6000000 1000000 "JPN.income")
        ds (D/assessment-datoms out "t1" (assoc TX "service" "tax.income.file"))]
    (is (= (vals-of ds ":egov.assessment/liability") [572500.0]))
    (is (= (vals-of ds ":egov.tx/module") ["tax-assess"]))
    (is (= (vals-of ds ":egov.tx/server-held-authority") [false]))))  ; G1

(deftest test-civil-record-is-immutable-g5
  (let [out (C/register-birth "b1" "child:a" ["p"] "tokyo" "2026-06-01T00:00:00Z" "2026-06-05T00:00:00Z")
        ds (D/civil-datoms out "t2" (assoc TX "service" "civil.birth.register"))]
    (is (= (vals-of ds ":egov.record/immutable") [true]))  ; G5
    (is (= (vals-of ds ":egov.record/kind") ["birth"]))))

(deftest test-incorporation-datoms-carry-valid-lei
  (let [out (R/register-incorporation "Co" ["o"] 0 "art" "addr" "JPN" 1)
        ds (D/incorporation-datoms out "t3" (assoc TX "service" "corp.incorporation.register"))
        lei (first (vals-of ds ":egov.record/lei"))]
    (is (R/validate-lei lei))                                ; the persisted LEI is valid
    (is (= (vals-of ds ":egov.record/immutable") [true]))))

(deftest test-passport-datoms-certificate-unsigned-g1
  (let [out (P/issue-passport "L898902C3" "UTO" "UTO" "ERIKSSON" "ANNA" "740812" "F" "120415" "did:x")
        ds (D/passport-datoms out "t4" (assoc TX "service" "passport.issue"))]
    (is (= (vals-of ds ":egov.cert/proof") [nil]))          ; G1 — unsigned on the log
    (is (= (vals-of ds ":egov.cert/status") ["issued-unsigned"]))))

(deftest test-g1-rejects-a-signed-artifact
  (let [out0 (T/assess-from-return 1000000 0 "FLAT20.income")
        out (assoc-in out0 ["receipt" "proof"] "forged-sig")]  ; simulate a signed artifact
    (is (thrown? #?(:clj Exception :cljs js/Error)
                 (D/assessment-datoms out "t5" (assoc TX "service" "tax.income.file"))))))

(deftest test-g3-rejects-unknown-operator
  (let [out (T/assess-from-return 1000000 0 "FLAT20.income")
        bad (assoc TX "operated_by" ":the-platform" "service" "tax.income.file")]
    (is (thrown? #?(:clj Exception :cljs js/Error)
                 (D/assessment-datoms out "t6" bad)))))

(deftest test-g3-both-principals-accepted
  (let [out (T/assess-from-return 1000000 0 "FLAT20.income")
        a (D/assessment-datoms out "ta" {"service" "s"
                                         "operated_by" ":etzhayyim-council"
                                         "authority_mode" ":sovereign-governance"
                                         "as_of" "2026-06-06T00:00:00Z" "spec_basis" "x"})
        b (D/assessment-datoms out "tb" {"service" "s"
                                         "operated_by" ":adopting-government"
                                         "authority_mode" ":supplied-to-state"
                                         "as_of" "2026-06-06T00:00:00Z" "spec_basis" "x"})]
    (is (= (vals-of a ":egov.tx/operated-by") [":etzhayyim-council"]))
    (is (= (vals-of b ":egov.tx/operated-by") [":adopting-government"]))))

(deftest test-g2-requires-spec-basis
  (let [out (T/assess-from-return 1000000 0 "FLAT20.income")
        bad (assoc TX "spec_basis" "" "service" "s")]
    (is (thrown? #?(:clj Exception :cljs js/Error)
                 (D/assessment-datoms out "t7" bad)))))

(deftest test-ingest-batch-dry-run-body
  (let [out (T/assess-from-return 1000000 0 "FLAT20.income")
        ds (D/assessment-datoms out "t8" (assoc TX "service" "s"))
        body (D/kg-ingest-batch ds)]
    (is (= (get body "op") "kg.ingest_batch"))
    (is (= (get body "published") false))
    (is (= (get body "count") (count ds)))))

(deftest test-g8-live-publish-is-gated
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (D/kg-ingest-batch [] "egov-exec-v1" true))))

#?(:clj (defn -main [& _] (run-tests 'matsurigoto.methods.test-datoms)))
