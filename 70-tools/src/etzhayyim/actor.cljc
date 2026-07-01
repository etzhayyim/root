(ns etzhayyim.actor
  "kotoba-genome W3 — the shared actor behavior library (ADR-2606302205 D3).

  Composes the once-implemented behaviors into ONE inheritable actor runtime:
    · identity  — did:key present-only + member-CACAO leash ref (ADR-2606111400),
                  channel-agnostic (the same identity signs AT/email/X/Telegram).
    · social    — egress via etzhayyim.channel (the W1 driver registry).
    · evolution — the etzhayyim.genome closed learning loop (the W2 lib).
    · dialog    — converse (a disclosure-honest response; Murakumo-inference hook).
    · gate-kit  — the Charter content/disclosure scan (channel/charter-scan), run
                  before every post AND every converse.

  An actor DECLARES what it is (handle, domain, voice, catalog, lexicons); it
  INHERITS how it lives. Changing a capability — a new channel, a new gate, a
  learning improvement — propagates to every actor by library change, not by
  editing N manifests (the audit's 'behavior reuse by copy' gap).

  Reference runtime: the upstream 40-engine/kotoba kotodama-evolver is deferred
  (external submodule); this clj path is the runnable reference per ADR D3. .cljc
  (JVM/bb/cljs/WASM)."
  (:require [etzhayyim.channel :as channel]
            [etzhayyim.genome :as genome]
            [clojure.string :as str]))

;; decl = {:handle "ooyake" :domain "world-government" :glyph "公"
;;         :voice-of "etzhayyim" :is-observatory true
;;         :lexicon-ns "com.etzhayyim.ooyake" :catalog [{:mechanism :m :base 1.0} …]
;;         :leash-ref "leash:cacao:…" :persona "…" :subject "…"?}
(defrecord Actor [decl state])

(defn make-actor
  "Born self-keyed, self-evolving, multi-channel, dialogic from a declaration."
  [decl]
  (->Actor decl genome/empty-state))

(defn identity-of
  "did:key present-only + member-CACAO leash (the revocable off-switch). NOT a
  platform-held custodial key (ADR-2605231525/2606111400); channel-agnostic."
  [{:keys [decl]}]
  {:did      (str "did:web:etzhayyim.com:actor:" (:handle decl))
   :did-key  :present-only
   :leash    (:leash-ref decl)
   :voice-of (:voice-of decl)})

;; ── evolution ────────────────────────────────────────────────────────────────
(defn learn!
  "One closed evolution beat on a REAL reading (genome). Returns the new actor;
  the recommendation is dry-run (never auto-applied — ADR-2605240200)."
  [actor reading]
  (update actor :state genome/beat (:catalog (:decl actor)) reading))

(defn recommendation [actor] (get-in actor [:state :recommendation]))

;; ── social ───────────────────────────────────────────────────────────────────
(defn envelope
  "Channel-neutral emit envelope carrying the actor's DISCLOSURE (voiceOf /
  isObservatory) + the person-protection flags. claims-to-be-entity is always
  false — an actor never impersonates a real entity (D4)."
  [actor lexicon content & {:keys [targets person-subject? consent?]}]
  (let [d (:decl actor)]
    (cond-> {:actor (:handle d) :lexicon lexicon :content content
             :voice-of (:voice-of d) :is-observatory (boolean (:is-observatory d))
             :claims-to-be-entity false
             :person-subject? (boolean person-subject?) :consent? (boolean consent?)
             :identity-ref (:leash-ref d) :dry-run true}
      targets (assoc :targets targets))))

(defn post!
  "Social egress via the channel registry — the scan-before-emit floors
  (impersonation / disclosure / person-consent) are enforced by channel/emit!."
  [actor lexicon content & opts]
  (channel/emit! (apply envelope actor lexicon content opts)))

;; ── dialog ───────────────────────────────────────────────────────────────────
(defn converse-prompt
  "The disclosure-honest system+user messages for the Murakumo fleet — the actor
  speaks AS etzhayyim's <domain> observatory, grounded in public record, NEVER as
  the real entity, NEVER targeting a person."
  [d message]
  [{:role "system"
    :content (str "あなたは etzhayyim の " (:domain d) " 観測アクター（handle: " (:handle d)
                  "）。voiceOf=etzhayyim として、公開記録に基づく観測を簡潔に一〜二文で述べる。"
                  (when (:subject d) (str "観測対象は『" (:subject d) "』だが、決してその実体になりすまさず、その一人称で語らない。"))
                  " 個人を標的化しない。前置き・ローマ字・記号装飾は禁止。")}
   {:role "user" :content (str/trim (str message))}])

(defn converse
  "Disclosure-honest reply to a message. The gate-kit runs first (an actor never
  speaks AS the real entity, never targets a person). With an injected `infer-fn`
  (e.g. etzhayyim.murakumo/infer-text) the reply is Murakumo-inferred (G6, fail-open
  to the template — never a non-Murakumo endpoint); without it (default/tests) the
  deterministic template is used. actor.cljc stays network-free — the live wiring
  injects the fleet. Returns {:reply … :inference :murakumo|:template :blocked? …}."
  ([actor message] (converse actor message nil))
  ([actor message infer-fn]
   (let [d (:decl actor)
         scan (channel/charter-scan
               {:voice-of (:voice-of d) :is-observatory (:is-observatory d)
                :claims-to-be-entity false :targets-person? false})]
     (if (= :veto (:verdict scan))
       {:from (:handle d) :blocked? true :scan scan}
       (let [inferred (when infer-fn
                        (try (let [t (infer-fn (converse-prompt d message))]
                               (when (and t (seq (str t))) (str t)))
                             (catch #?(:clj Throwable :cljs :default) _ nil)))
             tmpl (str (when (:glyph d) (str (:glyph d) " ")) (:handle d)
                       " (etzhayyim の " (:domain d) " 観測アクター): "
                       "「" (str/trim (str message)) "」 — 公開記録に基づき観測を返します"
                       (when (:subject d) (str "（subject: " (:subject d) "、なりすましではありません）"))
                       "。")]
         {:from (:handle d) :blocked? false
          :voice-of (:voice-of d) :is-observatory (boolean (:is-observatory d))
          :reply (or inferred tmpl)
          :persona (:persona d)
          :inference (if inferred :murakumo :template)})))))

;; ── introspection ────────────────────────────────────────────────────────────
(defn summary [actor]
  {:identity (identity-of actor)
   :domain (get-in actor [:decl :domain])
   :beat (get-in actor [:state :beat])
   :recommendation (recommendation actor)})
