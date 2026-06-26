(ns etzhayyim.pds.store-test
  "Direct PdsStore protocol contract — exercised against BOTH the MemStore and the
  DurableStore (same datom-log semantics), so the core persistence layer has its own
  coverage independent of the xrpc/server handlers that use it. KotobaStore needs the
  live kotoba engine and is covered at cutover, not here."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.java.io :as io]
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
