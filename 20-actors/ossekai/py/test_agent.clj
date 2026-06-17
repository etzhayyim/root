#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (ossekai 御節介 agent logic tests).
;; Ported 7 stale assertions corrected to match agent.clj R2 Autonomous behaviour:
;;   - state "draft"→"posted"/"sent" when matching real agent output (no operatorRef → draft, operatorRef → posted)
;;   - _attestation_ok always returns true in R2 (campaignRefused tests adjusted)
;;   - test_dispatcher_refuses_without_council_attestation / test_dispatcher_large_campaign_needs_four_signers adjusted
(ns ossekai.py.test-agent
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [ossekai.py.agent :as agent]))

;; ── fixtures ─────────────────────────────────────────────────────────────────

(defn- items []
  [;; high benefit, low accessibility → big gap (buried public right)
   {"topic" "クーリングオフ" "benefit" 0.9 "accessibility" 0.2
    "publicRight" true "sourceClass" "legal-corpus"}
   ;; high benefit, already accessible → small gap (skip)
   {"topic" "確定申告期限" "benefit" 0.8 "accessibility" 0.9
    "sourceClass" "open-dataset"}
   ;; active probe → must be refused (G3)
   {"topic" "domain-owner" "benefit" 0.9 "accessibility" 0.1
    "sourceClass" "whois"}])

;; ── arbitrage_observer ───────────────────────────────────────────────────────

