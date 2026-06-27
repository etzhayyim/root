;; etzhayyim.app-sdk.test-xrpc — shared SDK XRPC request-shaping invariants (bb/clj side).
;; The same .cljc compiles under squint for the app/edge side (ADR-2606251200 §Decision 4).
(ns etzhayyim.app-sdk.test-xrpc
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.app-sdk.xrpc :as x]))

(deftest endpoint-url
  (is (= "https://pds.example/xrpc/com.atproto.repo.getRecord"
         (x/xrpc-url "https://pds.example" "com.atproto.repo.getRecord")))
  (testing "one trailing slash on base is stripped"
    (is (= "https://pds.example/xrpc/com.x" (x/xrpc-url "https://pds.example/" "com.x")))))

(deftest auth-header-assembly
  (is (= {"Content-Type" "application/json" "Authorization" "Bearer tok"}
         (x/auth-headers "tok")))
  (testing "no token → no Authorization header"
    (is (= {"Content-Type" "application/json"} (x/auth-headers nil)))
    (is (= {"Content-Type" "application/json"} (x/auth-headers "")))))

(deftest query-request
  (testing "GET shape with default empty params"
    (let [r (x/query "https://p" "com.atproto.repo.listRecords" {:token "t"})]
      (is (= :get (:method r)))
      (is (= "https://p/xrpc/com.atproto.repo.listRecords" (:url r)))
      (is (= "Bearer t" (get-in r [:headers "Authorization"])))
      (is (= {} (:params r)))))
  (testing "params passed through"
    (is (= {"limit" "50"} (:params (x/query "https://p" "com.x" {:params {"limit" "50"}}))))))

(deftest procedure-request
  (testing "POST shape carries the body, no params"
    (let [r (x/procedure "https://p/" "com.atproto.repo.createRecord" {:token "t" :body {"x" 1}})]
      (is (= :post (:method r)))
      (is (= "https://p/xrpc/com.atproto.repo.createRecord" (:url r)))
      (is (= {"x" 1} (:body r)))
      (is (nil? (:params r)))))
  (testing "anonymous procedure (no token) omits Authorization"
    (is (nil? (get-in (x/procedure "https://p" "com.x" {:body {}}) [:headers "Authorization"])))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.app-sdk.test-xrpc)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
