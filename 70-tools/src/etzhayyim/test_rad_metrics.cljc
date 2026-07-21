(ns etzhayyim.test-rad-metrics
  "etzhayyim.rad-metrics — BMC gate emitter tests (:hyp/etzhayyim-registry-value).
   Pure aggregation over synthetic RAD journals + give datoms, plus a live-ledger
   invariant check against 80-data/kotoba-rad."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]
            [etzhayyim.rad-metrics :as rm]))

;; ── synthetic RAD journals (datom vectors [e a v tx op]) ────────────────────
(def ^:private registered-only
  ;; registered, sigref referenced, but NOT signed (pending)
  [["rid.a" :rad/type :identity 1 :add]
   ["rid.a" :rad/name "alpha" 1 :add]
   ["sigref:rid.a" :rad/type :sigref 1 :add]
   ["sigref:rid.a" :rad/head "head.a" 1 :add]
   ["sigref:rid.a" :rad/by "did:web:example:alpha" 1 :add]])

(def ^:private signed
  ;; registered, sigref referenced AND carries a real :rad/sig → attested
  [["rid.b" :rad/type :identity 1 :add]
   ["rid.b" :rad/name "beta" 1 :add]
   ["sigref:rid.b" :rad/type :sigref 1 :add]
   ["sigref:rid.b" :rad/head "head.b" 1 :add]
   ["sigref:rid.b" :rad/sig "deadbeef" 1 :add]])

(def ^:private no-ref
  ;; registered only, no sigref at all
  [["rid.c" :rad/type :identity 1 :add]
   ["rid.c" :rad/name "gamma" 1 :add]])

(deftest rad-summary-counts
  (let [s (rm/rad-summary [registered-only signed no-ref])]
    (is (= 3 (:registered-organisms s)) "all three organisms registered")
    (is (= 2 (:attestation-refs s)) "alpha + beta carry a sigref reference")
    (is (= 1 (:attested-organisms s)) "only beta carries a real :rad/sig")
    (is (= 1 (:pending-attestations s)) "alpha is referenced but unsigned")))

(deftest journal-summary-signed-vs-pending
  (is (true?  (:attested? (rm/journal-summary signed))))
  (is (false? (:attested? (rm/journal-summary registered-only))))
  (is (true?  (:attestation-ref? (rm/journal-summary registered-only))))
  (is (false? (:attestation-ref? (rm/journal-summary no-ref)))))

;; ── funding channel + non-profit invariant ─────────────────────────────────
(def ^:private give-datoms
  [;; allowed: donation, JPY-denominated
   ["give.1" :give/type :donation 1 :add]
   ["give.1" :give/purpose "donation" 1 :add]
   ["give.1" :give/amount-jpy 5000 1 :add]
   ;; allowed: grant, USDC micros (1 USDC)
   ["give.2" :give/type :donation 1 :add]
   ["give.2" :give/purpose "grant" 1 :add]
   ["give.2" :give/amount-micros 1000000 1 :add]
   ;; rejected: purpose outside donation-only set → must NOT count (non-profit invariant)
   ["give.3" :give/type :donation 1 :add]
   ["give.3" :give/purpose "tithe" 1 :add]
   ["give.3" :give/amount-jpy 999 1 :add]])

(deftest funding-summary-non-profit-invariant
  (let [f (rm/funding-summary give-datoms)]
    (is (= 2 (:funding-events f)) "only donation + grant purposes count")
    (is (= 5000 (:funding-jpy f)) "only explicit JPY amounts sum; no fabricated FX")
    (is (= 1000000 (:funding-usdc-micros f)) "USDC micros surfaced separately")
    (is (= 1 (:rejected-events f)) "the tithe record is rejected, not summed")))

(deftest funding-empty-ledger-is-zero
  (let [f (rm/funding-summary [])]
    (is (= 0 (:funding-events f)))
    (is (= 0 (:funding-jpy f)) "absent ledger ⇒ 0, never fabricated")))

;; ── live ledger invariant (read-only, against 80-data/kotoba-rad) ───────────
(deftest live-rad-ledger-registered-matches-files
  (let [dir "80-data/kotoba-rad"]
    (when (.isDirectory (io/file dir))
      (let [journals (rm/read-journals dir)
            s        (rm/rad-summary journals)]
        (is (pos? (:registered-organisms s)) "the RAD ledger has registered organisms")
        (is (= (count journals) (:registered-organisms s))
            "every *.identity.journal.edn carries a :rad/type :identity")
        (is (>= (:attestation-refs s) (:attested-organisms s))
            "attested ⊆ attestation-refs (a signed sigref is still a sigref)")
        (is (= (:attestation-refs s)
               (+ (:attested-organisms s) (:pending-attestations s)))
            "refs partition into signed + pending")))))

#?(:clj
   (defn -main [& _]
     (let [{:keys [fail error]} (run-tests 'etzhayyim.test-rad-metrics)]
       (System/exit (if (zero? (+ fail error)) 0 1)))))
