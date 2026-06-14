;; kudamori 管守 — test suite (clojure.test, babashka-runnable).
;; Run: bb --classpath 20-actors 20-actors/kudamori/methods/test_kudamori.clj
;; Per ADR-2606142030 (kudamori R0).
(ns kudamori.methods.test-kudamori
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.edn :as edn]
            [kudamori.methods.atmosphere :as atm]
            [kudamori.methods.pipe-nav :as nav]
            [kudamori.methods.jetting :as jet]
            [kudamori.methods.analyze :as az]
            [kudamori.methods.datom-emit :as de]
            [kudamori.methods.handoff :as ho]))

;; ── atmosphere (★ G5 — the headline confined-space entry gate) ────────────────
(def safe-air  {:o2-pct 20.9 :h2s-ppm 0.0 :ch4-lel 0.0 :co-ppm 0.0})
(def foul-air  {:o2-pct 18.6 :h2s-ppm 22.0 :ch4-lel 14.0 :co-ppm 12.0})

(deftest entry-permitted-on-safe-air
  (testing "a fresh-air reading permits entry with no hazards"
    (is (atm/entry-permitted? safe-air))
    (is (empty? (atm/hazards safe-air)))
    (is (= safe-air (atm/assert-entry! safe-air)))))

(deftest entry-refused-on-unsafe-air
  (testing "★ G5 — an unsafe atmosphere refuses entry and assert-entry! RAISES"
    (is (not (atm/entry-permitted? foul-air)))
    (is (thrown? clojure.lang.ExceptionInfo (atm/assert-entry! foul-air)))))

(deftest each-gas-threshold-detected
  (testing "every individual breach (O2 low/high, H2S, CH4, CO) is caught"
    (is (not (atm/entry-permitted? {:o2-pct 18.0 :h2s-ppm 0 :ch4-lel 0 :co-ppm 0})))   ; O2 low
    (is (not (atm/entry-permitted? {:o2-pct 24.0 :h2s-ppm 0 :ch4-lel 0 :co-ppm 0})))   ; O2 high
    (is (not (atm/entry-permitted? {:o2-pct 20.9 :h2s-ppm 10 :ch4-lel 0 :co-ppm 0})))  ; H2S at limit
    (is (not (atm/entry-permitted? {:o2-pct 20.9 :h2s-ppm 0 :ch4-lel 10 :co-ppm 0})))  ; CH4 at LEL
    (is (not (atm/entry-permitted? {:o2-pct 20.9 :h2s-ppm 0 :ch4-lel 0 :co-ppm 35}))))) ; CO at limit

(deftest purge-to-entry-converges
  (testing "forced ventilation drives a foul atmosphere to a passing reading"
    (let [r (atm/purge-to-entry foul-air 0.25 60)]
      (is (:entry-permitted? r))
      (is (pos? (:minutes r)))
      ;; the post-purge reading actually passes the gate (no lying about safety)
      (is (atm/entry-permitted? (:reading r))))))

(deftest purge-honest-when-budget-exhausted
  (testing "★ G5 — if ventilation can't clear it in the budget, entry stays refused"
    (let [r (atm/purge-to-entry foul-air 0.25 0)]  ; zero-minute budget
      (is (not (:entry-permitted? r)))
      (is (seq (:hazards r))))))

;; ── pipe_nav ──────────────────────────────────────────────────────────────────
(deftest diameter-fit-check
  (testing "crawler fits a wide pipe, not a narrow one"
    (is (nav/fits? 200 300 30))
    (is (not (nav/fits? 200 220 30)))))   ; 200+30 = 230 > 220

(deftest assert-fit-raises-on-no-fit
  (testing "a pipe the crawler cannot clear RAISES"
    (let [robot {:od-mm 200 :clearance-mm 30}]
      (is (= {:id "ok" :id-mm 300} (nav/assert-fit! robot {:id "ok" :id-mm 300})))
      (is (thrown? clojure.lang.ExceptionInfo
                   (nav/assert-fit! robot {:id "tight" :id-mm 210}))))))

