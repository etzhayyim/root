;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/fuchi/methods/provision.py (unit_refactor stage 0)
;; provision.py — 扶持 (fuchi) R1(a): wire in-kind rails to the real producing actors.
(ns root.fuchi.methods.provision
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare provider-registry provisioning-intent provision dispatched-provision dispatch-live)

(def provider-registry
  {"housing-commons" ["commons-land" "commons" "LANDS.md commons"]
   "food-mitsuho"    ["did:web:etzhayyim.com:actor:mitsuho" "actor" "mitsuho 瑞穂"]
   "energy-hikari"   ["did:web:etzhayyim.com:actor:hikari" "actor" "hikari 光"]
   "compute-murakumo" ["murakumo" "infra" "Murakumo mesh"]
   "tooling-okaimono" ["did:web:etzhayyim.com:actor:okaimono" "actor" "okaimono 御買物"]
   "care-iyashi"      ["did:web:etzhayyim.com:actor:iyashi" "actor" "iyashi 癒"]
   "liquidity-warifu" ["did:web:etzhayyim.com:actor:warifu" "actor" "warifu 割符 (0% qard-ḥasan)"]})

;; TODO: port-failed unit ProvisioningIntent (assembled-lint error)
;; class ProvisioningIntent:
;;     alloc_id: str
;;     rail_kind: str
;;     provider_did: str
;;     provider_kind: str            # actor | commons | infra
;;     imputed_usd_micros_yr: int
;;     member_principal: bool = False
;;     cash_usd_micros: int = 0      # G2 — structural
;;     server_held_key: bool = False  # G9 — structural
;;     published: bool = False        # G10 — structural at R0/R1
;; 
;;     def __post_init__(self) -> None:
;;         if self.cash_usd_micros != 0:
;;             raise ValueError("cash≡0 INVARIANT (G2): a provisioning intent never moves cash")
;;         if self.server_held_key:
;;             raise ValueError("no-server-key INVARIANT (G9): the intent is member/Council-signed")
;;         if self.published:
;;             raise ValueError("G10: published must be false — live provisioning is Council Lv6+ + operator gated")
;;         if self.rail_kind not in PROVIDER_REGISTRY:
;;             raise ValueError(f"G3: rail kind {self.rail_kind!r} has no provider")
(defn provisioning-intent [& _]
  (throw (ex-info "TODO: port-failed" {:from "ProvisioningIntent"})))

;; TODO: port-failed unit provision (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp788k2d36/scratch.clj:7:70: w)
;; def provision(rails: list, alloc_id: str) -> list[ProvisioningIntent]:
;;     """Map routing rails → provisioning intents addressed to real producing actors.
;; 
;;     `rails` are route.Rail instances (or dicts with .kind/.imputed_usd_micros_yr/.member_principal).
;;     """
;;     import json
;;     from pathlib import Path
;; 
;;     abaki_policy_path = Path(__file__).resolve().parents[3] / "abaki" / "out" / "routing-policy.json"
;;     blocked_ids = set()
;;     if abaki_policy_path.exists():
;;         try:
;;             with open(abaki_policy_path, "r", encoding="utf-8") as f:
;;                 policy = json.load(f)
;;             blocked_ids = {e["id"] for e in policy.get("blocked_entities", [])}
;;         except Exception:
;;             pass
;; 
;;     out: list[ProvisioningIntent] = []
;;     for r in rails:
;;         kind = getattr(r, "kind", None) or r.get("kind")
;;         imputed = getattr(r, "imputed_usd_micros_yr", None)
;;         if imputed is None:
;;             imputed = r.get("imputedUsdMicrosYr", r.get("imputed_usd_micros_yr", 0))
;;         member_principal = getattr(r, "member_principal", None)
;;         if member_principal is None:
;;             member_principal = bool(r.get("memberPrincipal", r.get("member_principal", False)))
;;         provider_did, provider_kind, _label = PROVIDER_REGISTRY[kind]
;; 
;;         for blocked_id in blocked_ids:
;;             if blocked_id in provider_did:
;;                 raise ValueError(f"Provider {provider_did} blocked by abaki Anti-Monopoly policy. React mechanism triggered: Route Around {blocked_id}.")
;; 
;;         out.append(ProvisioningIntent(
;;             alloc_id=alloc_id,
;;             rail_kind=kind,
;;             provider_did=provider_did,
;;             provider_kind=provider_kind,
;;             imputed_usd_micros_yr=int(imputed),
;;             member_principal=bool(member_principal),
;;         ))
;;     return out
(defn provision [& _]
  (throw (ex-info "TODO: port-failed" {:from "provision"})))

(defn dispatched-provision
  "Constructor for DispatchedProvision. Returns a map representing the object."
  [intent operator_did council_level member_signature authorized_to_publish]
  (let [authorized_to_publish (or authorized_to_publish true)]
    (if (not= 0 (:cash-usd-micros intent))
      (throw (ex-info "cash≡0 INVARIANT (G2) holds in live mode too" {:intent intent}))
      (if (:server-held-key intent)
        (throw (ex-info "no-server-key INVARIANT (G9) holds in live mode too" {:intent intent}))
        {:intent intent
         :operator-did operator_did
         :council-level council_level
         :member-signature member_signature
         :authorized-to-publish authorized_to_publish}))))

;; TODO: port-failed unit dispatch_live (assembled-lint error)
;; def dispatch_live(
;;     intents: list[ProvisioningIntent],
;;     gate: LiveGate,
;;     *,
;;     env: dict[str, str] | None = None,
;; ) -> list[DispatchedProvision]:
;;     """Authorize LIVE provisioning dispatch to the producing actors.
;; 
;;     RAISES `live_gate.LiveGateRefused` unless the operator flag + attestation + Council Lv6+ +
;;     member signature are all present (the default at R0/R1). When authorized, returns one dispatch
;;     receipt per intent. The member-principal liquidity intent stays member-principal (warifu 0%;
;;     扶持 still never holds, lends, or pays).
;;     """
;;     require(gate, env=env)  # refuses by default
;;     return [DispatchedProvision(
;;         intent=i,
;;         operator_did=gate.operator_did,
;;         council_level=gate.council_level,
;;         member_signature=gate.member_signature,
;;     ) for i in intents]
(defn dispatch-live [& _]
  (throw (ex-info "TODO: port-failed" {:from "dispatch_live"})))

