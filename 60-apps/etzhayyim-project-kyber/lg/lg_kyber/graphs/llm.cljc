(ns lg.lg-kyber.graphs.llm
  "Guarded LLM caller for lg-kyber graphs — faithful port of graphs/_llm.py.

  Priority (unchanged from the python):
    1. Murakumo fleet (MURAKUMO_BASE_URL / gemma-4-e4b-it) — DEFAULT-PREFERRED
       per ADR-2605215000 / Rider §2(i); loopback over babashka.http-client.
    2. OpenRouter (OPENROUTER_API_KEY) fallback.
  Returns [parsed-json-or-nil source-label]; falls back to [nil \"deterministic\"] on
  missing key / network error / non-JSON.

  Parsed JSON is returned STRING-KEYED to match the kyber graphs' string-keyed state
  (the same shape `parsed[\"observation\"]` the python read). The whole caller is also
  the `:llm-api` injection seam: a graph reads `{:call-json …}` out of its state and
  calls it, so tests inject `mock-llm` and production uses `live-llm`."
  (:require [cheshire.core :as json]
            [clojure.string :as str]
            #?(:clj [babashka.http-client :as http])))

;; key under which a graph carries its injected llm-api in the state map
(def llm-api-key ::llm-api)

(defn strip-think
  "Port of `re.sub(r\"<think>…</think>\", \"\", content).strip()` — drop reasoning blocks."
  [s]
  (-> (str/replace (or s "") #"(?s)<think>.*?</think>" "")
      (str/trim)))

(defn call-llm-json
  "Port of _llm.call_llm_json. prompt → [parsed-or-nil source]. Murakumo first, then
  OpenRouter, else [nil \"deterministic\"]. opts: {:max-tokens :model-murakumo
  :model-openrouter}."
  ([prompt] (call-llm-json prompt {}))
  ([prompt {:keys [max-tokens model-murakumo model-openrouter]
            :or {max-tokens 200 model-murakumo "gemma-4-e4b-it"
                 model-openrouter "anthropic/claude-haiku-4"}}]
   #?(:clj
      (let [base (or (System/getenv "MURAKUMO_BASE_URL") "https://murakumo.etzhayyim.com")
            murakumo
            (try
              (let [meta (-> (http/get (str base "/_app/meta") {:timeout 5000})
                             :body (json/parse-string true))]
                (when (= 0 (get-in meta [:fleet :healthPct] -1))
                  (throw (ex-info "fleet offline" {})))
                (let [resp (-> (http/post (str base "/api/openai/v1/chat/completions")
                                          {:headers {"content-type" "application/json"
                                                     "x-kotodama-verified" "true"}
                                           :body (json/generate-string
                                                  {:model model-murakumo
                                                   :messages [{:role "user" :content prompt}]
                                                   :max_tokens max-tokens
                                                   :temperature 0.2
                                                   :response_format {:type "json_object"}})
                                           :timeout 30000})
                               :body (json/parse-string true))
                      content (strip-think (get-in resp [:choices 0 :message :content]))]
                  [(json/parse-string content false) "llm"]))
              (catch Exception _ nil))]
        (or murakumo
            (let [key (System/getenv "OPENROUTER_API_KEY")]
              (when key
                (try
                  (let [resp (-> (http/post "https://openrouter.ai/api/v1/chat/completions"
                                            {:headers {"authorization" (str "Bearer " key)
                                                       "content-type" "application/json"
                                                       "http-referer" "https://kyber.etzhayyim.com"
                                                       "x-title" "lg-kyber"}
                                             :body (json/generate-string
                                                    {:model model-openrouter
                                                     :messages [{:role "user" :content prompt}]
                                                     :max_tokens max-tokens
                                                     :temperature 0.2
                                                     :response_format {:type "json_object"}})
                                             :timeout 30000})
                                 :body (json/parse-string true))
                        content (get-in resp [:choices 0 :message :content])]
                    [(json/parse-string content false) "llm"])
                  (catch Exception _ nil))))
            [nil "deterministic"]))
      :default [nil "deterministic"])))

(def live-llm
  "Production llm-api map (Murakumo → OpenRouter → deterministic)."
  {:call-json call-llm-json})

(defn mock-llm
  "Deterministic llm-api for tests. `steps` is a seq of [parsed source] pairs returned
  in order on successive calls (a nil parsed ends the ReAct loop, matching the python)."
  [steps]
  (let [remaining (atom steps)]
    {:call-json (fn [_prompt & _opts]
                  (let [[head] @remaining]
                    (swap! remaining rest)
                    (or head [nil "deterministic"])))}))

(defn llm-of
  "Pull the injected llm-api out of a graph state, defaulting to the live caller."
  [state]
  (or (get state llm-api-key) live-llm))
