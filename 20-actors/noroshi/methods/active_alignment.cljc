(ns noroshi.methods.active-alignment
  "noroshi (烽) active-alignment + laser-safety core — packaging-robotics face (ADR-2606051600).
  1:1 Clojure port of methods/active_alignment.py.

  enable-laser refuses to energise unless civilian-use (N1) and, above Class 1, an
  enclosure interlock + safety attestation are present. align runs a Hooke-Jeeves
  pattern search over (dx,dy) maximising coupling efficiency. Pure + deterministic.
  Frozen dataclasses → string-keyed maps. The __main__ demo is omitted."
  (:require [clojure.string :as str]))

(def PERMITTED-USES ["alignment" "comms" "soldering" "trimming" "inspection"])
(def FORBIDDEN-USES ["weapon" "directed-energy" "dazzle" "fire-control"])
(def HAZARDOUS-CLASSES ["2" "3R" "3B" "4"])

(defn laser-safety-error
  "N1 / IEC 60825 — the laser may not be energised for this use or without an interlock."
  [msg] (ex-info msg {:type :laser-safety-error}))

;; ── LaserSpec / CouplerModel as maps ────────────────────────────────────────────
(defn laser-spec
  [& {:keys [laser_class use enclosure_interlock safety_attestation_ref]
      :or {laser_class "1" use "alignment" enclosure_interlock false safety_attestation_ref ""}}]
  {"laser_class" laser_class "use" use
   "enclosure_interlock" enclosure_interlock "safety_attestation_ref" safety_attestation_ref})

(defn coupler-model
  [& {:keys [peak_efficiency mode_radius_um opt_x_um opt_y_um]
      :or {peak_efficiency 0.80 mode_radius_um 5.0 opt_x_um 2.3 opt_y_um -1.7}}]
  {"peak_efficiency" peak_efficiency "mode_radius_um" mode_radius_um
   "opt_x_um" opt_x_um "opt_y_um" opt_y_um})

(defn efficiency
  "Gaussian coupling vs lateral misalignment from the (unknown) optimal fibre offset."
  [model dx-um dy-um]
  (let [r2 (+ (Math/pow (- dx-um (get model "opt_x_um")) 2)
              (Math/pow (- dy-um (get model "opt_y_um")) 2))]
    (* (get model "peak_efficiency") (Math/exp (/ (- r2) (Math/pow (get model "mode_radius_um") 2))))))

(defn loss-db [eff]
  (* -10.0 (Math/log10 (max eff 1e-12))))

