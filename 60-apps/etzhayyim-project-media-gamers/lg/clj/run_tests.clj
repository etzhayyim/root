#!/usr/bin/env bb
;; media-gamers LangGraph clj-port test runner (repo rule: run_tests.clj, NOT .sh).
;; Usage (from this dir):  bb run_tests.clj   |   bb test
(require '[babashka.http-client :as http]
         '[clojure.test :as t]
         '[media-gamers.audit :as audit]
         '[media-gamers.llm :as llm]
         '[media-gamers.graphs.autopilot :as autopilot]
         '[media-gamers.graphs.guide-generator :as guide]
         '[media-gamers.graphs.health :as health]
         '[media-gamers.graphs.ingest-charts :as charts]
         'tests.test-smoke)

(defn- env [name default] (or (System/getenv name) default))
(def app-did (env "MEDIA_GAMERS_APP_DID" "did:web:media-gamers.etzhayyim.com"))
(def endpoints
  (cond-> [[(env "MURAKUMO_OPENAI_URL" "http://127.0.0.1:4000/v1")
            (env "MURAKUMO_API_KEY" "")]]
    (and (seq (env "RUNPOD_OPENAI_URL" "")) (seq (env "RUNPOD_API_KEY" "")))
    (conj [(env "RUNPOD_OPENAI_URL" "") (env "RUNPOD_API_KEY" "")])) )

(defn with-capabilities [f]
  (binding [audit/*config* {:url (env "BPMN_DISPATCHER_INTERNAL_URL" (:url audit/default-config))
                            :secret (env "BPMN_DISPATCHER_INTERNAL_SECRET" "")
                            :disabled? (= "1" (env "LG_AUDIT_DISABLED" "0"))
                            :timeout-ms (long (* 1000 (Double/parseDouble (env "LG_AUDIT_TIMEOUT_SEC" "3.0"))))}
            audit/*http-post* http/post
            llm/*config* {:endpoints endpoints :model (env "LLM_MODEL" "qwen3.5-4b")
                          :timeout-ms (long (* 1000 (Double/parseDouble (env "LLM_TIMEOUT_SEC" "60"))))}
            llm/*http-post* http/post
            health/*config* {:app-did app-did
                             :store-configured? (boolean (or (seq (env "RW_URL" ""))
                                                             (seq (env "KOTOBA_URL" ""))))}
            charts/*config* {:app-did app-did} charts/*http-get* http/get
            guide/*config* {:app-did app-did
                            :commit-guide-url (env "COMMIT_GUIDE_XRPC_URL" (:commit-guide-url guide/*config*))}
            guide/*http-post* http/post
            autopilot/*config* {:app-did app-did
                                :repo-did (env "MEDIA_GAMERS_REPO_DID" (:repo-did autopilot/*config*))
                                :pds-url (env "PDS_URL" (:pds-url autopilot/*config*))
                                :commit-guide-url (env "COMMIT_GUIDE_XRPC_URL" (:commit-guide-url autopilot/*config*))}
            autopilot/*http-post* http/post]
    (f)))

(let [{:keys [fail error]} (t/run-tests 'tests.test-smoke)]
  (System/exit (if (zero? (+ (or fail 0) (or error 0))) 0 1)))
