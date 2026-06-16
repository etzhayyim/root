(ns noroshi.methods.link-budget
  "noroshi (烽) optical link-budget core — the chip face (ADR-2606051600). Stdlib only.
  1:1 Clojure port of 20-actors/noroshi/methods/link_budget.py.

  Computes the end-to-end power budget of a silicon-photonic / co-packaged-optics (CPO)
  link plus an energy-per-bit figure of merit. Pure; deterministic. Sign convention:
  gains/sources +dB(m), losses positive numbers SUBTRACTED; optical powers in dBm.

  Python dataclasses → Clojure string-keyed maps. `round(x, n)` is mirrored with
  HALF_EVEN (Python's banker's rounding). The __main__ demo is omitted (it only printed
  `report()`)."
  (:require [clojure.string :as str]))

;; ── Python round(x, n): HALF_EVEN ──────────────────────────────────────────────
(defn- py-round
  "Mirror Python's round(x, ndigits) — round-half-to-even on a decimal scale."
  [x n]
  #?(:clj (-> (java.math.BigDecimal. (double x))
              (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
              (.doubleValue))
     :default (let [f (Math/pow 10 n)] (/ (Math/round (* x f)) f))))

;; ── LinkDesign defaults (Python dataclass) ─────────────────────────────────────
(def link-design-defaults
  {"name"                   "cpo-2km-100g"
   "laser_power_dbm"        10.0
   "modulator_il_db"        4.0
   "tx_waveguide_cm"        1.5
   "tx_grating_coupler_db"  1.5
   "fibre_m"                2000.0
   "fibre_loss_db_per_km"   0.35
   "connector_db"           0.5
   "rx_grating_coupler_db"  1.5
   "rx_waveguide_cm"        1.0
   "waveguide_loss_db_per_cm" 1.5
   "rx_responsivity_a_per_w" 0.9
   "rx_sensitivity_dbm"     -12.0
   "line_rate_gbps"         106.25
   "tx_energy_pj_per_bit"   1.2
   "rx_energy_pj_per_bit"   1.0
   "laser_wall_plug_eff"    0.10})

(defn link-design
  "Construct a LinkDesign map from keyword/string overrides over the defaults."
  [& {:as overrides}]
  (merge link-design-defaults
         (into {} (map (fn [[k v]] [(name k) v]) overrides))))

(defn- waveguide-loss [d]
  (* (+ (get d "tx_waveguide_cm") (get d "rx_waveguide_cm"))
     (get d "waveguide_loss_db_per_cm")))

(defn- fibre-loss [d]
  (* (/ (get d "fibre_m") 1000.0) (get d "fibre_loss_db_per_km")))

(defn compute
  "Return the closed-form power budget + energy-per-bit for one link design (a map)."
  [design]
  (when (<= (get design "line_rate_gbps") 0)
    (throw (ex-info "line_rate_gbps must be positive" {})))
  (let [losses {"modulator_il"       (get design "modulator_il_db")
                "tx_grating_coupler" (get design "tx_grating_coupler_db")
                "rx_grating_coupler" (get design "rx_grating_coupler_db")
                "waveguide"          (waveguide-loss design)
                "fibre"              (fibre-loss design)
                "connector"          (get design "connector_db")}
        total-loss   (reduce + (vals losses))
        received-dbm (- (get design "laser_power_dbm") total-loss)
        margin       (- received-dbm (get design "rx_sensitivity_dbm"))
        received-mw  (Math/pow 10.0 (/ received-dbm 10.0))
        received-current-ua (* (get design "rx_responsivity_a_per_w") received-mw 1e3)
        laser-optical-w     (/ (Math/pow 10.0 (/ (get design "laser_power_dbm") 10.0)) 1e3)
        laser-electrical-w  (/ laser-optical-w (max (get design "laser_wall_plug_eff") 1e-9))
        laser-pj-per-bit    (* (/ laser-electrical-w (* (get design "line_rate_gbps") 1e9)) 1e12)
        energy-pj-per-bit   (+ (get design "tx_energy_pj_per_bit")
                               (get design "rx_energy_pj_per_bit")
                               laser-pj-per-bit)]
    {"name"                (get design "name")
     "received_dbm"        (py-round received-dbm 3)
     "margin_db"           (py-round margin 3)
     "closes"              (>= margin 0.0)
     "total_loss_db"       (py-round total-loss 3)
     "energy_pj_per_bit"   (py-round energy-pj-per-bit 3)
     "received_current_ua" (py-round received-current-ua 3)
     "breakdown"           (into {} (map (fn [[k v]] [k (py-round v 3)]) losses))}))

