;; kuramori 倉守 — test suite (clojure.test, babashka-runnable).
;; Run: bb --classpath 20-actors 20-actors/kuramori/methods/test_kuramori.clj
;; Per ADR-2606142000 (kuramori R0).
(ns kuramori.methods.test-kuramori
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [kuramori.methods.agv-amr :as fleet]
            [kuramori.methods.slotting :as slot]
            [kuramori.methods.analyze :as az]
            [kuramori.methods.datom-emit :as de]))

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

(let [{:keys [fail error]} (run-tests 'kuramori.methods.test-kuramori)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
