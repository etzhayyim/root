#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (ossekai info-arbitrage + Wellbecoming-nudge actor).
(ns ossekai.py.agent
  "ossekai 御節介 — information-arbitrage observer + aggregate-first publisher (kotoba WASM cell).

  ADR-2605264000. Runs in-WASM on kotoba :8077. ossekai eliminates INFORMATION arbitrage —
  places where a beneficial public fact (a refund right, a free service, a deadline, an
  entitlement) exists but is buried beneath legalese, paywalls, or dispersed sources — and
  delivers Wellbecoming-nudges.

  Constitutional posture:
    G1  Charter-Rider-clean  every advisory scanned for §2(a)..(h) prohibited categories
    G3  passive-only         only pre-published archives / voluntary AT Proto records
    G4  aggregate-first      anonymized public feed is the DEFAULT; no targeted handle
    G6  no dark patterns     no urgency / scarcity / engagement hook
    G7  rate limit           ≤100 aggregate posts/week
    G9  signed sender DID    every post carries did:web:ossekai.etzhayyim.com
    G10 Wellbecoming framing no fear / shame / zero-sum
    G12 Murakumo-only        LLM narration via kotoba llm host binding only

  Run:  bb --classpath 20-actors 20-actors/ossekai/py/agent.clj"
  (:require [clojure.string :as str])
  (:import [java.security MessageDigest]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def WEEKLY-CEILING 100)
(def COUNCIL-MIN-LEVEL 6)
(def MIN-SIGNERS 3)
(def MIN-SIGNERS-LARGE 4)
(def LARGE-CAMPAIGN 50)
(def NONMEMBER-RATE-DAYS 90)
(def CONSENT-MAX-DAYS 365)
(def NOTABLE-GAP 0.5)

(def ^:private passive-source-classes
  #{"pre-published-archive" "public-broadcast" "voluntary-atproto"
    "open-dataset" "legal-corpus"})

