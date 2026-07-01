(ns etzhayyim.channel
  "kotoba-genome W1 — the Channel egress protocol (ADR-2606302205 D2).

  ONE driver registry maps a target channel to an egress driver, so the organism
  and every actor emit a single channel-neutral envelope and a fan-out drainer
  delivers it to N channels (AT Protocol / email / X / Telegram / LINE / SMS …) —
  instead of the per-channel bespoke bridges of today (only email exists, hand-
  built). Identity is already channel-agnostic (the did:key CACAO leash, reused
  for DKIM); a new channel = one driver + one `app.<channel>.*` lexicon family.

  The content-safety + DISCLOSURE scan runs BEFORE emit, channel-independently
  (ADR-2606281500 seed-and-grow + ADR-2606302205 D4): an actor posts AS
  'etzhayyim's <domain> observatory actor' (voiceOf=etzhayyim, isObservatory) and
  must NEVER claim to BE a real entity; private persons are consent-gated. These
  are the floors derived from the un-amendable Charter catastrophe term — they are
  what make 'every actor posts' safe.

  W1 scope: drivers are DRY-RUN reference implementations (they return the wire
  shape they WOULD send); live legs are Council/operator-gated (W4). .cljc so the
  same protocol runs on JVM/bb, cljs and WASM."
  (:require [clojure.string :as str]
            [etzhayyim.ecl :as ecl]))

;; ── emit envelope ───────────────────────────────────────────────────────────
;; {:actor          "ooyake"                      ; emitting actor handle
;;  :lexicon        "app.bsky.feed.post"          ; target record/NSID (dispatch key)
;;  :content        {:text "…"}                   ; channel-neutral payload
;;  :targets        #{:at-proto :telegram}        ; which channels to fan out to
;;  :voice-of       "etzhayyim"                   ; disclosure: whose voice this is
;;  :is-observatory true                          ; disclosure: observatory actor
;;  :claims-to-be-entity false                    ; impersonation flag (must be false)
;;  :person-subject? false :consent? false        ; person protection
;;  :identity-ref   "leash:cacao:…"               ; member-CACAO leash ref (off-switch)
;;  :dry-run        true}

(defprotocol Channel
  "An egress driver for one channel. Implementations are pure w.r.t. the envelope
  in W1 (dry-run): -emit! returns the wire shape it WOULD send."
  (channel-id [this] "Stable keyword id, e.g. :at-proto / :email / :telegram.")
  (accepts? [this lexicon] "True when this driver handles the envelope's lexicon.")
  (-emit! [this envelope] "Deliver (W1: return the would-be wire record)."))

;; ── registry ────────────────────────────────────────────────────────────────
(defonce ^:private registry (atom {}))

(defn register!
  "Register a Channel driver. Returns the driver."
  [driver]
  (swap! registry assoc (channel-id driver) driver)
  driver)

(defn unregister! [id] (swap! registry dissoc id) nil)
(defn registered [] (set (keys @registry)))
(defn clear-registry! [] (reset! registry {}) nil)

(defn drivers-for
  "Registered drivers that (a) are in the envelope's :targets (or all, if no
  :targets) AND (b) accept the envelope's :lexicon."
  [{:keys [lexicon targets]}]
  (->> (vals @registry)
       (filter (fn [d] (and (or (nil? targets) (contains? targets (channel-id d)))
                            (accepts? d lexicon))))
       (sort-by channel-id)))

;; ── the Charter floor: content-safety + disclosure scan (before emit) ─────────
(defn charter-scan
  "ADR-2606302205 D4 + ADR-2606281500. Returns
  {:verdict :pass|:veto :reasons [..]}. The floors that make universal posting
  safe — derived from the un-amendable catastrophe term, NOT separately amendable."
  [{:keys [voice-of is-observatory claims-to-be-entity
           person-subject? consent? targets-person?] :as _env}]
  (let [reasons
        (cond-> []
          ;; impersonation floor: must not claim to BE a real third-party entity
          (true? claims-to-be-entity)
          (conj :impersonation/claims-to-be-real-entity)
          ;; disclosure duty: an observatory voice must declare voiceOf=etzhayyim
          (and (true? is-observatory) (not= "etzhayyim" voice-of))
          (conj :disclosure/observatory-missing-voiceof-etzhayyim)
          ;; person protection: subject is a private person without consent
          (and (true? person-subject?) (not (true? consent?)))
          (conj :person/subject-without-consent)
          ;; no person-targeting (ADR-2606281500)
          (true? targets-person?)
          (conj :person/targeting))]
    (if (seq reasons)
      {:verdict :veto :reasons reasons}
      {:verdict :pass :reasons []})))

