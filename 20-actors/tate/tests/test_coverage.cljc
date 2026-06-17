(ns tate.tests.test-coverage
  "tate 盾 — jurisdiction-coverage honesty tests (G10, ADR-2606112400).
  1:1 Clojure port of tests/test_coverage.py (stdlib asserts → clojure.test).

  test_manifest_jurisdictions_in_sync / test_claude_md_counts_in_sync read repo files
  (manifest.edn / CLAUDE.md) via the inlined EDN reader behind #?(:clj …), *file*-relative."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [clojure.set :as set]
            [tate.methods.terms-scan :as ts]
            [tate.methods.respond-plan :as rp]
            [tate.methods.coverage-report :as cr]))

(def CORE #{":jp" ":us" ":eu" ":uk" ":de"})

(deftest test-jurisdiction-registry-complete
  (let [juris (rp/load-jurisdictions)]
    (is (set/subset? CORE (set (keys juris))))
    (doseq [j (vals juris)]
      (is (get j ":juris/upl-anchor") (get j ":juris/id"))
      (is (and (get j ":juris/fake-help") (get j ":juris/referrals")) (get j ":juris/id"))
      (is (some #(str/includes? % "tasuke") (get j ":juris/fake-help")) (get j ":juris/id"))
      (is (get j ":juris/service-note") (get j ":juris/id"))
      (is (= (get j ":juris/verify-current-law") true))
      (is (= (get j ":juris/sourcing") ":representative"))
      (is (> (double (get j ":juris/refer-over-amount")) 0)))))

(deftest test-no-hollow-jurisdiction
  (let [cov (cr/coverage)]
    (doseq [j (get cov "jurisdictions")]
      (is (>= (get-in cov ["patterns_by_jurisdiction" j] 0) 1) (str j " has no clause patterns"))
      (is (>= (get-in cov ["procedures_by_jurisdiction" j] 0) 1) (str j " has no procedures")))))

(deftest test-coverage-ratio-honest
  (let [cov (cr/coverage)]
    (is (= (get cov "covered_count") (count (rp/load-jurisdictions))))
    (is (= (get cov "un_member_states") 193))
    (is (< (get cov "coverage_ratio") 0.25) "coverage must be reported as the small number it is")
    (is (>= (count (get cov "named_gaps")) 4))))

(deftest test-gap-list-never-stale
  (let [cov (cr/coverage)
        covered (set (get cov "jurisdictions"))
        gap-text (str/join " " (get cov "named_gaps"))]
    (doseq [j (get cov "worklist_remaining")]
      (is (not (contains? covered j)) (str j " is covered but still on the worklist")))
    (doseq [j covered]
      (is (not (str/includes? gap-text (str j " — 未収載"))) (str j " is covered but named as a gap")))))

(deftest test-us-states-registry
  (let [states (rp/load-us-states)]
    (is (= (count states) 50))
    (doseq [s (vals states)]
      (is (and (get s ":state/label") (get s ":state/answer-rule")) (get s ":state/id"))
      (is (get s ":state/answer-anchor") (get s ":state/id"))
      (is (> (double (get s ":state/small-claims-usd")) 0) (get s ":state/id"))
      (is (= (get s ":state/verify-current-law") true))
      (is (= (get s ":state/sourcing") ":representative")))
    (let [cov (cr/coverage)]
      (is (= (get cov "us_states_covered") (count states)))
      (is (= (get cov "us_states_total") 50))
      (is (some #(str/includes? % "全50州収載") (get cov "named_gaps"))))))

(deftest test-manifest-jurisdictions-in-sync
  (let [manifest (ts/read-edn (slurp (str (clojure.java.io/file ts/HERE "manifest.edn"))))
        declared (set (get manifest ":actor/jurisdictions"))
        actual (set (keys (rp/load-jurisdictions)))]
    (is (= declared actual) [(sort (set/difference declared actual)) (sort (set/difference actual declared))])))

(deftest test-civil-only-jurisdictions-named
  (let [cov (cr/coverage)
        co (get cov "civil_only_jurisdictions")]
    (is (= co []))
    (is (some #(str/includes? % "全管轄に専門トラックあり") (get cov "named_gaps")))))

(deftest test-critical-deadline-census
  (let [cov (cr/coverage)
        cds (get cov "critical_deadlines")
        ids (set (map #(get % "proc") cds))]
    (is (>= (count cds) 8))
    (is (set/subset? #{"proc:de-kuendigung" "proc:ch-zahlungsbefehl" "proc:au-unfair-dismissal"
                       "proc:it-licenziamento" "proc:es-despido"} ids))
    (is (str/includes? (cr/report cov) "Critical deadlines"))))

(deftest test-claude-md-counts-in-sync
  (let [md (slurp (str (clojure.java.io/file ts/HERE "CLAUDE.md")))
        m1 (re-find #"procedure registry \((\d+) procs" md)
        m2 (re-find #"clause registry \((\d+) shapes, (\d+) juris" md)]
    ;; (the `# N tests, pure stdlib` Python-test-count assertion was dropped in the
    ;; ADR-2606160842 py→clj prune wave — it counted `\ndef test_` across the now-pruned
    ;; Python test files. The registry-count guards below stay: they sync CLAUDE.md against
    ;; the .edn registries, which are not pruned.)
    (is (and m1 (= (Long/parseLong (nth m1 1)) (count (rp/load-procs)))) "CLAUDE.md proc count drift")
    (is (and m2 (= (Long/parseLong (nth m2 1)) (count (ts/load-patterns)))) "CLAUDE.md pattern count drift")
    (is (= (Long/parseLong (nth m2 2)) (count (rp/load-jurisdictions))) "CLAUDE.md juris count drift")))

(deftest test-protective-census
  (let [cov (cr/coverage)
        n (count (for [p (get cov "_procs")
                       o (get p ":proc/options" [])
                       :when (= (get o ":opt/protective") true)]
                   o))]
    (is (>= n 60))
    (is (str/includes? (cr/report cov) "protective options"))))

(deftest test-report-names-the-gap
  (let [text (cr/report (cr/coverage))]
    (is (or (str/includes? (str/lower-case text) "named gaps") (str/includes? text "Named gaps")))
    (is (str/includes? text ":unknown-jurisdiction"))
    (is (str/includes? text "193"))))

(deftest test-every-clause-pattern-exercised
  (let [[docs _] (ts/load-docs)
        patterns (ts/load-patterns)
        hit (set (map #(get % "clause") (get (ts/scan docs patterns) "flags")))
        missing (sort (for [p patterns :when (not (contains? hit (get p ":clause/id")))]
                        (get p ":clause/id")))]
    (is (empty? missing) (str "patterns with no exercising seed doc: " missing))))

(deftest test-every-procedure-exercised
  (let [[_ notices] (ts/load-docs)
        procs (rp/load-procs)
        exercised (set (for [p (rp/plans notices procs) :when (= (get p "status") ":genuine")]
                         (get p "proc")))
        missing (sort (for [p procs :when (not (contains? exercised (get p ":proc/id")))]
                        (get p ":proc/id")))]
    (is (empty? missing) (str "procedures with no genuine seed notice: " missing))))

(deftest test-registry-lint
  (let [patterns (ts/load-patterns)
        procs (rp/load-procs)
        pids (mapv #(get % ":clause/id") patterns)
        qids (mapv #(get % ":proc/id") procs)]
    (is (= (count pids) (count (set pids))) "duplicate clause ids")
    (is (= (count qids) (count (set qids))) "duplicate proc ids")
    (doseq [p patterns]
      (is (and (get p ":clause/keywords") (get p ":clause/anchor")) (get p ":clause/id")))
    (doseq [p procs]
      (is (get p ":proc/options") (get p ":proc/id"))
      (is (get p ":proc/deadline-rules") (get p ":proc/id"))
      (doseq [dl (get p ":proc/deadline-rules")]
        (is (get dl ":dl/anchor") [(get p ":proc/id") dl])
        (is (= (get dl ":dl/verify-service-date") true) [(get p ":proc/id") (get dl ":dl/label")]))
      (is (get p ":proc/genuine-channels") (get p ":proc/id"))
      (is (get p ":proc/refer-when") (get p ":proc/id"))
      (is (contains? #{":civil" ":labor" ":housing" ":enforcement" ":insolvency" ":family"}
                     (get p ":proc/track" ":civil")) (get p ":proc/id")))))

(deftest test-specialty-track-counted
  (let [cov (cr/coverage)]
    (is (>= (get-in cov ["procedure_tracks" ":labor"] 0) 3))
    (is (>= (get-in cov ["procedure_tracks" ":housing"] 0) 4))
    (is (>= (get-in cov ["procedure_tracks" ":enforcement"] 0) 3))
    (is (>= (get-in cov ["procedure_tracks" ":insolvency"] 0) 3))
    (is (>= (get-in cov ["procedure_tracks" ":family"] 0) 3))
    (is (>= (get-in cov ["procedure_tracks" ":civil"] 0) 20))
    (is (some #(and (str/includes? % "専門トラック") (str/includes? % "管轄横展開")) (get cov "named_gaps")))))

(deftest test-track-matrix
  (let [cov (cr/coverage)
        matrix (get cov "track_matrix")]
    (doseq [[track total] (get cov "procedure_tracks")]
      (is (= (reduce + (map #(get % track 0) (vals matrix))) total) track))
    (is (>= (count (filter #(pos? (get % ":labor" 0)) (vals matrix))) 6))
    (is (>= (count (filter #(pos? (get % ":housing" 0)) (vals matrix))) 6))
    (is (>= (count (filter #(pos? (get % ":enforcement" 0)) (vals matrix))) 5))
    (is (>= (count (filter #(pos? (get % ":insolvency" 0)) (vals matrix))) 5))
    (is (>= (count (filter #(pos? (get % ":family" 0)) (vals matrix))) 4))
    (is (str/includes? (cr/report cov) "Track × jurisdiction matrix"))))

#?(:clj (defn -main [& _] (run-tests 'tate.tests.test-coverage)))
