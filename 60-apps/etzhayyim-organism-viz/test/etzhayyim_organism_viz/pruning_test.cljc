(ns etzhayyim-organism-viz.pruning-test
  "Coverage for the pruning-candidate detector (盆栽 剪定 surface). Pure fns
  (candidate / round1 / to-markdown) + a tmp-dir fixture for the #?(:clj) FS
  scanners. The daemon NEVER prunes — these assert it SURFACES honestly."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [etzhayyim-organism-viz.pruning :as p]))

(deftest candidate-shape
  (testing "candidate builds the Python @dataclass-shaped, string-keyed map"
    (let [c (p/candidate "cell/x" "cell" "20-actors/x" 91.3 3 '("idle"))]
      (is (= {"id" "cell/x" "kind" "cell" "path" "20-actors/x"
              "idle_days" 91.3 "severity" 3 "reasons" ["idle"]} c))
      (is (vector? (get c "reasons")) "reasons is vectorised (asdict parity)")
      (is (= p/candidate-fields ["id" "kind" "path" "idle_days" "severity" "reasons"])))))

(deftest round1-half-even
  (testing "round1 matches Python round(x, 1) (1 decimal place)"
    (let [r1 #'etzhayyim-organism-viz.pruning/round1]   ;; private var
      (is (= 91.3 (r1 91.34)))
      (is (= 91.4 (r1 91.37)))
      (is (= 5.0 (r1 5.0)))
      (is (= 0.0 (r1 0.0)))
      (is (= 200.0 (r1 199.96))))))

(deftest to-markdown-rendering
  (testing "empty candidate list renders the honest 'no candidates' surface"
    (let [md (p/to-markdown "repo" [])]
      (is (str/includes? md "# Pruning Candidates"))
      (is (str/includes? md "Daemon does not prune"))
      (is (str/includes? md "healthy growth"))))
  (testing "candidates render as a severity-sorted table with the operator protocol"
    (let [c (p/candidate "cell/stale" "cell" "20-actors/stale" 120.5 3 ["idle 120 days (>90)" "no docstring"])
          md (p/to-markdown "repo" [c])]
      (is (str/includes? md "1 candidate(s)"))
      (is (str/includes? md "`cell/stale`"))
      (is (str/includes? md "`20-actors/stale`"))
      (is (str/includes? md "🔴🔴🔴"))                 ;; severity 3 → 3 dots
      (is (str/includes? md "git rm -r"))))) ;; operator pruning protocol present

#?(:clj
   (deftest scan-apps-surfaces-stale-app
     (testing "scan-apps flags a stale, README-less 60-apps dir (severity ≥ 1)"
       (let [tmp (str (java.nio.file.Files/createTempDirectory
                       "prune" (make-array java.nio.file.attribute.FileAttribute 0)))
             stale (java.io.File. ^String tmp "60-apps/etzhayyim-project-ghost")
             _ (.mkdirs stale)
             marker (java.io.File. stale "old.txt")
             _ (spit marker "x")
             ;; backdate the dir's newest file to ~200 days ago → idle > 180
             _ (.setLastModified marker (- (System/currentTimeMillis)
                                           (long (* 200 86400 1000))))
             cands (p/scan-apps tmp)
             ghost (first (filter #(= "app/etzhayyim-project-ghost" (get % "id")) cands))]
         (try
           (is (some? ghost) "the stale app is surfaced")
           (is (>= (get ghost "severity") 1))
           (is (str/includes? (str/join " " (get ghost "reasons")) "idle"))
           (is (some #(str/includes? % "README") (get ghost "reasons"))
               "README-less + stale is noted")
           (finally
             (doseq [f (reverse (file-seq (java.io.File. ^String tmp)))] (.delete f))))))))
