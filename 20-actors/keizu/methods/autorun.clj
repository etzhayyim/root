#!/usr/bin/env bb
;; autorun.clj — 系図 (keizu) AUTONOMOUS government-power-relations heartbeat on the kotoba
;; Datom log. ADR-2606066000. Port of autorun.py.
;;
;; Each heartbeat the actor runs its whole power-relations pipeline ITSELF, no human in the loop:
;;   observe (load the OFFLINE relation-graph seed) → weave (validate every node / relation /
;;     committee / money / statement against the gates; raises on a violation)
;;   → concentration (aggregate, edge-primary: committee cross-organ, cross-committee seats,
;;     connector seats, money/payer HHI, revolving-door, award-and-fund co-occurrence,
;;     by-jurisdiction — all computed on read from edges/flows, never a per-person score)
;;   → PERSIST a content-addressed transaction to the append-only kotoba Datom log
;;     (graph datoms + derived :keizu.conc/* signals), linking the previous tx's CID.
;;
;; Constitutional posture holds by construction: an accountability MAP, never a target-list;
;; FACTUAL + non-adjudicating (revolving-door / award-and-fund datoms carry
;; `:keizu.conc/non-adjudicating true` — a co-occurrence of disclosed flows, NOT an allegation);
;; no-doxxing (PII node attrs unrepresentable, validated by weave); edge-primary (no per-person
;; score). The loop persists exactly what weave + concentration produced; derived flagged
;; :keizu.conc/derived.
;;
;; The loop is deterministic / resume-safe: canonical-order sorts datoms by canonical JSON before
;; hashing so the CID is reproducible across processes regardless of any set-iteration order inside
;; concentration (verified stable under PYTHONHASHSEED=random); EAVT is an unordered set, so order
;; carries no meaning. Append-only. WHAT STAYS GATED (G7/G8): no live ingest, no live-node push,
;; no live social posting. Stdlib only.
(ns keizu.methods.autorun
  (:require [keizu.methods.edn :as e]
            [keizu.methods.kotoba :as k]
            [keizu.methods.weave :as w]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)

(defn- data-dir []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile (io/file "data")))

(defn default-seed*
  "Public accessor for the default seed path (exposed for tests)."
  [] (io/file (data-dir) "seed-relation-graph.kotoba.edn"))

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
;; We build the sort key using the same json-val fn as kotoba.clj (private there) —
;; replicated here for the sort key only, matching json-val in kotoba.clj exactly
;; (ensure_ascii=False, separators=(",",":") i.e. NO spaces after separators).

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
  (json-val-sk* d))

(defn- canonical-order
  "Sort datoms by canonical JSON so the tx is DETERMINISTIC regardless of any set-iteration
  order inside concentration (PYTHONHASHSEED-randomized). EAVT is an unordered set, so a
  canonical sort makes the content-addressed CID reproducible / resume-safe.
  Mirrors autorun.py _canonical_order."
  [datoms]
  (sort-by datom-sort-key datoms))

;; ── one heartbeat cycle ────────────────────────────────────────────────────────

(defn run-cycle
  "One autonomous heartbeat: observe → weave (validate) → concentration → persist a
  content-addressed Datom transaction (graph + derived :keizu.conc/* signals). cycle drives
  tx-id + as-of. Mirrors autorun.py run_cycle."
  ([cycle] (run-cycle cycle (default-seed) (default-log)))
  ([cycle seed-path log-path]
   (let [g      (w/weave (e/load-edn seed-path))         ; observe + VALIDATE (raises on gate)
         c      (w/concentration g)                      ; aggregate, edge-primary (G4)
         datoms (vec (canonical-order
                      (concat (k/graph-datoms g)
                              (k/derived-datoms c))))    ; deterministic / resume-safe
         tx     (k/make-tx datoms
                            :tx-id    cycle
                            :as-of    (+ BASE-AS-OF cycle)
                            :prev-cid (k/head-cid log-path))
         cid    (k/append-tx tx log-path)]               ; PERSIST to append-only LOCAL kotoba log
     {:cycle      cycle
      :nodes      (get c "node_count")
      :rels       (get c "rel_count")
      :committees (get c "committee_count")
      :money      (get c "money_count")
      :money-hhi  (get (get c "money_concentration") "hhi")
      :revolving  (count (get c "revolving_door"))
      :award-fund (count (get c "award_and_fund"))
      :datoms     (count datoms)
      :cid        cid})))

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
      (println (str "# keizu (系図) — AUTONOMOUS government-power-relations over the kotoba Datom log "
                    "(offline seed, LOCAL persist; live ingest / posting stays G7/G8-gated)\n"))
      (doseq [b (:beats res)]
        (println (format "  ♥ cycle %d: %d nodes / %d rels / %d committees / %d money · money-HHI %s · revolving %d · award-fund %d +%d datoms → cid %s…"
                         (:cycle b) (:nodes b) (:rels b) (:committees b) (:money b)
                         (str (:money-hhi b))
                         (:revolving b) (:award-fund b)
                         (:datoms b) (subs (:cid b) 0 14))))
      (let [ch (:chain res)]
        (println (format "\n  log: %d tx · head %s… · chain %s · accountability map, never a target-list; edge-primary, non-adjudicating (G4)"
                         (:log-length res)
                         (subs (:head-cid res) 0 14)
                         (if (:ok ch) "OK ✓" (str "BROKEN at " (:broken-at ch)))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
