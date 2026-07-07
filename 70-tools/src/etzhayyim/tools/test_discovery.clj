;; test_discovery.clj — etzhayyim.tools.discovery: the bb test:actors auto-discovery must only
;; pick up files whose DECLARED ns matches the path-derived ns (classpath-safe), skipping
;; run_tests_clj.sh-style suites (root.* ns + cwd-relative load-file). ADR-2606131500 + 2606142300.
(ns etzhayyim.tools.test-discovery
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.tools.discovery :as d]))

(deftest declared-ns-reads-the-ns-form
  (testing "declared-ns returns the ns a file actually declares (clj + cljc)"
    ;; the canonical danjo analyze test (.cljc) declares the path-matching ns
    (is (= 'danjo.methods.test-analyze
           (d/declared-ns "20-actors/danjo/methods/test_analyze.cljc")))
    ;; a run_tests_clj.sh-style suite declares a root.-prefixed ns (NOT the path-derived one)
    (is (= 'root.danjo.methods.test-ingest
           (d/declared-ns "20-actors/danjo/methods/test_ingest.clj")))
    (is (nil? (d/declared-ns "20-actors/danjo/methods/does-not-exist.clj")))))

(deftest discovery-only-classpath-safe-nss
  (testing "actor-test-nss includes path-matching tests, excludes path-mismatched (root.*) ones"
    (let [nss (set (d/actor-test-nss))]
      ;; the canonical .cljc test IS discovered (declares danjo.methods.test-analyze)
      (is (contains? nss 'danjo.methods.test-analyze))
      ;; the run_tests_clj.sh-owned suites are NOT (they'd crash a classpath require from root)
      (is (not (contains? nss 'danjo.methods.test-ingest)))
      (is (not (contains? nss 'danjo.methods.test-kotoba)))
      (is (not (contains? nss 'danjo.methods.test-revenue-ledger)))
      ;; mimamori/yobel/ibuki stay owned by their dedicated tasks (excluded? unchanged)
      (is (not-any? #(re-find #"^(mimamori|yobel|ibuki)\." (str %)) nss))
      ;; sanity: discovery still finds a healthy population of real tests
      (is (> (count nss) 100)))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'etzhayyim.tools.test-discovery)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
