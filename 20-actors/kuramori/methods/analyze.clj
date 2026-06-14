;; kuramori 倉守 — end-to-end warehouse analyzer (orchestrator).
;;
;; Loads the warehouse seed and runs the R0 sim pipeline:
;;   1. ABC-class every SKU + velocity-greedy slotting (golden-zone packing);
;;   2. build the outbound pick-route (nearest-neighbour) over the order's slots;
;;   3. dispatch the pick legs across the electric fleet (LPT makespan), with the
;;      shared-zone speed cap + battery opportunity-charge gate applied.
;;
;; Pure Clojure, no deps → babashka-runnable AND kotoba-pywasm-portable.
;; Per ADR-2606142000 (kuramori R0).
(ns kuramori.methods.analyze
  (:require [clojure.edn :as edn]
            [kuramori.methods.slotting :as slot]
            [kuramori.methods.agv-amr :as fleet]))

(defn load-seed
  "Read the warehouse EDN seed into a Clojure map."
  [path]
  (edn/read-string (slurp path)))

(defn run
  "Run the full R0 analysis over a loaded seed map. Returns a report map."
  [seed]
  (let [skus (:skus seed)
        slots (:slots seed)
        by-slot (into {} (map (juxt :id identity) slots))
        ;; 1. slotting
        slotting (slot/assign-slots skus slots {})
        classed (into {} (map (fn [s] [(:id s) (slot/abc-class (:velocity s 0) {})]) skus))
        ;; 2. pick-route for the order (dock origin [0 0])
        order (:order seed)
        pick-coords (map #(:coord (by-slot %)) (:picks order))
        route-m (slot/pick-route [0 0] pick-coords)
        ;; 3. dispatch the pick legs across the fleet
        ;;    one move per pick leg (face → slot), shared? for zones near the human face
        moves (map-indexed
               (fn [i sid]
                 (let [s (by-slot sid)]
                   {:move-id (str "pick-" i "-" sid)
                    :distance-m (:dist-from-face s 0)
                    :shared? (= :golden (:kind (->> slots (filter #(= (:id %) sid)) first)))}))
               (:picks order))
        veh (fleet/make-vehicle :amr)
        disp (fleet/dispatch moves (mapv :id (:fleet seed)) veh)
        ;; battery gate: would the longest single leg breach the reserve floor?
        max-leg (apply max 0.0 (map :distance-m moves))
        charge-needed (fleet/needs-charge? veh max-leg)]
    {:slotting slotting
     :abc classed
     :pick-route-m route-m
     :dispatch disp
     :battery {:max-leg-m max-leg :charge-needed charge-needed}}))

(defn report-str
  "Human-readable report (for out/ and Murakumo narration input, G6)."
  [res]
  (str ";; kuramori 倉守 — warehouse R0 analysis\n"
       "ABC: " (pr-str (:abc res)) "\n"
       "slotting placement: " (pr-str (get-in res [:slotting :placement])) "\n"
       "weighted-travel: " (format "%.1f" (get-in res [:slotting :weighted-travel])) "\n"
       "pick-route (m): " (format "%.1f" (:pick-route-m res)) "\n"
       "dispatch makespan (s): " (format "%.1f" (get-in res [:dispatch :makespan])) "\n"
       "battery charge-needed: " (get-in res [:battery :charge-needed]) "\n"))

(defn -main [& args]
  (let [path (or (first args) "20-actors/kuramori/data/warehouse.edn")
        res (run (load-seed path))]
    (print (report-str res))
    (flush)))
