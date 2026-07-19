(ns lg-organism.llm
  "LLM edge for the organism — Murakumo loopback gateway (ADR-2605215000).

  The Python `hakkou.llmTransform` worker calls an inference endpoint. Per the
  Murakumo DEFAULT-PREFERRED policy the only representable inference target is
  the LiteLLM loopback gateway (127.0.0.1:4000) / on-fleet Ollama. `*llm-chat*`
  is an injectable seam: no network authority exists unless the host binds it;
  `murakumo-llm-chat-with` is the explicit-capability implementation and is
  guarded by `assert-murakumo` (refuses any off-fleet endpoint)."
  (:require #?(:clj [cheshire.core :as json])
            [clojure.string :as str]))

(def murakumo-allowed-hosts
  #{"127.0.0.1:4000" "localhost:4000"
    "192.168.1.70:8077" "192.168.1.70:11434"
    "127.0.0.1:11434" "localhost:11434"})

(def default-config {:url "http://127.0.0.1:4000/v1"
                     :model "gemma3:4b"
                     :timeout-sec 120.0})

(defn- clip [s n] (let [s (str s)] (subs s 0 (min n (count s)))))

(defn assert-murakumo
  "Refuse any inference endpoint outside the Murakumo fleet (http only)."
  [endpoint]
  (let [[_ scheme host] (or (re-find #"^([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)" (str endpoint))
                            [nil nil nil])]
    (when-not (and (= "http" (some-> scheme str/lower-case))
                   (contains? murakumo-allowed-hosts (some-> host str/lower-case)))
      (throw (ex-info (str "inference endpoint " (pr-str endpoint)
                           " is outside the Murakumo fleet (ADR-2605215000)")
                      {:murakumo-only-violation true :endpoint endpoint})))))

(defn murakumo-llm-chat-with
  "POST through a host-provided capability and explicit configuration."
  [http-post {:keys [url model timeout-sec]
              :or {url (:url default-config)
                   model (:model default-config)
                   timeout-sec (:timeout-sec default-config)}} system user]
  (when-not (fn? http-post)
    (throw (ex-info "KI inference requires an explicit HTTP POST capability"
                    {:capability :ki/murakumo-http-post})))
  #?(:clj
     (try
       (let [url (str/replace (str url) #"/+$" "")]
         (assert-murakumo url)
         (let [resp     (http-post (str url "/chat/completions")
                            {:headers {"Content-Type" "application/json"}
                             :timeout (long (* 1000 (double timeout-sec)))
                             :body (json/generate-string {:model model
                                              :messages [{:role "system" :content system}
                                                         {:role "user" :content user}]
                                              :temperature 0.3})})
             status   (:status resp)]
         (if (>= status 400)
           {:error (str "murakumo " status ": " (clip (:body resp) 200))}
           (let [body (json/parse-string (:body resp) true)
                 txt  (some-> (get-in body [:choices 0 :message :content]) str str/trim)]
             (if (seq txt) txt {:error "LLM returned empty completion"})))))
       (catch Exception e {:error (clip (#?(:clj .getMessage) e) 200)}))
     :cljs {:error "murakumo-llm-chat unavailable in cljs"}))

(def ^:dynamic *llm-chat*
  "Host-bound LLM edge. Nil denies ambient network authority."
  nil)

(defn llm-chat [system user]
  (when-not (fn? *llm-chat*)
    (throw (ex-info "KI inference requires an explicit chat capability"
                    {:capability :ki/chat})))
  (*llm-chat* system user))
