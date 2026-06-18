;; autorun.clj — danjo AUTONOMOUS public-accountability cross-reference heartbeat on the
;; kotoba Datom log.
;;
;; Clojure port of autorun.py (ADR-2605301600), Wave 1 of the clj-native migration
;; (ADR-2606142300) — the step that makes danjo's full pipeline clj-native (analyze + kotoba
;; already ported; this is the thin orchestrator over them). Each heartbeat the actor runs its
;; whole oversight pipeline ITSELF, with no human in the loop:
;;
;;   observe (load the OFFLINE pre-published procurement corpus + the OPEN method-pack)
;;     → run every IMPLEMENTED open detector (R0/R1: single-bidder-streak) → build
;;       danjo.discrepancyObservation records (G4 non-adjudicating / G5 ≥2 CIDs / G6 method-note)
;;     → PERSIST a content-addressed transaction to the append-only LOCAL kotoba Datom log
;;       (procurement-record graph datoms + derived observation datoms), linking the previous CID.
;;
;; Constitutional posture holds by construction: the censor's EYE, never the SWORD — only FACTUAL
;; observations are representable, NEVER a verdict (G4; derived-datoms RAISES on a verdict attr);
;; passive-only offline ingestion (G3 — re-fetches nothing); ≥2 source CIDs (G5) + method-note (G6).
;; Named-party publication stays G10 + 1 SBT = 1 vote gated — this loop persists to the LOCAL log
;; only, it publishes nothing.
;;
;; Deterministic / resume-safe: cycle drives tx-id + as-of (no wall clock); the detector iterates
;; in list order and graph-datoms emits in a canonicalized (sorted) order, so re-running the same
;; cycles reproduces the same CIDs. NOTE: because graph-datoms canonicalizes emission order
;; (kotoba.clj) rather than inheriting Python dict order, the COMBINED per-cycle tx CID is NOT
;; byte-identical with autorun.py — the clj log is internally self-consistent (the derived-only
;; observation tx remains byte-exact, see test_kotoba). stdlib + the sibling clj methods only.
(ns root.danjo.methods.autorun
  (:require [clojure.string :as str]))

(load-file "analyze.cljc")   ; canonical danjo analyze (ns danjo.methods.analyze); .clj dup removed
(load-file "kotoba.clj")
(alias 'an 'danjo.methods.analyze)
(alias 'ko 'root.danjo.methods.kotoba)

(def base-as-of 20260609)
(def default-corpus "../data/corpus.seed.json")
(def default-methods "v1-jp-seed.json")
(def default-log "../data/persisted/danjo.datoms.kotoba.edn")

(defn run-cycle
  "One autonomous heartbeat: observe corpus + open methods → run detectors → persist a
   content-addressed Datom transaction (procurement graph + discrepancy observations).
   `cycle` drives tx-id + as-of."
  [cycle {:keys [corpus-path methods-path log-path]
          :or {corpus-path default-corpus methods-path default-methods log-path default-log}}]
  (let [corpus       (an/load-json corpus-path)                 ; observe — OFFLINE corpus (G3)
        methods      (an/load-json methods-path)                ; the OPEN method-pack (G6)
        records      (get corpus "procurementRecords" [])
        observations (an/run-all corpus methods)                ; FACTUAL observations (G4)
        datoms       (into (ko/graph-datoms records) (ko/derived-datoms observations))
        tx           (ko/make-tx datoms {:tx-id cycle :as-of (+ base-as-of cycle)
                                         :prev-cid (ko/head-cid log-path)})
        cid          (ko/append-tx tx log-path)]                ; PERSIST to append-only LOCAL log
    {:cycle cycle :records (count records) :methods (count (get methods "methods" []))
     :observations (count observations) :datoms (count datoms) :cid cid}))

(defn run-autonomous
  ([cycles] (run-autonomous cycles {}))
  ([cycles {:keys [corpus-path methods-path log-path]
            :or {corpus-path default-corpus methods-path default-methods log-path default-log}
            :as opts}]
   (let [opts  (merge {:corpus-path corpus-path :methods-path methods-path :log-path log-path} opts)
         beats (mapv #(run-cycle % opts) (range 1 (inc cycles)))]
     {:cycles     cycles
      :beats      beats
      :log-length (count (ko/read-log log-path))
      :head-cid   (ko/head-cid log-path)
      :chain      (ko/verify-chain log-path)})))

(defn -main
  [& args]
  (let [argv   (vec args)
        idx    (fn [flag] (let [i (.indexOf argv flag)] (when (>= i 0) (nth argv (inc i)))))
        cycles (Integer/parseInt (or (idx "--cycles") "3"))
        corpus (or (idx "--corpus") default-corpus)
        meths  (or (idx "--methods") default-methods)
        log    (or (idx "--log") default-log)]
    (when (and (some #{"--fresh"} argv) (.exists (clojure.java.io/file log)))
      (.delete (clojure.java.io/file log)))
    (let [res (run-autonomous cycles {:corpus-path corpus :methods-path meths :log-path log})
          ch  (:chain res)]
      (println (str "# danjo — AUTONOMOUS public-accountability cross-reference over the kotoba "
                    "Datom log (offline corpus, LOCAL persist; live fetch / named-party publish "
                    "stays G3/G10-gated)\n"))
      (doseq [bt (:beats res)]
        (println (format "  ♥ cycle %d: %d procurement records / %d open methods → %d discrepancy observation(s) +%d datoms → cid %s…"
                         (:cycle bt) (:records bt) (:methods bt) (:observations bt) (:datoms bt)
                         (subs (:cid bt) 0 (min 14 (count (:cid bt)))))))
      (println (format "\n  log: %d tx · head %s… · chain %s · the censor's EYE, never the SWORD — non-adjudicating (G4)"
                       (:log-length res) (subs (:head-cid res) 0 (min 14 (count (:head-cid res))))
                       (if (:ok ch) "OK ✓" (str "BROKEN at " (:broken-at ch))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
