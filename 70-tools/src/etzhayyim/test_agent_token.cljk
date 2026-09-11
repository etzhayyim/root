;; etzhayyim.test-agent-token — agent-token pure-helper invariants (cljc port, wave 5a).
;; Run: bb test:agent-token
;; Covers etzhayyim.agent-token build-agent-token-payload / agent-token-xrpc-url,
;; mirroring the Python agent_token.py payload assembly + endpoint building.
(ns etzhayyim.test-agent-token
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.agent-token :as at]))

(deftest payload-assembly
  (testing "2-arity: lxm + exp only"
    (is (= {"lxm" "com.etzhayyim.myLex" "exp" 1750000000}
           (at/build-agent-token-payload "com.etzhayyim.myLex" 1750000000))))
  (testing "aud is added when non-empty"
    (is (= {"lxm" "com.etzhayyim.myLex" "exp" 1750000000 "aud" "did:web:atproto.etzhayyim.com"}
           (at/build-agent-token-payload "com.etzhayyim.myLex" 1750000000
                                         "did:web:atproto.etzhayyim.com"))))
  (testing "nil / empty aud is omitted (no nil leakage into the JSON payload)"
    (is (= {"lxm" "x" "exp" 1} (at/build-agent-token-payload "x" 1 nil)))
    (is (= {"lxm" "x" "exp" 1} (at/build-agent-token-payload "x" 1 ""))))
  (testing "sub-did override is NOT part of the payload (it is an X-Active-DID header)"
    (is (= {"lxm" "x" "exp" 1}
           (at/build-agent-token-payload "x" 1 nil "did:web:other.etzhayyim.com")))))

(deftest xrpc-url-building
  (testing "the getServiceAuth path is appended"
    (is (= "https://pds.aozora.app/xrpc/com.atproto.server.getServiceAuth"
           (at/agent-token-xrpc-url "https://pds.aozora.app"))))
  (testing "trailing slashes are stripped (single and multiple)"
    (is (= "https://pds.aozora.app/xrpc/com.atproto.server.getServiceAuth"
           (at/agent-token-xrpc-url "https://pds.aozora.app/")))
    (is (= "https://pds.aozora.app/xrpc/com.atproto.server.getServiceAuth"
           (at/agent-token-xrpc-url "https://pds.aozora.app///"))))
  (testing "nil base yields just the path"
    (is (= "/xrpc/com.atproto.server.getServiceAuth"
           (at/agent-token-xrpc-url nil)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-agent-token)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