(def segs
  [{:id "a-b" :from "A" :to "B" :id-mm 300 :length-m 10.0}
   {:id "b-c" :from "B" :to "C" :id-mm 300 :length-m 10.0 :blocked? true}
   {:id "a-c" :from "A" :to "C" :id-mm 300 :length-m 30.0}])

(deftest shortest-route-bfs
  (testing "BFS finds the fewest-hop route; trivial start=goal is empty"
    (is (= {:nodes ["A"] :segments []} (nav/shortest-route segs "A" "A")))
    (is (= ["a-c"] (:segments (nav/shortest-route segs "A" "C"))))))   ; 1 hop beats A-B-C

(deftest route-around-blocked-segment
  (testing "avoid-blocked? excludes the blocked segment from the graph"
    ;; reaching C: with blocked allowed, A-C (1 hop) anyway; force via B by removing a-c
    (let [s2 [{:id "a-b" :from "A" :to "B" :id-mm 300 :length-m 10.0}
              {:id "b-c" :from "B" :to "C" :id-mm 300 :length-m 10.0 :blocked? true}]]
      (is (some? (nav/shortest-route s2 "A" "C" false)))          ; blocked allowed → reachable
      (is (nil? (nav/shortest-route s2 "A" "C" true))))))         ; route-around → unreachable

(deftest plan-nav-flags-blocked-target
  (testing "planning to a blocked target reports it blocked but still fits + routes"
    (let [robot {:od-mm 200 :clearance-mm 30}
          plan (nav/plan-nav robot segs "A" "b-c" false)]   ; allow the blocked target's neighbours
      (is (:target-blocked? plan))
      (is (:fits plan))
      (is (>= (:hops plan) 0)))))

;; ── jetting (★ G7 — no pipe over-pressure) ────────────────────────────────────
(deftest jet-pressure-safe-within-rating
  (testing "pressure at/below the material rating is safe"
    (is (jet/jet-pressure-safe? 120.0 :vcp))      ; rating 150
    (is (not (jet/jet-pressure-safe? 120.0 :pvc))))) ; rating 100

(deftest jet-over-pressure-raises
  (testing "★ G7 — over-pressure that would damage the pipe RAISES"
    (is (thrown? clojure.lang.ExceptionInfo (jet/assert-jet-pressure! 200.0 :pvc)))
    (is (= 90.0 (jet/assert-jet-pressure! 90.0 :pvc)))
    ;; an unknown material has no rating → conservative raise
    (is (thrown? clojure.lang.ExceptionInfo (jet/rating-for :mystery)))))

(deftest debris-and-water-balance
  (testing "debris removal positive; effluent hands off to mizuho, never discharged"
    (let [seg {:id "s" :id-mm 300 :length-m 50.0 :material :vcp}
          d (jet/debris-removed-m3 seg 0.35)
          wb (jet/water-balance 60.0 30.0 0.7)]
      (is (pos? d))
      (is (= 1800.0 (:used-l wb)))
      (is (= :mizuho (:handoff wb)))          ; G2 — untreated effluent → mizuho
      (is (< (Math/abs (- (:effluent-l wb) 540.0)) 1e-6)))))   ; 30% of 1800

;; ── analyze + datom_emit (end-to-end over the seed) ──────────────────────────
(def seed (az/load-seed "20-actors/kudamori/data/network.edn"))

(deftest analyze-end-to-end
  (let [res (az/run seed)]
    (testing "the foul entry atmosphere is purged to a permitted entry (G5)"
      (is (true? (get-in res [:entry :permitted?])))
      (is (false? (get-in res [:entry :raw-safe?])))   ; raw reading was unsafe
      (is (pos? (get-in res [:entry :purge :minutes]))))
    (testing "navigation reaches the blocked target and jetting is pressure-safe"
      (is (= "seg-2-3" (get-in res [:navigation :target])))
      (is (true? (get-in res [:navigation :target-blocked?])))
      (is (pos? (get-in res [:jetting :debris-removed-m3])))
      (is (<= (get-in res [:jetting :pressure-bar]) (get-in res [:jetting :rating-bar]))))))

