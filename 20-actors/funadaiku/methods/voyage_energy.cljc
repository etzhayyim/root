(ns funadaiku.methods.voyage-energy
  "funadaiku 船大工 — Nagi 凪 class voyage energy-budget simulation.
  1:1 Clojure port of `methods/voyage_energy.py` (ADR-2606013400).

  Stdlib-only reduced-order analytic model of the zero-emission powertrain over a
  representative coastal voyage. Computes how much of the voyage propulsion + hotel
  energy is met by each source — wind-assist, solar, hydrogen fuel-cell (with battery
  buffering peaks) — and the resulting green-H2 demand.

  HONEST: a transparent first-order model (Admiralty propulsion-power law + flat-rate
  solar capacity factor + average wind-assist saving fraction), NOT CFD or sea-keeping.
  It makes the wind/solar/hydrogen split EMPIRICAL rather than asserted. Numbers are
  :representative. The 6-DOF dynamics live in kami-autodrive ShipHydro (ADR-2606010600).

  House style: data maps are STRING-keyed (mirroring the Python dicts byte-for-byte);
  Python ':…' keyword strings stay strings; pure fns; file/host I/O only behind #?(:clj …).
  Float/round parity: Python f-string `{x:.Nf}` rounds the exact binary double HALF_EVEN —
  mirrored here with BigDecimal(double).setScale.

  The Python `__main__` demo printer is provided as the #?(:clj) -main; the side-effecting
  out/ writers stay behind the #?(:clj …) host edge."
  (:require [clojure.string :as str]
            #?(:clj [clojure.java.io :as io])))

;; Captured at load time so -main can find the actor out/ dir even when invoked
;; from another file (sci/bb rebind *file* to the caller at runtime).
#?(:clj (def ^:private source-file *file*))

;; ── reference vessel (mirrors data/vessel.edn, Nagi 凪 class) ──────────────────
;; @dataclass(frozen=True) Vessel — string-keyed map with the Python field defaults.

(defn vessel
  "Vessel() with default field values (string-keyed). Override with a partial map."
  ([] (vessel {}))
  ([overrides]
   (merge {"name" "Nagi 凪 (coastal cargo)"
           "dwt" 3000
           "displacement_t" 4500.0     ; full-load displacement ~ 1.5x DWT (small cargo)
           "admiralty_coeff" 450.0     ; Δ^(2/3)·V^3 / P_shaft ; typical small cargo
           "service_speed_kn" 10.0
           "hotel_load_kw" 120.0       ; auxiliary / hotel / control load
           ;; powertrain installed capacities
           "solar_kwp" 160.0
           "fuelcell_kw" 2400.0
           "battery_kwh" 2000.0
           "rotor_sails" 2}
          overrides)))

(defn voyage
  "Voyage() with default field values (string-keyed). Override with a partial map."
  ([] (voyage {}))
  ([overrides]
   (merge {"name" "representative coastal short-sea leg"
           "distance_nm" 200.0
           ;; environment / route assumptions (:representative)
           "solar_capacity_factor" 0.13      ; marine daytime-averaged annual CF
           "wind_assist_saving_frac" 0.18    ; avg propulsion-power saved by 2 rotor sails
           ;;   (rotor sails on suitable routes save ~10-30%; 18% = conservative mid)
           "propulsive_efficiency" 0.62      ; hull+pod quasi-propulsive coefficient
           "fuelcell_lhv_eff" 0.52}          ; PEM FC electrical efficiency (LHV)
          overrides)))

(def H2_LHV_KWH_PER_KG 33.33)  ; lower-heating-value energy density of hydrogen

(defn shaft-power-kw
  "Admiralty-coefficient propulsion power at service speed (calm water).
  disp^(2/3) · V^3 / admiralty_coeff."
  [v]
  (let [disp23 (Math/pow (double (get v "displacement_t")) (/ 2.0 3.0))]
    (/ (* disp23 (Math/pow (double (get v "service_speed_kn")) 3)) ;; V^3
       (double (get v "admiralty_coeff")))))

(defn simulate
  "Port of simulate(v, voy). Returns a string-keyed result map."
  [v voy]
  (let [hours (/ (double (get voy "distance_nm")) (double (get v "service_speed_kn")))

        ;; propulsion demand at the bus (account for propulsive efficiency of pod+hull)
        p-shaft (shaft-power-kw v)
        p-prop-bus (/ p-shaft (double (get voy "propulsive_efficiency")))
        prop-energy-kwh (* p-prop-bus hours)
        hotel-energy-kwh (* (double (get v "hotel_load_kw")) hours)
        total-demand-kwh (+ prop-energy-kwh hotel-energy-kwh)

        ;; ── wind-assist: reduces propulsion demand directly ──
        wind-kwh (* prop-energy-kwh (double (get voy "wind_assist_saving_frac")))

        ;; ── solar: average power = peak * capacity factor, over voyage hours ──
        solar-avg-kw (* (double (get v "solar_kwp")) (double (get voy "solar_capacity_factor")))
        solar-kwh (min (* solar-avg-kw hours) (+ hotel-energy-kwh (* prop-energy-kwh 0.10)))
        ;;   cap solar so it serves hotel + a little propulsion (it is NOT a main mover)

        ;; ── hydrogen fuel cell: supplies the residual; battery only shifts peaks ──
        residual-kwh (max 0.0 (- total-demand-kwh wind-kwh solar-kwh))
        h2-kg (/ residual-kwh (* H2_LHV_KWH_PER_KG (double (get voy "fuelcell_lhv_eff"))))

        shares {"wind_assist" (/ wind-kwh total-demand-kwh)
                "solar" (/ solar-kwh total-demand-kwh)
                "hydrogen_fuelcell" (/ residual-kwh total-demand-kwh)}

        ;; battery sanity: can it cover a peak-shave window (e.g. 30 min harbour manoeuvre)?
        harbour-manoeuvre-kw (+ (* p-prop-bus 0.6) (double (get v "hotel_load_kw")))
        battery-minutes (* (/ (double (get v "battery_kwh")) harbour-manoeuvre-kw) 60.0)]

    {"hours" hours
     "p_shaft_kw" p-shaft
     "p_prop_bus_kw" p-prop-bus
     "prop_energy_kwh" prop-energy-kwh
     "hotel_energy_kwh" hotel-energy-kwh
     "total_demand_kwh" total-demand-kwh
     "wind_kwh" wind-kwh
     "solar_kwh" solar-kwh
     "residual_kwh" residual-kwh
     "h2_kg" h2-kg
     "shares" shares
     "battery_harbour_minutes" battery-minutes
     "fossil_engine" false}))

;; ── float formatting (Python f-string parity: HALF_EVEN over the exact double) ──

(defn- fmt-f
  "Python `format(x, '.Nf')` — fixed-point N decimals, HALF_EVEN over the exact double."
  [x n]
  #?(:clj (-> (java.math.BigDecimal. (double x))
              (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
              (.toPlainString))
     :cljs (.toFixed (double x) (int n))))

(defn- fmt0 [x] (fmt-f x 0))   ; {x:.0f}
(defn- fmt1 [x] (fmt-f x 1))   ; {x:.1f}
(defn- fmt2 [x] (fmt-f x 2))   ; {x:.2f}
(defn- fmt4 [x] (fmt-f x 4))   ; {x:.4f}

(defn- pct
  "Python `pct = lambda x: f\"{x*100:.1f}%\"`."
  [x]
  (str (fmt1 (* (double x) 100.0)) "%"))

(defn report
  "Port of report(v, voy, r) — byte-identical markdown."
  [v voy r]
  (let [s (get r "shares")]
    (str
     "# funadaiku 船大工 — Nagi 凪 voyage energy budget\n"
     "\n"
     "> ADR-2606013400 · reduced-order analytic model (`methods/voyage_energy.py`) · :representative\n"
     "> **No fossil engine** (G13/N5). Hydrogen must be green (G14, well-to-wake).\n"
     "\n"
     "## Inputs\n"
     "\n"
     "| Vessel (" (get v "name") ") | | Voyage (" (get voy "name") ") | |\n"
     "|---|---|---|---|\n"
     "| DWT | " (get v "dwt") " | Distance | " (fmt0 (get voy "distance_nm")) " nm |\n"
     "| Displacement | " (fmt0 (get v "displacement_t")) " t | Service speed | " (fmt0 (get v "service_speed_kn")) " kn |\n"
     "| Solar | " (fmt0 (get v "solar_kwp")) " kWp | Voyage time | " (fmt1 (get r "hours")) " h |\n"
     "| Fuel cell | " (fmt0 (get v "fuelcell_kw")) " kW | Solar capacity factor | " (pct (get voy "solar_capacity_factor")) " |\n"
     "| Battery | " (fmt0 (get v "battery_kwh")) " kWh | Wind-assist saving | " (pct (get voy "wind_assist_saving_frac")) " |\n"
     "| Rotor sails | " (get v "rotor_sails") " | FC efficiency (LHV) | " (pct (get voy "fuelcell_lhv_eff")) " |\n"
     "\n"
     "## Result\n"
     "\n"
     "- Propulsion shaft power @ " (fmt0 (get v "service_speed_kn")) " kn: **" (fmt0 (get r "p_shaft_kw")) " kW** (Admiralty law, calm water)\n"
     "- Bus propulsion power (÷ QPC " (get voy "propulsive_efficiency") "): **" (fmt0 (get r "p_prop_bus_kw")) " kW**\n"
     "- Voyage energy demand (propulsion + hotel): **" (fmt0 (get r "total_demand_kwh")) " kWh**\n"
     "\n"
     "### Energy met by source\n"
     "\n"
     "| Source | Energy (kWh) | Share | Role |\n"
     "|---|---:|---:|---|\n"
     "| Wind-assist (2× rotor sail) | " (fmt0 (get r "wind_kwh")) " | **" (pct (get s "wind_assist")) "** | primary fuel-saver |\n"
     "| Solar deck | " (fmt0 (get r "solar_kwh")) " | **" (pct (get s "solar")) "** | hotel + top-up |\n"
     "| Hydrogen fuel cell (residual) | " (fmt0 (get r "residual_kwh")) " | **" (pct (get s "hydrogen_fuelcell")) "** | electrical prime mover |\n"
     "| **Fossil engine** | 0 | **0.0%** | none (G13) |\n"
     "\n"
     "- **Green hydrogen demand for this leg: " (fmt0 (get r "h2_kg")) " kg** (LHV " H2_LHV_KWH_PER_KG " kWh/kg ÷ FC " (pct (get voy "fuelcell_lhv_eff")) ")\n"
     "- Battery covers a harbour manoeuvre (~60% prop + hotel) for **" (fmt0 (get r "battery_harbour_minutes")) " min** → zero-emission at berth/port.\n"
     "\n"
     "## Honest reading\n"
     "\n"
     "Wind + solar together meet **" (pct (+ (double (get s "wind_assist")) (double (get s "solar")))) "** of this representative\n"
     "coastal leg; hydrogen carries the remaining **" (pct (get s "hydrogen_fuelcell")) "** as the prime mover —\n"
     "exactly the survey conclusion that **no single source is a complete prime mover** at cargo\n"
     "scale. Wind-assist share rises on windier/longer routes and falls on calm ones; solar is\n"
     "capped to hotel + a little propulsion by construction (low areal power). Tank-to-wake CO₂ is\n"
     "**zero**; the well-to-wake figure depends entirely on the **green-H₂ chain-of-custody** (G14) —\n"
     "hydrogen made from fossil power would erase the benefit. This is a first-order model, not CFD.\n")))

(defn to-edn
  "Port of to_edn(v, voy, r) — byte-identical kotoba EDN string."
  [_v voy r]
  (let [s (get r "shares")]
    (str
     ";; funadaiku Nagi 凪 — voyage energy-budget result (kotoba EAVT)\n"
     ";; ADR-2606013400 · generated by methods/voyage_energy.py · :representative\n"
     "[{:voyage/id \"funadaiku.nagi.voyage-rep-200nm\" :voyage/vessel \"funadaiku.nagi-0001\"\n"
     "  :voyage/distance-nm " (fmt0 (get voy "distance_nm")) " :voyage/hours " (fmt2 (get r "hours")) "\n"
     "  :voyage/total-demand-kwh " (fmt0 (get r "total_demand_kwh")) "\n"
     "  :voyage/share-wind " (fmt4 (get s "wind_assist")) " :voyage/share-solar " (fmt4 (get s "solar")) "\n"
     "  :voyage/share-hydrogen " (fmt4 (get s "hydrogen_fuelcell")) " :voyage/fossil-engine false\n"
     "  :voyage/green-h2-kg " (fmt0 (get r "h2_kg")) " :voyage/battery-harbour-min " (fmt0 (get r "battery_harbour_minutes")) "\n"
     "  :voyage/sourcing :representative}]\n")))

#?(:clj
   (defn -main
     "CLI entry — regenerate the deterministic out/ artifacts + print the summary
     (port of voyage_energy.py main())."
     [& _]
     (let [v (vessel)
           voy (voyage)
           r (simulate v voy)
           here (-> source-file io/file .getParentFile .getParentFile)
           out (io/file here "out")
           sh (get r "shares")]
       (.mkdirs out)
       (spit (io/file out "voyage-energy-report.md") (report v voy r))
       (spit (io/file out "voyage-energy.kotoba.edn") (to-edn v voy r))
       (println (str "Nagi 凪 voyage " (fmt0 (get voy "distance_nm")) " nm @ "
                     (fmt0 (get v "service_speed_kn")) " kn  "
                     "(" (fmt1 (get r "hours")) " h, " (fmt0 (get r "total_demand_kwh")) " kWh)"))
       (println (str "  wind-assist " (fmt1 (* (double (get sh "wind_assist")) 100.0)) "% | "
                     "solar " (fmt1 (* (double (get sh "solar")) 100.0)) "% | "
                     "hydrogen " (fmt1 (* (double (get sh "hydrogen_fuelcell")) 100.0)) "% | fossil 0.0%"))
       (println (str "  green-H2 demand: " (fmt0 (get r "h2_kg")) " kg   battery harbour: "
                     (fmt0 (get r "battery_harbour_minutes")) " min"))
       (println "  wrote out/voyage-energy-report.md + out/voyage-energy.kotoba.edn")
       0)))