;; ── receiver sensitivity from a target BER ──────────────────────────────────────
(def ^:private K-BOLTZMANN 1.380649e-23)

(defn- poly-horner
  "Evaluate Σ coeffs[i]·t^i via Horner from the highest coefficient down."
  [t coeffs]
  (reduce (fn [acc c] (+ c (* t acc))) 0.0 (reverse coeffs)))

(defn- erfc
  "Complementary error function (no stdlib erfc on JVM). Numerical-Recipes erfcc
  rational approximation accurate to ~1.2e-7, sufficient for the Q-factor bisection
  (test tolerance ±0.05)."
  [x]
  (let [z   (Math/abs (double x))
        t   (/ 1.0 (+ 1.0 (* 0.5 z)))
        ;; coefficients in ascending power of t
        poly (poly-horner t [-1.26551223 1.00002368 0.37409196 0.09678418
                             -0.18628806 0.27886807 -1.13520398 1.48851587
                             -0.82215223 0.17087277])
        tau (* t (Math/exp (+ (* (- z) z) poly)))]
    (if (>= x 0.0) tau (- 2.0 tau))))

(defn q-factor-for-ber
  "Solve BER = ½·erfc(Q/√2) for the Q-factor (NRZ-OOK direct detection), via bisection."
  [ber]
  (when-not (and (< 0.0 ber) (< ber 0.5))
    (throw (ex-info "BER must lie in (0, 0.5)" {})))
  (loop [lo 0.0 hi 12.0 i 0]
    (if (>= i 100)
      (* 0.5 (+ lo hi))
      (let [mid (* 0.5 (+ lo hi))]
        (if (> (* 0.5 (erfc (/ mid (Math/sqrt 2.0)))) ber)
          (recur mid hi (inc i))
          (recur lo mid (inc i)))))))

(defn receiver-sensitivity-dbm
  "Thermal-noise-limited receiver sensitivity (min received optical power, dBm)."
  ([ber line-rate-gbps] (receiver-sensitivity-dbm ber line-rate-gbps 0.9 300.0 50.0))
  ([ber line-rate-gbps responsivity-a-per-w] (receiver-sensitivity-dbm ber line-rate-gbps responsivity-a-per-w 300.0 50.0))
  ([ber line-rate-gbps responsivity-a-per-w temperature-k load-ohm]
   (when (<= line-rate-gbps 0)
     (throw (ex-info "line_rate_gbps must be positive" {})))
   (let [q (q-factor-for-ber ber)
         bandwidth-hz (* 0.7 line-rate-gbps 1e9)
         sigma-thermal-a (Math/sqrt (/ (* 4.0 K-BOLTZMANN temperature-k bandwidth-hz) load-ohm))
         p-min-w (/ (* q sigma-thermal-a) responsivity-a-per-w)]
     (* 10.0 (Math/log10 (* p-min-w 1e3))))))

(defn with-ber-sensitivity
  "Return a copy of `design` whose rx_sensitivity_dbm is derived from a target BER."
  [design ber]
  (let [sens (receiver-sensitivity-dbm ber (get design "line_rate_gbps") (get design "rx_responsivity_a_per_w"))]
    (assoc design "rx_sensitivity_dbm" (py-round sens 3))))

;; ── APD receiver ────────────────────────────────────────────────────────────────
(defn excess-noise-factor
  "McIntyre excess-noise factor F(M) = k·M + (1−k)·(2 − 1/M)."
  ([gain-m] (excess-noise-factor gain-m 0.3))
  ([gain-m k-eff]
   (when (< gain-m 1)
     (throw (ex-info "APD gain M must be ≥ 1" {})))
   (when-not (<= 0.0 k-eff 1.0)
     (throw (ex-info "k_eff (ionization ratio) must lie in [0,1]" {})))
   (+ (* k-eff gain-m) (* (- 1.0 k-eff) (- 2.0 (/ 1.0 gain-m))))))