(defn enable-laser
  "Raise unless the laser may be energised. No return value (gate only)."
  [spec]
  (let [use (get spec "use")]
    (when (or (some #{use} FORBIDDEN-USES) (not (some #{use} PERMITTED-USES)))
      (throw (laser-safety-error
              (str "N1: use '" use "' is not a permitted civilian photonic-fab use; "
                   "weaponisation / directed-energy can never be energised (Mission Charter §1.12)"))))
    (when (some #{(get spec "laser_class")} HAZARDOUS-CLASSES)
      (when-not (get spec "enclosure_interlock")
        (throw (laser-safety-error
                (str "IEC 60825: a Class-" (get spec "laser_class") " laser requires a physical enclosure "
                     "interlock before energising (soft-safety gate; not a certified safety controller)"))))
      (when (str/blank? (get spec "safety_attestation_ref"))
        (throw (laser-safety-error
                (str "IEC 60825: a Class-" (get spec "laser_class") " laser requires an operator safety "
                     "attestation reference before energising")))))))

;; ── round helper (Python round HALF_EVEN) ───────────────────────────────────────
(defn- py-round [x n]
  #?(:clj (-> (java.math.BigDecimal. (double x))
              (.setScale (int n) java.math.RoundingMode/HALF_EVEN) (.doubleValue))
     :default (let [f (Math/pow 10 n)] (/ (Math/round (* x f)) f))))

(defn align
  "Hooke-Jeeves pattern search for peak coupling. Raises (via enable-laser) before any probe."
  [model laser & {:keys [start_x_um start_y_um step_um tol_um max_probes]
                  :or {start_x_um 0.0 start_y_um 0.0 step_um 4.0 tol_um 0.05 max_probes 2000}}]
  (enable-laser laser)
  (loop [x start_x_um y start_y_um best (efficiency model start_x_um start_y_um)
         step step_um probes 1]
    (if (and (> step tol_um) (< probes max_probes))
      ;; probe the four axis-aligned neighbours; move to the FIRST improving one (Python breaks).
      (let [nbrs [[step 0.0] [(- step) 0.0] [0.0 step] [0.0 (- step)]]
            ;; scan neighbours, incrementing probes for each examined, stopping at first improvement
            scan (reduce
                  (fn [acc [dx dy]]
                    (if (:improved acc)
                      acc
                      (let [p2 (inc (:probes acc))
                            eff (efficiency model (+ x dx) (+ y dy))]
                        (if (> eff best)
                          {:improved true :probes p2 :x (+ x dx) :y (+ y dy) :best eff}
                          (assoc acc :probes p2)))))
                  {:improved false :probes probes :x x :y y :best best}
                  nbrs)]
        (if (:improved scan)
          (recur (:x scan) (:y scan) (:best scan) step (:probes scan))
          (recur x y best (/ step 2.0) (:probes scan))))
      {"x_um" (py-round x 4) "y_um" (py-round y 4)
       "efficiency" (py-round best 6) "loss_db" (py-round (loss-db best) 4)
       "probes" probes "converged" (<= step tol_um)})))

(defn coarse-scan
  "Coarse acquisition raster → [best_x best_y best_eff probes]. Raises before any probe."
  [model laser & {:keys [span_um step_um] :or {span_um 70.0 step_um nil}}]
  (enable-laser laser)
  (let [step (if (nil? step_um) (get model "mode_radius_um") step_um)]
    (when (or (<= step 0) (<= span_um 0))
      (throw (ex-info "span_um and step_um must be positive" {})))
    (let [n (int (/ span_um step))]
      (loop [i (- n) best-x 0.0 best-y 0.0 best-eff (efficiency model 0.0 0.0) probes 1]
        (if (> i n)
          [best-x best-y best-eff probes]
          (let [[bx by be pr] (loop [j (- n) bx best-x by best-y be best-eff pr probes]
                                (if (> j n)
                                  [bx by be pr]
                                  (let [x (* i step) y (* j step) pr2 (inc pr)
                                        eff (efficiency model x y)]
                                    (if (> eff be)
                                      (recur (inc j) x y eff pr2)
                                      (recur (inc j) bx by be pr2)))))]
            (recur (inc i) bx by be pr)))))))

(defn spiral-search
  "Expanding-square spiral that STOPS on first signal → [best_x best_y best_eff probes]."
  [model laser & {:keys [span_um step_um detect_floor] :or {span_um 70.0 step_um nil detect_floor 1e-6}}]
  (enable-laser laser)
  (let [step (if (nil? step_um) (get model "mode_radius_um") step_um)]
    (when (or (<= step 0) (<= span_um 0))
      (throw (ex-info "span_um and step_um must be positive" {})))
    (let [max-ring (int (/ span_um step))
          best0 [0.0 0.0 (efficiency model 0.0 0.0)]]
      (if (> (best0 2) detect_floor)
        [(best0 0) (best0 1) (best0 2) 1]
        (let [dirs [[1 0] [0 1] [-1 0] [0 -1]]]
          ;; iterate runs 1,1,2,2,3,3,... cycling R,U,L,D
          (loop [ix 0 iy 0 best best0 probes 1 di 0 run 1]
            (if (> run (+ (* 2 max-ring) 1))
              [(best 0) (best 1) (best 2) probes]
              (let [;; two passes per run
                    result
                    (loop [pass 0 ix ix iy iy best best probes probes di di
                           returned nil]
                      (if (or returned (>= pass 2))
                        {:ret returned :ix ix :iy iy :best best :probes probes :di di}
                        (let [[dx dy] (nth dirs (mod di 4))
                              step-res
                              (loop [s 0 ix ix iy iy best best probes probes]
                                (if (>= s run)
                                  {:done false :ix ix :iy iy :best best :probes probes}
                                  (let [ix2 (+ ix dx) iy2 (+ iy dy)]
                                    (if (> (max (Math/abs ix2) (Math/abs iy2)) max-ring)
                                      {:done true :early :bound :ix ix2 :iy iy2 :best best :probes probes}
                                      (let [x (* ix2 step) y (* iy2 step) probes2 (inc probes)
                                            eff (efficiency model x y)
                                            best2 (if (> eff (best 2)) [x y eff] best)]
                                        (if (> eff detect_floor)
                                          {:done true :early :signal :best2 best2 :ix ix2 :iy iy2 :best best2 :probes probes2}
                                          (recur (inc s) ix2 iy2 best2 probes2)))))))]
                          (cond
                            (= (:early step-res) :bound)
                            {:ret :bound :ix (:ix step-res) :iy (:iy step-res) :best (:best step-res) :probes (:probes step-res) :di di}
                            (= (:early step-res) :signal)
                            {:ret :signal :ix (:ix step-res) :iy (:iy step-res) :best (:best step-res) :probes (:probes step-res) :di di}
                            :else
                            (recur (inc pass) (:ix step-res) (:iy step-res) (:best step-res) (:probes step-res) (inc di) nil)))))]
                (if (:ret result)
                  (let [b (:best result)]
                    (if (= (:ret result) :bound)
                      [(b 0) (b 1) (b 2) (:probes result)]
                      [(b 0) (b 1) (b 2) (:probes result)]))
                  (recur (:ix result) (:iy result) (:best result) (:probes result) (:di result) (inc run)))))))))))

(defn align-two-stage
  "Coarse acquisition → Hooke-Jeeves fine refinement."
  [model laser & {:keys [span_um coarse_step_um fine_tol_um acquire]
                  :or {span_um 70.0 coarse_step_um nil fine_tol_um 0.05 acquire "raster"}}]
  (let [step (if (nil? coarse_step_um) (get model "mode_radius_um") coarse_step_um)
        [cx cy _ cprobes]
        (cond
          (= acquire "spiral") (spiral-search model laser :span_um span_um :step_um step)
          (= acquire "raster") (coarse-scan model laser :span_um span_um :step_um step)
          :else (throw (ex-info "acquire must be 'raster' or 'spiral'" {})))
        fine (align model laser :start_x_um cx :start_y_um cy :step_um step :tol_um fine_tol_um)]
    {"x_um" (get fine "x_um") "y_um" (get fine "y_um")
     "efficiency" (get fine "efficiency") "loss_db" (get fine "loss_db")
     "probes" (+ cprobes (get fine "probes")) "converged" (get fine "converged")}))

(defn report
  "Render the packaging-robotics face out/ artifact."
  ([] (report (coupler-model)))
  ([model]
   (let [model (or model (coupler-model))
         safe (laser-spec :laser_class "1" :use "alignment")
         res (align model safe)]
     (str/join "\n"
               ["# noroshi 烽 — photonic active alignment (fibre ↔ grating coupler)"
                ""
                (str "- true peak offset : (" (get model "opt_x_um") ", " (get model "opt_y_um") ") µm  (unknown to the robot)")
                (str "- found offset     : (" (get res "x_um") ", " (get res "y_um") ") µm  in " (get res "probes") " probes "
                     "(" (if (get res "converged") "converged" "budget-exhausted") ")")
                (str "- coupling         : η = " (get res "efficiency") "  → insertion loss " (get res "loss_db") " dB")
                ""
                "## laser-safety interlock (IEC 60825 + N1 civilian-use)"
                "- Class 1 alignment laser              → energise OK"
                "- Class 4 without enclosure interlock  → REFUSED"
                "- use = 'directed-energy' / 'weapon'   → REFUSED (structurally unrepresentable, N1)"
                ""
                (str "> R0 simulation only — no robot, no live laser, no live actuation (G7). A live fleet displaces "
                     "human alignment technicians ⇒ G2-coupled to the Displacement Dividend (ADR-2606032130).")]))))
