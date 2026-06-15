#!/usr/bin/env bb
;; Working Clojure port of methods/agv_transfer.py.
(ns niyaku.methods.agv-transfer
  "agv_transfer — automated guided vehicle (AGV) horizontal-transport core (ADR-2606082000).

  After the STS crane lands a box on the quay apron, a battery AGV carries it to the yard
  stack. Planning core behind the yard_transfer cell:
    * a trapezoidal velocity profile (accel→cruise→decel, or triangular when the leg is too
      short to reach cruise) giving time-optimal travel time;
    * a lane-segment conflict check — two AGVs on a one-way segment must not have overlapping
      occupancy windows (deadlock/collision avoidance);
    * a greedy LPT dispatch minimising makespan.

  Pure planning compute; dispatches no real vehicle (G12 no-server-key). Electric AGV with
  regenerative braking (G8).

  Run:  bb --classpath 20-actors 20-actors/niyaku/methods/agv_transfer.clj"
  (:require [clojure.string :as str]))

(defn make-agv [& {:keys [v-max a-max length-m] :or {v-max 6.0 a-max 0.8 length-m 16.0}}]
  {:v-max v-max :a-max a-max :length-m length-m})

(defn- value-error [msg] (throw (ex-info msg {:type :value-error})))

(defn travel-time
  "Time-optimal travel time over a straight leg under a trapezoidal profile (triangular if too
  short to reach v-max)."
  [distance-m agv]
  (cond
    (< distance-m 0) (value-error "distance must be non-negative")
    (zero? distance-m) 0.0
    :else
    (let [a (:a-max agv) v (:v-max agv)
          d-to-vmax (/ (* v v) a)]               ; distance to accel to v-max then decel to 0
      (if (>= distance-m d-to-vmax)
        (let [t-ramp (/ v a) d-cruise (- distance-m d-to-vmax)]
          (+ (* 2.0 t-ramp) (/ d-cruise v)))
        (let [vp (Math/sqrt (* a distance-m))]   ; triangular peak velocity
          (/ (* 2.0 vp) a))))))

;; a reservation {:segment :agv-id :t-in :t-out}; a move {:move-id :distance-m}.
(defn reservation [segment agv-id t-in t-out]
  {:segment segment :agv-id agv-id :t-in (double t-in) :t-out (double t-out)})

(defn reservations-conflict?
  "True iff two reservations share a segment (different AGVs) and overlap in time. Touching at
  an endpoint (t_out == t_in) is NOT a conflict."
  [r1 r2]
  (if (or (not= (:segment r1) (:segment r2)) (= (:agv-id r1) (:agv-id r2)))
    false
    (and (< (:t-in r1) (:t-out r2)) (< (:t-in r2) (:t-out r1)))))

(defn find-conflicts
  "All conflicting index pairs [i j] (i<j) in a reservation vector."
  [reservations]
  (let [v (vec reservations) n (count v)]
    (vec (for [i (range n) j (range (inc i) n)
               :when (reservations-conflict? (v i) (v j))]
           [i j]))))

(defn move [move-id distance-m] {:move-id move-id :distance-m (double distance-m)})

(defn- argmin-first
  "Item of `coll` minimising (keyfn item); first one wins ties (matches Python's min)."
  [coll keyfn]
  (reduce (fn [best x] (if (< (keyfn x) (keyfn best)) x best)) (first coll) (rest coll)))

(defn dispatch
  "Greedy makespan-minimising assignment: each move (longest-first / LPT) goes to the AGV that
  frees up soonest. Returns {:assignment {agv [move-ids]} :finish-time {agv secs}}."
  [moves agv-ids agv]
  (when (empty? agv-ids) (value-error "need at least one AGV"))
  (let [assignment (atom (into {} (map (fn [a] [a []]) agv-ids)))
        finish (atom (into {} (map (fn [a] [a 0.0]) agv-ids)))]
    (doseq [mv (sort-by #(- (:distance-m %)) moves)]
      (let [a (argmin-first agv-ids #(@finish %))]
        (swap! assignment update a conj (:move-id mv))
        (swap! finish update a + (travel-time (:distance-m mv) agv))))
    {:assignment @assignment :finish-time @finish}))

(defn makespan [res]
  (if (seq (:finish-time res)) (reduce max (vals (:finish-time res))) 0.0))

(defn main [& _]
  (let [agv (make-agv)
        moves [(move "big" 300) (move "s1" 20) (move "s2" 20)]
        res (dispatch moves ["AGV1" "AGV2"] agv)]
    (println "niyaku AGV dispatch (LPT, makespan-balanced):")
    (doseq [[a ms] (sort-by key (:assignment res))]
      (println (format "  %s ← %s  (busy %.2fs)" a (str/join ", " ms)
                       (double (get (:finish-time res) a)))))
    (println (format "  makespan %.2fs" (makespan res)))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
