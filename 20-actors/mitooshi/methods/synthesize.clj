#!/usr/bin/env bb
;; Working Clojure port of methods/synthesize.py.
(ns mitooshi.methods.synthesize
  "mitooshi 見通し — cross-actor chokepoint RESILIENCE composite (R1, offline).

  ADR-2606051800 / 2606012600. Fuses the SAME chokepoint keyword across three actors —
  watari 渡り (live vessel transit :transit-load), watatsuna 綿津綱 (submarine-cable load
  :cable-load), and mitooshi 見通し (forecast next-value distribution) — into ONE per-chokepoint
  composite ranked by resilience attention.

  A RESILIENCE map, NEVER a target-list. Aggregate-first, DERIVED :representative, live
  promotion G10-gated.

  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/synthesize.clj"
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(def ^:private default-trail (io/file (actor-root) "data" "persisted" "chokepoint-trail.kotoba.edn"))
(def ^:private default-forecast (io/file (actor-root) "data" "persisted" "chokepoint-forecast.kotoba.edn"))

(defn load-edn
  "Inline small EDN loader (do not depend on mitooshi.methods.analyze)."
  [path]
  (edn/read-string (slurp (io/file path))))

(defn- key-as-str
  "Python stores keywords as ':ns/name' strings; clojure.edn returns real keywords.
   Normalize to the Python string form when inspecting data imported from EDN."
  [k]
  (if (keyword? k)
    (str (when (= (namespace k) "cljs") "cljs.")
         (name k))
    (str k)))

(defn- str-keyword
  "Ensure chokepoint string begins with ':'."
  [s]
  (if (str/starts-with? (str s) ":")
    (str s)
    (str ":" s)))

(defn chokepoint-of
  "s-malacca-cable / s-malacca-transit → ':malacca'."
  [series-id]
  (let [sid (str series-id)
        core (if (str/starts-with? sid "s-")
               (subs sid 2)
               sid)
        stripped (reduce (fn [s sfx]
                           (if (str/ends-with? s sfx)
                             (subs s 0 (- (count s) (count sfx)))
                             s))
                         core
                         ["-cable" "-transit"])]
    (str-keyword stripped)))

(defn latest-by-series
  "{series-id: value at max observed-at} — current value per series."
  [trail-rows]
  (reduce (fn [m row]
            ;; the trail mixes :series/* definition rows with :obs/* observation rows;
            ;; fold ONLY the observation rows (mirrors latest_by_series in synthesize.py).
            (if-let [sid0 (:obs/series row)]
              (let [sid (key-as-str sid0)
                    t (long (:obs/observed-at row))
                    v (double (:obs/value row))]
                (if (or (not (contains? m sid)) (> t (first (get m sid))))
                  (assoc m sid [t v])
                  m))
              m))
          {}
          trail-rows))

(defn forecast-by-series
  "{series-id: [mean sd]} from forecast rows."
  [fc-rows]
  (reduce (fn [m row]
            (let [sid (get row (or (keyword "forecast/series")
                                   ":forecast/series"))]
              (if sid
                (assoc m (key-as-str sid)
                       [(double (get row (or (keyword "forecast/mean")
                                             ":forecast/mean") 0.0))
                        (double (get row (or (keyword "forecast/sd")
                                             ":forecast/sd") 0.0))])
                m)))
          {}
          fc-rows))

(defn synthesize
  "Per-chokepoint composite. Returns rows sorted by resilience attention (desc).

  attention = normalized cable load (capacity-at-risk, dominant) +
              live-pressure bump from current transit.
  Both normalized to [0,1] across chokepoints so the blend is scale-free."
  [trail-rows fc-rows]
  (let [cur (latest-by-series trail-rows)
        fc (forecast-by-series fc-rows)
        chokes (atom {})]
    (doseq [[sid [_t v]] cur]
      (let [cp (chokepoint-of sid)
            d (or (get @chokes cp)
                  {:chokepoint cp
                   :transit nil
                   :cable_load nil
                   :forecast_cable_mean nil})]
        (cond
          (str/ends-with? sid "-transit")
          (swap! chokes assoc cp
                 (assoc d :transit v
                        :forecast_transit_mean (first (get fc sid [nil nil]))))
          (str/ends-with? sid "-cable")
          (swap! chokes assoc cp
                 (assoc d :cable_load v
                        :forecast_cable_mean (first (get fc sid [nil nil])))))))
    (let [cables (keep :cable_load (vals @chokes))
          transits (keep :transit (vals @chokes))
          max-cable (if (seq cables) (apply max cables) 1.0)
          max-transit (if (seq transits) (apply max transits) 1.0)]
      (->> (vals @chokes)
           (mapv (fn [d]
                   (let [nc (if (and (:cable_load d) (pos? max-cable))
                              (/ (:cable_load d) max-cable)
                              0.0)
                         nt (if (and (:transit d) (pos? max-transit))
                              (/ (:transit d) max-transit)
                              0.0)
                         attention (/ (Math/round (* (+ (* 0.7 nc) (* 0.3 nt)) 10000.0)) 10000.0)]
                     (assoc d :attention attention))))
           (sort-by :attention >)))))

(defn- nil-or-print [x]
  (if (nil? x) "nil" (str x)))

(defn render-edn
  "Render the composite as a kotoba EDN string."
  [composite]
  (str/join
   "\n"
   (concat
    [";; chokepoint-resilience-composite.kotoba.edn — cross-actor (watari+watatsuna+mitooshi)."
     ";; ONE maritime resilience picture per chokepoint: live transit + cable load +"
     ";; forecast. attention = 0.7*norm(cable) + 0.3*norm(transit). A RESILIENCE map,"
     ";; NEVER a target-list (routed to redundancy/repair, never interdiction)."
     ";; DERIVED :representative. Live promotion G10-gated. ADR-2606012600." "" "["]
    (for [d composite]
      (str " {:choke/id " (:chokepoint d)
           " :choke/transit " (nil-or-print (:transit d))
           " :choke/cable-load-tbps " (nil-or-print (:cable_load d))
           " :choke/forecast-cable-mean " (nil-or-print (:forecast_cable_mean d))
           " :choke/attention " (:attention d)
           " :choke/sourcing :representative}"))
    ["]"])))

(defn main
  "CLI entrypoint."
  [& argv]
  (let [args (vec argv)
        trail-idx (.indexOf args "--trail")
        trail (if (>= trail-idx 0)
                (nth args (inc trail-idx))
                default-trail)
        fc-idx (.indexOf args "--forecast")
        forecast (if (>= fc-idx 0)
                   (nth args (inc fc-idx))
                   default-forecast)
        composite (synthesize (load-edn trail) (load-edn forecast))]
    (when (>= (.indexOf args "--out") 0)
      (let [outdir (io/file (nth args (inc (.indexOf args "--out"))))]
        (.mkdirs outdir)
        (spit (io/file outdir "chokepoint-resilience-composite.kotoba.edn")
              (render-edn composite))))
    (println "mitooshi cross-actor chokepoint resilience composite (redundancy, not interdiction):")
    (doseq [d composite]
      (println (format "  %-18s attention=%.3f  transit=%s  cable=%sTbps  fc-cable=%s"
                       (:chokepoint d)
                       (:attention d)
                       (nil-or-print (:transit d))
                       (nil-or-print (:cable_load d))
                       (nil-or-print (:forecast_cable_mean d)))))
    0))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