(deftest gated-when-atmosphere-unrecoverable
  (testing "★ G5 — if entry cannot be made safe, navigation + jetting are GATED"
    (let [bad (assoc seed :blower {:air-changes-per-min 0.0}      ; no ventilation
                          :gas-reading {:node "mh-entry" :o2-pct 5.0 :h2s-ppm 500.0
                                        :ch4-lel 80.0 :co-ppm 400.0})
          res (az/run bad)]
      (is (false? (get-in res [:entry :permitted?])))
      (is (= :gated (:navigation res)))
      (is (= :gated (:jetting res))))))

(deftest datom-emit-shape
  (let [res (az/run seed)
        out (de/emit seed res 1)]
    (testing "emits ground :add datoms + transient :derived readouts"
      (is (re-find #":kuda\.pipe/material" out))
      (is (re-find #":kuda\.node/h2s-ppm" out))
      (is (re-find #":kuda\.robot/kind" out))
      (is (re-find #":en/kind :cleans" out))
      (is (re-find #":bond/entry-permitted" out))
      (is (re-find #":derived\]" out))
      ;; well-formed EDN vector of datoms (load-bearing: must parse)
      (is (vector? (edn/read-string out))))))

(deftest datom-emit-gated-shape
  (testing "a gated run emits the gate datom and no cleans 縁"
    (let [bad (assoc seed :blower {:air-changes-per-min 0.0}
                          :gas-reading {:node "mh-entry" :o2-pct 5.0 :h2s-ppm 500.0
                                        :ch4-lel 80.0 :co-ppm 400.0})
          res (az/run bad)
          out (de/emit bad res 1)]
      (is (re-find #":bond/jetting-gated true" out))
      (is (not (re-find #":en/kind :cleans" out)))
      (is (vector? (edn/read-string out))))))

;; ── handoff (cross-actor chain edges: kudamori→mizuho effluent) ──────────────
(deftest outbound-to-mizuho
  (testing "cleaned segments → mizuho wastewater-treatment intents, source-attributed"
    (let [hs (ho/outbound-handoff [{:segment-id "seg-1-2" :debris-m3 0.42 :effluent-l 540.0}
                                   {:segment-id "seg-2-3" :debris-m3 0.18 :effluent-l 360.0}])]
      (is (= 2 (count hs)))
      (is (every? #(= "kudamori" (:from-actor %)) hs))
      (is (every? #(= "mizuho" (:to-actor %)) hs))
      (is (= :effluent (:kind (first hs))))
      (is (= 0.42 (get-in (first hs) [:payload :debris-m3])))
      (is (= 540.0 (get-in (first hs) [:payload :effluent-l]))))))

(deftest effluent-handoff-single
  (testing "a single cleaned segment → one mizuho effluent handoff"
    (let [h (ho/effluent-handoff {:segment-id "seg-3-4" :debris-m3 0.25 :effluent-l 300.0})]
      (is (= "kudamori" (:from-actor h)))
      (is (= "mizuho" (:to-actor h)))
      (is (= :effluent (:kind h)))
      (is (= "seg-3-4" (get-in h [:payload :segment-id])))
      (is (= 300.0 (get-in h [:payload :effluent-l]))))))

(deftest handoff-provenance-gate
  (testing "G9 — an orphan handoff (no source/destination) RAISES"
    (is (thrown? clojure.lang.ExceptionInfo (ho/assert-handoff! {:id "x" :to-actor "mizuho"})))
    (is (thrown? clojure.lang.ExceptionInfo (ho/assert-handoff! {:id "x" :from-actor "kudamori"})))
    (is (= "kudamori" (:from-actor (ho/assert-handoff! {:id "x" :from-actor "kudamori" :to-actor "mizuho"}))))))

(deftest handoff-emit-shape
  (testing "emits well-formed EDN :handoff/* 縁 with actor provenance on every edge"
    (let [hs (ho/outbound-handoff [{:segment-id "seg-1-2" :debris-m3 0.42 :effluent-l 540.0}])
          out (ho/emit hs 1)]
      (is (re-find #":handoff/from-actor" out))
      (is (re-find #":handoff/to-actor" out))
      (is (re-find #"en\.handoff\.kudamori\.mizuho\." out))
      (is (vector? (edn/read-string out))))))

(let [{:keys [fail error]} (run-tests 'kudamori.methods.test-kudamori)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
