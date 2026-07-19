(ns lg-open-patent.llm
  "Murakumo-guarded LLM edge for the open-patent generation graphs.

  The Python graphs (re-exported from `kotodama.langgraph_graphs.*`) call an LLM
  for seed synthesis (temperature 0.6) and novelty assessment. Per ADR-2605215000
  / ADR-2606172359 (Murakumo DEFAULT-PREFERRED, loopback only) the inference edge
  here defaults to the Murakumo loopback gateway (LiteLLM 127.0.0.1:4000,
  no-server-key/read-only) and REFUSES any endpoint outside the fleet allowlist.

  Injectable: rebind `*chat*` in tests to a deterministic stub (no network)."
  (:require #?(:clj [cheshire.core :as json])
            [clojure.string :as str]))

;; Murakumo fleet (ADR-2605215000) — the ONLY inference endpoints representable.
(def murakumo-allowed-hosts
  #{"127.0.0.1:4000" "localhost:4000"
    "192.168.1.70:8077" "192.168.1.70:11434"
    "127.0.0.1:11434" "localhost:11434"})

(def default-config {:url "http://127.0.0.1:4000/v1"
                     :model "gemma3:4b"
                     :timeout-sec 120.0})

(defn- clip [s n] (let [s (str s)] (subs s 0 (min n (count s)))))

(defn assert-murakumo
  "Refuse any LLM endpoint outside the Murakumo fleet (http loopback only)."
  [endpoint]
  (let [[_ scheme host] (or (re-find #"^([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)" (str endpoint))
                            [nil nil nil])]
    (when-not (and (= "http" (some-> scheme str/lower-case))
                   (contains? murakumo-allowed-hosts (some-> host str/lower-case)))
      (throw (ex-info (str "inference endpoint " (pr-str endpoint)
                           " is outside the Murakumo fleet (ADR-2605215000)")
                      {:murakumo-only-violation true :endpoint endpoint})))))

(defn chat-with
  "Default `*chat*`: POST a chat-completions request to the Murakumo loopback
  gateway. Returns the assistant text string, or {:error ...}.

  `opts` keys: :temperature (default 0.6), :max-tokens (default 1024)."
  [http-post {:keys [url model timeout-sec]
              :or {url (:url default-config) model (:model default-config)
                   timeout-sec (:timeout-sec default-config)}} system user opts]
  (when-not (fn? http-post)
    (throw (ex-info "Open Patent inference requires an explicit HTTP POST capability"
                    {:capability :open-patent/murakumo-http-post})))
  (try
    (let [url (str/replace (str url) #"/+$" "")
          _ (assert-murakumo url)
          resp     (http-post (str url "/chat/completions")
                         {:headers {"Content-Type" "application/json"}
                          :timeout (long (* 1000 (double timeout-sec)))
                          :throw false
                          :body (json/generate-string {:model model
                                           :messages [{:role "system" :content system}
                                                      {:role "user" :content user}]
                                           :max_tokens (or (:max-tokens opts) 1024)
                                           :temperature (or (:temperature opts) 0.6)})})
          status   (:status resp)]
      (if (>= status 400)
        {:error (str "vllm " status ": " (clip (:body resp) 200))}
        (let [body (json/parse-string (:body resp) true)
              txt  (some-> (get-in body [:choices 0 :message :content]) str str/trim)]
          (if (seq txt) txt {:error "LLM returned empty completion"}))))
    (catch #?(:clj Exception :cljs :default) e
      {:error (clip #?(:clj (.getMessage e) :cljs (str e)) 200)})))

(def ^:dynamic *chat* nil)

(defn chat
  "Invoke the (injectable) LLM edge."
  ([system user] (chat system user {}))
  ([system user opts]
   (when-not (fn? *chat*)
     (throw (ex-info "Open Patent inference requires an explicit chat capability"
                     {:capability :open-patent/chat})))
   (*chat* system user opts)))
