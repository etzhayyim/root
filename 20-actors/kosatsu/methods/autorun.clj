#!/usr/bin/env bb
;; autorun.clj — 高札 (kosatsu) AUTONOMOUS crime/sanctions competing-claim heartbeat on the kotoba
;; Datom log. ADR-2606072000. Port of autorun.py.
;;
;; Each heartbeat the actor runs its whole competing-claim pipeline ITSELF, no human in the loop:
;;   observe (load the OFFLINE designation-graph seed) → weave (validate every authority / subject /
;;     designation against the gates; raises on a violation)
;;   → report (aggregate, politically-neutral: agreement index, per-subject divergence
;;     {contested | unanimous | single-asserter}, by-authority coverage, co-designation —
;;     every designation an ATTRIBUTED append-only event, asserter + as-of)
;;   → PERSIST a content-addressed transaction to the append-only kotoba Datom log
;;     (graph datoms + derived :kosatsu.div/* signals), linking the previous tx's CID.
;;
;; Constitutional posture holds by construction: etzhayyim authors NO designation (every designation
;; carries its own :asserter — a sovereign/body, never etzhayyim), NO verdict, NO per-subject score.
;; The computed divergence class makes "crime varies by political stance" a NEUTRAL fact.
;;
;; The loop is deterministic / resume-safe: _canonical-order sorts datoms by canonical JSON before
;; hashing so the CID is reproducible across processes regardless of any set-iteration order inside
;; report. Append-only. WHAT STAYS GATED (G7/G8): no live designation-list ingest, no live-node push,
;; no live posting. Stdlib only.
(ns kosatsu.methods.autorun
  (:require [kosatsu.methods.edn :as e]
            [kosatsu.methods.kotoba :as k]
            [kosatsu.methods.weave :as w]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)

(defn- data-dir []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile (io/file "data")))

(defn default-seed*
  "Public accessor for the default seed path (exposed for tests)."
  [] (io/file (data-dir) "seed-designation-graph.kotoba.edn"))

(defn- default-seed [] (default-seed*))
(defn- default-log  [] (k/log-default))

(def BASE-AS-OF 20260609)

;; ── canonical-order (determinism keystone) ────────────────────────────────────
;;
;; Mirrors autorun.py _canonical_order:
;;   sorted(datoms, key=lambda d: json.dumps(d, ensure_ascii=False, sort_keys=True))
;;
;; A datom is [op entity attr value] — a vector/list.
;; Python json.dumps of a list produces:  ["op", "entity", "attr", value]
;; sort_keys=True is irrelevant for lists (only affects dict keys inside), but we
;; replicate the exact JSON string so string ordering matches byte-for-byte.
;;
;; We build the sort key using kosatsu.methods.kotoba's json-val fn (private) — but
;; since that fn is private we replicate it here for the sort key only, matching the
;; json-val in kotoba.clj exactly (ensure_ascii=False, separators=(",",":")
;; i.e. NO spaces after separators).

(defn json-val-sk*
  "Serialize a single value to JSON for sort-key computation.
  Matches Python json.dumps with ensure_ascii=False, separators=(',',':').
  Public for test use (canonical-order sort key verification)."
  [v]
  (cond
    (nil? v)     "null"
    (boolean? v) (if v "true" "false")
    (instance? Long v)    (str v)
    (instance? Integer v) (str v)
    (and (number? v) (not (float? v)) (not (instance? Double v)))
    (str (long v))
    (or (float? v) (instance? Double v))
    (.toString (double v))
    (string? v)
    (str "\""
         (-> v
             (str/replace "\\" "\\\\")
             (str/replace "\"" "\\\"")
             (str/replace "\n" "\\n")
             (str/replace "\r" "\\r")
             (str/replace "\t" "\\t"))
         "\"")
    (or (sequential? v) (vector? v))
    (str "[" (str/join "," (map json-val-sk* v)) "]")
    :else (str "\"" (str v) "\"")))

(defn- datom-sort-key
  "Canonical JSON sort key for one datom (a vector [op entity attr value]).
  Matches: json.dumps(d, ensure_ascii=False, sort_keys=True)
  Since d is a list (not a dict), sort_keys has no effect; we just JSON-serialize the vector."
  [d]
  ;; json-val-sk* handles sequential/vector → builds [v0,v1,v2,v3] which is exactly what
  ;; Python json.dumps([...]) produces.
  (json-val-sk* d))

(defn- canonical-order
  "Sort datoms by canonical JSON so the tx is DETERMINISTIC regardless of any set-iteration
  order inside report (PYTHONHASHSEED-randomized). EAVT is an unordered set, so a canonical
  sort makes the content-addressed CID reproducible / resume-safe.
  Mirrors autorun.py _canonical_order."
  [datoms]
  (sort-by datom-sort-key datoms))

;; ── one heartbeat cycle ────────────────────────────────────────────────────────

(defn run-cycle
  "One autonomous heartbeat: observe → weave (validate) → report → persist a content-addressed
  Datom transaction (graph + derived :kosatsu.div/* signals). cycle drives tx-id + as-of.
  Mirrors autorun.py run_cycle."
  ([cycle] (run-cycle cycle (default-seed) (default-log)))
  ([cycle seed-path log-path]
   (let [g      (w/weave (e/load-edn seed-path))         ; observe + VALIDATE (raises on gate)
         r      (w/report g)                              ; aggregate, politically-neutral (G2/G4/G9)
         datoms (vec (canonical-order
                      (concat (k/graph-datoms g)
                              (k/derived-datoms r))))     ; deterministic / resume-safe
         tx     (k/make-tx datoms
                            :tx-id    cycle
                            :as-of    (+ BASE-AS-OF cycle)
                            :prev-cid (k/head-cid log-path))
         cid    (k/append-tx tx log-path)                 ; PERSIST to append-only LOCAL kotoba log
         ai     (get r "agreement_index")]
     {:cycle          cycle
      :authorities    (get r "authority_count")
      :subjects       (get r "subject_count")
      :designations   (get r "designation_count")
      :contested      (get ai "contested")
      :unanimous      (get ai "unanimous")
      :single-asserter (get ai "single_asserter")
      :datoms         (count datoms)
      :cid            cid})))

;; ── autonomous multi-cycle loop ───────────────────────────────────────────────

(defn run-autonomous
  "Drive `cycles` self-paced heartbeats. Each appends one content-addressed transaction to
  the kotoba Datom log. Returns the run summary + final head CID + chain verification.
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

;; ── CLI main ──────────────────────────────────────────────────────────────────

(defn -main [& argv]
  (let [args   (vec argv)
        cy-i   (.indexOf args "--cycles")
        cycles (if (>= cy-i 0) (Integer/parseInt (nth args (inc cy-i))) 3)
        seed-i (.indexOf args "--seed")
        seed-p (if (>= seed-i 0) (io/file (nth args (inc seed-i))) (default-seed))
        log-i  (.indexOf args "--log")
        log-p  (if (>= log-i 0) (io/file (nth args (inc log-i))) (default-log))
        fresh? (some #{"--fresh"} args)]
    (when (and fresh? (.exists (io/file log-p)))
      (.delete (io/file log-p)))
    (let [res (run-autonomous cycles seed-p log-p)]
      (println (str "# kosatsu (高札) — AUTONOMOUS competing-claim over the kotoba Datom log "
                    "(offline seed, LOCAL persist; live ingest / posting stays G7/G8-gated)\n"))
      (doseq [b (:beats res)]
        (println (format "  ♥ cycle %d: %d authorities / %d subjects / %d designations · contested %d · unanimous %d · single-asserter %d +%d datoms → cid %s…"
                         (:cycle b) (:authorities b) (:subjects b) (:designations b)
                         (:contested b) (:unanimous b) (:single-asserter b)
                         (:datoms b) (subs (:cid b) 0 14))))
      (let [ch (:chain res)]
        (println (format "\n  log: %d tx · head %s… · chain %s · every designation ATTRIBUTED; no designation/verdict/score authored by etzhayyim (G2/G4)"
                         (:log-length res)
                         (subs (:head-cid res) 0 14)
                         (if (:ok ch) "OK ✓" (str "BROKEN at " (:broken-at ch)))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
