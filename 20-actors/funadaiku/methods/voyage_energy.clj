;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/funadaiku/methods/voyage_energy.py (unit_refactor stage 0)
;; funadaiku 船大工 — Nagi 凪 class voyage energy-budget simulation.
(ns root.funadaiku.methods.voyage-energy
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare vessel voyage h2-lhv-kwh-per-kg shaft-power-kw simulate report to-edn main)

(defn vessel []
  {:name "Nagi 凪 (coastal cargo)"
   :dwt 3000
   :displacement-t 4500.0
   :admiralty-coeff 450.0
   :service-speed-kn 10.0
   :hotel-load-kw 120.0
   :solar-kwp 160.0
   :fuelcell-kw 2400.0
   :battery-kwh 2000.0
   :rotor-sails 2})

;; TODO: port-failed unit Voyage (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpgwt_i0pu/scratch.clj:3:3: er)
;; class Voyage:
;;     name: str = "representative coastal short-sea leg"
;;     distance_nm: float = 200.0
;;     # environment / route assumptions (:representative)
;;     solar_capacity_factor: float = 0.13     # marine daytime-averaged annual CF
;;     wind_assist_saving_frac: float = 0.18    # avg propulsion-power saved by 2 rotor sails
;;     #   (rotor sails on suitable routes save ~10-30%; 18% = conservative mid)
;;     propulsive_efficiency: float = 0.62      # hull+pod quasi-propulsive coefficient
;;     fuelcell_lhv_eff: float = 0.52           # PEM FC electrical efficiency (LHV)
(defn voyage [& _]
  (throw (ex-info "TODO: port-failed" {:from "Voyage"})))

(def H2_LHV_KWH_PER_KG 33.33)

;; TODO: port-failed unit shaft_power_kw (assembled-lint error)
;; def shaft_power_kw(v: Vessel) -> float:
;;     """Admiralty-coefficient propulsion power at service speed (calm water)."""
;;     disp23 = v.displacement_t ** (2.0 / 3.0)
;;     return disp23 * (v.service_speed_kn ** 3) / v.admiralty_coeff
(defn shaft-power-kw [& _]
  (throw (ex-info "TODO: port-failed" {:from "shaft_power_kw"})))

(defn simulate [v voy]
  (let [hours (/ (:distance-nm voy) (:service-speed-kn v))

        ;; propulsion demand at the bus (account for propulsive efficiency of pod+hull)
        p_shaft (shaft-power-kw v)
        p_prop_bus (/ p_shaft (:propulsive-efficiency voy))
        prop_energy_kwh (* p_prop_bus hours)
        hotel_energy_kwh (* (:hotel-load-kw v) hours)
        total_demand_kwh (+ prop_energy_kwh hotel_energy_kwh)

        ;; ── wind-assist: reduces propulsion demand directly ──
        wind_kwh (* prop_energy_kwh (:wind-assist-saving-frac voy))

        ;; ── solar: average power = peak * capacity factor, over voyage hours ──
        solar_avg_kw (* (:solar-kwp v) (:solar-capacity-factor voy))
        solar_kwh (min (* solar_avg_kw hours) (+ hotel_energy_kwh (* prop_energy_kwh 0.10)))
        ;;   cap solar so it serves hotel + a little propulsion (it is NOT a main mover)

        ;; ── hydrogen fuel cell: supplies the residual; battery only shifts peaks ──
        residual_kwh (max 0.0 (- total_demand_kwh wind_kwh solar_kwh))
        h2_kg (/ residual_kwh (* H2_LHV_KWH_PER_KG (:fuelcell-lhv-eff voy)))

        shares {"wind_assist" (/ wind_kwh total_demand_kwh)
                "solar" (/ solar_kwh total_demand_kwh)
                "hydrogen_fuelcell" (/ residual_kwh total_demand_kwh)}

        ;; battery sanity: can it cover a peak-shave window (e.g. 30 min harbour manoeuvre)?
        harbour_manoeuvre_kw (+ (* p_prop_bus 0.6) (:hotel-load-kw v))
        battery_minutes (* (/ (:battery-kwh v) harbour_manoeuvre_kw) 60.0)]

    {:hours hours
     :p_shaft_kw p_shaft
     :p_prop_bus_kw p_prop_bus
     :prop_energy_kwh prop_energy_kwh
     :hotel_energy_kwh hotel_energy_kwh
     :total_demand_kwh total_demand_kwh
     :wind_kwh wind_kwh
     :solar_kwh solar_kwh
     :residual_kwh residual_kwh
     :h2_kg h2_kg
     :shares shares
     :battery_harbour_minutes battery_minutes
     :fossil_engine false}))

