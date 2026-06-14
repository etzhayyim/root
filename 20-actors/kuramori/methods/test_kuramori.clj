;; kuramori 倉守 — test suite (clojure.test, babashka-runnable).
;; Run: bb --classpath 20-actors 20-actors/kuramori/methods/test_kuramori.clj
;; Per ADR-2606142000 (kuramori R0).
(ns kuramori.methods.test-kuramori
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [kuramori.methods.agv-amr :as fleet]
            [kuramori.methods.slotting :as slot]
            [kuramori.methods.analyze :as az]
            [kuramori.methods.datom-emit :as de]
            [kuramori.methods.picking :as pick]
            [kuramori.methods.handoff :as ho]))

;; ── agv_amr ──────────────────────────────────────────────────────────────────
(deftest travel-time-monotonic
  (testing "longer legs take longer; zero leg is free"
    (let [v (fleet/make-vehicle :agv)]
      (is (= 0.0 (fleet/travel-time 0.0 v)))
      (is (< (fleet/travel-time 5.0 v) (fleet/travel-time 50.0 v))))))

(deftest travel-time-rejects-negative
  (is (thrown? clojure.lang.ExceptionInfo (fleet/travel-time -1.0 (fleet/make-vehicle)))))

(deftest trapezoidal-matches-niyaku-closed-form
  (testing "long leg = 2*t_ramp + d_cruise/v (niyaku closed form)"
    (let [v (fleet/make-vehicle :agv {:v-max 2.0 :a-max 0.5})  ; d-to-vmax = 8m
          d 20.0
          expected (+ (* 2.0 (/ 2.0 0.5)) (/ (- 20.0 8.0) 2.0))]
      (is (< (Math/abs (- (fleet/travel-time d v) expected)) 1e-9)))))

(deftest shared-zone-yield-caps-speed
  (testing "G5 — a robot near a human is capped at shared-zone speed"
    (let [v (fleet/make-vehicle :agv {:v-max 3.0})]
      (is (= fleet/shared-zone-cap-mps (fleet/effective-vmax v true)))
      (is (= 3.0 (fleet/effective-vmax v false))))))

(deftest battery-charge-gate
  (testing "G2 — a long leg below reserve floor flags needs-charge"
    (let [low (fleet/make-vehicle :amr {:soc 0.16 :soc-min 0.15 :battery-kwh 0.05})]
      (is (fleet/needs-charge? low 100.0)))
    (let [full (fleet/make-vehicle :amr {:soc 1.0})]
      (is (not (fleet/needs-charge? full 5.0))))))

(deftest agv-segment-conflict
  (testing "same one-way segment + overlapping time = conflict; touching ≠ conflict"
    (let [a {:segment "lane-1" :vehicle-id "agv-1" :t-in 0.0 :t-out 5.0}
          b {:segment "lane-1" :vehicle-id "agv-2" :t-in 3.0 :t-out 8.0}
          c {:segment "lane-1" :vehicle-id "agv-2" :t-in 5.0 :t-out 9.0}
          d {:segment "lane-2" :vehicle-id "agv-2" :t-in 3.0 :t-out 8.0}]
      (is (fleet/reservations-conflict? a b))
      (is (not (fleet/reservations-conflict? a c)))    ; touch at t=5
      (is (not (fleet/reservations-conflict? a d)))    ; different lane
      (is (= [[0 1]] (fleet/find-conflicts [a b c]))))))

(deftest amr-never-segment-conflicts
  (testing "AMRs (no :segment) are not deconflicted by lanes"
    (let [a {:vehicle-id "amr-1" :t-in 0.0 :t-out 5.0}
          b {:vehicle-id "amr-2" :t-in 1.0 :t-out 6.0}]
      (is (not (fleet/reservations-conflict? a b))))))

(deftest dispatch-balances-makespan
  (testing "LPT dispatch spreads load; needs ≥1 vehicle"
    (let [moves [{:move-id "m1" :distance-m 40.0} {:move-id "m2" :distance-m 38.0}
                 {:move-id "m3" :distance-m 5.0}]
          r (fleet/dispatch moves ["a" "b"] (fleet/make-vehicle :amr))]
      (is (= 3 (reduce + (map count (vals (:assignment r))))))
      (is (pos? (:makespan r)))
      (is (thrown? clojure.lang.ExceptionInfo (fleet/dispatch moves [] (fleet/make-vehicle)))))))

;; ── slotting ──────────────────────────────────────────────────────────────────
(deftest abc-classes
  (is (= :A (slot/abc-class 220 {})))
  (is (= :B (slot/abc-class 60 {})))
  (is (= :C (slot/abc-class 5 {}))))

