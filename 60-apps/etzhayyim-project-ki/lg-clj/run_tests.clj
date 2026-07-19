;; lg-organism clj-port test runner (repo rule: run_tests.clj, NOT .sh).
;;
;;   bb run_tests.clj      (from 60-apps/etzhayyim-project-ki/lg-clj/)
;;   bb test               (bb.edn task alias)
;;
;; Exits non-zero if any test fails or errors.
(ns lg-organism.host
  (:require [babashka.http-client :as http]
            [clojure.test :as t]
            [org.httpkit.server :as httpkit]
            [lg-organism.audit :as audit]
            [lg-organism.llm :as llm]
            [lg-organism.server :as server]
            [lg-organism.smoke-test]))

(defn- env [primary fallback default]
  (or (System/getenv primary) (some-> fallback System/getenv) default))

(def murakumo-config
  {:url (env "MURAKUMO_URL" "VLLM_URL" (:url llm/default-config))
   :model (env "MURAKUMO_MODEL" "VLLM_MODEL" (:model llm/default-config))
   :timeout-sec (Double/parseDouble
                 (env "MURAKUMO_TIMEOUT_SEC" nil
                      (str (:timeout-sec llm/default-config))))})

(def audit-disabled?
  (contains? #{"1" "true" "yes"}
             (.toLowerCase ^String (env "LG_AUDIT_DISABLED" nil "false"))))

(defn murakumo-chat [system user]
  (llm/murakumo-llm-chat-with http/post murakumo-config system user))

(defn handler [request]
  (binding [llm/*llm-chat* murakumo-chat
            audit/*disabled?* audit-disabled?]
    (server/ring-handler request)))

(defn start-server! [port]
  (binding [audit/*disabled?* audit-disabled?]
    (server/start! (fn [_ options] (httpkit/run-server handler options)) port)))

(let [{:keys [fail error]} (t/run-tests 'lg-organism.smoke-test)]
  (when (pos? (+ (or fail 0) (or error 0)))
    (System/exit 1)))