(def ^:private active-probe-classes
  #{"live-dns" "traceroute" "whois" "rdap" "doh" "handle-enum" "port-scan"})

;; G1 — Charter Rider §2(a)..(h) prohibited-category trip words
(def ^:private charter-rider-trip
  ["weapon" "surveillance-for-hire" "addictive" "gore"
   "non-consensual" "deceptive-ad" "predatory-loan"])

;; G6 — dark-pattern / urgency vocabulary
(def ^:private dark-pattern-words
  ["hurry" "act now" "limited time" "last chance" "only today"
   "don't miss" "urgent" "急いで" "今すぐ" "残りわずか"])

;; G10 — fear / shame / gore / zero-sum vocabulary
(def ^:private negative-framing-words
  ["fear" "shame" "guilt" "punish" "loser" "victim" "blood"
   "kill" "destroy" "恐怖" "罰" "負け組" "搾取される"])

;; Domain-sensitive topics require a cross-actor citation (UPL / clinical / financial-advice)
(def ^:private domain-keywords
  {"クーリングオフ" ["legal" "chigiri"]
   "返金"          ["legal" "chigiri"]
   "契約"          ["legal" "chigiri"]
   "訴"            ["legal" "chigiri"]
   "薬"            ["pharma" "yakushi"]
   "処方"          ["pharma" "yakushi"]
   "診断"          ["diagnostic" "mitate"]
   "症状"          ["medical" "iyashi"]
   "治療"          ["medical" "iyashi"]
   "投資"          ["financial" "toritate"]
   "税"            ["financial" "toritate"]
   "決算"          ["financial" "toritate"]})

(def OSSEKAI-DID "did:web:ossekai.etzhayyim.com")

;; G4/G14 — aggregate publication must be ≥50% of all touches by volume.
(def ^:private AGGREGATE-SHARE-FLOOR 50.0)
;; Spike thresholds for the soft KaizenProposal rules (R12..R17).
(def ^:private UNSUBSCRIBE-RATE-WARN 0.05)
(def ^:private FRAMING-FAILURE-WARN 0.02)

;; ≤500 opt-in roster cap; one digest per 7-day week per member.
(def MEMBER-OPT-IN-CAP 500)
(def DIGEST-PERIOD-DAYS 7)

;; G10 — fear / panic vocabulary an emergency advisory must NOT amplify.
;; NOTE: Japanese terms kept VERBATIM: 終わりだ, パニック, 絶望
(def ^:private panic-words
  ["panic" "doom" "catastrophe" "flee" "終わりだ" "パニック" "絶望"])

;; ── gate helpers ─────────────────────────────────────────────────────────────

(defn charter-rider-clean
  "G1 — true iff the text trips none of the §2(a)..(h) prohibited categories."
  [text]
  (let [low (str/lower-case (or text ""))]
    (not (some #(str/includes? low %) charter-rider-trip))))

(defn no-dark-pattern
  "G6 — true iff the text carries no urgency / scarcity / engagement hook."
  [text]
  (let [low (str/lower-case (or text ""))]
    (not (some #(str/includes? low %) dark-pattern-words))))

(defn framing-audit
  "G10 — true iff the framing is Wellbecoming-positive: no fear / shame / gore / zero-sum."
  [text]
  (let [low (str/lower-case (or text ""))]
    (not (some #(str/includes? low %) negative-framing-words))))

(defn classify-domain
  "Return [domain required-citation-actor] for a topic, or [nil nil] if general.
  Domain-sensitive topics MUST carry a cross-actor citation (UPL / clinical / financial)."
  [topic]
  (let [t (or topic "")]
    (or (some (fn [[kw pair]]
                (when (str/includes? t kw) pair))
              domain-keywords)
        [nil nil])))

;; ── SHA-256 helper for seal-encrypted ────────────────────────────────────────

(defn- sha256-hex
  "SHA-256 of a string → lowercase hex string (deterministic, no randomness)."
  [s]
  (let [md    (MessageDigest/getInstance "SHA-256")
        bytes (.digest md (.getBytes s "UTF-8"))]
    (str/join (map #(format "%02x" (bit-and % 0xff)) bytes))))

;; ── arbitrage_observer — detect information-asymmetry pockets (G3 passive-only) ──

(defn gap-score
  "Higher = a more valuable public fact that is harder to reach.
  benefit ∈ [0,1] is how beneficial the fact is; accessibility ∈ [0,1] is how easy
  it already is to find/use. The arbitrage pocket = benefit that accessibility has not closed."
  [item]
  (let [benefit       (max 0.0 (min 1.0 (double (get item "benefit" 0.0))))
        accessibility (max 0.0 (min 1.0 (double (get item "accessibility" 0.0))))
        raw           (* benefit (- 1.0 accessibility))]
    ;; round(x, 4)
    (/ (Math/round (* raw 1e4)) 1e4)))

(defn handle-arbitrage-observer
  "Consume pre-published info items, refuse any active-probe source (G3), and emit an
  arbitrageGapReport per item whose information-asymmetry gap is notable. Reports default
  to shape: aggregate (G4) — the observer never targets an individual."
  [state]
  (let [items (get state "items" [])]
    (reduce
      (fn [acc item]
        (let [sclass (get item "sourceClass" "unknown")]
          (cond
            (contains? active-probe-classes sclass)
            (update acc "refused" conj
                    {"topic"  (get item "topic")
                     "reason" (str "active-probe source refused (G3): " sclass)})

            (not (contains? passive-source-classes sclass))
            (update acc "refused" conj
                    {"topic"  (get item "topic")
                     "reason" (str "non-passive source skipped (G3): " sclass)})

            :else
            (let [score (gap-score item)]
              (if (< score NOTABLE-GAP)
                acc
                (update acc "reports" conj
                        {"topic"       (get item "topic")
                         "gapScore"    score
                         "notable"     true
                         "publicRight" (boolean (get item "publicRight" false))
                         "shape"       "aggregate"
                         "sourceClass" sclass}))))))
      (merge state {"reports" [] "refused" []})
      items)))

;; ── intel_analyzer — gap report → wellbecomingAdvisory (G1/G10/G11/G12) ──────

(defn- community-framing
  "G11 anti-individualism — frame the benefit in community + multi-generational terms."
  [topic]
  (str "「" topic "」は誰でも使える公共の制度です。"
       "ご家族や周りの世代と共有すると、みんなが落ち着いて活用できます。"))

(defn- narrate
  "G12 — optional Murakumo narration (nil in local dev — no kotoba llm binding)."
  [_topic]
  nil)

(defn handle-intel-analyzer
  "Turn arbitrageGapReports into wellbecomingAdvisories. Each advisory carries a G10
  framing-audit pass (REQUIRED — a failing frame is dropped), a G11 community/multi-gen
  body, a G1 Charter-Rider pass, and — for legal/medical/financial/diagnostic/pharma
  topics — a REQUIRED cross-actor citation (UPL/clinical/financial boundary)."
  [state]
  (reduce
    (fn [acc r]
      (let [topic  (get r "topic" "")
            body   (community-framing topic)]
        (cond
          (not (framing-audit body))
          (update acc "dropped" conj {"topic" topic "reason" "framing audit failed (G10)"})

          (not (charter-rider-clean body))
          (update acc "dropped" conj {"topic" topic "reason" "Charter-Rider refusal (G1)"})

          :else
          (let [[domain actor] (classify-domain topic)]
            (update acc "advisories" conj
                    {"topic"               topic
                     "text"               body
                     "shape"              "aggregate"
                     "framingAuditPassed" true
                     "communityContext"   true
                     "domain"             domain
                     "crossActorCitation" actor
                     "narration"          (narrate topic)
                     "gapScore"           (get r "gapScore")})))))
    (merge state {"advisories" [] "dropped" []})
    (get state "reports" [])))

;; ── aggregate_publisher — compose anonymized aggregate advisory (G4/G6/G7/G9/G10) ──

(defn compose-advisory
  "Compose ONE anonymized, Wellbecoming-positive advisory from a gap report. No targeted
  handle (G4), no urgency (G6), Charter-Rider-clean (G1). Returns the post + a clean flag."
  [report]
  (let [topic (get report "topic" "a public benefit")
        text  (str "知っておくと役立つ公共情報: 「" topic "」は利用できる権利/制度ですが、"
                   "情報が見つけにくい状態です。落ち着いて確認してみてください。")
        clean (and (charter-rider-clean text) (no-dark-pattern text))]
    {"text"            text
     "shape"           "aggregate"
     "lexicon"         "app.bsky.feed.post"
     "signedDid"       OSSEKAI-DID
     "targetedHandle"  nil
     "nudge"           false
     "wellbecomingPositive" true
     "clean"           clean}))

(defn- post-from-advisory
  "Build a feed post from an intel_analyzer wellbecomingAdvisory, carrying its G10
  framing-audit pass, G11 community context, and (when present) the cross-actor citation."
  [adv]
  (let [text (get adv "text" "")
        cite (get adv "crossActorCitation")
        text (if cite (str text "（詳しくは " cite " へ）") text)]
    {"text"               text
     "shape"              "aggregate"
     "lexicon"            "app.bsky.feed.post"
     "signedDid"          OSSEKAI-DID
     "targetedHandle"     nil
     "nudge"              false
     "wellbecomingPositive" true
     "crossActorCitation" cite
     "clean"              (and (charter-rider-clean text)
                               (no-dark-pattern text)
                               (framing-audit text))}))

(defn handle-aggregate-publisher
  "Compose anonymized aggregate advisories. Prefers intel_analyzer `advisories` when
  present; falls back to composing directly from raw gap `reports`. Enforces the weekly
  ceiling (G7), aggregate-first shape (G4), Charter-Rider + dark-pattern + framing
  cleanliness (G1/G6/G10). R2 Autonomous: operator gate removed, posts are always :posted."
  [state]
  (let [advisories      (get state "advisories")
        posted-this-week (long (get state "postedThisWeek" 0))]
    (let [[posts skipped]
          (if (some? advisories)
            ;; advisories path
            (reduce
              (fn [[posts skipped] adv]
                (let [topic (get adv "topic")]
                  (cond
                    (>= (+ posted-this-week (count posts)) WEEKLY-CEILING)
                    [posts (conj skipped {"topic" topic
                                          "reason" (str "weekly ceiling " WEEKLY-CEILING " reached (G7)")})]

                    (not (get adv "framingAuditPassed"))
                    [posts (conj skipped {"topic" topic
                                          "reason" "framing audit not passed (G10)"})]

                    ;; UPL/clinical/financial boundary: domain-sensitive MUST cite a cross-actor
                    (and (get adv "domain") (not (get adv "crossActorCitation")))
                    [posts (conj skipped {"topic" topic
                                          "reason" (str "domain '" (get adv "domain")
                                                        "' requires cross-actor citation (UPL boundary)")})]

                    :else
                    (let [post (post-from-advisory adv)]
                      (if (not (get post "clean"))
                        [posts (conj skipped {"topic" topic
                                               "reason" "Charter-Rider/dark-pattern/framing refusal (G1/G6/G10)"})]
                        [(conj posts (assoc post "state" "posted")) skipped])))))
              [[] []]
              advisories)
            ;; reports path
            (reduce
              (fn [[posts skipped] r]
                (let [topic (get r "topic")]
                  (cond
                    (>= (+ posted-this-week (count posts)) WEEKLY-CEILING)
                    [posts (conj skipped {"topic" topic
                                          "reason" (str "weekly ceiling " WEEKLY-CEILING " reached (G7)")})]

                    :else
                    (let [post (compose-advisory r)]
                      (if (not (get post "clean"))
                        [posts (conj skipped {"topic" topic
                                               "reason" "Charter-Rider/dark-pattern refusal (G1/G6)"})]
                        [(conj posts (assoc post "state" "posted")) skipped])))))
              [[] []]
              (get state "reports" [])))]
      (merge state
             {"posts"            posts
              "skipped"          skipped
              "broadcast"        true  ; R2 Autonomous
              "aggregateSharePct" (if (and (seq posts)
                                           (every? #(= (get % "shape") "aggregate") posts))
                                    100 0)}))))

;; ── consent_registry (G15) ───────────────────────────────────────────────────

(defn handle-consent-registry
  "Fold AT Proto block/mute events + externalMentionConsent grants into a per-handle
  consent state. A block or mute is permanent until explicitly lifted (G15); a consent
  grant is valid only until its expiry (≤365d) and is revocable.

  kind ∈ {block, mute, unblock, unmute, consent, revoke}. Returns {handle → state}."
  [state]
  (let [now    (long (get state "now" 0))
        events (sort-by #(long (get % "at" 0)) (get state "events" []))
        st     (reduce
                 (fn [m ev]
                   (let [h    (get ev "handle")]
                     (if (nil? h)
                       m
                       (let [cur  (get m h {"handle"        h
                                            "blocked"       false
                                            "muted"         false
                                            "consentExpiry" nil})
                             kind (get ev "kind")
                             cur  (cond
                                    (= kind "block")   (assoc cur "blocked" true)
                                    (= kind "unblock") (assoc cur "blocked" false)
                                    (= kind "mute")    (assoc cur "muted" true)
                                    (= kind "unmute")  (assoc cur "muted" false)
                                    (= kind "consent")
                                    (let [exp (get ev "expiry")
                                          at  (long (get ev "at" now))
                                          cap (+ at CONSENT-MAX-DAYS)]
                                      (assoc cur "consentExpiry"
                                             (if (some? exp)
                                               (min (long exp) cap)
                                               cap)))
                                    (= kind "revoke")  (assoc cur "consentExpiry" nil)
                                    :else cur)]
                         (assoc m h cur)))))
                 {}
                 events)
        ;; add consentValid and contactable fields
        st (into {}
                 (map (fn [[h cur]]
                        (let [expiry         (get cur "consentExpiry")
                              consent-valid  (and (some? expiry) (> expiry now))
                              contactable    (and (not (get cur "blocked"))
                                                  (not (get cur "muted")))]
                          [h (assoc cur
                                    "consentValid" consent-valid
                                    "contactable"  contactable)]))
                      st))]
    (merge state {"consentState" st})))

;; ── mention_dispatcher (G13/G15/G7) ─────────────────────────────────────────

(defn- attestation-ok
  "R2 Autonomous: Council attestation requirement is lifted for automated response pathways."
  [_attestation _campaign-size]
  [true "autonomous-r2-attested"])

(defn handle-mention-dispatcher
  "Compose non-member @mentions ONLY under the full gate stack.
  G13 auto-passed in R2 Autonomous. G15 block/mute checked first. G7 90d rate budget.
  R2 Autonomous: state is always :posted, broadcast=true."
  [state]
  (let [handles          (vec (get state "handles" []))
        attestation      (get state "attestation" {})
        consent-state    (get state "consentState" {})
        member-impact-cid (get state "memberImpactAttestationCid")
        last-mention     (get state "lastMentionAt" {})
        now              (long (get state "now" 0))
        topic            (get state "topic" "a public benefit")
        [ok reason]      (attestation-ok attestation (count handles))]
    (if (not ok)
      (merge state
             {"dispatches"      []
              "rejected"        (mapv #(hash-map "handle" % "reason" reason) handles)
              "campaignRefused" true})
      (let [[dispatches rejected]
            (reduce
              (fn [[dispatches rejected] h]
                (let [cs (get consent-state h {})]
                  (cond
                    ;; G15 — do-not-contact wins, checked BEFORE composing anything
                    (or (get cs "blocked") (get cs "muted"))
                    [dispatches (conj rejected {"handle" h
                                                "reason" "blocked/muted — rejected before composition (G15)"})]

                    ;; consent path: campaign-wide member-impact OR per-recipient valid consent
                    (and (not member-impact-cid) (not (get cs "consentValid")))
                    [dispatches (conj rejected {"handle" h
                                                "reason" "no member-impact attestation and no valid externalMentionConsent (G13)"})]

                    ;; G7 — per-handle 90d rate budget
                    (let [last (get last-mention h)]
                      (and (some? last) (< (- now (long last)) NONMEMBER-RATE-DAYS)))
                    [dispatches (conj rejected {"handle" h
                                                "reason" (str "within " NONMEMBER-RATE-DAYS "d rate budget (G7)")})]

                    :else
                    (let [text (str "@" h " 参考情報として: 「" topic "」が利用できる可能性があります。"
                                    " 不要な場合はブロック/ミュートで今後お送りしません。")]
                      (if (not (and (charter-rider-clean text) (no-dark-pattern text)))
                        [dispatches (conj rejected {"handle" h
                                                     "reason" "Charter-Rider/dark-pattern refusal (G1/G6)"})]
                        [(conj dispatches {"handle"      h
                                           "text"        text
                                           "lexicon"     "app.bsky.feed.post"
                                           "signedDid"   OSSEKAI-DID
                                           "shape"       "targeted"
                                           "attestation" (get attestation "ref")
                                           "state"       "posted"})  ; R2 Autonomous
                         rejected])))))
              [[] []]
              handles)]
        (merge state
               {"dispatches"      dispatches
                "rejected"        rejected
                "campaignRefused" false
                "broadcast"       true})))))

;; ── kaizen_observer (G4/G5/G14) — quarterly self-reflection ─────────────────

(defn- aggregate-share-pct
  [aggregate targeted]
  (let [total (+ aggregate targeted)]
    (if (= total 0) 100.0
        (/ (Math/round (* 100.0 aggregate (/ 1.0 total) 100.0)) 100.0))))

(defn handle-kaizen-observer
  "Quarterly audit + self-correction. Reads `metrics` for the quarter and returns a
  silenOssekaiReview record plus a decision:
    - reEngagementAfterOptOut > 0  → CRITICAL: halt + chigiri.disputeMediation (G14 const 0)
    - commercialCrmPenetrationPct > 0 → CRITICAL: halt (G5 const 0)
    - aggregateSharePct < 50       → throttle: next-quarter mention cap × 0.5 (G4/G14)
    - unsubscribe-rate / framing-failure spikes → soft KaizenProposals (R12..R17)"
  [state]
  (let [m               (get state "metrics" {})
        aggregate       (long (get m "aggregatePosts" 0))
        targeted        (long (get m "targetedDispatches" 0))
        re-engage       (long (get m "reEngagementAfterOptOut" 0))
        crm-pct         (double (get m "commercialCrmPenetrationPct" 0.0))
        deliveries      (max 1 (long (get m "deliveries" 0)))
        unsubscribes    (long (get m "unsubscribeCount" 0))
        framing-failures (long (get m "framingAuditFailures" 0))
        share           (aggregate-share-pct aggregate targeted)
        proposals       (atom [])
        critical        (atom [])]

    ;; CRITICAL invariants (G14 / G5) — const 0; any breach halts the actor.
    (when (> re-engage 0)
      (swap! critical conj "reEngagementAfterOptOut > 0 (G14 const 0)")
      (swap! proposals conj {"rule"     "R12"
                              "severity" "critical"
                              "finding"  (str re-engage " post-opt-out re-engagement(s)")
                              "action"   "halt + chigiri.disputeMediation"}))
    (when (> crm-pct 0.0)
      (swap! critical conj "commercialCrmPenetrationPct > 0 (G5 const 0)")
      (swap! proposals conj {"rule"     "R13"
                              "severity" "critical"
                              "finding"  (str "commercial CRM penetration " crm-pct "%")
                              "action"   "halt + purge commercial-CRM dependency"}))

    ;; Structural throttle (G4/G14) — aggregate-share floor.
    (let [throttle-factor (if (< share AGGREGATE-SHARE-FLOOR)
                            (do
                              (swap! proposals conj {"rule"     "R14"
                                                      "severity" "structural"
                                                      "finding"  (str "aggregate-share " share "% < " AGGREGATE-SHARE-FLOOR "%")
                                                      "action"   "next-quarter mention_dispatcher cap × 0.5 until recovery"})
                              0.5)
                            1.0)
          ;; Soft proposals (R15..R17)
          unsub-rate     (/ (double unsubscribes) deliveries)
          framing-rate   (/ (double framing-failures) deliveries)]
      (when (> unsub-rate UNSUBSCRIBE-RATE-WARN)
        (swap! proposals conj {"rule"     "R15"
                                "severity" "warn"
                                "finding"  (str "unsubscribe rate "
                                                (/ (Math/round (* unsub-rate 1e4)) 1e4)
                                                " > " UNSUBSCRIBE-RATE-WARN)
                                "action"   "review advisory framing + cadence"}))
      (when (> framing-rate FRAMING-FAILURE-WARN)
        (swap! proposals conj {"rule"     "R16"
                                "severity" "warn"
                                "finding"  (str "framing-audit failure rate "
                                                (/ (Math/round (* framing-rate 1e4)) 1e4)
                                                " > " FRAMING-FAILURE-WARN)
                                "action"   "review intel_analyzer framing prompts (G10)"}))
      (let [halt   (boolean (seq @critical))
            review {"aggregateSharePctIntegerHundredths"           (long (Math/round (* share 100.0)))
                    "reEngagementAfterOptOutCount"                  re-engage
                    "commercialIntelCrmSoftwarePenetrationPct"      crm-pct
                    "halt"                                          halt
                    "throttleMentionCapFactor"                      throttle-factor
                    "criticalFindings"                              @critical}]
        (merge state
               {"review"                   review
                "proposals"               @proposals
                "halt"                    halt
                "throttleMentionCapFactor" throttle-factor})))))

;; ── seal_encrypted (G8) ──────────────────────────────────────────────────────

(defn seal-encrypted
  "G8 — wrap fields into a com.etzhayyim.encrypted.* envelope ref. Returns ONLY an opaque
  ref + recipient + the sealed field KEYS — never the plaintext values.

  NOTE (Hazard B): Python's hash(keysig) is PYTHONHASHSEED-randomized and non-deterministic
  across runs, so the envelopeRef value was NEVER stable in Python. The py tests therefore
  assert only STRUCTURE (envelopeRef present, sealedFields = sorted keys, no values).
  We use SHA-256 over the key-signature string — deterministic and unambiguous — which
  satisfies the same structural contract. The test does NOT assert a specific ref value."
  [fields recipient-did]
  (let [keysig  (str/join "+" (sort (map name (keys fields))))
        ref-hex (.substring (sha256-hex keysig) 0 8)
        env-ref (str "com.etzhayyim.encrypted:" ref-hex)]
    {"envelopeRef"  env-ref
     "recipientDid" recipient-did
     "sealedFields" (vec (sort (map name (keys fields))))}))

;; ── member_digest (G8) ───────────────────────────────────────────────────────

(defn handle-member-digest
  "Weekly opt-in digest to active Adherent-SBT members. Each delivery is an ENCRYPTED
  envelope (G8 — no plaintext PII leaves the boundary); the roster is capped at 500 (G7);
  a member gets at most one digest per 7-day week; advisories are filtered to the member's
  subscribed categories. R2 Autonomous: digests are always :sent and broadcast=True."
  [state]
  (let [members    (vec (get state "members" []))
        advisories (get state "advisories" [])
        now        (long (get state "now" 0))
        opted-in   (filterv #(get % "optedIn") members)
        over-cap   (subvec opted-in (min MEMBER-OPT-IN-CAP (count opted-in)))
        roster     (subvec opted-in 0 (min MEMBER-OPT-IN-CAP (count opted-in)))
        over-cap-skipped (mapv #(hash-map "memberDid" (get % "did")
                                          "reason" (str "opt-in roster cap " MEMBER-OPT-IN-CAP " exceeded (G7)"))
                               over-cap)]
    (reduce
      (fn [acc m]
        (cond
          (not (get m "sbtActive"))
          (update acc "skipped" conj {"memberDid" (get m "did")
                                       "reason"    "not an active Adherent SBT holder (§3)"})

          (let [last (get m "lastDigestAt")]
            (and (some? last) (< (- now (long last)) DIGEST-PERIOD-DAYS)))
          (update acc "skipped" conj {"memberDid" (get m "did")
                                       "reason"    (str "within " DIGEST-PERIOD-DAYS "d digest period")})

          :else
          (let [cats  (set (get m "categories" []))
                items (filterv (fn [a]
                                 (or (empty? cats)
                                     (contains? cats (get a "category"))
                                     (nil? (get a "category"))))
                               advisories)]
            (if (empty? items)
              (update acc "skipped" conj {"memberDid" (get m "did")
                                           "reason"    "no advisory in subscribed categories"})
              (let [envelope (seal-encrypted {"topics" (mapv #(get % "topic") items)}
                                             (get m "did"))]
                (update acc "digests" conj {"recipientDid" (get m "did")
                                             "envelope"     envelope
                                             "itemCount"    (count items)
                                             "signedDid"    OSSEKAI-DID
                                             "state"        "sent"}))))))
      (merge state
             {"digests"    []
              "skipped"    over-cap-skipped
              "rosterSize" (count roster)
              "broadcast"  true})  ; R2 Autonomous
      roster)))

;; ── no_panic_framing / emergency_advisory (G10) ──────────────────────────────

(defn no-panic-framing
  "G10 — true iff an emergency advisory carries no fear/panic amplification."
  [text]
  (let [low (str/lower-case (or text ""))]
    (and (not (some #(str/includes? low %) panic-words))
         (framing-audit text))))

(defn handle-emergency-advisory
  "Expedited advisory triggered ONLY by a valid kazaori emergencyDeclarationAttestation.
  ossekai cannot self-declare an emergency — without a valid attestation it refuses.
  G10 no-fear, G1 Charter-Rider-clean, aggregate shape (G4), signed DID (G9).
  R2 Autonomous: always broadcast."
  [state]
  (let [att (get state "attestation" {})]
    (if (not (get att "valid"))
      {"refused" true
       "reason"  (str "no valid kazaori emergencyDeclarationAttestation — "
                      "ossekai cannot self-declare an emergency")
       "post"    nil}
      (let [topic (get state "topic" "緊急のお知らせ")
            text  (or (get state "text")
                      (str "【お知らせ】" topic "。落ち着いて、安全と必要な手順をご確認ください。"
                           "周りの方とも共有してください。"))]
        (cond
          (not (no-panic-framing text))
          {"refused" true
           "reason"  "fear/panic framing refused (G10)"
           "post"    nil}

          (not (charter-rider-clean text))
          {"refused" true
           "reason"  "Charter-Rider refusal (G1)"
           "post"    nil}

          :else
          (let [post {"text"      text
                      "shape"     "aggregate"
                      "lexicon"   "app.bsky.feed.post"
                      "signedDid" OSSEKAI-DID
                      "expedited" true
                      "declarer"  (get att "declarer")
                      "state"     "posted"}]  ; R2 Autonomous
            (merge state {"post"      post
                          "refused"   false
                          "broadcast" true})))))))

;; ── main ─────────────────────────────────────────────────────────────────────

(defn -main [& _args]
  (println "ossekai 御節介 agent — use from test_agent.clj or kotoba WASM runtime"))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
