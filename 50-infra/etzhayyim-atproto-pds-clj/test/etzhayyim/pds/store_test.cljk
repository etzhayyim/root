(ns etzhayyim.pds.store-test
  "Direct PdsStore protocol contract — exercised against BOTH the MemStore and the
  DurableStore (same datom-log semantics), so the core persistence layer has its own
  coverage independent of the xrpc/server handlers that use it. KotobaStore needs the
  live kotoba engine and is covered at cutover, not here."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [cheshire.core :as json]
            [babashka.http-client :as http]
            [etzhayyim.pds.store :as store]))

(def did  "did:web:etzhayyim.com:actor:unspsc-10101500")
(def did2 "did:web:etzhayyim.com:actor:unspsc-99999999")

(defn- tmp-path []
  (str (System/getProperty "java.io.tmpdir") "/pds-store-" (hash (str (gensym))) ".edn"))

;; a deterministic fake signer: {:sig <b64> :multikey <str>}; commit-sig decodes :sig.
(def ^bytes sig-bytes (byte-array (map byte (range 1 65))))   ; 64 raw bytes (P-256 compact)
(def sig-b64 (.encodeToString (java.util.Base64/getEncoder) sig-bytes))
(defn- fake-signer [_did _msg] {:sig sig-b64 :multikey "zDnaFAKEkeyForStoreContract"})

;; ── the shared contract, run against each backend ────────────────────────────

