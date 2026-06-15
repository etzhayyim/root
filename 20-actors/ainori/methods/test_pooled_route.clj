;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/ainori/methods/test_pooled_route.py (unit_refactor stage 0)
;; test_pooled_route — pins ainori's pooled sequencing to the REUSED todoke route core.
(ns root.ainori.methods.test-pooled-route
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare fixture parity pooled-route plan-pooled-trip)

;; TODO: port-failed unit _fixture (bb-compile error)
;; def _fixture():
;;     # pedestrian-zone fixture so todoke.plan_last_mile's envelope accepts it
;;     return [
;;         todoke.Stop(0, 0.0, 0.0, "sidewalk"),
;;         todoke.Stop(1, 3.0, 0.0, "sidewalk"),
;;         todoke.Stop(2, 3.0, 3.0, "sidewalk"),
;;         todoke.Stop(3, 0.0, 3.0, "sidewalk"),
;;         todoke.Stop(4, 1.0, 1.0, "sidewalk"),
;;     ]
(defn fixture [& _]
  (throw (ex-info "TODO: port-failed" {:from "_fixture"})))

;; TODO: port-failed unit Parity (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpp6c6q1w3/scratch.clj:3:8: er)
;; class Parity(unittest.TestCase):
;;     def test_parity_with_todoke(self):
;;         stops = _fixture()
;;         order_a, len_a = pr.sequence_stops(stops)
;;         order_t, len_t = todoke.plan_last_mile(stops, sae_level=4, commanded_mps=1.5)
;;         self.assertEqual(order_a, order_t)            # SAME engine, not a fork
;;         self.assertAlmostEqual(len_a, len_t, places=9)
;; 
;;     def test_reuses_todoke_primitives(self):
;;         # pooled_route imports the actual todoke Stop class (identity, not a copy)
;;         self.assertIs(pr.Stop, todoke.Stop)
(defn parity [& _]
  (throw (ex-info "TODO: port-failed" {:from "Parity"})))

;; TODO: port-failed unit PooledRoute (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpcv7kl6nb/scratch.clj:2:21: w)
;; class PooledRoute(unittest.TestCase):
;;     def test_origin_pinned_first(self):
;;         out = pr.pooled_route((0.0, 0.0), [
;;             {"id": 1, "x": 5.0, "y": 0.0}, {"id": 2, "x": 1.0, "y": 0.0}])
;;         self.assertEqual(out["order"][0], 0)          # carrier origin pinned
;;         self.assertEqual(out["occupancy"], 2)
;; 
;;     def test_vehicular_zone_sequences(self):
;;         # ainori uses road/arterial zones — sequencing works WITHOUT todoke's pedestrian envelope
;;         out = pr.pooled_route((0.0, 0.0), [
;;             {"id": 1, "x": 10.0, "y": 0.0, "zone": "expressway"},
;;             {"id": 2, "x": 2.0, "y": 0.0, "zone": "arterial"}])
;;         self.assertEqual(out["order"], [0, 2, 1])     # nearest-first sequencing
;;         self.assertGreater(out["lengthM"], 0)
;; 
;;     def test_empty(self):
;;         self.assertEqual(pr.sequence_stops([]), ([], 0.0))
(defn pooled-route [& _]
  (throw (ex-info "TODO: port-failed" {:from "PooledRoute"})))

;; TODO: port-failed unit PlanPooledTrip (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmph76skeof/scratch.clj:25:42: )
;; class PlanPooledTrip(unittest.TestCase):
;;     def test_composes_route_and_cost_share(self):
;;         out = pr.plan_pooled_trip((0.0, 0.0), [
;;             {"id": 1, "x": 5.0, "y": 0.0}, {"id": 2, "x": 1.0, "y": 0.0}], 1_200_000)
;;         self.assertEqual(out["order"][0], 0)               # routing (todoke core)
;;         self.assertEqual(out["occupancy"], 2)
;;         self.assertEqual(out["costSharePerRiderMinor"], 600_000)   # cost_share split (no surge)
;; 
;;     def test_no_profit_invariant(self):
;;         # odd cost: per-rider rounds down; total collected ≤ real fuel/wear (carrier absorbs rest)
;;         out = pr.plan_pooled_trip((0.0, 0.0), [
;;             {"id": 1, "x": 5.0, "y": 0.0}, {"id": 2, "x": 1.0, "y": 0.0},
;;             {"id": 3, "x": 3.0, "y": 0.0}], 1_000_000)
;;         self.assertLessEqual(out["totalCollectedMinor"], out["fuelWearMinor"])
;; 
;;     def test_pooling_lowers_each_share(self):
;;         two = pr.plan_pooled_trip((0.0, 0.0), [{"id": 1, "x": 1.0, "y": 0.0},
;;                                                {"id": 2, "x": 2.0, "y": 0.0}], 1_200_000)
;;         three = pr.plan_pooled_trip((0.0, 0.0), [{"id": 1, "x": 1.0, "y": 0.0},
;;                                                  {"id": 2, "x": 2.0, "y": 0.0},
;;                                                  {"id": 3, "x": 3.0, "y": 0.0}], 1_200_000)
;;         self.assertLess(three["costSharePerRiderMinor"], two["costSharePerRiderMinor"])
;; 
;;     def test_uses_real_agent_cost_share(self):
;;         # composition, not duplication: pr.cost_share IS ainori agent's cost_share
;;         import agent as ainori_agent  # noqa: PLC0415
;;         self.assertIs(pr.cost_share, ainori_agent.cost_share)
(defn plan-pooled-trip [& _]
  (throw (ex-info "TODO: port-failed" {:from "PlanPooledTrip"})))

