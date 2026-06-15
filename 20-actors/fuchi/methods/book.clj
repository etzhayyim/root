;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/fuchi/methods/book.py (unit_refactor stage 0)
;; book.py — 扶持 (fuchi) R1(c): toritate booking + kanae-renderable flow viz.
(ns root.fuchi.methods.book
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare rail-to-category ledger-entry flow-edge rail-fields book-toritate flow-graph booking-receipt write-live)

(def RAIL_TO_CATEGORY
  {"housing-commons" "subsistence-flow"
   "food-mitsuho"    "subsistence-flow"
   "energy-hikari"   "subsistence-flow"
   "compute-murakumo" "vocation-flow"
   "tooling-okaimono" "vocation-flow"
   "care-iyashi"     "care-flow"})

(def TORITATE_CATEGORIES ["subsistence-flow" "vocation-flow" "care-flow" "liberation-flow" "grant"])

(def FORBIDDEN_CATEGORIES ["payroll" "salary" "wage" "bonus" "commission"])

(def PUBLIC_FUND "did:web:etzhayyim.com:actor:etzhayyim-public-fund")

(def FUCHI "did:web:etzhayyim.com:actor:fuchi")

;; TODO: port-failed unit LedgerEntry (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp5jfu88q0/scratch.clj:2:78: w)
;; class LedgerEntry:
;;     alloc_id: str
;;     category: str                 # toritate ledgerEntry category
;;     imputed_usd_micros_yr: int
;;     counterparty_did: str
;;     cash_usd_micros: int = 0      # toritate cashStipendUsd ≡ 0
;; 
;;     def __post_init__(self) -> None:
;;         if self.cash_usd_micros != 0:
;;             raise ValueError("cash≡0 INVARIANT (G2): toritate cashStipendUsd ≡ 0")
;;         if self.category in FORBIDDEN_CATEGORIES:
;;             raise ValueError(f"category {self.category!r} unrepresentable (no payroll/wage)")
;;         if self.category not in TORITATE_CATEGORIES:
;;             raise ValueError(f"category {self.category!r} not a toritate ledgerEntry category")
(defn ledger-entry [& _]
  (throw (ex-info "TODO: port-failed" {:from "LedgerEntry"})))

(defn flow-edge
  "A map representing a FlowEdge.
  Fields:
  - frm (str)
  - to (str)
  - flow-class (str): publicfund-to-fuchi | fuchi-to-provider | provider-to-maintainer
  - imputed-usd-micros-yr (int)
  - in-kind (bool, default: true)"
  [frm to flow-class imputed-usd-micros-yr {:keys [in-kind]}]
  (->> {:frm frm
        :to to
        :flow-class flow-class
        :imputed-usd-micros-yr imputed-usd-micros-yr
        :in-kind (or in-kind true)}))

(defn _rail-fields [r]
  (let [kind (or (get r :kind) (if (map? r) (get r "kind") nil))
        imputed (or (get r :imputed_usd_micros_yr)
                    (if (map? r) (or (get r "imputedUsdMicrosYr") (get r "imputed_usd_micros_yr")) nil))
        member-principal (or (get r :member_principal)
                             (if (map? r) (or (get r "memberPrincipal") (get r "member_principal")) nil))
        provider (or (get r :provider_actor)
                     (if (map? r) (or (get r "providerActor") (get r "provider_actor")) nil))]
    (let [imputed-val (if (nil? imputed) 0 imputed)
          member-principal-val (if (nil? member-principal) false member-principal)
          provider-val (if (nil? provider) kind provider)]
      [kind (int imputed-val) (boolean member-principal-val) provider-val])))

;; TODO: port-failed unit book_toritate (assembled-lint error)
;; def book_toritate(rails: list, alloc_id: str, maintainer_did: str) -> list[LedgerEntry]:
;;     """Project in-kind rails into toritate ledgerEntry records. Skips the member-principal
;;     liquidity rail (not a Public-Fund disbursement)."""
;;     out: list[LedgerEntry] = []
;;     for r in rails:
;;         kind, imputed, member_principal, _provider = _rail_fields(r)
;;         if member_principal or kind not in RAIL_TO_CATEGORY:
;;             continue  # liquidity-warifu (member loan) is not booked as fuchi income
;;         out.append(LedgerEntry(
;;             alloc_id=alloc_id,
;;             category=RAIL_TO_CATEGORY[kind],
;;             imputed_usd_micros_yr=imputed,
;;             counterparty_did=maintainer_did,
;;         ))
;;     return out
(defn book-toritate [& _]
  (throw (ex-info "TODO: port-failed" {:from "book_toritate"})))

;; TODO: port-failed unit flow_graph (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp49_qd2wq/scratch.clj:2:25: w)
;; def flow_graph(rails: list, alloc_id: str, maintainer_did: str) -> list[FlowEdge]:
;;     """Emit a kanae-renderable internal sustenance-flow graph for this allocation."""
;;     edges: list[FlowEdge] = []
;;     in_kind_total = 0
;;     legs: list[FlowEdge] = []
;;     for r in rails:
;;         kind, imputed, member_principal, provider = _rail_fields(r)
;;         in_kind = not member_principal
;;         if in_kind:
;;             in_kind_total += imputed
;;         legs.append(FlowEdge(FUCHI, provider, "fuchi-to-provider", imputed, in_kind))
;;         legs.append(FlowEdge(provider, maintainer_did, "provider-to-maintainer", imputed, in_kind))
;;     # the funding leg only covers the in-kind value (liquidity is a member loan, not funded here)
;;     if in_kind_total > 0:
;;         edges.append(FlowEdge(PUBLIC_FUND, FUCHI, "publicfund-to-fuchi", in_kind_total, True))
;;     edges.extend(legs)
;;     return edges
(defn flow-graph [& _]
  (throw (ex-info "TODO: port-failed" {:from "flow_graph"})))

;; TODO: port-failed unit BookingReceipt (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpgwadov2s/scratch.clj:4:17: e)
;; class BookingReceipt:
;;     entries: tuple
;;     operator_did: str
;;     council_level: int
;;     member_signature: str
;;     committed: bool = True
;; 
;;     def __post_init__(self) -> None:
;;         for e in self.entries:
;;             if e.cash_usd_micros != 0:
;;                 raise ValueError("cash≡0 INVARIANT (G2) holds in live mode too")
(defn booking-receipt [& _]
  (throw (ex-info "TODO: port-failed" {:from "BookingReceipt"})))

(defn write-live
  [entries gate ^:all maps {:keys [env]}]
  (let [{:keys [operator_did council_level member_signature]} gate]
    (require gate env)
    {:entries (vec entries)
     :operator_did operator_did
     :council_level council_level
     :member_signature member_signature}))

