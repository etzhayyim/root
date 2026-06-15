;; route.clj — 扶持 (fuchi) in-kind rail decomposition + governance gate.
;;
;; Clojure port of route.py (ADR-2606052300), Wave 1 of the clj-native migration (ADR-2606142300).
;; Two pure functions, both charter-clean by construction:
;;
;; 1. route-envelope — decompose a maintainer's sustenance envelope into delivery RAILS over the
;;    EXISTING producing actors/commons (housing→commons land, food→mitsuho, energy→hikari,
;;    compute→Murakumo, tooling→okaimono, care→iyashi, liquidity→warifu 0% qard-ḥasan
;;    MEMBER-PRINCIPAL). A :cash / :stipend rail is UNREPRESENTABLE (cash≡0); 扶持 never pays.
;;
;; 2. gov-route — the governance gate: a PURE FUNCTION of (imputed total, invariant touch,
;;    Charter-Rider hit) → {:refused :council-lv7 :sbt-vote :auto}. 扶持 computes + ROUTES to the
;;    body that decides; it never DECIDES accept/reject (非裁定, the ake G2 pattern).
;; stdlib only.
(ns fuchi.methods.route
  (:require [clojure.string :as str])
  (:import [java.math BigDecimal RoundingMode]))

;; G3 — envelope line → [rail-kind provider-actor]. The closed map (mirror of the ontology).
(def line-to-rail
  {"housing"   ["housing-commons" "commons-land"]
   "food"      ["food-mitsuho" "mitsuho"]
   "energy"    ["energy-hikari" "hikari"]
   "compute"   ["compute-murakumo" "murakumo"]
   "tooling"   ["tooling-okaimono" "okaimono"]
   "care"      ["care-iyashi" "iyashi"]
   "liquidity" ["liquidity-warifu" "warifu"]})

;; G7 — governance threshold (imputed USD micros / yr): auto fast-path below ~$24k/yr in-kind.
(def optimistic-ceiling-usd-micros-yr 24000000000)
;; Charter-Rider §2(a)-(h) hard-gate tokens (local mirror of charter_rider.scan()).
(def rider-forbidden
  ["advertis" "affiliate" "adsense" "weapon" "munition" "fire-control"
   "surveillance" "biometric" "addictive" "dark-pattern" "広告" "兵器"])
;; Allocation contexts that touch a constitutional invariant → Council Lv7+ (never optimistic).
(def invariant-touch-tokens
  ["commons-land" "land-grant" "new-land" "force" "license-change" "charter"])

(defn- kw [v] (-> (str (or v "")) (str/replace #"^:+" "") (str/split #"/") last str/lower-case))

(defn route-envelope
  "Decompose envelope lines → in-kind delivery rails. The liquidity line becomes a MEMBER-PRINCIPAL
   warifu rail (扶持 never pays); a :cash line RAISES (cash≡0)."
  [envelope]
  (mapv
   (fn [line]
     (let [kind-kw (kw (:envelope/line line ""))]
       (when (#{"cash" "cash-disbursement" "stipend"} kind-kw)
         (throw (ex-info "cash≡0 INVARIANT: a cash/stipend rail is UNREPRESENTABLE (扶持 never pays cash)" {})))
       (when (not= 0 (long (:envelope/cash-usd-micros line 0)))
         (throw (ex-info "cash≡0 INVARIANT: :envelope/cash-usd-micros must be 0" {})))
       (when-not (contains? line-to-rail kind-kw)
         (throw (ex-info (str "G3: envelope line " (pr-str kind-kw) " has no in-kind rail") {})))
       (let [[rail-kind provider] (line-to-rail kind-kw)]
         {:kind rail-kind
          :provider-actor provider
          :imputed-usd-micros-yr (long (:envelope/imputed-usd-micros-yr line 0))
          :member-principal (= kind-kw "liquidity")})))
   envelope))

(defn in-kind-coverage
  "Fraction of total imputed value delivered IN KIND (vs member-principal liquidity). The honesty
   metric: how much of a maintainer's sustenance never touches fiat at all."
  [rails]
  (let [total (reduce + 0 (map :imputed-usd-micros-yr rails))]
    (if (<= total 0)
      1.0
      (let [in-kind (reduce + 0 (map :imputed-usd-micros-yr (remove :member-principal rails)))]
        (.doubleValue (.setScale (BigDecimal/valueOf (/ (double in-kind) total)) 4 RoundingMode/HALF_EVEN))))))

(defn rider-hit
  "Return the first Charter-Rider forbidden token present across `texts`, or \"\"."
  [& texts]
  (let [blob (str/lower-case (str/join " " (map #(or % "") texts)))]
    (or (some #(when (str/includes? blob %) %) rider-forbidden) "")))

(defn touches-invariant
  "True if any constitutional-invariant token appears across `texts`."
  [& texts]
  (let [blob (str/lower-case (str/join " " (map #(or % "") texts)))]
    (boolean (some #(str/includes? blob %) invariant-touch-tokens))))

(defn gov-route
  "G7 INVARIANT — route is a PURE FUNCTION of (imputed total, invariant touch, rider). 扶持 never
   decides; this only ROUTES to the body that decides (非裁定, ake G2 pattern)."
  [imputed-total-usd-micros-yr invariant-touch rider]
  (cond
    (and rider (not (str/blank? (str rider)))) "refused"      ; Charter-Rider §2 hit
    invariant-touch                             "council-lv7"  ; e.g. a new commons-land grant
    (> imputed-total-usd-micros-yr optimistic-ceiling-usd-micros-yr) "sbt-vote"  ; → 1 SBT=1 vote
    :else                                       "auto"))       ; optimistic fast-path
