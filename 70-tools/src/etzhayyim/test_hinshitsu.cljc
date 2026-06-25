;; etzhayyim.test-hinshitsu — hinshitsu quality-scoring pure invariants (cljc port).
;; Run: bb test:hinshitsu
;; Covers score-actor · grade · build-actor-report · fix-suggestions ·
;; diff-snap · diff-delta (filesystem/http legs deferred).
(ns etzhayyim.test-hinshitsu
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.hinshitsu :as q]))

(def complete {"name" "x" "did" "did:x" "performerType" "agent" "description" "d"})

(deftest score-actor-deductions
  (testing "a complete actor with no file/src signals scores 100"
    (is (= [100 []] (q/score-actor complete))))
  (testing "missing required fields deduct 5 each"
    (let [[score issues] (q/score-actor {})]
      (is (= 80 score))                         ;; 4 fields × -5
      (is (= 4 (count issues)))
      (is (every? #(re-find #"^missing_field:" %) issues))))
  (testing "nsid placeholder + hardcoded model deduct 10 each"
    (let [[score issues] (q/score-actor
                          (assoc complete "app_ts_content"
                                 "const n = \"nsid\"; const m = \"gpt-4o\";"))]
      (is (= 80 score))
      (is (some #{"nsid_placeholder"} issues))
      (is (some #{"hardcoded_model"} issues))))
  (testing "missing required files deduct 20 each (via existing_files set)"
    (let [[score issues] (q/score-actor (assoc complete "existing_files" ["kotodama.jsonld"]))]
      (is (= 60 score))                         ;; missing src/app.ts + wrangler.jsonc
      (is (some #{"missing:src/app.ts"} issues)))))

(deftest grade-bands
  (is (= "S" (q/grade 90)))
  (is (= "A" (q/grade 70)))
  (is (= "B" (q/grade 50)))
  (is (= "C" (q/grade 30)))
  (is (= "D" (q/grade 29))))

(deftest actor-report-shape
  (let [r (q/build-actor-report (assoc complete "nanoid" "n1"))]
    (is (= "n1" (get r "nanoid")))
    (is (= 100 (get r "score")))
    (is (= "S" (get r "grade")))
    (is (= [] (get r "issues")))))

(deftest fix-suggestions-mapping
  (is (= ["Create src/app.ts"] (q/fix-suggestions ["missing:src/app.ts"])))
  (is (= ["Add 'name' field to kotodama.jsonld"] (q/fix-suggestions ["missing_field:name"])))
  (is (re-find #"NSID" (first (q/fix-suggestions ["nsid_placeholder"]))))
  (is (re-find #"resolveModelId" (first (q/fix-suggestions ["hardcoded_model"]))))
  (is (= ["Fix: weird"] (q/fix-suggestions ["weird"]))))

(deftest diff-snap-and-delta
  (let [before (q/diff-snap ["d1" "d2"]
                            {"d1" {"did_doc_reachable" true}}
                            {"d1" {"total_score" 80}})
        after  (q/diff-snap ["d1" "d2"]
                            {"d1" {"did_doc_reachable" true} "d2" {"did_doc_reachable" true}}
                            {"d1" {"total_score" 80} "d2" {"total_score" 100}})]
    (testing "snapshot counts"
      (is (= 1 (:scan-count before)))
      (is (= 1 (:did-doc-reachable before)))
      (is (= 80.0 (:avg-total-score before)))
      (is (= 2 (:scan-count after)))
      (is (= 90.0 (:avg-total-score after))))
    (testing "delta = after − before"
      (let [d (q/diff-delta before after)]
        (is (= 1 (:scan-count d)))
        (is (= 1 (:did-doc-reachable d)))
        (is (= 10.0 (:avg-total-score d)))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-hinshitsu)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
