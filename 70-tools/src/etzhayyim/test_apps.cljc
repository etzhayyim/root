;; etzhayyim.test-apps — apps pure-helper invariants (cljc port).
;; Run: bb test:apps
;; Covers the pure scoring/extraction helpers (IO fns take an injectable :http-fn):
;; coverage-grade / kyumei-grade · tier-score · infer-app-name-from-collections ·
;; extract-sources-from-src.
(ns etzhayyim.test-apps
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.apps :as apps]))

(deftest coverage-grade-bands
  (is (= "S" (apps/coverage-grade 80)))
  (is (= "A" (apps/coverage-grade 60)))
  (is (= "B" (apps/coverage-grade 40)))
  (is (= "C" (apps/coverage-grade 20)))
  (is (= "D" (apps/coverage-grade 19)))
  (testing "kyumei-grade is an alias"
    (is (= (apps/coverage-grade 75) (apps/kyumei-grade 75)))))

(deftest tier-score-interpolation
  (testing "boundaries: ≤0 → 0, ≥hi → 100"
    (is (= 0.0 (apps/tier-score 0 1 5 10)))
    (is (= 100.0 (apps/tier-score 10 1 5 10)))
    (is (= 100.0 (apps/tier-score 99 1 5 10))))
  (testing "lo band [20,60): n=lo → 20, midpoint interpolates"
    (is (= 20.0 (apps/tier-score 1 1 5 10)))
    (is (= 40.0 (apps/tier-score 3 1 5 10))))   ;; 20 + 40*(3-1)/(5-1)
  (testing "mid band [60,100): n=mid → 60, interpolates upward"
    (is (= 60.0 (apps/tier-score 5 1 5 10)))
    (is (= 76.0 (apps/tier-score 7 1 5 10)))))  ;; 60 + 40*(7-5)/(10-5)

(deftest infer-app-name
  (testing "extracts <name> from com.etzhayyim.apps.<name>.*"
    (is (= "cargo" (apps/infer-app-name-from-collections
                    ["com.etzhayyim.apps.cargo.billOfLading"
                     "com.etzhayyim.apps.cargo.container"]))))
  (testing "non-matching collections → empty string"
    (is (= "" (apps/infer-app-name-from-collections ["app.bsky.feed.post"])))
    (is (= "" (apps/infer-app-name-from-collections [])))))

(deftest extract-sources
  (testing "sourceUrl / caseDbUrl / legislationUrl are pulled out"
    (is (= [{:url "https://a.example/x" :format "http" :category "external"}]
           (apps/extract-sources-from-src "const s = { sourceUrl: \"https://a.example/x\" };")))
    (is (= 2 (count (apps/extract-sources-from-src
                     "caseDbUrl: 'http://c.example' legislationUrl: \"https://l.example\"")))))
  (testing "no URLs → empty vector"
    (is (= [] (apps/extract-sources-from-src "no source urls here")))
    (is (= [] (apps/extract-sources-from-src nil))))
  (testing "result is capped at 20"
    (let [many (apply str (repeat 25 "sourceUrl: \"https://x.example/p\" "))]
      (is (= 20 (count (apps/extract-sources-from-src many)))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-apps)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