(defn apd-sensitivity-dbm
  "APD receiver sensitivity (dBm) — PIN thermal-limited value improved by M/√F(M)."
  ([ber line-rate-gbps] (apd-sensitivity-dbm ber line-rate-gbps 10.0 0.3 0.9 300.0 50.0))
  ([ber line-rate-gbps gain-m k-eff] (apd-sensitivity-dbm ber line-rate-gbps gain-m k-eff 0.9 300.0 50.0))
  ([ber line-rate-gbps gain-m k-eff responsivity-a-per-w temperature-k load-ohm]
   (let [pin (receiver-sensitivity-dbm ber line-rate-gbps responsivity-a-per-w temperature-k load-ohm)
         improvement-db (* 10.0 (Math/log10 (/ gain-m (Math/sqrt (excess-noise-factor gain-m k-eff)))))]
     (- pin improvement-db))))

;; ── reference designs ───────────────────────────────────────────────────────────
(def CPO-REFERENCE
  (link-design :name "cpo-2km-100g"
               :laser_power_dbm 10.0 :modulator_il_db 4.0
               :tx_grating_coupler_db 1.5 :rx_grating_coupler_db 1.5
               :tx_waveguide_cm 1.5 :rx_waveguide_cm 1.0
               :fibre_m 2000.0 :tx_energy_pj_per_bit 1.2 :rx_energy_pj_per_bit 1.0))

(def PLUGGABLE-REFERENCE
  (link-design :name "pluggable-2km-100g"
               :laser_power_dbm 10.0 :modulator_il_db 5.0
               :tx_grating_coupler_db 2.0 :rx_grating_coupler_db 2.0
               :tx_waveguide_cm 2.0 :rx_waveguide_cm 2.0
               :fibre_m 2000.0
               :tx_energy_pj_per_bit 6.0 :rx_energy_pj_per_bit 5.5))

;; ── render helpers (mirror Python f-strings) ────────────────────────────────────
(defn- num->str
  "Python str(float) parity for the values that reach report() — drop a trailing .0
  ONLY where Python's round produced an integral float that still prints as e.g. 5.0
  is kept; but our breakdown / energy values print like Python's repr of a float."
  [v]
  (cond
    (and (number? v) (not (integer? v)) (== v (Math/floor v)) (not (Double/isInfinite (double v))))
    (str (long v) ".0")
    :else (str v)))

(defn- breakdown->str [m]
  ;; Python dict repr: {'modulator_il': 4.0, ...} preserving insertion order.
  (str "{" (str/join ", "
                     (map (fn [k] (str "'" k "': " (num->str (get m k))))
                          ["modulator_il" "tx_grating_coupler" "rx_grating_coupler"
                           "waveguide" "fibre" "connector"]))
       "}"))

(defn report
  "Render a human-readable link-budget comparison (the chip-face out/ artifact)."
  ([] (report [CPO-REFERENCE PLUGGABLE-REFERENCE]))
  ([designs]
   (let [designs (if (seq designs) designs [CPO-REFERENCE PLUGGABLE-REFERENCE])
         budgets (mapv compute designs)
         lines (atom ["# noroshi 烽 — optical link budget (光電融合 / CPO)" ""])]
     (doseq [b budgets]
       (let [verdict (if (get b "closes") "CLOSES" "FAILS (insufficient margin)")]
         (swap! lines into
                [(str "## " (get b "name"))
                 (str "- received power : " (num->str (get b "received_dbm")) " dBm  (total loss " (num->str (get b "total_loss_db")) " dB)")
                 (str "- link margin    : " (num->str (get b "margin_db")) " dB  → " verdict)
                 (str "- photocurrent   : " (num->str (get b "received_current_ua")) " µA")
                 (str "- energy/bit     : " (num->str (get b "energy_pj_per_bit")) " pJ/bit")
                 (str "- loss breakdown : " (breakdown->str (get b "breakdown")))
                 ""])))
     (when (and (>= (count budgets) 2) (> (get (budgets 1) "energy_pj_per_bit") 0))
       (let [ratio (/ (get (budgets 1) "energy_pj_per_bit") (get (budgets 0) "energy_pj_per_bit"))]
         (swap! lines conj
                (str "**CPO energy advantage**: " (get (budgets 0) "name") " costs "
                     (num->str (get (budgets 0) "energy_pj_per_bit")) " pJ/bit vs " (get (budgets 1) "name") " "
                     (num->str (get (budgets 1) "energy_pj_per_bit")) " pJ/bit — **"
                     (#?(:clj format :default identity) "%.2f" (double ratio)) "× lower energy/bit**."))))
     (swap! lines conj "")
     (swap! lines conj (str "> R0 design arithmetic only. No foundry tapeout, no measured device, no live "
                            "laser (G7 outward-gated). `:representative` device parameters."))
     (str/join "\n" @lines))))
