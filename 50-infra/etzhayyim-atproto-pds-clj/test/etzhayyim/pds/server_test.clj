(ns etzhayyim.pds.server-test
  "Round-trip tests for the independent etzhayyim PDS: identity is etzhayyim (no
  gftd), and the datom-log store survives create/get/list/put/delete."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [cheshire.core :as json]
            [etzhayyim.pds.config :as cfg]
            [etzhayyim.pds.store :as store]
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
  (testing "the ring handler serves did.json and describeServer"
    (let [h (server/make-handler (store/->mem-store))
          did-resp (h {:uri "/.well-known/did.json" :request-method :get})
          desc (h {:uri "/xrpc/com.atproto.server.describeServer" :request-method :get})]
      (is (= 200 (:status did-resp)))
      (is (str/includes? (:body did-resp) "did:web:atproto.etzhayyim.com"))
      (is (= 200 (:status desc)))
      (is (not (str/includes? (:body desc) "gftd"))))))

;; ── account lifecycle + blobs (ADR-2606242330 P1) ────────────────────────────

(deftest account-lifecycle
  (let [st (store/->mem-store)]
    (testing "createAccount registers a handle under a user-domain"
      (let [r (xrpc/create-account st {:handle "alice.etzhayyim.com" :email "a@etzhayyim.com"})]
        (is (= 200 (:status r)))
        (is (= "did:web:alice.etzhayyim.com" (get-in r [:body "did"])))
        (is (= "alice.etzhayyim.com" (get-in r [:body "handle"])))
        (is (str/starts-with? (get-in r [:body "accessJwt"]) "etzhayyim-session."))))
    (testing "a handle outside the user-domain is rejected (etzhayyim-only)"
      (let [r (xrpc/create-account st {:handle "bob.example.com"})]
        (is (= 400 (:status r)))
        (is (= "InvalidHandle" (get-in r [:body "error"])))))
    (testing "a duplicate handle is rejected"
      (let [r (xrpc/create-account st {:handle "alice.etzhayyim.com"})]
        (is (= 400 (:status r)))
        (is (= "HandleNotAvailable" (get-in r [:body "error"])))))
    (testing "getSession reflects the account by handle and by did"
      (is (= "did:web:alice.etzhayyim.com"
             (get-in (xrpc/get-session st {:identifier "alice.etzhayyim.com"}) [:body "did"])))
      (is (= "alice.etzhayyim.com"
             (get-in (xrpc/get-session st {:identifier "did:web:alice.etzhayyim.com"}) [:body "handle"]))))
    (testing "getSession for an unknown identifier is a 400"
      (is (= 400 (:status (xrpc/get-session st {:identifier "ghost.etzhayyim.com"})))))))

(deftest blob-round-trip
  (let [st (store/->mem-store)
        did "did:web:alice.etzhayyim.com"
        data (.getBytes "shalom-blob-bytes" "UTF-8")
        up (xrpc/upload-blob st did "text/plain" data)
        cid (get-in up [:body "blob" "ref" "$link"])]
    (testing "uploadBlob returns a content-addressed blob ref"
      (is (= 200 (:status up)))
      (is (= "blob" (get-in up [:body "blob" "$type"])))
      (is (str/starts-with? cid "b"))
      (is (= (alength data) (get-in up [:body "blob" "size"]))))
    (testing "getBlob returns the same bytes + mimeType via :blob"
      (let [g (xrpc/get-blob st {:cid cid})]
        (is (= 200 (:status g)))
        (is (= "shalom-blob-bytes" (String. ^bytes (get-in g [:blob :bytes]) "UTF-8")))
        (is (= "text/plain" (get-in g [:blob :mimeType])))))
    (testing "identical bytes content-address to the same cid (idempotent)"
      (is (= cid (get-in (xrpc/upload-blob st did "text/plain" data)
                         [:body "blob" "ref" "$link"]))))
    (testing "a missing blob is a 404"
      (is (= 404 (:status (xrpc/get-blob st {:cid "bdoesnotexist"})))))
    (testing "an empty blob is rejected"
      (is (= 400 (:status (xrpc/upload-blob st did "text/plain" (byte-array 0))))))))

(deftest http-account-and-blob
  (testing "createAccount over the ring handler (JSON)"
    (let [h (server/make-handler (store/->mem-store))
          resp (h {:uri "/xrpc/com.atproto.server.createAccount"
                   :request-method :post
                   :body (json/generate-string {"handle" "carol.etzhayyim.com"})})]
      (is (= 200 (:status resp)))
      (is (str/includes? (:body resp) "did:web:carol.etzhayyim.com"))))
  (testing "uploadBlob over the ring handler (raw bytes in, JSON ref out)"
    (let [h (server/make-handler (store/->mem-store))
          resp (h {:uri "/xrpc/com.atproto.repo.uploadBlob"
                   :request-method :post
                   :headers {"content-type" "application/octet-stream"}
                   :body (.getBytes "raw-bytes-blob" "UTF-8")})]
      (is (= 200 (:status resp)))
      (is (str/includes? (:body resp) "$type"))
      (is (str/includes? (:body resp) "blob")))))
