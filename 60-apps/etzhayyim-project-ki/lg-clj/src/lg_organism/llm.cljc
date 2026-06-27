(ns lg-organism.llm
  "LLM edge for the organism — Murakumo loopback gateway (ADR-2605215000).

  The Python `hakkou.llmTransform` worker calls an inference endpoint. Per the
  Murakumo DEFAULT-PREFERRED policy the only representable inference target is
  the LiteLLM loopback gateway (127.0.0.1:4000) / on-fleet Ollama. `*llm-chat*`
  is an injectable seam: the default is offline-safe (no network) so every cljc
  ns loads + tests pass under bb; `murakumo-llm-chat` is the real swap and is
  guarded by `assert-murakumo` (refuses any off-fleet endpoint)."
  (:require [clojure.string :as str]))

(defn- env [k] #?(:clj (System/getenv k) :cljs nil))

(def murakumo-allowed-hosts
  #{"127.0.0.1:4000" "localhost:4000"
    "192.168.1.70:8077" "192.168.1.70:11434"
    "127.0.0.1:11434" "localhost:11434"})

(def llm-url
  (-> (or (env "MURAKUMO_URL") (env "VLLM_URL") "http://127.0.0.1:4000/v1")
      (str/replace #"/+$" "")))
(def llm-model (or (env "MURAKUMO_MODEL") (env "VLLM_MODEL") "gemma3:4b"))
(def llm-timeout-sec
  #?(:clj (Double/parseDouble (or (env "MURAKUMO_TIMEOUT_SEC") "120"))
     :cljs 120))

(defn- clip [s n] (let [s (str s)] (subs s 0 (min n (count s)))))

(defn assert-murakumo
  "Refuse any inference endpoint outside the Murakumo fleet (http only)."
  [endpoint]
  (when-let [[_ scheme host]
             (re-find #"^([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)" (str endpoint))]
    (when-not (and (= "http" (str/lower-case scheme))
                   (contains? murakumo-allowed-hosts (str/lower-case host)))
      (throw (ex-info (str "inference endpoint " (pr-str endpoint)
                           " is outside the Murakumo fleet (ADR-2605215000)")
                      {:murakumo-only-violation true :endpoint endpoint})))))

(defn murakumo-llm-chat
  "Real swap for `*llm-chat*`: POST chat-completions to the Murakumo loopback
  gateway. Returns the assistant text or {:error ...}. Uses requiring-resolve so
  the namespace still loads where babashka.http-client/cheshire are absent."
  [system user]
  #?(:clj
     (try
       (assert-murakumo llm-url)
       (let [post     (requiring-resolve 'babashka.http-client/post)
             generate (requiring-resolve 'cheshire.core/generate-string)
             parse    (requiring-resolve 'cheshire.core/parse-string)
             resp     (post (str llm-url "/chat/completions")
                            {:headers {"Content-Type" "application/json"}
                             :timeout (long (* 1000 llm-timeout-sec))
                             :body (generate {:model llm-model
                                              :messages [{:role "system" :content system}
                                                         {:role "user" :content user}]
                                              :temperature 0.3})})
             status   (:status resp)]
         (if (>= status 400)
           {:error (str "murakumo " status ": " (clip (:body resp) 200))}
           (let [body (parse (:body resp) true)
                 txt  (some-> (get-in body [:choices 0 :message :content]) str str/trim)]
             (if (seq txt) txt {:error "LLM returned empty completion"}))))
       (catch Exception e {:error (clip (#?(:clj .getMessage) e) 200)}))
     :cljs {:error "murakumo-llm-chat unavailable in cljs"}))

(def ^:dynamic *llm-chat*
  "Injectable LLM edge. Default is an offline-safe deterministic stub so the
  organism dispatcher is verifiable under bb without a live Murakumo gateway.
  Rebind to `murakumo-llm-chat` (or a test stub) at deploy/test time."
  (fn [_system user] (str "[stub-llm] " (clip user 80))))
