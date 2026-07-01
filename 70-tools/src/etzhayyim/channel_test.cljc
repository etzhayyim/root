(ns etzhayyim.channel-test
  "Tests for the kotoba-genome W1 Channel egress protocol (ADR-2606302205 D2/D4).
  Run: bb --classpath 70-tools/src -e \"(require 'etzhayyim.channel-test)
       (clojure.test/run-tests 'etzhayyim.channel-test)\""
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.channel :as ch]))

(def base
  {:actor "ooyake" :lexicon "app.bsky.feed.post"
   :content {:text "公 observatory: a public-record update." :chat-id 42 :subject "update"}
   :voice-of "etzhayyim" :is-observatory true
   :claims-to-be-entity false :person-subject? false :consent? false
   :dry-run true})

(deftest registry-and-routing
  (testing "default registry registers the five W1 drivers"
    (is (= #{:at-proto :email :telegram :x :line} (ch/default-registry!))))
  (testing "drivers-for routes by lexicon prefix"
    (ch/default-registry!)
    (is (= [:at-proto] (mapv ch/channel-id (ch/drivers-for {:lexicon "app.bsky.feed.post"}))))
    (is (= [:email]    (mapv ch/channel-id (ch/drivers-for {:lexicon "app.openmail.message"}))))
    (is (= [:telegram] (mapv ch/channel-id (ch/drivers-for {:lexicon "app.telegram.message"}))))
    (is (= [:x]        (mapv ch/channel-id (ch/drivers-for {:lexicon "app.x.tweet"}))))
    (is (= [:line]     (mapv ch/channel-id (ch/drivers-for {:lexicon "app.line.push"})))))
  (testing ":targets intersects with lexicon acceptance"
    (ch/default-registry!)
    ;; lexicon only matches at-proto, so telegram target yields nothing
    (is (empty? (ch/drivers-for {:lexicon "app.bsky.feed.post" :targets #{:telegram}})))))

(deftest x-and-line-drivers-carry-disclosure
  (ch/default-registry!)
  (testing "the X driver emits the v2 POST /tweets it would make, disclosure in-band"
    (let [r (ch/emit! (assoc base :lexicon "app.x.tweet"))]
      (is (true? (:emitted r)))
      (is (= [:x] (:channels r)))
      (is (= "/2/tweets" (get-in r [:results :x :api-call :path])))
      (is (= "etzhayyim" (get-in r [:results :x :disclosure :voiceOf])))
      (is (true? (get-in r [:results :x :disclosure :isObservatory])))))
  (testing "the LINE driver emits the Messaging API push it would make, disclosure in-band"
    (let [r (ch/emit! (assoc base :lexicon "app.line.push"
                             :content {:text "公 observatory update." :to "U123" :subject "u"}))]
      (is (true? (:emitted r)))
      (is (= [:line] (:channels r)))
      (is (= "/v2/bot/message/push" (get-in r [:results :line :api-call :path])))
      (is (= "text" (get-in r [:results :line :api-call :body :messages 0 :type])))
      (is (= "etzhayyim" (get-in r [:results :line :disclosure :voiceOf])))))
  (testing "the disclosure floor vetoes X/LINE just like every channel (impersonation)"
    (let [r (ch/emit! (assoc base :lexicon "app.x.tweet" :claims-to-be-entity true))]
      (is (false? (:emitted r)))
      (is (empty? (:results r))))))

(deftest valid-observatory-emit
  (ch/default-registry!)
  (testing "a disclosure-honest observatory post emits (dry-run) via at-proto"
    (let [r (ch/emit! base)]
      (is (true? (:emitted r)))
      (is (= :pass (get-in r [:scan :verdict])))
      (is (true? (:dry-run r)))
      (is (= [:at-proto] (:channels r)))
      (is (= "etzhayyim" (get-in r [:results :at-proto :record :voiceOf])))
      (is (true? (get-in r [:results :at-proto :record :isObservatory]))))))

(deftest disclosure-floor-vetoes-impersonation
  (ch/default-registry!)
  (testing "claiming to BE a real entity is vetoed — blocks ALL channels"
    (let [r (ch/emit! (assoc base :claims-to-be-entity true))]
      (is (false? (:emitted r)))
      (is (= :veto (get-in r [:scan :verdict])))
      (is (some #{:impersonation/claims-to-be-real-entity} (get-in r [:scan :reasons])))
      (is (empty? (:results r)))))
  (testing "observatory voice without voiceOf=etzhayyim is vetoed"
    (let [r (ch/emit! (assoc base :voice-of "toyota"))]
      (is (false? (:emitted r)))
      (is (some #{:disclosure/observatory-missing-voiceof-etzhayyim} (get-in r [:scan :reasons]))))))

(deftest person-floor-vetoes-unconsented-subject
  (ch/default-registry!)
  (testing "a private-person subject without consent is vetoed"
    (let [r (ch/emit! (assoc base :person-subject? true :consent? false))]
      (is (false? (:emitted r)))
      (is (some #{:person/subject-without-consent} (get-in r [:scan :reasons])))))
  (testing "person-targeting is vetoed"
    (let [r (ch/emit! (assoc base :targets-person? true))]
      (is (false? (:emitted r)))
      (is (some #{:person/targeting} (get-in r [:scan :reasons])))))
  (testing "consented person subject passes the person floor"
    (let [r (ch/emit! (assoc base :person-subject? true :consent? true))]
      (is (true? (:emitted r))))))

(deftest content-catastrophe-floor
  (testing "clean public-record content passes"
    (is (= :pass (:verdict (ch/content-scan "public record: the legislature passed the budget.")))))
  (testing "self-impersonation (first-person AS the entity) is vetoed"
    (is (= :veto (:verdict (ch/content-scan "私は政府です。"))))
    (is (some #{:content/self-impersonation} (:reasons (ch/content-scan "I am the government of X")))))
  (testing "targeted violence + CSAM are vetoed AND routed :non-aligned by the REAL ECL objective function (catastrophe term)"
    (is (= :veto (:verdict (ch/content-scan "kill them now"))))
    (let [csam (ch/content-scan "児童ポルノ")]
      (is (= :veto (:verdict csam)))
      (is (= :non-aligned (get-in csam [:ecl :route])))
      (is (= :catastrophe (get-in csam [:ecl :reason])))))
  (testing "emit! blocks catastrophe content on ALL channels (before egress)"
    (ch/default-registry!)
    (let [r (ch/emit! {:lexicon "app.bsky.feed.post" :content {:text "私は政府です"}
                            :voice-of "etzhayyim" :is-observatory true :targets #{:at-proto}})]
      (is (false? (:emitted r)))
      (is (some #{:content/self-impersonation} (get-in r [:scan :reasons]))))))

(deftest multi-channel-fanout
  (ch/default-registry!)
  (testing "one envelope fans out to multiple channels by lexicon+targets"
    ;; emit the same logical content to at-proto AND telegram via two envelopes
    ;; (each tagged with the channel's lexicon) — the registry routes each.
    (let [at  (ch/emit! base)
          tg  (ch/emit! (assoc base :lexicon "app.telegram.message"))]
      (is (= [:at-proto] (:channels at)))
      (is (= [:telegram] (:channels tg)))
      (is (every? #(true? (:dry-run %)) [(get-in at [:results :at-proto])
                                         (get-in tg [:results :telegram])]))
      (is (= "sendMessage" (get-in tg [:results :telegram :api-call :method]))))))
