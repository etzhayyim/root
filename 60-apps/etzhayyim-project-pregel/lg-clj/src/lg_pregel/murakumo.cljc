(ns lg-pregel.murakumo
  "Murakumo loopback LLM seam (ADR-2605215000) for the pregel triage actors.

  The external `kotodama` classifier talks to an LLM; per repo policy any LLM
  call MUST go through the Murakumo loopback gateway. This namespace validates
  the endpoint and accepts the HTTP implementation and configuration from an
  explicit host adapter."
  (:require #?(:clj [cheshire.core :as json])
            [clojure.string :as str]))

(def default-config {:url "http://127.0.0.1:4000/v1"
                     :model "gpt-4o-mini"})

(defn assert-murakumo
  "Throw unless `url` targets the Murakumo loopback gateway (127.0.0.1 / ::1 /
  localhost). Mirrors the off-fleet refusal guard used across the wave-1 twins."
  [url]
  (let [[_ scheme host] (or (re-find #"^([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)" (str url))
                            [nil nil nil])
        host (some-> host str/lower-case)]
    (when-not (and (= "http" (some-> scheme str/lower-case))
                   (contains? #{"127.0.0.1:4000" "localhost:4000" "[::1]:4000"} host))
      (throw (ex-info "off-fleet LLM endpoint refused (Murakumo loopback only)"
                      {:url url})))
    nil))

(defn chat-with
  "POST through an explicit HTTP capability. Returns assistant content."
  [http-post {:keys [url model] :or {url (:url default-config)
                                     model (:model default-config)}} system user]
  (when-not (fn? http-post)
    (throw (ex-info "Pregel inference requires an explicit HTTP POST capability"
                    {:capability :pregel/murakumo-http-post})))
  (let [url   (str/replace (str url) #"/+$" "")
        _     (assert-murakumo url)
        body  (json/generate-string {:model model
                    :messages [{:role "system" :content system}
                               {:role "user" :content user}]})
        resp  (http-post (str url "/chat/completions")
                    {:headers {"content-type" "application/json"}
                     :body body :throw false})
        data  (json/parse-string (:body resp) true)]
    (get-in data [:choices 0 :message :content])))

(def ^:dynamic *llm-chat* nil)

(defn chat [system user]
  (when-not (fn? *llm-chat*)
    (throw (ex-info "Pregel inference requires an explicit chat capability"
                    {:capability :pregel/chat})))
  (*llm-chat* system user))
