(ns media-gamers.llm
  "media-gamers LLM helper — clj twin of the `_chat` coroutine shared by the
  guide_generator / autopilot / ingest_charts python graphs.

  Port notes (ADR-2606280030 + ADR-2605215000):
    - httpx.AsyncClient → babashka.http-client (clj, bb-built-in).
    - JSON          → cheshire.
    - LLM endpoint  → the **Murakumo loopback** is the DEFAULT (LiteLLM gateway
      127.0.0.1:4000, OpenAI-compatible /chat/completions). The python code's
      RunPod fallback is DROPPED per the Murakumo-default inference rule
      (ADR-2605215000 / 2606172359) — RunPod is still honoured ONLY if its env
      is explicitly set, exactly as the python multi-endpoint loop did, so the
      topology (try-each-endpoint, fail-open to \"\") is preserved.
    - no-server-key: Murakumo loopback needs no bearer; `Authorization` is sent
      only when a key env is present.

  Fail-open: returns \"\" on any error / no reachable endpoint (byte-for-byte the
  python contract — an empty string flows downstream as an `:error` later)."
  (:require [clojure.string :as str]
            #?(:clj [babashka.http-client :as http])
            #?(:clj [cheshire.core :as json])))

(defn- getenv [k default]
  #?(:clj (or (System/getenv k) default) :default default))

(def think-re #"(?s)<think>.*?</think>")

(defn strip-think [s] (-> (str s) (str/replace think-re "") str/trim))

(defn endpoints
  "Resolve the ordered [url key] endpoint list, Murakumo first (loopback default),
  RunPod only if its env is set. Mirrors the python `endpoints` accumulation."
  []
  (let [mk-url (-> (getenv "MURAKUMO_OPENAI_URL" "http://127.0.0.1:4000/v1")
                   str (str/replace #"/+$" ""))
        mk-key (getenv "MURAKUMO_API_KEY" "")
        rp-url (-> (getenv "RUNPOD_OPENAI_URL" "") str (str/replace #"/+$" ""))
        rp-key (getenv "RUNPOD_API_KEY" "")]
    (cond-> []
      (seq mk-url) (conj [mk-url mk-key])
      (and (seq rp-url) (seq rp-key)) (conj [rp-url rp-key]))))

(def llm-model (delay (getenv "LLM_MODEL" "qwen3.5-4b")))
(def llm-timeout-ms
  (delay #?(:clj (long (* 1000 (Double/parseDouble (getenv "LLM_TIMEOUT_SEC" "60"))))
            :default 60000)))

#?(:clj
   (defn chat
     "Port of `_chat`: POST an OpenAI-style chat completion to each endpoint in
     turn; return the first non-error assistant message (think-stripped), or \"\"
     if every endpoint fails / none configured."
     [system user & {:keys [max-tokens temp] :or {max-tokens 1000 temp 0.7}}]
     (let [eps (endpoints)]
       (if (empty? eps)
         ""
         (loop [[[url key] & more] eps]
           (if (nil? url)
             ""
             (let [text
                   (try
                     (let [body (json/generate-string
                                 {:model @llm-model
                                  :messages [{:role "system" :content system}
                                             {:role "user" :content user}]
                                  :max_tokens max-tokens
                                  :temperature temp})
                           headers (cond-> {"Content-Type" "application/json"}
                                     (seq key) (assoc "Authorization" (str "Bearer " key)))
                           resp (http/post (str url "/chat/completions")
                                           {:body body :headers headers
                                            :timeout @llm-timeout-ms :throw false})]
                       (if (>= (:status resp) 400)
                         ::retry
                         (-> (json/parse-string (:body resp) true)
                             :choices first :message :content (or "")
                             strip-think)))
                     (catch Exception _ ::retry))]
               (if (= text ::retry)
                 (recur more)
                 text))))))))
