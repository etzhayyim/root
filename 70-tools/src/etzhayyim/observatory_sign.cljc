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

  The kagi-clj + langchain deps are CROSS-REPO and heavy (BouncyCastle); an explicit
  member-owned host adapter supplies them so the base build/tests never need them. The
  member runs the host namespace with member-publish.deps.edn — e.g. as the
  ETZHAYYIM_MEMBER_SIGN_CMD / ETZHAYYIM_MEMBER_PUBLISH_CMD that observatory:submit
  invokes. Absent the deps / a key / --yes / non-cron → nothing publishes.
  See 90-docs/runbooks/observatory-member-publish.md."
  (:require [clojure.string :as str]))

(def endpoint "https://kotobase.net")            ; the CACAO-gated datom:transact XRPC
(def post-lexicon "com.etzhayyim.observatory.post")

(defn- capability! [caps k]
  (let [f (get caps k)]
    (if (fn? f)
      f
      (throw (ex-info (str "member-publish capability unavailable: " k
                           " — run the member-owned host adapter. The agent cannot publish.")
                      {:missing-capability k})))))

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
(defn member-key-with
  "Read the member's PKCS8 key b64 from Keychain (nil if absent → no publish)."
  [caps actor]
  ((capability! caps :keychain-read) actor))

(defn member-key [actor]
  (member-key-with {} actor))

(defn mint-leash-with
  "Mint the datom:transact CACAO leash with the member's own key (kagi.cacao/mint,
  depth-1 self-mint). Returns {:leash <cacao_b64> :did :graph}."
  [caps {:keys [priv-b64 pub-b64 aud ttl-seconds] :or {ttl-seconds 900}}]
  (let [load-id (capability! caps :load-identity)
        mint    (capability! caps :mint-cacao)
        nonce   ((capability! caps :nonce))
        expiry  ((capability! caps :expiry) ttl-seconds)
        me      (load-id {:private-b64 priv-b64 :public-b64 pub-b64})]
    {:leash (mint me {:cap :cap/transact :scope (:graph me)}
                  {:aud aud :nonce nonce :expiry expiry})
     :did (:did me) :graph (:graph me)}))

(defn mint-leash [request]
  (mint-leash-with {} request))

(defn publish-post-with!
  "Publish one member-signed observatory post via kotoba-lang (present-only cacao).
  Member-attributed. Requires http-caps injected by the member's runtime."
  [caps {:keys [leash did graph]} post]
  (let [conn ((capability! caps :kotoba-conn) endpoint graph {:cacao leash :did did})
        api  ((capability! caps :kotoba-api)
              {:http-fn (capability! caps :http-request)
               :json-write pr-str :json-read identity})]
    ((:transact! api) conn [(post-record post)])))

(defn publish-post! [ctx _http-caps post]
  (publish-post-with! {} ctx post))

(defn sign-and-publish-with
  "The member's SIGN_CMD+PUBLISH_CMD backend, invoked by observatory:submit only
  when its gate passes (non-cron + --yes + member signer). Reads the member key
  from Keychain, mints the leash, publishes. Args: --actor <h> --aud <did> --text …
  --subject … [--ttl N]. Refuses (nil key → throw) when no member key is present."
  [caps & args]
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
            has-key (boolean (try (member-key-with caps actor) (catch Throwable _ nil)))]
        (println "[observatory-sign] PILOT (--dry) — nothing published.")
        (println "  actor:" actor "· member key in Keychain:"
                 (if has-key "present ✓" "absent — seal it first (runbook step 1)"))
        (println "  would mint (kagi.cacao/mint, YOUR key):" (pr-str lr))
        (println "  would post (kotoba-lang transact, member-attributed, AS etzhayyim):" (pr-str rec))
        {:dry true :leash-request lr :record rec :member-key-present has-key})
      ;; real path (member-only): kagi leash + kotoba-lang transact with the key
      (let [priv (member-key-with caps actor)]
        (when (str/blank? priv)
          (throw (ex-info "no member key in Keychain — the agent cannot publish; the member must seal their did:key first (runbook step 1)." {:actor actor})))
        (let [ctx (mint-leash-with
                   caps {:priv-b64 priv
                         :pub-b64 ((capability! caps :public-key-from-private) priv)
                         :aud aud :ttl-seconds ttl})]
          (publish-post-with! caps ctx post))))))

(defn -sign-and-publish [& args]
  (apply sign-and-publish-with {} args))

(defn -main
  "Portable namespaces do not assemble signing authority. Run the member-owned
  `etzhayyim.observatory-sign-host` entrypoint with member-publish.deps.edn."
  [& _args]
  (throw (ex-info "member-owned host adapter required; run etzhayyim.observatory-sign-host"
                  {:capability :member-publish})))
