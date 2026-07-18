;; robotics-coverage maturity scorecard.
;;
;; Scans the robotics GAP-closure actors (and their siblings), reads each
;; manifest.edn + counts methods / gates / raising-safety-gates / deftests, and
;; emits a measurable R0→R1 maturity scorecard to MATURITY.md.
;;
;; This is the baseline the `/loop coverage, 成熟度を向上して` iterations improve
;; against — each maturity increment should move a cell of this table.
;;
;; Run: bb --classpath 20-actors 70-tools/robotics-coverage/maturity.clj
;; Per ADR-2606142000 (Clojure-first GAP-actor wave).
(ns robotics-coverage.maturity
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.java.io :as io]))

;; The robotics-coverage wave + the actors whose GAPs they close (ADR-2606073001).
(def actors
  [{:id "kuramori" :glyph "倉守" :occupation "倉庫 / 積み下ろし"        :adr "2606142000"}
   {:id "soma"     :glyph "杣"   :occupation "伐採 (logging)"          :adr "2606142010"}
   {:id "madomori" :glyph "窓守" :occupation "高所/façade window clean" :adr "2606142020"}
   {:id "kudamori" :glyph "管守" :occupation "下水道/confined-space"    :adr "2606142030"}])

(defn- slurp* [p] (when (.exists (io/file p)) (slurp p)))

(defn- count-re [s re] (if s (count (re-seq re s)) 0))

