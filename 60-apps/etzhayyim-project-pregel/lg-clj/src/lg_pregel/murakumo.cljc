(ns lg-pregel.murakumo
  "Murakumo loopback LLM seam (ADR-2605215000) for the pregel triage actors.

  The external `kotodama` classifier talks to an LLM; per repo policy any LLM
  call MUST go through the Murakumo loopback gateway at 127.0.0.1:4000
  (no-server-key / read-only). This ns provides the guard + a default chat fn so
  any clj graph node that wants the classifier has a faithful, fleet-safe seam.
  `httpx` (Python) → `babashka.http-client`; JSON → `cheshire` (loaded lazily so
  the ns also compiles/loads under plain bb without the deps on the path)."
  (:require [clojure.string :as str]))

(def gateway
  (or (System/getenv "MURAKUMO_BASE_URL") "http://127.0.0.1:4000/v1"))

(defn assert-murakumo
  "Throw unless `url` targets the Murakumo loopback gateway (127.0.0.1 / ::1 /
  localhost). Mirrors the off-fleet refusal guard used across the wave-1 twins."
  [url]
  (let [u (str/lower-case (str url))]
    (when-not (or (str/includes? u "127.0.0.1")
                  (str/includes? u "localhost")
                  (str/includes? u "[::1]"))
      (throw (ex-info "off-fleet LLM endpoint refused (Murakumo loopback only)"
                      {:url url})))
    nil))

(defn default-chat
  "Default `*llm-chat*`: POST an OpenAI-shaped chat completion to the Murakumo
  loopback. Read-only / no server key. Returns the assistant message string."
  [system user]
  (assert-murakumo gateway)
  (let [post  (requiring-resolve 'babashka.http-client/post)
        gen   (requiring-resolve 'cheshire.core/generate-string)
        parse (requiring-resolve 'cheshire.core/parse-string)
        model (or (System/getenv "MURAKUMO_MODEL") "gpt-4o-mini")
        body  (gen {:model model
                    :messages [{:role "system" :content system}
                               {:role "user" :content user}]})
        resp  (post (str gateway "/chat/completions")
                    {:headers {"content-type" "application/json"}
                     :body body :throw false})
        data  (parse (:body resp) true)]
    (get-in data [:choices 0 :message :content])))

(def ^:dynamic *llm-chat* default-chat)
