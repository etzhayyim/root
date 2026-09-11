;; etzhayyim.app-sdk.test-record — shared SDK record-module invariants (bb/clj side).
;; The same .cljc compiles under squint for the app/edge side (ADR-2606251200 §Decision 4).
(ns etzhayyim.app-sdk.test-record
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.app-sdk.record :as r]))

(deftest nsid-syntax
  (testing "valid reverse-DNS NSIDs (≥3 segments)"
    (is (r/nsid? "com.etzhayyim.apps.cargo.profile"))
    (is (r/nsid? "app.bsky.feed.post"))
    (is (r/nsid? "com.atproto.repo")))                  ;; exactly 3 segments
  (testing "rejects too-few segments / bad starts / non-strings"
    (is (not (r/nsid? "com.etzhayyim")))                ;; only 2 segments
    (is (not (r/nsid? "Com.Etzhayyim.Apps")))           ;; uppercase
    (is (not (r/nsid? "1com.etzhayyim.apps")))          ;; leading digit
    (is (not (r/nsid? "")))
    (is (not (r/nsid? nil)))))

(deftest record-type-and-validity
  (is (= "app.bsky.feed.post" (r/record-type {"$type" "app.bsky.feed.post" "text" "hi"})))
  (is (nil? (r/record-type {"text" "hi"})))
  (is (nil? (r/record-type "not-a-map")))
  (testing "a valid record is a map with a valid NSID $type"
    (is (r/valid-record? {"$type" "com.etzhayyim.apps.cargo.profile" "x" 1}))
    (is (not (r/valid-record? {"text" "no type"})))      ;; missing $type
    (is (not (r/valid-record? {"$type" "bad"})))          ;; $type not an NSID
    (is (not (r/valid-record? "not-a-map")))))

(deftest at-uri-build-and-parse
  (is (= "at://did:web:x/com.x/rk1" (r/at-uri "did:web:x" "com.x" "rk1")))
  (testing "parse round-trips the components"
    (is (= {:did "did:web:x" :collection "app.bsky.feed.post" :rkey "rk1"}
           (r/parse-at-uri "at://did:web:x/app.bsky.feed.post/rk1")))
    (let [u (r/at-uri "did:plc:abc" "com.etzhayyim.apps.cargo.profile" "self")]
      (is (= "did:plc:abc" (:did (r/parse-at-uri u))))))
  (testing "non-at-uri / non-string → nil"
    (is (nil? (r/parse-at-uri "https://example.com")))
    (is (nil? (r/parse-at-uri "at://did/only-two")))
    (is (nil? (r/parse-at-uri nil)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.app-sdk.test-record)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
