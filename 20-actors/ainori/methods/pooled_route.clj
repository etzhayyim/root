;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/ainori/methods/pooled_route.py (unit_refactor stage 0)
;; pooled_route — ainori multi-stop pooled sequencing, REUSING the todoke route core.
(ns root.ainori.methods.pooled-route
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare todoke-methods sequence-stops pooled-route plan-pooled-trip)

;; TODO: port-failed unit _TODOKE_METHODS (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpl4octgvq/scratch.clj:3:172: )
;; _TODOKE_METHODS = os.path.abspath(
;;     os.path.join(os.path.dirname(__file__), "..", "..", "todoke", "methods")
;; )
;; _AINORI_PY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "py"))
(def todoke-methods nil) ;; TODO: port-failed const

;; TODO: port-failed unit sequence_stops (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpdulol9zc/scratch.clj:3:3: wa)
;; def sequence_stops(stops: list) -> tuple[list, float]:
;;     """Order a list of Stops (stops[0] pinned as origin) and return (order_of_ids, length_m).
;; 
;;     This IS todoke's sequencing core — the same `_nearest_neighbour` + `_two_opt` primitives the
;;     Rust crate mirrors. The parity test asserts it matches `todoke.plan_last_mile` order, so
;;     ainori provably reuses rather than reimplements the engine. No safety envelope is applied
;;     here (sequencing is charter-neutral; ainori's vehicular envelope lives in agent.py, G3)."""
;;     if not stops:
;;         return [], 0.0
;;     seq = _two_opt(_nearest_neighbour(stops), stops)
;;     length = sum(stops[seq[i]].dist(stops[seq[i + 1]]) for i in range(len(seq) - 1))
;;     return [stops[i].id for i in seq], length
(defn sequence-stops [& _]
  (throw (ex-info "TODO: port-failed" {:from "sequence_stops"})))

;; TODO: port-failed unit pooled_route (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpl4ij2l7d/scratch.clj:4:20: e)
;; def pooled_route(carrier_origin: tuple, rider_points: list) -> dict:
;;     """Build a pooled vehicular route: the carrier's origin (id 0) plus each rider's pickup /
;;     dropoff point, sequenced by the reused todoke core to minimise added distance (G11 — fill a
;;     trip already happening). `carrier_origin` is (x, y); `rider_points` is a list of
;;     {id, x, y, zone}. Returns {order, lengthM, occupancy}."""
;;     stops = [Stop(0, float(carrier_origin[0]), float(carrier_origin[1]), "arterial")]
;;     for p in rider_points:
;;         stops.append(Stop(int(p["id"]), float(p["x"]), float(p["y"]), p.get("zone", "arterial")))
;;     order, length = sequence_stops(stops)
;;     return {"order": order, "lengthM": length, "occupancy": len(rider_points)}
(defn pooled-route [& _]
  (throw (ex-info "TODO: port-failed" {:from "pooled_route"})))

;; TODO: port-failed unit plan_pooled_trip (assembled-lint error)
;; def plan_pooled_trip(carrier_origin: tuple, rider_points: list, fuel_wear_minor: int) -> dict:
;;     """End-to-end pooled trip: sequence the stops with the reused todoke core, then split the
;;     REAL fuel/wear cost flat across the pooled riders with ainori's no-surge cost_share (composed,
;;     not duplicated). Returns the route + per-rider share + total collected.
;; 
;;     Honest cost-share property (G1/G2): totalCollected = share × occupancy NEVER exceeds the real
;;     fuel_wear (integer division rounds the per-rider share DOWN, so the carrier absorbs any
;;     remainder — the platform/carrier never profits)."""
;;     route = pooled_route(carrier_origin, rider_points)
;;     occ = route["occupancy"]
;;     share = cost_share(fuel_wear_minor, occ)
;;     return {
;;         **route,
;;         "fuelWearMinor": int(fuel_wear_minor),
;;         "costSharePerRiderMinor": share,
;;         "totalCollectedMinor": share * occ,   # ≤ fuelWearMinor by construction (no profit)
;;     }
(defn plan-pooled-trip [& _]
  (throw (ex-info "TODO: port-failed" {:from "plan_pooled_trip"})))

