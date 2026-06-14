#!/usr/bin/env bb
;; Working Clojure port of methods/voyage_energy.py (replaces the failed unit_refactor stub).
(ns funadaiku.methods.voyage-energy
  "funadaiku 船大工 — Nagi 凪 class voyage energy-budget simulation.

  ADR-2606013400. Stdlib-only reduced-order analytic model of the zero-emission
  powertrain over a representative coastal voyage. Computes how much of the voyage
  propulsion + hotel energy is met by each source — wind-assist, solar, hydrogen
  fuel-cell (with battery buffering peaks) — and the resulting green-H2 demand.

  HONEST: a transparent first-order model (Admiralty propulsion-power law + flat-rate
  solar capacity factor + average wind-assist saving fraction), NOT CFD or sea-keeping.
  It makes the wind/solar/hydrogen split EMPIRICAL rather than asserted. Numbers are
  :representative. The 6-DOF dynamics live in kami-autodrive ShipHydro (ADR-2606010600).

  Run:  bb --classpath 20-actors 20-actors/funadaiku/methods/voyage_energy.clj
        -> writes out/voyage-energy-report.md + out/voyage-energy.kotoba.edn"
  (:require [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

;; ── reference vessel (mirrors data/vessel.edn, Nagi 凪 class) ──────────────────
(def default-vessel
  {:name "Nagi 凪 (coastal cargo)"
   :dwt 3000
   :displacement-t 4500.0        ; full-load displacement ~ 1.5x DWT (small cargo)
   :admiralty-coeff 450.0        ; Δ^(2/3)·V^3 / P_shaft ; typical small cargo
   :service-speed-kn 10.0
   :hotel-load-kw 120.0          ; auxiliary / hotel / control load
   :solar-kwp 160.0
   :fuelcell-kw 2400.0
   :battery-kwh 2000.0
   :rotor-sails 2})

(def default-voyage
  {:name "representative coastal short-sea leg"
   :distance-nm 200.0
   :solar-capacity-factor 0.13       ; marine daytime-averaged annual CF
   :wind-assist-saving-frac 0.18     ; avg propulsion-power saved by 2 rotor sails
   :propulsive-efficiency 0.62       ; hull+pod quasi-propulsive coefficient
   :fuelcell-lhv-eff 0.52})          ; PEM FC electrical efficiency (LHV)

(def H2-LHV-KWH-PER-KG 33.33)  ; lower-heating-value energy density of hydrogen

(defn shaft-power-kw
  "Admiralty-coefficient propulsion power at service speed (calm water)."
  [v]
  (let [disp23 (Math/pow (:displacement-t v) (/ 2.0 3.0))]
    (/ (* disp23 (Math/pow (:service-speed-kn v) 3.0)) (:admiralty-coeff v))))

(defn simulate [v voy]
  (let [hours            (/ (:distance-nm voy) (:service-speed-kn v))
        p-shaft          (shaft-power-kw v)
        p-prop-bus       (/ p-shaft (:propulsive-efficiency voy))
        prop-energy-kwh  (* p-prop-bus hours)
        hotel-energy-kwh (* (:hotel-load-kw v) hours)
        total-demand-kwh (+ prop-energy-kwh hotel-energy-kwh)
        ;; wind-assist: reduces propulsion demand directly
        wind-kwh         (* prop-energy-kwh (:wind-assist-saving-frac voy))
        ;; solar: average power = peak * capacity factor, capped to hotel + a little propulsion
        solar-avg-kw     (* (:solar-kwp v) (:solar-capacity-factor voy))
        solar-kwh        (min (* solar-avg-kw hours)
                              (+ hotel-energy-kwh (* prop-energy-kwh 0.10)))
        ;; hydrogen fuel cell: supplies the residual; battery only shifts peaks
        residual-kwh     (max 0.0 (- total-demand-kwh wind-kwh solar-kwh))
        h2-kg            (/ residual-kwh (* H2-LHV-KWH-PER-KG (:fuelcell-lhv-eff voy)))
        shares           {:wind-assist       (/ wind-kwh total-demand-kwh)
                          :solar             (/ solar-kwh total-demand-kwh)
                          :hydrogen-fuelcell (/ residual-kwh total-demand-kwh)}
        ;; battery sanity: can it cover a ~30 min harbour-manoeuvre window?
        harbour-kw       (+ (* p-prop-bus 0.6) (:hotel-load-kw v))
        battery-minutes  (* (/ (:battery-kwh v) harbour-kw) 60.0)]
    {:hours hours
     :p-shaft-kw p-shaft
     :p-prop-bus-kw p-prop-bus
     :prop-energy-kwh prop-energy-kwh
     :hotel-energy-kwh hotel-energy-kwh
     :total-demand-kwh total-demand-kwh
     :wind-kwh wind-kwh
     :solar-kwh solar-kwh
     :residual-kwh residual-kwh
     :h2-kg h2-kg
     :shares shares
     :battery-harbour-minutes battery-minutes
     :fossil-engine false}))

(defn- f [fmt x] (format fmt (double x)))
(defn- pct [x] (format "%.1f%%" (* (double x) 100.0)))

(defn report [v voy r]
  (let [s (:shares r)]
    (str/join
     "\n"
     ["# funadaiku 船大工 — Nagi 凪 voyage energy budget"
      ""
      "> ADR-2606013400 · reduced-order analytic model (`methods/voyage_energy.clj`) · :representative"
      "> **No fossil engine** (G13/N5). Hydrogen must be green (G14, well-to-wake)."
      ""
      "## Inputs"
      ""
      (format "| Vessel (%s) | | Voyage (%s) | |" (:name v) (:name voy))
      "|---|---|---|---|"
      (format "| DWT | %d | Distance | %s nm |" (:dwt v) (f "%.0f" (:distance-nm voy)))
      (format "| Displacement | %s t | Service speed | %s kn |"
              (f "%.0f" (:displacement-t v)) (f "%.0f" (:service-speed-kn v)))
      (format "| Solar | %s kWp | Voyage time | %s h |"
              (f "%.0f" (:solar-kwp v)) (f "%.1f" (:hours r)))
      (format "| Fuel cell | %s kW | Solar capacity factor | %s |"
              (f "%.0f" (:fuelcell-kw v)) (pct (:solar-capacity-factor voy)))
      (format "| Battery | %s kWh | Wind-assist saving | %s |"
              (f "%.0f" (:battery-kwh v)) (pct (:wind-assist-saving-frac voy)))
      (format "| Rotor sails | %d | FC efficiency (LHV) | %s |"
              (:rotor-sails v) (pct (:fuelcell-lhv-eff voy)))
      ""
      "## Result"
      ""
      (format "- Propulsion shaft power @ %s kn: **%s kW** (Admiralty law, calm water)"
              (f "%.0f" (:service-speed-kn v)) (f "%.0f" (:p-shaft-kw r)))
      (format "- Bus propulsion power (÷ QPC %s): **%s kW**"
              (:propulsive-efficiency voy) (f "%.0f" (:p-prop-bus-kw r)))
      (format "- Voyage energy demand (propulsion + hotel): **%s kWh**" (f "%.0f" (:total-demand-kwh r)))
      ""
      "### Energy met by source"
      ""
      "| Source | Energy (kWh) | Share | Role |"
      "|---|---:|---:|---|"
      (format "| Wind-assist (2× rotor sail) | %s | **%s** | primary fuel-saver |"
              (f "%.0f" (:wind-kwh r)) (pct (:wind-assist s)))
      (format "| Solar deck | %s | **%s** | hotel + top-up |"
              (f "%.0f" (:solar-kwh r)) (pct (:solar s)))
      (format "| Hydrogen fuel cell (residual) | %s | **%s** | electrical prime mover |"
              (f "%.0f" (:residual-kwh r)) (pct (:hydrogen-fuelcell s)))
      "| **Fossil engine** | 0 | **0.0%** | none (G13) |"
      ""
      (format "- **Green hydrogen demand for this leg: %s kg** (LHV %s kWh/kg ÷ FC %s)"
              (f "%.0f" (:h2-kg r)) H2-LHV-KWH-PER-KG (pct (:fuelcell-lhv-eff voy)))
      (format "- Battery covers a harbour manoeuvre (~60%% prop + hotel) for **%s min** → zero-emission at berth/port."
              (f "%.0f" (:battery-harbour-minutes r)))
      ""
      "## Honest reading"
      ""
      (format (str "Wind + solar together meet **%s** of this representative coastal leg; hydrogen carries "
                   "the remaining **%s** as the prime mover — exactly the survey conclusion that **no single "
                   "source is a complete prime mover** at cargo scale. Tank-to-wake CO₂ is **zero**; the "
                   "well-to-wake figure depends entirely on the **green-H₂ chain-of-custody** (G14). This is "
                   "a first-order model, not CFD.")
              (pct (+ (:wind-assist s) (:solar s))) (pct (:hydrogen-fuelcell s)))
      ""])))

(defn to-edn [v voy r]
  (let [s (:shares r)]
    (str/join
     "\n"
     [";; funadaiku Nagi 凪 — voyage energy-budget result (kotoba EAVT)"
      ";; ADR-2606013400 · generated by methods/voyage_energy.clj · :representative"
      "[{:voyage/id \"funadaiku.nagi.voyage-rep-200nm\" :voyage/vessel \"funadaiku.nagi-0001\""
      (format "  :voyage/distance-nm %s :voyage/hours %s"
              (f "%.0f" (:distance-nm voy)) (f "%.2f" (:hours r)))
      (format "  :voyage/total-demand-kwh %s" (f "%.0f" (:total-demand-kwh r)))
      (format "  :voyage/share-wind %s :voyage/share-solar %s"
              (f "%.4f" (:wind-assist s)) (f "%.4f" (:solar s)))
      (format "  :voyage/share-hydrogen %s :voyage/fossil-engine false"
              (f "%.4f" (:hydrogen-fuelcell s)))
      (format "  :voyage/green-h2-kg %s :voyage/battery-harbour-min %s"
              (f "%.0f" (:h2-kg r)) (f "%.0f" (:battery-harbour-minutes r)))
      "  :voyage/sourcing :representative}]"
      ""])))

(defn main [& _]
  (let [v default-vessel voy default-voyage
        r (simulate v voy)
        out (io/file (actor-root) "out")]
    (.mkdirs out)
    (spit (io/file out "voyage-energy-report.md") (report v voy r))
    (spit (io/file out "voyage-energy.kotoba.edn") (to-edn v voy r))
    (let [s (:shares r)]
      (println (format "Nagi 凪 voyage %s nm @ %s kn  (%s h, %s kWh)"
                       (f "%.0f" (:distance-nm voy)) (f "%.0f" (:service-speed-kn v))
                       (f "%.1f" (:hours r)) (f "%.0f" (:total-demand-kwh r))))
      (println (format "  wind-assist %5.1f%% | solar %5.1f%% | hydrogen %5.1f%% | fossil 0.0%%"
                       (* (double (:wind-assist s)) 100) (* (double (:solar s)) 100)
                       (* (double (:hydrogen-fuelcell s)) 100)))
      (println (format "  green-H2 demand: %s kg   battery harbour: %s min"
                       (f "%.0f" (:h2-kg r)) (f "%.0f" (:battery-harbour-minutes r))))
      (println "  wrote out/voyage-energy-report.md + out/voyage-energy.kotoba.edn"))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
