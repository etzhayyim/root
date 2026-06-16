(ns noroshi.methods.cable-endpoint
  "noroshi (烽) ↔ watatsuna (綿津綱) optical-network resilience join (ADR-2606051600 §R1c).
  1:1 Clojure port of methods/cable_endpoint.py. Stdlib only.

  Reads the watatsuna submarine-cable seed and sizes the CPO transceiver fleet per cable,
  per station, and per chokepoint, using the noroshi CPO reference link. The resilience
  lens is inherited from watatsuna (NEVER a target-list). The __main__ demo is omitted."
  (:require [clojure.string :as str]
            [noroshi.methods._edn :as edn]
            [noroshi.methods.link-budget :as lb]))

;; ROOT/20-actors from this file: …/noroshi/methods/cable_endpoint.cljc → up 2 = 20-actors.
#?(:clj
   (def ^:private watatsuna-seed
     (-> (java.io.File. *file*) .getParentFile .getParentFile .getParentFile
         (java.io.File. "watatsuna") (java.io.File. "data")
         (java.io.File. "seed-cable-graph.kotoba.edn"))))

(defn lanes-for
  "CPO transceiver lanes needed to carry a cable's design capacity at one landing."
  [capacity-tbps line-rate-gbps]
  (max 1 (long (Math/ceil (/ (* capacity-tbps 1000.0) line-rate-gbps)))))

#?(:clj
   (defn load-graph
     ([] (load-graph nil))
     ([seed]
      (let [seed (or seed watatsuna-seed)
            f (java.io.File. (str seed))]
        (when-not (.exists f)
          (throw (ex-info (str "watatsuna cable seed not found at " seed "; the noroshi×watatsuna join needs the "
                               "sibling actor's seed (20-actors/watatsuna/data/seed-cable-graph.kotoba.edn)")
                          {:type :file-not-found})))
        (let [rows (edn/load-edn seed)]
          (loop [rows rows cables {} stations {} links [] segments []]
            (if (empty? rows)
              {"cables" cables "stations" stations "links" links "segments" segments}
              (let [r (first rows)]
                (cond
                  (not (map? r)) (recur (rest rows) cables stations links segments)
                  (contains? r ":cable/id") (recur (rest rows) (assoc cables (get r ":cable/id") r) stations links segments)
                  (contains? r ":station/id") (recur (rest rows) cables (assoc stations (get r ":station/id") r) links segments)
                  (contains? r ":cable.link/id") (recur (rest rows) cables stations (conj links r) segments)
                  (contains? r ":cable.seg/id") (recur (rest rows) cables stations links (conj segments r))
                  :else (recur (rest rows) cables stations links segments))))))))))

