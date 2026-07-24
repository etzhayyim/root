(ns etzhayyim.observatory-test
  "Tests for the kotoba-genome W4 first-party observatory actors (ADR-2606302205 D4)."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [etzhayyim.observatory :as obs]
            [etzhayyim.actor :as actor]
            [etzhayyim.channel :as channel]))

(def toyota
  (obs/make-observatory {:ns "corp" :handle "corp-7203" :subject "Toyota Motor Corp" :glyph "兜"}))

(deftest first-party-not-keyless
  (testing "an observatory is a FIRST-PARTY self-keyed actor (not the keyless mirror)"
    (let [id (actor/identity-of toyota)]
      (is (= :present-only (:did-key id)))           ; keyed (present-only + leashed), not keyless
      (is (= "etzhayyim" (:voice-of id)))
      (is (str/includes? (:leash id) "observatory:corp-7203")))))

(deftest posts-grow-and-are-disclosure-honest
  (channel/default-registry!)
  (testing "an observatory POSTS (dry-run) AS etzhayyim, never AS the entity"
    (let [r (obs/observatory-post! toyota "FY filing disclosed: …")]
      (is (true? (:emitted r)))
      (is (true? (:dry-run r)))
      (is (= "etzhayyim" (get-in r [:results :at-proto :record :voiceOf])))
      (is (true? (get-in r [:results :at-proto :record :isObservatory]))))))

(deftest impersonation-and-person-floors-hold
  (channel/default-registry!)
  (testing "a private-person subject without consent is vetoed"
    (let [r (obs/observatory-post! toyota "about a named individual"
                                   :person-subject? true :consent? false)]
      (is (false? (:emitted r)))
      (is (some #{:person/subject-without-consent} (get-in r [:scan :reasons])))))
  (testing "consented person subject passes"
    (let [r (obs/observatory-post! toyota "about a consenting public official"
                                   :person-subject? true :consent? true)]
      (is (true? (:emitted r))))))

(deftest grows-by-learning-not-accumulating
  (channel/default-registry!)
  (testing "grow! runs a genome learning beat AND prepares a dry-run post"
    (let [g1 (obs/grow! toyota 10 "10 new public facts ingested")
          g2 (obs/grow! (:actor g1) 14 "4 more public facts")]
      (is (= 1 (get-in g1 [:actor :state :beat])))
      (is (= 2 (get-in g2 [:actor :state :beat])))
      (is (= :dry-run (get-in g2 [:recommendation :status])))
      (is (true? (get-in g2 [:post :emitted]))))))

(deftest can-be-conversed-with
  (testing "the dialogic-API surface the keyless mirror never had"
    (let [a (obs/ask toyota "Did they disclose Q3 results?")]
      (is (false? (:blocked? a)))
      (is (= "etzhayyim" (:voice-of a)))
      (is (str/includes? (:reply a) "Toyota Motor Corp"))
      (is (str/includes? (:reply a) "なりすましではありません")))))

(deftest mirror-migration-mapping
  (testing "keyless mirror handle → first-party observatory decl (W4 registry regen)"
    (let [m (obs/from-mirror-handle {:handle "gov-jp-kokkai" :ns "gov" :subject "国会" :glyph "公"})]
      (is (= :keyless-mirror (:was m)))
      (is (= :first-party-observatory (:now m)))
      (is (= :present-only-leashed (:key m)))
      (is (= "etzhayyim" (:voice-of m)))
      (is (true? (:is-observatory m))))))
