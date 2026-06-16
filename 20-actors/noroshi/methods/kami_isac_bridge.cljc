(ns noroshi.methods.kami-isac-bridge
  "noroshi (烽) ↔ kami-autodrive ISAC sensor bridge (ADR-2606051600 §R1a).
  1:1 Clojure port of methods/kami_isac_bridge.py. Stdlib only.

  Drives the noroshi ISAC estimator from a kami-autodrive-style scenario (objects with a
  range + constant radial velocity) → per-object tracks. CIVILIAN objects only (N1/N2).
  The __main__ demo is omitted."
  (:require [clojure.string :as str]
            [noroshi.methods.isac-sim :as isac]))

(defn scenario-object [object-id range0-m velocity-mps]
  {"object_id" object-id "range0_m" range0-m "velocity_mps" velocity-mps})

(defn- track-point [frame time-s range-m velocity-mps range-bin doppler-bin]
  {"frame" frame "time_s" time-s "range_m" range-m "velocity_mps" velocity-mps
   "range_bin" range-bin "doppler_bin" doppler-bin})

(defn- py-round [x n]
  #?(:clj (-> (java.math.BigDecimal. (double x))
              (.setScale (int n) java.math.RoundingMode/HALF_EVEN) (.doubleValue))
     :default (let [f (Math/pow 10 n)] (/ (Math/round (* x f)) f))))

(defn track-object
  "Sense one object across `frames` snapshots → a kinematic track."
  [wf obj & {:keys [frames frame_dt_s] :or {frames 8 frame_dt_s 0.002}}]
  (loop [k 0 track []]
    (if (>= k frames)
      track
      (let [t (* k frame_dt_s)
            rng (- (get obj "range0_m") (* (get obj "velocity_mps") t))]
        (if (<= rng 0)
          track
          (let [est (isac/estimate-target wf (isac/target :range_m rng :velocity_mps (get obj "velocity_mps")))]
            (recur (inc k)
                   (conj track (track-point k (py-round t 4) (get est "range_m") (get est "velocity_mps")
                                            (get est "range_bin") (get est "doppler_bin"))))))))))

(defn run-scenario
  "Run the ISAC sensor over a multi-object scenario → {object_id track}."
  [objects & {:keys [wf frames frame_dt_s] :or {wf nil frames 8 frame_dt_s 0.002}}]
  (let [wf (or wf (isac/isac-waveform))]
    (into {} (map (fn [o] [(get o "object_id") (track-object wf o :frames frames :frame_dt_s frame_dt_s)]) objects))))

(defn sense-frame
  "One-shot multi-target scene sense: detect ALL objects from a single combined echo."
  [objects & {:keys [wf] :or {wf nil}}]
  (let [wf (or wf (isac/isac-waveform))
        targets (->> objects
                     (filter #(> (get % "range0_m") 0))
                     (mapv #(isac/target :range_m (get % "range0_m") :velocity_mps (get % "velocity_mps"))))]
    (isac/estimate-targets wf targets)))

;; A :representative kami-autodrive scenario.
(def DEMO-SCENARIO
  (let [wf (isac/isac-waveform)]
    [(scenario-object "lead-vehicle" (* 4 (isac/range-resolution-m wf)) (* 2 (isac/velocity-resolution-mps wf)))
     (scenario-object "cross-object" (* 10 (isac/range-resolution-m wf)) (* 1 (isac/velocity-resolution-mps wf)))]))

(defn- fmt [fmt-str x] (#?(:clj format :default (fn [_ v] (str v))) fmt-str (double x)))

(defn report
  ([] (report DEMO-SCENARIO))
  ([objects]
   (let [wf (isac/isac-waveform)
         tracks (run-scenario (or objects DEMO-SCENARIO) :wf wf)
         lines (atom ["# noroshi 烽 × kami-autodrive — ISAC sensor in the GNC loop"
                      ""
                      (str "waveform: " (fmt "%.0f" (/ (isac/bandwidth-hz wf) 1e6)) " MHz, ΔR=" (fmt "%.2f" (isac/range-resolution-m wf)) " m, "
                           "Δv=" (fmt "%.1f" (isac/velocity-resolution-mps wf)) " m/s. Civilian objects only (collision-avoidance; N1/N2).")
                      ""])]
     (doseq [[oid track] tracks]
       (swap! lines into [(str "## track: " oid "  (" (count track) " frames)")
                          "| frame | t (s) | range (m) | velocity (m/s) | bins (k,l) |"
                          "|---|---|---|---|---|"])
       (doseq [p track]
         (swap! lines conj (str "| " (get p "frame") " | " (get p "time_s") " | " (fmt "%.2f" (get p "range_m")) " | "
                                (fmt "%.1f" (get p "velocity_mps")) " | (" (get p "range_bin") "," (get p "doppler_bin") ") |")))
       (swap! lines conj ""))
     (swap! lines conj
            (str "> The ISAC estimate feeds kami-autodrive perception (the `IsacSensor` plant the WIT contract "
                 "`wit/kami-isac.wit` defines). HONEST: the kami-engine submodule is unpopulated here, so this is "
                 "the data bridge + interface contract, not a compiled crate; live emission is G8-gated."))
     (str/join "\n" @lines))))
