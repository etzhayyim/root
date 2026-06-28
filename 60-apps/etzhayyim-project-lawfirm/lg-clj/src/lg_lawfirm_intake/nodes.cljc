(ns lg-lawfirm-intake.nodes
  "Intake triage + bengoshi matching nodes — faithful clj port of
  `lg/lg_lawfirm_intake/nodes.py` (ADR-2606280030).

  Flow: triage-node → summarize-node → search-node → match-node

    triage-node    — LLM classify domain / urgency / specialization (guarded;
                     falls back when no LLM key, exactly like the Python).
    summarize-node — encrypt summary with `signal:v1:` prefix (ADR-0018 Stage 1).
    search-node    — GET bengoshi.etzhayyim.com searchLawyers by jurisdiction +
                     specialization.
    match-node     — POST inviteExternalCounsel for the top-N matched lawyers.

  PORT NOTES / DEVIATIONS:
    * `urllib` → `babashka.http-client`; JSON → `cheshire`. The two HTTP edges
      (`*http-get*` / `*http-post*`) and the triage LLM edge (`*call-triage-llm*`)
      are INJECTABLE dynamic vars (the actor swap pattern) so the graph verifies
      offline under bb — mirroring the Python tests' monkeypatch of `_http_get` /
      `_http_post`.
    * The Python triage LLM points at a RunPod gemma URL. Per ADR-2605215000
      (Murakumo DEFAULT-PREFERRED, no-server-key/read-only loopback) the default
      LLM edge here targets the Murakumo loopback gateway (127.0.0.1:4000) and is
      key-gated identically — absent a key it returns nil and the deterministic
      fallback triage is used.
    * langgraph-clj is synchronous: the Python `async def` nodes become plain
      fns (no RetryPolicy / no asyncio). Node return = partial state map, merged
      by the StateGraph runtime (same contract as the Python dict updates)."
  (:require [clojure.string :as str]
            [cheshire.core :as json]))

;; ---------------------------------------------------------------------------
;; Config (env, with the Python defaults)
;; ---------------------------------------------------------------------------

(defn- env [k default] (or (System/getenv k) default))

;; Default LLM edge → Murakumo loopback gateway (ADR-2605215000), key-gated.
(def llm-url     (env "etzhayyim_LLM_URL" "http://127.0.0.1:4000/v1/chat/completions"))
(defn- llm-key [] (env "etzhayyim_LLM_API_KEY" ""))
(def llm-model   (env "LAWFIRM_LLM_MODEL" (env "etzhayyim_LLM_MODEL" "gemma-4-E4B-it")))
(def llm-timeout-sec (Double/parseDouble (env "LAWFIRM_LLM_TIMEOUT_SEC" "20")))

(def bengoshi-url   (env "BENGOSHI_URL"   "https://bengoshi.etzhayyim.com"))
(def dispatcher-url (env "DISPATCHER_URL" "https://dispatcher.etzhayyim.com"))
(defn- internal-secret [] (env "DISPATCHER_INTERNAL_SECRET" ""))

(def invite-limit        (Long/parseLong (env "LAWFIRM_INVITE_LIMIT" "3")))
(def invite-expires-days (Long/parseLong (env "LAWFIRM_INVITE_EXPIRES_DAYS" "90")))

(def known-domains
  #{"ni138" "land" "family" "consumer" "labour" "corporate"
    "tax" "criminal" "rera" "fema" "pil-rti" "visa"})

;; ---------------------------------------------------------------------------
;; HTTP edges (injectable — defaults lazily resolve babashka.http-client)
;; ---------------------------------------------------------------------------

