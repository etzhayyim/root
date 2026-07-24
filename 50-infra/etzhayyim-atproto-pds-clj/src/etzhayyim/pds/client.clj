(ns etzhayyim.pds.client
  "Minimal PDS client — the actor-side posting path (Path B slice 4).

  An actor (e.g. ibuki's react_loop --live → drainer) uses this to publish a record
  to ITS OWN independent etzhayyim PDS, and any consumer uses it to resolve + verify
  an actor's records from the PDS-served did:web doc. The actor's record is signed by
  the actor's sealed key (PDS-side actorkeys registry); this client submits the record
  and verifies the result against the actor's PUBLISHED multikey — no shared key.

  Stdlib + babashka.http-client; the `transport` is injectable so tests run offline."
  (:require [cheshire.core :as json]
            [babashka.http-client :as http]
            [etzhayyim.pds.keys :as keys]))

(defn default-transport
  "The live HTTP transport: (method url body?) -> {:status :body}. Mirrors store.clj's
  kpost (no-throw, JSON in/out). Tests inject a fake to stay offline."
  [method url body]
  (let [resp (case method
               :post (http/post url {:headers {"content-type" "application/json"}
                                     :body (json/generate-string body)
                                     :throw false})
               :get  (http/get url {:throw false}))]
    {:status (:status resp)
     :body (try (json/parse-string (:body resp)) (catch Exception _ nil))}))

(defn create-record!
  "POST com.atproto.repo.createRecord to `base`. Returns
  {:status :uri :cid :sig :signedBy :author}. The PDS signs with the actor's registry
  key; this client just submits the record (the actor never hands over its key).

  An optional `leash` (an opaque member CACAO leash the actor PRESENTS — never signs;
  etzhayyim.pds.leash) is forwarded in the request so the PDS attributes the autonomous
  write to the consenting member; the verified member is echoed back as :author. Absent
  → the write is unattributed (back-compat)."
  [base {:keys [repo collection record rkey leash]}
   & {:keys [transport]}]
  ;; coalesce nil → default: a destructuring `:or` does NOT fire on an explicit
  ;; `:transport nil` (only on an absent key), and `drain!` passes `:transport transport`
  ;; where transport is nil on the production path (no injected fake) — that nil was
  ;; being called as a fn → NPE. The test suite always injects a transport, so this
  ;; latent break never surfaced there; it only bit the live `bb drain` runtime.
  (let [transport (or transport default-transport)
        {:keys [status body]}
        (transport :post (str base "/xrpc/com.atproto.repo.createRecord")
                   (cond-> {:repo repo :collection collection :record record}
                     rkey  (assoc :rkey rkey)
                     leash (assoc :leash leash)))]
    {:status status :uri (get body "uri") :cid (get body "cid")
     :sig (get body "sig") :signedBy (get body "signedBy")
     :author (get body "author")}))

(defn resolve-actor-multikey
  "GET /actor/<handle>/did.json from `base`; return the actor's #atproto
  publicKeyMultibase, or nil if unresolved."
  [base handle & {:keys [transport] :or {transport default-transport}}]
  (let [{:keys [status body]} (transport :get (str base "/actor/" handle "/did.json") nil)]
    (when (= 200 status)
      (get (first (get body "verificationMethod")) "publicKeyMultibase"))))

(defn verify-record
  "Full consumer round-trip: resolve the actor's multikey from the PDS, then verify a
  record's content-cid signature against it. `cid`/`sig` come from create-record! or
  getRecord. Returns true iff the signature checks out under the PUBLISHED key (so the
  consumer trusts no shared secret — only the actor's resolvable did doc)."
  [base handle cid sig & {:keys [transport] :or {transport default-transport}}]
  (boolean
   (when-let [mk (resolve-actor-multikey base handle :transport transport)]
     (and cid sig (keys/verify-b64 mk (.getBytes ^String cid "UTF-8") sig)))))
