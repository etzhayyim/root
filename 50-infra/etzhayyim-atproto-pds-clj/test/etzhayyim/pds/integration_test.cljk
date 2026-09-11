(ns etzhayyim.pds.integration-test
  "End-to-end Path B through the REAL ring handler (server/make-handler), not the
  in-process xrpc fns: an actor posts a signed record OVER THE WIRE (JSON request →
  routing → per-actor sealed signing → JSON response), a consumer resolves the actor's
  did.json THROUGH the handler and verifies the signature against the published key,
  and the post surfaces in both the author feed and the cross-actor discover feed.
  This is the integration seam — routing + body parsing + the /actor/<h>/did.json route
  + dispatch wiring — that the unit suites each exercise only in isolation."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [cheshire.core :as json]
            [etzhayyim.pds.server :as server]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.actorkeys :as ak]
            [etzhayyim.pds.client :as client]
            [etzhayyim.pds.repo :as repo]
            [etzhayyim.pds.keys :as keys]
            [etzhayyim.pds.config :as cfg]
            [etzhayyim.pds.util :as util]))

(defn- b64 ^String [^bytes b] (.encodeToString (java.util.Base64/getEncoder) b))

(def secret "node-secret")
(def handle "unspsc-30202000")

(defn- tmp-dir [] (str (System/getProperty "java.io.tmpdir") "/pds-integ-" (System/nanoTime)))
(defn- rm-rf [dir]
  (let [d (io/file dir)]
    (when (.exists d) (doseq [f (.listFiles d)] (.delete f)) (.delete d))))

