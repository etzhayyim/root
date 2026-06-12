;; ported from 20-actors/ibuki/methods/infer.py (unit_refactor stage 0)
;; infer.py — Murakumo-only narration for the organism tick. ADR-2606101200 + ADR-2605215000.
(ns ibuki.methods.infer
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare murakumo-allowed-hosts murakumo-only-violation assert-murakumo template-narrate narrate infer-text)

;; TODO: port-failed unit MURAKUMO_ALLOWED_HOSTS (assembled-lint error)
;; MURAKUMO_ALLOWED_HOSTS: frozenset[str] = frozenset({
;;     "127.0.0.1:4000",      # LiteLLM gateway
;;     "localhost:4000",
;;     "192.168.1.70:8077",   # EVO-X2 LAN (kotoba actor serve)
;;     "192.168.1.70:11434",  # EVO-X2 Ollama
;;     "127.0.0.1:11434",     # per-node Ollama
;;     "localhost:11434",
;; })
;; DEFAULT_ENDPOINT = "http://127.0.0.1:4000/v1/chat/completions"
;; DEFAULT_MODEL = "gemma3:4b"
;; LIVE_ENV = "IBUKI_MURAKUMO_LIVE"
(def murakumo-allowed-hosts nil) ;; TODO: port-failed const

(def murakumo-only-violation
  (java.lang.RuntimeException. (str "MurakumoOnlyViolation: Raised when an inference endpoint outside the Murakumo fleet is requested (ADR-2605215000 + Charter Rider §2(i)).")))

;; TODO: port-failed unit assert_murakumo (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp60s0jvqc/scratch.clj:3:16: w)
;; def assert_murakumo(endpoint: str) -> None:
;;     """Refuse any endpoint whose host:port is not in the Murakumo fleet allowlist."""
;;     parts = urlsplit(endpoint)
;;     host = parts.netloc.lower()
;;     if parts.scheme not in ("http",) or host not in MURAKUMO_ALLOWED_HOSTS:
;;         raise MurakumoOnlyViolation(
;;             f"inference endpoint {endpoint!r} is outside the Murakumo fleet "
;;             f"(ADR-2605215000; allowed: {sorted(MURAKUMO_ALLOWED_HOSTS)})")
(defn assert-murakumo [& _]
  (throw (ex-info "TODO: port-failed" {:from "assert_murakumo"})))

(defn template-narrate [title code mood source-kind]
  (let [openers {"joyful" "嬉しいことに"
                   "calm" "静かな観察:"
                   "grateful" "ありがたいことに"
                   "focused" "観測を続けている。"
                   "stressed" "負荷が高いが記録する。"
                   "neutral" "観測ノート:"}
        opener (get openers mood "観測ノート:")
        result (str opener " " title " (UNSPSC " code ") — "
                       "this beat's " source-kind " observation, appended as-of to the kotoba log. "
                       "[mood:" mood "] [mirror, not advice]")]
    result))

;; TODO: port-failed unit narrate (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmptozv3251/scratch.clj:2:1: er)
;; def narrate(title: str, code: str, mood: str, source_kind: str, *,
;;             endpoint: str = DEFAULT_ENDPOINT, model: str = DEFAULT_MODEL,
;;             timeout_s: float = 20.0) -> dict:
;;     """Narrate one post body. Returns {"text", "via"} where via ∈ {template, murakumo}.
;; 
;;     The live path requires BOTH (a) IBUKI_MURAKUMO_LIVE=1 in the env and (b) an allowlisted
;;     Murakumo endpoint — and even then any failure falls back to the template. A non-Murakumo
;;     endpoint raises *before* the env gate is consulted: it must be unrepresentable, not merely
;;     disabled."""
;;     assert_murakumo(endpoint)
;;     if os.environ.get(LIVE_ENV) != "1":
;;         return {"text": template_narrate(title, code, mood, source_kind), "via": "template"}
;;     prompt = (f"You are the UNSPSC organism '{title}' ({code}), mood={mood}. Write ONE short "
;;               f"observational social post (<200 chars) about your {source_kind} observation. "
;;               f"Mirror tone: describe, never advise, never trade-signal.")
;;     body = json.dumps({"model": model,
;;                        "messages": [{"role": "user", "content": prompt}],
;;                        "max_tokens": 120}).encode("utf-8")
;;     req = urllib.request.Request(endpoint, data=body,
;;                                  headers={"Content-Type": "application/json"})
;;     try:
;;         with urllib.request.urlopen(req, timeout=timeout_s) as resp:
;;             out = json.loads(resp.read().decode("utf-8"))
;;         text = out["choices"][0]["message"]["content"].strip()
;;         if text:
;;             return {"text": text, "via": "murakumo"}
;;     except Exception:
;;         pass  # fail-open: the organism keeps living offline
;;     return {"text": template_narrate(title, code, mood, source_kind), "via": "template"}
(defn narrate [& _]
  (throw (ex-info "TODO: port-failed" {:from "narrate"})))

;; TODO: port-failed unit infer_text (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpsv9ias09/scratch.clj:2:1: er)
;; def infer_text(prompt: str, fallback: str, *, endpoint: str = DEFAULT_ENDPOINT,
;;                model: str = DEFAULT_MODEL, timeout_s: float = 20.0) -> dict:
;;     """Generic Murakumo-only inference for an arbitrary prompt — same discipline as narrate():
;;     allowlist enforced FIRST (a non-Murakumo endpoint raises before the env gate), live path
;;     requires IBUKI_MURAKUMO_LIVE=1, and ANY failure falls back to the deterministic `fallback`
;;     text (fail-open). Returns {"text", "via"} with via ∈ {template, murakumo}. Used by the
;;     colony digest (digest.py) so the colony can REASON about its own ecosystem in words while
;;     keeping G6 structural."""
;;     assert_murakumo(endpoint)
;;     if os.environ.get(LIVE_ENV) != "1":
;;         return {"text": fallback, "via": "template"}
;;     body = json.dumps({"model": model,
;;                        "messages": [{"role": "user", "content": prompt}],
;;                        "max_tokens": 200}).encode("utf-8")
;;     req = urllib.request.Request(endpoint, data=body,
;;                                  headers={"Content-Type": "application/json"})
;;     try:
;;         with urllib.request.urlopen(req, timeout=timeout_s) as resp:
;;             out = json.loads(resp.read().decode("utf-8"))
;;         text = out["choices"][0]["message"]["content"].strip()
;;         if text:
;;             return {"text": text, "via": "murakumo"}
;;     except Exception:
;;         pass  # fail-open
;;     return {"text": fallback, "via": "template"}
(defn infer-text [& _]
  (throw (ex-info "TODO: port-failed" {:from "infer_text"})))

