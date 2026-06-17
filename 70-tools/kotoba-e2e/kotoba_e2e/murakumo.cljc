;; ported from 70-tools/kotoba-e2e/kotoba_e2e/murakumo.py — real port replacing the
;; unit_refactor stage-0 "TODO: port-failed" stub. NS fixed (the doubled
;; "kotoba-e2e.kotoba-e2e.*" -> path-derived "kotoba-e2e.murakumo") and the file is now .cljc.
;; Self-contained; no dependency on any sibling namespace. Host/process/env I/O is behind
;; #?(:clj ...). The pure parts (assert-murakumo-only / base-url / model-name) are the
;; testable charter guard; make-llm is host-only and constructs no client on :cljs.
(ns kotoba-e2e.murakumo
  "murakumo.py — Murakumo-only LLM factory + charter guard (ADR-2605215000).

  The agentic e2e layer (browser-use + langgraph) drives a browser with an LLM.
  That LLM MUST be the Murakumo fleet (LiteLLM gateway on loopback 127.0.0.1:4000,
  or a LAN fleet node), NEVER a commercial endpoint. `assert-murakumo-only` refuses
  any non-fleet base URL by construction.

  Pure + import-light: the guard + key resolution are testable without langchain or
  browser-use installed (make-llm imports them lazily on the host)."
  (:require [clojure.string :as str]))

;; The charter inference SSoT: LiteLLM gateway on loopback (TCC-exempt per
;; ADR-2605302355) -> EVO-X2 LAN + per-node Ollama. OpenAI-compatible surface.
(def DEFAULT_BASE_URL "http://127.0.0.1:4000/v1")
(def DEFAULT_MODEL "gemma4")

