#!/usr/bin/env bb
;; Working Clojure port of methods/persist.py.
(ns mitooshi.methods.persist
  "mitooshi 見通し — append-only chokepoint-intel persistence (R0, offline).

  ADR-2606051800. `bridge.clj` turns ONE watari/watatsuna snapshot into `:series` + `:obs`
  datoms. This module PERSISTS successive snapshots into a single durable, **append-only**
  kotoba-EDN trail — the as-of observation history mitooshi actually forecasts (非終末論: a
  later snapshot never overwrites an earlier one; the trail only grows).

  Invariants preserved:
    * append-only — `append-obs` NEVER removes or mutates an existing `:obs`; a re-run is
      idempotent (dedup by `:obs/id`), and a new snapshot at a new `:obs/observed-at` is
      additive. There is no overwrite path (非終末論 — no final-state datom).
    * DERIVED / :representative — every persisted record stays `:series/sourcing
      :representative` and carries its `:obs/source-actor`; the trail header says 'DERIVED,
      do NOT re-ingest as authoritative' (G11 sourcing-honesty, G4 public-broadcast).
    * no live ingest — this writes a FILE. Pushing the trail into a live kotoba server is
      `--live`, which REFUSES without the G10 operator gate (mirrors watari/yadori).

  stdlib only. Run:
    bb --classpath 20-actors 20-actors/mitooshi/methods/persist.clj \\
       --watari ../data/bridge/watari-sample.edn \\
       --watatsuna ../data/bridge/watatsuna-sample.edn \\
       --at 1 --trail ../data/persisted/chokepoint-trail.kotoba.edn"
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [mitooshi.methods.bridge :as mb]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

;; ── EDN keyword → string key conversion ──────────────────────────────────────
;; The in-memory maps (from bridge.clj) use STRING keys like ":series/id".
;; The emitted EDN trail uses REAL EDN keywords like :series/id.
;; When we read the trail back, we must convert real keywords → string keys.

(defn- kw->str
  "Convert a Clojure keyword or any value to its string representation used as map key.
  Real keyword :series/id → string \":series/id\". Non-keywords pass through."
  [k]
  (if (keyword? k)
    (str ":" (if (namespace k) (str (namespace k) "/" (name k)) (name k)))
    k))

(defn- rec->str-keys
  "Convert a map whose keys are real EDN keywords into string-keyed map (bridge.clj style)."
  [m]
  (when (map? m)
    (into {} (map (fn [[k v]] [(kw->str k) v]) m))))

;; ── load-trail ────────────────────────────────────────────────────────────────

(defn load-trail
  "Read an existing trail file → [{series-id series-map} [obs...]]. Missing file = empty."
  [path]
  (let [f (io/file path)]
    (if-not (.exists f)
      [{} []]
      (let [recs (edn/read-string (slurp f))
            ;; recs is a vector of maps with real EDN keywords → convert to string-keyed
            str-recs (map rec->str-keys recs)
            series (reduce (fn [acc r]
                             (if (contains? r ":series/id")
                               (assoc acc (get r ":series/id") r)
                               acc))
                           {} str-recs)
            obs (filter #(contains? % ":obs/id") str-recs)]
        [series (vec obs)]))))

;; ── append-obs ────────────────────────────────────────────────────────────────

(defn append-obs
  "Append-only merge. Returns [merged n-added n-duplicate].

  A duplicate is an `:obs/id` already present — it is NOT re-added and NOT mutated
  (idempotent re-run). Existing obs are never removed (非終末論). Order is stable:
  existing first, then newly-added in input order."
  [existing incoming]
  (let [seen (atom (set (map #(get % ":obs/id") existing)))
        merged (atom (vec existing))
        added (atom 0)
        dup (atom 0)]
    (doseq [o incoming]
      (let [oid (get o ":obs/id")]
        (if (contains? @seen oid)
          (swap! dup inc)
          (do
            (swap! seen conj oid)
            (swap! merged conj o)
            (swap! added inc)))))
    [@merged @added @dup]))

;; ── merge-series ──────────────────────────────────────────────────────────────

(defn merge-series
  "Union of series definitions keyed by :series/id (a series is its identity; first
  definition wins — its metadata is stable across snapshots)."
  [existing incoming]
  (reduce (fn [acc [sid s]]
            (if (contains? acc sid)
              acc
              (assoc acc sid s)))
          existing
          incoming))

;; ── emit-trail-edn ───────────────────────────────────────────────────────────

(defn emit-trail-edn
  "Serialise the trail to append-only kotoba EDN. Obs sorted by (series, observed-at)
  so the as-of history of each chokepoint reads in order; the file is still append-only
  in MEANING (no obs dropped/mutated), the sort is presentation only."
  [series obs]
  (let [span (if (seq obs)
               (sort (set (map #(get % ":obs/observed-at") obs)))
               [])
        header [(str ";; chokepoint-trail.kotoba.edn — APPEND-ONLY as-of intel trail.")
                ";; Bridged from watari 渡り (transit-load) + watatsuna 綿津綱 (cable-load)."
                ";; DERIVED public :representative observations — do NOT re-ingest as authoritative."
                ";; 非終末論: snapshots only ACCUMULATE; no obs is ever overwritten. ADR-2606051800."
                (str ";; observed-at span: " (if (seq span) (str span) "(empty)")
                     "  |  series: " (count series) "  obs: " (count obs))
                ";; Live kotoba-server ingest of this trail is G10-gated (Council Lv6+ + operator)."
                ""
                "["]
        series-lines (for [s (sort-by #(get % ":series/id") (vals series))]
                       (str " {:series/id \"" (get s ":series/id") "\""
                            " :series/kind " (get s ":series/kind" ":transit-load")
                            " :series/unit \"" (get s ":series/unit" "") "\""
                            " :series/source-class :public-broadcast"
                            " :series/sourcing :representative}"))
        obs-sorted (sort-by (juxt #(get % ":obs/series") #(get % ":obs/observed-at")) obs)
        obs-lines (for [o obs-sorted]
                    (str " {:obs/id \"" (get o ":obs/id") "\""
                         " :obs/series \"" (get o ":obs/series") "\""
                         " :obs/observed-at " (get o ":obs/observed-at")
                         " :obs/value " (get o ":obs/value")
                         " :obs/source-actor \"" (get o ":obs/source-actor" "?") "\"}"))
        footer ["]"]]
    (str (str/join "\n" (concat header series-lines obs-lines footer)) "\n")))

;; ── persist ───────────────────────────────────────────────────────────────────

(defn persist
  "Append a bridged snapshot to the durable trail file (creating it if absent).
  Returns {:added :duplicate :total-obs :series}."
  [trail-path bridged]
  (let [[ex-series ex-obs] (load-trail trail-path)
        [merged-obs added dup] (append-obs ex-obs (get bridged "obs"))
        merged-series (merge-series ex-series (get bridged "series"))
        f (io/file trail-path)]
    (.mkdirs (.getParentFile (.getAbsoluteFile f)))
    (spit f (emit-trail-edn merged-series merged-obs))
    {"added"      added
     "duplicate"  dup
     "total_obs"  (count merged-obs)
     "series"     (count merged-series)}))

;; ── main ─────────────────────────────────────────────────────────────────────

(defn main [& argv]
  (let [args (vec argv)]
    (when (or (not (.contains args "--at")) (not (.contains args "--trail")))
      (println "persist: --at <ts> and --trail <path> are required")
      (System/exit 1))
    (let [observed-at (Long/parseLong (nth args (inc (.indexOf args "--at"))))
          trail-path  (io/file (nth args (inc (.indexOf args "--trail"))))
          by-actor
          (reduce (fn [m [actor flag]]
                    (let [idx (.indexOf args flag)]
                      (if (>= idx 0)
                        (assoc m actor (mb/load-edn (nth args (inc idx))))
                        m)))
                  {}
                  [["watari" "--watari"] ["watatsuna" "--watatsuna"]])]
      (when (empty? by-actor)
        (println "persist: provide at least one of --watari <edn> / --watatsuna <edn>")
        (System/exit 1))
      (when (.contains args "--live")
        (let [allow (System/getenv "MITOOSHI_ALLOW_LIVE_INGEST")]
          (when (not= allow "1")
            (println "persist --live REFUSED (G10): live kotoba-server ingest needs Council"
                     "Lv6+ + operator (set MITOOSHI_ALLOW_LIVE_INGEST=1 after ratification)."
                     "Offline file persistence runs without --live.")
            (System/exit 1)))
        (println "persist --live: operator-gated kotoba ingest not implemented at R0"
                 "(file-persistence only). Remove --live to write the durable trail.")
        (System/exit 1))
      (let [bridged (mb/bridge by-actor observed-at)
            stats   (persist trail-path bridged)]
        (println (str "mitooshi persist @ ts=" observed-at " → " trail-path))
        (println (str "  +" (get stats "added") " obs added, "
                      (get stats "duplicate") " duplicate(s) skipped"
                      " (idempotent); trail now " (get stats "total_obs")
                      " obs across " (get stats "series") " series"))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
