(ns covscan.scan-test
  (:require [clojure.test :refer [deftest is testing]]
            [babashka.fs :as fs]
            [covscan.scan :as scan]))

(deftest tested?-recognises-every-form
  (testing "all test forms used in the tree are detected"
    (doseq [p ["run_tests.sh" "run_tests.clj"
               "tests/foo.py" "test/foo.clj"
               "methods/test_analyze.cljc" "test_live.cljc" "test_foo.py"
               "src/etzhayyim/pds/server_test.clj" "foo_test.cljc" "x_test.py"
               "lib/widget_test.ts" "a_test.js"
               "src/Comp.test.ts" "src/Comp.test.tsx"]]
      (is (scan/tested? [p]) (str "should detect " p))))
  (testing "non-test paths are not misdetected"
    (doseq [p ["src/main.clj" "README.md" "methods/analyze.cljc"
               "src/contest.clj" "src/latest.ts" "data/seed.json"]]
      (is (not (scan/tested? [p])) (str "should NOT detect " p)))))

(deftest project-tested?-over-a-fixture
  (let [base (fs/create-temp-dir {:prefix "covscan"})]
    (try
      (let [tested-dir   (fs/create-dirs (fs/path base "with" "methods"))
            untested-dir (fs/create-dirs (fs/path base "without" "src"))]
        (spit (str (fs/path tested-dir "test_analyze.cljc")) "(ns x)")
        (spit (str (fs/path untested-dir "main.clj")) "(ns m)")
        (testing "a project with methods/test_*.cljc is tested"
          (is (true? (scan/project-tested? (fs/path base "with")))))
        (testing "a project with only src/main.clj is untested"
          (is (false? (scan/project-tested? (fs/path base "without")))))
        (testing "scan classifies both"
          (let [r (scan/scan (str base) [["with" "with"] ["without" "without"]])]
            ;; areas here are the project dirs themselves; each has 1 subdir
            (is (map? r))
            (is (= #{"with" "without"} (set (keys r)))))))
      (finally (fs/delete-tree base)))))
