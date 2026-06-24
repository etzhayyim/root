(ns etzhayyim.pds.server-test
  "Round-trip tests for the independent etzhayyim PDS: identity is etzhayyim (no
  gftd), and the datom-log store survives create/get/list/put/delete."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [cheshire.core :as json]
            [etzhayyim.pds.config :as cfg]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.repo :as repo]
            [etzhayyim.pds.xrpc :as xrpc]
            [etzhayyim.pds.server :as server]))

(def repo cfg/host) ;; "atproto.etzhayyim.com"

(deftest independent-identity
  (testing "describeServer is etzhayyim, never gftd"
    (let [d (cfg/describe-server)
          s (json/generate-string d)]
      (is (= "did:web:atproto.etzhayyim.com" (get d "did")))
      (is (= ["etzhayyim.com"] (get d "availableUserDomains")))
      (is (not (str/includes? s "gftd")))))
  (testing "did document service endpoints are all etzhayyim-owned"
    (let [s (json/generate-string (cfg/did-document))]
      (is (str/includes? s "atproto.etzhayyim.com"))
      (is (not (str/includes? s "gftd"))))))

(deftest record-round-trip
  (let [st (store/->mem-store)
        coll "app.bsky.feed.post"
        rec {"text" "shalom from etzhayyim" "createdAt" "2026-06-17T00:00:00Z"}
        created (xrpc/create-record st {:repo repo :collection coll :record rec})
        uri (get-in created [:body "uri"])
        rkey (last (str/split uri #"/"))]
    (testing "createRecord returns an at-uri + cid"
      (is (= 200 (:status created)))
      (is (str/starts-with? uri "at://did:web:atproto.etzhayyim.com/"))
      (is (str/starts-with? (get-in created [:body "cid"]) "b")))
    (testing "getRecord returns the stored value"
      (let [g (xrpc/get-record st {:repo repo :collection coll :rkey rkey})]
        (is (= 200 (:status g)))
        (is (= rec (get-in g [:body "value"])))))
    (testing "listRecords includes the record"
      (let [l (xrpc/list-records st {:repo repo :collection coll})]
        (is (= 200 (:status l)))
        (is (= 1 (count (get-in l [:body "records"]))))))
    (testing "putRecord overwrites at a fixed rkey"
      (let [p (xrpc/put-record st {:repo repo :collection coll :rkey "self"
                                   :record {"displayName" "etzhayyim"}})
            g (xrpc/get-record st {:repo repo :collection coll :rkey "self"})]
        (is (= 200 (:status p)))
        (is (= {"displayName" "etzhayyim"} (get-in g [:body "value"])))))
    (testing "deleteRecord tombstones the record"
      (xrpc/delete-record st {:repo repo :collection coll :rkey rkey})
      (let [g (xrpc/get-record st {:repo repo :collection coll :rkey rkey})]
        (is (= 404 (:status g)))))
    (testing "describeRepo reports collections"
      (let [d (xrpc/describe-repo st {:repo repo})]
        (is (= 200 (:status d)))
        (is (some #{coll} (get-in d [:body "collections"])))))))

(deftest handle-resolution
  (testing "handle under user-domain resolves to did:web"
    (is (= "did:web:alice.etzhayyim.com"
           (get-in (xrpc/resolve-handle {:handle "alice.etzhayyim.com"}) [:body "did"]))))
  (testing "a did passes through"
    (is (= "did:web:atproto.etzhayyim.com" (xrpc/resolve-repo "did:web:atproto.etzhayyim.com")))))

(deftest http-layer
  (testing "the ring handler serves did.json (with signing key) and describeServer"
    (let [kp (repo/gen-keypair)
          mb (repo/pubkey-multibase (.getPublic kp))
          h (server/make-handler (store/->mem-store) (.getPrivate kp) mb)
          did-resp (h {:uri "/.well-known/did.json" :request-method :get})
          desc (h {:uri "/xrpc/com.atproto.server.describeServer" :request-method :get})]
      (is (= 200 (:status did-resp)))
      (is (str/includes? (:body did-resp) "did:web:atproto.etzhayyim.com"))
      (is (str/includes? (:body did-resp) mb))                 ; signing key published
      (is (str/includes? (:body did-resp) "Multikey"))
      (is (= 200 (:status desc)))
      (is (not (str/includes? (:body desc) "gftd"))))))

(deftest signing-key-published-and-stable
  (testing "pubkey multibase is a did:key Ed25519 (z6Mk…)"
    (is (str/starts-with? (repo/pubkey-multibase (.getPublic (repo/gen-keypair))) "z6Mk")))
  (testing "the signing key file is created once and reloaded stably"
    (let [path (str (System/getProperty "java.io.tmpdir") "/pds-key-" (hash (str (gensym))) ".edn")
          a (repo/load-or-create-keypair path)
          b (repo/load-or-create-keypair path)]    ; reloads the same key
      (is (= (repo/pubkey-multibase (:public a)) (repo/pubkey-multibase (:public b))))
      ;; a commit signed by the reloaded key verifies against the published key
      (let [[_ _ commit] (repo/make-commit cfg/pds-did (repo/block-cid {}) "3kr" nil (:private b))]
        (is (repo/verify (:public a) (repo/dag-cbor (dissoc commit :sig)) (:sig commit))))
      (.delete (clojure.java.io/file path)))))

(deftest durable-store-survives-restart
  (testing "a record written to a durable store is replayed from disk by a fresh store"
    (let [path (str (System/getProperty "java.io.tmpdir") "/pds-durable-" (hash (str (gensym))) ".edn")
          s1 (store/->durable-store path)]
      (store/put-record s1 "did:web:atproto.etzhayyim.com" "app.bsky.feed.post" "3kdur1"
                        {"$type" "app.bsky.feed.post" "text" "durable"})
      (let [s2 (store/->durable-store path)            ; fresh store replays the journal
            got (store/get-record s2 "did:web:atproto.etzhayyim.com" "app.bsky.feed.post" "3kdur1")]
        (is (= "durable" (get (:value got) "text")))
        (.delete (clojure.java.io/file path))))))

(deftest dag-cbor-is-spec-correct
  (testing "empty-map CID matches the canonical IPLD vector"
    (is (= "bafyreigbtj4x7ip5legnfznufuopl4sg4knzc2cof6duas4b3q2fy6swua"
           (repo/cid-str (repo/block-cid {})))))
  (testing "dag-cbor map key order is deterministic"
    (is (= (seq (repo/dag-cbor {:b 2 :a 1})) (seq (repo/dag-cbor {:a 1 :b 2}))))))

(deftest federation-sync-surface
  (testing "getRepo returns a non-empty CAR; getLatestCommit returns a commit cid"
    (let [k (.getPrivate (repo/gen-keypair))
          st (store/->mem-store)]
      (store/put-record st cfg/pds-did "app.bsky.feed.post" "3kfed1" {"$type" "app.bsky.feed.post" "text" "x"})
      (let [h (server/make-handler st k (repo/pubkey-multibase (.getPublic (repo/gen-keypair))))
            car (h {:uri "/xrpc/com.atproto.sync.getRepo" :request-method :get
                    :query-string (str "did=" cfg/pds-did)})
            commit (h {:uri "/xrpc/com.atproto.sync.getLatestCommit" :request-method :get
                       :query-string (str "did=" cfg/pds-did)})
            status (h {:uri "/xrpc/com.atproto.sync.getRepoStatus" :request-method :get
                       :query-string (str "did=" cfg/pds-did)})
            getrec (h {:uri "/xrpc/com.atproto.sync.getRecord" :request-method :get
                       :query-string (str "did=" cfg/pds-did "&collection=app.bsky.feed.post&rkey=3kfed1")})
            blocks (h {:uri "/xrpc/com.atproto.sync.getBlocks" :request-method :get
                       :query-string (str "did=" cfg/pds-did)})]
        (is (= "application/vnd.ipld.car" (get-in car [:headers "content-type"])))
        (is (instance? java.io.InputStream (:body car)))
        (is (str/starts-with? (get (json/parse-string (:body commit)) "cid") "bafyrei"))
        (is (true? (get (json/parse-string (:body status)) "active")))
        (is (= "application/vnd.ipld.car" (get-in getrec [:headers "content-type"]))) ; record found → CAR
        (is (= "application/vnd.ipld.car" (get-in blocks [:headers "content-type"]))))
      (testing "getRecord for a missing rkey 404s"
        (let [h (server/make-handler st k "z6Mkx")
              miss (h {:uri "/xrpc/com.atproto.sync.getRecord" :request-method :get
                       :query-string (str "did=" cfg/pds-did "&collection=app.bsky.feed.post&rkey=nope")})]
          (is (= 404 (:status miss))))))))

(deftest firehose-frame-wellformed
  (testing "commit-frame is dag-cbor(#commit header) ++ dag-cbor(body)"
    (let [k (.getPrivate (repo/gen-keypair))
          build (repo/build-repo cfg/pds-did
                                 [{:uri (str "at://" cfg/pds-did "/app.bsky.feed.post/3kfh1") :value {"$type" "app.bsky.feed.post" "text" "y"}}]
                                 "3kfh1" k)
          ops [{:action "create" :path "app.bsky.feed.post/3kfh1" :cid-bytes nil}]
          frame (repo/commit-frame 1 cfg/pds-did build ops "2026-06-24T00:00:00Z")
          header (repo/dag-cbor {:op 1 :t "#commit"})]
      ;; frame begins with the exact #commit header bytes
      (is (= (seq header) (take (count header) (seq frame))))
      (is (> (alength frame) (alength header))))))  ; a body follows the header

(deftest commit-signature-roundtrips
  (testing "the repo commit signature verifies against the signing key"
    (let [kp (repo/gen-keypair)
          [_ _ commit] (repo/make-commit cfg/pds-did (repo/block-cid {}) "3krev" nil (.getPrivate kp))
          unsigned (dissoc commit :sig)]
      (is (repo/verify (.getPublic kp) (repo/dag-cbor unsigned) (:sig commit))))))
