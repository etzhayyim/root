(ns covscan.scan
  "Accurate, regenerable test-coverage signal across the monorepo.

  The committed `apps_maturity_report.csv` is a stale hand-maintained artifact
  with no generator and a crude `has_test` notion that misses the clj-native
  test forms actually used in the tree (e.g. `methods/test_*.cljc`, `run_tests*`).
  This bb-native scan recognises EVERY form — `tests/` · `test/` · `run_tests*` ·
  `methods/test_*.cljc` · `*_test.{clj,cljc,py,ts,js}` · `*.test.{ts,tsx}` ·
  `test_*.py` — and reports per-area coverage. clj/bb per the repo convention."
  (:require [babashka.fs :as fs]))

;; ── pure detector (the spec; unit-tested over path lists) ────────────────────
;; Matches every test form used in the tree, project-relative POSIX path:
;;   run_tests* · tests/ · test/ · __tests__/ · e2e/ · methods/test_*.cljc ·
;;   test_*.py · *_test.{clj,cljc,py,ts,js} · *.{test,spec}.{ts,tsx,js,jsx}
(def test-path-re
  #"(?i)(^|/)run_tests|(^|/)(tests?|__tests__|e2e)/|(^|/)test_[^/]*\.(cljc?|py)$|_test\.(cljc?|py|ts|js)$|\.(test|spec)\.(tsx?|jsx?)$")

(defn tested?
  "Pure predicate: do any of `paths` (project-relative, POSIX) indicate a test?"
  [paths]
  (boolean (some #(re-find test-path-re %) paths)))

;; ── fs application (bounded globs over source locations, skips vendor noise) ──
(defn project-tested?
  "Whether a project dir carries any test, by targeted globs (fast — never walks
  node_modules / build output)."
  [dir]
  (boolean
   (or (some #(fs/directory? (fs/path dir %)) ["tests" "test" "__tests__" "e2e"])
       (seq (fs/glob dir "run_tests*"))
       (seq (fs/glob dir "methods/test_*.cljc"))
       (seq (fs/glob dir "{test_*.py,*_test.clj,*_test.cljc,*_test.py}"))
       (seq (fs/glob dir (str "{src,lib,app,appview,worker,packages,test,tests,__tests__,e2e}/**/"
                              "{*_test.clj,*_test.cljc,*_test.py,*_test.ts,*_test.js,"
                              "*.test.ts,*.test.tsx,*.test.js,*.test.jsx,"
                              "*.spec.ts,*.spec.tsx,*.spec.js,*.spec.jsx}")
                     {:max-depth 8})))))

(defn scan
  "Classify the immediate subdirs of each `area` under `root`. Returns
  {area {:total n :tested n :untested [names]}}."
  [root areas]
  (into (sorted-map)
        (for [area areas
              :let [adir (fs/path root area)]
              :when (fs/exists? adir)]
          [area
           (let [projs (sort (filter fs/directory? (fs/list-dir adir)))
                 results (mapv (fn [p] [(str (fs/file-name p)) (project-tested? p)]) projs)]
             {:total (count results)
              :tested (count (filter second results))
              :untested (mapv first (remove second results))})])))

(defn -main [& args]
  (let [root (or (first args) ".")
        areas ["20-actors" "30-graph" "40-engine" "50-infra" "60-apps" "70-tools"]
        r (scan root areas)
        pct (fn [t n] (if (pos? n) (* 100.0 (/ (double t) n)) 0.0))]
    (doseq [[area {:keys [total tested untested]}] r]
      (println (format "%-10s  tested %4d / %4d  (%5.1f%%)   untested %d"
                       area tested total (pct tested total) (count untested))))
    (let [tot (reduce + (map (comp :total val) r))
          tst (reduce + (map (comp :tested val) r))]
      (println (format "%-10s  tested %4d / %4d  (%5.1f%%)" "TOTAL" tst tot (pct tst tot))))))
