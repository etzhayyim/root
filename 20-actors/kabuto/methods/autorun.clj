#!/usr/bin/env bb
;; Working Clojure port of methods/autorun.py — the autonomous supply-chain heartbeat.
(ns kabuto.methods.autorun
  "autorun.clj — kabuto AUTONOMOUS supply-chain-concentration heartbeat on the kotoba Datom log.
  ADR-2606022000.

  Each heartbeat: observe (OFFLINE merged/seed graph, G7 no live feed) → classify → analyze
  (aggregate concentration signal, G2 resilience+accountability not target-list) → PERSIST a
  content-addressed transaction (graph datoms + derived :supply/*, in CANONICAL sorted order so
  the CID is reproducible regardless of set-iteration order). Deterministic / resume-safe; no
  external I/O; live GLEIF/EDGAR push + social posting stay G7/G11-gated.

  Run:  bb --classpath 20-actors 20-actors/kabuto/methods/autorun.clj --cycles 3 --fresh"
  (:require [kabuto.methods.kabuto-edn :as e]
            [kabuto.methods.analyze :as a]
            [kabuto.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- data-dir [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile (io/file "data")))
(defn- merged [] (io/file (data-dir) "companies.merged.kotoba.edn"))
(defn- seed [] (io/file (data-dir) "seed-public-companies.kotoba.edn"))
(defn- default-log [] (io/file (data-dir) "kabuto.datoms.kotoba.edn"))
(def BASE-AS-OF 20260608)

(defn- graph-path [gp] (or gp (let [m (merged)] (if (.exists m) m (seed)))))

(defn run-cycle
  [cycle & {:keys [graph-path* log-path]}]
  (let [log-path (or log-path (default-log))
        rows (e/load-edn (graph-path graph-path*))
        g (e/classify rows)
        an (a/analyze (:companies g) (:edges g))
        datoms (k/canonical-order (concat (k/graph-datoms rows) (k/derived-datoms an)))
        tx (k/make-tx datoms :tx-id cycle :as-of (+ BASE-AS-OF cycle) :prev-cid (k/head-cid log-path))
        cid (k/append-tx tx log-path)
        top-systemic (if (seq (:systemic an)) (key (apply max-key val (:systemic an))) "—")]
    {:cycle cycle :companies (count (:companies g)) :edges (count (:edges g))
     :single-source (count (:single-source an)) :commodities (count (:commodity-hhi an))
     :top-systemic top-systemic :datoms (count datoms) :cid cid}))

(defn run-autonomous [& {:keys [cycles graph-path* log-path] :or {cycles 3}}]
  (let [log-path (or log-path (default-log))
        beats (mapv #(run-cycle % :graph-path* graph-path* :log-path log-path) (range 1 (inc cycles)))]
    {:cycles cycles :beats beats :log-length (count (k/read-log log-path))
     :head-cid (k/head-cid log-path) :chain (k/verify-chain log-path)}))

(defn -main [& argv]
  (let [args (vec argv)
        cyc-idx (.indexOf args "--cycles")
        cycles (if (>= cyc-idx 0) (Integer/parseInt (nth args (inc cyc-idx))) 3)
        log-idx (.indexOf args "--log")
        log-path (if (>= log-idx 0) (io/file (nth args (inc log-idx))) (default-log))]
    (when (and (some #{"--fresh"} args) (.exists (io/file log-path))) (.delete (io/file log-path)))
    (let [res (run-autonomous :cycles cycles :log-path log-path)]
      (println (str "# kabuto — AUTONOMOUS supply-chain concentration over the kotoba Datom log "
                    "(offline ingest, LOCAL persist; live GLEIF/EDGAR / posting stays G7/G11-gated)\n"))
      (doseq [bt (:beats res)]
        (println (format "  ♥ cycle %d: %d companies / %d edges · single-source %d · commodities %d (top systemic %s) +%d datoms → cid %s…"
                         (:cycle bt) (:companies bt) (:edges bt) (:single-source bt) (:commodities bt)
                         (:top-systemic bt) (:datoms bt) (subs (:cid bt) 0 14))))
      (let [ch (:chain res)]
        (println (format "\n  log: %d tx · head %s… · chain %s · resilience+accountability, never a target-list (G2)"
                         (:log-length res) (subs (:head-cid res) 0 14)
                         (if (:ok ch) "OK ✓" (str "BROKEN at " (:broken-at ch)))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
