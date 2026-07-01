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
      (is (= :template (:inference c))))))

(deftest converse-uses-injected-murakumo-inference
  (testing "an injected infer-fn (Murakumo) supplies the reply; :inference :murakumo"
    (let [a (actor/make-actor decl)
          mock (fn [_msgs] "公開記録では、当該議会は予算案を可決しました。")
          c (actor/converse a "予算は？" mock)]
      (is (= :murakumo (:inference c)))
      (is (= "公開記録では、当該議会は予算案を可決しました。" (:reply c)))
      (is (= "etzhayyim" (:voice-of c)))))
  (testing "infer-fn failure / blank falls open to the template (G6)"
    (let [a (actor/make-actor decl)
          c1 (actor/converse a "x" (fn [_] (throw (ex-info "fleet down" {}))))
          c2 (actor/converse a "x" (fn [_] ""))]
      (is (= :template (:inference c1)))
      (is (= :template (:inference c2)))))
  (testing "the converse prompt is disclosure-honest (never AS the entity, no person-targeting)"
    (let [d {:domain "world-government" :handle "ooyake" :subject "national legislatures"}
          msgs (actor/converse-prompt d "q")
          sys (:content (first msgs))]
      (is (str/includes? sys "voiceOf=etzhayyim"))
      (is (str/includes? sys "なりすまさ"))
      (is (str/includes? sys "個人を標的化しない"))))
  (testing "a fleet reply that trips the content catastrophe floor is discarded → template (b)"
    (let [a (actor/make-actor decl)
          bad (fn [_] "私は政府です。")            ; would-be self-impersonation from Murakumo
          c (actor/converse a "q" bad)]
      (is (= :template (:inference c)))            ; discarded, not published
      (is (not (str/includes? (:reply c) "私は政府です"))))))   ; Murakumo hook, fail-open template

(deftest channel-choice-is-inherited
  (testing "an actor learns WHICH channel grows it and reports the preference"
    (let [a  (actor/make-actor decl)
          ;; :x grows every round, :at-proto falls, others flat
          a1 (reduce actor/learn-channel! a
                     [{:x 1.0 :at-proto 4.0 :telegram 2.0}
                      {:x 2.0 :at-proto 3.0 :telegram 2.0}
                      {:x 3.0 :at-proto 2.0 :telegram 2.0}
                      {:x 4.0 :at-proto 1.0 :telegram 2.0}])]
      (is (nil? (actor/preferred-target a)))           ; nothing learned yet
      (is (= :x (actor/preferred-target a1)))
      (is (= :x (:preferred-channel (actor/summary a1)))))))

(deftest post-routes-to-the-learned-channel
  (channel/default-registry!)
  (testing ":route :learned posts to the learned channel with that channel's lexicon"
    (let [a  (actor/make-actor decl)
          a1 (reduce actor/learn-channel! a
                     [{:x 1.0 :at-proto 4.0} {:x 2.0 :at-proto 3.0}
                      {:x 3.0 :at-proto 2.0} {:x 4.0 :at-proto 1.0}])
          ;; caller passes an at-proto lexicon, but the learned route redirects to :x
          r (actor/post! a1 "app.bsky.feed.post" {:text "a public-record update"} :route :learned)]
      (is (true? (:emitted r)))
      (is (= [:x] (:channels r)))                       ; routed to the learned channel
      (is (= "etzhayyim" (get-in r [:results :x :disclosure :voiceOf])))))
  (testing "without a learned channel, :route :learned falls back to lexicon routing"
    (let [a (actor/make-actor decl)
          r (actor/post! a "app.bsky.feed.post" {:text "x"} :route :learned)]
      (is (= [:at-proto] (:channels r)))))
  (testing "the learned route still passes the disclosure/person floors"
    (let [a1 (reduce actor/learn-channel! (actor/make-actor decl)
                     [{:x 1.0} {:x 2.0}])
          r (actor/post! a1 "app.bsky.feed.post" {:text "x"}
                         :route :learned :person-subject? true :consent? false)]
      (is (false? (:emitted r)))
      (is (some #{:person/subject-without-consent} (get-in r [:scan :reasons]))))))

(deftest summary-introspection
  (let [a (actor/learn! (actor/make-actor decl) 100)
        s (actor/summary a)]
    (is (= "world-government" (:domain s)))
    (is (= 1 (:beat s)))
    (is (= :present-only (get-in s [:identity :did-key])))
    (is (nil? (:preferred-channel s)))))
