;; lg-pregel clj-port test runner (repo rule: run_tests.clj, NOT .sh).
;;
;;   bb run_tests.clj      (from 60-apps/etzhayyim-project-pregel/lg-clj/)
;;   bb test               (bb.edn task alias)
;;
;; Exits non-zero if any test fails or errors.
(ns lg-pregel.host
  (:require [babashka.http-client :as http]
            [clojure.test :as t]
            [org.httpkit.server :as httpkit]
            [lg-pregel.murakumo :as murakumo]
            [lg-pregel.server :as server]
            [lg-pregel.smoke-test]))

(defn- env [name default] (or (System/getenv name) default))

(def murakumo-config
  {:url (env "MURAKUMO_BASE_URL" (:url murakumo/default-config))
   :model (env "MURAKUMO_MODEL" (:model murakumo/default-config))})

(def api-key (env "LG_PREGEL_API_KEY" ""))

(defn murakumo-chat [system user]
  (murakumo/chat-with http/post murakumo-config system user))

(defn handler [request]
  (binding [murakumo/*llm-chat* murakumo-chat
            server/*api-key* api-key]
    (server/ring-handler request)))

(defn start-server! [port]
  (server/serve! (fn [_ options] (httpkit/run-server handler options))
                 {:port port}))

(let [{:keys [fail error]} (t/run-tests 'lg-pregel.smoke-test)]
  (when (pos? (+ (or fail 0) (or error 0)))
    (System/exit 1)))
