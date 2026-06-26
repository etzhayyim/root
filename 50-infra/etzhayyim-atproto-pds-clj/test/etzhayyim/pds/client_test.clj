(ns etzhayyim.pds.client-test
  "Actor-side posting path: an actor publishes a signed record through the client and
  a consumer resolves+verifies it from the PDS-served did doc — end to end, OFFLINE
  (the transport is wired to the in-process xrpc + actorkeys, no network)."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [etzhayyim.pds.client :as client]
            [etzhayyim.pds.actorkeys :as ak]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.xrpc :as xrpc]
            [etzhayyim.pds.leash :as leash]
            [etzhayyim.pds.config :as cfg]
            [etzhayyim.pds.util :as util]))

(def secret "node-secret")
(def handle "unspsc-10101500")
(def base "https://pds.example")

(defn- tmp-dir []
  (str (System/getProperty "java.io.tmpdir") "/pds-client-" (hash (str (gensym)))))

(defn- rm-rf [dir]
  (let [d (io/file dir)]
    (when (.exists d)
      (doseq [f (.listFiles d)] (.delete f))
      (.delete d))))

;; A fake PDS: routes the client's HTTP calls into the in-process xrpc + actorkeys,
;; backed by a signed mem-store whose signer is the actor's registry key.
(defn- fake-pds [dir]
  (let [actor (ak/handle->actor-did handle)
        st    (store/->mem-store (ak/signer-for dir actor secret))]   ; mints + signs
    (fn [method url body]
      (cond
        (and (= method :post) (str/ends-with? url "createRecord"))
        (xrpc/create-record st body)
        (and (= method :get) (re-find #"/actor/([^/]+)/did\.json" url))
        (ak/serve-actor-did dir secret (second (re-find #"/actor/([^/]+)/did\.json" url)))
        :else {:status 404 :body nil}))))

(deftest post-then-resolve-and-verify-end-to-end
  (testing "actor posts a signed record; a consumer verifies it from the resolved did doc"
    (let [dir       (tmp-dir)
          transport (fake-pds dir)
          actor     (ak/handle->actor-did handle)
          rec       {"$type" "app.bsky.feed.post"
                     "text" "観測を続けている。 [mirror, not advice]"
                     "createdAt" "2026-06-25T00:00:00Z"}]
      (try
        (let [res (client/create-record! base {:repo actor :collection "app.bsky.feed.post" :record rec}
                                         :transport transport)]
          (is (= 200 (:status res)))
          (is (str/starts-with? (:uri res) "at://"))
          (is (string? (:sig res)))
          (is (= (util/content-cid rec) (:cid res)) "client sees the same content cid")
          ;; the consumer resolves the actor's published key and verifies — no shared secret
          (is (= (:signedBy res)
                 (client/resolve-actor-multikey base handle :transport transport)))
          (is (true?  (client/verify-record base handle (:cid res) (:sig res) :transport transport)))
          ;; tampered cid, or an unknown actor, both fail to verify
          (is (false? (client/verify-record base handle "bafkrei-wrong" (:sig res) :transport transport)))
          (is (false? (client/verify-record base "no-such-actor" (:cid res) (:sig res) :transport transport))))
        (finally (rm-rf dir))))))

(deftest actor-presents-leash-write-attributed-to-member
  (testing "actor PRESENTS a member leash through the client → PDS attributes the member (end-to-end)"
    (let [dir       (tmp-dir)
          transport (fake-pds dir)
          actor     (ak/handle->actor-did handle)
          member    (leash/gen-member-key)
          ;; exp far in the future so the PDS's wall-clock `now` accepts it
          presented (leash/issue-leash member {:aud cfg/pds-did :exp 4070908800})
          rec       {"$type" "app.bsky.feed.post" "text" "attributed by consent"}]
      (try
        ;; with a presented leash → response echoes the consenting member as author
        (let [res (client/create-record! base {:repo actor :collection "app.bsky.feed.post"
                                               :record rec :rkey "lz" :leash presented}
                                         :transport transport)]
          (is (= 200 (:status res)))
          (is (string? (:sig res)) "still actor-signed (key path unchanged)")
          (is (= (:did member) (:author res)) "the consenting human is named"))
        ;; without a leash → unattributed (back-compat)
        (let [res (client/create-record! base {:repo actor :collection "app.bsky.feed.post"
                                               :record rec :rkey "lz2"}
                                         :transport transport)]
          (is (= 200 (:status res)))
          (is (nil? (:author res))))
        (finally (rm-rf dir))))))

(deftest verify-record-handles-unresolvable-actor
  (testing "verify-record is false (never throws) when the did doc can't be resolved"
    (let [transport (fn [_ _ _] {:status 404 :body nil})]
      (is (false? (client/verify-record base handle "cid" "sig" :transport transport))))))
