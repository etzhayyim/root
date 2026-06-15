;; test_datoms.clj — matsurigoto EAVT membrane: module outputs → kotoba Datom log, parity with
;; datoms.py + G1/G3/G5/G8 enforced. Run via `bb test:matsurigoto`. ADR-2606142300.
(ns matsurigoto.methods.test-datoms
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [matsurigoto.methods.datoms :as dm]
            [matsurigoto.methods.modules.tax-assess :as ta]
            [matsurigoto.methods.modules.civil-registry :as cv]
            [matsurigoto.methods.modules.corp-registry :as cr]
            [matsurigoto.methods.modules.credential-issue :as ci]))

(def ^:private tx
  {:tx-id "tx-demo" :service "tax.income.file" :operated-by :etzhayyim-council
   :authority-mode :sovereign-governance :as-of "2026-06-06T00:00:00Z" :spec-basis "JP 速算表"})

(defn- has-datom? [ds e a v] (some #(= [e a v] %) ds))

(deftest assessment-datoms-shape
  (testing "tax-assess → 17 EAVT datoms (golden count from datoms.py) + G1/G3 fields"
    (let [out (ta/assess-from-return 6000000 1000000 "JPN.income")
          ds  (dm/assessment-datoms out tx)]
      (is (= 17 (count ds)))
      (is (has-datom? ds "tx-demo" :egov.tx/operated-by :etzhayyim-council))          ; G3
      (is (has-datom? ds "tx-demo" :egov.tx/server-held-authority false))             ; G1
      (is (has-datom? ds "tx-demo" :egov.assessment/liability 572500.0))
      (is (has-datom? ds "tx-demo#cert" :egov.cert/proof nil))                         ; G1
      (is (has-datom? ds "tx-demo#cert" :egov.cert/kind "?"))                          ; receipt has no :type
      (is (has-datom? ds "tx-demo#cert" :egov.cert/status "assessed-unsigned")))))

(deftest civil-and-corp-and-passport-datoms
  (testing "each module's output → record + cert datoms with the right kind + G5 immutability"
    (let [birth (cv/register-birth "birth-1" "child:aoi" ["parent:rin"] "東京" "2026-06-01" "2026-06-05")
          cd    (dm/civil-datoms birth (assoc tx :service "civil.birth.register"))
          inc   (cr/register-incorporation {:entity-name "X K.K." :officers ["o"] :capital 0
                                            :articles "a" :address "addr" :jurisdiction "JPN" :sequence 1})
          id    (dm/incorporation-datoms inc (assoc tx :service "corp.incorporation.register"))
          pass  (ci/issue-passport {:doc-number "L898902C3" :issuing-state "UTO" :nationality "UTO"
                                    :surname "ERIKSSON" :given-names "ANNA MARIA" :dob-yymmdd "740812"
                                    :sex "F" :expiry-yymmdd "120415" :subject-did "did:web:x"})
          pd    (dm/passport-datoms pass (assoc tx :service "passport.issue"))]
      (is (has-datom? cd "birth-1" :egov.record/kind "birth"))
      (is (has-datom? cd "birth-1" :egov.record/immutable true))                       ; G5
      (is (has-datom? cd "tx-demo#cert" :egov.cert/kind "BirthCertificate"))
      (is (has-datom? id "JPN-00000001" :egov.record/kind "incorporation"))
      (is (has-datom? id "JPN-00000001" :egov.record/lei (:lei inc)))
      (is (has-datom? id "tx-demo#cert" :egov.cert/kind "IncorporationCertificate"))
      (is (has-datom? pd "tx-demo#mrtd" :egov.record/kind "passport"))
      (is (has-datom? pd "tx-demo#cert" :egov.cert/kind "Passport")))))

(deftest guards-G1-G3
  (testing "G1 unsigned + G3 authority enforced"
    (let [out (ta/assess-from-return 6000000 1000000 "JPN.income")]
      ;; G3 — operated-by / authority-mode allow-lists
      (is (thrown? Exception (dm/assessment-datoms out (assoc tx :operated-by :hacker))))
      (is (thrown? Exception (dm/assessment-datoms out (assoc tx :authority-mode :offensive))))
      (is (thrown? Exception (dm/assessment-datoms out (assoc tx :spec-basis ""))))
      ;; G1 — a signed/authority-bearing artifact is rejected
      (is (thrown? Exception (dm/assessment-datoms (assoc-in out [:receipt :proof] "sig") tx)))
      (is (thrown? Exception (dm/assessment-datoms (assoc-in out [:receipt :server-held-authority] true) tx))))))

(deftest kg-ingest-batch-G8
  (testing "G8 — dry-run body builds; published true RAISES (Council+operator gated)"
    (let [ds   (dm/assessment-datoms (ta/assess-from-return 6000000 1000000 "JPN.income") tx)
          body (dm/kg-ingest-batch ds)]
      (is (= "kg.ingest_batch" (:op body)))
      (is (= "egov-exec-v1" (:graph body)))
      (is (false? (:published body)))
      (is (= 17 (:count body)))
      (is (thrown? Exception (dm/kg-ingest-batch ds {:published true}))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'matsurigoto.methods.test-datoms)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
