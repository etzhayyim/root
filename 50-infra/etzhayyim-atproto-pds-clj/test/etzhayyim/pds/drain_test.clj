(ns etzhayyim.pds.drain-test
  "Post-queue drainer: idempotent re-drain (never double-posts), retry-after-failure,
  and per-actor signing through the drain → client → PDS path — OFFLINE (the transport
  is wired to an in-process signed store, no network)."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [cheshire.core :as json]
            [etzhayyim.pds.drain :as drain]
            [etzhayyim.pds.actorkeys :as ak]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.xrpc :as xrpc]))

(def secret "node-secret")
(def base "https://pds.example")

(defn- tmp-dir [] (str (System/getProperty "java.io.tmpdir") "/pds-drain-" (hash (str (gensym)))))
(defn- rm-rf [dir]
  (let [d (io/file dir)]
    (when (.exists d) (doseq [f (.listFiles d)] (.delete f)) (.delete d))))

;; A fake PDS over an in-process multi-actor signed store. `fail` is a set of repo
;; DIDs whose createRecord returns 500 (to exercise the retry path).
(defn- fake-pds [dir fail]
  (let [st (store/->mem-store (ak/registry-signer dir secret))]
    (fn [method url body]
      (cond
        (and (= method :post) (str/ends-with? url "createRecord"))
        (if (contains? fail (:repo body))
          {:status 500 :body {"error" "Down"}}
          (xrpc/create-record st body))
        :else {:status 404 :body nil}))))

(defn- spec [n]
  {:key (str "q-" n)
   :repo (str "did:web:etzhayyim.com:actor:unspsc-" n)
   :collection "app.bsky.feed.post"
   :record {"$type" "app.bsky.feed.post" "text" (str "post " n) "createdAt" "2026-06-25T00:00:00Z"}})

