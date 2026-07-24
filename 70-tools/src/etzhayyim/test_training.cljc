;; etzhayyim.test-training — training job request-shaping pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure helpers (XRPC dispatch deferred): build-auth-headers ·
;; parse-bench-list · validate-run-opts! · build-{list,get,run,promote,eval,list-runs}-request.
(ns etzhayyim.test-training
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.training :as tr]))

(deftest auth-headers-and-bench-list
  (is (= {"Authorization" "Bearer t" "Content-Type" "application/json"} (tr/build-auth-headers "t")))
  (testing "parse-bench-list trims, drops empties, handles nil"
    (is (= ["a" "b" "c"] (tr/parse-bench-list "a, b ,c")))
    (is (= ["x" "y"] (tr/parse-bench-list "x,, y")))
    (is (= [] (tr/parse-bench-list "")))
    (is (= [] (tr/parse-bench-list nil)))))

(deftest validate-run-opts
  (testing "dataset always required"
    (is (thrown? clojure.lang.ExceptionInfo (tr/validate-run-opts! {:kind "sft" :base-model "m"}))))
  (testing "sft/lora require base-model"
    (is (thrown? clojure.lang.ExceptionInfo (tr/validate-run-opts! {:kind "sft" :dataset "d"}))))
  (testing "distill requires student-base and teacher-kind"
    (is (thrown? clojure.lang.ExceptionInfo
                 (tr/validate-run-opts! {:kind "distill" :dataset "d" :teacher-kind "run"})))
    (is (thrown? clojure.lang.ExceptionInfo
                 (tr/validate-run-opts! {:kind "distill" :dataset "d" :student-base "s"}))))
  (testing "a complete sft spec validates (returns nil, no throw)"
    (is (nil? (tr/validate-run-opts! {:kind "sft" :dataset "d" :base-model "m"})))))

(deftest list-and-get-requests
  (testing "listJobs: optional status param, trailing slash stripped"
    (is (= {} (:params (tr/build-list-request {:pds-url "https://p/"}))))
    (is (= {"status" "running"} (:params (tr/build-list-request {:pds-url "https://p" :filter-status "running"})))))
  (is (= {"id" "j1"} (:params (tr/build-get-request {:pds-url "https://p" :job-id "j1"})))))

(deftest run-request-payload
  (testing "sft → runSft NSID + baseModel + default eval bench"
    (let [r (tr/build-run-request {:pds-url "https://p" :kind "sft" :dataset "ds" :base-model "bm"})]
      (is (= "https://p/xrpc/com.etzhayyim.apps.training.runSft" (:url r)))
      (is (= "ds" (get (:body r) "datasetName")))
      (is (= "bm" (get (:body r) "baseModel")))
      (is (= ["internal-loss"] (get (:body r) "evalBenches")))))
  (testing "distill → studentBaseModel + teacherKind + default distillMethod"
    (let [b (:body (tr/build-run-request {:pds-url "https://p" :kind "distill" :dataset "ds"
                                          :student-base "sb" :teacher-kind "run"}))]
      (is (= "sb" (get b "studentBaseModel")))
      (is (= "run" (get b "teacherKind")))
      (is (= "soft-logits" (get b "distillMethod")))))
  (testing "unknown kind throws"
    (is (thrown? clojure.lang.ExceptionInfo
                 (tr/build-run-request {:pds-url "https://p" :kind "wat" :dataset "d"})))))

(deftest eval-and-list-runs
  (testing "runEval defaults bench to internal-loss when nil"
    (is (= ["internal-loss"]
           (get (:body (tr/build-eval-request {:pds-url "p" :checkpoint-id "c"})) "benches"))))
  (testing "runEval with an explicitly empty bench throws"
    (is (thrown? clojure.lang.ExceptionInfo
                 (tr/build-eval-request {:pds-url "p" :checkpoint-id "c" :bench ""}))))
  (testing "listRuns limit defaults to 50"
    (is (= 50 (get (:body (tr/build-list-runs-request {:pds-url "p"})) "limit"))))
  (testing "promote: required checkpointId+alias, optionals omitted when blank"
    (is (= {"checkpointId" "c" "alias" "a"}
           (:body (tr/build-promote-request {:pds-url "p" :checkpoint-id "c" :alias "a"}))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-training)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