(defn- rank
  "Mirror Python _rank: list of {chokepoint lanes cables capacity_tbps} sorted lanes desc.
  Python sorted is stable; the input dict preserves insertion order."
  [d order]
  (->> order
       (map (fn [k] (let [v (get d k)]
                      {"chokepoint" k "lanes" (get v "lanes") "cables" (count (get v "cables"))
                       "capacity_tbps" (-> (get v "capacity_tbps") (* 10.0) Math/round (/ 10.0))})))
       (sort-by #(get % "lanes") #(compare %2 %1))
       vec))

#?(:clj
   (defn size-fleet
     "Size the CPO transceiver fleet per cable / station / chokepoint from the watatsuna graph."
     ([] (size-fleet nil))
     ([seed]
      (let [g (load-graph seed)
            budget (lb/compute lb/CPO-REFERENCE)
            line-rate (get lb/CPO-REFERENCE "line_rate_gbps")
            energy-pj (get budget "energy_pj_per_bit")
            ;; incidence: cable → [station …] (preserve link append order)
            incidence (reduce (fn [acc lk]
                                (update acc (get lk ":cable.link/cable") (fnil conj []) (get lk ":cable.link/station")))
                              {} (get g "links"))
            ;; authoritative per-cable chokepoint crossings from :cable.seg/traverses
            seg-crossings (reduce (fn [acc sg]
                                    (let [cid (get sg ":cable.seg/cable")]
                                      (reduce (fn [a cp] (update a cid (fnil conj #{}) cp))
                                              acc (or (get sg ":cable.seg/traverses") []))))
                                  {} (get g "segments"))]
        ;; iterate cables in insertion order
        (loop [cable-ids (keys (get g "cables"))
               per-cable []
               by-station {}
               by-chokepoint {}      ; ordered via tracking order vector
               cp-order []
               by-chokepoint-seg {}
               cp-seg-order []]
          (if (empty? cable-ids)
            (let [_ nil]
              {"per_cable" per-cable
               "by_station_lanes" by-station
               "chokepoints" (rank by-chokepoint cp-order)
               "chokepoints_via_segments" (rank by-chokepoint-seg cp-seg-order)
               "lane_rate_gbps" line-rate
               "energy_pj_per_bit" energy-pj})
            (let [cid (first cable-ids)
                  c (get-in g ["cables" cid])
                  status (get c ":cable/status")]
              (if-not (or (= status ":in-service") (nil? status))
                (recur (rest cable-ids) per-cable by-station by-chokepoint cp-order by-chokepoint-seg cp-seg-order)
                (let [cap (double (or (get c ":cable/design-capacity-tbps") 0.0))
                      stns (get incidence cid [])
                      lanes (lanes-for cap line-rate)
                      energy-kw (-> (/ (* energy-pj cap) 1e3) (* 100.0) Math/round (/ 100.0))
                      cab {"cable_id" cid "name" (get c ":cable/name" cid) "design_capacity_tbps" cap
                           "stations" stns "lanes_per_endpoint" lanes "energy_kw" energy-kw}
                      ;; per station + chokepoint via station tags
                      [by-station2 by-cp2 cp-order2]
                      (reduce (fn [[bs bcp cpo] s]
                                (let [bs2 (update bs s (fnil + 0) lanes)
                                      cps (or (get-in g ["stations" s ":station/chokepoint"]) [])]
                                  (reduce (fn [[bs bcp cpo] cp]
                                            (let [seen? (contains? bcp cp)
                                                  agg (get bcp cp {"lanes" 0 "cables" #{} "capacity_tbps" 0.0})
                                                  agg2 {"lanes" (+ (get agg "lanes") lanes)
                                                        "cables" (conj (get agg "cables") cid)
                                                        "capacity_tbps" (+ (get agg "capacity_tbps") cap)}]
                                              [bs (assoc bcp cp agg2) (if seen? cpo (conj cpo cp))]))
                                          [bs2 bcp cpo] cps)))
                              [by-station by-chokepoint cp-order] stns)
                      ;; authoritative crossing attribution via segments
                      [by-cp-seg2 cp-seg-order2]
                      (reduce (fn [[bcp cpo] cp]
                                (let [seen? (contains? bcp cp)
                                      agg (get bcp cp {"lanes" 0 "cables" #{} "capacity_tbps" 0.0})
                                      agg2 {"lanes" (+ (get agg "lanes") lanes)
                                            "cables" (conj (get agg "cables") cid)
                                            "capacity_tbps" (+ (get agg "capacity_tbps") cap)}]
                                  [(assoc bcp cp agg2) (if seen? cpo (conj cpo cp))]))
                              [by-chokepoint-seg cp-seg-order] (get seg-crossings cid #{}))]
                  (recur (rest cable-ids) (conj per-cable cab) by-station2
                         by-cp2 cp-order2 by-cp-seg2 cp-seg-order2))))))))))

#?(:clj
   (defn report
     ([] (report nil))
     ([seed]
      (let [f (size-fleet seed)
            lines (atom ["# noroshi 烽 × watatsuna 綿津綱 — optical-network resilience (CPO transceivers at the cable ends)"
                         ""
                         (str "Each in-service cable terminates on noroshi CPO transceivers ("
                              (format "%.2f" (double (get f "lane_rate_gbps"))) " Gb/s/lane, "
                              (get f "energy_pj_per_bit") " pJ/bit). Demand sized from the watatsuna seed.")
                         ""
                         "## CPO transceiver demand behind each maritime chokepoint (resilience, NOT a target-list)"
                         "| chokepoint | CPO lanes (per end) | cables | aggregate capacity (Tb/s) |"
                         "|---|---|---|---|"])]
        (doseq [cp (get f "chokepoints")]
          (swap! lines conj (str "| " (get cp "chokepoint") " | " (get cp "lanes") " | " (get cp "cables") " | " (get cp "capacity_tbps") " |")))
        (swap! lines into
               ["" "## same demand by AUTHORITATIVE segment crossing (:cable.seg/traverses — physical, not landing-tag)"
                "| chokepoint | CPO lanes (per end) | cables | aggregate capacity (Tb/s) |"
                "|---|---|---|---|"])
        (doseq [cp (get f "chokepoints_via_segments")]
          (swap! lines conj (str "| " (get cp "chokepoint") " | " (get cp "lanes") " | " (get cp "cables") " | " (get cp "capacity_tbps") " |")))
        (swap! lines into ["" "## per-cable endpoint transceiver sizing" "| cable | capacity (Tb/s) | landings | CPO lanes/end | endpoint power (kW) |" "|---|---|---|---|---|"])
        (doseq [c (sort-by #(get % "lanes_per_endpoint") #(compare %2 %1) (get f "per_cable"))]
          (swap! lines conj (str "| " (get c "name") " | " (get c "design_capacity_tbps") " | " (count (get c "stations")) " | " (get c "lanes_per_endpoint") " | " (get c "energy_kw") " |")))
        (swap! lines into
               ["" (str "> **Composition**: watatsuna ranks where cable *capacity* concentrates behind a chokepoint; "
                        "noroshi turns that into the *transceiver* fleet that must be built and diversified there. "
                        "The output routes to **redundant endpoints + diverse routes + faster repair**, never "
                        "interdiction (watatsuna G2 / watatsumi N8). R0: sizing arithmetic over the `:representative` "
                        "watatsuna seed + the noroshi CPO reference; no live deployment (G8).")])
        (str/join "\n" @lines)))))
