;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/himotoki/methods/request.py (unit_refactor stage 0)
;; himotoki 繙き — DSAR/FOIA disclosure-request draft generator (R0/R1, offline).
(ns root.himotoki.methods.request
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare here load-registry is-dsar is-verified build-request can-dispatch build-batch render-edn main)

;; TODO: port-failed unit _HERE (bb-compile error)
;; _HERE = pathlib.Path(__file__).resolve().parent.parent
;; _REGISTRY = _HERE / "registry" / "targets.seed.json"
;; MAX_BATCH = 5                       # G8 — no mass-filing / agency flooding
;; DSAR_REGIME_PREFIXES = ("gdpr", "ccpa", "cpra", "appi", "lgpd", "pipeda", "pdpa", "pipl")
;; _FORBIDDEN_PRETEXT_FIELDS = ("pretext", "sockpuppet", "impersonat", "alias", "false-identity")
(def here nil) ;; TODO: port-failed const

(defn load-registry [path _REGISTRY=]
  "Return {targetId: target}. targetId = '<organization>:<regime>' (stable, human)."
  (let [content (slurp path)
        d (clojure.edn/read-string content)]
    (into {}
           (for [t (:targets d)]
             [(str (get t "organization") ":" (get t "regime")) t]))))

;; TODO: port-failed unit is_dsar (bb-compile error)
;; def is_dsar(target: dict) -> bool:
;;     """DSAR (own-data) vs FOIA (public records), inferred from the regime."""
;;     regime = str(target.get("regime", "")).lower()
;;     if regime.startswith(DSAR_REGIME_PREFIXES):
;;         return True
;;     if "foia" in regime or "情報公開" in regime or regime.endswith("-foia"):
;;         return False
;;     # altRegimes fallback
;;     return any(str(r).lower().startswith(DSAR_REGIME_PREFIXES)
;;                for r in target.get("altRegimes", []))
(defn is-dsar [& _]
  (throw (ex-info "TODO: port-failed" {:from "is_dsar"})))

;; TODO: port-failed unit is_verified (assembled-lint error)
;; def is_verified(target: dict) -> bool:
;;     return str(target.get("verificationStatus", "")) == "verified"
(defn is-verified [& _]
  (throw (ex-info "TODO: port-failed" {:from "is_verified"})))