;; ── content catastrophe-scan (the Rider §2 floor, made operational at R0) ─────
;; A reference deny-list over the FREE-TEXT content — the always-on floor before
;; every emit (ADR-2606281500: content-safety scan before emit). The full Rider §2
;; objective-function scan (ADR-2606182359) is the upstream engine; this is the
;; catastrophe-term backstop. Categories, not graphic. Independent of channel.
(def ^:private catastrophe-patterns
  {:content/csam               #"(?i)child\s*(?:sexual|porn)|児童\s*ポルノ|小児性愛"
   :content/targeted-violence  #"(?i)\bkill\s+(?:him|her|them)\b|(?:殺|襲撃)\s*(?:せ|し)ろ"
   :content/self-impersonation #"(?i)\bI am the (?:government|company|official|CEO)\b|私は(?:政府|当社|本人|公式)(?:です|である)"})

(defn- hit->scores
  "Map a content deny-list hit to ECL 子孫-wellbecoming evidence scores (the
  objective-function's catastrophe dims). CSAM / targeted-violence = maximal harm
  to 子/孫 (≤ -1.9 → catastrophe term fires). Self-impersonation is a disclosure
  violation, not a 子孫-catastrophe — still vetoed by the floor, but not via J."
  [cat]
  (case cat
    :content/csam               {:ko-wellbecoming -2.0 :mago-wellbecoming -2.0}
    :content/targeted-violence  {:ko-wellbecoming -2.0}
    {}))

(defn content-scan
  "Scan free-text content before emit, CONNECTED to the Rider §2 objective function
  (etzhayyim.ecl, ADR-2606182359): deny-list hits become catastrophic 子孫 scores and
  the REAL ECL `route` confirms the verdict (:ecl {:route :J}); fail-open to the
  deny-list floor when the spec is unavailable. Returns {:verdict :pass|:veto :reasons
  [category…] :ecl {…}}. voiceOf=etzhayyim posts must never read as the entity's own
  first-person voice, never target a person, never carry CSAM — the un-amendable
  catastrophe floor (the priority is absolute)."
  [text]
  (let [s (str text)
        hits (vec (keep (fn [[cat re]] (when (re-find re s) cat)) catastrophe-patterns))]
    (if (empty? hits)
      {:verdict :pass :reasons []}
      (let [scores (reduce (fn [m c] (merge m (hit->scores c))) {} hits)
            r (try (ecl/route scores) (catch #?(:clj Throwable :cljs :default) _ nil))]
        {:verdict :veto :reasons hits
         :ecl (if r (select-keys r [:route :J :reason]) :unavailable)}))))

;; ── the fan-out drainer ───────────────────────────────────────────────────────
(defn emit!
  "Scan (metadata disclosure/person floor AND content catastrophe floor), then fan
  out a channel-neutral envelope to every matching registered driver. Returns
  {:emitted bool :scan {…} :results {channel-id <driver-result>} :dry-run bool}.
  A veto (either scan) blocks ALL channels (the scan is channel-independent)."
  [{:keys [dry-run content] :or {dry-run true} :as envelope}]
  (let [meta-scan (charter-scan envelope)
        text-scan (content-scan (if (map? content) (:text content) content))
        scan (cond (= :veto (:verdict meta-scan)) meta-scan
                   (= :veto (:verdict text-scan)) text-scan
                   :else meta-scan)]
    (if (= :veto (:verdict scan))
      {:emitted false :scan scan :results {} :dry-run dry-run}
      (let [drivers (drivers-for envelope)
            results (reduce (fn [m d]
                              (assoc m (channel-id d) (-emit! d envelope)))
                            {} drivers)]
        {:emitted (boolean (seq results))
         :scan scan
         :channels (vec (sort (keys results)))
         :results results
         :dry-run dry-run}))))

;; ── reference drivers (W1: dry-run wire shapes) ──────────────────────────────
(defn- prefixes? [lexicon ps] (some #(str/starts-with? (str lexicon) %) ps))

(defrecord AtProtoChannel [pds]
  Channel
  (channel-id [_] :at-proto)
  (accepts? [_ lexicon] (boolean (prefixes? lexicon ["app.bsky." "com.etzhayyim.apps." "com.etzhayyim.convo." "com.etzhayyim.observatory."])))
  (-emit! [_ {:keys [actor lexicon content voice-of is-observatory]}]
    {:driver :at-proto :dry-run true :endpoint pds
     :op :com.atproto.repo.createRecord
     :record {:$type lexicon :actor actor :voiceOf voice-of :isObservatory (boolean is-observatory)
              :payload content}}))

(defrecord EmailChannel [relay]
  Channel
  (channel-id [_] :email)
  (accepts? [_ lexicon] (boolean (prefixes? lexicon ["app.openmail." "com.etzhayyim.apps.kotoba.email."])))
  (-emit! [_ {:keys [actor content voice-of]}]
    {:driver :email :dry-run true :relay relay
     :message {:from (str actor "@actors.etzhayyim.com") :dkim-by voice-of
               :subject (:subject content) :body (:text content)}}))

(defrecord TelegramChannel [bot]
  Channel
  (channel-id [_] :telegram)
  (accepts? [_ lexicon] (boolean (prefixes? lexicon ["app.telegram."])))
  (-emit! [_ {:keys [content]}]
    ;; PoC driver — the Bot API call it WOULD make (dry-run; live = W4, leash-signed)
    {:driver :telegram :dry-run true :bot bot
     :api-call {:method "sendMessage" :chat_id (:chat-id content) :text (:text content)}}))

(defn default-registry!
  "Register the W1 reference drivers. Returns the set of registered channel ids."
  []
  (clear-registry!)
  (register! (->AtProtoChannel "https://aozora.app"))
  (register! (->EmailChannel "https://kotoba-server.etzhayyim.com"))
  (register! (->TelegramChannel "did:web:bridge.telegram.etzhayyim.com"))
  (registered))
