(ns etzhayyim.pds.config
  "Independent etzhayyim atproto PDS identity + endpoint configuration.

  This PDS does NOT depend on gftd.ai code or infrastructure. Every outward
  identity value below resolves under *.etzhayyim.com. The canonical state
  substrate is the kotoba Datom log (ADR-2605262130 / ADR-2605312345): records
  are appended as content-addressed EAVT datoms, NOT RisingWave/Postgres.

  All values are overridable via env so the same image can serve a staging
  host. Defaults are the production etzhayyim identity."
  (:require [clojure.string :as str]))

(defn- env
  ([k] (env k nil))
  ([k default] (or (System/getenv k) default)))

(def host
  "The PDS host. did:web is derived from this."
  (env "PDS_HOST" "atproto.etzhayyim.com"))

(def pds-did (str "did:web:" host))

(def user-domains
  "Handle suffixes this PDS issues accounts under. etzhayyim, never gftd."
  (-> (env "PDS_USER_DOMAINS" "etzhayyim.com")
      (str/split #",")
      (->> (map str/trim) (remove str/blank?) vec)))

(def appview-url (env "APPVIEW_URL" "https://bsky.etzhayyim.com"))
(def chat-url    (env "CHAT_URL"    "https://chat.etzhayyim.com"))
(def contact-email (env "PDS_CONTACT" "support@etzhayyim.com"))
(def privacy-url (env "PDS_PRIVACY" "https://etzhayyim.com/privacy"))
(def terms-url   (env "PDS_TERMS"   "https://etzhayyim.com/terms"))

(def port (Integer/parseInt (env "PORT" "8787")))

;; kotoba Datom-log backend. When KOTOBA_URL is set the PDS persists records to
;; the live kotoba engine over its XRPC/HTTP surface; otherwise it falls back to
;; the in-process EAVT datom log (same semantics, single-node, for local/dev).
(def kotoba-url (env "KOTOBA_URL"))
(def kotoba-graph (env "KOTOBA_GRAPH" "etzhayyim-pds"))

;; Durable on-disk datom log. When PDS_STORE_PATH is set (and KOTOBA_URL is not)
;; the PDS write-throughs to an append-only EDN journal at that path and replays
;; it on boot — records survive a restart with no external service.
(def store-path (env "PDS_STORE_PATH"))

;; Stable Ed25519 commit-signing key file (present-only). Persisted so the commit
;; `sig` is stable across restarts and its public key can be pinned in the did doc.
(def signing-key-file (env "PDS_SIGNING_KEY_FILE" "signing-key.edn"))

;; Content-addressed blob store directory (uploadBlob / sync.getBlob / listBlobs).
(def blob-dir (env "PDS_BLOB_DIR" "blobs"))

;; Accounts (handle → did + PBKDF2 password) + opt-in write auth. When
;; PDS_REQUIRE_AUTH is set, write methods require a Bearer session whose `sub` did
;; matches the repo; otherwise writes stay open (network/operator-gated).
(def accounts-file (env "PDS_ACCOUNTS_FILE" "accounts.edn"))
(def require-auth (some? (env "PDS_REQUIRE_AUTH")))

;; Opt-in lexicon-shape validation for known collections (off by default).
(def validate-records (some? (env "PDS_VALIDATE_RECORDS")))

(defn did-document
  "did:web:<host> document. Service endpoints are all etzhayyim-owned — this is
  the structural break from gftd: nothing here points at *.gftd.ai. When the
  signing key's `multibase` is supplied, publish it as the atproto Multikey so a
  relay can verify the repo commit `sig`."
  ([] (did-document nil))
  ([multibase]
   {"@context" ["https://www.w3.org/ns/did/v1"
                "https://w3id.org/security/multikey/v1"]
    "id" pds-did
    "alsoKnownAs" [(str "https://" host)]
    "verificationMethod" (if multibase
                           [{"id" (str pds-did "#atproto")
                             "type" "Multikey"
                             "controller" pds-did
                             "publicKeyMultibase" multibase}]
                           [])
    "service"
    [{"id" "#atproto_pds"
      "type" "AtprotoPersonalDataServer"
      "serviceEndpoint" (str "https://" host)}
     {"id" "#bsky_appview"
      "type" "BskyAppView"
      "serviceEndpoint" appview-url}
     {"id" "#bsky_chat"
      "type" "BskyChatService"
      "serviceEndpoint" chat-url}]}))

(defn describe-server
  "com.atproto.server.describeServer payload — independent etzhayyim identity."
  []
  {"availableUserDomains" user-domains
   "did" pds-did
   "inviteCodeRequired" false
   "phoneVerificationRequired" false
   "links" {"privacyPolicy" privacy-url "termsOfService" terms-url}
   "contact" {"email" contact-email}})
