(ns etzhayyim.observatory-sign
  "kotoba-genome W4-live — the concrete MEMBER-SIGN + PUBLISH backend, composing
  kagi (the CACAO leash) + kotoba-lang (the datom:transact XRPC) + the member's
  macOS Keychain key. This is the real implementation behind step 2/4 of the
  member runbook — but it is the MEMBER's to run, never the agent's:

    · the member's key is read from Keychain at runtime (etzhayyim.kotoba-rad-sign
      /keychain-read; service 'etzhayyim.kotoba-rad', account = actor) — the agent
      holds NO key;
    · a revocable datom:transact CACAO leash is minted with the MEMBER's own key
      (kagi.cacao/mint; aud = node operator DID; short TTL = the off-switch);
    · the post is published present-only via kotoba-lang
      (langchain.kotoba-db/kotoba-api :transact!, cacao_b64 + x-kotoba-did) to
      kotobase.net — member-attributed (iss inside the CACAO = the member's did:key).

  The kagi-clj + langchain deps are CROSS-REPO and heavy (BouncyCastle); they are
  resolved LAZILY (requiring-resolve) so the base build/tests never need them. The
  member runs this with the :member-publish deps alias (deps.edn) — e.g. as the
  ETZHAYYIM_MEMBER_SIGN_CMD / ETZHAYYIM_MEMBER_PUBLISH_CMD that observatory:submit
  invokes. Absent the deps / a key / --yes / non-cron → nothing publishes.
  See 90-docs/runbooks/observatory-member-publish.md."
  (:require [clojure.string :as str]))

(def endpoint "https://kotobase.net")            ; the CACAO-gated datom:transact XRPC
(def post-lexicon "com.etzhayyim.observatory.post")

(defn- resolve!
  "Resolve a cross-repo member-publish fn, or throw a clear install hint."
  [sym]
  (or (try (requiring-resolve sym) (catch Throwable _ nil))
      (throw (ex-info (str "member-publish dependency unavailable: " sym
                           " — run with the :member-publish deps alias so kagi-clj + "
                           "langchain are on the classpath (see the runbook). The "
                           "AGENT cannot publish; this is the member's runtime.")
                      {:missing sym}))))

;; ── pure: the leash request + the post record (testable without kagi/langchain) ──
(defn leash-request
  "The revocable datom:transact leash to mint with the member's key. Pure."
  [{:keys [aud graph ttl-seconds] :or {ttl-seconds 900}}]
  {:cap :cap/transact :scope graph :aud aud :ttlSeconds ttl-seconds
   :note "revocable datom:transact CACAO leash; short TTL = the off-switch (ADR-2606111400)"})

(defn post-record
  "The member-signed observatory record. voiceOf/isObservatory are non-negotiable
  (disclosure — never impersonate the real entity). Pure."
  [{:keys [text subject]}]
  {:$type post-lexicon :text text :subject subject
   :voiceOf "etzhayyim" :isObservatory true})

;; ── member runtime (lazy kagi + kotoba-lang) ─────────────────────────────────
(defn member-key
  "Read the member's PKCS8 key b64 from Keychain (nil if absent → no publish)."
  [actor]
  ((resolve! 'etzhayyim.kotoba-rad-sign/keychain-read) actor))

(defn mint-leash
  "Mint the datom:transact CACAO leash with the member's own key (kagi.cacao/mint,
  depth-1 self-mint). Returns {:leash <cacao_b64> :did :graph}."
  [{:keys [priv-b64 pub-b64 aud ttl-seconds] :or {ttl-seconds 900}}]
  (let [load-id (resolve! 'kagi.identity/load-identity)
        mint    (resolve! 'kagi.cacao/mint)
        me      (load-id {:private-b64 priv-b64 :public-b64 pub-b64})]
    {:leash (mint me {:cap :cap/transact :scope (:graph me)}
                  {:aud aud :nonce (str (java.util.UUID/randomUUID))
                   :expiry (str (.plusSeconds (java.time.Instant/now) (long ttl-seconds)))})
     :did (:did me) :graph (:graph me)}))

(defn publish-post!
  "Publish one member-signed observatory post via kotoba-lang (present-only cacao).
  Member-attributed. Requires http-caps injected by the member's runtime."
  [{:keys [leash did graph]} http-caps post]
  (let [conn ((resolve! 'langchain.kotoba-db/kotoba-conn) endpoint graph {:cacao leash :did did})
        api  ((resolve! 'langchain.kotoba-db/kotoba-api) http-caps)]
    ((:transact! api) conn [(post-record post)])))

(defn -sign-and-publish
  "The member's SIGN_CMD+PUBLISH_CMD backend, invoked by observatory:submit only
  when its gate passes (non-cron + --yes + member signer). Reads the member key
  from Keychain, mints the leash, publishes. Args: --actor <h> --aud <did> --text …
  --subject … [--ttl N]. Refuses (nil key → throw) when no member key is present."
  [& args]
  (let [f (fn [k d] (or (second (drop-while #(not= % k) args)) d))
        actor (f "--actor" nil)
        aud   (f "--aud" nil)
        ttl   (Long/parseLong (str (f "--ttl" "900")))
        post  {:text (f "--text" "") :subject (f "--subject" "")}
        dry?  (boolean (some #{"--dry"} args))]
    (if dry?
      ;; --dry PILOT preview: the full signed path (leash + member-attributed
      ;; record) with NO kagi / NO network / NO key — the walk-through the member
      ;; reviews before the real one-actor pilot. Nothing is published.
      (let [lr  (leash-request {:aud aud :graph (str "graph-of:" actor) :ttl-seconds ttl})
            rec (post-record post)
            has-key (boolean (try (member-key actor) (catch Throwable _ nil)))]
        (println "[observatory-sign] PILOT (--dry) — nothing published.")
        (println "  actor:" actor "· member key in Keychain:"
                 (if has-key "present ✓" "absent — seal it first (runbook step 1)"))
        (println "  would mint (kagi.cacao/mint, YOUR key):" (pr-str lr))
        (println "  would post (kotoba-lang transact, member-attributed, AS etzhayyim):" (pr-str rec))
        {:dry true :leash-request lr :record rec :member-key-present has-key})
      ;; real path (member-only): kagi leash + kotoba-lang transact with the key
      (let [priv (member-key actor)]
        (when (str/blank? priv)
          (throw (ex-info "no member key in Keychain — the agent cannot publish; the member must seal their did:key first (runbook step 1)." {:actor actor})))
        (let [ctx (mint-leash {:priv-b64 priv
                               :pub-b64 ((resolve! 'etzhayyim.kotoba-rad-sign/pubkey-hex-from-priv-b64) priv)
                               :aud aud :ttl-seconds ttl})]
          (publish-post! ctx
                         {:http-fn (resolve! 'babashka.http-client/request) :json-write pr-str :json-read identity}
                         post))))))
