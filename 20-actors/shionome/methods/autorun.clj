#!/usr/bin/env bb
;; autorun.clj — 潮目 (shionome) AUTONOMOUS heartbeat loop on the kotoba Datom log.
;; ADR-2606072200. Port of autorun.py.
;;
;; Each heartbeat the actor runs its whole pipeline ITSELF, with no human in the loop:
;;   observe (load public-source batch) → ingest + VALIDATE (G1/G2/G3, トレードはしない)
;;   → weave → aggregate concentration (edge-primary, G4)
;;   → draft DRY-RUN social posts (G5 mirror, G2 no-trade body scan)
;;   → PERSIST a content-addressed transaction to the append-only kotoba Datom log (G10)
;;
;; WHAT STAYS GATED (G8 / G7): this loop NEVER posts to an external network and NEVER
;; ingests from a live portal. Posts are dry-run; ingest is offline. Live external
;; publication + live market-data ingest are Council Lv6+ + operator + member-signature
;; gated. Autonomy here = the actor drives its own observe→analyze→persist cycle over
;; its own substrate, not that it speaks to the world unsupervised.
;;
;; Stdlib only. Deterministic (caller supplies cycle index → tx-id + as-of).
(ns shionome.methods.autorun
  (:require [shionome.methods.edn :as e]
            [shionome.methods.kotoba :as k]
            [shionome.methods.social :as s]
            [shionome.methods.weave :as w]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)

(defn- data-dir []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile (io/file "data")))

(defn- default-seed [] (io/file (data-dir) "seed-capital-flow-graph.kotoba.edn"))
(defn- default-log  [] (k/log-default))

(def BASE-AS-OF 20260607)

;; ── draft posts (mirrors autorun.py _draft_posts) ─────────────────────────────

(defn- draft-posts
  "Compose the three dry-run social posts from the concentration report.
  G2 no-trade guards are inside each social fn. Mirrors autorun.py _draft_posts."
  [g c]
  (let [allsrcs (sort (into #{} (mapcat #(get % ":flow/sources" []) (get g "flows"))))
        posts   (atom [])]
    (when (seq allsrcs)
      (when (seq (get c "net_flow_by_bucket"))
        (swap! posts conj (s/draft-netflow-post (get c "net_flow_by_bucket") allsrcs)))
      (when (seq (get c "rotation_pairs"))
        (swap! posts conj (s/draft-rotation-post (get c "rotation_pairs") allsrcs)))
      (swap! posts conj (s/draft-regime-post (get c "regime") allsrcs)))
    @posts))

;; ── one heartbeat cycle (mirrors autorun.py run_cycle) ───────────────────────

(defn run-cycle
  "One autonomous heartbeat: observe → validate → weave → analyze → dry-run post →
  persist a content-addressed Datom transaction. Returns a heartbeat summary.
  cycle drives tx-id + as-of (deterministic / resume-safe).
  Mirrors autorun.py run_cycle."
  ([cycle] (run-cycle cycle (default-seed) (default-log)))
  ([cycle seed-path log-path]
   (let [g      (w/weave (e/load-edn seed-path))           ; observe + VALIDATE (raises on gate)
         c      (w/concentration g)                         ; aggregate, edge-primary (G4)
         posts  (draft-posts g c)                           ; DRY-RUN, no-trade scanned (G2/G5)
         datoms (vec (concat (k/graph-datoms g)
                             (k/post-datoms posts (str "post-c" cycle))))
         tx     (k/make-tx datoms
                            :tx-id    cycle
                            :as-of    (+ BASE-AS-OF cycle)
                            :prev-cid (k/head-cid log-path))
         cid    (k/append-tx tx log-path)                   ; PERSIST to append-only log (G10)
         nbf    (get c "net_flow_by_bucket")
         top-inflow (if (seq nbf) (get (first nbf) "label") "—")]
     {:cycle     cycle
      :regime    (get (get c "regime") "regime")
      :top-inflow top-inflow
      :datoms    (count datoms)
      :posts     (count posts)
      :cid       cid})))

;; ── autonomous multi-cycle loop (mirrors autorun.py run_autonomous) ──────────

(defn run-autonomous
  "Drive `cycles` self-paced heartbeats. Each appends one content-addressed transaction
  to the kotoba Datom log. Returns the run summary + final head CID + chain verification.
  Mirrors autorun.py run_autonomous."
  ([] (run-autonomous 3 (default-seed) (default-log)))
  ([cycles] (run-autonomous cycles (default-seed) (default-log)))
  ([cycles seed-path log-path]
   (let [beats (mapv #(run-cycle % seed-path log-path) (range 1 (inc cycles)))]
     {:cycles     cycles
      :beats      beats
      :log-length (count (k/read-log log-path))
      :head-cid   (k/head-cid log-path)
      :chain      (k/verify-chain log-path)})))

;; ── CLI main (mirrors autorun.py argparse CLI) ────────────────────────────────

(defn -main [& argv]
  (let [args   (vec argv)
        cy-i   (.indexOf args "--cycles")
        cycles (if (>= cy-i 0) (Integer/parseInt (nth args (inc cy-i))) 3)
        log-i  (.indexOf args "--log")
        log-p  (if (>= log-i 0) (io/file (nth args (inc log-i))) (default-log))
        fresh? (some #{"--fresh"} args)]
    (when (and fresh? (.exists (io/file log-p)))
      (.delete (io/file log-p)))
    (let [res (run-autonomous cycles (default-seed) log-p)]
      (println (str "# 潮目 (shionome) — AUTONOMOUS run over the kotoba Datom log "
                    "(dry-run posts, offline ingest; live publish/ingest stays G8-gated)\n"))
      (doseq [b (:beats res)]
        (println (format "  ♥ cycle %d: regime=%-13s top-inflow=%-14s +%d datoms, %d dry-run posts → cid %s…"
                         (:cycle b) (:regime b) (:top-inflow b) (:datoms b) (:posts b)
                         (subs (:cid b) 0 14))))
      (let [ch (:chain res)]
        (println (format "\n  log: %d tx · head %s… · chain %s"
                         (:log-length res)
                         (subs (:head-cid res) 0 14)
                         (if (:ok ch) "OK ✓" (str "BROKEN at " (:broken-at ch)))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
