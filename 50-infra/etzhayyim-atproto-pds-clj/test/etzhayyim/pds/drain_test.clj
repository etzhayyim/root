(ns etzhayyim.pds.drain-test
  "Post-queue drainer: idempotent re-drain (never double-posts), retry-after-failure,
  and per-actor signing through the drain → client → PDS path — OFFLINE (the transport
  is wired to an in-process signed store, no network)."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.java.io :as io]
            [clojure.string :as str]
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

(deftest post-key-falls-back-to-content-hash
  (testing "no explicit :key → stable content-based key (same record → same key)"
    (let [s {:repo "did:web:etzhayyim.com:actor:x" :collection "c"
             :record {"$type" "t" "text" "hello"}}]
      (is (= (drain/post-key s) (drain/post-key s)))
      (is (not= (drain/post-key s)
                (drain/post-key (assoc-in s [:record "text"] "world")))))))
