(ns lg-animeka.llm
  "Injectable LLM chat seam — clj port of the vLLM (`httpx` → RunPod) edge shared
  by the generation/chat graphs (ADR-2606280030).

  DEVIATION (noted): the Python posts to a RunPod vLLM proxy URL
  (`https://…proxy.runpod.net/v1`). Per ADR-2605215000 / ADR-2606172359
  (Murakumo DEFAULT-PREFERRED) the inference edge here defaults to the Murakumo
  loopback gateway (LiteLLM 127.0.0.1:4000) and asserts the endpoint is on the
  Murakumo fleet allowlist before any request leaves the box. The chat call is
  the injectable `*chat*` seam so tests run offline with deterministic stubs.

  `*chat*` contract:  (system user opts) →
      {:content <str> :model <str>
       :prompt-tokens <int> :completion-tokens <int> :total-tokens <int>
       :latency-ms <int>}
    | {:error <str> :latency-ms <int>}"
  (:require [clojure.string :as str]))

;; Murakumo fleet (ADR-2605215000) — the ONLY inference endpoints representable.
(def murakumo-allowed-hosts
  #{"127.0.0.1:4000" "localhost:4000"
    "192.168.1.70:8077" "192.168.1.70:11434"
    "127.0.0.1:11434" "localhost:11434"})

(def llm-url
  (-> (or #?(:clj (System/getenv "VLLM_URL") :default nil) "http://127.0.0.1:4000/v1")
      (str/replace #"/+$" "")))

(def llm-model
  (or #?(:clj (System/getenv "VLLM_MODEL") :default nil) "tier0-general"))

(def llm-timeout-sec
  #?(:clj (Double/parseDouble (or (System/getenv "VLLM_TIMEOUT_SEC") "60")) :default 60.0))

(defn assert-murakumo
  "Refuse any LLM endpoint outside the Murakumo fleet (http only)."
  [endpoint]
  (when-let [[_ scheme host] (re-find #"^([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)" (str endpoint))]
    (when-not (and (= "http" (str/lower-case scheme))
                   (contains? murakumo-allowed-hosts (str/lower-case host)))
      (throw (ex-info (str "inference endpoint " (pr-str endpoint)
                           " is outside the Murakumo fleet (ADR-2605215000)")
                      {:murakumo-only-violation true :endpoint endpoint})))))

(defn- clip [s n] (let [s (str s)] (subs s 0 (min n (count s)))))

(defn default-chat
  "Default `*chat*`: POST a chat-completions request to the Murakumo loopback
  gateway. opts: {:max-tokens :temperature}. Returns the response map or
  {:error ...} (parity with each node's httpx try/except)."
  [system user {:keys [max-tokens temperature] :or {max-tokens 300 temperature 0.7}}]
  #?(:clj
     (try
       (assert-murakumo llm-url)
       (let [post  (requiring-resolve 'babashka.http-client/post)
             gen   (requiring-resolve 'cheshire.core/generate-string)
             parse (requiring-resolve 'cheshire.core/parse-string)
             resp  (post (str llm-url "/chat/completions")
                         {:headers {"Content-Type" "application/json"}
                          :timeout (long (* 1000 llm-timeout-sec))
                          :throw false
                          :body (gen {:model llm-model
                                      :messages [{:role "system" :content system}
                                                 {:role "user" :content user}]
                                      :max_tokens max-tokens
                                      :temperature temperature})})
             status (:status resp)]
         (if (>= status 400)
           {:error (str "vllm " status ": " (clip (:body resp) 200))}
           (let [body   (parse (:body resp) true)
                 choice (get-in body [:choices 0])
                 usage  (or (:usage body) {})]
             {:content (str/trim (str (get-in choice [:message :content])))
              :model (or (:model body) llm-model)
              :prompt-tokens (int (or (:prompt_tokens usage) 0))
              :completion-tokens (int (or (:completion_tokens usage) 0))
              :total-tokens (int (or (:total_tokens usage) 0))})))
       (catch Exception e {:error (clip (.getMessage e) 200)}))
     :default {:error "llm not available on this host"}))

(def ^:dynamic *chat* default-chat)

(defn chat
  "Convenience: (chat system user) | (chat system user opts). Always returns a
  map (never throws to the node)."
  ([system user] (chat system user {}))
  ([system user opts] (*chat* system user opts)))

(defn content
  "Best-effort content string from a chat result ('' on error)."
  [res]
  (if (and (map? res) (not (:error res))) (str (:content res)) ""))
