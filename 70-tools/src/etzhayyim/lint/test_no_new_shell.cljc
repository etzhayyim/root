#!/usr/bin/env bb
;; etzhayyim.lint.no-new-shell — gate tests.
;; Run:  bb --classpath 70-tools/src 70-tools/src/etzhayyim/lint/test_no_new_shell.cljc
(ns etzhayyim.lint.test-no-new-shell
  (:require [etzhayyim.lint.no-new-shell :as l]
            [clojure.test :refer [deftest is run-tests]]))

(deftest new-scripts-are-present-minus-baseline
  (is (= ["orgs/etzhayyim/com-etzhayyim-new/run_tests.sh"]
         (l/new-scripts ["orgs/etzhayyim/com-etzhayyim-a/run_tests.sh" "orgs/etzhayyim/com-etzhayyim-new/run_tests.sh"]
                        ["orgs/etzhayyim/com-etzhayyim-a/run_tests.sh"])))
  (is (= [] (l/new-scripts ["orgs/etzhayyim/com-etzhayyim-a/run_tests.sh"] ["orgs/etzhayyim/com-etzhayyim-a/run_tests.sh"]))))

(deftest removed-scripts-are-baseline-minus-present   ; baseline shrinks-only
  (is (= ["orgs/etzhayyim/com-etzhayyim-gone/run_tests.sh"]
         (l/removed-scripts ["orgs/etzhayyim/com-etzhayyim-a/run_tests.sh"]
                            ["orgs/etzhayyim/com-etzhayyim-a/run_tests.sh" "orgs/etzhayyim/com-etzhayyim-gone/run_tests.sh"]))))

(deftest the-live-baseline-has-no-violations   ; the committed baseline matches the tree
  (let [present (l/present-scripts "20-actors")
        baseline (clojure.edn/read-string
                  (slurp "70-tools/src/etzhayyim/lint/shell-baseline.edn"))]
    (is (empty? (l/new-scripts present baseline))
        "a new first-party .sh slipped in without a bb runner — author it in clj/bb")))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (let [{:keys [fail error]} (run-tests 'etzhayyim.lint.test-no-new-shell)]
       (System/exit (if (zero? (+ fail error)) 0 1)))))
