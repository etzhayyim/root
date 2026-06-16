(ns silicon.methods.test-wafer-handler
  "Tests for silicon.methods.wafer-handler."
  (:require [clojure.test :refer [deftest is]]
            [silicon.methods.wafer-handler :as wh]))

(deftest test-move-time-monotonic-in-distance
  (let [a (wh/move-time {:dist 0.5})
        b (wh/move-time {:dist 1.5})
        c (wh/move-time {:dist 6.0})]
    (is (< a b))
    (is (< b c))
    (is (pos? a))))

(deftest test-short-move-is-triangular
  ;; a very short move never reaches vmax; still positive, includes settle
  (let [t (wh/move-time {:dist 0.01 :vmax 3.14 :acc 12.0 :settle 0.15})]
    (is (> t 0.15))
    (is (< t 0.5))))

(deftest test-transfer-time-positive
  (is (pos? (wh/transfer-time {})))
  ;; bigger rotation costs more
  (is (< (wh/transfer-time {:swap-dist 0.5})
         (wh/transfer-time {:swap-dist 3.0}))))

(deftest test-loadlock-cycle
  ;; lower base pressure (deeper vacuum) takes longer to pump
  (is (< (wh/loadlock-cycle {:base-pa 10.0})
         (wh/loadlock-cycle {:base-pa 0.1}))))

(deftest test-route-cycle-time
  (let [t (wh/route-cycle-time [60.0 120.0 90.0])]
    ;; ≥ sum of process times (240) plus transfers
    (is (> t 240.0))))

(deftest test-throughput-bottleneck-bound
  (let [proc [60.0 120.0 90.0]
        out (wh/throughput-wph proc :slots 25)]
    (is (pos? (:wph out)))
    (is (pos? (:foup-time-min out)))
    ;; bottleneck = max process + one transfer
    (is (> (:bottleneck-s out) 120.0))
    ;; more wafers in the FOUP → higher steady-state throughput (amortized loadlock)
    (let [few (wh/throughput-wph proc :slots 5)
          many (wh/throughput-wph proc :slots 50)]
      (is (> (:wph many) (:wph few))))))

(deftest test-schedule-feasible
  (is (wh/schedule-feasible? [60.0 120.0] (wh/transfer-time {}))))
