;; soma 杣 — end-to-end forestry-stand analyzer (orchestrator).
;;
;; Loads the forest-stand seed and runs the R0 sim pipeline:
;;   1. fell — for every harvestable tree, plan a directional fell (notch + hinge +
;;      back cut) aimed into a clear lane; protected/no-cut trees are REFUSED (G7),
;;      unsafe fells (fall zone overlapping a human/road/watercourse) are REFUSED (G5);
;;   2. buck — cut-to-length value optimization of each felled stem (sawlog>pulp DP);
;;   3. extract — slope-limited, low-ground-impact forwarder route to the landing
;;      (refuses over-grade / over-pressure / protected soil, G2).
;;
;; Pure Clojure, no deps → babashka-runnable AND kotoba-pywasm-portable.
;; Per ADR-2606142010 (soma R0).
(ns soma.methods.analyze
  (:require [clojure.edn :as edn]
            [soma.methods.fell-plan :as fp]
            [soma.methods.harvester :as hv]
            [soma.methods.extraction :as ex]))

(defn load-seed
  "Read the forest-stand EDN seed into a Clojure map."
  [path]
  (edn/read-string (slurp path)))

(defn- aim-away-from-exclusions
  "Choose a fell aim azimuth (deg) for a tree: bias toward its natural lean, but
   if that line is blocked, sweep candidate azimuths and pick the first that
   clears every exclusion. Returns an azimuth, or nil if none clears (caller then
   records the tree as unsafe-to-fell rather than forcing it)."
  [tree exclusions]
  (let [candidates (cons (:lean-az tree 0.0)
                         (map double (range 0 360 15)))]
    (some (fn [aim]
            (let [az (fp/predict-fall-az {:aim-az aim
                                          :lean-az (:lean-az tree 0.0)
                                          :lean-deg (:lean-deg tree 0.0)
                                          :wind-az (:wind-az tree 0.0)
                                          :wind-mps (:wind-mps tree 0.0)})]
              (when (fp/safe-fell? tree az exclusions) aim)))
          candidates)))

(defn run
  "Run the full R0 analysis over a loaded seed map. Returns a report map.
   Each tree lands in exactly one of {:fells :refused :unsafe}."
  [seed]
  (let [{:keys [trees exclusions price-table forwarder route]} seed
        soil (get-in seed [:stand :soil] :firm)
        ;; 1. fell + 2. buck per tree
        results
        (reduce
         (fn [acc tree]
           (cond
             ;; G7 — protected / no-cut: refuse, do not fell
             (fp/protected? tree)
             (update acc :refused conj {:tree (:id tree) :reason :protected})
             :else
             (if-let [aim (aim-away-from-exclusions tree exclusions)]
               (let [plan (fp/plan-fell tree aim exclusions)
                     ;; merchantable stem length ≈ height minus crown/butt trim
                     stem-len (* 0.80 (:height-m tree))
                     buck (hv/buck-summary (hv/buck-stem stem-len price-table))]
                 (update acc :fells conj
                         {:tree (:id tree)
                          :fall-az (:fall-az plan)
                          :hinge-m (:hinge-m plan)
                          :stem-length-m stem-len
                          :buck buck}))
               ;; G5 — no safe aim clears the exclusions
               (update acc :unsafe conj {:tree (:id tree) :reason :no-clear-fall-line}))))
         {:fells [] :refused [] :unsafe []}
         trees)
        ;; 3. extract — plan the forwarder route (raises if over-grade/over-impact)
        extraction (ex/plan-route forwarder soil (:segments route))
        total-value (reduce + 0.0 (map #(get-in % [:buck :value]) (:fells results)))]
    (assoc results
           :extraction extraction
           :total-value total-value
           :n-trees (count trees))))

(defn report-str
  "Human-readable report (for out/ and Murakumo narration input, G6)."
  [res]
  (str ";; soma 杣 — forestry-stand R0 analysis\n"
       "trees: " (:n-trees res) "\n"
       "felled (safe): " (count (:fells res)) "\n"
       "refused (protected/no-cut, G7): " (pr-str (mapv :tree (:refused res))) "\n"
       "unsafe (no clear fall line, G5): " (pr-str (mapv :tree (:unsafe res))) "\n"
       "total bucked value: " (format "%.1f" (:total-value res)) "\n"
       "extraction segments: " (get-in res [:extraction :n-segments])
       " (max grade " (format "%.1f" (get-in res [:extraction :max-grade-pct])) "%)\n"))

(defn -main [& args]
  (let [path (or (first args) "20-actors/soma/data/stand.edn")
        res (run (load-seed path))]
    (print (report-str res))
    (flush)))
