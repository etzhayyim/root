(ns etzhayyim.observatory-submit-test
  "Tests for the W4-live member-principal publish gate (no-server-key, ibuki G7/G8)."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.channel :as channel]
            [etzhayyim.observatory-submit :as sub]))

(def prepared-actor
  {:handle "cable-marea" :subject "MAREA" :did "did:web:etzhayyim.com:actor:cable-marea"
   :voiceOf "etzhayyim" :isObservatory true
   :post {:status :prepared :requiresMemberSignature true :serverHeldKey false :published false}})

(def member-ctx
  {:cron? false :member-did "did:web:etzhayyim.com:founder"
   :sign-cmd "op item get leash --field sig" :publish-cmd nil})

(deftest agent-default-cannot-publish
  (channel/default-registry!)
  (testing "no member signer (the agent/default) → refused, never published"
    (let [g (sub/gate prepared-actor {:cron? false :member-did nil :sign-cmd nil} {:yes? true})]
      (is (false? (:ok g)))
      (is (= :member-signer-absent (:reason g))))))

(deftest cron-is-refused
  (testing "cron/agent context is refused even with a member signer + --yes (ibuki refuse_if_cron)"
    (let [g (sub/gate prepared-actor (assoc member-ctx :cron? true) {:yes? true})]
      (is (false? (:ok g)))
      (is (= :cron-refused (:reason g))))))

(deftest yes-is-required
  (testing "no --yes → refused"
    (let [g (sub/gate prepared-actor member-ctx {:yes? false})]
      (is (false? (:ok g)))
      (is (= :yes-required (:reason g))))))

(deftest server-held-key-forbidden
  (testing "a serverHeldKey post can never publish (no-server-key invariant)"
    (let [a (assoc-in prepared-actor [:post :serverHeldKey] true)
          g (sub/gate a member-ctx {:yes? true})]
      (is (false? (:ok g)))
      (is (= :server-held-key-forbidden (:reason g))))))

(deftest charter-scan-re-gates
  (channel/default-registry!)
  (testing "defence in depth — a non-disclosed (would-impersonate) post is vetoed at submit"
    (let [a (assoc prepared-actor :voiceOf "toyota")     ; observatory voice not etzhayyim
          g (sub/gate a member-ctx {:yes? true})]
      (is (false? (:ok g)))
      (is (= :charter-scan-veto (:reason g))))))

(deftest member-present-is-submit-ready
  (channel/default-registry!)
  (testing "member signer + --yes + non-cron + scan-pass → submit-ready, attributed to the member"
    (let [g (sub/gate prepared-actor member-ctx {:yes? true})]
      (is (true? (:ok g)))
      (is (= :ready (:reason g))))
    (let [[p] (sub/plan [prepared-actor] member-ctx {:yes? true})]
      (is (= :submit-ready (:decision p)))
      (is (= :submitted-by-member (get-in p [:receipt :status])))
      (is (= "did:web:etzhayyim.com:founder" (get-in p [:receipt :submittedByMember])))
      (is (false? (get-in p [:receipt :serverHeldKey]))))))

(deftest plan-mixes-ready-and-refused
  (channel/default-registry!)
  (testing "plan reports per-actor decisions"
    (let [bad (assoc-in prepared-actor [:post :status] :dry-run)   ; not prepared
          ps (sub/plan [prepared-actor bad] member-ctx {:yes? true})]
      (is (= :submit-ready (:decision (first ps))))
      (is (= :refused (:decision (second ps))))
      (is (= :not-prepared (:reason (second ps)))))))

(deftest member-context-reads-env-no-key
  (testing "member-context reads the member DID + cmd NAMES from env — never a key"
    (let [c (sub/member-context {"ETZHAYYIM_MEMBER_DID" "did:web:x" "IBUKI_CRON" "1"})]
      (is (true? (:cron? c)))
      (is (= "did:web:x" (:member-did c))))))
