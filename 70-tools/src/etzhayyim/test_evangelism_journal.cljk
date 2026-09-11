;; etzhayyim.test-evangelism-journal — personal interpersonal-evangelism
;; self-attestation journal invariants. Run via the aggregate: bb test:helpers
;; Covers: record construction (structural consts pinned, no recipient field
;; possible), MemStore append-only accumulation, summarize/report, and a
;; schema-drift guard against the REAL evangelismActivityAttestation.json
;; lexicon file (not a hand-copied list) — mirrors com-etzhayyim-tomoshibi's
;; own test/tomoshibi/operation_test.cljc pattern for the same lexicon.
(ns etzhayyim.test-evangelism-journal
  (:require [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.evangelism-journal :as ej]))

(def ^:private now "2026-07-10T09:00:00Z")
(def ^:private founder-did "did:key:z6MkfounderPlaceholder")

(deftest record-pins-structural-consts
  (testing "every recorded attestation fixes the four STRUCTURAL const fields"
    (let [att (ej/record {:adherent-did founder-did
                           :interpersonal-method "door-to-door"
                           :now now})]
      (is (true?  (:optOutAffordancePresent att)))
      (is (false? (:coercionAttested att)))
      (is (false? (:minorSoloSolicitationAttested att)))
      (is (true?  (:voluntaryAttested att)))
      (is (= "interpersonal" (:mode att)))
      (is (= founder-did (:adherentDid att)))
      (is (= founder-did (:attestingCellDid att)))
      (is (= "door-to-door" (:interpersonalMethod att)))
      (is (= now (:createdAt att))))))

(deftest record-has-no-recipient-identifying-field
  (testing "there is no parameter for, and no way to produce, a recipient/household/outcome field"
    (let [att (ej/record {:adherent-did founder-did
                           :interpersonal-method "door-to-door"
                           :now now})]
      (is (not (contains? att :recipientDid)))
      (is (not (contains? att :householdId)))
      (is (not (contains? att :address)))
      (is (not (contains? att :responseNoted)))
      (is (= (set (keys att))
             #{:optOutAffordancePresent :coercionAttested :minorSoloSolicitationAttested
               :voluntaryAttested :createdAt :mode :adherentDid :interpersonalMethod
               :attestingCellDid})))))

(deftest record-rejects-unknown-method
  (testing "an interpersonal-method outside the lexicon's knownValues throws, not silently accepted"
    (is (thrown? #?(:clj AssertionError :cljs js/Error)
                 (ej/record {:adherent-did founder-did
                             :interpersonal-method "cold-call"
                             :now now})))))

(deftest memstore-append-only-accumulation
  (testing "successive record! calls accumulate, oldest first"
    (let [s (ej/seed-db)
          a1 (ej/record {:adherent-did founder-did :interpersonal-method "door-to-door" :now "2026-07-01T09:00:00Z"})
          a2 (ej/record {:adherent-did founder-did :interpersonal-method "face-to-face" :now "2026-07-02T09:00:00Z"})]
      (ej/record! s a1)
      (ej/record! s a2)
      (is (= [a1 a2] (ej/all-records s))))))

(deftest summarize-personal-report
  (testing "summarize tallies total / by-method / by-month — recognition, never a quota comparison"
    (let [records [(ej/record {:adherent-did founder-did :interpersonal-method "door-to-door" :now "2026-07-01T09:00:00Z"})
                   (ej/record {:adherent-did founder-did :interpersonal-method "door-to-door" :now "2026-07-15T09:00:00Z"})
                   (ej/record {:adherent-did founder-did :interpersonal-method "street" :now "2026-08-01T09:00:00Z"})]
          report (ej/summarize records)]
      (is (= 3 (:total report)))
      (is (= {"door-to-door" 2 "street" 1} (:by-method report)))
      (is (= {"2026-07" 2 "2026-08" 1} (:by-month report))))))

;; ---------------------------------------------------------------------------
;; Lexicon-schema cross-check (reads the REAL lexicon file, not a hand-copy)
;; ---------------------------------------------------------------------------

(def ^:private lexicon-path
  "00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/evangelismActivityAttestation.json")

(deftest journal-matches-real-lexicon-required-fields
  (testing "etzhayyim.evangelism-journal/lexicon-required-fields matches the actual lexicon file's `required` array"
    (let [lex (json/parse-string (slurp (io/file lexicon-path)) true)
          required (set (map keyword (get-in lex [:defs :main :record :required])))]
      (is (seq required) "sanity: the lexicon actually declares required fields")
      (is (= required ej/lexicon-required-fields)))))

(deftest journal-matches-real-lexicon-const-values
  (testing "the four STRUCTURAL const fields in the real lexicon match what this journal writes"
    (let [lex (json/parse-string (slurp (io/file lexicon-path)) true)
          props (get-in lex [:defs :main :record :properties])
          const-of (fn [k] (get-in props [k :const]))]
      (is (= true  (const-of :optOutAffordancePresent)))
      (is (= false (const-of :coercionAttested)))
      (is (= false (const-of :minorSoloSolicitationAttested)))
      (is (= true  (const-of :voluntaryAttested))))))

(deftest journal-matches-real-lexicon-known-methods
  (testing "known-methods matches the lexicon's interpersonalMethod knownValues exactly"
    (let [lex (json/parse-string (slurp (io/file lexicon-path)) true)
          props (get-in lex [:defs :main :record :properties])
          known (set (get-in props [:interpersonalMethod :knownValues]))]
      (is (= known ej/known-methods)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-evangelism-journal)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