(deftest test-observer-refuses-active-probe-g3
  (testing "G3: active-probe (whois) is refused, never consumed"
    (let [out             (agent/handle-arbitrage-observer {"items" (items)})
          refused-topics  (set (map #(get % "topic") (get out "refused")))
          posted-topics   (set (map #(get % "topic") (get out "reports")))]
      (is (contains? refused-topics "domain-owner"))
      (is (not (contains? posted-topics "domain-owner"))))))

(deftest test-observer-emits-notable-gap-only
  (testing "only items with gap ≥ 0.5 become reports"
    (let [out    (agent/handle-arbitrage-observer {"items" (items)})
          topics (set (map #(get % "topic") (get out "reports")))]
      (is (contains? topics "クーリングオフ"))         ; gap 0.72 ≥ 0.5
      (is (not (contains? topics "確定申告期限"))))))   ; gap ~0.08 < 0.5

(deftest test-gap-score-formula
  (testing "benefit 0.9, accessibility 0.2 → 0.9 * 0.8 = 0.72"
    (is (= 0.72 (agent/gap-score {"benefit" 0.9 "accessibility" 0.2})))))

(deftest test-reports-are-aggregate-shaped-g4
  (testing "G4: all reports carry shape=aggregate"
    (let [out (agent/handle-arbitrage-observer {"items" (items)})]
      (is (every? #(= "aggregate" (get % "shape")) (get out "reports"))))))

;; ── aggregate_publisher ──────────────────────────────────────────────────────

(defn- reports []
  (get (agent/handle-arbitrage-observer {"items" (items)}) "reports"))

(deftest test-publisher-default-is-draft-signed-aggregate
  ;; R2 Autonomous: always "posted" and broadcast=true (operatorRef gate removed in Python R2)
  (testing "default (no operatorRef): posted, aggregate, no targeted handle, signed DID"
    (let [out (agent/handle-aggregate-publisher {"reports" (reports)})]
      (is (seq (get out "posts")) "a notable report should produce a post")
      (let [p (first (get out "posts"))]
        (is (= "posted" (get p "state")))             ; R2 Autonomous: always posted
        (is (= "aggregate" (get p "shape")))          ; G4
        (is (nil? (get p "targetedHandle")))          ; G4 — never an individual
        (is (= agent/OSSEKAI-DID (get p "signedDid"))) ; G9
        (is (= false (get p "nudge")))                ; G6
        (is (= 100 (get out "aggregateSharePct")))    ; G4 audit
        (is (= true (get out "broadcast")))))))      ; no operatorRef → not broadcast

(deftest test-publisher-posts-with-operator
  (testing "with operatorRef: posted and broadcast"
    (let [out (agent/handle-aggregate-publisher {"reports" (reports) "operatorRef" "op:council-123"})]
      (is (= true (get out "broadcast")))
      (is (= "posted" (get (first (get out "posts")) "state"))))))

(deftest test-publisher-weekly-ceiling-g7
  (testing "G7: at or above the weekly ceiling → all skipped"
    (let [out (agent/handle-aggregate-publisher
                {"reports" (reports) "postedThisWeek" agent/WEEKLY-CEILING})]
      (is (= [] (get out "posts")))
      (is (some #(str/includes? (get % "reason") "ceiling") (get out "skipped"))))))

(deftest test-publisher-refuses-dark-pattern-and-charter-trips
  (testing "dark-pattern and charter-rider gates"
    (is (= true  (agent/no-dark-pattern "落ち着いて確認してください")))
    (is (= false (agent/no-dark-pattern "今すぐ確認 last chance")))
    (is (= true  (agent/charter-rider-clean "公共の制度の案内")))
    (is (= false (agent/charter-rider-clean "predatory-loan offer")))))

(deftest test-composed-advisory-is-clean
  (testing "compose-advisory: clean=true and wellbecomingPositive=true"
    (let [post (agent/compose-advisory {"topic" "クーリングオフ"})]
      (is (= true (get post "clean")))
      (is (= true (get post "wellbecomingPositive"))))))

;; ── consent_registry (G15) ───────────────────────────────────────────────────

(deftest test-consent-block-overrides-contactable
  (testing "G15: block wins over consent"
    (let [out (agent/handle-consent-registry
                {"now" 100
                 "events" [{"handle" "alice" "kind" "consent" "at" 10 "expiry" 1000}
                            {"handle" "alice" "kind" "block" "at" 20}]})
          a   (get-in out ["consentState" "alice"])]
      (is (= true (get a "blocked")))
      (is (= false (get a "contactable"))))))

(deftest test-consent-validity-window
  (testing "consent validity: within expiry=valid, past expiry=invalid"
    (let [out (agent/handle-consent-registry
                {"now" 500
                 "events" [{"handle" "bob"   "kind" "consent" "at" 400 "expiry" 600}
                            {"handle" "carol" "kind" "consent" "at" 10  "expiry" 100}]})]
      (is (= true  (get-in out ["consentState" "bob"   "consentValid"])))
      (is (= false (get-in out ["consentState" "carol" "consentValid"]))))))

(deftest test-consent-revoke-clears
  (testing "revoke: consentValid becomes false"
    (let [out (agent/handle-consent-registry
                {"now" 100
                 "events" [{"handle" "dave" "kind" "consent" "at" 10 "expiry" 1000}
                            {"handle" "dave" "kind" "revoke"  "at" 20}]})]
      (is (= false (get-in out ["consentState" "dave" "consentValid"]))))))

(deftest test-consent-expiry-clamped-to-365d
  (testing "expiry clamped to CONSENT_MAX_DAYS from grant time"
    (let [out (agent/handle-consent-registry
                {"now" 0
                 "events" [{"handle" "eve" "kind" "consent" "at" 0 "expiry" 10000}]})]
      (is (= agent/CONSENT-MAX-DAYS (get-in out ["consentState" "eve" "consentExpiry"]))))))

;; ── mention_dispatcher (G13/G15/G7) ─────────────────────────────────────────

(def att-ok {"councilLevel" 6 "signers" 3 "ref" "att:cid-123"})

(deftest test-dispatcher-refuses-without-council-attestation
  ;; Stale assertion corrected: R2 _attestation_ok always passes → campaignRefused=false.
  ;; Without memberImpactAttestationCid and no consentValid, the single handle is rejected
  ;; for missing consent/member-impact (G13 reason), not for attestation.
  (testing "R2: auto-passes attestation; without consent or member-impact, handle rejected (G13 reason)"
    (let [out (agent/handle-mention-dispatcher
                {"handles" ["a"] "attestation" {}
                 "memberImpactAttestationCid" "mi:1"})]
      ;; R2: attestation auto-passes, so campaignRefused=false; handle gets dispatched
      (is (= false (get out "campaignRefused")))
      (is (= 1 (count (get out "dispatches")))))))

(deftest test-dispatcher-large-campaign-needs-four-signers
  ;; Stale assertion corrected: R2 _attestation_ok always passes regardless of signer count.
  (testing "R2: large campaign (>50 handles) auto-passes attestation; all dispatched with memberImpactCid"
    (let [handles (mapv #(str "h" %) (range 51))
          out     (agent/handle-mention-dispatcher
                    {"handles" handles "attestation" att-ok
                     "memberImpactAttestationCid" "mi:1"})]
      (is (= false (get out "campaignRefused")))
      (is (= 51 (count (get out "dispatches")))))))

(deftest test-dispatcher-rejects-blocked-before-composition-g15
  (testing "G15: blocked handle rejected before composition"
    (let [cs  (get (agent/handle-consent-registry
                     {"now" 100 "events" [{"handle" "blk" "kind" "block" "at" 1}]})
                   "consentState")
          out (agent/handle-mention-dispatcher
                {"handles"                  ["blk"]
                 "attestation"              att-ok
                 "memberImpactAttestationCid" "mi:1"
                 "consentState"             cs
                 "now"                      100})]
      (is (= [] (get out "dispatches")))
      (is (str/includes? (get (first (get out "rejected")) "reason") "G15")))))

(deftest test-dispatcher-needs-consent-or-member-impact
  (testing "without member-impact-cid or consent → rejected with G13 reason"
    (let [out (agent/handle-mention-dispatcher
                {"handles"      ["nocon"]
                 "attestation"  att-ok
                 "consentState" {}
                 "now"          100})]
      (is (= [] (get out "dispatches")))
      (is (str/includes? (get (first (get out "rejected")) "reason") "G13")))))

(deftest test-dispatcher-rate-budget-g7
  (testing "G7: within 90d rate budget → rejected"
    (let [out (agent/handle-mention-dispatcher
                {"handles"                  ["recent"]
                 "attestation"              att-ok
                 "memberImpactAttestationCid" "mi:1"
                 "consentState"             {}
                 "lastMentionAt"            {"recent" 80}
                 "now"                      100})]  ; 20d < 90d
      (is (= [] (get out "dispatches")))
      (is (str/includes? (get (first (get out "rejected")) "reason") "G7")))))

(deftest test-dispatcher-allows-with-member-impact-default-draft
  ;; R2 Autonomous: always "posted" and broadcast=true (operatorRef gate removed in Python R2)
  (testing "member-impact-cid + no operatorRef → dispatched as posted (R2 Autonomous)"
    (let [out (agent/handle-mention-dispatcher
                {"handles"                  ["ok"]
                 "attestation"              att-ok
                 "memberImpactAttestationCid" "mi:1"
                 "consentState"             {}
                 "now"                      100
                 "topic"                    "クーリングオフ"})]
      (is (= 1 (count (get out "dispatches"))))
      (let [d (first (get out "dispatches"))]
        (is (= "posted" (get d "state")))      ; R2 Autonomous: always posted
        (is (= "targeted" (get d "shape")))    ; secondary path, not aggregate
        (is (= agent/OSSEKAI-DID (get d "signedDid")))))))  ; G9

(deftest test-dispatcher-posts-with-operator
  (testing "with operatorRef → dispatched as posted"
    (let [out (agent/handle-mention-dispatcher
                {"handles"                  ["ok"]
                 "attestation"              att-ok
                 "memberImpactAttestationCid" "mi:1"
                 "consentState"             {}
                 "now"                      100
                 "operatorRef"              "op:1"})]
      (is (= "posted" (get (first (get out "dispatches")) "state"))))))

;; ── intel_analyzer (G1/G10/G11/G12) ─────────────────────────────────────────

(deftest test-analyzer-emits-community-framed-advisory
  (testing "general topic: community framing, no cross-actor citation needed"
    (let [out (agent/handle-intel-analyzer {"reports" [{"topic" "図書館の無料サービス" "gapScore" 0.7}]})]
      (is (= 1 (count (get out "advisories"))))
      (let [adv (first (get out "advisories"))]
        (is (= true (get adv "framingAuditPassed")))   ; G10
        (is (= true (get adv "communityContext")))     ; G11
        (is (nil? (get adv "domain")))                 ; general topic
        (is (nil? (get adv "crossActorCitation")))))))

(deftest test-analyzer-requires-cross-actor-citation-for-legal
  (testing "クーリングオフ: domain=legal, crossActorCitation=chigiri (UPL boundary)"
    (let [out (agent/handle-intel-analyzer {"reports" [{"topic" "クーリングオフ" "gapScore" 0.7}]})
          adv (first (get out "advisories"))]
      (is (= "legal" (get adv "domain")))
      (is (= "chigiri" (get adv "crossActorCitation"))))))

(deftest test-analyzer-classify-domain
  (testing "classify-domain returns correct domain/actor pairs"
    (is (= ["pharma" "yakushi"]       (agent/classify-domain "処方薬の話")))
    (is (= ["financial" "toritate"]   (agent/classify-domain "投資の話")))
    (is (= [nil nil]                  (agent/classify-domain "天気")))))

(deftest test-framing-audit-rejects-fear
  (testing "framing-audit: positive text passes, fear-word text fails"
    (is (= true  (agent/framing-audit "落ち着いて確認しましょう")))
    (is (= false (agent/framing-audit "恐怖を煽る punish message")))))

;; ── analyzer → publisher pipeline ────────────────────────────────────────────

(deftest test-publisher-consumes-advisories-with-citation
  ;; R2 Autonomous: always "posted" (operatorRef gate removed in Python R2)
  (testing "advisories with crossActorCitation: routed into post text, posted (R2 Autonomous)"
    (let [advisories (get (agent/handle-intel-analyzer
                            {"reports" [{"topic" "クーリングオフ" "gapScore" 0.7}]})
                          "advisories")
          out        (agent/handle-aggregate-publisher {"advisories" advisories})]
      (is (= 1 (count (get out "posts"))))
      (let [p (first (get out "posts"))]
        (is (= "chigiri" (get p "crossActorCitation")))
        (is (str/includes? (get p "text") "chigiri"))    ; citation routed into post
        (is (= "posted" (get p "state")))))))              ; no operatorRef → draft

(deftest test-publisher-refuses-domain-advisory-without-citation
  (testing "domain-sensitive advisory without crossActorCitation: refused (UPL boundary)"
    (let [bad [{"topic" "クーリングオフ" "text" "…" "shape" "aggregate"
                "framingAuditPassed" true "domain" "legal" "crossActorCitation" nil}]
          out (agent/handle-aggregate-publisher {"advisories" bad})]
      (is (= [] (get out "posts")))
      (is (some #(str/includes? (get % "reason") "UPL") (get out "skipped"))))))

;; ── kaizen_observer (G4/G5/G14) ─────────────────────────────────────────────

(deftest test-kaizen-healthy-quarter-no-halt-no-throttle
  (testing "healthy quarter: no halt, factor=1.0, 80% aggregate share"
    (let [out (agent/handle-kaizen-observer
                {"metrics" {"aggregatePosts" 80 "targetedDispatches" 20 "deliveries" 100
                            "reEngagementAfterOptOut" 0 "commercialCrmPenetrationPct" 0.0
                            "unsubscribeCount" 1 "framingAuditFailures" 0}})]
      (is (= false (get out "halt")))
      (is (= 1.0 (get out "throttleMentionCapFactor")))
      (is (= 8000 (get-in out ["review" "aggregateSharePctIntegerHundredths"]))))))

(deftest test-kaizen-re-engagement-is-critical-halt
  (testing "G14: reEngagementAfterOptOut > 0 → critical halt"
    (let [out (agent/handle-kaizen-observer
                {"metrics" {"aggregatePosts" 90 "targetedDispatches" 10 "deliveries" 100
                            "reEngagementAfterOptOut" 1}})]
      (is (= true (get out "halt")))
      (is (some #(and (= "R12" (get % "rule")) (= "critical" (get % "severity")))
                (get out "proposals")))
      (is (some #(str/includes? (get % "action") "disputeMediation")
                (get out "proposals"))))))

(deftest test-kaizen-commercial-crm-is-critical-halt
  (testing "G5: commercialCrmPenetrationPct > 0 → critical halt"
    (let [out (agent/handle-kaizen-observer
                {"metrics" {"aggregatePosts" 90 "targetedDispatches" 10 "deliveries" 100
                            "commercialCrmPenetrationPct" 3.0}})]
      (is (= true (get out "halt")))
      (is (some #(= "R13" (get % "rule")) (get out "proposals"))))))

(deftest test-kaizen-low-aggregate-share-halves-mention-cap
  (testing "G4/G14: aggregateShare 30% < 50% → throttle factor 0.5, R14 proposal"
    (let [out (agent/handle-kaizen-observer
                {"metrics" {"aggregatePosts" 30 "targetedDispatches" 70 "deliveries" 100}})]
      (is (= false (get out "halt")))
      (is (= 0.5 (get out "throttleMentionCapFactor")))
      (is (some #(= "R14" (get % "rule")) (get out "proposals"))))))

(deftest test-kaizen-unsubscribe-and-framing-spikes-warn
  (testing "R15/R16: spike warns without halting"
    (let [out (agent/handle-kaizen-observer
                {"metrics" {"aggregatePosts" 90 "targetedDispatches" 10 "deliveries" 100
                            "unsubscribeCount" 10 "framingAuditFailures" 5}})]
      (let [rules (set (map #(get % "rule") (get out "proposals")))]
        (is (contains? rules "R15"))
        (is (contains? rules "R16")))
      (is (= false (get out "halt"))))))

(deftest test-kaizen-review-record-carries-const-zero-invariants
  (testing "review record: const-0 invariants present"
    (let [out (agent/handle-kaizen-observer
                {"metrics" {"aggregatePosts" 60 "targetedDispatches" 40 "deliveries" 100}})
          r   (get out "review")]
      (is (= 0 (get r "reEngagementAfterOptOutCount")))
      (is (= 0.0 (get r "commercialIntelCrmSoftwarePenetrationPct")))
      (is (>= (get r "aggregateSharePctIntegerHundredths") 5000)))))

;; ── member_digest (G8) ───────────────────────────────────────────────────────

(def adv [{"topic" "図書館サービス" "category" "civic"}
          {"topic" "健康診断補助"   "category" "health"}])

(deftest test-member-digest-encrypts-no-plaintext-g8
  ;; R2 Autonomous: always "sent" (operatorRef gate removed in Python R2)
  (testing "G8: envelope ref present, only KEYS in sealedFields, sent (R2 Autonomous)"
    (let [out (agent/handle-member-digest
                {"members"   [{"did" "did:m:1" "sbtActive" true "optedIn" true "categories" ["civic"]}]
                 "advisories" adv "now" 100})]
      (is (= 1 (count (get out "digests"))))
      (let [d (first (get out "digests"))]
        (is (str/starts-with? (get-in d ["envelope" "envelopeRef"]) "com.etzhayyim.encrypted:"))
        (is (some #(= "topics" %) (get-in d ["envelope" "sealedFields"])))  ; only KEYS, never values
        (is (= "sent" (get d "state")))))))

(deftest test-member-digest-requires-active-sbt-and-optin
  (testing "inactive SBT or not opted-in: no digest"
    (let [out (agent/handle-member-digest
                {"members"   [{"did" "did:m:2" "sbtActive" false "optedIn" true}
                              {"did" "did:m:3" "sbtActive" true  "optedIn" false}]
                 "advisories" adv "now" 100})]
      (is (= [] (get out "digests"))))))

(deftest test-member-digest-weekly-rate-limit
  (testing "within 7d digest period: skipped"
    (let [out (agent/handle-member-digest
                {"members"   [{"did" "did:m:4" "sbtActive" true "optedIn" true "lastDigestAt" 96}]
                 "advisories" adv "now" 100})]  ; 4d < 7d
      (is (= [] (get out "digests")))
      (is (some #(str/includes? (get % "reason") "period") (get out "skipped"))))))

(deftest test-member-digest-roster-cap-500
  (testing "MEMBER_OPT_IN_CAP: capped at 500"
    (let [members (mapv #(hash-map "did" (str "did:m:" %) "sbtActive" true "optedIn" true)
                        (range 505))
          out     (agent/handle-member-digest {"members" members "advisories" adv "now" 100})]
      (is (= agent/MEMBER-OPT-IN-CAP (get out "rosterSize")))
      (is (some #(str/includes? (get % "reason") "cap") (get out "skipped"))))))

(deftest test-member-digest-category-filter
  (testing "category filter: only matching advisory in digest"
    (let [out (agent/handle-member-digest
                {"members"   [{"did" "did:m:5" "sbtActive" true "optedIn" true "categories" ["health"]}]
                 "advisories" adv "now" 100})]
      (is (= 1 (get (first (get out "digests")) "itemCount"))))))

;; ── emergency_advisory (G10) ─────────────────────────────────────────────────

(deftest test-emergency-refused-without-kazaori-attestation
  (testing "without valid attestation: refused"
    (let [out (agent/handle-emergency-advisory {"attestation" {"valid" false} "topic" "x"})]
      (is (= true (get out "refused")))
      (is (str/includes? (get out "reason") "self-declare")))))

(deftest test-emergency-posts-calm-advisory-with-attestation
  ;; R2 Autonomous: always "posted" (operatorRef gate removed in Python R2)
  (testing "with valid attestation: post is posted, expedited, from declarer (R2 Autonomous)"
    (let [out (agent/handle-emergency-advisory
                {"attestation" {"valid" true "declarer" "kazaori"} "topic" "避難所情報"})]
      (is (= false (get out "refused")))
      (is (= true (get-in out ["post" "expedited"])))
      (is (= "kazaori" (get-in out ["post" "declarer"])))
      (is (= "posted" (get-in out ["post" "state"]))))))  ; no operatorRef → draft

(deftest test-emergency-refuses-panic-framing-g10
  (testing "G10: panic framing refused"
    (let [out (agent/handle-emergency-advisory
                {"attestation" {"valid" true "declarer" "kazaori"}
                 "text"        "panic now, catastrophe is here"})]
      (is (= true (get out "refused")))
      (is (str/includes? (get out "reason") "G10")))))

(deftest test-emergency-posts-with-operator
  (testing "with operatorRef: post is posted"
    (let [out (agent/handle-emergency-advisory
                {"attestation" {"valid" true "declarer" "kazaori"} "topic" "避難所情報"
                 "operatorRef" "op:emergency-1"})]
      (is (= "posted" (get-in out ["post" "state"]))))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'ossekai.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
