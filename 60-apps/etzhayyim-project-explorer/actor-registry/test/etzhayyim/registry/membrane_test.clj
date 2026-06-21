(ns etzhayyim.registry.membrane-test
  "The validating membrane: CACAO member vouch (Sybil boundary), witness quorum,
   and warrant-on-violation."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.registry.agent :as ag]
            [etzhayyim.registry.register :as reg]))

(defn- mk-member [] (let [kp (ag/gen-keypair)] {:kp kp :did (ag/did-key kp)}))
(defn- mk-validator [] (let [kp (ag/gen-keypair)] {:validator-kp kp :validator-did (ag/did-key kp)}))

(deftest vouched-agent-passes-quorum
  (let [m (mk-member)
        vs (vec (repeatedly 3 mk-validator))
        roster #{(:did m)}
        a (reg/author-genesis "busshi" (:kp m) (:did m))
        doc (reg/run-membrane a vs roster #{} vs)]
    (testing "every validator attests a well-formed, vouched genesis"
      (is (= 3 (count (get-in doc [:membrane :attestations]))))
      (is (empty? (get-in doc [:membrane :warrants])))
      (is (get-in doc [:membrane :quorum :met?])))
    (testing "the entry is DHT-replicated to r neighbours"
      (is (= reg/dht-r (count (get-in doc [:dht :replicas])))))))

(deftest unvouched-agent-rejected-sybil-boundary
  (let [vs (vec (repeatedly 3 mk-validator))
        a (reg/author-genesis "rogue" nil nil)         ; no member vouch
        doc (reg/run-membrane a vs #{} #{} vs)]
    (testing "no member vouch → every validator issues a warrant, quorum fails"
      (is (not (get-in doc [:membrane :quorum :met?])))
      (is (= 3 (count (get-in doc [:membrane :warrants]))))
      (is (every? #(= "no-member-vouch" (:reason %)) (get-in doc [:membrane :warrants]))))))

(deftest duplicate-handle-rejected
  (let [m (mk-member)
        vs (vec (repeatedly 3 mk-validator))
        a (reg/author-genesis "busshi" (:kp m) (:did m))
        doc (reg/run-membrane a vs #{(:did m)} #{"busshi"} vs)]   ; handle already seen
    (testing "a taken handle is warranted, quorum fails"
      (is (not (get-in doc [:membrane :quorum :met?])))
      (is (every? #(= "duplicate-handle" (:reason %)) (get-in doc [:membrane :warrants]))))))

(deftest vouch-by-non-member-rejected
  (let [real (mk-member)
        impostor (mk-member)                            ; has a key, but NOT in the roster
        vs (vec (repeatedly 3 mk-validator))
        a (reg/author-genesis "busshi" (:kp impostor) (:did impostor))
        doc (reg/run-membrane a vs #{(:did real)} #{} vs)]
    (testing "a vouch from a non-roster key does not satisfy the membrane"
      (is (not (get-in doc [:membrane :quorum :met?])))
      (is (every? #(= "no-member-vouch" (:reason %)) (get-in doc [:membrane :warrants]))))))
