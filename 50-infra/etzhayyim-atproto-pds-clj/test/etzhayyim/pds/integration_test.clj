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
            [etzhayyim.pds.config :as cfg]
            [etzhayyim.pds.util :as util]))

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

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.integration-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
