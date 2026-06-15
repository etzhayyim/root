;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/ake/methods/triage.py (unit_refactor stage 0)
;; triage.py — 朱 (ake) edit triage: risk + quality scoring and routing. ADR-2606052100.
(ns root.ake.methods.triage
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare target-kinds kw verifiable-provenance rider-hit assess-quality edit-op assess-risk route-for score-edit)

(def TARGET_KINDS ["kg-fact" "actor-profile"])

(def RISKS ["low" "medium" "high" "invariant"])

(def ROUTES ["auto-accept" "vote" "council-lv7" "refused"])

(def INVARIANT_ATTRS (set ["license" "charter" "force-class" "forceclass" "server-held-key" "serverheldkey"
                            "verification-method" "verificationmethod" "vm" "gates" "is-mirror" "ismirror"]))

(def SENSITIVE_ATTRS (set ["status" "did" "handle" "owner" "operator" "controller" "adr" "primary-lexicon"]))

(def RIDER_FORBIDDEN ["advertis" "affiliate" "adsense" "meta pixel" "ga4"
                       "weapon" "munition" "fire-control" "directed-energy"
                       "surveillance" "biometric" "pattern-of-life"
                       "addictive" "dark-pattern" "engagement-maxim"
                       "広告" "アフィリエイト" "兵器"])

(def QUALITY_AUTO_ACCEPT 0.7)

(defn kw [v]
  (let [s (clojure.string/replace (str (or v "")) ":" "")
        parts (clojure.string/split s "/")]
    (clojure.string/lower-case (last parts))))

;; TODO: port-failed unit _verifiable_provenance (bb-compile error)
;; def _verifiable_provenance(p: str) -> bool:
;;     p = (p or "").strip().lower()
;;     return p.startswith(("http://", "https://", "ipfs://", "cid:", "bafy")) or "://" in p
(defn verifiable-provenance [& _]
  (throw (ex-info "TODO: port-failed" {:from "_verifiable_provenance"})))

(defn rider-hit [*texts]
  "Return the first Charter-Rider §2 forbidden token found, or '' if clean."
  (let [blob (clojure.string/lower-case 
               (clojure.string/join " " (map #(or % "") *texts)))]
    (first (filter (fn [tok] (clojure.string/includes? blob tok)) RIDER_FORBIDDEN))))

;; TODO: port-failed unit assess_quality (dan: timed out)
;; def assess_quality(edit: dict, rider: str) -> float:
;;     """0..1 sourcing + plausibility + Rider-clean score (the ORES analogue)."""
;;     if rider:
;;         return 0.0   # a Charter-Rider violation is unpromotable, full stop
;;     q = 0.0
;;     if _verifiable_provenance(edit.get(":edit/provenance", "")):
;;         q += 0.5
;;     elif edit.get(":edit/provenance"):
;;         q += 0.15    # present but not obviously verifiable
;;     rationale = str(edit.get(":edit/rationale", ""))
;;     if len(rationale.strip()) >= 10:
;;         q += 0.2
;;     # plausibility: a non-empty proposed value for an :assert, sane length
;;     val = str(edit.get(":edit/proposed-value", ""))
;;     if edit_op(edit) in ("assert", "promote-sourcing") and 0 < len(val) <= 4000:
;;         q += 0.3
;;     elif edit_op(edit) in ("retract", "challenge"):
;;         q += 0.3     # retraction/challenge needs no value
;;     return round(min(q, 1.0), 4)
(defn assess-quality [& _]
  (throw (ex-info "TODO: port-failed" {:from "assess_quality"})))

;; TODO: port-failed unit edit_op (assembled-lint error)
;; def edit_op(edit: dict) -> str:
;;     return _kw(edit.get(":edit/op", "assert"))
(defn edit-op [& _]
  (throw (ex-info "TODO: port-failed" {:from "edit_op"})))

;; TODO: port-failed unit assess_risk (assembled-lint error)
;; def assess_risk(edit: dict, rider: str) -> str:
;;     attr = _kw(edit.get(":edit/target-attr", ""))
;;     if rider:
;;         return "invariant"            # a Rider hit is treated as the highest risk class
;;     if attr in INVARIANT_ATTRS:
;;         return "invariant"
;;     if edit_op(edit) == "challenge" or attr in SENSITIVE_ATTRS:
;;         return "high"
;;     if _kw(edit.get(":edit/target-kind", "")) == "actor-profile":
;;         return "medium"               # subjective prose → community eyes
;;     return "low"                      # a sourced KG fact
(defn assess-risk [& _]
  (throw (ex-info "TODO: port-failed" {:from "assess_risk"})))

(defn route-for [risk quality rider]
  "G2 INVARIANT — route is a PURE FUNCTION of (risk, quality, rider). No model decides this."
  (if rider
    "refused"              ;; Charter-Rider §2 hit: no vote can promote it
    (cond
      (= risk "invariant") "council-lv7"          ;; constitutional-adjacent → Council Lv7+ (G7)
      (and (= risk "low") (>= quality QUALITY_AUTO_ACCEPT)) "auto-accept"          ;; optimistic fast-path (the Wikipedia good-edit case)
      :else "vote")))                     ;; everything else → 1 SBT = 1 vote

;; TODO: port-failed unit score_edit (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpn1hy4vh1/scratch.clj:3:8: wa)
;; def score_edit(edit: dict, by: str = "murakumo:gemma3:4b") -> dict:
;;     """Validate (G1/G3/G4) then score + route a proposal. Raises ValueError on a hard gate.
;; 
;;     Returns a triage dict with risk + quality + route + by. It NEVER returns a decision (G2).
;;     """
;;     if "decision" in edit or ":triage/decision" in edit:
;;         raise ValueError("G2: triage scores risk+quality and routes; it never accepts/rejects (非裁定)")
;; 
;;     kind = _kw(edit.get(":edit/target-kind", ""))
;;     if kind not in TARGET_KINDS:
;;         raise ValueError(
;;             f"G3: target-kind {kind!r} not in {TARGET_KINDS} — entity-speech/impersonation unrepresentable"
;;         )
;;     if _kw(edit.get(":edit/author-kind", "")) != "member":
;;         raise ValueError("G1: author-kind must be 'member' (no-server-key + 信者-gated; server/anon refused)")
;;     if edit.get(":edit/server-held-key", False):
;;         raise ValueError("G1/no-server-key: server-held-key must be false (ADR-2605231525)")
;;     if not str(edit.get(":edit/provenance", "")).strip():
;;         raise ValueError("G4: an unsourced proposal is refused — provenance (URL/CID) is mandatory")
;; 
;;     rider = rider_hit(edit.get(":edit/proposed-value", ""), edit.get(":edit/rationale", ""))
;;     risk = assess_risk(edit, rider)
;;     quality = assess_quality(edit, rider)
;;     route = route_for(risk, quality, rider)
;;     return {
;;         ":triage/edit": edit.get(":edit/id", "?"),
;;         ":triage/risk": ":" + risk,
;;         ":triage/quality": quality,
;;         ":triage/route": ":" + route,
;;         ":triage/by": by,
;;         ":triage/rider-token": rider,   # diagnostic; "" when clean
;;     }
(defn score-edit [& _]
  (throw (ex-info "TODO: port-failed" {:from "score_edit"})))