;; Hosts that ARE the Murakumo fleet (loopback + the private LAN per ADR-2605215000).
;; Anything else is rejected.
(def ^:private allowed-hosts #{"127.0.0.1" "localhost" "::1" "0.0.0.0"})
(def ^:private allowed-host-suffixes [".murakumo.etzhayyim.com"])
(def ^:private allowed-private-prefixes
  ["192.168." "10." "172.16." "172.17." "172.18." "172.19."])

;; Commercial inference hosts that are constitutionally prohibited in any etzhayyim
;; inference path (ADR-2605215000). Listed for an explicit, legible refusal message;
;; the allowlist above is the actual gate.
(def ^:private prohibited-substrings
  ["api.openai.com"
   "api.anthropic.com"
   "openai.azure.com"
   "generativelanguage.googleapis.com"
   "aiplatform.googleapis.com"
   "bedrock"
   "api.runpod"
   "api.together"
   "api.groq.com"
   "api.mistral.ai"])

;; CharterInferenceViolation: raised when an LLM endpoint is not the Murakumo fleet.
;; Python had a RuntimeError subclass; we encode the type as ex-info data so callers
;; (and tests) can dispatch on (:charter-violation (ex-data e)).
(defn charter-inference-violation
  "Construct (do not throw) the charter-violation ex-info for `msg`."
  [msg]
  (ex-info msg {:charter-violation true :type "CharterInferenceViolation"}))

(defn- url-host
  "Lowercased hostname of `base-url`, or \"\" when absent — mirrors
  urllib.parse.urlparse(base_url).hostname for http(s)://host[:port]/... shapes."
  [base-url]
  (let [s (or base-url "")
        ;; strip scheme
        after-scheme (let [idx (str/index-of s "://")]
                       (if idx (subs s (+ idx 3)) s))
        ;; authority = up to the first '/', '?' or '#'
        authority (first (str/split after-scheme #"[/?#]" 2))
        ;; drop userinfo (user:pass@host)
        authority (if-let [at (str/last-index-of authority "@")]
                    (subs authority (inc at))
                    authority)]
    (str/lower-case
      (cond
        (str/blank? authority) ""
        ;; bracketed IPv6 literal: [::1]:4000 -> ::1
        (str/starts-with? authority "[")
        (let [close (str/index-of authority "]")]
          (if close (subs authority 1 close) authority))
        ;; host:port -> host (IPv4 / name)
        (str/includes? authority ":")
        (first (str/split authority #":" 2))
        :else authority))))

(defn assert-murakumo-only
  "Refuse any base-url that is not the loopback gateway / LAN fleet.
  This is the ADR-2605215000 enforcement point for the e2e harness.
  Returns nil on success; throws CharterInferenceViolation otherwise."
  [base-url]
  (let [low (str/lower-case (or base-url ""))]
    (doseq [bad prohibited-substrings]
      (when (str/includes? low bad)
        (throw (charter-inference-violation
                 (str "commercial inference endpoint '" bad "' is prohibited "
                      "(ADR-2605215000 — Murakumo fleet only): " base-url)))))
    (let [host (url-host base-url)]
      (cond
        (contains? allowed-hosts host) nil
        (some #(str/ends-with? host %) allowed-host-suffixes) nil
        (some #(str/starts-with? host %) allowed-private-prefixes) nil
        :else
        (throw (charter-inference-violation
                 (str "LLM base_url host '" host "' is not a Murakumo fleet node "
                      "(loopback / *.murakumo.etzhayyim.com / private LAN only): "
                      base-url)))))))

(defn- getenv
  "Read environment variable `k`, or nil. Host-only; :cljs returns nil."
  [k]
  #?(:clj (System/getenv k)
     :default nil))

(defn resolve-api-key
  "KOTOBA_INFERENCE_API_KEY from env, else the macOS Keychain mirror.

  The key authorizes the loopback LiteLLM gateway (bearer). Never a commercial
  vendor key (those would be refused by assert-murakumo-only anyway). Falls back to
  a placeholder so a misconfigured key surfaces as an auth error, not a silent
  commercial call."
  []
  (let [env (or (getenv "KOTOBA_INFERENCE_API_KEY") (getenv "MURAKUMO_API_KEY"))]
    (if (and env (not (str/blank? env)))
      env
      #?(:clj
         (try
           (let [pb (ProcessBuilder. ["security" "find-generic-password"
                                      "-s" "etzhayyim"
                                      "-a" "KOTOBA_INFERENCE_API_KEY" "-w"])
                 proc (.start pb)
                 out (slurp (.getInputStream proc))
                 code (.waitFor proc)]
             (if (and (zero? code) (not (str/blank? out)))
               (str/trim out)
               "sk-murakumo-loopback"))
           (catch Exception _ "sk-murakumo-loopback"))
         :default "sk-murakumo-loopback"))))

(defn base-url
  "MURAKUMO_BASE_URL from env, else DEFAULT_BASE_URL."
  []
  (or (getenv "MURAKUMO_BASE_URL") DEFAULT_BASE_URL))

(defn model-name
  "MURAKUMO_MODEL from env, else DEFAULT_MODEL."
  []
  (or (getenv "MURAKUMO_MODEL") DEFAULT_MODEL))

(defn make-llm
  "Construct the browser-use / langchain chat model bound to Murakumo.

  The charter guard runs BEFORE any client is built, so a misconfigured base-url can
  never reach a commercial host. Faithful to the Python: the actual ChatOpenAI client
  construction is a host concern (browser-use / langchain_openai are Python libs); on
  the JVM/cljs there is no such client to build, so after the guard + key/model
  resolution we return the resolved config map (the data the host client would be
  constructed from). Keyword opts: :model :temperature (default 0.0)."
  [& {:keys [model temperature] :or {temperature 0.0}}]
  (let [url (base-url)]
    (assert-murakumo-only url)            ; charter gate — before any network client
    (let [key (resolve-api-key)
          mdl (or model (model-name))]
      {"model" mdl "base_url" url "api_key" key "temperature" temperature})))

;; The Python "__main__" demo is omitted (no top-level side effects).
