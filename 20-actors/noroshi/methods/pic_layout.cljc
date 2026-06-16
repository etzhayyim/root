(ns noroshi.methods.pic-layout
  "noroshi (烽) photonic-IC layout generator (ADR-2606051600 §R1b).
  1:1 Clojure port of methods/pic_layout.py. Stdlib only.

  Generates a Tx/Rx PIC as a neutral ModelOp plan and closes the loop back to
  link_budget. The optional gdsfactory backend is never importable here, so try-build-gds
  always returns the gated, honest stub (mirroring the Python ImportError branch).
  The __main__ demo is omitted."
  (:require [clojure.string :as str]
            [noroshi.methods.link-budget :as lb]))

(defn model-op
  [op name & {:keys [kind x_um y_um length_um ports]
              :or {kind "" x_um 0.0 y_um 0.0 length_um 0.0 ports []}}]
  {"op" op "name" name "kind" kind "x_um" x_um "y_um" y_um "length_um" length_um "ports" ports})

(defn transmitter-plan
  ([] (transmitter-plan "noroshi-tx-pic" 1500.0))
  ([name route-um]
   (when (<= route-um 0)
     (throw (ex-info "route_um (modulator→coupler waveguide length) must be positive" {})))
   (let [ops [(model-op "place" "laser0" :kind "laser" :x_um 0.0 :y_um 0.0)
              (model-op "place" "mzm0" :kind "mzm" :x_um 200.0 :y_um 0.0)
              (model-op "place" "gc0" :kind "grating_coupler" :x_um (+ 200.0 route-um) :y_um 0.0)
              (model-op "route" "wg_laser_mzm" :length_um 200.0 :ports ["laser0.o" "mzm0.i"])
              (model-op "route" "wg_mzm_gc" :length_um route-um :ports ["mzm0.o" "gc0.i"])]
         total-wg (reduce + (map #(get % "length_um") (filter #(= (get % "op") "route") ops)))
         comps (mapv #(get % "name") (filter #(= (get % "op") "place") ops))]
     {"name" name "ops" ops "total_waveguide_um" total-wg "components" comps})))

(defn receiver-plan
  ([] (receiver-plan "noroshi-rx-pic" 1000.0))
  ([name route-um]
   (when (<= route-um 0)
     (throw (ex-info "route_um (coupler→photodetector waveguide length) must be positive" {})))
   (let [ops [(model-op "place" "gc_in" :kind "grating_coupler" :x_um 0.0 :y_um 0.0)
              (model-op "place" "pd0" :kind "photodetector" :x_um route-um :y_um 0.0)
              (model-op "route" "wg_gc_pd" :length_um route-um :ports ["gc_in.o" "pd0.i"])]
         total-wg (reduce + (map #(get % "length_um") (filter #(= (get % "op") "route") ops)))
         comps (mapv #(get % "name") (filter #(= (get % "op") "place") ops))]
     {"name" name "ops" ops "total_waveguide_um" total-wg "components" comps})))

(defn plan-to-link-design
  "Feed the plan's on-chip waveguide length into a link budget (the layout→budget loop)."
  ([plan] (plan-to-link-design plan nil))
  ([plan base]
   (let [base (or base (lb/link-design))
         tx-wg-cm (/ (get plan "total_waveguide_um") 1e4)]
     (lb/link-design :name (str (get plan "name") "-budget")
                     :tx_waveguide_cm tx-wg-cm
                     :rx_waveguide_cm (get base "rx_waveguide_cm")))))

(defn full-link-design
  "Compose BOTH on-chip waveguide lengths (tx + rx PIC) into one end-to-end link design."
  ([tx-plan rx-plan] (full-link-design tx-plan rx-plan nil))
  ([tx-plan rx-plan _base]
   (lb/link-design :name (str (get tx-plan "name") "+" (get rx-plan "name") "-budget")
                   :tx_waveguide_cm (/ (get tx-plan "total_waveguide_um") 1e4)
                   :rx_waveguide_cm (/ (get rx-plan "total_waveguide_um") 1e4))))

(defn try-build-gds
  "gdsfactory is never importable on this host → return the gated, honest stub result
  (mirrors the Python ImportError branch)."
  ([plan] (try-build-gds plan "out/noroshi-tx-pic.gds"))
  ([plan _out-path]
   {"built" false
    "reason" (str "gdsfactory not available (ImportError); GDS write gated (G8) — "
                  "the verifiable R0 artifact is the ModelOp plan, not a mask")
    "components" (get plan "components")}))

(defn- fmt [fmt-str x] (#?(:clj format :default (fn [_ v] (str v))) fmt-str (double x)))

(defn report []
  (let [tx (transmitter-plan) rx (receiver-plan)
        budget (lb/compute (full-link-design tx rx))
        gds (try-build-gds tx)
        lines (atom ["# noroshi 烽 — photonic-IC layout (open-EDA / GDSFactory-shaped ModelOp plan)" ""])]
    (doseq [[plan role] [[tx "transmitter"] [rx "receiver"]]]
      (swap! lines into
             [(str "## " role " plan: " (get plan "name"))
              (str "- components       : " (str/join ", " (get plan "components")))
              (str "- total waveguide  : " (fmt "%.0f" (get plan "total_waveguide_um")) " µm (" (fmt "%.3f" (/ (get plan "total_waveguide_um") 1e4)) " cm)")
              "- ops:"])
      (doseq [o (get plan "ops")]
        (if (= (get o "op") "place")
          (swap! lines conj (str "  - place " (get o "name") " (" (get o "kind") ") @ (" (fmt "%.0f" (get o "x_um")) "," (fmt "%.0f" (get o "y_um")) ") µm"))
          (swap! lines conj (str "  - route " (get o "name") ": " (get (get o "ports") 0) " → " (get (get o "ports") 1) "  (" (fmt "%.0f" (get o "length_um")) " µm)"))))
      (swap! lines conj ""))
    (swap! lines into
           ["## end-to-end layout → link budget (tx + rx waveguide, the closed loop)"
            (str "- both PIC waveguides → received " (get budget "received_dbm") " dBm, "
                 "margin " (get budget "margin_db") " dB → " (if (get budget "closes") "CLOSES" "FAILS"))
            ""
            "## GDS write (open-EDA backend, outward-gated G8)"
            (str "- " (if (get gds "built") (str "built " (get gds "path")) (get gds "reason")))
            ""
            (str "> R0 verifiable artifact = the deterministic ModelOp plan + the layout→budget loop. "
                 "The GDS write runs only with the open-source gdsfactory installed and is G8-gated; "
                 "no proprietary EDA, no NDA foundry PDK (G1/N5).")])
    (str/join "\n" @lines)))
