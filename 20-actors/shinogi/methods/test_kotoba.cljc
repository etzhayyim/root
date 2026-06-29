#!/usr/bin/env bb
;; shinogi 鎬 — findings-ledger tests (content-address + tamper-evident chain).
(ns shinogi.methods.test-kotoba
  (:require [shinogi.methods.kotoba :as k]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]))

(defn- tmp-log []
  (str (io/file (System/getProperty "java.io.tmpdir")
                (str "shinogi-test-ledger-" (hash (str (gensym))) ".edn"))))

(def ds1 [(k/add "shinogi-stock:effort-inflation" ":shinogi.exam.stock/regime" ":vicious")
          (k/add "shinogi-stock:effort-inflation" ":shinogi/hypothesis" ":true")])
(def ds2 [(k/add "shinogi-stock:effort-inflation" ":shinogi.exam.stock/regime" ":virtuous")])

;; ── content address is deterministic + prev-sensitive ────────────────────────
(deftest cid-deterministic
  (is (= (k/tx-cid ds1) (k/tx-cid ds1)) "same datoms → same cid")
  (is (str/starts-with? (k/tx-cid ds1) "b") "cid is 'b'+sha256")
  (is (not= (k/tx-cid ds1 "") (k/tx-cid ds1 "bprev")) "prev-cid changes the cid (chaining)"))

;; ── append + read round-trips, chain verifies ────────────────────────────────
(deftest append-read-verify
  (let [log (tmp-log)]
    (try
      (let [tx1 (k/make-tx ds1 "t1" "as-of-1" "")
            c1 (k/append-tx tx1 log)
            tx2 (k/make-tx ds2 "t2" "as-of-2" c1)
            c2 (k/append-tx tx2 log)
            txs (k/read-log log)]
        (is (= 2 (count txs)) "two txs read back")
        (is (= c2 (k/head-cid log)) "head is the last cid")
        (is (= "" (get (first txs) ":tx/prev")) "first tx prev is empty")
        (is (= c1 (get (second txs) ":tx/prev")) "second tx chains to first")
        (let [v (k/verify-chain log)]
          (is (:ok v) "chain verifies")
          (is (= 2 (:length v)))))
      (finally (io/delete-file log true)))))

;; ── tamper detection ─────────────────────────────────────────────────────────
(deftest tamper-breaks-chain
  (let [log (tmp-log)]
    (try
      (k/append-tx (k/make-tx ds1 "t1" "a1" "") log)
      ;; corrupt the file: flip a recorded regime value in the datoms
      (let [body (slurp log)
            corrupted (clojure.string/replace body ":vicious" ":virtuous")]
        (spit log corrupted))
      (is (not (:ok (k/verify-chain log))) "corrupted datoms break the verify-chain")
      (finally (io/delete-file log true)))))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'shinogi.methods.test-kotoba)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))