;; TODO: port-failed unit build_request (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpe6qijis4/scratch.clj:4:15: w)
;; def build_request(target: dict, member: dict) -> dict:
;;     """Build a disclosure-request draft. RAISES on a charter violation (G3/G4/G6)."""
;;     requester = member.get("requesterDid") or ""
;;     if not requester:
;;         raise ValueError("G4: every request must identify the true requester DID (no pretext)")
;;     # G4 — no pretext/sockpuppet field may be supplied.
;;     for k in member:
;;         if any(b in k.lower() for b in _FORBIDDEN_PRETEXT_FIELDS):
;;             raise ValueError(f"G4: pretext field {k!r} is unrepresentable; the true requester must file")
;;     dsar = is_dsar(target)
;;     if dsar and not member.get("ownDataOnly") is True:
;;         raise ValueError("G3: a DSAR is own-data-only; member must assert ownDataOnly=true")
;;     # G6 — the member's PII must be an encrypted envelope ref, never plaintext in the draft.
;;     env = member.get("subjectEnvelopeRef") or ""
;;     if not env.startswith("com.etzhayyim.encrypted:"):
;;         raise ValueError("G6: member identity must be a com.etzhayyim.encrypted:* envelope ref, "
;;                          "never plaintext PII in the draft")
;;     for forbidden in ("name", "email", "address", "phone"):
;;         if forbidden in member and member[forbidden]:
;;             raise ValueError(f"G6: plaintext PII {forbidden!r} must not be in the request; use the envelope")
;; 
;;     return {
;;         "type": "himotoki.disclosureRequest",
;;         "kind": "DSAR" if dsar else "FOIA",
;;         "regime": target.get("regime"),
;;         "organization": target.get("organization"),
;;         "jurisdiction": target.get("jurisdiction"),
;;         "channelType": target.get("channelType"),
;;         "requesterDid": requester,                       # G4 — true requester
;;         "subjectEnvelopeRef": env,                       # G6 — encrypted, never plaintext
;;         "ownDataOnly": bool(dsar),                       # G3
;;         "statutoryDeadlineDays": target.get("statutoryDeadlineDays"),
;;         "targetVerified": is_verified(target),           # G14 input
;;         "dispatchReady": False,                          # never ready at R0 (G10/G14)
;;         "sourcing": ":representative",
;;     }
(defn build-request [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_request"})))

(defn can-dispatch [target operator-gate]
  "G14 + G10: a draft may be transmitted ONLY against a verified target AND with the
  operator gate. Returns (allowed, reason-if-refused)."
  (if (not (is-verified target))
    [false "G14: target is unverified-seed / stale; verify (and re-check within the freshness window) before any dispatch"]
    (if (not operator-gate)
      [false "G10: live dispatch needs HIMOTOKI_OPERATOR_GATE=1 (Council + operator)"]
      [true ""])))

;; TODO: port-failed unit build_batch (bb-compile error)
;; def build_batch(target_ids: list[str], member: dict, registry: dict[str, dict]) -> list[dict]:
;;     """Build drafts for several targets. RAISES (G8) if more than MAX_BATCH — no mass-filing."""
;;     if len(target_ids) > MAX_BATCH:
;;         raise ValueError(f"G8: no mass-filing — at most {MAX_BATCH} targets per batch, got {len(target_ids)}")
;;     return [build_request(registry[t], member) for t in target_ids]
(defn build-batch [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_batch"})))

;; TODO: port-failed unit render_edn (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmppz0fy1_w/scratch.clj:10:38: )
;; def render_edn(drafts: list[dict]) -> str:
;;     L = [";; himotoki-request-drafts.kotoba.edn — disclosure-request DRAFTS (never dispatched).",
;;          ";; G3 own-data-only DSAR · G4 true-requester (no pretext) · G6 PII = encrypted",
;;          ";; envelope ref (never plaintext) · G14 dispatch refused vs unverified target ·",
;;          ";; G10 outbound-gated. DERIVED :representative. ADR-2605302130.", "", "["]
;;     for d in drafts:
;;         L.append(
;;             f' {{:himotoki.req/kind :{d["kind"]} :himotoki.req/regime "{d["regime"]}" '
;;             f':himotoki.req/organization "{d["organization"]}" '
;;             f':himotoki.req/requester-did "{d["requesterDid"]}" '
;;             f':himotoki.req/subject-envelope-ref "{d["subjectEnvelopeRef"]}" '
;;             f':himotoki.req/own-data-only {str(d["ownDataOnly"]).lower()} '
;;             f':himotoki.req/target-verified {str(d["targetVerified"]).lower()} '
;;             f':himotoki.req/dispatch-ready false :himotoki.req/sourcing :representative}}')
;;     L.append("]")
;;     return "\n".join(L) + "\n"
(defn render-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "render_edn"})))

;; TODO: port-failed unit main (assembled-lint error)
;; def main(argv: list[str]) -> int:
;;     if "--target" not in argv or "--member" not in argv:
;;         sys.exit(__doc__)
;;     registry = load_registry()
;;     tid = argv[argv.index("--target") + 1]
;;     if tid not in registry:
;;         sys.exit(f"unknown target {tid!r}; e.g. one of: " + ", ".join(list(registry)[:3]))
;;     member = {
;;         "requesterDid": argv[argv.index("--member") + 1],
;;         "ownDataOnly": True,
;;         "subjectEnvelopeRef": "com.etzhayyim.encrypted:env:demo-subject",
;;     }
;;     target = registry[tid]
;;     draft = build_request(target, member)
;;     allowed, reason = can_dispatch(target, os.environ.get("HIMOTOKI_OPERATOR_GATE") == "1")
;;     if "--out" in argv:
;;         outdir = pathlib.Path(argv[argv.index("--out") + 1])
;;         outdir.mkdir(parents=True, exist_ok=True)
;;         (outdir / "himotoki-request-drafts.kotoba.edn").write_text(render_edn([draft]))
;;     print(f"himotoki draft: {draft['kind']} to {draft['organization']} ({draft['regime']}, "
;;           f"{draft['jurisdiction']}); deadline {draft['statutoryDeadlineDays']}d")
;;     print(f"  dispatch: {'ALLOWED' if allowed else 'REFUSED — ' + reason}")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

