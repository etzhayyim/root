(ns etzhayyim.pds.server-test
  "Round-trip tests for the independent etzhayyim PDS: identity is etzhayyim (no
  gftd), and the datom-log store survives create/get/list/put/delete."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [cheshire.core :as json]
            [etzhayyim.pds.config :as cfg]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.repo :as repo]
            [etzhayyim.pds.blob :as blob]
            [etzhayyim.pds.account :as account]
            [etzhayyim.pds.xrpc :as xrpc]
            [etzhayyim.pds.server :as server]
            [org.httpkit.server :as http]))

(def repo cfg/host) ;; "atproto.etzhayyim.com"
(def tsecret (.getBytes "etzhayyim-test-secret-32bytes!!!!" "UTF-8"))

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
        rec {"$type" "app.bsky.feed.post" "text" "shalom from etzhayyim" "createdAt" "2026-06-17T00:00:00Z"}
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
                                   :record {"$type" "app.bsky.actor.profile" "displayName" "etzhayyim"}})
            g (xrpc/get-record st {:repo repo :collection coll :rkey "self"})]
        (is (= 200 (:status p)))
        (is (= {"$type" "app.bsky.actor.profile" "displayName" "etzhayyim"} (get-in g [:body "value"])))))
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
          h (server/make-handler (store/->mem-store) (.getPrivate kp) mb tsecret)
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
      (let [h (server/make-handler st k (repo/pubkey-multibase (.getPublic (repo/gen-keypair))) tsecret)
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
        (let [h (server/make-handler st k "z6Mkx" tsecret)
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

(deftest relay-verification-chain
  (testing "a relay reconstructs the key from did.json multibase + verifies the commit sig"
    (let [kp (repo/gen-keypair)
          mb (repo/pubkey-multibase (.getPublic kp))   ; published in did.json
          relay-pub (repo/multibase->pubkey mb)         ; what a relay derives from it
          [_ _ commit] (repo/make-commit cfg/pds-did (repo/block-cid {}) "3kr" nil (.getPrivate kp))]
      (is (repo/verify relay-pub (repo/dag-cbor (dissoc commit :sig)) (:sig commit)))
      (testing "a tampered commit fails verification"
        (is (not (repo/verify relay-pub (repo/dag-cbor (assoc (dissoc commit :sig) :rev "evil")) (:sig commit))))))))

(deftest dag-cbor-and-car-roundtrip
  (testing "dag-cbor encode→decode is lossless (nesting/ints/arrays/bools)"
    (let [v {"text" "hi" "n" 42 "nested" {"a" 1} "arr" [1 2 3] "flag" true}]
      (is (= v (repo/dag-cbor-decode (repo/dag-cbor v))))))
  (testing "cid-links survive (bytes compared by value)"
    (let [link (repo/cid-link (repo/block-cid {}))
          dec (repo/dag-cbor-decode (repo/dag-cbor {"link" link}))]
      (is (= (seq (:etzhayyim.pds.repo/cid link))
             (seq (:etzhayyim.pds.repo/cid (get dec "link")))))))
  (testing "CAR build→parse recovers every block"
    (let [k (.getPrivate (repo/gen-keypair))
          build (repo/build-repo cfg/pds-did
                                 [{:uri (str "at://" cfg/pds-did "/app.bsky.feed.post/3a") :value {"x" 1}}] "3a" k)
          parsed (repo/car-parse (repo/blocks-car build nil))]
      (is (= (set (keys (:blocks build))) (set (keys (:blocks parsed)))))
      (is (contains? (:blocks parsed) (:commit-cid build))))))

(deftest relay-verifies-from-served-car
  (testing "the full relay path: parse the getRepo CAR → decode commit → verify sig from did.json key"
    (let [kp (repo/gen-keypair)
          mb (repo/pubkey-multibase (.getPublic kp))           ; published in did.json
          build (repo/build-repo cfg/pds-did
                                 [{:uri (str "at://" cfg/pds-did "/app.bsky.feed.post/3a") :value {"x" 1}}] "3a" (.getPrivate kp))
          parsed (repo/car-parse (repo/blocks-car build nil))   ; what a relay receives
          commit (repo/dag-cbor-decode (get (:blocks parsed) (:commit-cid build)))
          relay-pub (repo/multibase->pubkey mb)]
      (is (repo/verify relay-pub (repo/dag-cbor (dissoc commit "sig")) (get commit "sig"))))))

(deftest firehose-frame-carries-the-repo
  (testing "the #commit frame body decodes to a CAR containing the commit"
    (let [k (.getPrivate (repo/gen-keypair))
          path "app.bsky.feed.post/3kfd"
          build (repo/build-repo cfg/pds-did
                                 [{:uri (str "at://" cfg/pds-did "/" path) :value {"$type" "app.bsky.feed.post" "text" "hi"}}] "3kfd" k)
          ops [{:action "create" :path path :cid-bytes (get-in build [:blocks (get-in build [:record-cids path]) :cid])}]
          frame (repo/commit-frame 1 cfg/pds-did build ops "2026-01-01T00:00:00Z")
          hlen (alength (repo/dag-cbor {:op 1 :t "#commit"}))
          header (repo/dag-cbor-decode (java.util.Arrays/copyOfRange frame 0 hlen))
          body (repo/dag-cbor-decode (java.util.Arrays/copyOfRange frame hlen (alength frame)))
          parsed (repo/car-parse (get body "blocks"))]
      (is (= "#commit" (get header "t")))
      (is (= cfg/pds-did (get body "repo")))
      (is (contains? (:blocks parsed) (:commit-cid build))))))

(deftest account-and-session-auth
  (testing "createAccount → accessJwt; getSession verifies it; createSession by password"
    (let [acct-file (str (System/getProperty "java.io.tmpdir") "/pds-acct-" (hash (str (gensym))) ".edn")]
      (with-redefs [cfg/accounts-file acct-file]
        (let [h (server/make-handler (store/->mem-store) (.getPrivate (repo/gen-keypair)) "z6Mkx" tsecret)
              created (h {:uri "/xrpc/com.atproto.server.createAccount" :request-method :post
                          :headers {"content-type" "application/json"}
                          :body (json/generate-string {"handle" "alice.etzhayyim.com" "password" "hunter2"})})
              jwt (get (json/parse-string (:body created)) "accessJwt")
              sess (h {:uri "/xrpc/com.atproto.server.getSession" :request-method :get
                       :headers {"authorization" (str "Bearer " jwt)}})
              nosess (h {:uri "/xrpc/com.atproto.server.getSession" :request-method :get})
              login (h {:uri "/xrpc/com.atproto.server.createSession" :request-method :post
                        :headers {"content-type" "application/json"}
                        :body (json/generate-string {"identifier" "alice.etzhayyim.com" "password" "hunter2"})})]
          (is (= 200 (:status created)))
          (is (= "did:web:alice.etzhayyim.com" (get (json/parse-string (:body created)) "did")))
          (is (= "did:web:alice.etzhayyim.com" (get (json/parse-string (:body sess)) "did")))   ; JWT verified
          (is (= 401 (:status nosess)))                                                          ; no Bearer → 401
          (is (= "did:web:alice.etzhayyim.com" (get (json/parse-string (:body login)) "did")))  ; password login
          (.delete (clojure.java.io/file acct-file)))))))

(deftest jwt-expiry
  (testing "an expired JWT does not verify; a fresh one does"
    (is (nil? (account/verify-jwt tsecret (account/make-jwt tsecret "did:web:x.etzhayyim.com" -1))))
    (is (= "did:web:x.etzhayyim.com" (account/verify-jwt tsecret (account/make-jwt tsecret "did:web:x.etzhayyim.com" 3600))))))

(deftest write-auth-gate
  (testing "with require-auth: no Bearer → 401, own-repo Bearer → 200, other-repo Bearer → 403"
    (with-redefs [cfg/require-auth true]
      (let [st (store/->mem-store)
            h (server/make-handler st (.getPrivate (repo/gen-keypair)) "z6Mkx" tsecret)
            body (json/generate-string {"repo" "atproto.etzhayyim.com" "collection" "app.bsky.feed.post" "record" {"$type" "app.bsky.feed.post" "text" "x"}})
            req (fn [auth] (h (cond-> {:uri "/xrpc/com.atproto.repo.createRecord" :request-method :post
                                       :headers {"content-type" "application/json"} :body body}
                                auth (assoc-in [:headers "authorization"] (str "Bearer " auth)))))]
        (is (= 401 (:status (req nil))))
        (is (= 200 (:status (req (account/make-jwt tsecret "did:web:atproto.etzhayyim.com")))))
        (is (= 403 (:status (req (account/make-jwt tsecret "did:web:someone-else.etzhayyim.com")))))))))

(deftest list-records-cursor-and-order
  (testing "reverse, rkeyStart/rkeyEnd, and limit+cursor paging"
    (let [st (store/->mem-store)]
      (doseq [k ["3a" "3b" "3c" "3d" "3e"]]
        (store/put-record st cfg/pds-did "app.bsky.feed.post" k {"$type" "x" "k" k}))
      (let [rkeys (fn [opts] (mapv :rkey (:records (store/list-records st cfg/pds-did "app.bsky.feed.post" opts))))]
        (is (= ["3a" "3b" "3c" "3d" "3e"] (rkeys {})))                       ; ascending default
        (is (= ["3e" "3d" "3c" "3b" "3a"] (rkeys {:reverse true})))          ; reverse
        (is (= ["3b" "3c" "3d"] (rkeys {:rkey-start "3b" :rkey-end "3d"})))  ; bounds
        ;; limit + cursor paging walks the whole set without dupes/gaps
        (let [p1 (store/list-records st cfg/pds-did "app.bsky.feed.post" {:limit 2})
              p2 (store/list-records st cfg/pds-did "app.bsky.feed.post" {:limit 2 :cursor (:cursor p1)})
              p3 (store/list-records st cfg/pds-did "app.bsky.feed.post" {:limit 2 :cursor (:cursor p2)})]
          (is (= ["3a" "3b" "3c" "3d" "3e"]
                 (mapv :rkey (concat (:records p1) (:records p2) (:records p3))))))))))

(deftest update-and-revive-latest-wins
  (testing "an updated record reflects its newest value (latest-wins), and a re-create after delete revives it"
    (let [st (store/->mem-store)]
      (store/put-record st cfg/pds-did "c" "r" {"$type" "x" "v" 1})
      (store/put-record st cfg/pds-did "c" "r" {"$type" "x" "v" 2})   ; update
      (is (= 2 (get (:value (store/get-record st cfg/pds-did "c" "r")) "v")))
      (store/delete-record st cfg/pds-did "c" "r")
      (is (nil? (store/get-record st cfg/pds-did "c" "r")))
      (store/put-record st cfg/pds-did "c" "r" {"$type" "x" "v" 3})   ; re-create
      (is (= 3 (get (:value (store/get-record st cfg/pds-did "c" "r")) "v")))
      (is (= 1 (:count (store/describe-repo st cfg/pds-did)))))))

(deftest swap-record-concurrency
  (testing "swapRecord acts as compare-and-set: matching CID succeeds, stale CID 409s"
    (let [st (store/->mem-store)
          coll "app.bsky.actor.profile"
          v1 {"$type" coll "displayName" "v1"}
          {cid1 :cid} (store/put-record st cfg/pds-did coll "self" v1)]
      ;; stale/wrong swap → 409 InvalidSwap
      (is (= 409 (:status (xrpc/put-record st {:repo repo :collection coll :rkey "self"
                                               :record {"$type" coll "displayName" "v2"} :swapRecord "bafyreiwrong"}))))
      ;; correct swap (current cid) → 200
      (let [r (xrpc/put-record st {:repo repo :collection coll :rkey "self"
                                   :record {"$type" coll "displayName" "v2"} :swapRecord cid1})]
        (is (= 200 (:status r)))
        ;; the old cid is now stale → a second swap on cid1 409s
        (is (= 409 (:status (xrpc/delete-record st {:repo repo :collection coll :rkey "self" :swapRecord cid1}))))
        ;; delete with the new cid → ok
        (is (= 200 (:status (xrpc/delete-record st {:repo repo :collection coll :rkey "self"
                                                    :swapRecord (get-in r [:body "cid"])}))))))))

(deftest lexicon-validation
  (testing "with PDS_VALIDATE_RECORDS, known collections enforce their shape"
    (with-redefs [cfg/validate-records true]
      (let [st (store/->mem-store)
            mk (fn [rec] (xrpc/create-record st {:repo repo :collection "app.bsky.feed.post" :record rec}))]
        (is (= 400 (:status (mk {"$type" "app.bsky.feed.post" "text" "hi"}))))                            ; no createdAt
        (is (= 400 (:status (mk {"$type" "app.bsky.feed.post" "text" 42 "createdAt" "t"}))))             ; text not string
        (is (= 200 (:status (mk {"$type" "app.bsky.feed.post" "text" "hi" "createdAt" "2026-01-01T00:00:00Z"}))))
        (is (= 200 (:status (xrpc/create-record st {:repo repo :collection "com.example.custom"          ; unknown collection passes
                                                    :record {"$type" "x" "n" 1}})))))))
  (testing "off by default: a createdAt-less post is accepted"
    (is (= 200 (:status (xrpc/create-record (store/->mem-store) {:repo repo :collection "app.bsky.feed.post"
                                                                 :record {"$type" "app.bsky.feed.post" "text" "hi"}}))))))

(deftest record-sanity-on-write
  (testing "createRecord/putRecord reject a non-object or $type-less record"
    (let [st (store/->mem-store)]
      (is (= 400 (:status (xrpc/create-record st {:repo repo :collection "c" :record "not-a-map"}))))
      (is (= 400 (:status (xrpc/create-record st {:repo repo :collection "c" :record {"text" "no type"}}))))
      (is (= 200 (:status (xrpc/create-record st {:repo repo :collection "c" :record {"$type" "app.x" "text" "ok"}}))))
      (is (= 400 (:status (xrpc/put-record st {:repo repo :collection "c" :rkey "self" :record {"no" "type"}})))))))

(deftest describe-repo-collection-counts
  (testing "describeRepo reports total + per-collection record counts"
    (let [st (store/->mem-store)]
      (store/put-record st cfg/pds-did "app.bsky.feed.post" "3a" {"$type" "x"})
      (store/put-record st cfg/pds-did "app.bsky.feed.post" "3b" {"$type" "x"})
      (store/put-record st cfg/pds-did "app.bsky.actor.profile" "self" {"$type" "y"})
      (let [d (xrpc/describe-repo st {:repo repo})]
        (is (= 3 (get-in d [:body "recordCount"])))
        (is (= 2 (get-in d [:body "collectionCounts" "app.bsky.feed.post"])))
        (is (= 1 (get-in d [:body "collectionCounts" "app.bsky.actor.profile"])))))))

(deftest list-missing-blobs
  (testing "listMissingBlobs surfaces blob refs not present in the store"
    (let [st (store/->mem-store)
          h (server/make-handler st (.getPrivate (repo/gen-keypair)) "z6Mkx" tsecret)]
      ;; put a record (store-level, as importRepo would) referencing an un-uploaded blob
      (store/put-record st cfg/pds-did "app.bsky.feed.post" "3mb1"
                        {"$type" "app.bsky.feed.post" "text" "x"
                         "img" {"$type" "blob" "ref" {"$link" "bafkreimissing1"} "mimeType" "image/png" "size" 1}})
      (let [resp (h {:uri "/xrpc/com.atproto.repo.listMissingBlobs" :request-method :get
                     :query-string (str "repo=" cfg/pds-did)})]
        (is (= 200 (:status resp)))
        (is (= ["bafkreimissing1"] (mapv #(get % "cid") (get (json/parse-string (:body resp)) "blobs"))))))))

(deftest resolve-handle-account-backed
  (testing "a registered account's did wins; an unregistered handle falls back to did:web"
    (let [acct (str (System/getProperty "java.io.tmpdir") "/pds-rh-" (hash (str (gensym))) ".edn")]
      (with-redefs [cfg/accounts-file acct]
        (account/create-account acct {:handle "bob.etzhayyim.com" :password "pw" :did "did:plc:bob123"})
        (is (= "did:plc:bob123" (get-in (xrpc/resolve-handle {:handle "bob.etzhayyim.com"}) [:body "did"])))
        (is (= "did:web:carol.etzhayyim.com" (get-in (xrpc/resolve-handle {:handle "carol.etzhayyim.com"}) [:body "did"])))
        (is (= 400 (:status (xrpc/resolve-handle {:handle ""}))))
        (.delete (clojure.java.io/file acct))))))

(deftest error-paths
  (testing "consistent error envelopes for bad/absent requests"
    (let [st (store/->mem-store)
          h (server/make-handler st (.getPrivate (repo/gen-keypair)) "z6Mkx" tsecret)
          post (fn [nsid m] (h {:uri (str "/xrpc/" nsid) :request-method :post
                                :headers {"content-type" "application/json"} :body (json/generate-string m)}))
          get* (fn [nsid qs] (h {:uri (str "/xrpc/" nsid) :request-method :get :query-string qs}))]
      (is (= 400 (:status (post "com.atproto.repo.createRecord" {"repo" "atproto.etzhayyim.com" "record" {"x" 1}})))) ; no collection
      (is (= 400 (:status (post "com.atproto.repo.createRecord" {"repo" "atproto.etzhayyim.com" "collection" "c"}))))  ; no record
      (is (= 400 (:status (post "com.atproto.repo.applyWrites" {"repo" "atproto.etzhayyim.com"}))))                    ; no writes
      (is (= 404 (:status (get* "com.atproto.repo.getRecord" "repo=atproto.etzhayyim.com&collection=c&rkey=nope"))))   ; absent record
      (is (= 404 (:status (get* "com.atproto.sync.getBlob" "cid=bafkreiabsentxyz"))))                                  ; absent blob
      (is (= 404 (:status (get* "com.atproto.sync.getRecord" "did=did:web:atproto.etzhayyim.com&collection=c&rkey=nope")))) ; absent sync record
      (is (= 501 (:status (get* "com.atproto.repo.notAMethod" ""))))                                                   ; unknown method
      (testing "every error response carries an \"error\" key"
        (doseq [resp [(post "com.atproto.repo.createRecord" {}) (get* "com.atproto.sync.getBlob" "cid=x")
                      (get* "com.atproto.repo.notAMethod" "")]]
          (is (contains? (json/parse-string (:body resp)) "error")))))))

(deftest firehose-websocket-integration
  (testing "a websocket client receives a binary #commit frame carrying the repo (over the wire)"
    (let [st (store/->mem-store)
          _ (store/put-record st cfg/pds-did "app.bsky.feed.post" "3kws1" {"$type" "app.bsky.feed.post" "text" "wire"})
          port 19287
          handler (server/make-handler st (.getPrivate (repo/gen-keypair))
                                       (repo/pubkey-multibase (.getPublic (repo/gen-keypair))) tsecret)
          stop (http/run-server handler {:port port})]
      (try
        (let [sock (java.net.Socket. "127.0.0.1" (int port))]
          (.setSoTimeout sock 2500)
          (let [out (.getOutputStream sock)
                in (.getInputStream sock)
                wskey (.encodeToString (java.util.Base64/getEncoder) (.getBytes "0123456789abcdef"))
                req (str "GET /xrpc/com.atproto.sync.subscribeRepos HTTP/1.1\r\n"
                         "Host: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                         "Sec-WebSocket-Key: " wskey "\r\nSec-WebSocket-Version: 13\r\n\r\n")
                baos (java.io.ByteArrayOutputStream.)
                buf (byte-array 4096)]
            (.write out (.getBytes req "UTF-8")) (.flush out)
            (loop []  ; read until the server stops sending (frame then idle → SoTimeout)
              (let [n (try (.read in buf) (catch java.net.SocketTimeoutException _ -1))]
                (when (pos? n) (.write baos buf 0 n) (recur))))
            (.close sock)
            (let [data (.toByteArray baos)
                  s (String. data "ISO-8859-1")
                  bidx (.indexOf s "\r\n\r\n")
                  fstart (+ bidx 4)
                  b1 (bit-and (aget data (inc fstart)) 0x7f)
                  [plen poff] (if (= b1 126)
                                [(+ (* 256 (bit-and (aget data (+ fstart 2)) 0xff)) (bit-and (aget data (+ fstart 3)) 0xff)) (+ fstart 4)]
                                [b1 (+ fstart 2)])
                  payload (java.util.Arrays/copyOfRange data poff (+ poff plen))
                  hlen (alength (repo/dag-cbor {:op 1 :t "#commit"}))
                  header (repo/dag-cbor-decode (java.util.Arrays/copyOfRange payload 0 hlen))
                  body (repo/dag-cbor-decode (java.util.Arrays/copyOfRange payload hlen (alength payload)))
                  parsed (repo/car-parse (get body "blocks"))]
              (is (str/includes? (subs s 0 bidx) "101"))               ; HTTP 101 upgrade
              (is (= 2 (bit-and (aget data fstart) 0x0f)))             ; binary opcode
              (is (= "#commit" (get header "t")))
              (is (= cfg/pds-did (get body "repo")))
              (is (pos? (count (:blocks parsed)))))))
        (finally (stop))))))

(deftest blob-ref-validation
  (testing "createRecord referencing an absent blob is rejected (400)"
    (let [h (server/make-handler (store/->mem-store) (.getPrivate (repo/gen-keypair)) "z6Mkx" tsecret)
          body (json/generate-string
                {"repo" "atproto.etzhayyim.com" "collection" "app.bsky.feed.post"
                 "record" {"text" "see image" "image" {"$type" "blob" "ref" {"$link" "bafkreiabsentblobxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"} "mimeType" "image/png" "size" 1}}})
          resp (h {:uri "/xrpc/com.atproto.repo.createRecord" :request-method :post
                   :headers {"content-type" "application/json"} :body body})]
      (is (= 400 (:status resp)))
      (is (str/includes? (:body resp) "BlobNotFound")))))

(deftest import-repo-roundtrips
  (testing "export a repo to a CAR, import it into a fresh store → records recovered"
    (let [k (.getPrivate (repo/gen-keypair))
          src (store/->mem-store)]
      (doseq [i (range 12)]
        (store/put-record src cfg/pds-did "app.bsky.feed.post" (str "3p" i) {"text" (str "n" i)}))
      (let [recs (for [c ["app.bsky.feed.post"]
                       r (:records (store/list-records src cfg/pds-did c {:limit 100}))] r)
            build (repo/build-repo cfg/pds-did recs "3rev" k)
            car (repo/blocks-car build nil)
            {:keys [did records]} (repo/import-records car)
            dst (store/->mem-store)]
        (is (= cfg/pds-did did))
        (is (= 12 (count records)))
        (doseq [[coll rkey value] records] (store/put-record dst did coll rkey value))
        (is (= 12 (:count (store/describe-repo dst cfg/pds-did))))
        (is (= "n7" (get (:value (store/get-record dst cfg/pds-did "app.bsky.feed.post" "3p7")) "text")))))))

(deftest apply-writes-batch
  (testing "applyWrites creates a batch of records in one call"
    (let [st (store/->mem-store)
          h (server/make-handler st (.getPrivate (repo/gen-keypair)) "z6Mkx" tsecret)
          resp (h {:uri "/xrpc/com.atproto.repo.applyWrites" :request-method :post
                   :headers {"content-type" "application/json"}
                   :body (json/generate-string
                          {"repo" "atproto.etzhayyim.com"
                           "writes" [{"$type" "com.atproto.repo.applyWrites#create" "collection" "app.bsky.feed.post" "rkey" "3w1" "value" {"$type" "app.bsky.feed.post" "text" "a"}}
                                     {"$type" "com.atproto.repo.applyWrites#create" "collection" "app.bsky.feed.post" "rkey" "3w2" "value" {"$type" "app.bsky.feed.post" "text" "b"}}]})})
          results (get (json/parse-string (:body resp)) "results")]
      (is (= 200 (:status resp)))
      (is (= 2 (count results)))
      (is (= 2 (:count (store/describe-repo st cfg/pds-did)))))))

(deftest blob-store-roundtrips
  (testing "uploadBlob → content-addressed ref; getBlob returns the verified bytes"
    (let [dir (str (System/getProperty "java.io.tmpdir") "/pds-blobs-" (hash (str (gensym))))
          data (.getBytes "fake image bytes" "UTF-8")
          {:keys [cid size]} (blob/put-blob dir data "image/png")]
      (is (str/starts-with? cid "bafkrei"))   ; CIDv1 raw / sha2-256
      (is (= (alength data) size))
      (let [{:keys [bytes mime]} (blob/get-blob dir cid)]
        (is (= "fake image bytes" (String. bytes "UTF-8")))
        (is (= "image/png" mime)))
      (is (= [cid] (blob/list-blobs dir)))
      (doseq [f (.listFiles (clojure.java.io/file dir))] (.delete f))
      (.delete (clojure.java.io/file dir)))))
