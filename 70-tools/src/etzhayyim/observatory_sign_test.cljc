(ns etzhayyim.observatory-sign-test
  "Tests for the W4-live kagi+kotoba-lang member-sign backend (ADR-2606302205 D4).
  Only the PURE parts + the lazy-dep guard are tested here — minting a real CACAO /
  publishing needs the member's Keychain key + the :member-publish deps alias
  (kagi-clj + langchain), which is the member's runtime, never the test/agent."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.observatory-sign :as sign]))

(deftest leash-request-is-datom-transact-revocable
  (testing "the leash is a datom:transact CACAO with a short TTL (the off-switch)"
    (let [r (sign/leash-request {:aud "did:web:node-operator" :graph "k51abc" :ttl-seconds 300})]
      (is (= :cap/transact (:cap r)))                 ; write capability
      (is (= "k51abc" (:scope r)))                    ; the member's graph
      (is (= "did:web:node-operator" (:aud r)))       ; aud = node operator DID
      (is (= 300 (:ttlSeconds r))))))                 ; revocable / short

(deftest post-record-is-disclosure-honest
  (testing "the record is AS etzhayyim's observatory, NEVER as the entity"
    (let [r (sign/post-record {:text "FY filing disclosed" :subject "Toyota Motor Corp"})]
      (is (= sign/post-lexicon (:$type r)))
      (is (= "etzhayyim" (:voiceOf r)))               ; not AS Toyota
      (is (true? (:isObservatory r)))
      (is (= "Toyota Motor Corp" (:subject r))))))

(deftest agent-path-cannot-mint-without-member-deps
  (testing "without the :member-publish alias (kagi-clj absent from the base classpath), minting the leash throws a clear hint — the agent never publishes"
    (is (thrown-with-msg? clojure.lang.ExceptionInfo
                          #"member-publish dependency unavailable"
                          (sign/mint-leash {:priv-b64 "x" :pub-b64 "y" :aud "did:web:node-operator"})))))