(deftest drains-once-and-is-idempotent
  (testing "all posts go out once; re-draining with the returned cursor posts nothing"
    (let [dir (tmp-dir)]
      (try
        (let [specs [(spec 1) (spec 2) (spec 3)]
              t (fake-pds dir #{})
              r1 (drain/drain! base specs {:transport t})]
          (is (= 3 (count (:receipts r1))))
          (is (empty? (:errors r1)))
          (is (every? #(= 200 (:status %)) (:receipts r1)))
          (is (every? :sig (:receipts r1)) "each receipt carries the actor signature")
          (is (= #{"q-1" "q-2" "q-3"} (:posted r1)))
          ;; re-drain with the cursor → no new posts
          (let [r2 (drain/drain! base specs {:transport t :posted (:posted r1)})]
            (is (empty? (:receipts r2)))
            (is (empty? (:errors r2)))
            (is (= (:posted r1) (:posted r2)))))
        (finally (rm-rf dir))))))

(deftest failed-post-stays-unposted-and-retries
  (testing "a non-200 leaves the key un-posted; the next drain (once healthy) sends it"
    (let [dir (tmp-dir)
          down "did:web:etzhayyim.com:actor:unspsc-2"]
      (try
        (let [specs [(spec 1) (spec 2)]
              r1 (drain/drain! base specs {:transport (fake-pds dir #{down})})]
          (is (= 1 (count (:receipts r1))) "only the healthy actor posted")
          (is (= [{:key "q-2" :status 500}] (:errors r1)))
          (is (= #{"q-1"} (:posted r1)))
          ;; retry with the now-healthy PDS, carrying the cursor → only q-2 posts
          (let [r2 (drain/drain! base specs {:transport (fake-pds dir #{}) :posted (:posted r1)})]
            (is (= 1 (count (:receipts r2))))
            (is (= "q-2" (:key (first (:receipts r2)))))
            (is (= #{"q-1" "q-2"} (:posted r2)))))
        (finally (rm-rf dir))))))

(defn- qline [n]
  (json/generate-string
   {"v" 1 "ts" (* n 1000) "actorDid" (str "did:web:etzhayyim.com:actor:unspsc-" n)
    "code" (str n) "title" "t" "mood" "neutral" "contentSourceKind" "recordAnalysis"
    "text" (str "観測 " n) "lexicon" "app.bsky.feed.post" "createdAt" "2026-06-25T00:00:00.000Z"}))

(deftest parse-queue-maps-ibuki-v1-and-rejects-bad-lines
  (testing "valid v=1 lines → specs; bad JSON / wrong version / missing keys → errors"
    (let [text (str/join "\n"
                 [(qline 1)
                  ""                                   ; blank skipped
                  "{not json"                          ; bad JSON
                  (json/generate-string {"v" 2 "ts" 1 "actorDid" "x" "text" "t"
                                         "lexicon" "l" "createdAt" "c"})  ; wrong version
                  (json/generate-string {"v" 1 "ts" 5})                   ; missing keys
                  (qline 2)])
          {:keys [specs errors]} (drain/parse-queue text)]
      (is (= 2 (count specs)))
      (is (= 3 (count errors)))
      (let [s (first specs)]
        (is (= "1000" (:key s)))
        (is (= "did:web:etzhayyim.com:actor:unspsc-1" (:repo s)))
        (is (= "app.bsky.feed.post" (:collection s)))
        (is (= "app.bsky.feed.post" (get-in s [:record "$type"])))
        (is (= "観測 1" (get-in s [:record "text"])))))))

(deftest run-queue-parses-then-drains-end-to-end
  (testing "run-queue! parses an ibuki queue and drains it through the signed PDS"
    (let [dir (tmp-dir)]
      (try
        (let [text (str/join "\n" [(qline 1) (qline 2)])
              r (drain/run-queue! base text {:transport (fake-pds dir #{})})]
          (is (empty? (:parse-errors r)))
          (is (= 2 (count (:receipts r))))
          (is (every? :sig (:receipts r)))
          (is (= #{"1000" "2000"} (:posted r))))
        (finally (rm-rf dir))))))

(deftest run-file-persists-cursor-and-is-idempotent
  (testing "run-file! drains a queue file, writes the cursor, and re-runs post nothing"
    (let [dir    (tmp-dir)
          qfile  (str dir "/queue.ndjson")
          cursor (str dir "/cursor.txt")
          recf   (str dir "/receipts.ndjson")]
      (try
        (io/make-parents qfile)
        (spit qfile (str/join "\n" [(qline 1) (qline 2)]))
        (let [t (fake-pds dir #{})
              r1 (drain/run-file! {:base base :queue-path qfile :cursor-path cursor
                                   :receipts-path recf :transport t})]
          (is (= 2 (count (:receipts r1))))
          (is (= #{"1000" "2000"} (set (str/split-lines (slurp cursor)))) "cursor persisted")
          (is (= 2 (count (str/split-lines (slurp recf)))) "receipts written")
          ;; re-run reads the cursor → nothing new posts
          (let [r2 (drain/run-file! {:base base :queue-path qfile :cursor-path cursor
                                     :transport (fake-pds dir #{})})]
            (is (empty? (:receipts r2)))
            (is (= #{"1000" "2000"} (:posted r2)))))
        (finally (rm-rf dir))))))

(deftest receipts-become-receipt-datoms
  (testing "drain receipts → :receipt/* provenance datoms (what actually went out, :submitted)"
    (let [dir (tmp-dir)]
      (try
        (let [text (str/join "\n" [(qline 1) (qline 2)])
              r   (drain/run-queue! base text {:transport (fake-pds dir #{})})
              ds  (:datoms r)
              ;; fold the EAVT datoms into {entity {attr v}} the same way store does
              db  (reduce (fn [m [e a v]] (assoc-in m [e a] v)) {} ds)]
          (is (= 12 (count ds)) "6 datoms × 2 receipts")
          (is (= :submitted (get-in db ["receipt-1000" :receipt/status])))
          (is (= "1000" (get-in db ["receipt-1000" :receipt/key])))
          (is (str/starts-with? (get-in db ["receipt-1000" :receipt/uri]) "at://"))
          ;; the recorded signedBy is the actor's published key (verifiable via actors.json)
          (is (= (ak/multikey-for dir "did:web:etzhayyim.com:actor:unspsc-1" secret)
                 (get-in db ["receipt-1000" :receipt/signed-by])))
          ;; ibuki invariant: the actor never asserts :published on its own authority
          (is (not-any? #(= :published %) (map (fn [[_ _ v]] v) ds))))
        (finally (rm-rf dir))))))

(defn- shared-pds
  "A fake PDS over ONE persistent signed store (so two drains share state)."
  [dir]
  (let [st (store/->mem-store (ak/registry-signer dir secret))]
    {:store st
     :transport (fn [method url body]
                  (if (and (= method :post) (str/ends-with? url "createRecord"))
                    (xrpc/create-record st body)
                    {:status 404 :body nil}))}))

(deftest deterministic-rkey-prevents-duplicate-on-cursor-loss
  (testing "draining the same queue twice with NO cursor (crash) → ONE record, not two"
    (let [dir (tmp-dir)]
      (try
        (let [{:keys [store transport]} (shared-pds dir)
              actor "did:web:etzhayyim.com:actor:unspsc-1"
              text  (qline 1)]
          ;; simulate a crash that lost the cursor: drain the SAME queue twice fresh
          (drain/run-queue! base text {:transport transport})
          (drain/run-queue! base text {:transport transport})
          ;; the deterministic rkey makes the second write a PUT (overwrite), not a dup
          (let [recs (get-in (xrpc/list-records store {:repo actor :collection "app.bsky.feed.post"})
                             [:body "records"])]
            (is (= 1 (count recs)) "deterministic rkey → overwrite, no duplicate"))
          (is (= "1000" (drain/rkey-from "1000")))
          (is (= "x-y" (drain/rkey-from "x/y")) "invalid chars sanitised")
          (is (= "self" (drain/rkey-from ""))))
        (finally (rm-rf dir))))))

(deftest post-key-falls-back-to-content-hash
  (testing "no explicit :key → stable content-based key (same record → same key)"
    (let [s {:repo "did:web:etzhayyim.com:actor:x" :collection "c"
             :record {"$type" "t" "text" "hello"}}]
      (is (= (drain/post-key s) (drain/post-key s)))
      (is (not= (drain/post-key s)
                (drain/post-key (assoc-in s [:record "text"] "world")))))))
