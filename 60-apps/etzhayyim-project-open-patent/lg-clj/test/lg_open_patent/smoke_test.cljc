(ns lg-open-patent.smoke-test
  "Smoke tests for the lg-open-patent clj port — clojure.test analogue of the
  Python `lg/tests/test_smoke.py`, plus node-behaviour tests the original could
  not run offline (the LLM + RisingWave store are injectable here, so the seed /
  novelty / ingest pipelines verify under bb with deterministic stubs)."
  (:require [clojure.test :refer [deftest is testing]]
            [langgraph.graph :as g]
            [lg-open-patent.server :as server]
            [lg-open-patent.kotoba-datomic :as kd]
            [lg-open-patent.cron :as cron]
            [lg-open-patent.llm :as llm]
            [lg-open-patent.store :as store]
            [lg-open-patent.graphs.health :as health]
            [lg-open-patent.graphs.ingest-multi :as ingest]
            [lg-open-patent.graphs.synthesize-invention :as synth]))

(def expected-graphs #{"health" "ingest_multi" "synthesize_invention"})

(def expected-nsid-map
  {"com.etzhayyim.apps.openPatent.ingestMulti"        "ingest_multi"
   "com.etzhayyim.apps.openPatent.synthesizeInvention" "synthesize_invention"})

;; ── server registry parity (mirrors test_smoke.py) ──────────────────────────

(deftest graphs-match-expected-set
  (is (= expected-graphs (set (keys server/GRAPHS)))))

(deftest nsid-map-completeness
  (is (= expected-nsid-map server/NSID-MAP)))

(deftest nsid-map-references-known-graphs
  (doseq [[nsid gname] server/NSID-MAP]
    (is (contains? server/GRAPHS gname) (str nsid " → " gname " not in GRAPHS"))))

(deftest all-graphs-invocable
  (doseq [[nm graph] server/GRAPHS]
    (is (some? graph) (str "GRAPHS[" nm "] nil"))))

;; ── drift guards vs the deployed Python langgraph.json (mirrors test_smoke.py) ─

(deftest langgraph-json-graphs-match-server
  (let [cfg (cron/read-langgraph-json)]
    (is (some? cfg) "../lg/langgraph.json must be readable")
    (is (= expected-graphs (set (map name (keys (:graphs cfg)))))
        "drift: langgraph.json graphs vs server GRAPHS")))

(deftest langgraph-json-has-crons-for-scheduled-graphs
  (let [cg (cron/cron-graphs)]
    (is (contains? cg "ingest_multi") "ingest_multi must have a daily cron")
    (is (contains? cg "synthesize_invention") "synthesize_invention must have a weekly cron")))

(deftest cron-schedules-valid
  (doseq [spec (cron/cron-specs)]
    (is (cron/valid-crontab? (:schedule spec)) (str "bad crontab: " (:schedule spec)))))

;; ── dispatch surface (/ok, /health, /runs, /xrpc) ───────────────────────────

(deftest ok-endpoint-lists-graphs
  (let [r (server/ok)]
    (is (= 200 (:status r)))
    (is (true? (get-in r [:body :ok])))
    (is (= expected-graphs (set (get-in r [:body :graphs]))))
    (is (= "0.1.0" (get-in r [:body :version])))))

(deftest health-endpoint
  (let [r (server/health)]
    (is (= 200 (:status r)))
    (is (true? (get-in r [:body :ok])))))

(deftest unknown-assistant-404
  (is (= 404 (:status (server/dispatch-run {:assistant_id "nope" :input {}})))))

(deftest unknown-nsid-404
  (is (= 404 (:status (server/dispatch-xrpc "com.etzhayyim.apps.openPatent.unknownMethod" {})))))

(deftest api-key-guard
  (testing "no key configured → pass"
    (is (nil? (server/check-api-key ""))))
  (testing "configured key mismatch → 401"
    (binding [server/*api-key* "secret"]
      (is (= 401 (:status (server/dispatch-run {:assistant_id "health"}
                                               {:x-api-key "wrong"})))))))

(deftest kotoba-http-capability-is-required
  (is (thrown-with-msg? #?(:clj clojure.lang.ExceptionInfo :cljs :default)
                        #"explicit Kotoba HTTP capability required"
                        (kd/q (kd/->client "graph") "[:find ?e]"))))

(deftest injected-kotoba-wire-contract
  #?(:clj
     (let [seen (atom nil)]
       (binding [kd/*config* {:xrpc-url "https://kotoba.test/"
                              :bearer "secret"
                              :graph "open-patent-test"}
                 kd/*post-json!* (fn [url opts]
                                   (reset! seen [url opts])
                                   {:status 200 :body "{\"rows_edn\":[]}"})]
         (is (= [] (kd/q (kd/->client) "[:find ?e]")))
         (is (= "https://kotoba.test/xrpc/ai.etzhayyim.apps.kotoba.datomic.q"
                (first @seen)))
         (is (= "Bearer secret"
                (get-in @seen [1 :headers "Authorization"])))))))

;; ── health graph end-to-end ─────────────────────────────────────────────────

(deftest health-graph-invokes
  (is (true? (:ok (g/invoke health/GRAPH {})))))

(deftest health-via-runs
  (let [r (server/dispatch-run {:assistant_id "health" :input {}})]
    (is (= 200 (:status r)))
    (is (true? (get-in r [:body :ok])))))

;; ── Murakumo guard (ADR-2605215000) ─────────────────────────────────────────

(deftest murakumo-guard
  (testing "off-fleet endpoint refused"
    (is (thrown? #?(:clj clojure.lang.ExceptionInfo :cljs :default)
                 (llm/assert-murakumo "https://api.openai.com/v1"))))
  (testing "malformed and lookalike endpoints refused"
    (is (thrown? #?(:clj clojure.lang.ExceptionInfo :cljs :default)
                 (llm/assert-murakumo "not-a-url")))
    (is (thrown? #?(:clj clojure.lang.ExceptionInfo :cljs :default)
                 (llm/assert-murakumo "http://127.0.0.1.attacker.example:4000/v1"))))
  (testing "loopback gateway allowed"
    (is (nil? (llm/assert-murakumo "http://127.0.0.1:4000/v1")))))

(deftest live-authority-requires-explicit-capabilities
  (is (thrown-with-msg? #?(:clj clojure.lang.ExceptionInfo :cljs :default)
                        #"explicit chat capability"
                        (llm/chat "system" "user")))
  (is (thrown-with-msg? #?(:clj clojure.lang.ExceptionInfo :cljs :default)
                        #"explicit HTTP POST capability"
                        (llm/chat-with nil llm/default-config "system" "user" {}))))

(deftest injected-llm-wire-contract
  #?(:clj
     (let [seen (atom nil)
           result (llm/chat-with
                   (fn [url opts]
                     (reset! seen [url opts])
                     {:status 200
                      :body "{\"choices\":[{\"message\":{\"content\":\"safe\"}}]}"})
                   llm/default-config "system" "user"
                   {:temperature 0.2 :max-tokens 33})]
       (is (= "safe" result))
       (is (= "http://127.0.0.1:4000/v1/chat/completions" (first @seen)))
       (is (= 120000 (get-in @seen [1 :timeout])))
       (is (re-find #"max_tokens.*33" (get-in @seen [1 :body]))))))

;; ── store seam (fake) ───────────────────────────────────────────────────────

(deftest fake-store-roundtrip
  (let [s (store/->fake-patent-store
           {:patents [{:title "Quantum widget A" :publicationNumber "US1A" :tech_domain "quantum"}
                      {:title "Quantum widget B" :publicationNumber "US2B" :tech_domain "quantum"}
                      {:title "Solar panel C"    :publicationNumber "US3C" :tech_domain "solar"}]})]
    (is (= [{:domain "quantum" :count 2} {:domain "solar" :count 1}] (store/tech-trends s)))
    (is (= 2 (count (store/search-patents s "quantum"))))
    (is (= 0 (count (store/search-patents s "nonexistent"))))
    (is (= {:seed_uri "mem://seed/x"} (store/put-seed! s {:seedId "x"}))
        "put-seed! returns a uri map")))

;; ── ingest_multi graph: Follow-based ingest via stubs ───────────────────────

(deftest ingest-default-empty
  ;; Default *ingest-source* yields nothing (Follow has no local firehose).
  (binding [store/*store* (store/->fake-patent-store)]
    (let [out (g/invoke ingest/GRAPH {})]
      (is (true? (:ok out)))
      (is (= 0 (get-in out [:summary :patents])))
      (is (= 0 (get-in out [:summary :citations]))))))

(deftest ingest-happy-path-stubbed
  (binding [store/*store* (store/->fake-patent-store)
            ingest/*ingest-source*
            (fn [_cursor]
              {:patents [{:patentId "p1" :title "Widget" :jurisdiction "US"}
                         {:patentId "p2" :title "Gadget" :jurisdiction "EP"}]
               :cursor "c-2"})
            ingest/*enrich-citations*
            (fn [p] [{:citationId (str (:patentId p) "-cite") :citingPatentId (:patentId p)
                      :citedRef "US0Z" :citationType "examiner"}])]
    (let [out (g/invoke ingest/GRAPH {})]
      (is (true? (:ok out)))
      (is (= 2 (get-in out [:summary :patents])))
      (is (= 2 (get-in out [:summary :citations]))))))

;; ── synthesize_invention graph: documented 6-node pipeline ──────────────────

(defn- stub-chat
  "Deterministic LLM stub: seed step returns prose, novelty step returns a score."
  [score]
  (fn [system _user _opts]
    (if (clojure.string/includes? system "examiner")
      (str score)
      (str "Invented thing\nA novel apparatus."))))

(deftest synthesize-flags-high-novelty
  (binding [store/*store* (store/->fake-patent-store
                           {:patents [{:title "Base quantum patent" :publicationNumber "US9X"
                                       :tech_domain "quantum"}]})
            llm/*chat* (stub-chat 85)]
    (let [out (g/invoke synth/GRAPH {})]
      (is (true? (:ok out)))
      (is (= 1 (get-in out [:summary :domains])))
      (is (= 1 (get-in out [:summary :seeds])))
      (is (= 1 (get-in out [:summary :flagged])) "novelty 85 >= 60 → flagged for review")
      (is (= 60 (get-in out [:summary :threshold]))))))

(deftest synthesize-skips-low-novelty
  (binding [store/*store* (store/->fake-patent-store
                           {:patents [{:title "Base solar patent" :tech_domain "solar"}]})
            llm/*chat* (stub-chat 30)]
    (let [out (g/invoke synth/GRAPH {})]
      (is (= 1 (get-in out [:summary :seeds])))
      (is (= 0 (get-in out [:summary :flagged])) "novelty 30 < 60 → not flagged"))))

(deftest synthesize-empty-corpus
  (binding [store/*store* (store/->fake-patent-store)
            llm/*chat* (stub-chat 99)]
    (let [out (g/invoke synth/GRAPH {})]
      (is (true? (:ok out)))
      (is (= 0 (get-in out [:summary :seeds])) "no domains → no seeds"))))

(deftest synthesize-pinned-domains
  ;; caller may pin tech_domains directly (cron rotation / manual run).
  (binding [store/*store* (store/->fake-patent-store)
            llm/*chat* (stub-chat 70)]
    (let [out (g/invoke synth/GRAPH {:tech_domains ["robotics" "biotech"]})]
      (is (= 2 (get-in out [:summary :domains])))
      (is (= 2 (get-in out [:summary :seeds])))
      (is (= 2 (get-in out [:summary :flagged]))))))
