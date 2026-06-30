(ns etzhayyim.actor-test
  "Tests for the kotoba-genome W3 shared actor runtime (ADR-2606302205 D3)."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [etzhayyim.actor :as actor]
            [etzhayyim.channel :as channel]))

(def decl
  {:handle "ooyake" :domain "world-government" :glyph "公"
   :voice-of "etzhayyim" :is-observatory true
   :lexicon-ns "com.etzhayyim.ooyake"
   :catalog [{:mechanism :ingest :base 1.0} {:mechanism :narrate :base 1.0}]
   :leash-ref "leash:cacao:ooyake" :persona "公 observatory" :subject "national legislatures"})

(deftest identity-is-present-only-leashed
  (let [a (actor/make-actor decl)
        id (actor/identity-of a)]
    (is (= :present-only (:did-key id)))            ; not platform-held / custodial
    (is (= "leash:cacao:ooyake" (:leash id)))       ; revocable off-switch
    (is (= "etzhayyim" (:voice-of id)))
    (is (str/starts-with? (:did id) "did:web:etzhayyim.com:actor:"))))

(deftest learning-is-inherited-from-genome
  (testing "learn! folds a real reading through the genome loop (beat increments)"
    (let [a  (actor/make-actor decl)
          a1 (actor/learn! a 100)
          a2 (actor/learn! a1 130)]
      (is (= 2 (get-in a2 [:state :beat])))
      (is (= :dry-run (get-in (actor/recommendation a2) [:status]))))))

(deftest post-emits-dry-run-with-disclosure
  (channel/default-registry!)
  (testing "an actor posts AS etzhayyim (voiceOf/isObservatory), dry-run via channel"
    (let [a (actor/make-actor decl)
          r (actor/post! a "app.bsky.feed.post" {:text "a public-record update"})]
      (is (true? (:emitted r)))
      (is (true? (:dry-run r)))
      (is (= "etzhayyim" (get-in r [:results :at-proto :record :voiceOf]))))))

(deftest gate-kit-floors-are-inherited
  (channel/default-registry!)
  (testing "person subject without consent is vetoed (person floor)"
    (let [a (actor/make-actor decl)
          r (actor/post! a "app.bsky.feed.post" {:text "x"} :person-subject? true :consent? false)]
      (is (false? (:emitted r)))
      (is (some #{:person/subject-without-consent} (get-in r [:scan :reasons]))))))

(deftest converse-is-disclosure-honest
  (testing "an actor responds, AS etzhayyim, never AS the real entity"
    (let [a (actor/make-actor decl)
          c (actor/converse a "What did the legislature decide?")]
      (is (false? (:blocked? c)))
      (is (= "etzhayyim" (:voice-of c)))
      (is (str/includes? (:reply c) "観測"))
      (is (str/includes? (:reply c) "なりすましではありません"))
      (is (= :template (:inference c))))))   ; Murakumo hook, fail-open template

(deftest summary-introspection
  (let [a (actor/learn! (actor/make-actor decl) 100)
        s (actor/summary a)]
    (is (= "world-government" (:domain s)))
    (is (= 1 (:beat s)))
    (is (= :present-only (get-in s [:identity :did-key])))))
