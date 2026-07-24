;; etzhayyim.test-dodaf — DoDAF pure-helper invariants (cljc port; module is IO-free).
;; Run: bb test:dodaf
;; Covers find-viewpoints · artifact-counts · build-tag-cond · build-path-cond ·
;; build-where · dodaf-id-from-title · dodaf-tags-for-file · deps-mv-name.
(ns etzhayyim.test-dodaf
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.dodaf :as dodaf]))

(deftest find-viewpoints-distinct
  (is (= ["AV-1" "OV-5"] (dodaf/find-viewpoints "see AV-1 and OV-5 and AV-1 again")))
  (is (= [] (dodaf/find-viewpoints "no codes here")))
  (is (= [] (dodaf/find-viewpoints nil))))

(deftest artifact-counts-by-type
  (is (= {"TV-1" 2 "AV-2" 1}
         (dodaf/artifact-counts [{:type "TV-1"} {:type "TV-1"} {:type "AV-2"}])))
  (is (= {} (dodaf/artifact-counts []))))

(deftest sql-where-builders
  (testing "tag condition (OR of list_contains, single-quote escaped)"
    (is (= "(list_contains(scope_tags, 'a') OR list_contains(scope_tags, 'b'))"
           (dodaf/build-tag-cond "scope_tags" ["a" "b"])))
    (is (= "" (dodaf/build-tag-cond "scope_tags" [])))
    (is (= "(list_contains(c, 'o''brien'))" (dodaf/build-tag-cond "c" ["o'brien"]))))
  (testing "path condition is skipped when col or path is blank"
    (is (= "" (dodaf/build-path-cond "" "x")))
    (is (= "" (dodaf/build-path-cond "f" "")))
    (is (str/includes? (dodaf/build-path-cond "scope_folders" "60-apps/x") "len(scope_folders)")))
  (testing "build-where joins present conditions with AND"
    (is (= "WHERE (list_contains(t, 'a'))" (dodaf/build-where "t" "" ["a"] "")))
    (is (= "" (dodaf/build-where "t" "" [] "")))
    (is (str/starts-with? (dodaf/build-where "t" "f" ["a"] "60-apps/x") "WHERE "))
    (is (str/includes? (dodaf/build-where "t" "f" ["a"] "60-apps/x") " AND "))))

(deftest dodaf-id-from-title-slug
  (testing "base = parent dir; title slugified"
    (is (= "foo-hello-world" (dodaf/dodaf-id-from-title "60-apps/foo/CLAUDE.md" "Hello World"))))
  (testing "single-segment path → base 'root'"
    (is (= "root-title" (dodaf/dodaf-id-from-title "CLAUDE.md" "Title"))))
  (testing "repeated hyphens collapse"
    (is (= "d-a-b" (dodaf/dodaf-id-from-title "x/d/CLAUDE.md" "A -- B")))))

(deftest dodaf-tags-for-file-inference
  (is (= ["claude" "docs" "at-protocol" "kotodama" "typescript"]
         (dodaf/dodaf-tags-for-file "60-apps/x/CLAUDE.md")))
  (is (= ["claude" "docs" "etzhayyim-cli" "tooling"]
         (dodaf/dodaf-tags-for-file "70-tools/y/CLAUDE.md")))
  (is (= ["claude" "docs" "root-policy"] (dodaf/dodaf-tags-for-file "CLAUDE.md"))))

(deftest deps-mv-name-extraction
  (is (= "my_view" (dodaf/deps-mv-name "CREATE MATERIALIZED VIEW IF NOT EXISTS my_view AS SELECT 1;")))
  (is (= "plain" (dodaf/deps-mv-name "CREATE MATERIALIZED VIEW plain AS SELECT 1")))
  (is (= "?" (dodaf/deps-mv-name "SELECT * FROM nope"))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-dodaf)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
