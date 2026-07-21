;; test_discovery.clj — etzhayyim.tools.discovery: the bb test:actors auto-discovery must only
;; pick up files whose DECLARED ns matches the path-derived ns (classpath-safe), skipping
;; run_tests_clj.sh-style suites (root.* ns + cwd-relative load-file). ADR-2606131500 + 2606142300.
(ns etzhayyim.tools.test-discovery
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.tools.discovery :as d]))

(deftest declared-ns-reads-the-ns-form
  (testing "declared-ns returns the ns a file actually declares (clj + cljc)"
    (is (= 'etzhayyim.tools.test-discovery
           (d/declared-ns "70-tools/src/etzhayyim/tools/test_discovery.clj")))
    (is (nil? (d/declared-ns "70-tools/src/etzhayyim/tools/does-not-exist.clj")))))

(deftest discovery-only-classpath-safe-nss
  (testing "actor-test-nss includes path-matching tests, excludes path-mismatched (root.*) ones"
    (let [nss (set (d/actor-test-nss))]
      ;; mimamori/yobel/ibuki stay owned by their dedicated tasks (excluded? unchanged)
      (is (not-any? #(re-find #"^(mimamori|yobel|ibuki)\." (str %)) nss))
      ;; sanity: discovery still finds a healthy population of real tests
      (is (> (count nss) 100)))))

(deftest run-all-isolates-a-namespace-that-cannot-be-required
  (testing "a namespace that doesn't exist counts as one :error + one :load-failure, without
            aborting the namespaces around it (the ADR-2607071000 System/exit landmine class,
            generalized: one broken namespace must never silently truncate the whole sweep)"
    (let [r (d/run-all ['etzhayyim.test-manimani
                        'etzhayyim.tools.this-namespace-does-not-exist
                        'etzhayyim.test-bb-migration-cli])]
      (is (= 1 (count (:load-failures r))))
      (is (= 'etzhayyim.tools.this-namespace-does-not-exist (:ns (first (:load-failures r)))))
      (is (= :require (:phase (first (:load-failures r)))))
      ;; the two REAL namespaces either side of the broken one still ran and contributed
      ;; real assertions — proof the failure was isolated, not fatal to the whole call.
      (is (pos? (:test r)))
      (is (pos? (:pass r)))
      (is (pos? (:error r))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'etzhayyim.tools.test-discovery)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
