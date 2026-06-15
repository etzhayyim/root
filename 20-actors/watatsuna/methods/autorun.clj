#!/usr/bin/env bb
;; Working Clojure port of methods/autorun.py — the autonomous cable-resilience heartbeat.
(ns watatsuna.methods.autorun
  "autorun.clj — watatsuna AUTONOMOUS submarine-cable-resilience heartbeat on the kotoba Datom log.
  ADR-2606012600.

  Each heartbeat the actor runs its whole RESILIENCE pipeline itself, no human in the loop:
    observe (load the OFFLINE merged cable graph) → classify → analyze (chokepoint-load /
    redundancy-gap, aggregate-first, G2 RESILIENCE not interdiction) → PERSIST a content-addressed
    transaction (graph datoms + derived :resilience/*) to the append-only kotoba Datom log,
    linking the previous tx's CID.

  Deterministic / resume-safe (cycle drives tx-id + as-of → same CIDs) and append-only. WHAT
  STAYS GATED (G7): never a live TeleGeography/AIS/fault feed, never a live-node push. Ingest is
  the offline merged graph; persistence is the LOCAL append-only log.

  Run:  bb --classpath 20-actors 20-actors/watatsuna/methods/autorun.clj --cycles 3 --fresh"
  (:require [watatsuna.methods.analyze :as a]
            [watatsuna.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- data-dir [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile (io/file "data")))
(defn- merged [] (io/file (data-dir) "cable-graph.merged.kotoba.edn"))
(defn- seed [] (io/file (data-dir) "seed-cable-graph.kotoba.edn"))
(defn- default-log [] (io/file (data-dir) "watatsuna.datoms.kotoba.edn"))
(def BASE-AS-OF 20260608)

(defn- graph-path [gp] (or gp (let [m (merged)] (if (.exists m) m (seed)))))

(defn run-cycle
  "One autonomous heartbeat: observe → classify → analyze → persist a content-addressed Datom
  transaction (graph + derived :resilience/* signals). cycle drives tx-id + as-of."
  [cycle & {:keys [graph-path* log-path]}]
  (let [log-path (or log-path (default-log))
        rows (a/load-edn (graph-path graph-path*))     ; observe — OFFLINE graph (G7: no live feed)
        g (a/classify rows)
        an (a/analyze g)
        datoms (vec (concat (k/graph-datoms rows) (k/derived-datoms g an)))
        tx (k/make-tx datoms :tx-id cycle :as-of (+ BASE-AS-OF cycle) :prev-cid (k/head-cid log-path))
        cid (k/append-tx tx log-path)
        top-choke (if (seq (:choke-load an))
                    (key (apply max-key val (:choke-load an))) "—")]
    {:cycle cycle :cables (count (:cables g)) :stations (count (:stations g))
     :segments (count (:segs g)) :faults (count (:faults g))
     :chokepoints (count (:choke-load an)) :top-chokepoint top-choke
     :redundancy-gaps (count (:redundancy-gap an)) :datoms (count datoms) :cid cid}))

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
    (when (and (some #{"--fresh"} args) (.exists (io/file log-path)))
      (.delete (io/file log-path)))
    (let [res (run-autonomous :cycles cycles :log-path log-path)]
      (println (str "# watatsuna — AUTONOMOUS submarine-cable resilience over the kotoba Datom log "
                    "(offline ingest, LOCAL persist; live feed / live-node push stays G7-gated)\n"))
      (doseq [bt (:beats res)]
        (println (format "  ♥ cycle %d: %d cables / %d stations / %d segs / %d faults · chokepoints %d (top %s) · redundancy-gaps %d +%d datoms → cid %s…"
                         (:cycle bt) (:cables bt) (:stations bt) (:segments bt) (:faults bt)
                         (:chokepoints bt) (:top-chokepoint bt) (:redundancy-gaps bt) (:datoms bt)
                         (subs (:cid bt) 0 14))))
      (let [ch (:chain res)]
        (println (format "\n  log: %d tx · head %s… · chain %s · resilience map, never interdiction (G2)"
                         (:log-length res) (subs (:head-cid res) 0 14)
                         (if (:ok ch) "OK ✓" (str "BROKEN at " (:broken-at ch)))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
