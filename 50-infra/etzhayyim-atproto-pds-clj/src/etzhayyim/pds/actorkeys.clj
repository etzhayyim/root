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
        (spit p (keys/seal->json (keys/seal k secret)))
        k))))

(defn multikey-for
  "The actor's published multikey (its public signing key)."
  [dir actor-did secret]
  (:multikey (load-or-create! dir actor-did secret)))

(defn signer-for
  "A store signer (etzhayyim.pds.store/->mem-store etc.) bound to this actor's key,
  so each of the actor's writes is signed by the actor itself."
  [dir actor-did secret]
  (keys/record-signer (load-or-create! dir actor-did secret)))

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
