(ns etzhayyim.pds.xrpc-test
  "com.atproto.* handler invariants: identity resolution + a repo round-trip
  over the in-process MemStore (also exercises store.clj end-to-end)."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.pds.xrpc :as x]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.config :as cfg]))

(deftest resolve-repo-rules
  (is (nil? (x/resolve-repo nil)))
  (testing "a did passes through unchanged"
    (is (= "did:web:foo" (x/resolve-repo "did:web:foo"))))
  (testing "the PDS host resolves to the PDS did"
    (is (= cfg/pds-did (x/resolve-repo cfg/host))))
  (testing "a handle under a user-domain → did:web:<handle>"
    (is (= "did:web:alice.etzhayyim.com" (x/resolve-repo "alice.etzhayyim.com")))
    (is (= "did:web:etzhayyim.com" (x/resolve-repo "etzhayyim.com"))))
  (testing "an unknown identifier passes through"
    (is (= "random.example" (x/resolve-repo "random.example")))))

(deftest identity-and-server-handlers
  (testing "resolveHandle requires a handle"
    (is (= 200 (:status (x/resolve-handle {:handle "did:plc:x"}))))
    (is (= "did:plc:x" (get-in (x/resolve-handle {:handle "did:plc:x"}) [:body "did"])))
    (is (= 400 (:status (x/resolve-handle {})))))
  (testing "describeServer reports the etzhayyim identity"
    (let [r (x/describe-server nil)]
      (is (= 200 (:status r)))
      (is (= cfg/pds-did (get-in r [:body "did"])))))
  (testing "createSession issues a did-bound session token"
    (let [r (x/create-session {:identifier "alice.etzhayyim.com"})]
      (is (= "did:web:alice.etzhayyim.com" (get-in r [:body "did"])))
      (is (re-find #"^etzhayyim-session\." (get-in r [:body "accessJwt"]))))))

(deftest create-record-validation
  (let [s (store/->mem-store)]
    (is (= 400 (:status (x/create-record s {:repo "" :collection "c" :record {}}))))
    (is (= 400 (:status (x/create-record s {:repo "did:web:x" :collection "" :record {}}))))
    (is (= 400 (:status (x/create-record s {:repo "did:web:x" :collection "c" :record nil}))))))

(deftest repo-round-trip
  (let [s    (store/->mem-store)
        repo "did:web:x"
        coll "app.bsky.feed.post"]
    (testing "create → get returns the stored value + a uri/cid"
      (let [rec {"$type" coll "text" "hi"}     ;; atproto records must carry a $type
            c (x/create-record s {:repo repo :collection coll :rkey "rk1" :record rec})]
        (is (= 200 (:status c)))
        (is (string? (get-in c [:body "uri"])))
        (is (string? (get-in c [:body "cid"])))
        (let [g (x/get-record s {:repo repo :collection coll :rkey "rk1"})]
          (is (= 200 (:status g)))
          (is (= rec (get-in g [:body "value"]))))))
    (testing "list-records returns the created record; missing repo → 400"
      (let [l (x/list-records s {:repo repo :collection coll})]
        (is (= 200 (:status l)))
        (is (= 1 (count (get-in l [:body "records"])))))
      (is (= 400 (:status (x/list-records s {:repo repo :collection ""})))))
    (testing "delete → subsequent get is 404"
      (is (= 200 (:status (x/delete-record s {:repo repo :collection coll :rkey "rk1"}))))
      (is (= 404 (:status (x/get-record s {:repo repo :collection coll :rkey "rk1"})))))))

(deftest appview-read-rendering-from-local-log
  (testing "getAuthorFeed + getProfile render an actor's feed/profile from the local kotoba log (Method A)"
    (let [s (store/->mem-store)
          actor "did:web:etzhayyim.com:actor:unspsc-10101500"
          post (fn [rkey text] (store/put-record s actor "app.bsky.feed.post" rkey
                                                 {"$type" "app.bsky.feed.post" "text" text
                                                  "createdAt" "2026-06-25T00:00:00Z"}))]
      (post "a" "first") (post "b" "second")
      ;; getAuthorFeed → AppView-shaped feed of the actor's posts (newest first), no gftd
      (let [resp (x/get-author-feed s {:actor actor})
            feed (get (:body resp) "feed")]
        (is (= 200 (:status resp)))
        (is (= 2 (count feed)))
        (is (= "second" (get-in (first feed) ["post" "record" "text"])) "reverse: newest first")
        (is (= {"did" actor "handle" "unspsc-10101500.etzhayyim.com"}
               (get-in (first feed) ["post" "author"])) "author rendered from did:web:…:actor:<h>")
        (is (str/starts-with? (get-in (first feed) ["post" "uri"]) (str "at://" actor))))
      ;; getProfile → minimal profileView with the authoritative postsCount
      (let [resp (x/get-profile s {:actor actor})]
        (is (= 200 (:status resp)))
        (is (= actor (get (:body resp) "did")))
        (is (= 2 (get (:body resp) "postsCount"))))
      ;; missing actor → 400
      (is (= 400 (:status (x/get-author-feed s {}))))
      (is (= 400 (:status (x/get-profile s {})))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.xrpc-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