(deftest putaway-respects-weight-temp-hazmat
  (testing "G7 — zone constraints are hard"
    (let [ambient {:id "s" :max-kg 50 :temps #{:ambient} :dist-from-face 5}
          reefer  {:id "r" :max-kg 50 :temps #{:reefer}  :dist-from-face 5}
          haz     {:id "h" :max-kg 50 :temps #{:ambient} :hazmat-rated true
                   :segregate-from #{:oxidizer} :dist-from-face 5}]
      (is (slot/putaway-feasible? {:weight-kg 8 :temp :ambient} ambient))
      (is (not (slot/putaway-feasible? {:weight-kg 80 :temp :ambient} ambient))) ; overweight
      (is (not (slot/putaway-feasible? {:weight-kg 8 :temp :reefer} ambient)))   ; wrong temp
      (is (slot/putaway-feasible? {:weight-kg 8 :temp :reefer} reefer))
      (is (slot/putaway-feasible? {:weight-kg 8 :temp :ambient :hazmat :flammable} haz))
      (is (not (slot/putaway-feasible? {:weight-kg 8 :temp :ambient :hazmat :flammable} ambient))) ; not rated
      (is (not (slot/putaway-feasible? {:weight-kg 8 :temp :ambient :hazmat :oxidizer} haz)))))) ; segregated

(deftest assign-slot-raises-when-infeasible
  (testing "G7 — an infeasible putaway RAISES (never silently forced)"
    (is (thrown? clojure.lang.ExceptionInfo
                 (slot/assign-slot! {:id "x" :weight-kg 999 :temp :ambient}
                                    [{:id "s" :max-kg 50 :temps #{:ambient} :dist-from-face 5}])))))

(deftest golden-zone-packing
  (testing "fastest SKU claims the closest feasible slot"
    (let [skus [{:id "fast" :velocity 200 :weight-kg 5 :temp :ambient}
                {:id "slow" :velocity 1 :weight-kg 5 :temp :ambient}]
          slots [{:id "near" :dist-from-face 5 :max-kg 50 :temps #{:ambient}}
                 {:id "far"  :dist-from-face 50 :max-kg 50 :temps #{:ambient}}]
          r (slot/assign-slots skus slots {})]
      (is (= "near" (get-in r [:placement "fast"])))
      (is (= "far"  (get-in r [:placement "slow"]))))))

(deftest pick-route-returns-to-dock
  (testing "nearest-neighbour route is positive and closes the loop"
    (let [d (slot/pick-route [0 0] [[3 4] [6 8]])]
      (is (pos? d)))))

;; ── analyze + datom_emit (end-to-end over the seed) ──────────────────────────
(def seed (az/load-seed "20-actors/kuramori/data/warehouse.edn"))

(deftest analyze-end-to-end
  (let [res (az/run seed)]
    (testing "every SKU is placed in a feasible slot"
      (is (= (count (:skus seed)) (count (get-in res [:slotting :placement]))))
      ;; the flammable SKU must land in the hazmat-rated slot
      (is (= "s-h1" (get-in res [:slotting :placement "sku-flam"])))
      ;; the cold SKU must land in the reefer slot
      (is (= "s-r1" (get-in res [:slotting :placement "sku-cold"]))))
    (testing "fast mover is class A and lands in the golden zone"
      (is (= :A (get-in res [:abc "sku-fast"])))
      (is (= "z-golden" (->> (:slots seed)
                             (filter #(= (:id %) (get-in res [:slotting :placement "sku-fast"])))
                             first :zone))))
    (testing "dispatch + battery readouts present"
      (is (pos? (get-in res [:dispatch :makespan])))
      (is (contains? (:battery res) :charge-needed)))))

(deftest datom-emit-shape
  (let [res (az/run seed)
        out (de/emit seed res 1)]
    (testing "emits ground :add datoms + transient :derived readouts"
      (is (re-find #":wh\.sku/abc" out))
      (is (re-find #":wh\.slot/in-zone" out))
      (is (re-find #":en/kind :slotted-in" out))
      (is (re-find #":bond/dispatch-makespan" out))
      (is (re-find #":derived\]" out))
      ;; well-formed EDN vector of datoms
      (is (vector? (clojure.edn/read-string out))))))

;; ── picking (multi-order batch consolidation + congestion) ───────────────────
(def orders
  [{:id "o1" :picks ["s-g1" "s-g2" "s-r1"]}
   {:id "o2" :picks ["s-g3" "s-b1"]}
   {:id "o3" :picks ["s-h1"]}])

(deftest consolidate-packs-into-waves
  (testing "FFD packing respects wave capacity; every order placed exactly once"
    (let [waves (pick/consolidate orders 4)
          placed (mapcat :orders waves)]
      (is (= #{"o1" "o2" "o3"} (set placed)))
      (is (= 3 (count placed)))                       ; no order duplicated/dropped
      (is (every? #(<= (count (:picks %)) 4) waves))  ; capacity respected
      ;; total picks preserved across waves
      (is (= 6 (reduce + (map #(count (:picks %)) waves)))))))

(deftest batch-capacity-gate-raises
  (testing "G9 — an order larger than the wave cap RAISES (atomic, never split)"
    (is (thrown? clojure.lang.ExceptionInfo
                 (pick/consolidate [{:id "big" :picks ["a" "b" "c" "d" "e"]}] 4)))
    (is (thrown? clojure.lang.ExceptionInfo
                 (pick/assert-batch-capacity! [{:id "big" :picks ["a" "b" "c"]}] 2)))))

(deftest tight-cap-one-order-per-wave
  (testing "cap below the second-largest order forces separate waves"
    (let [waves (pick/consolidate orders 3)]
      ;; o1 has 3 picks = cap, so it fills its own wave; o2(2)+o3(1) can share
      (is (>= (count waves) 2))
      (is (every? #(<= (count (:picks %)) 3) waves)))))

(deftest zone-occupancy-sweep
  (testing "peak concurrent occupancy per zone; touching endpoints don't overlap"
    (let [entries [{:zone "z-golden" :t-in 0 :t-out 5}
                   {:zone "z-golden" :t-in 3 :t-out 8}   ; overlaps the first → peak 2
                   {:zone "z-golden" :t-in 8 :t-out 9}   ; touches at 8 → not concurrent
                   {:zone "z-bulk"   :t-in 0 :t-out 5}]]
      (is (= 2 (get (pick/zone-occupancy entries) "z-golden")))
      (is (= 1 (get (pick/zone-occupancy entries) "z-bulk"))))))

(deftest congestion-detection
  (testing "overflow when peak exceeds zone capacity; worst-first"
    (let [entries [{:zone "aisle-1" :t-in 0 :t-out 5}
                   {:zone "aisle-1" :t-in 1 :t-out 6}
                   {:zone "aisle-1" :t-in 2 :t-out 7}    ; peak 3
                   {:zone "aisle-2" :t-in 0 :t-out 5}]]
      (is (pick/congested? entries 2))                  ; 3 > cap 2
      (is (not (pick/congested? entries 3)))            ; 3 ≤ cap 3
      (let [ovf (pick/congestion-overflows entries 2)]
        (is (= "aisle-1" (:zone (first ovf))))
        (is (= 1 (:over (first ovf))))))))

;; ── handoff (cross-actor chain edges: niyaku→kuramori→todoke) ────────────────
(deftest inbound-from-niyaku
  (testing "niyaku discharge → kuramori putaway intents, source-attributed"
    (let [hs (ho/inbound-handoff [{:box-id "b1" :sku-id "sku-fast" :weight-kg 8 :temp :ambient}
                                  {:box-id "b2" :sku-id "sku-cold" :weight-kg 9 :temp :reefer}])]
      (is (= 2 (count hs)))
      (is (every? #(= "niyaku" (:from-actor %)) hs))
      (is (every? #(= "kuramori" (:to-actor %)) hs))
      (is (= :inbound (:kind (first hs))))
      (is (= "sku-fast" (get-in (first hs) [:payload :sku-id]))))))

(deftest outbound-to-todoke
  (testing "completed picked order → todoke last-mile delivery intent"
    (let [h (ho/outbound-handoff {:id "ord-1" :picks ["s-g1" "s-r1" "s-b1"]})]
      (is (= "kuramori" (:from-actor h)))
      (is (= "todoke" (:to-actor h)))
      (is (= :outbound (:kind h)))
      (is (= 3 (get-in h [:payload :parcel-count]))))))

(deftest handoff-provenance-gate
  (testing "G10 — an orphan handoff (no source/destination) RAISES"
    (is (thrown? clojure.lang.ExceptionInfo (ho/assert-handoff! {:id "x" :to-actor "todoke"})))
    (is (thrown? clojure.lang.ExceptionInfo (ho/assert-handoff! {:id "x" :from-actor "kuramori"})))
    (is (= "kuramori" (:from-actor (ho/assert-handoff! {:id "x" :from-actor "kuramori" :to-actor "todoke"}))))))

(deftest handoff-emit-shape
  (testing "emits well-formed EDN :handoff/* 縁 with actor provenance on every edge"
    (let [hs (conj (ho/inbound-handoff [{:box-id "b1" :sku-id "s" :weight-kg 8 :temp :ambient}])
                   (ho/outbound-handoff {:id "ord-1" :picks ["s-g1"]}))
          out (ho/emit hs 1)]
      (is (re-find #":handoff/from-actor" out))
      (is (re-find #":handoff/to-actor" out))
      (is (re-find #"en\.handoff\.niyaku\.kuramori\." out))
      (is (re-find #"en\.handoff\.kuramori\.todoke\." out))
      (is (vector? (clojure.edn/read-string out))))))

(let [{:keys [fail error]} (run-tests 'kuramori.methods.test-kuramori)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