(defn default-http-get
  "Default `*http-get*`: GET url with query params, parse JSON body → map."
  [url params]
  (let [get* (requiring-resolve 'babashka.http-client/get)
        resp (get* url {:query-params (or params {})
                        :timeout 10000})]
    (json/parse-string (:body resp) true)))

(defn default-http-post
  "Default `*http-post*`: POST JSON body with optional extra headers → parsed map."
  [url body {:keys [headers timeout]}]
  (let [post* (requiring-resolve 'babashka.http-client/post)
        resp  (post* url {:headers (merge {"Content-Type" "application/json"}
                                          (or headers {}))
                          :body (json/generate-string body)
                          :timeout (long (* 1000 (or timeout 15)))})]
    (json/parse-string (:body resp) true)))

(def ^:dynamic *http-get*  default-http-get)
(def ^:dynamic *http-post* default-http-post)

(defn- internal-headers []
  (let [s (internal-secret)]
    (if (seq s) {"x-internal-trust" s} {})))

;; ---------------------------------------------------------------------------
;; Triage LLM edge (injectable; guarded — nil when no key or call fails)
;; ---------------------------------------------------------------------------

(def triage-system
  (str "You are a legal intake triage assistant for lawfirm.etzhayyim.com.\n"
       "Given a client complaint in any language, classify it and return JSON:\n"
       "{\"domain\": \"<one of: ni138|land|family|consumer|labour|corporate|tax|criminal|rera|fema|pil-rti|visa|other>\",\n"
       " \"urgency\": \"<routine|urgent|ex-parte>\",\n"
       " \"specializations\": [\"<csv tokens from: labor,contract,family,ip,criminal,tax,land,corporate,consumer,immigration,other>\"],\n"
       " \"jurisdiction\": \"<ISO 3166-1 alpha-3 or ISO 3166-2, infer from state/lang/context>\",\n"
       " \"summary_en\": \"<1-2 sentence English summary, no PII>\"}\n"
       "Reply ONLY with the JSON object. Default urgency=routine when unclear."))

(defn- clip [s n] (let [s (str s)] (subs s 0 (min n (count s)))))

(defn default-call-triage-llm
  "Default `*call-triage-llm*`: POST a chat-completions request to the Murakumo
  loopback gateway. Returns the parsed JSON map, or nil when no key / on failure
  (parity with Python `_call_triage_llm`)."
  [summary lang domain-hint]
  (when (seq (llm-key))
    (let [prompt (str "Client language: " lang "\n"
                      "Domain hint: " (if (seq domain-hint) domain-hint "unknown") "\n"
                      "Complaint: " (clip summary 800) "\n\nReturn ONLY the JSON object.")]
      (try
        (let [post* (requiring-resolve 'babashka.http-client/post)
              resp  (post* llm-url
                           {:headers {"Authorization" (str "Bearer " (llm-key))
                                      "Content-Type" "application/json"}
                            :timeout (long (* 1000 llm-timeout-sec))
                            :body (json/generate-string
                                    {:model llm-model
                                     :messages [{:role "system" :content triage-system}
                                                {:role "user" :content prompt}]
                                     :temperature 0.1
                                     :max_tokens 256
                                     :response_format {:type "json_object"}})})
              body    (json/parse-string (:body resp) true)
              content (or (get-in body [:choices 0 :message :content]) "")
              parsed  (json/parse-string content true)]
          (when (map? parsed) parsed))
        (catch Exception e
          (binding [*out* *err*]
            (println "[triage-node] llm call failed:" (.getMessage e)))
          nil)))))

(def ^:dynamic *call-triage-llm* default-call-triage-llm)

(defn fallback-triage
  "Deterministic triage when the LLM edge is unavailable (parity with
  `_fallback_triage`)."
  [domain-hint]
  {:domain (if (contains? known-domains domain-hint) domain-hint "other")
   :urgency "routine"
   :specializations ["contract"]
   :jurisdiction "IND"
   :summary_en "(triage unavailable — LLM key not configured)"})

;; ---------------------------------------------------------------------------
;; signal:v1: encryption (ADR-0018 Stage 1 — base64 envelope)
;; ---------------------------------------------------------------------------

(defn signal-v1-encrypt [plaintext]
  (let [encoded (.encodeToString (java.util.Base64/getEncoder)
                                 (.getBytes (str plaintext) "UTF-8"))]
    (str "signal:v1:" encoded)))

;; ---------------------------------------------------------------------------
;; Nodes
;; ---------------------------------------------------------------------------

(defn triage-node
  "Classify intake by domain, urgency, and specialization using the LLM edge."
  [state]
  (let [summary     (or (:summary_plain state) "")
        lang        (or (:lang state) "en")
        domain-hint (or (:domain state) "")
        result      (or (*call-triage-llm* summary lang domain-hint)
                        (fallback-triage domain-hint))]
    (cond-> {:triage_result result}
      (and (not (seq (:domain state)))       (:domain result))       (assoc :domain (:domain result))
      (and (not (seq (:urgency state)))      (:urgency result))      (assoc :urgency (:urgency result))
      (and (not (seq (:jurisdiction state))) (:jurisdiction result)) (assoc :jurisdiction (:jurisdiction result)))))

(defn summarize-node
  "Encrypt the plaintext summary with the signal:v1: prefix (ADR-0018 Stage 1)."
  [state]
  (let [plain (or (:summary_plain state) "")]
    (if-not (seq plain)
      {}
      (let [triage     (or (:triage_result state) {})
            summary-en (or (:summary_en triage) (clip plain 200))]
        {:summary_cipher (signal-v1-encrypt summary-en)}))))

(defn search-node
  "Search bengoshi.etzhayyim.com for verified lawyers matching jurisdiction +
  specialization."
  [state]
  (let [jurisdiction    (or (:jurisdiction state) "IND")
        triage          (or (:triage_result state) {})
        specializations (or (:specializations triage) [])
        specialization  (first specializations)
        params          (cond-> {"jurisdiction" jurisdiction
                                 "limit" "10"
                                 "offset" "0"}
                          (seq specialization) (assoc "specialization" specialization))]
    (try
      (let [resp    (*http-get* (str bengoshi-url "/xrpc/com.etzhayyim.apps.bengoshi.searchLawyers")
                                params)
            lawyers (or (:lawyers resp) [])]
        {:lawyers (vec (take invite-limit lawyers))})
      (catch Exception e
        (binding [*out* *err*]
          (println "[search-node] bengoshi search failed:" (.getMessage e)))
        {:lawyers []}))))

(defn- expires-at []
  (let [inst (.plus (java.time.Instant/now)
                    (java.time.Duration/ofDays invite-expires-days))]
    (-> (java.time.format.DateTimeFormatter/ofPattern "yyyy-MM-dd'T'HH:mm:ss'Z'")
        (.withZone (java.time.ZoneOffset/UTC))
        (.format inst))))

(defn match-node
  "Send inviteExternalCounsel for the top matched lawyers."
  [state]
  (let [lawyers  (or (:lawyers state) [])
        case-did (or (:case_did state) "")]
    (if (or (empty? lawyers) (not (seq case-did)))
      (do (binding [*out* *err*]
            (println (str "[match-node] skip — no lawyers (" (count lawyers) ") or no case_did")))
          {:grants []})
      (let [exp    (expires-at)
            grants (reduce
                     (fn [acc lawyer]
                       (let [grantee-did (or (:did lawyer) "")]
                         (if-not (seq grantee-did)
                           acc
                           (try
                             (let [resp (*http-post*
                                          (str dispatcher-url "/xrpc/com.etzhayyim.apps.lawfirm.inviteExternalCounsel")
                                          {:matterDid case-did
                                           :granteeDid grantee-did
                                           :granteeHandle (or (:fullName lawyer) "")
                                           :role "advisory"
                                           :capabilities ["read" "comment" "propose"]
                                           :expiresAt exp
                                           :message "Intake case requires legal consultation. Please review."}
                                          {:headers (internal-headers)})]
                               (conj acc {:granteeDid grantee-did
                                          :grantDid (:grantDid resp)
                                          :grantUri (:grantUri resp)
                                          :conflictCheckPassed (get resp :conflictCheckPassed true)}))
                             (catch Exception e
                               (binding [*out* *err*]
                                 (println (str "[match-node] invite failed for " grantee-did ": " (.getMessage e))))
                               acc)))))
                     []
                     (take invite-limit lawyers))]
        {:grants grants}))))
