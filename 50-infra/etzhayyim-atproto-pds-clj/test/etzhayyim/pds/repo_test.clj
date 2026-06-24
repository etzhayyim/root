(ns etzhayyim.pds.repo-test
  "The com.atproto.sync.* bridge: PDS records → app-aozora-repo MST/commit/CAR."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.xrpc :as xrpc]
            [etzhayyim.pds.repo :as pdsrepo]
            [etzhayyim.pds.server :as server]))

(def repo-id "atproto.etzhayyim.com")

(deftest sync-bridge
  (let [st (store/->mem-store)]
    (xrpc/create-record st {:repo repo-id :collection "app.bsky.feed.post" :record {"text" "one"}})
    (xrpc/put-record st {:repo repo-id :collection "app.bsky.actor.profile" :rkey "self"
                         :record {"displayName" "etz"}})
    (let [did (xrpc/resolve-repo repo-id)]
      (testing "build! materialises an MST + commit from the PDS records"
        (let [{:keys [commit rev]} (pdsrepo/build! st did)]
          (is (string? commit))
          (is (= "r2" rev))))
      (testing "getLatestCommit returns the rebuilt head"
        (let [lc (pdsrepo/get-latest-commit st did)]
          (is (string? (:cid lc)))
          (is (= "r2" (:rev lc)))))
      (testing "getRepo returns a non-empty CARv1"
        (is (pos? (alength ^bytes (pdsrepo/get-repo-car st did))))))))

(deftest sync-over-http
  (let [st (store/->mem-store)
        h (server/make-handler st)
        did (xrpc/resolve-repo repo-id)]
    (xrpc/create-record st {:repo repo-id :collection "app.bsky.feed.post" :record {"text" "hi"}})
    (testing "com.atproto.sync.getLatestCommit over the ring handler (JSON)"
      (let [resp (h {:uri "/xrpc/com.atproto.sync.getLatestCommit" :request-method :get
                     :query-string (str "did=" did)})]
        (is (= 200 (:status resp)))
        (is (str/includes? (:body resp) "rev"))))
    (testing "com.atproto.sync.getRepo over the ring handler serves a CARv1"
      (let [resp (h {:uri "/xrpc/com.atproto.sync.getRepo" :request-method :get
                     :query-string (str "did=" did)})]
        (is (= 200 (:status resp)))
        (is (= "application/vnd.ipld.car" (get-in resp [:headers "content-type"])))))))
