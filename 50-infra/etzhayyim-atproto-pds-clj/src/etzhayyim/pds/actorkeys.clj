(ns etzhayyim.pds.actorkeys
  "Per-actor sealed-key registry — the bridge that makes Path B operational.

  Slices 1-3 gave the primitives: an actor-sealed P-256 key (keys.clj), a signed
  write (store.clj), and a per-actor did:web doc that publishes the key (config.clj).
  This registry ties them to a stable, on-disk identity: given an actor DID it
  returns the SAME key across restarts, a store `signer` for that actor's writes,
  and the actor's did document.

  Custody posture is unchanged (Charter Server-side-signing / no-server-key, the
  kaname/ibuki/tsubasa pattern): the private key never leaves keys.clj as raw bytes;
  on disk it is AES-256-GCM ciphertext sealed under the per-node `secret`
  (MURAKUMO_SEAL_KEY), so the operator sees only ciphertext. The key belongs to the
  actor; no one — operator or platform — can read its private scalar.

  Pure JVM/babashka, no external deps."
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [etzhayyim.pds.keys :as keys]
            [etzhayyim.pds.config :as cfg]))

(defn- safe-name
  "A filesystem-safe file stem for an actor DID (one sealed blob per actor)."
  [actor-did]
  (str/replace (str actor-did) #"[^A-Za-z0-9._-]" "_"))

(defn key-path [dir actor-did]
  (str dir "/" (safe-name actor-did) ".json"))

(defn load-or-create!
  "Return the actor's sealed handle, generating + sealing it on first use and
  reloading the SAME key thereafter (stable identity). On disk: AES-GCM ciphertext
  only. `secret` is the per-node sealing key; nil/blank → refuse (no platform
  fallback key exists)."
  [dir actor-did secret]
  (when (str/blank? (str secret))
    (throw (ex-info "no node sealing secret — set MURAKUMO_SEAL_KEY (no platform fallback)"
                    {:actor actor-did})))
  (let [p (key-path dir actor-did)
        f (io/file p)]
    (if (.exists f)
      (keys/unseal (keys/json->seal (slurp f)) secret)
      (let [k (keys/new-actor-key)]
        (io/make-parents p)
        ;; persist the seal blob + the actor's DID in the clear (both DID and the
        ;; public multikey are public) so the registry can be ENUMERATED without the
        ;; sealing secret (actors-index below); the private key stays ciphertext.
        (spit p (keys/seal->json (assoc (keys/seal k secret) :did actor-did)))
        k))))

(defn multikey-for
  "The actor's published multikey (its public signing key)."
  [dir actor-did secret]
  (:multikey (load-or-create! dir actor-did secret)))

(defn actors-index
  "Enumerate the registry's actors from the on-disk seal blobs WITHOUT the sealing
  secret — each blob carries its DID + public multikey in the clear. Returns
  {\"actors\" [{\"did\" .. \"multikey\" ..} ..]} sorted by DID. A relay/worker uses
  this to discover etzhayyim's actors and verify their records (private keys never
  read). Returns an empty index when the dir is absent."
  [dir]
  (let [d (io/file dir)
        files (when (and dir (.isDirectory d))
                (filter #(.endsWith (.getName %) ".json") (seq (.listFiles d))))]
    {"actors"
     (->> files
          (keep (fn [f]
                  (let [m (try (keys/json->seal (slurp f)) (catch Exception _ nil))]
                    (when (and (:did m) (:multikey m))
                      {"did" (:did m) "multikey" (:multikey m)}))))
          (sort-by #(get % "did"))
          vec)}))

(defn signer-for
  "A store signer (etzhayyim.pds.store/->mem-store etc.) bound to ONE actor's key,
  so each of that actor's writes is signed by the actor itself."
  [dir actor-did secret]
  (keys/record-signer (load-or-create! dir actor-did secret)))

(defn registry-signer
  "A MULTI-ACTOR store signer: `(fn [did ^bytes payload] -> {:sig :multikey})` that
  picks (load-or-creates) the key for the WRITE's own actor `did`. This is what a
  PDS hosting many actors uses, so each actor's writes are signed by ITS OWN key —
  not one shared key. nil/blank secret → refuse (no platform fallback)."
  [dir secret]
  (fn [did ^bytes payload]
    (let [{:keys [multikey] :as sealed} (load-or-create! dir did secret)]
      {:sig (keys/sign-b64 sealed payload) :multikey multikey})))

(defn did-document-for
  "The actor's did:web document, publishing its #atproto Multikey so any verifier
  resolves it and checks the actor's record signatures (Path B, end to end)."
  ([dir actor-did secret] (did-document-for dir actor-did secret nil))
  ([dir actor-did secret handle]
   (cfg/actor-did-document actor-did (multikey-for dir actor-did secret) handle)))

(defn handle->actor-did
  "Canonical actor DID for a handle: did:web:etzhayyim.com:actor:<handle>."
  [handle]
  (str "did:web:etzhayyim.com:actor:" handle))

(defn serve-actor-did
  "Ring-style response {:status :body} serving the per-actor did:web doc, IFF the
  registry is configured (dir + secret) AND the actor already has a sealed key.
  Returns a 404 body when the key is absent, nil when the registry is unconfigured
  (so the caller can fall through). A GET never MINTS a key — only an explicit
  load-or-create! does, so a stray request cannot create identities."
  [dir secret handle]
  (when (and dir (not (str/blank? (str secret))) (not (str/blank? (str handle))))
    (let [actor (handle->actor-did handle)]
      (if (.exists (io/file (key-path dir actor)))
        {:status 200 :body (did-document-for dir actor secret (str handle ".etzhayyim.com"))}
        {:status 404 :body {"error" "NotFound" "message" (str "no key for " actor)}}))))
