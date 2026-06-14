#!/usr/bin/env bb
;; Working Clojure port of methods/autorun.py — the autonomous moving-craft heartbeat.
(ns watari.methods.autorun
  "autorun.clj — watari AUTONOMOUS moving-craft situational-awareness heartbeat on the kotoba
  Datom log. ADR-2606041827.

  Each heartbeat: observe (OFFLINE merged craft graph, G7 no live feed) → classify → analyze
  (aggregate lane/chokepoint situational signal, G2) → PERSIST a content-addressed transaction
  (graph datoms + derived :movement/*) to the append-only kotoba Datom log, linking the previous
  CID. Deterministic / resume-safe; no external I/O; live AIS/ADS-B feed + live-node push stay
  G7-gated. A craft is a craft, never a person (G4).

  Run:  bb --classpath 20-actors 20-actors/watari/methods/autorun.clj --cycles 3 --fresh"
  (:require [watari.methods.analyze :as a]
            [watari.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- data-dir [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile (io/file "data")))
(defn- merged [] (io/file (data-dir) "craft-graph.merged.kotoba.edn"))
(defn- seed [] (io/file (data-dir) "seed-craft-graph.kotoba.edn"))
(defn- default-log [] (io/file (data-dir) "watari.datoms.kotoba.edn"))
(def BASE-AS-OF 20260608)

(defn- graph-path [gp] (or gp (let [m (merged)] (if (.exists m) m (seed)))))

(defn run-cycle
  [cycle & {:keys [graph-path* log-path]}]
  (let [log-path (or log-path (default-log))
        rows (a/load-edn (graph-path graph-path*))
        g (a/classify rows)
        an (a/analyze g)
        datoms (vec (concat (k/graph-datoms rows) (k/derived-datoms g an)))
        tx (k/make-tx datoms :tx-id cycle :as-of (+ BASE-AS-OF cycle) :prev-cid (k/head-cid log-path))
        cid (k/append-tx tx log-path)
        top-choke (if (seq (:choke-transit an)) (key (apply max-key val (:choke-transit an))) "—")]
    {:cycle cycle :craft (count (:craft g)) :fixes (count (:fixes g)) :lanes (count (:lanes g))
     :chokepoints (count (:choke-transit an)) :top-chokepoint top-choke
     :stale (count (:stale an)) :datoms (count datoms) :cid cid}))

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
      (println (str "# watari — AUTONOMOUS moving-craft situational-awareness over the kotoba Datom log "
                    "(offline ingest, LOCAL persist; live AIS/ADS-B / live-node push stays G7-gated)\n"))
      (doseq [bt (:beats res)]
        (println (format "  ♥ cycle %d: %d craft / %d fixes / %d lanes · chokepoints %d (top %s) · stale %d +%d datoms → cid %s…"
                         (:cycle bt) (:craft bt) (:fixes bt) (:lanes bt) (:chokepoints bt)
                         (:top-chokepoint bt) (:stale bt) (:datoms bt) (subs (:cid bt) 0 14))))
      (let [ch (:chain res)]
        (println (format "\n  log: %d tx · head %s… · chain %s · situational-awareness, never surveillance (G2/G4)"
                         (:log-length res) (subs (:head-cid res) 0 14)
                         (if (:ok ch) "OK ✓" (str "BROKEN at " (:broken-at ch)))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
