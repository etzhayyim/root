(ns kaiyaku.tests.test-pipeline
  "kaiyaku 解約 — R1 END-TO-END pipeline test (ADR-2606112201 R1).

  One integration that threads analyze→plan→enrich→dispatch→serviceop→receipt over a
  minimal in-memory ledger, proving the seven R1 pieces COMPOSE (and catches interface
  drift any single change would introduce). Uses a 2-tie graph:
    - 'netflix'           (cancel api :none / browser :prohibited) → T3 → member-submits, no op
    - 'generic-saas-api'  (cancel api :available)                  → T1 → karakuri ServiceOp
  both real catalog ids (so enrichment fires), both member-approved in the capability."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]
            [kaiyaku.methods.pipeline :as pipeline]
            [kaiyaku.methods.catalog :as catalog]
            [kaiyaku.methods.karakuri-bridge :as kb]
            [kaiyaku.methods.kotoba :as k]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))
(defn- catalog-by-id []
  (catalog/by-id (catalog/load-file* (io/file actor-dir "data" "cancel-procedures.kotoba.edn"))))

;; minimal string-key ledger graph (the analyze/load-file* parsed shape)
(def member "member:test")
(defn- node [id api browser]
  {":svc/id" id ":svc/label" id ":svc/kind" ":subscription" ":svc/category" "x"
   ":svc/cancel" {":api" api ":browser" browser ":self-submit" true}
   ":svc/notice-days" 0 ":svc/penalty-jpy" 0})
(def nodes
  {member {":member/id" member ":member/label" "Test"}
   "netflix" (node "netflix" ":none" ":prohibited")
   "generic-saas-api" (node "generic-saas-api" ":available" ":prohibited")})
(defn- edge [to]
  {":en/from" member ":en/to" to ":en/kind" ":subscribes"
   ":en/monthly-cost-jpy" 1500.0 ":en/usage-score" 5.0 ":en/last-used-days" 10.0})
(def edges [(edge "netflix") (edge "generic-saas-api")])

(def bundle
  {"cacao_b64" "opaque" "aud" "did:web:etzhayyim.com" "capability" "service:cancel"
   "graph" "graph:kaiyaku" "exp" 9999999999 "nonce" "n"
   "approved" ["netflix" "generic-saas-api"]})

(defn- run [] (pipeline/run {:nodes nodes :edges edges :catalog (catalog-by-id)
                             :bundle bundle :now-epoch 1000 :as-of "T0"}))

(deftest test-pipeline-plans-and-tiers
  (let [{:keys [plans]} (run)]
    (is (= 2 (count plans)))
    (is (= #{"netflix" "generic-saas-api"} (set (map #(get % "svc") plans))))
    (let [by-svc (into {} (map (juxt #(get % "svc") #(get % "tier")) plans))]
      (is (= "T3" (by-svc "netflix")))
      (is (= "T1" (by-svc "generic-saas-api"))))))

(deftest test-pipeline-enrichment-fires
  (let [{:keys [enriched]} (run)]
    (is (every? #(true? (get % "catalog_coverage")) enriched))
    (is (every? #(seq (get-in % ["catalog" "self_submit_steps"])) enriched))))

(deftest test-pipeline-all-authorized
  (let [{:keys [descriptors]} (run)]
    (is (every? #(true? (get % "authorized")) descriptors))
    ;; G6 — nothing executed
    (is (every? #(false? (get % "executed")) descriptors))))

(deftest test-pipeline-serviceops-only-t1-t2
  (let [{:keys [serviceops]} (run)]
    ;; only the T1 plan becomes a karakuri op; T3 (netflix) is member-submits → no op
    (is (= 1 (count serviceops)))
    (is (= "generic-saas-api" (:service (first serviceops))))
    (is (= "delete" (:verb (first serviceops))))))

(deftest test-pipeline-serviceops-valid-against-karakuri
  (let [{:keys [serviceops]} (run)
        lex (kb/lexicon (io/file (.getParentFile actor-dir) "karakuri" "lex" "serviceOp.edn"))]
    (doseq [op serviceops]
      (is (= [] (kb/validate-serviceop op lex))))))

(deftest test-pipeline-receipts-and-exactly-once
  (let [{:keys [receipt-datoms severed]} (run)]
    (is (pos? (count receipt-datoms)))
    ;; both T1+T3 authorized; only the T1 (:authorized-dry-run) advances the severed cursor
    (is (= #{"generic-saas-api"} severed))
    ;; G6 — every receipt executed=false
    (is (every? (fn [[_ _ a v]] (or (not= a ":kaiyaku.receipt/executed") (false? v))) receipt-datoms))))

(deftest test-pipeline-persist-roundtrip
  (let [p (str (System/getProperty "java.io.tmpdir") "/kaiyaku-pipeline-" (gensym) ".edn")]
    (try
      (let [r (pipeline/run+persist! {:nodes nodes :edges edges :catalog (catalog-by-id)
                                      :bundle bundle :now-epoch 1000}
                                     p {:tx-id "t1" :as-of "T0"})]
        (is (clojure.string/starts-with? (:receipt-cid r) "b"))
        (is (= 1 (count (k/read-log p))))
        (is (:ok (k/verify-chain p))))
      (finally (io/delete-file p true)))))

(deftest test-pipeline-unapproved-svc-refused
  ;; a capability that approves only netflix → the T1 tie is refused (G5 in the leash)
  (let [b (assoc bundle "approved" ["netflix"])
        {:keys [descriptors serviceops]} (pipeline/run {:nodes nodes :edges edges
                                                        :catalog (catalog-by-id) :bundle b
                                                        :now-epoch 1000 :as-of "T0"})
        by-svc (into {} (map (juxt #(get % "svc") identity) descriptors))]
    (is (true? (get (by-svc "netflix") "authorized")))
    (is (false? (get (by-svc "generic-saas-api") "authorized")))
    ;; the refused tie produces no karakuri op
    (is (empty? serviceops))))

(deftest test-member-report-honest
  (let [md (pipeline/member-report (run))]
    ;; dry-run honesty up front
    (is (clojure.string/includes? md "dry-run"))
    (is (clojure.string/includes? md "まだ何も実行されていません"))
    ;; both services appear with their disclosed procedure steps
    (is (clojure.string/includes? md "netflix"))
    (is (clojure.string/includes? md "generic-saas-api"))
    (is (clojure.string/includes? md "手順:"))
    ;; never claims execution
    (is (clojure.string/includes? md "executed: false"))
    (is (not (clojure.string/includes? md "executed: true")))))

(deftest test-member-report-flags-operator-verification
  ;; catalog entries are operator-verified=false → the ⚠ flag must appear
  (let [md (pipeline/member-report (run))]
    (is (clojure.string/includes? md "operator 検証が必要"))))

(deftest test-member-report-shows-refusal-reason
  ;; with a capability approving only netflix, the T1 tie is refused → its reason shows
  (let [b (assoc bundle "approved" ["netflix"])
        r (pipeline/run {:nodes nodes :edges edges :catalog (catalog-by-id)
                         :bundle b :now-epoch 1000 :as-of "T0"})
        md (pipeline/member-report r)]
    (is (clojure.string/includes? md "理由:"))
    (is (clojure.string/includes? md "allowlist"))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'kaiyaku.tests.test-pipeline)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
