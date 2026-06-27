(ns lg-open-patent.llm
  "Murakumo-guarded LLM edge for the open-patent generation graphs.

  The Python graphs (re-exported from `kotodama.langgraph_graphs.*`) call an LLM
  for seed synthesis (temperature 0.6) and novelty assessment. Per ADR-2605215000
  / ADR-2606172359 (Murakumo DEFAULT-PREFERRED, loopback only) the inference edge
  here defaults to the Murakumo loopback gateway (LiteLLM 127.0.0.1:4000,
  no-server-key/read-only) and REFUSES any endpoint outside the fleet allowlist.

  Injectable: rebind `*chat*` in tests to a deterministic stub (no network)."
  (:require [clojure.string :as str]))

(defn- env [k default] #?(:clj (or (System/getenv k) default) :cljs default))

;; Murakumo fleet (ADR-2605215000) — the ONLY inference endpoints representable.
(def murakumo-allowed-hosts
  #{"127.0.0.1:4000" "localhost:4000"
    "192.168.1.70:8077" "192.168.1.70:11434"
    "127.0.0.1:11434" "localhost:11434"})

(def llm-url   (-> (env "VLLM_URL" "http://127.0.0.1:4000/v1") (str/replace #"/+$" "")))
(def llm-model (or (env "VLLM_MODEL" nil) (env "MURAKUMO_MODEL" nil) "gemma3:4b"))
(def llm-timeout-sec (Double/parseDouble (env "VLLM_TIMEOUT_SEC" "120")))

(defn- clip [s n] (let [s (str s)] (subs s 0 (min n (count s)))))

(defn assert-murakumo
  "Refuse any LLM endpoint outside the Murakumo fleet (http loopback only)."
  [endpoint]
  (when-let [[_ scheme host] (re-find #"^([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)" (str endpoint))]
    (when-not (and (= "http" (str/lower-case scheme))
                   (contains? murakumo-allowed-hosts (str/lower-case host)))
      (throw (ex-info (str "inference endpoint " (pr-str endpoint)
                           " is outside the Murakumo fleet (ADR-2605215000)")
                      {:murakumo-only-violation true :endpoint endpoint})))))

(defn default-chat
  "Default `*chat*`: POST a chat-completions request to the Murakumo loopback
  gateway. Returns the assistant text string, or {:error ...}.

  `opts` keys: :temperature (default 0.6), :max-tokens (default 1024)."
  [system user opts]
  (try
    (assert-murakumo llm-url)
    (let [post     (requiring-resolve 'babashka.http-client/post)
          generate (requiring-resolve 'cheshire.core/generate-string)
          parse    (requiring-resolve 'cheshire.core/parse-string)
          resp     (post (str llm-url "/chat/completions")
                         {:headers {"Content-Type" "application/json"}
                          :timeout (long (* 1000 llm-timeout-sec))
                          :throw false
                          :body (generate {:model llm-model
                                           :messages [{:role "system" :content system}
                                                      {:role "user" :content user}]
                                           :max_tokens (or (:max-tokens opts) 1024)
                                           :temperature (or (:temperature opts) 0.6)})})
          status   (:status resp)]
      (if (>= status 400)
        {:error (str "vllm " status ": " (clip (:body resp) 200))}
        (let [body (parse (:body resp) true)
              txt  (some-> (get-in body [:choices 0 :message :content]) str str/trim)]
          (if (seq txt) txt {:error "LLM returned empty completion"}))))
    (catch #?(:clj Exception :cljs :default) e
      {:error (clip #?(:clj (.getMessage e) :cljs (str e)) 200)})))

(def ^:dynamic *chat* default-chat)

(defn chat
  "Invoke the (injectable) LLM edge."
  ([system user] (chat system user {}))
  ([system user opts] (*chat* system user opts)))
