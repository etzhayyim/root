;; etzhayyim.test-xrpc — xrpc request-shaping pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure base/url/request/response helpers (HTTP dispatch deferred):
;; resolve-base · build-xrpc-url · build-xrpc-request · parse-xrpc-response-body.
(ns etzhayyim.test-xrpc
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.xrpc :as x]))

(deftest resolve-base-priority
  (testing "explicit url wins and trailing slash is stripped"
    (is (= "https://u.example" (x/resolve-base "com.x" nil "https://u.example/" "https://pds"))))
  (testing "explicit app → app host template"
    (is (= "https://myid.com.etzhayyim.com" (x/resolve-base "com.x" "myid" nil "https://pds"))))
  (testing "NSID inference resolves a known apps slug"
    (is (= "https://q7v8yed1k.com.etzhayyim.com"
           (x/resolve-base "com.etzhayyim.apps.autorace.list" nil nil "https://pds"))))
  (testing "unknown slug / non-apps NSID falls back to the PDS url"
    (is (= "https://pds" (x/resolve-base "com.etzhayyim.apps.nosuchslug.x" nil nil "https://pds/")))
    (is (= "https://pds" (x/resolve-base "com.atproto.repo.get" nil nil "https://pds/")))))

(deftest build-xrpc-url-shape
  (is (= "https://base.example/xrpc/com.x" (x/build-xrpc-url "https://base.example" "com.x"))))

(deftest build-xrpc-request-shape
  (testing "GET with no payload → no body, content-type header"
    (let [r (x/build-xrpc-request "com.x" {:url "https://u"})]
      (is (= :get (:method r)))
      (is (= "https://u/xrpc/com.x" (:url r)))
      (is (= "application/json" (get-in r [:headers "Content-Type"])))
      (is (nil? (:body r)))))
  (testing "POST with payload → body + merged auth headers"
    (let [r (x/build-xrpc-request "com.x" {:url "https://u" :payload {"k" 1}
                                           :auth-headers {"Authorization" "Bearer t"}})]
      (is (= :post (:method r)))
      (is (= {"k" 1} (:body r)))
      (is (= "Bearer t" (get-in r [:headers "Authorization"])))))
  (testing "GET with a map payload → :params"
    (let [r (x/build-xrpc-request "com.x" {:url "https://u" :method :get :payload {"q" "1"}})]
      (is (= {"q" "1"} (:params r)))
      (is (nil? (:body r))))))

(deftest parse-xrpc-response-body-formatting
  (testing "pretty-print valid JSON → [pretty true]"
    (let [[s ok?] (x/parse-xrpc-response-body "{\"a\":1}" true)]
      (is (true? ok?))
      (is (re-find #"\"a\"" s))))
  (testing "pretty with invalid JSON → [raw false]"
    (is (= ["not json" false] (x/parse-xrpc-response-body "not json" true))))
  (testing "no pretty → [raw false]"
    (is (= ["raw" false] (x/parse-xrpc-response-body "raw" false)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-xrpc)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