;; TODO: port-failed unit report (bb-compile error)
;; def report(v: Vessel, voy: Voyage, r: dict) -> str:
;;     s = r["shares"]
;;     pct = lambda x: f"{x*100:.1f}%"
;;     md = f"""# funadaiku 船大工 — Nagi 凪 voyage energy budget
;; 
;; > ADR-2606013400 · reduced-order analytic model (`methods/voyage_energy.py`) · :representative
;; > **No fossil engine** (G13/N5). Hydrogen must be green (G14, well-to-wake).
;; 
;; ## Inputs
;; 
;; | Vessel ({v.name}) | | Voyage ({voy.name}) | |
;; |---|---|---|---|
;; | DWT | {v.dwt} | Distance | {voy.distance_nm:.0f} nm |
;; | Displacement | {v.displacement_t:.0f} t | Service speed | {v.service_speed_kn:.0f} kn |
;; | Solar | {v.solar_kwp:.0f} kWp | Voyage time | {r['hours']:.1f} h |
;; | Fuel cell | {v.fuelcell_kw:.0f} kW | Solar capacity factor | {pct(voy.solar_capacity_factor)} |
;; | Battery | {v.battery_kwh:.0f} kWh | Wind-assist saving | {pct(voy.wind_assist_saving_frac)} |
;; | Rotor sails | {v.rotor_sails} | FC efficiency (LHV) | {pct(voy.fuelcell_lhv_eff)} |
;; 
;; ## Result
;; 
;; - Propulsion shaft power @ {v.service_speed_kn:.0f} kn: **{r['p_shaft_kw']:.0f} kW** (Admiralty law, calm water)
;; - Bus propulsion power (÷ QPC {voy.propulsive_efficiency}): **{r['p_prop_bus_kw']:.0f} kW**
;; - Voyage energy demand (propulsion + hotel): **{r['total_demand_kwh']:.0f} kWh**
;; 
;; ### Energy met by source
;; 
;; | Source | Energy (kWh) | Share | Role |
;; |---|---:|---:|---|
;; | Wind-assist (2× rotor sail) | {r['wind_kwh']:.0f} | **{pct(s['wind_assist'])}** | primary fuel-saver |
;; | Solar deck | {r['solar_kwh']:.0f} | **{pct(s['solar'])}** | hotel + top-up |
;; | Hydrogen fuel cell (residual) | {r['residual_kwh']:.0f} | **{pct(s['hydrogen_fuelcell'])}** | electrical prime mover |
;; | **Fossil engine** | 0 | **0.0%** | none (G13) |
;; 
;; - **Green hydrogen demand for this leg: {r['h2_kg']:.0f} kg** (LHV {H2_LHV_KWH_PER_KG} kWh/kg ÷ FC {pct(voy.fuelcell_lhv_eff)})
;; - Battery covers a harbour manoeuvre (~60% prop + hotel) for **{r['battery_harbour_minutes']:.0f} min** → zero-emission at berth/port.
;; 
;; ## Honest reading
;; 
;; Wind + solar together meet **{pct(s['wind_assist'] + s['solar'])}** of this representative
;; coastal leg; hydrogen carries the remaining **{pct(s['hydrogen_fuelcell'])}** as the prime mover —
;; exactly the survey conclusion that **no single source is a complete prime mover** at cargo
;; scale. Wind-assist share rises on windier/longer routes and falls on calm ones; solar is
;; capped to hotel + a little propulsion by construction (low areal power). Tank-to-wake CO₂ is
;; **zero**; the well-to-wake figure depends entirely on the **green-H₂ chain-of-custody** (G14) —
;; hydrogen made from fossil power would erase the benefit. This is a first-order model, not CFD.
;; """
;;     return md
(defn report [& _]
  (throw (ex-info "TODO: port-failed" {:from "report"})))

(defn to-edn [v voy r]
  (let [s (:shares r)
        distance (format "%.0f" (:distance-nm voy))
        hours (format "%.2f" (:hours r))
        total-demand (format "%.0f" (:total_demand_kwh r))
        wind-assist (format "%.4f" (:wind_assist s))
        solar (format "%.4f" (:solar s))
        hydrogen (format "%.4f" (:hydrogen_fuelcell s))
        h2-kg (format "%.0f" (:h2_kg r))
        battery-min (format "%.0f" (:battery_harbour_minutes r))]
    (str ";; funadaiku Nagi 凪 — voyage energy-budget result (kotoba EAVT)
;; ADR-2606013400 · generated by methods/voyage_energy.py · :representative
[{{:voyage/id \"funadaiku.nagi.voyage-rep-200nm\" :voyage/vessel \"funadaiku.nagi-0001\"
  :voyage/distance-nm "
  :voyage/hours \""
  :voyage/total-demand-kwh \""
  :voyage/share-wind \""
  :voyage/share-solar \""
  :voyage/share-hydrogen \""
  :voyage/fossil-engine false
  :voyage/green-h2-kg \""
  :voyage/battery-harbour-min \""
  :voyage/sourcing :representative}}]")))

;; TODO: port-failed unit main (bb-compile error)
;; def main() -> None:
;;     v, voy = Vessel(), Voyage()
;;     r = simulate(v, voy)
;;     here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
;;     out = os.path.join(here, "out")
;;     os.makedirs(out, exist_ok=True)
;;     with open(os.path.join(out, "voyage-energy-report.md"), "w") as f:
;;         f.write(report(v, voy, r))
;;     with open(os.path.join(out, "voyage-energy.kotoba.edn"), "w") as f:
;;         f.write(to_edn(v, voy, r))
;;     sh = r["shares"]
;;     print(f"Nagi 凪 voyage {voy.distance_nm:.0f} nm @ {v.service_speed_kn:.0f} kn  "
;;           f"({r['hours']:.1f} h, {r['total_demand_kwh']:.0f} kWh)")
;;     print(f"  wind-assist {sh['wind_assist']*100:5.1f}% | "
;;           f"solar {sh['solar']*100:5.1f}% | "
;;           f"hydrogen {sh['hydrogen_fuelcell']*100:5.1f}% | fossil 0.0%")
;;     print(f"  green-H2 demand: {r['h2_kg']:.0f} kg   battery harbour: {r['battery_harbour_minutes']:.0f} min")
;;     print(f"  wrote out/voyage-energy-report.md + out/voyage-energy.kotoba.edn")
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

