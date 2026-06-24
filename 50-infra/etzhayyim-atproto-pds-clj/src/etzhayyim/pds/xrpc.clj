(ns etzhayyim.pds.xrpc
  "com.atproto.* XRPC method handlers. Pure functions of (store, params) →
  {:status n :body m}; the HTTP layer (server.clj) handles transport. No vendor
  SDK, no gftd code — the method surface is implemented directly against the
  kotoba Datom-log store."
  (:require [clojure.string :as str]
            [etzhayyim.pds.config :as cfg]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.util :as util]))

(defn- ok [body] {:status 200 :body body})
(defn- err [status error message]
  {:status status :body {"error" error "message" message}})

(defn resolve-repo
  "Resolve a `repo` identifier (did or handle) to a did. A handle under a
  configured user-domain resolves to did:web:<handle>; a did passes through; the
  PDS host itself maps to the PDS did."
  [repo]
  (cond
    (nil? repo) nil
    (str/starts-with? repo "did:") repo
    (= repo cfg/host) cfg/pds-did
    (some #(str/ends-with? repo (str "." %)) cfg/user-domains) (str "did:web:" repo)
    (contains? (set cfg/user-domains) repo) (str "did:web:" repo)
    :else repo))

;; ── identity ─────────────────────────────────────────────────────────────────
(defn resolve-handle [{:keys [handle]}]
  (if-let [did (and handle (resolve-repo handle))]
    (ok {"did" did})
    (err 400 "InvalidRequest" "handle is required")))

;; ── server ───────────────────────────────────────────────────────────────────
(defn describe-server [_] (ok (cfg/describe-server)))

(defn create-session [{:keys [identifier]}]
  ;; Minimal: issues a non-cryptographic session bound to the resolved did. Real
  ;; JWT/OAuth issuance is staged (README) — kept deliberately small, not copied.
  (let [did (or (resolve-repo identifier) cfg/pds-did)]
    (ok {"did" did
         "handle" (or identifier cfg/host)
         "accessJwt" (str "etzhayyim-session." (util/content-cid did))
         "refreshJwt" (str "etzhayyim-refresh." (util/content-cid (str did "/r")))})))

;; ── repo ─────────────────────────────────────────────────────────────────────
(defn create-record [store {:keys [repo collection record rkey]}]
  (let [did (resolve-repo repo)]
    (cond
      (or (str/blank? repo) (nil? did)) (err 400 "InvalidRequest" "repo is required")
      (str/blank? collection) (err 400 "InvalidRequest" "collection is required")
      (nil? record) (err 400 "InvalidRequest" "record is required")
      :else
      (let [rkey (if (str/blank? rkey) (util/tid) rkey)
            {:keys [uri cid]} (store/put-record store did collection rkey record)]
        (ok {"uri" uri "cid" cid})))))

(defn put-record [store {:keys [repo collection rkey record]}]
  (let [did (resolve-repo repo)]
    (cond
      (or (str/blank? repo) (nil? did)) (err 400 "InvalidRequest" "repo is required")
      (str/blank? collection) (err 400 "InvalidRequest" "collection is required")
      (str/blank? rkey) (err 400 "InvalidRequest" "rkey is required")
      (nil? record) (err 400 "InvalidRequest" "record is required")
      :else
      (let [{:keys [uri cid]} (store/put-record store did collection rkey record)]
        (ok {"uri" uri "cid" cid})))))

(defn get-record [store {:keys [repo collection rkey]}]
  (let [did (resolve-repo repo)]
    (if-let [r (and did (not (str/blank? collection)) (not (str/blank? rkey))
                    (store/get-record store did collection rkey))]
      (ok {"uri" (:uri r) "cid" (:cid r) "value" (:value r)})
      (err 404 "RecordNotFound" "record not found"))))

(defn delete-record [store {:keys [repo collection rkey]}]
  (let [did (resolve-repo repo)]
    (cond
      (or (str/blank? repo) (nil? did)) (err 400 "InvalidRequest" "repo is required")
      (str/blank? collection) (err 400 "InvalidRequest" "collection is required")
      (str/blank? rkey) (err 400 "InvalidRequest" "rkey is required")
      :else (do (store/delete-record store did collection rkey) (ok {})))))

(defn list-records [store {:keys [repo collection limit cursor]}]
  (let [did (resolve-repo repo)
        limit (let [n (try (Integer/parseInt (str (or limit "50"))) (catch Exception _ 50))]
                (max 1 (min 100 n)))]
    (if (or (nil? did) (str/blank? collection))
      (err 400 "InvalidRequest" "repo and collection are required")
      (let [{:keys [records cursor]} (store/list-records store did collection limit cursor)]
        (ok (cond-> {"records" (mapv (fn [r] {"uri" (:uri r) "cid" (:cid r) "value" (:value r)}) records)}
              cursor (assoc "cursor" cursor)))))))

(defn describe-repo [store {:keys [repo]}]
  (let [did (resolve-repo repo)]
    (if (nil? did)
      (err 400 "InvalidRequest" "repo is required")
      (let [{:keys [collections count]} (store/describe-repo store did)]
        (ok {"did" did
             "handle" repo
             "didDoc" (cfg/did-document)
             "collections" collections
             "handleIsCorrect" true
             "recordCount" count})))))

;; ── account lifecycle (ADR-2606242330 P1) ────────────────────────────────────

(defn- under-user-domain? [handle]
  (boolean (and handle (some #(or (= handle %) (str/ends-with? handle (str "." %)))
                             cfg/user-domains))))

(defn- session-tokens [did]
  {"accessJwt"  (str "etzhayyim-session." (util/content-cid did))
   "refreshJwt" (str "etzhayyim-refresh." (util/content-cid (str did "/r")))})

(defn create-account
  "com.atproto.server.createAccount — register a handle under a user-domain and
  open its repo. Real JWT/OAuth issuance stays staged (README #3); the session
  token shape mirrors createSession."
  [store {:keys [handle did email]}]
  (cond
    (str/blank? handle) (err 400 "InvalidRequest" "handle is required")
    (not (under-user-domain? handle))
    (err 400 "InvalidHandle"
         (str "handle must be under one of: " (str/join ", " cfg/user-domains)))
    :else
    (let [did (if (str/blank? did) (str "did:web:" handle) did)
          res (store/create-account store did handle email)]
      (if (:error res)
        (err 400 "HandleNotAvailable" (:error res))
        (ok (merge {"did" did "handle" handle} (session-tokens did)))))))

(defn get-session
  "com.atproto.server.getSession — reflect the account for an identifier (did or
  handle). Auth is stubbed (README #3); identity is taken from the param here."
  [store {:keys [identifier handle did]}]
  (let [ident (or identifier handle did)
        acct (and (not (str/blank? ident)) (store/get-account store ident))]
    (if acct
      (ok {"did" (:did acct) "handle" (:handle acct) "active" true})
      (err 400 "InvalidRequest" "no account for identifier"))))

(defn upload-blob
  "com.atproto.repo.uploadBlob — store raw bytes, return a blob ref. `did` is the
  uploading repo (from the stubbed session / optional param)."
  [store did mime ^bytes data]
  (if (or (nil? data) (zero? (alength data)))
    (err 400 "InvalidRequest" "blob body is empty")
    (let [{:keys [cid mimeType size]} (store/put-blob store did mime data)]
      (ok {"blob" {"$type" "blob"
                   "ref" {"$link" cid}
                   "mimeType" mimeType
                   "size" size}}))))

(defn get-blob
  "com.atproto.sync.getBlob — return the raw blob. The HTTP layer serves
  `:blob` as the raw body with its mimeType; JSON errors use the usual shape."
  [store {:keys [cid]}]
  (if (str/blank? cid)
    (err 400 "InvalidRequest" "cid is required")
    (if-let [b (store/get-blob store cid)]
      {:status 200 :blob b}
      (err 404 "BlobNotFound" "blob not found"))))