(defn scan-actor
  "Read one actor's manifest + test files; return a maturity row."
  [{:keys [id] :as a}]
  (let [base (str "orgs/etzhayyim/com-etzhayyim-" id)
        manifest (some-> (slurp* (str base "/manifest.edn")) edn/read-string)
        ;; test files: methods/test_<id>.clj
        test-src (slurp* (str base "/methods/test_" id ".clj"))
        ;; integration: does any method emit cross-actor :handoff/* chain edges?
        methods-src (apply str (map #(slurp* (str base "/methods/" % ".clj"))
                                    ["handoff" "datom_emit"]))
        analyze-src (slurp* (str base "/methods/analyze.clj"))
        gates (:actor/gates manifest)
        methods (:actor/methods manifest)
        ;; pipeline integration: fraction of DOMAIN methods (excl. analyze/datom_emit/
        ;; coverage) that analyze.clj actually requires (i.e. composes end-to-end)
        domain-methods (remove #(#{"analyze" "datom_emit" "coverage"} (:method/id %)) methods)
        wired (when analyze-src
                (count (filter #(re-find (re-pattern (str "methods\\." (clojure.string/replace (:method/id %) "_" "-")))
                                         analyze-src)
                               domain-methods)))
        ;; a "raising" safety gate = its rule mentions raise/refuse/unrepresentable
        raising (->> gates
                     (filter #(re-find #"(?i)raise|refus|unrepresentable|RAISES"
                                       (:gate/rule % "")))
                     count)]
    (assoc a
           :status (name (:actor/status manifest :unknown))
           :methods (count methods)
           :gates (count gates)
           :raising-gates raising
           :deftests (count-re test-src #"\(deftest ")
           :has-datom-emit (boolean (some #(= "datom_emit" (:method/id %)) methods))
           ;; does the emitter project the FULL run-day (complete canonical log) or just base run?
           :datom-day (boolean (let [d (slurp* (str base "/methods/datom_emit.clj"))]
                                 (and d (re-find #"emit-day|run-day" d))))
           :has-handoff (boolean (and methods-src (re-find #":handoff/" methods-src)))
           :has-coverage (.exists (io/file (str base "/methods/coverage.clj")))
           :pipeline-frac (when (and wired (pos? (count domain-methods)))
                            (/ (double wired) (count domain-methods)))
           ;; pull the ACTUAL occupation sub-task coverage fraction from the module
           :occ-coverage (try
                           (when-let [r (requiring-resolve
                                         (symbol (str id ".methods.coverage") "report"))]
                             (:coverage (r)))
                           (catch Throwable _ nil))
           :clojure (every? #(= :clojure (:method/lang %)) methods))))

(defn maturity-score
  "A simple 0..1 R0-maturity index per actor across 6 axes (each worth ~equal weight).
   Intentionally coarse — it tracks *direction* of improvement, not a precise grade."
  [{:keys [methods gates raising-gates deftests has-datom-emit datom-day has-handoff
           has-coverage pipeline-frac clojure]}]
  (let [axes [(min 1.0 (/ methods 5.0))        ; ≥5 methods = full
              (min 1.0 (/ gates 8.0))          ; ≥8 gates = full
              (min 1.0 (/ raising-gates 2.0))  ; ≥2 raising safety gates = full
              (min 1.0 (/ deftests 12.0))      ; ≥12 deftests = full
              (if has-datom-emit 1.0 0.0)
              (if datom-day 1.0 0.0)           ; canonical log captures the FULL day (R1)
              (if has-handoff 1.0 0.0)         ; cross-actor chain edges (R1 integration)
              (if has-coverage 1.0 0.0)        ; honest occupation sub-task coverage map
              (or pipeline-frac 0.0)           ; fraction of methods composed in analyze (R1)
              (if clojure 1.0 0.0)]]
    (/ (reduce + axes) (count axes))))

(defn render [rows]
  (let [hdr (str "# robotics-coverage — maturity scorecard\n\n"
                 "Generated by `70-tools/robotics-coverage/maturity.clj` (the "
                 "`/loop coverage, 成熟度を向上して` baseline). Closes the GAPs of "
                 "ADR-2606073001 §3/§4. **All R0** — score tracks R0-completeness + the "
                 "direction toward R1; it is NOT an R1 claim.\n\n"
                 "| Actor | Occupation | Status | methods | gates | raising | deftests | datom | day-log | handoff | occ-cov | pipeline | clj | score |\n"
                 "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        body (->> rows
                  (map (fn [r]
                         (format "| %s %s | %s | %s | %d | %d | %d | %d | %s | %s | %s | %s | %s | %s | %.2f |"
                                 (:id r) (:glyph r) (:occupation r) (:status r)
                                 (:methods r) (:gates r) (:raising-gates r) (:deftests r)
                                 (if (:has-datom-emit r) "✓" "✗")
                                 (if (:datom-day r) "✓" "✗")
                                 (if (:has-handoff r) "✓" "✗")
                                 (if (:occ-coverage r) (format "%.0f%%" (* 100.0 (:occ-coverage r))) "✗")
                                 (if (:pipeline-frac r) (format "%.0f%%" (* 100.0 (:pipeline-frac r))) "✗")
                                 (if (:clojure r) "✓" "✗")
                                 (maturity-score r))))
                  (str/join "\n"))
        total-tests (reduce + (map :deftests rows))
        avg (/ (reduce + (map maturity-score rows)) (count rows))
        occs (keep :occ-coverage rows)
        mean-occ (when (seq occs) (/ (reduce + occs) (count occs)))]
    (str hdr body "\n\n"
         (format "**Wave**: %d actors · %d deftests · mean R0-maturity %.2f%s.\n"
                 (count rows) total-tests avg
                 (if mean-occ
                   (format " · mean occupation-coverage %.0f%%%s" (* 100.0 mean-occ)
                           (if (>= mean-occ 1.0)
                             " (all named occupation sub-tasks now backed by a method — R1 is depth/fidelity + cell-runtime, not coverage)"
                             " (honest; sub-tasks still GAP are the real R1 worklist)"))
                   ""))
         "\n## Next maturity moves (R0→R1)\n"
         "- cell-runtime `.solve()` wiring (methods are pure; cells are manifest scaffold)\n"
         "- cross-actor handoff edges in the Datom log (niyaku→kuramori→todoke; kudamori→mizuho)\n"
         "- deeper sim: kuramori multi-pick consolidation + congestion replanning; soma stand-level harvest scheduling; madomori multi-face routing; kudamori network-wide cleaning campaign\n"
         "- per-actor `coverage.clj` (occupation sub-task coverage, honest gap list)\n")))

(defn -main [& _]
  (let [rows (map scan-actor actors)
        out "70-tools/robotics-coverage/MATURITY.md"]
    (spit out (render rows))
    (println (str "robotics-coverage maturity → " out))
    (doseq [r rows]
      (println (format "  %-10s score=%.2f (methods=%d gates=%d raising=%d tests=%d)"
                       (:id r) (maturity-score r) (:methods r) (:gates r)
                       (:raising-gates r) (:deftests r))))))

;; Run when invoked as a script (`bb --classpath 20-actors <this-file>`), matching
;; the actor test-file idiom (top-level invocation; bb does not auto-call -main).
(apply -main *command-line-args*)
