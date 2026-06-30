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
  (testing "default registry registers the three W1 drivers"
    (is (= #{:at-proto :email :telegram} (ch/default-registry!))))
  (testing "drivers-for routes by lexicon prefix"
    (ch/default-registry!)
    (is (= [:at-proto] (mapv ch/channel-id (ch/drivers-for {:lexicon "app.bsky.feed.post"}))))
    (is (= [:email]    (mapv ch/channel-id (ch/drivers-for {:lexicon "app.openmail.message"}))))
    (is (= [:telegram] (mapv ch/channel-id (ch/drivers-for {:lexicon "app.telegram.message"})))))
  (testing ":targets intersects with lexicon acceptance"
    (ch/default-registry!)
    ;; lexicon only matches at-proto, so telegram target yields nothing
    (is (empty? (ch/drivers-for {:lexicon "app.bsky.feed.post" :targets #{:telegram}})))))

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
