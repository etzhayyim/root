;; book.clj — 扶持 (fuchi) R1(c): toritate booking + kanae-renderable flow viz.
;;
;; Clojure port of book.py (ADR-2606052300 R1), Wave 1 of the clj-native migration (ADR-2606142300).
;; Two cross-actor projections of an accepted allocation:
;;
;; 1. book-toritate — projects each IN-KIND rail into a toritate ledgerEntry using toritate's own
;;    category enum (ADR-2605262900): housing/food/energy → subsistence-flow, compute/tooling →
;;    vocation-flow, care → care-flow. `cashStipendUsd ≡ 0`; :payroll/:salary/:wage are
;;    unrepresentable. The MEMBER-PRINCIPAL liquidity rail is NOT booked as income (it is the
;;    member's own warifu 0% loan, not a Public-Fund disbursement — honest accounting).
;;
;; 2. flow-graph — a kanae-renderable internal sustenance-flow Sankey: Public Fund → 扶持 →
;;    each provider → the maintainer. The liquidity leg is flagged in-kind false (member-principal);
;;    the funding leg covers only the in-kind value. stdlib only.
(ns fuchi.methods.book
  (:require [fuchi.methods.live-gate :as lg]))

;; rail kind → toritate ledgerEntry category. liquidity-warifu is ABSENT (not a Public-Fund disbursement).
(def rail-to-category
  {"housing-commons"  "subsistence-flow"
   "food-mitsuho"     "subsistence-flow"
   "energy-hikari"    "subsistence-flow"
   "compute-murakumo" "vocation-flow"
   "tooling-okaimono" "vocation-flow"
   "care-iyashi"      "care-flow"})

(def toritate-categories #{"subsistence-flow" "vocation-flow" "care-flow" "liberation-flow" "grant"})
(def forbidden-categories #{"payroll" "salary" "wage" "bonus" "commission"})

(def public-fund "did:web:etzhayyim.com:actor:etzhayyim-public-fund")
(def fuchi "did:web:etzhayyim.com:actor:fuchi")

(defn make-ledger-entry
  "Construct a toritate ledgerEntry, asserting cash≡0 + a representable category (no payroll/wage)."
  [{:keys [category cash-usd-micros] :or {cash-usd-micros 0} :as e}]
  (when (not= 0 cash-usd-micros)
    (throw (ex-info "cash≡0 INVARIANT (G2): toritate cashStipendUsd ≡ 0" {})))
  (when (forbidden-categories category)
    (throw (ex-info (str "category " (pr-str category) " unrepresentable (no payroll/wage)") {})))
  (when-not (toritate-categories category)
    (throw (ex-info (str "category " (pr-str category) " not a toritate ledgerEntry category") {})))
  (merge {:cash-usd-micros 0} e))

(defn book-toritate
  "Project in-kind rails into toritate ledgerEntry records. Skips the member-principal liquidity
   rail (not a Public-Fund disbursement)."
  [rails alloc-id maintainer-did]
  (vec (keep (fn [r]
               (let [kind (:kind r)]
                 (when (and (not (:member-principal r)) (rail-to-category kind))
                   (make-ledger-entry {:alloc-id alloc-id
                                       :category (rail-to-category kind)
                                       :imputed-usd-micros-yr (:imputed-usd-micros-yr r)
                                       :counterparty-did maintainer-did}))))
             rails)))

(defn flow-graph
  "Emit a kanae-renderable internal sustenance-flow graph for this allocation."
  [rails _alloc-id maintainer-did]
  (let [legs (vec (mapcat
                   (fn [r]
                     (let [in-kind  (not (:member-principal r))
                           imputed  (:imputed-usd-micros-yr r)
                           provider (:provider-actor r)]
                       [{:frm fuchi :to provider :flow-class "fuchi-to-provider"
                         :imputed-usd-micros-yr imputed :in-kind in-kind}
                        {:frm provider :to maintainer-did :flow-class "provider-to-maintainer"
                         :imputed-usd-micros-yr imputed :in-kind in-kind}]))
                   rails))
        in-kind-total (reduce + 0 (map :imputed-usd-micros-yr (remove :member-principal rails)))]
    (vec (concat (when (pos? in-kind-total)
                   [{:frm public-fund :to fuchi :flow-class "publicfund-to-fuchi"
                     :imputed-usd-micros-yr in-kind-total :in-kind true}])
                 legs))))

(defn write-live
  "Authorize a LIVE write of the ledgerEntry projection into toritate (R2 autonomous gate). cash≡0
   holds on every entry in live mode too."
  [entries gate]
  (lg/require-gate gate)
  (doseq [e entries]
    (when (not= 0 (:cash-usd-micros e 0))
      (throw (ex-info "cash≡0 INVARIANT (G2) holds in live mode too" {}))))
  {:entries (vec entries) :operator-did (:operator-did gate) :council-level (:council-level gate)
   :member-signature (:member-signature gate) :committed true})
