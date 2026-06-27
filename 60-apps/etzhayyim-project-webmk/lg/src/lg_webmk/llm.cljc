(ns lg-webmk.llm
  "LLM inference via the Murakumo fleet loopback (ADR-2605215000 / 2606172359):
  the LiteLLM gateway (OpenAI-compatible /v1/chat/completions) over
  babashka.http-client — replacing the Python langchain_anthropic / ChatAnthropic.
  Default model gemma-4-e4b-it (lg/CLAUDE.md). Read-only call, fail-open: any
  error returns nil so the caller falls back to a deterministic template, exactly
  like the Python try/except graceful fallback."
  (:require [cheshire.core :as json]
            [babashka.http-client :as http]
            [clojure.string :as str]))

(defn- env [k default] (or (System/getenv k) default))

(def ^:private llm-url     (env "WEBMK_LLM_URL" "http://llm.etzhayyim.com"))
(def ^:private llm-api-key (env "WEBMK_LLM_API_KEY" ""))
(def ^:private llm-model   (env "WEBMK_LLM_MODEL" "gemma-4-e4b-it"))
(def ^:private llm-timeout (long (* 1000 (Long/parseLong (env "WEBMK_LLM_TIMEOUT" "30")))))

(defn complete
  "Single-prompt chat completion. Returns the assistant text, or nil on any
  failure (the caller then uses its template fallback). max-tokens optional."
  ([prompt] (complete prompt 1024))
  ([prompt max-tokens]
   (try
     (let [headers (cond-> {"Content-Type" "application/json"}
                     (seq llm-api-key) (assoc "Authorization" (str "Bearer " llm-api-key)))
           body {:model llm-model
                 :max_tokens max-tokens
                 :messages [{:role "user" :content prompt}]}
           resp (http/post (str (str/replace llm-url #"/+$" "") "/v1/chat/completions")
                           {:headers headers
                            :body (json/generate-string body)
                            :timeout llm-timeout
                            :throw false})]
       (when (= 200 (:status resp))
         (let [parsed (json/parse-string (:body resp) true)
               txt (get-in parsed [:choices 0 :message :content])]
           (when (and txt (seq (str/trim txt))) txt))))
     (catch Exception _ nil))))
