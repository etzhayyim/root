(ns etzhayyim.registry.register-test
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.registry.agent :as ag]
            [etzhayyim.registry.register :as reg]
            [kotoba.datom :as kd]))

(deftest did-key-roundtrips
  (let [kp (ag/gen-keypair)
        did (ag/did-key kp)]
    (testing "did:key is the ed25519 multicodec form (z6Mk… prefix)"
      (is (re-find #"^did:key:z6Mk" did)))
    (testing "did:key decodes back to the raw 32-byte public key"
      (is (= (seq (ag/raw-pubkey kp)) (seq (ag/did-key->raw-pub did)))))))

(deftest agent-self-signs-its-genesis
  (let [m-kp (ag/gen-keypair)
        m-did (ag/did-key m-kp)
        doc (reg/author-genesis "busshi" m-kp m-did)
        {:keys [datoms cid author-sig]} (first (:chain doc))]
    (testing "content-address recomputes (kotoba commit-DAG integrity)"
      (is (= cid (kd/tx-cid datoms ""))))
    (testing "the agent's OWN key signed its genesis address"
      (is (ag/verify (:agent/did doc) cid author-sig)))
    (testing "the genesis carries a member CACAO vouch"
      (is (= m-did (get-in doc [:membrane :vouch :iss])))
      (is (= (:agent/did doc) (get-in doc [:membrane :vouch :aud]))))))

(deftest tamper-breaks-the-genesis
  (let [m-kp (ag/gen-keypair), m-did (ag/did-key m-kp)
        doc (reg/author-genesis "busshi" m-kp m-did)
        {:keys [datoms cid author-sig]} (first (:chain doc))
        tampered (assoc-in (vec datoms) [0 3] "EVIL")]
    (testing "a tampered datom no longer matches the content-address"
      (is (not= cid (kd/tx-cid tampered ""))))
    (testing "the self-signature does not verify against the tampered address"
      (is (not (ag/verify (:agent/did doc) (kd/tx-cid tampered "") author-sig))))))
