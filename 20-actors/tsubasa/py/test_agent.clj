#!/usr/bin/env bb
;; tsubasa 翼 — test harness (babashka / clojure.test; no kotoba host needed).
;;
;; Verifies the structural invariants of ADR-2606072802:
;;   G4 emissions-honest      — total cost includes baggage; co2Kg on every result; greenest first-class
;;   G1 no-affiliate-no-inflow — affiliate params stripped; handoff has no commission/tithe, member principal
;;   G3 anti-dark             — no urgency / price-will-rise field in any output
;;
;; Run: bb --classpath 20-actors 20-actors/tsubasa/py/test_agent.clj
(ns tsubasa.py.test-agent
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [tsubasa.py.agent :as agent]))

(defn- fare
  ([fid fare-amt]
   (fare fid fare-amt 0 100.0 120 "NH" "https://nh.example/book?flt=1"))
  ([fid fare-amt bag]
   (fare fid fare-amt bag 100.0 120 "NH" "https://nh.example/book?flt=1"))
  ([fid fare-amt bag co2]
   (fare fid fare-amt bag co2 120 "NH" "https://nh.example/book?flt=1"))
  ([fid fare-amt bag co2 dur]
   (fare fid fare-amt bag co2 dur "NH" "https://nh.example/book?flt=1"))
  ([fid fare-amt bag co2 dur carrier]
   (fare fid fare-amt bag co2 dur carrier "https://nh.example/book?flt=1"))
  ([fid fare-amt bag co2 dur carrier url]
   {:fareId      fid
    :origin      "HND"
    :destination "ITM"
    :departDate  "2026-07-01"
    :carrier     carrier
    :stops       0
    :durationMin dur
    :fareMinor   fare-amt
    :baggageMinor bag
    :currency    "JPY"
    :co2Kg       co2
    :cabin       "economy"
    :bookUrl     url
    :sourcing    "representative"}))

;; ── TotalCost ────────────────────────────────────────────────────────────────
(deftest test-includes-baggage
  (is (= 12000 (agent/total-cost-minor (fare "f" 10000 2000)))))

;; ── Search ───────────────────────────────────────────────────────────────────
(def ^:private search-fares
  (let [f1 (fare "cheap-dirty" 8000 0 300 130)
        f2 (fare "pricey-green" 12000 0 90 125)
        f3 (fare "mid" 10000 1000 150 120)
        f4 (assoc (fare "other" 5000 0 10.0 60) :destination "CTS")]
    [f1 f2 f3 f4]))

(deftest test-filters-route-and-date
  (let [out (agent/search-fares "HND" "ITM" "2026-07-01" search-fares)]
    (is (= 3 (count out)))))  ; the CTS one excluded

(deftest test-every-result-has-emissions
  (let [out (agent/search-fares "HND" "ITM" "2026-07-01" search-fares)]
    (doseq [r out]
      (is (contains? r :co2Kg) "G4: emissions on EVERY option")
      (is (contains? r :totalMinor)))))

(deftest test-sort-total-default
  (let [out (agent/search-fares "HND" "ITM" "2026-07-01" search-fares)]
    (is (= "cheap-dirty" (:fareId (first out))))))  ; 8000 total

(deftest test-sort-emissions
  (let [out (agent/search-fares "HND" "ITM" "2026-07-01" search-fares "emissions")]
    (is (= "pricey-green" (:fareId (first out))))))  ; 90 kg CO2 first

(deftest test-no-urgency-field
  (let [out (agent/search-fares "HND" "ITM" "2026-07-01" search-fares)]
    (doseq [r out
            k (keys r)]
      (let [kl (clojure.string/lower-case (name k))]
        (is (not (clojure.string/includes? kl "urgen")))
        (is (not (clojure.string/includes? kl "scarcit")))
        (is (not (clojure.string/includes? (clojure.string/replace kl "_" "") "willrise")))))))

;; ── Compare ──────────────────────────────────────────────────────────────────
(deftest test-greenest-is-first-class
  (let [fares [(fare "a" 8000 0 300)
               (fare "b" 12000 0 90)
               (fare "c" 9000 0 150 90)]
        out   (agent/compare fares)]
    (is (= "a" (:fareId (:cheapest out))))
    (is (= "b" (:fareId (:greenest out))))  ; emissions never hidden (G4)
    (is (= "c" (:fareId (:fastest out))))))

(deftest test-empty-compare
  (is (= {:cheapest nil :greenest nil :fastest nil}
         (agent/compare []))))

;; ── Handoff ──────────────────────────────────────────────────────────────────
(deftest test-affiliate-stripped
  (let [f   (fare "f" 10000 0 100.0 120 "NH"
                  "https://nh.example/book?flt=1&aff=skyscanner&utm_source=meta&tag=x")
        out (agent/self-book-handoff f)]
    (is (clojure.string/includes? (:bookUrl out) "flt=1"))
    (is (not (clojure.string/includes? (:bookUrl out) "aff=")))
    (is (not (clojure.string/includes? (:bookUrl out) "utm_source")))
    (is (not (clojure.string/includes? (:bookUrl out) "tag=")))))

(deftest test-no-commission-no-tithe-member-principal
  (let [out (agent/self-book-handoff (fare "f" 10000))]
    (is (= 0 (:commissionMinor out)))   ; G1
    (is (= 0 (:titheMinor out)))
    (is (= "member" (:principal out)))
    (is (= "self-book-handoff" (:mode out)))))

;; ── entry point ──────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'tsubasa.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
