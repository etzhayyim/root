#!/usr/bin/env bb
;; Working Clojure port of methods/stow_plan.py.
(ns niyaku.methods.stow-plan
  "stow_plan — container stowage slotting + discharge/load sequencing (ADR-2606082000, niyaku R0).

  A container ship cell is addressed by bay / row / tier (ISO stowage coords). Automated
  handling needs a STOW PLAN (which slot each box occupies — respecting weight-on-top, IMDG
  hazmat segregation, reefer-plug rows, and port-rotation so an earlier-discharge box is never
  buried under a later one) and a WORK SEQUENCE (discharge order with no re-handle).

  Pure planning compute; emits no outward action. G9: an infeasible request RAISES (stow-error),
  never silently relaxes a safety constraint. reefer rows = the cold-chain (food/seafood) plug
  slots — the food-logistics tie-in.

  Run:  bb --classpath 20-actors 20-actors/niyaku/methods/stow_plan.clj"
  (:require [clojure.string :as str]))

;; a slot {:bay :row :tier} (tier increases upward, 0 = bottom); a container
;; {:box-id :weight-t :discharge-port :reefer :hazmat}.
(defn slot [bay row tier] {:bay bay :row row :tier tier})
(defn slot-key [s] [(:bay s) (:row s) (:tier s)])

(defn container [box-id weight-t discharge-port & {:keys [reefer hazmat] :or {reefer false hazmat nil}}]
  {:box-id box-id :weight-t (double weight-t) :discharge-port discharge-port
   :reefer reefer :hazmat hazmat})

(defn stow-error [msg] (throw (ex-info msg {:type :stow-error})))
(defn stow-error? [e]
  (and (instance? clojure.lang.ExceptionInfo e) (= :stow-error (:type (ex-data e)))))

(defn slot-of [plan box-id] (get-in plan [:assignments box-id]))

(defn build-stow-plan
  "Assign every container a slot under capacity / port-rotation / weight-on-top / reefer-row /
  IMDG-segregation constraints. Raises (stow-error) if it cannot place all boxes."
  [containers rotation bays rows tiers & {:keys [reefer-rows] :or {reefer-rows ::all}}]
  (when (empty? rotation) (stow-error "rotation must list at least one discharge port"))
  (let [reefer-rows (set (if (= reefer-rows ::all) (range rows) reefer-rows))
        rot-index (into {} (map-indexed (fn [i p] [p i]) rotation))]
    (doseq [c containers]
      (when-not (contains? rot-index (:discharge-port c))
        (stow-error (str (:box-id c) ": discharge_port " (:discharge-port c) " not in rotation"))))
    ;; latest-discharge first (to the BOTTOM), then heaviest first; stable for ties.
    (let [order (sort-by (fn [c] [(- (rot-index (:discharge-port c))) (- (:weight-t c))]) containers)
          columns (vec (for [b (range bays) r (range rows)] [b r]))
          col-height (atom (zipmap columns (repeat 0)))
          col-hazmat (atom (zipmap columns (repeat nil)))
          col-top-weight (atom (zipmap columns (repeat Double/POSITIVE_INFINITY)))
          col-top-port (atom (zipmap columns (repeat -1)))
          assignments (atom {})]
      (doseq [c order]
        (let [placed (atom false)]
          (doseq [[b r :as col] columns :while (not @placed)]
            (when (and (< (@col-height col) tiers)
                       (or (not (:reefer c)) (contains? reefer-rows r))
                       (or (nil? (:hazmat c))
                           (nil? (@col-hazmat col))
                           (= (@col-hazmat col) (:hazmat c)))
                       (<= (:weight-t c) (@col-top-weight col))
                       (or (< (@col-top-port col) 0)
                           (<= (rot-index (:discharge-port c)) (@col-top-port col))))
              (let [tier (@col-height col)]
                (swap! assignments assoc (:box-id c) (slot b r tier))
                (swap! col-height assoc col (inc tier))
                (swap! col-top-weight assoc col (:weight-t c))
                (swap! col-top-port assoc col (rot-index (:discharge-port c)))
                (when (:hazmat c) (swap! col-hazmat assoc col (:hazmat c)))
                (reset! placed true))))
          (when-not @placed (stow-error (str "no feasible slot for " (:box-id c))))))
      {:assignments @assignments :rotation (vec rotation)})))

(defn- columns-of [plan]
  (group-by (fn [[_ s]] [(:bay s) (:row s)]) (seq (:assignments plan))))

(defn discharge-sequence
  "Order to discharge boxes: top tier first within each column; columns in (bay,row) order.
  No re-handle (the stow plan already placed earlier-discharge boxes higher)."
  [plan _port]
  (let [by-col (columns-of plan)]
    (vec (mapcat (fn [col]
                   (map first (sort-by (fn [[_ s]] (- (:tier s))) (get by-col col))))
                 (sort (keys by-col))))))

(defn validate-no-rehandle
  "True iff no column has a later-discharge box stacked above an earlier one."
  [plan rotation-index box-port]
  (every?
   (fn [items]
     (loop [prev nil
            xs (sort-by (fn [[_ s]] (:tier s)) items)]   ; bottom→top
       (if (empty? xs)
         true
         (let [[box-id _] (first xs)
               p (rotation-index (box-port box-id))]
           (if (and prev (> p prev))
             false
             (recur p (rest xs)))))))
   (vals (columns-of plan))))

(defn main [& _]
  (let [rotation ["SHA" "SIN" "ROT"]
        boxes [(container "A" 22.0 "ROT") (container "B" 18.0 "SIN") (container "C" 14.0 "SHA")]
        plan (build-stow-plan boxes rotation 1 1 3)]
    (println "niyaku stow plan (bay/row/tier):")
    (doseq [[bid s] (sort-by key (:assignments plan))]
      (println (format "  %s → bay %d row %d tier %d" bid (:bay s) (:row s) (:tier s))))
    (println "discharge sequence (top-first):" (discharge-sequence plan "ROT"))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
