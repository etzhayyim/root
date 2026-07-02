;; etzhayyim.aozora-identity — the actor's self-sovereign aozora identity +
;; app-aozora-pds session auth for the central CLI (`bb aozora:deploy` /
;; `e7m actor identify`). No special per-actor operation: the CLI loads (or
;; first-run generates) the actor's OWN Ed25519 did:key and authenticates the
;; PDS write itself.
;;
;; Identity file: `.{actor}/identity.edn` = {:private-b64 (PKCS8) :public-b64
;; (X.509)} — the EXACT format the per-actor publishers persist
;; (tashikame.cacao / kouhou.cacao `load-or-create-identity!`), so the central
;; CLI addresses the SAME did:key aozora repo the actor already published.
;; Resolution order: AOZORA_IDENTITY env → the published actor repo
;; (../../etzhayyim/com-etzhayyim-<name>/.<name>/identity.edn) → the monorepo
;; actor (20-actors/<name>/.<name>/identity.edn). The file is gitignored —
;; NEVER commit a private key. no-server-key: this is the actor's own
;; self-generated did:key held off-platform (ADR-2605231525 clarification),
;; not a custodial platform key.
;;
;; Auth flow (proven live 2026-07-02, tashikame/kouhou PR #3 each):
;;   mint CACAO (iss = the actor's own did:key; cacao.core over the raw seed)
;;     → POST com.atproto.server.createSession {cacao}  → HS256 session JWT
;;     → com.atproto.repo.createRecord (Bearer JWT, repo = the did:key)
;; app-aozora-pds enforces session DID == repo DID; the old
;; CACAO-Bearer-at-createRecord model returns 403 there.
(ns etzhayyim.aozora-identity
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [cheshire.core :as json]
            [babashka.http-client :as http]
            [cacao.core :as cacao]
            [ed25519.core :as ed])
  (:import [java.security KeyPairGenerator]
           [java.time Instant]
           [java.time.temporal ChronoUnit]
           [java.util Arrays Base64 UUID]))

(defn- b64->bytes ^bytes [^String s] (.decode (Base64/getDecoder) s))
(defn- bytes->b64 ^String [^bytes b] (.encodeToString (Base64/getEncoder) b))

(defn- last-32 ^bytes [^bytes b]
  (when (>= (alength b) 32)
    (Arrays/copyOfRange b (- (alength b) 32) (alength b))))

(defn identity-paths
  "Candidate identity files for `actor`, published repo first (that is where
   the already-live per-actor identities sit). Relative to etzhayyim/root."
  [actor]
  [(str "../../etzhayyim/com-etzhayyim-" actor "/." actor "/identity.edn")
   (str "20-actors/" actor "/." actor "/identity.edn")])

(defn resolve-identity-path
  "AOZORA_IDENTITY env → existing identity file → first-run creation target
   (whichever actor home dir exists). nil when the actor has no home at all."
  [actor]
  (or (some-> (System/getenv "AOZORA_IDENTITY") not-empty)
      (let [paths (identity-paths actor)]
        (or (first (filter #(.exists (io/file %)) paths))
            (first (filter #(-> (io/file %) .getAbsoluteFile
                                .getParentFile .getParentFile .exists)
                           paths))))))

(defn- identity-from-pkcs8
  "{:private-b64 :public-b64} → {:did :seed}. The raw Ed25519 seed is the last
   32 bytes of the (48-byte) PKCS8 encoding; when :public-b64 is present the
   seed-derived did:key is cross-checked against the X.509 public key."
  [{:keys [private-b64 public-b64]} path]
  (let [seed (or (some-> private-b64 b64->bytes last-32)
                 (throw (ex-info "unreadable identity (no PKCS8 :private-b64)"
                                 {:path path})))
        did (ed/did-key-from-seed seed)
        did-pub (some-> public-b64 b64->bytes last-32 ed/did-key-from-pub)]
    (when (and did-pub (not= did did-pub))
      (throw (ex-info "identity seed/public-key mismatch" {:path path})))
    {:did did :seed seed :path path}))

(defn existing-identity
  "Load the actor's persisted identity, or nil when none exists yet."
  [actor]
  (let [path (resolve-identity-path actor)]
    (when (and path (.exists (io/file path)))
      (identity-from-pkcs8 (edn/read-string (slurp path)) path))))

(defn load-or-create-identity!
  "Per-actor key: load the actor's persisted Ed25519 identity, or generate +
   persist one on first run (only the b64 key material is stored, per-actor
   publisher format). Returns {:did :seed :path :created?}."
  [actor]
  (let [path (resolve-identity-path actor)]
    (when-not path
      (throw (ex-info (str "no identity home for " actor " (neither the "
                           "published repo nor 20-actors/" actor " exists)")
                      {:actor actor})))
    (or (existing-identity actor)
        (let [kp (.generateKeyPair (KeyPairGenerator/getInstance "Ed25519"))
              priv-enc (.getEncoded (.getPrivate kp))
              pub-enc (.getEncoded (.getPublic kp))
              f (io/file path)]
          (some-> (.getParentFile (.getAbsoluteFile f)) .mkdirs)
          (spit f (pr-str {:private-b64 (bytes->b64 priv-enc)
                           :public-b64 (bytes->b64 pub-enc)}))
          (assoc (identity-from-pkcs8 {:private-b64 (bytes->b64 priv-enc)
                                       :public-b64 (bytes->b64 pub-enc)} path)
                 :created? true)))))

(defn mint-session-cacao
  "A 1-hour self-minted CACAO for `pds` (iss = the actor's own did:key)."
  [{:keys [did seed]} pds]
  (let [now (.truncatedTo (Instant/now) ChronoUnit/SECONDS)]
    (:cacao-b64
     (cacao/mint {:seed seed :aud pds
                  :iat (str now)
                  :exp (str (.plusSeconds now 3600))
                  :nonce (str (UUID/randomUUID))
                  :resources ["kotoba://op/datom:transact"
                              (str "kotoba://graph/" did)]}))))

(defn create-session!
  "createSession(self-CACAO) → {:jwt :did :handle}. Throws on auth failure."
  [pds identity]
  (let [resp (http/post (str pds "/xrpc/com.atproto.server.createSession")
                        {:headers {"content-type" "application/json"}
                         :body (json/generate-string
                                {:cacao (mint-session-cacao identity pds)})
                         :throw false})
        body (try (json/parse-string (:body resp)) (catch Exception _ nil))
        jwt (get body "accessJwt")]
    (when-not (and (= 200 (:status resp)) jwt)
      (throw (ex-info "aozora createSession failed"
                      {:pds pds :status (:status resp) :body (:body resp)})))
    {:jwt jwt :did (get body "did") :handle (get body "handle")}))

(defn create-record!
  "createRecord under the session JWT (repo = the actor's did:key; the PDS
   enforces session DID == repo DID). Returns {:status :uri :cid :body}."
  [pds jwt {:keys [repo collection rkey record leash]}]
  (let [resp (http/post (str pds "/xrpc/com.atproto.repo.createRecord")
                        {:headers {"content-type" "application/json"
                                   "authorization" (str "Bearer " jwt)}
                         :body (json/generate-string
                                (cond-> {:repo repo :collection collection
                                         :record record}
                                  rkey (assoc :rkey rkey)
                                  leash (assoc :leash leash)))
                         :throw false})
        body (try (json/parse-string (:body resp)) (catch Exception _ nil))]
    {:status (:status resp) :uri (get body "uri") :cid (get body "cid")
     :body (:body resp)}))
