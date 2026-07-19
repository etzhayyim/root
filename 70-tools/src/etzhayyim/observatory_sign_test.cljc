(ns etzhayyim.observatory-sign-test
  "Tests for the W4-live kagi+kotoba-lang member-sign backend (ADR-2606302205 D4).
  Only the PURE parts + the lazy-dep guard are tested here — minting a real CACAO /
  publishing needs the member's Keychain key + member-publish.deps.edn
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

(deftest agent-path-cannot-mint-without-member-capabilities
  (testing "without a member-owned capability bundle, minting throws — the agent never publishes"
    (is (thrown-with-msg? clojure.lang.ExceptionInfo
                          #"member-publish capability unavailable"
                          (sign/mint-leash {:priv-b64 "x" :pub-b64 "y" :aud "did:web:node-operator"})))))

(deftest injected-member-runtime-wire-contract
  (testing "the portable flow only signs and publishes through explicit member capabilities"
    (let [wire (atom [])
          caps {:keychain-read (fn [actor] (swap! wire conj [:keychain actor]) "private")
                :public-key-from-private (fn [private]
                                           (swap! wire conj [:public private]) "public")
                :load-identity (fn [keys]
                                 (swap! wire conj [:identity keys])
                                 {:did "did:key:member" :graph "member-graph"})
                :mint-cacao (fn [identity capability facts]
                              (swap! wire conj [:mint identity capability facts])
                              "signed-leash")
                :nonce (constantly "fixed-nonce")
                :expiry (fn [ttl] (str "expiry+" ttl))
                :kotoba-conn (fn [endpoint graph auth]
                               (swap! wire conj [:conn endpoint graph auth])
                               :connection)
                :http-request (fn [& _] (throw (ex-info "unused raw HTTP" {})))
                :kotoba-api (fn [http-caps]
                              (swap! wire conj [:api http-caps])
                              {:transact! (fn [conn tx]
                                            (swap! wire conj [:transact conn tx])
                                            {:ok true})})}
          result (sign/sign-and-publish-with
                  caps "--actor" "member" "--aud" "did:web:operator"
                  "--ttl" "300" "--subject" "subject" "--text" "disclosure")]
      (is (= {:ok true} result))
      (is (some #{[:keychain "member"]} @wire))
      (is (some #(and (= :mint (first %))
                      (= "fixed-nonce" (get-in % [3 :nonce]))
                      (= "expiry+300" (get-in % [3 :expiry]))) @wire))
      (let [[_ conn tx] (first (filter #(= :transact (first %)) @wire))]
        (is (= :connection conn))
        (is (= "etzhayyim" (:voiceOf (first tx))) "observatory disclosure remains explicit")
        (is (true? (:isObservatory (first tx))))))))

(deftest dry-run-has-no-signing-or-network-authority
  (let [result (sign/sign-and-publish-with
                {} "--dry" "--actor" "member" "--aud" "did:web:operator"
                "--subject" "subject" "--text" "preview")]
    (is (true? (:dry result)))
    (is (false? (:member-key-present result)))
    (is (= "preview" (get-in result [:record :text])))))
