(ns etzhayyim.pds.xrpc-test
  "com.atproto.* handler invariants: identity resolution + a repo round-trip
  over the in-process MemStore (also exercises store.clj end-to-end)."
  (:require [clojure.test :refer [deftest is testing run-tests]]
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

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.xrpc-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
