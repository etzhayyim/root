(ns etzhayyim.observatory
  "kotoba-genome W4 — entity/domain actors as FIRST-PARTY, disclosure-honest,
  self-evolving, dialogic actors (ADR-2606302205 D4 — retires the keyless
  observational mirror of ADR-2606042330).

  Every namespace/entity actor (corp 兜 / gov 公 / cable / station / craft …) is
  now a first-party actor built on the W3 runtime (etzhayyim.actor): its OWN
  did:key (present-only, member-CACAO-leashed — NOT keyless, NOT platform-held),
  the genome learning loop (it grows by LEARNING, not merely accumulating), the
  channel social egress, and a converse surface (it can be talked to and responds).

  It posts/speaks AS 'etzhayyim's <domain> observatory actor' — voiceOf=etzhayyim,
  isObservatory=true — and NEVER claims to BE the real government/company/person
  (the disclosure duty, enforced by the channel charter-scan, replaces the keyless
  impossibility). Private persons are excluded/consent-gated (former G3, re-anchored
  to the catastrophe term + §2(g)).

  R0: every post is DRY-RUN; live posting AS an observatory of a real entity is
  Council/operator-gated (seed-and-grow, ADR-2606281500). This module makes the
  former mirrors GROW + POST + CONVERSE while keeping the only floors that protect
  real third parties (no impersonation) and real people (consent)."
  (:require [etzhayyim.actor :as actor]
            [clojure.string :as str]))

(def observatory-post-lexicon "com.etzhayyim.observatory.post")

(def observatory-catalog
  ;; the levers an observatory actor learns over (what raises its public-record value)
  [{:mechanism :ingest-public-facts :base 1.0}   ; datafy more already-public disclosures
   {:mechanism :narrate-delta       :base 1.0}   ; surface what changed since last beat
   {:mechanism :widen-sources       :base 1.0}   ; add a public source to the mirror set
   {:mechanism :cross-link-peers    :base 1.0}]) ; relate to sibling observatory actors

(defn make-observatory
  "A first-party observatory actor for a domain/entity. `ns` ∈ corp/gov/cable/…;
  `subject` = the public entity it OBSERVES (disclosed, never impersonated). It is
  a full W3 actor: self-keyed, self-evolving, multi-channel, dialogic."
  [{:keys [ns handle subject glyph domain]}]
  (actor/make-actor
   {:handle      handle
    :domain      (or domain (str ns " observatory"))
    :glyph       glyph
    :voice-of    "etzhayyim"
    :is-observatory true
    :subject     subject
    :lexicon-ns  (str "com.etzhayyim.observatory." ns)
    :catalog     observatory-catalog
    :leash-ref   (str "leash:cacao:observatory:" handle)
    :persona     (str "etzhayyim's keyed observatory of the public entity '" subject
                      "' — reports public facts AS etzhayyim, never speaks AS " subject ".")}))

(defn observatory-post!
  "A disclosure-honest observatoryPost (dry-run). The channel charter-scan enforces
  voiceOf=etzhayyim + no-impersonation + the person consent-gate; a private-person
  subject without consent is vetoed (returns :emitted false)."
  [obs text & {:keys [person-subject? consent? targets]}]
  (actor/post! obs observatory-post-lexicon
               {:text text
                :subject (get-in obs [:decl :subject])
                :voiceOf "etzhayyim" :isObservatory true}
               :person-subject? person-subject? :consent? consent?
               :targets (or targets #{:at-proto})))

(defn grow!
  "One GROWTH beat: (1) LEARN from a real reading (e.g. count of new public facts
  ingested this cycle) via the genome loop, then (2) prepare a disclosure-honest
  observatory post for the delta (dry-run). Returns {:actor :recommendation :post}.
  This is what makes a former mirror GROW + POST instead of merely accumulate."
  [obs reading delta-text]
  (let [obs' (actor/learn! obs reading)]
    {:actor obs'
     :recommendation (actor/recommendation obs')
     :post (observatory-post! obs' delta-text)}))

(defn ask
  "Converse with an observatory actor — it RESPONDS (disclosure-honest), the
  dialogic-API surface the keyless mirror could never have. With an injected
  `infer-fn` (etzhayyim.murakumo/infer-text) the reply is Murakumo-inferred
  (fail-open to template); without it, the deterministic template."
  ([obs message] (actor/converse obs message))
  ([obs message infer-fn] (actor/converse obs message infer-fn)))

;; ── migration helper: keyless mirror handle → first-party observatory decl ─────
(defn from-mirror-handle
  "Map an ADR-2606042330 keyless mirror handle (e.g. 'corp-7203' for Toyota) to a
  first-party observatory declaration (W4). The DID stays did:web but gains a
  present-only key + leash; the profile gains voiceOf/isObservatory; the subject is
  disclosed. Pure — the registry regeneration (W4 live) feeds these decls."
  [{:keys [handle ns subject glyph]}]
  {:ns ns :handle handle :subject subject :glyph glyph
   :was :keyless-mirror :now :first-party-observatory
   :did (str "did:web:etzhayyim.com:actor:" handle)
   :key :present-only-leashed :voice-of "etzhayyim" :is-observatory true})
