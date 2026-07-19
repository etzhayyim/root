;; lg-open-patent clj-port test runner (repo rule: run_tests.clj, NOT .sh).
;;
;;   bb run_tests.clj      (from 60-apps/etzhayyim-project-open-patent/lg-clj/)
;;   bb test               (bb.edn task alias)
;;
;; Exits non-zero if any test fails or errors.
(ns lg-open-patent.host
  (:require [babashka.http-client :as http]
            [clojure.test :as t]
            [lg-open-patent.llm :as llm]
            [lg-open-patent.smoke-test]))

(defn- env [name default] (or (System/getenv name) default))

(def config
  {:url (env "VLLM_URL" (:url llm/default-config))
   :model (env "VLLM_MODEL" (env "MURAKUMO_MODEL" (:model llm/default-config)))
   :timeout-sec (Double/parseDouble (env "VLLM_TIMEOUT_SEC" "120"))})

(defn chat [system user opts]
  (llm/chat-with http/post config system user opts))

(defn with-capabilities [f]
  (binding [llm/*chat* chat] (f)))

(let [{:keys [fail error]} (t/run-tests 'lg-open-patent.smoke-test)]
  (when (pos? (+ (or fail 0) (or error 0)))
    (System/exit 1)))
