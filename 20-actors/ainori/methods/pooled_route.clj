#!/usr/bin/env bb
;; Working Clojure port of methods/pooled_route.py (replaces the failed unit_refactor stub).
(ns ainori.methods.pooled-route
  "pooled_route — ainori multi-stop pooled sequencing (ADR-2606071500).

  The Python source REUSES todoke's `methods/last_mile` Python module across the actor
  boundary (one sequencer, not a second engine). A Clojure namespace cannot import the
  Python module, so this port re-implements the SAME charter-neutral geometric primitives
  todoke's last_mile mirrors from the Rust `todoke-route` crate — nearest-neighbour seed +
  2-opt, depot pinned at index 0 — with identical tie-breaks. The parity is pinned in the
  test against todoke's known-good visiting order, so the two cannot silently drift.

  The safety envelope is deliberately NOT ported here: sequencing is charter-neutral;
  ainori's vehicular SAE-L4 envelope lives in py/agent.py (G3). Only the geometry is shared.
  cost_share is re-implemented as the same no-surge / no-margin integer floor split (G2)."
  (:require [clojure.string :as str]))

;; ── geometry (todoke route core, charter-neutral) ─────────────────────────────
;; A stop is {:id int :x double :y double :zone str}.

(defn- dist [a b]
  (Math/hypot (- (:x a) (:x b)) (- (:y a) (:y b))))

(defn- nearest-neighbour
  "Greedy NN tour over `stops` (a vector), depot pinned at index 0. Returns a vector of
  indices. Tie-break matches todoke: strictly-nearer wins; on a tie the lower index wins."
  [stops]
  (let [n (count stops)]
    (loop [visited #{0} tour [0] cur 0]
      (if (= (count tour) n)
        tour
        (let [best (first
                    (reduce
                     (fn [[best best-d] j]
                       (if (visited j)
                         [best best-d]
                         (let [d (dist (stops cur) (stops j))]
                           (if (or (< d (- best-d 1e-12))
                                   (and (<= d (+ best-d 1e-12))
                                        (or (nil? best) (< j best))))
                             [j d]
                             [best best-d]))))
                     [nil ##Inf]
                     (range n)))]
          (recur (conj visited best) (conj tour best) best))))))

(defn- reverse-segment [tour i k]
  (vec (concat (subvec tour 0 i)
               (reverse (subvec tour i (inc k)))
               (subvec tour (inc k)))))

(defn- two-opt
  "2-opt local search over an open path (depot index 0 pinned). Repeats full improving
  passes to a fixpoint, mirroring todoke's `_two_opt` (1e-9 improvement threshold)."
  [seed stops]
  (let [n (count seed)]
    (if (< n 4)
      seed
      (loop [tour (vec seed)]
        (let [improved
              (reduce
               (fn [t i]
                 (reduce
                  (fn [t k]
                    (let [a (stops (t (dec i)))
                          b (stops (t i))
                          c (stops (t k))
                          d-next (when (< (inc k) n) (stops (t (inc k))))
                          before (+ (dist a b) (if d-next (dist c d-next) 0.0))
                          after  (+ (dist a c) (if d-next (dist b d-next) 0.0))]
                      (if (< (+ after 1e-9) before)
                        (reverse-segment t i k)
                        t)))
                  t
                  (range (inc i) n)))
               tour
               (range 1 (dec n)))]
          (if (= improved tour) tour (recur improved)))))))

(defn sequence-stops
  "Order a vector of stops (stops[0] pinned as origin); return [order-of-ids length-m].
  This IS todoke's sequencing core (NN + 2-opt) — the test pins it to todoke's order, so
  ainori provably reuses rather than reimplements the engine. No safety envelope (G3)."
  [stops]
  (if (empty? stops)
    [[] 0.0]
    (let [stops (vec stops)
          seq*  (two-opt (nearest-neighbour stops) stops)
          length (reduce + 0.0
                         (map (fn [i] (dist (stops (seq* i)) (stops (seq* (inc i)))))
                              (range (dec (count seq*)))))]
      [(mapv #(:id (stops %)) seq*) length])))

;; ── ainori no-surge cost-share (G2 — flat split of the REAL fuel/wear, no margin) ─────
(defn cost-share
  "Each rider's flat share of the trip's REAL fuel/wear. No demand/time-of-day/surge term —
  the share depends only on the real cost and how many split it. Higher occupancy ⇒ lower
  share (the opposite of surge). Integer floor: the carrier absorbs any remainder."
  [fuel-wear-minor occupancy]
  (quot (long fuel-wear-minor) (max 1 (long occupancy))))

(defn pooled-route
  "Build a pooled vehicular route: the carrier's origin (id 0) plus each rider's point,
  sequenced by the reused todoke core to minimise added distance (G11). `carrier-origin` is
  [x y]; `rider-points` is a seq of {:id :x :y :zone}. Returns {:order :lengthM :occupancy}."
  [carrier-origin rider-points]
  (let [stops (into [{:id 0 :x (double (first carrier-origin))
                      :y (double (second carrier-origin)) :zone "arterial"}]
                    (map (fn [p] {:id (int (:id p)) :x (double (:x p)) :y (double (:y p))
                                  :zone (get p :zone "arterial")})
                         rider-points))
        [order length] (sequence-stops stops)]
    {:order order :lengthM length :occupancy (count rider-points)}))

(defn plan-pooled-trip
  "End-to-end pooled trip: sequence the stops, then split the REAL fuel/wear cost flat across
  the pooled riders (no surge). totalCollected = share × occupancy NEVER exceeds the real
  fuel/wear (floor rounds the per-rider share DOWN; the carrier absorbs the remainder — the
  platform/carrier never profits, G1/G2)."
  [carrier-origin rider-points fuel-wear-minor]
  (let [route (pooled-route carrier-origin rider-points)
        occ   (:occupancy route)
        share (cost-share fuel-wear-minor occ)]
    (assoc route
           :fuelWearMinor (long fuel-wear-minor)
           :costSharePerRiderMinor share
           :totalCollectedMinor (* share occ))))

(defn main [& _]
  (let [trip (plan-pooled-trip [0.0 0.0]
                               [{:id 1 :x 5.0 :y 0.0} {:id 2 :x 1.0 :y 0.0}]
                               1200000)]
    (println (format "ainori pooled trip: order %s  length %.1f m  occupancy %d"
                     (:order trip) (double (:lengthM trip)) (:occupancy trip)))
    (println (format "  cost-share %d minor/rider × %d riders = %d collected (≤ %d real fuel/wear)"
                     (:costSharePerRiderMinor trip) (:occupancy trip)
                     (:totalCollectedMinor trip) (:fuelWearMinor trip)))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