(defn- ->handler-transport
  "Adapt a ring handler to the client's (fn [method url body]) transport, driving the
  REAL server over JSON request/response maps exactly as HTTP would — base is empty so
  the client's URLs are the handler's :uri. Response bodies come back parsed (string
  keys), matching the in-process transport the client tests already use."
  [handler]
  (fn [method url body]
    (let [[path q] (str/split url #"\?" 2)
          req (cond-> {:uri path :request-method method}
                q                (assoc :query-string q)
                (= method :post) (assoc :body (json/generate-string body)
                                        :headers {"content-type" "application/json"}))
          {:keys [status body]} (handler req)]
      {:status status
       :body (when-not (str/blank? (str body)) (json/parse-string body))})))

(deftest path-b-end-to-end-through-the-ring-handler
  (testing "post → per-actor sign → serve did.json → verify → author+discover feed, all via make-handler"
    (let [dir (tmp-dir)]
      (try
        (with-redefs [cfg/actor-keys-dir    dir       ; the /actor/<h>/did.json route reads cfg
                      cfg/actor-seal-secret secret
                      cfg/require-auth      false]
          (let [store   (store/->mem-store (ak/registry-signer dir secret))   ; writes signed per-actor
                kp      (repo/gen-keypair)
                handler (server/make-handler store (.getPrivate kp)
                                             (repo/pubkey-multibase (.getPublic kp)) "jwt-secret")
                t       (->handler-transport handler)
                actor   (ak/handle->actor-did handle)
                rec     {"$type" "app.bsky.feed.post" "text" "path B over the wire"
                         "createdAt" "2026-06-26T00:00:00Z"}]
            ;; 1. POST com.atproto.repo.createRecord through the REAL handler → actor-signed
            (let [res (client/create-record! "" {:repo actor :collection "app.bsky.feed.post" :record rec}
                                             :transport t)]
              (is (= 200 (:status res)))
              (is (str/starts-with? (:uri res) "at://"))
              (is (string? (:sig res)) "the PDS returned the actor's signature")
              (is (= (util/content-cid rec) (:cid res)) "the content cid matches the submitted record")
              ;; 2+3. resolve the actor's did.json THROUGH the handler + verify — no shared secret
              (is (= (:signedBy res) (client/resolve-actor-multikey "" handle :transport t))
                  "the sig's key == the key published in the served did.json")
              (is (true?  (client/verify-record "" handle (:cid res) (:sig res) :transport t))
                  "the record sig verifies under the PUBLISHED actor key (full Path B loop over HTTP)")
              (is (false? (client/verify-record "" handle "bafkrei-wrong" (:sig res) :transport t)))
              ;; 4. the post surfaces in getAuthorFeed (query param routed through the wire)
              (let [feed (get (:body (t :get (str "/xrpc/app.bsky.feed.getAuthorFeed?actor=" actor) nil)) "feed")]
                (is (= 1 (count feed)))
                (is (= "path B over the wire" (get-in (first feed) ["post" "record" "text"])))
                (is (= (:sig res) (get-in (first feed) ["post" "sig"])) "the feed surfaces the same actor sig"))
              ;; 5. and in the cross-actor discover feed, carrying its author did
              (let [disc (get (:body (t :get "/xrpc/com.etzhayyim.feed.getDiscover" nil)) "feed")]
                (is (= 1 (count disc)))
                (is (= actor (get-in (first disc) ["post" "author" "did"])))))))
        (finally (rm-rf dir))))))

(deftest unknown-actor-did-json-404-through-the-handler
  (testing "GET /actor/<unknown>/did.json is a 404 via the real handler (a GET never mints a key)"
    (let [dir (tmp-dir)]
      (try
        (with-redefs [cfg/actor-keys-dir dir cfg/actor-seal-secret secret]
          (let [kp (repo/gen-keypair)
                handler (server/make-handler (store/->mem-store) (.getPrivate kp)
                                             (repo/pubkey-multibase (.getPublic kp)) "jwt-secret")
                t (->handler-transport handler)]
            (is (= 404 (:status (t :get "/actor/never-seen/did.json" nil))))))
        (finally (rm-rf dir))))))

(deftest well-known-did-and-describe-server-served
  (testing "the PDS identity surface answers over the wire"
    (let [kp (repo/gen-keypair)
          mb (repo/pubkey-multibase (.getPublic kp))
          handler (server/make-handler (store/->mem-store) (.getPrivate kp) mb "jwt-secret")
          t (->handler-transport handler)
          did (:body (t :get "/.well-known/did.json" nil))
          desc (:body (t :get "/xrpc/com.atproto.server.describeServer" nil))]
      (is (= cfg/pds-did (get did "id")))
      (is (= mb (get (first (get did "verificationMethod")) "publicKeyMultibase")))
      (is (= cfg/pds-did (get desc "did"))))))

(deftest getrepo-commit-is-relay-verifiable-against-the-actor-did-doc
  (testing "a relay GETs the actor's repo CAR + did.json and verifies the COMMIT sig from the published key alone (Path B slice 2, over the wire)"
    (let [dir (tmp-dir)]
      (try
        (with-redefs [cfg/actor-keys-dir    dir
                      cfg/actor-seal-secret secret
                      cfg/require-auth      false]
          (let [store   (store/->mem-store (ak/registry-signer dir secret))
                kp      (repo/gen-keypair)
                handler (server/make-handler store (.getPrivate kp)
                                             (repo/pubkey-multibase (.getPublic kp)) "jwt-secret")
                t       (->handler-transport handler)
                actor   (ak/handle->actor-did handle)
                rec     {"$type" "app.bsky.feed.post" "text" "commit signed by the actor"
                         "createdAt" "2026-06-26T00:00:00Z"}]
            ;; the actor posts (mints its sealed key + signs the record)
            (is (= 200 (:status (client/create-record! "" {:repo actor :collection "app.bsky.feed.post" :record rec}
                                                       :transport t))))
            ;; a RELAY pulls the repo CAR and reads the COMMIT from the CAR's own root
            ;; (the commit is the CAR header root; a P-256 sig is randomized so each build
            ;; differs — the relay must read the root from the CAR it holds, not re-derive)
            (let [car-resp (handler {:uri "/xrpc/com.atproto.sync.getRepo"
                                     :request-method :get :query-string (str "did=" actor)})
                  car-bytes (.readAllBytes ^java.io.InputStream (:body car-resp))
                  {:keys [header blocks]} (repo/car-parse car-bytes)
                  root-cid (repo/cid-str (:etzhayyim.pds.repo/cid (first (get header "roots"))))
                  commit (repo/dag-cbor-decode (get blocks root-cid))
                  ;; the relay reconstructs the signed bytes = the commit WITHOUT its sig
                  unsigned (repo/dag-cbor (dissoc commit "sig"))
                  ;; ...and resolves the actor's PUBLISHED key from /actor/<h>/did.json
                  mk (client/resolve-actor-multikey "" handle :transport t)]
              (is (= actor (get commit "did")) "the commit binds the actor's DID")
              (is (= 64 (alength ^bytes (get commit "sig"))) "a P-256 compact commit sig")
              (is (true? (keys/verify-b64 mk unsigned (b64 (get commit "sig"))))
                  "the repo commit verifies under the actor's published Multikey — no PDS key, no shared secret"))))
        (finally (rm-rf dir))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.integration-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
