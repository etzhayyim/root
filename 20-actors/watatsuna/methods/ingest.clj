#!/usr/bin/env bb
;; Working Clojure port of methods/ingest.py.
(ns watatsuna.methods.ingest
  "watatsuna 綿津綱 — TeleGeography-bridge ingester (public cable dataset → kotoba EAVT).

  Normalizes a public submarine-cable dataset (submarinecablemap.com / TeleGeography-shaped JSON:
  cables[] + landing_points[]) into the watatsuna ontology (:cable/* :station/* :cable.link/*),
  merges it with the curated seed graph (dedup by id, seed wins), and writes a merged graph
  analyze.clj can consume.

  GATES: G1 public-only · G2 resilience-not-interdiction — chokepoint tags come ONLY from the
  input and ONLY for KNOWN names; the ingester NEVER synthesizes a chokepoint (that would be a
  fabricated targeting signal) · G5 sourcing-honesty (offline/sample = :representative; only a
  live operator-gated attributed fetch tags :authoritative) · G7 outward-gated — LIVE fetch
  (--live) requires WATATSUNA_OPERATOR_GATE and even then is an R0 scaffold (refused).

  Run:  bb --classpath 20-actors 20-actors/watatsuna/methods/ingest.clj [src.json ...]"
  (:require [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [watatsuna.methods.analyze :as a]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(def known-chokepoints
  #{"luzon-strait" "malacca" "suez-red-sea" "south-china-sea" "gibraltar"
    "hormuz" "bab-el-mandeb" "sunda" "lombok" "taiwan-strait"})

(defn- slug [s]
  (-> (str/lower-case (str s)) (str/replace #"[^a-z0-9]+" "-") (str/replace #"^-+|-+$" "")))

(defn bridge-source
  "One public dataset JSON file → {:cables [] :stations [] :links []} in the kotoba ontology."
  [path & {:keys [sourcing] :or {sourcing "representative"}}]
  (let [doc (json/parse-string (slurp (io/file path)) true)
        src-kw (keyword sourcing)
        lps (:landing_points doc)
        station-id (into {} (map (fn [p] [(:id p) (str "station." (str/lower-case (or (:country p) "xx"))
                                                       "." (slug (:name p)))]) lps))
        stations (mapv (fn [p]
                         (let [sid (station-id (:id p))
                               ;; G2/G1: chokepoints ONLY from input, ONLY known names (never synthesized)
                               cps (vec (filter known-chokepoints (or (:chokepoints p) [])))]
                           (cond-> {:station/id sid :station/name (:name p)
                                    :station/country (or (:country p) "??")}
                             (contains? p :lat) (assoc :station/lat (:lat p))
                             (contains? p :lon) (assoc :station/lon (:lon p))
                             (seq cps) (assoc :station/chokepoint cps)
                             true (assoc :station/sourcing src-kw))))
                       lps)
        cables (mapv (fn [c]
                       (cond-> {:cable/id (str "cable." (slug (:id c))) :cable/name (:name c)
                                :cable/status :in-service}
                         (seq (:owners c)) (assoc :cable/owner-consortium (vec (:owners c)))
                         (contains? c :length_km) (assoc :cable/length-km (long (:length_km c)))
                         (contains? c :design_capacity_tbps) (assoc :cable/design-capacity-tbps
                                                                    (double (:design_capacity_tbps c)))
                         (contains? c :rfs) (assoc :cable/rfs-year (long (:rfs c)))
                         true (assoc :cable/sourcing src-kw)))
                     (:cables doc))
        links (vec (mapcat (fn [c]
                             (let [cid (str "cable." (slug (:id c)))]
                               (keep (fn [raw]
                                       (when-let [sid (station-id raw)]
                                         {:cable.link/id (str "lk." (slug (:id c)) "."
                                                              (last (str/split sid #"\.")))
                                          :cable.link/cable cid :cable.link/station sid
                                          :cable.link/sourcing src-kw}))
                                     (:landing_point_ids c))))
                           (:cables doc)))]
    {:cables cables :stations stations :links links}))

(def ^:private id-keys [:cable/id :station/id :cable.link/id :cable.seg/id :cable.fault/id])
(defn- rec-key [rec] (some #(get rec %) id-keys))

(defn merge-graph
  "Merge seed + bridged records, dedup by id (seed wins on conflict)."
  [seed bridged]
  (first
   (reduce (fn [[out seen] rec]
             (if-not (map? rec)
               [out seen]
               (let [k (rec-key rec)]
                 (if (and k (not (seen k)))
                   [(conj out rec) (conj seen k)]
                   [out seen]))))
           [[] #{}] (concat seed bridged))))

(defn live-refusal
  "Returns the G7 refusal message if --live is requested, else nil (offline needs no flag)."
  [argv env-gate]
  (when (some #{"--live"} argv)
    (if (str/blank? (str env-gate))
      (str "REFUSED: live cable-dataset ingest is G7/Council-gated. Set "
           "WATATSUNA_OPERATOR_GATE=<council-token> + supply an operator DID. "
           "Offline mode (no --live) needs no flag.")
      (str "REFUSED: live fetch is an R0 scaffold — not implemented. Wire the TeleGeography / "
           "submarinecablemap public feed via @etzhayyim/sdk under Council ratification, "
           "tag :authoritative, then re-run."))))

(defn to-edn [recs header-lines]
  (str/join "\n" (concat header-lines ["["] (map #(str " " (pr-str %)) recs) ["]" ""])))

(defn main [& argv]
  (when-let [msg (live-refusal argv (System/getenv "WATATSUNA_OPERATOR_GATE"))]
    (println msg) (System/exit 2))
  (let [root (actor-root)
        srcs (let [explicit (remove #(str/starts-with? % "--") argv)]
               (if (seq explicit) (map io/file explicit)
                   (sort (filter #(str/ends-with? (.getName %) ".json")
                                 (.listFiles (io/file root "data" "ingest"))))))
        bridged (vec (mapcat (fn [s]
                               (let [{:keys [cables stations links]} (bridge-source s)]
                                 (println (format "  bridged %s: %d cables · %d stations · %d links"
                                                  (.getName (io/file s)) (count cables) (count stations) (count links)))
                                 (concat cables stations links)))
                             srcs))
        seed (a/load-edn (io/file root "data" "seed-cable-graph.kotoba.edn"))
        merged (merge-graph seed bridged)
        nc (count (filter :cable/id merged))
        ns* (count (filter :station/id merged))]
    (spit (io/file root "data" "ingest" "telegeography-bridge.kotoba.edn")
          (to-edn bridged [";; watatsuna — GENERATED bridge graph (public dataset → kotoba EAVT). DO NOT hand-edit."
                           ";; :representative (offline/sample). Live operator-gated fetch would tag :authoritative (G5/G7)."]))
    (spit (io/file root "data" "cable-graph.merged.kotoba.edn")
          (to-edn merged [";; watatsuna — GENERATED merged graph (seed + ingest bridge). DO NOT hand-edit."
                          ";; dedup by id, seed wins. aggregate-first · sourcing-honest (ADR-2606012600)."]))
    (println (format "= merged graph: %d cables · %d stations · %d total records" nc ns* (count merged)))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
