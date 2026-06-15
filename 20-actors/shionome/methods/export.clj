#!/usr/bin/env bb
;; Clojure port of methods/export.py — 潮目 (shionome) → kanae render payload.
(ns shionome.methods.export
  "export.clj — 潮目 (shionome) → kanae render payload. ADR-2606072201.

  kanae (鼎) renders fund flows (Sankey/treemap). shionome emits its capital-movement :flow
  datoms in kanae fundFlowEdge shape and packages the aggregate concentration into a JSON-safe
  render payload.

  Honest scope (G11 + G2): only CAPITAL-MOVEMENT flow kinds are exported as fund flows
  (rotation / fund-inflow / fund-outflow / fx-flow). Observation-only kinds (cross-correlation /
  price-move / volume-shift / yield-shift) are in other units (zscore / pct / bps), NOT capital
  amounts, so they are excluded and reported as a skip count (no silent drop). Every payload
  carries isMirror + noTrade flags. Offline, deterministic; no live publish (G8).

  Reuses weave.cljc's CAPITAL-MOVEMENT-KINDS (a public def). The private `kw*` fn is inlined
  here (babashka cannot reach cross-ns private vars) — see grounding.clj for the same pattern."
  (:require [shionome.methods.weave :as w]
            [clojure.string :as str]
            [cheshire.core :as json]))

;; ── kw* inlined from weave.cljc (private there — babashka cannot reach cross-ns private vars) ──
;; Mirror of weave.cljc `kw*` which mirrors weave.py `_kw`:
;;   str(v or "").lstrip(":") → split("/")[-1].lower()
(defn- kw*
  "Normalize an edn keyword/string to a bare lowercase token (':flow/kind' → 'kind').
  Inlined mirror of weave.cljc `kw*` (private there). Do NOT modify independently."
  [v]
  (let [s (-> (str (or v "")) (str/replace #"^:+" ""))]
    (-> (last (str/split s #"/" -1)) str/lower-case)))

(defn to-kanae-flow
  "One shionome capital-movement :flow → one kanae fundFlowEdge. Throws if the kind is an
  observation-only kind (not a capital amount)."
  [f]
  (let [kind (kw* (get f ":flow/kind"))]
    (when-not (some #(= % kind) w/CAPITAL-MOVEMENT-KINDS)
      (throw (ex-info (str "export: " (pr-str kind)
                           " is an observation, not a capital flow (excluded from kanae render)")
                      {:kind kind})))
    {"edgeId"    (str "shionome:" (str (get f ":flow/id" "?")))
     "flowType"  kind
     "donor"     (get f ":flow/source" "")
     "recipient" (get f ":flow/target" "")
     "amount"    (double (get f ":flow/magnitude" 0.0))
     "currency"  (get f ":flow/unit" "")
     "asOf"      (long (get f ":flow/as-of" 0))
     "noTrade"   true
     "sources"   (vec (get f ":flow/sources" []))}))

(defn to-kanae-flows
  "All capital-movement :flow → kanae flows; observation-only kinds skipped + counted."
  [g]
  (let [{:keys [flows skipped]}
        (reduce (fn [{:keys [flows skipped]} f]
                  (if (some #(= % (kw* (get f ":flow/kind"))) w/CAPITAL-MOVEMENT-KINDS)
                    {:flows (conj flows (to-kanae-flow f)) :skipped skipped}
                    {:flows flows :skipped (conj skipped (get f ":flow/id"))}))
                {:flows [] :skipped []}
                (get g "flows"))]
    {"flows"         flows
     "skipped"       skipped
     "skipped_count" (count skipped)}))

(defn render-payload
  "JSON-safe aggregate concentration for a kanae render (Sankey/treemap-ready). Tuples are
  flattened to [key, value] pairs; no sets remain. Carries the mirror/no-trade flags."
  [c]
  {"actor"               "shionome"
   "isMirror"            true
   "noTrade"             true
   "counts"              (select-keys c ["bucket_count" "flow_count" "snapshot_count"])
   "net_flow_by_bucket"  (get c "net_flow_by_bucket")
   "rotation_pairs"      (get c "rotation_pairs")
   "inflow_shares"       (mapv vec (get-in c ["inflow_concentration" "shares"]))
   "inflow_hhi"          (get-in c ["inflow_concentration" "hhi"])
   "by_asset_class"      (get c "by_asset_class")
   "by_region"           (get c "by_region")
   "regime"              (get c "regime")
   "correlation_clusters" (get c "correlation_clusters")})

(defn render-json
  "The render payload as a JSON string (proves it is fully serializable). sort_keys=True."
  [c]
  (json/generate-string (render-payload c) {:sort-keys true}))

(defn -main [& _argv]
  (let [here (-> *file* java.io.File. .getAbsoluteFile .getParentFile)
        seed (str (java.io.File. here "../data/seed-capital-flow-graph.kotoba.edn"))
        g    (w/weave ((requiring-resolve 'shionome.methods.edn/load-edn) seed))
        kf   (to-kanae-flows g)]
    (println (str "# shionome → kanae export — " (count (get kf "flows"))
                  " capital flows, " (get kf "skipped_count") " observation-only skipped"))
    (doseq [f (get kf "flows")]
      (println (str "  " (format "%-13s" (get f "flowType")) " "
                    (get f "donor") " → " (get f "recipient") "  "
                    (format "%.1f" (get f "amount")) " " (get f "currency"))))
    (println (str "  render payload JSON bytes: "
                  (count (.getBytes (render-json (w/concentration g)) "UTF-8"))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
