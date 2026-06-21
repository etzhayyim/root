(ns kaiyaku.tests.test-receipt
  "kaiyaku 解約 — catalog + authorization-receipt persistence tests (ADR-2606112201 R1).

  Proves the G9 audit trail and its safety invariants:
    - catalog-datoms emit valid [:db/add proc:<id> a v] facts for every entry
    - receipt-datoms record authorized? / status / executed(always false, G6) /
      server-signed(false, G3) — keyed on svc, never a person (N1) / score (G2)
    - no-server-key: a credential-shaped value in a descriptor is REFUSED (raises)
    - persistence: catalog + receipts append to the commit-DAG, chain, verify-chain :ok"
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [kaiyaku.methods.receipt :as receipt]
            [kaiyaku.methods.catalog :as catalog]
            [kaiyaku.methods.kotoba :as k]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))
(defn- entries [] (catalog/load-file* (io/file actor-dir "data" "cancel-procedures.kotoba.edn")))
(defn- tmp [] (str (System/getProperty "java.io.tmpdir") "/kaiyaku-receipt-test-" (gensym) ".edn"))

(def descriptors
  [{"svc" "netflix" "authorized" true "status" ":authorized-dry-run"
    "authorized_by" "member" "executed" false}
   {"svc" "x" "authorized" false "status" ":refused"}])

;; ── catalog datoms ──────────────────────────────────────────────────────────

(deftest test-catalog-datoms-shape
  (let [ds (receipt/catalog-datoms (entries))]
    (is (pos? (count ds)))
    (doseq [d ds]
      (is (= ":db/add" (first d)))                       ; op
      (is (str/starts-with? (second d) "proc:"))         ; entity id
      (is (str/starts-with? (nth d 2) ":proc/")))        ; attr
    ;; tier attr present and a string T1/T2/T3
    (is (some (fn [[_ _ a v]] (and (= a ":proc/tier") (#{"T1" "T2" "T3"} v))) ds))))

;; ── receipt datoms ──────────────────────────────────────────────────────────

(deftest test-receipt-datoms-record-outcome
  (let [ds (receipt/receipt-datoms descriptors "T0")
        ;; NB: build a map — `some` returning a `false` datom value would be skipped.
        by-attr (fn [eid a] (->> ds (filter (fn [[_ e at _]] (and (= e eid) (= at a))))
                                 first (#(when % (nth % 3)))))
        nfx "receipt:netflix:T0"]
    (is (= true (by-attr nfx ":kaiyaku.receipt/authorized")))
    (is (= ":authorized-dry-run" (by-attr nfx ":kaiyaku.receipt/status")))
    ;; G6 — executed always false
    (is (= false (by-attr nfx ":kaiyaku.receipt/executed")))
    ;; G3 — provenance, never the server
    (is (= "member" (by-attr nfx ":kaiyaku.receipt/authorized-by")))
    (is (= false (by-attr nfx ":kaiyaku.receipt/server-signed")))))

(deftest test-receipt-executed-always-false-even-when-authorized
  (let [ds (receipt/receipt-datoms [{"svc" "a" "authorized" true "status" ":authorized-dry-run"
                                     "authorized_by" "member"}] "T0")]
    (is (every? (fn [[_ _ a v]] (or (not= a ":kaiyaku.receipt/executed") (false? v))) ds))))

(deftest test-no-server-key-refuses-credential-shaped-value
  ;; a descriptor that smuggles a credential-shaped field must be REFUSED at emit.
  (is (thrown? clojure.lang.ExceptionInfo
               (receipt/receipt-datoms [{"svc" "a" "authorized" true
                                         "status" "cacao_b64:AAAA-leaked"}] "T0")))
  ;; the clean descriptors emit no credential-shaped value
  (let [ds (receipt/receipt-datoms descriptors "T0")
        joined (str/lower-case (pr-str ds))]
    (is (not (str/includes? joined "cacao")))
    (is (not (str/includes? joined "signature")))))

(deftest test-no-person-keys
  ;; N1 — a receipt is keyed on a service, never a person.
  (let [ds (receipt/receipt-datoms descriptors "T0")]
    (doseq [[_ _ a _] ds]
      (is (not (str/includes? a "person")))
      (is (not (str/includes? a "member/"))))))

;; ── persistence (commit-DAG) ────────────────────────────────────────────────

(deftest test-persist-catalog-and-receipts-chain
  (let [p (tmp)]
    (try
      (let [c1 (receipt/persist-catalog! (entries) p {:tx-id "t1" :as-of "as1"})
            c2 (receipt/persist-receipts! descriptors p {:tx-id "t2" :as-of "T0" :prev-cid c1})
            log (k/read-log p)]
        (is (str/starts-with? c1 "b"))
        (is (str/starts-with? c2 "b"))
        (is (= 2 (count log)))
        (is (= c1 (get (second log) ":tx/prev")))        ; chained
        (is (:ok (k/verify-chain p))))
      (finally (io/delete-file p true)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'kaiyaku.tests.test-receipt)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