(defn- run-contract [mk-store label]
  (testing (str label " — put/get roundtrip + content-addressing")
    (let [s (mk-store)
          res (store/put-record s did "app.bsky.feed.post" "r1" {"text" "hi"})]
      (is (= (str "at://" did "/app.bsky.feed.post/r1") (:uri res)))
      (is (string? (:cid res)) "a content id is assigned")
      (let [got (store/get-record s did "app.bsky.feed.post" "r1")]
        (is (= {"text" "hi"} (:value got)))
        (is (= (:cid res) (:cid got))))))

  (testing (str label " — update is latest-wins (the latest-db fold)")
    (let [s (mk-store)]
      (store/put-record s did "app.bsky.feed.post" "r1" {"text" "v1"})
      (store/put-record s did "app.bsky.feed.post" "r1" {"text" "v2"})
      (is (= {"text" "v2"} (:value (store/get-record s did "app.bsky.feed.post" "r1")))
          "a re-put rkey reflects the newest value")))

  (testing (str label " — delete tombstones (append-only, get→nil, revive on re-create)")
    (let [s (mk-store)]
      (store/put-record s did "app.bsky.feed.post" "r1" {"text" "hi"})
      (is (true? (store/delete-record s did "app.bsky.feed.post" "r1")))
      (is (nil? (store/get-record s did "app.bsky.feed.post" "r1")) "tombstoned → not found")
      ;; re-create after delete revives (the :record/deleted false in a fresh put)
      (store/put-record s did "app.bsky.feed.post" "r1" {"text" "again"})
      (is (= {"text" "again"} (:value (store/get-record s did "app.bsky.feed.post" "r1"))))))

  (testing (str label " — list-records ordering, limit/cursor, reverse")
    (let [s (mk-store)]
      (doseq [k ["a" "b" "c" "d"]]
        (store/put-record s did "app.bsky.feed.post" k {"text" k}))
      (store/delete-record s did "app.bsky.feed.post" "c")        ; tombstoned → excluded
      (let [{:keys [records cursor]} (store/list-records s did "app.bsky.feed.post" {:limit 2})]
        (is (= ["a" "b"] (mapv :rkey records)) "ascending by rkey")
        (is (= "b" cursor) "cursor = last rkey of a full page"))
      (let [{:keys [records]} (store/list-records s did "app.bsky.feed.post"
                                                  {:limit 50 :cursor "b"})]
        (is (= ["d"] (mapv :rkey records)) "after cursor 'b', c is tombstoned, only d remains"))
      (let [{:keys [records]} (store/list-records s did "app.bsky.feed.post" {:reverse true})]
        (is (= ["d" "b" "a"] (mapv :rkey records)) "reverse = descending, tombstone excluded"))))

  (testing (str label " — recent-feed is cross-actor with an opaque cursor")
    (let [s (mk-store)]
      (store/put-record s did  "app.bsky.feed.post" "r1" {"text" "a" "createdAt" "2026-06-26T00:00:01Z"})
      (store/put-record s did2 "app.bsky.feed.post" "r2" {"text" "b" "createdAt" "2026-06-26T00:00:03Z"})
      (store/put-record s did  "app.bsky.feed.post" "r3" {"text" "c" "createdAt" "2026-06-26T00:00:02Z"})
      (let [{:keys [records]} (store/recent-feed s "app.bsky.feed.post" {:limit 50})]
        (is (= 3 (count records)) "records from BOTH actors appear")
        (is (= #{did did2} (set (map :did records))) "each record carries its author did")
        (is (= ["r2" "r3" "r1"] (mapv :rkey records)) "newest-first by createdAt"))
      (let [{:keys [records cursor]} (store/recent-feed s "app.bsky.feed.post" {:limit 1})]
        (is (= ["r2"] (mapv :rkey records)))
        (is (string? cursor) "opaque continuation token, not an rkey")
        (let [nxt (store/recent-feed s "app.bsky.feed.post" {:limit 1 :cursor cursor})]
          (is (= ["r3"] (mapv :rkey (:records nxt))) "cursor advances past the newest")))))

  (testing (str label " — describe-repo: collections + live count")
    (let [s (mk-store)]
      (store/put-record s did "app.bsky.feed.post" "r1" {"text" "x"})
      (store/put-record s did "app.bsky.actor.profile" "self" {"displayName" "A"})
      (store/put-record s did "app.bsky.feed.post" "r2" {"text" "y"})
      (store/delete-record s did "app.bsky.feed.post" "r2")
      (let [d (store/describe-repo s did)]
        (is (= did (:did d)))
        (is (= ["app.bsky.actor.profile" "app.bsky.feed.post"] (:collections d)) "sorted, deduped")
        (is (= 2 (:count d)) "live records only (tombstone excluded)")))))

;; ── MemStore + DurableStore both honour the contract ─────────────────────────

(deftest mem-store-contract
  (run-contract store/->mem-store "mem"))

(deftest durable-store-contract
  (run-contract #(store/->durable-store (tmp-path)) "durable"))

;; ── signer-dependent behaviour (Path B) ──────────────────────────────────────

(deftest commit-sig-needs-a-signer
  (testing "without a signer the store returns nil (caller falls back to the PDS key)"
    (is (nil? (store/commit-sig (store/->mem-store) did (.getBytes "msg" "UTF-8")))))
  (testing "with a signer commit-sig returns the raw signature bytes (decoded from :sig)"
    (let [sig (store/commit-sig (store/->mem-store fake-signer) did (.getBytes "msg" "UTF-8"))]
      (is (bytes? sig))
      (is (= (seq sig-bytes) (seq sig)) "the 64 raw P-256 bytes, base64-decoded"))))

(deftest signed-writes-attribute-the-actor
  (testing "a signer makes each write an actor-attributed assertion (Path B)"
    (let [s (store/->mem-store fake-signer)
          res (store/put-record s did "app.bsky.feed.post" "r1" {"text" "signed"})]
      (is (= sig-b64 (:sig res)))
      (is (= "zDnaFAKEkeyForStoreContract" (:signedBy res)))
      (is (= sig-b64 (:sig (store/get-record s did "app.bsky.feed.post" "r1"))) "sig surfaces on read"))))

(deftest leash-author-is-attributed-on-the-write
  (testing "the 6-arg put attributes a consenting member (:author), surfaced on read"
    (let [s (store/->mem-store)]
      (is (nil? (:author (store/put-record s did "app.bsky.feed.post" "r1" {"text" "x"})))
          "unattributed by default")
      (let [res (store/put-record s did "app.bsky.feed.post" "r2" {"text" "y"}
                                  {:author "did:web:etzhayyim.com:actor:consenting-member"})]
        (is (= "did:web:etzhayyim.com:actor:consenting-member" (:author res)))
        (is (= "did:web:etzhayyim.com:actor:consenting-member"
               (:author (store/get-record s did "app.bsky.feed.post" "r2"))))))))

;; ── durable persistence: write-through + replay-on-reopen (protocol level) ────

(deftest durable-replays-from-disk-on-reopen
  (testing "a fresh DurableStore on the same path sees prior writes + tombstones"
    (let [path (tmp-path)]
      (let [s1 (store/->durable-store path)]
        (store/put-record s1 did "app.bsky.feed.post" "r1" {"text" "persisted"})
        (store/put-record s1 did "app.bsky.feed.post" "r2" {"text" "gone"})
        (store/delete-record s1 did "app.bsky.feed.post" "r2"))
      (is (.exists (io/file path)) "the on-disk journal was written")
      (let [s2 (store/->durable-store path)]               ; reopen = replay the journal
        (is (= {"text" "persisted"} (:value (store/get-record s2 did "app.bsky.feed.post" "r1"))))
        (is (nil? (store/get-record s2 did "app.bsky.feed.post" "r2")) "tombstone survived the reopen")))))

;; ── KotobaStore: the production backend's kotoba XRPC wire contract ───────────
;; The live engine is absent in CI, so we mock babashka.http-client/post to capture
;; the request KotobaStore builds + feed it a stub response. This locks the kg.*
;; endpoint + body shape (change-detectable BEFORE cutover), independent of a server.

(defmacro ^:private with-kpost
  "Run `body` with http/post stubbed: every call is recorded into the `reqs` atom as
  {:url :body(parsed)} and returns {:body (json of (resp-for url))}. `resp-for` is a
  fn url→clj-map (the engine's JSON response)."
  [reqs resp-for & body]
  `(with-redefs [http/post (fn [url# opts#]
                             (swap! ~reqs conj {:url url# :body (json/parse-string (:body opts#) true)})
                             {:body (json/generate-string (~resp-for url#))})]
     ~@body))

(def kbase "http://kotoba.local")
(def kgraph "etzhayyim-pds")

(deftest kotoba-put-record-wire-shape
  (testing "put-record POSTs kg.ingest_batch with {:graph :datoms} carrying the record fields"
    (let [reqs (atom [])]
      (with-kpost reqs (constantly {})
        (let [s (store/->kotoba-store kbase kgraph)
              res (store/put-record s did "app.bsky.feed.post" "r1" {"text" "hi"})]
          (is (= 1 (count @reqs)))
          (let [{:keys [url body]} (first @reqs)]
            (is (str/ends-with? url "/xrpc/com.etzhayyim.apps.kotoba.kg.ingest_batch"))
            (is (= kgraph (:graph body)))
            (let [attrs (set (map second (:datoms body)))]
              (is (contains? attrs "record/did"))
              (is (contains? attrs "record/value"))
              (is (contains? attrs "record/cid"))
              (is (not (contains? attrs "record/sig")) "unsigned when no signer")))
          (is (= (str "at://" did "/app.bsky.feed.post/r1") (:uri res)))
          (is (= {"text" "hi"} (:value res))))))))

(deftest kotoba-put-record-signed-adds-sig-datoms
  (testing "with a signer the ingest carries record/sig + record/signedBy datoms (Path B)"
    (let [reqs (atom [])]
      (with-kpost reqs (constantly {})
        (store/put-record (store/->kotoba-store kbase kgraph fake-signer)
                          did "app.bsky.feed.post" "r1" {"text" "hi"})
        (let [attrs (set (map second (:datoms (:body (first @reqs)))))]
          (is (contains? attrs "record/sig"))
          (is (contains? attrs "record/signedBy")))))))

(deftest kotoba-get-record-parses-and-honours-tombstone
  (testing "get-record reads kg.get_entity, parses :record/value, returns nil when deleted"
    (let [reqs (atom [])
          resp (fn [_url] {(keyword "record/value") (json/generate-string {"text" "hi"})
                           (keyword "record/cid") "cid1"})]
      (with-kpost reqs resp
        (let [got (store/get-record (store/->kotoba-store kbase kgraph) did "app.bsky.feed.post" "r1")]
          (is (str/ends-with? (:url (first @reqs)) "/xrpc/com.etzhayyim.apps.kotoba.kg.get_entity"))
          (is (= (str "at://" did "/app.bsky.feed.post/r1") (:uri got)))
          (is (= {"text" "hi"} (:value got)))
          (is (= "cid1" (:cid got))))))
    (testing "a tombstoned entity → nil"
      (let [reqs (atom [])
            resp (fn [_] {(keyword "record/value") (json/generate-string {"text" "x"})
                          (keyword "record/deleted") true})]
        (with-kpost reqs resp
          (is (nil? (store/get-record (store/->kotoba-store kbase kgraph) did "app.bsky.feed.post" "r1"))))))))

(deftest kotoba-delete-posts-a-tombstone-datom
  (testing "delete-record POSTs kg.ingest_batch with a record/deleted=true datom"
    (let [reqs (atom [])]
      (with-kpost reqs (constantly {})
        (is (true? (store/delete-record (store/->kotoba-store kbase kgraph) did "app.bsky.feed.post" "r1")))
        (let [{:keys [url body]} (first @reqs)]
          (is (str/ends-with? url "/xrpc/com.etzhayyim.apps.kotoba.kg.ingest_batch"))
          (is (= [[(str "at://" did "/app.bsky.feed.post/r1") "record/deleted" true]] (:datoms body))))))))

(deftest kotoba-list-and-recent-feed-map-the-response
  (testing "list-records queries kg.list_records + maps {:uri :cid :value}"
    (let [reqs (atom [])
          resp (fn [_] {:records [{:uri "u1" :cid "c1" :value (json/generate-string {"text" "a"})}]
                        :cursor "cur"})]
      (with-kpost reqs resp
        (let [{:keys [records cursor]} (store/list-records (store/->kotoba-store kbase kgraph)
                                                           did "app.bsky.feed.post" {:limit 10})]
          (is (str/ends-with? (:url (first @reqs)) "/xrpc/com.etzhayyim.apps.kotoba.kg.list_records"))
          (is (= [{:uri "u1" :cid "c1" :value {"text" "a"}}] records))
          (is (= "cur" cursor))))))
  (testing "recent-feed queries kg.recent_feed + carries :did per record"
    (let [reqs (atom [])
          resp (fn [_] {:records [{:uri "u1" :did did :cid "c1" :value (json/generate-string {"text" "a"})}]
                        :cursor nil})]
      (with-kpost reqs resp
        (let [{:keys [records]} (store/recent-feed (store/->kotoba-store kbase kgraph)
                                                   "app.bsky.feed.post" {:limit 10})]
          (is (str/ends-with? (:url (first @reqs)) "/xrpc/com.etzhayyim.apps.kotoba.kg.recent_feed"))
          (is (= did (:did (first records)))))))))

(deftest kotoba-describe-repo-and-commit-sig
  (testing "describe-repo queries kg.describe_repo"
    (let [reqs (atom [])]
      (with-kpost reqs (constantly {:did did :collections [] :count 0})
        (store/describe-repo (store/->kotoba-store kbase kgraph) did)
        (is (str/ends-with? (:url (first @reqs)) "/xrpc/com.etzhayyim.apps.kotoba.kg.describe_repo")))))
  (testing "commit-sig is nil — the live engine signs its own commits (PDS holds no key)"
    (is (nil? (store/commit-sig (store/->kotoba-store kbase kgraph) did (.getBytes "m" "UTF-8"))))))
