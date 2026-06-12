;; ported from 70-tools/kotoba-e2e/kotoba_e2e/murakumo.py (unit_refactor stage 0)
;; Murakumo-only LLM factory + charter guard (ADR-2605215000).
(ns kotoba-e2e.kotoba-e2e.murakumo
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare default-base-url charter-inference-violation assert-murakumo-only resolve-api-key base-url model-name make-llm)

;; TODO: port-failed unit DEFAULT_BASE_URL (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp8km78p48/scratch.clj:5:29: e)
;; DEFAULT_BASE_URL = "http://127.0.0.1:4000/v1"
;; DEFAULT_MODEL = "gemma4"
;; _ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1", "0.0.0.0"}
;; _ALLOWED_HOST_SUFFIXES = (".murakumo.etzhayyim.com",)
;; _ALLOWED_PRIVATE_PREFIXES = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.")
;; _PROHIBITED_SUBSTRINGS = (
;;     "api.openai.com",
;;     "api.anthropic.com",
;;     "openai.azure.com",
;;     "generativelanguage.googleapis.com",
;;     "aiplatform.googleapis.com",
;;     "bedrock",
;;     "api.runpod",
;;     "api.together",
;;     "api.groq.com",
;;     "api.mistral.ai",
;; )
(def default-base-url nil) ;; TODO: port-failed const

;; TODO: port-failed unit CharterInferenceViolation (assembled-lint error)
;; class CharterInferenceViolation(RuntimeError):
;;     """Raised when an LLM endpoint is not the Murakumo fleet."""
(defn charter-inference-violation [& _]
  (throw (ex-info "TODO: port-failed" {:from "CharterInferenceViolation"})))

;; TODO: port-failed unit assert_murakumo_only (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp9icaft5k/scratch.clj:3:27: w)
;; def assert_murakumo_only(base_url: str) -> None:
;;     """Refuse any base_url that is not the loopback gateway / LAN fleet.
;; 
;;     This is the ADR-2605215000 enforcement point for the e2e harness.
;;     """
;;     low = (base_url or "").lower()
;;     for bad in _PROHIBITED_SUBSTRINGS:
;;         if bad in low:
;;             raise CharterInferenceViolation(
;;                 f"commercial inference endpoint '{bad}' is prohibited "
;;                 f"(ADR-2605215000 — Murakumo fleet only): {base_url}"
;;             )
;;     host = (urlparse(base_url).hostname or "").lower()
;;     if host in _ALLOWED_HOSTS:
;;         return
;;     if any(host.endswith(s) for s in _ALLOWED_HOST_SUFFIXES):
;;         return
;;     if any(host.startswith(p) for p in _ALLOWED_PRIVATE_PREFIXES):
;;         return
;;     raise CharterInferenceViolation(
;;         f"LLM base_url host '{host}' is not a Murakumo fleet node "
;;         f"(loopback / *.murakumo.etzhayyim.com / private LAN only): {base_url}"
;;     )
(defn assert-murakumo-only [& _]
  (throw (ex-info "TODO: port-failed" {:from "assert_murakumo_only"})))

(defn resolve-api-key []
  (let [env (get Env/os "KOTOBA_INFERENCE_API_KEY")
        murakumo-key (get Env/os "MURAKUMO_API_KEY")]
    (if env
      env
      (try
        (let [process (java.lang.Process/start ["security" "find-generic-password" "-s" "etzhayyim" "-a" "KOTOBA_INFERENCE_API_KEY" "-w"])
              out (process/waitFor process 10) ; Wait up to 10 seconds
              stdout (clojure.string/trim (java.io/read-line out))]
          (if (= (:exit process) 0) stdout
            "sk-murakumo-loopback"))
        (catch Exception _
          "sk-murakumo-loopback")))))

(defn base-url []
  (get (java.lang.System/getenv "MURAKUMO_BASE_URL") "http://localhost:8080/"))

(defn model-name []
  (let [default-model "murakumo"] ; Assuming DEFAULT_MODEL is defined or hardcoded if not provided in context
    (get (System/getenv "MURAKUMO_MODEL") default-model)))

;; TODO: port-failed unit make_llm (assembled-lint error)
;; def make_llm(*, model: str | None = None, temperature: float = 0.0):
;;     """Construct the browser-use / langchain chat model bound to Murakumo.
;; 
;;     Tries browser-use's own ChatOpenAI wrapper first (newer browser-use ships
;;     its own), then langchain_openai.ChatOpenAI — BOTH are OpenAI-compatible
;;     clients that we point at the Murakumo gateway (NOT at OpenAI). The guard runs
;;     before any client is built, so a misconfigured base_url can never reach a
;;     commercial host.
;;     """
;;     url = base_url()
;;     assert_murakumo_only(url)  # charter gate — runs before any network client exists
;;     key = resolve_api_key()
;;     mdl = model or model_name()
;; 
;;     # Prefer browser-use's native LLM (keeps version compatibility with Agent).
;;     try:
;;         from browser_use.llm import ChatOpenAI as BuChatOpenAI  # type: ignore
;; 
;;         return BuChatOpenAI(model=mdl, base_url=url, api_key=key, temperature=temperature)
;;     except Exception:
;;         pass
;;     from langchain_openai import ChatOpenAI  # type: ignore
;; 
;;     return ChatOpenAI(model=mdl, base_url=url, api_key=key, temperature=temperature)
(defn make-llm [& _]
  (throw (ex-info "TODO: port-failed" {:from "make_llm"})))

