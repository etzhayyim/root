(ns lg-jukyu.llm
  "LLM edge for the jukyu clj port — clj analogue of the httpx LiteLLM calls in
  `extract_shocks.py` / `export_brief.py` / `run_stress_propagation.py`.

  DEVIATION (noted): the Python posts to `JUKYU_LLM_URL` (`llm.etzhayyim.com`
  LiteLLM gateway → murakumo-serve fleet). Per ADR-2605215000 / ADR-2606172359
  (Murakumo DEFAULT-PREFERRED) the default endpoint here is the Murakumo loopback
  gateway (LiteLLM 127.0.0.1:4000) and `assert-murakumo` refuses any off-fleet
  host (ibuki/recap pattern). The model ids (qwen3-30b extraction / gemma-4-e4b-it
  narrative) are preserved.

  `*chat*` is the single injectable edge (tests rebind to stubs)."
  (:require [clojure.string :as str]
            [lg-jukyu.util :as util]))

;; Murakumo fleet (ADR-2605215000) — the ONLY inference endpoints representable.
(def murakumo-allowed-hosts
  #{"127.0.0.1:4000" "localhost:4000"
    "192.168.1.70:8077" "192.168.1.70:11434"
    "127.0.0.1:11434" "localhost:11434"})

(def llm-url   (-> (or (System/getenv "JUKYU_LLM_URL") "http://127.0.0.1:4000")
                   (str/replace #"/+$" "")))
(def extraction-model (or (System/getenv "JUKYU_LLM_EXTRACTION_MODEL") "qwen3-30b"))
(def narrative-model  (or (System/getenv "JUKYU_LLM_NARRATIVE_MODEL")  "gemma-4-e4b-it"))
(def llm-timeout-sec  (Double/parseDouble (or (System/getenv "JUKYU_LLM_TIMEOUT") "30")))
(def llm-api-key      (or (System/getenv "JUKYU_LLM_API_KEY") ""))

(defn assert-murakumo
  "Refuse any LLM endpoint outside the Murakumo fleet (http only)."
  [endpoint]
  (when-let [[_ scheme host] (re-find #"^([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)" (str endpoint))]
    (when-not (and (= "http" (str/lower-case scheme))
                   (contains? murakumo-allowed-hosts (str/lower-case host)))
      (throw (ex-info (str "inference endpoint " (pr-str endpoint)
                           " is outside the Murakumo fleet (ADR-2605215000)")
                      {:murakumo-only-violation true :endpoint endpoint})))))

(defn default-chat
  "Default `*chat*`: POST a chat-completions request to the Murakumo loopback
  gateway. opts = {:model :system :user :messages :max-tokens :temperature}.
  Returns the assistant content string, or {:error ...}."
  [{:keys [model system user messages max-tokens temperature]}]
  (try
    (assert-murakumo llm-url)
    (let [post     (requiring-resolve 'babashka.http-client/post)
          generate (requiring-resolve 'cheshire.core/generate-string)
          parse    (requiring-resolve 'cheshire.core/parse-string)
          msgs     (or messages
                       [{:role "system" :content (or system "")}
                        {:role "user"   :content (or user "")}])
          headers  (cond-> {"Content-Type" "application/json"}
                     (seq llm-api-key) (assoc "Authorization" (str "Bearer " llm-api-key)))
          resp     (post (str llm-url "/v1/chat/completions")
                         {:headers headers
                          :timeout (long (* 1000 llm-timeout-sec))
                          :body (generate {:model (or model narrative-model)
                                           :messages msgs
                                           :max_tokens (or max-tokens 1024)
                                           :temperature (or temperature 0.3)})})
          status   (:status resp)]
      (if (>= status 400)
        {:error (str "llm " status ": " (util/clip (:body resp) 200))}
        (let [body (parse (:body resp) true)
              txt  (some-> (get-in body [:choices 0 :message :content]) str str/trim)]
          (if (seq txt) txt {:error "LLM returned empty content"}))))
    (catch Exception e {:error (util/clip (.getMessage e) 200)})))

(def ^:dynamic *chat* default-chat)
