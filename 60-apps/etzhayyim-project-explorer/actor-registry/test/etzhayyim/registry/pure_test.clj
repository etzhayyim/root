(ns etzhayyim.registry.pure-test
  "Coverage for the registrar's pure branches: base58 round-trip, the kotoba-dht
   XOR neighbourhood, and the validator's content-address / self-sig warrants."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.registry.agent :as ag]
            [etzhayyim.registry.register :as reg]))

(deftest base58-roundtrips-with-leading-zeros
  (testing "encode→decode is identity, including leading zero bytes"
    (doseq [bs [(byte-array [1 2 3 4])
                (byte-array [0 0 5 (unchecked-byte 250)])   ; leading zeros + high byte
                (byte-array [(unchecked-byte 255)])]]
      (is (= (seq bs) (seq (ag/base58-decode (ag/base58-encode bs))))))))

(deftest base58-decode-rejects-invalid-characters
  ;; String.indexOf returns -1 (not an exception) for a character outside
  ;; the base58btc alphabet, and BigInteger/valueOf happily accepted -1 as
  ;; a valid digit -- an invalid character in an untrusted did:key string
  ;; used to silently decode to wrong-but-plausible key bytes instead of
  ;; raising. "0", "O", "I", "l" are excluded from base58btc specifically
  ;; to avoid visual ambiguity with "o"/"0"/"1"/"I".
  (testing "an invalid character throws instead of silently misdecoding"
    (doseq [bad ["0" "O" "I" "l"]]
      (is (thrown? Exception (ag/base58-decode bad))
          (str "must reject invalid base58btc character: " bad)))))

(deftest dht-replicas-deterministic-and-closest
  (let [vs (mapv (fn [_] (let [kp (ag/gen-keypair)]
                           {:validator-kp kp :validator-did (ag/did-key kp)}))
                 (range 4))
        cid (str "b" (apply str (repeat 64 "a")))]
    (testing "returns exactly r replicas, deterministically"
      (is (= reg/dht-r (count (reg/dht-replicas cid vs reg/dht-r))))
      (is (= (reg/dht-replicas cid vs reg/dht-r)
             (reg/dht-replicas cid vs reg/dht-r))))
    (testing "the replicas are the r XOR-closest of the validator node-ids"
      (is (every? (set (reg/dht-replicas cid vs (count vs)))
                  (reg/dht-replicas cid vs reg/dht-r))))))

(deftest validate-flags-tamper-and-bad-self-sig
  (let [m (let [kp (ag/gen-keypair)] {:kp kp :did (ag/did-key kp)})
        vkp (ag/gen-keypair)
        v {:validator-kp vkp :validator-did (ag/did-key vkp)
           :member-roster #{(:did m)}}
        agent (reg/author-genesis "busshi" (:kp m) (:did m))]
    (testing "a vouched, well-formed genesis is attested :valid"
      (is (= "valid" (:verdict (reg/validate (assoc v :seen-handles #{}) agent)))))
    (testing "tampered datoms (cid no longer matches) → bad-content-address"
      (let [bad (assoc-in agent [:chain 0 :datoms 0 3] "EVIL")
            verdict (reg/validate (assoc v :seen-handles #{}) bad)]
        ;; self-sig is over the original cid (still valid); the content-address
        ;; check is what fails
        (is (= "invalid" (:verdict verdict)))
        (is (= "bad-content-address" (:reason verdict)))))
    (testing "a broken self-signature → bad-self-sig"
      (let [bad (assoc-in agent [:chain 0 :author-sig] "AAAA")
            verdict (reg/validate (assoc v :seen-handles #{}) bad)]
        (is (= "bad-self-sig" (:reason verdict)))))))
