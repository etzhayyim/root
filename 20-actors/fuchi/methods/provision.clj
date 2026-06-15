;; provision.clj — 扶持 (fuchi) R1(a): wire in-kind rails to the real producing actors.
;;
;; Clojure port of provision.py (ADR-2606052300 R1), Wave 1 of the clj-native migration
;; (ADR-2606142300). Takes the routing rails (from route.clj) and emits a PROVISIONING INTENT
;; per rail, addressed to the real producing actor / commons / infra that delivers the sustenance
;; IN KIND (mitsuho/hikari/okaimono/iyashi/commons-land/Murakumo; liquidity → warifu MEMBER-PRINCIPAL).
;;
;; A provisioning intent is a DRY-RUN at R0/R1: `published` is structurally false (G10 — live
;; provisioning is Council Lv6+ + operator gated), cash is structurally 0 (G2), and
;; `server-held-key` is false (G9 — the intent is member/Council-signed). The liquidity intent is
;; member-principal (the member is the borrower/payer via warifu 0% qard-ḥasan; 扶持 never holds,
;; lends, or pays). Honours the abaki 暴 Anti-Monopoly routing policy (route-around a blocked
;; provider). stdlib + cheshire (bundled in bb) only.
(ns fuchi.methods.provision
  (:require [cheshire.core :as json]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [fuchi.methods.live-gate :as lg]))

;; rail kind → [provider-did provider-kind label]. The single map; mirrors route/LINE_TO_RAIL.
(def provider-registry
  {"housing-commons"  ["commons-land" "commons" "LANDS.md commons"]
   "food-mitsuho"     ["did:web:etzhayyim.com:actor:mitsuho" "actor" "mitsuho 瑞穂"]
   "energy-hikari"    ["did:web:etzhayyim.com:actor:hikari" "actor" "hikari 光"]
   "compute-murakumo" ["murakumo" "infra" "Murakumo mesh"]
   "tooling-okaimono" ["did:web:etzhayyim.com:actor:okaimono" "actor" "okaimono 御買物"]
   "care-iyashi"      ["did:web:etzhayyim.com:actor:iyashi" "actor" "iyashi 癒"]
   "liquidity-warifu" ["did:web:etzhayyim.com:actor:warifu" "actor" "warifu 割符 (0% qard-ḥasan)"]})

(def ^:private abaki-policy-path "20-actors/abaki/out/routing-policy.json")

(defn make-provisioning-intent
  "Construct a provisioning intent, asserting cash≡0 (G2), no-server-key (G9), unpublished (G10),
   and a known rail kind (G3)."
  [{:keys [rail-kind cash-usd-micros server-held-key published]
    :or   {cash-usd-micros 0 server-held-key false published false} :as i}]
  (when (not= 0 cash-usd-micros)
    (throw (ex-info "cash≡0 INVARIANT (G2): a provisioning intent never moves cash" {})))
  (when server-held-key
    (throw (ex-info "no-server-key INVARIANT (G9): the intent is member/Council-signed" {})))
  (when published
    (throw (ex-info "G10: published must be false — live provisioning is Council Lv6+ + operator gated" {})))
  (when-not (contains? provider-registry rail-kind)
    (throw (ex-info (str "G3: rail kind " (pr-str rail-kind) " has no provider") {})))
  (merge {:cash-usd-micros 0 :server-held-key false :published false} i))

(defn load-blocked-ids
  "Read the abaki 暴 Anti-Monopoly routing policy (if present) → a set of blocked entity ids.
   Robust: a missing file / parse error → no blocks."
  ([] (load-blocked-ids abaki-policy-path))
  ([path]
   (let [f (io/file path)]
     (if-not (.exists f)
       #{}
       (try
         (set (map #(get % "id") (get (json/parse-string (slurp f)) "blocked_entities")))
         (catch Exception _ #{}))))))

(defn provision
  "Map routing rails → provisioning intents addressed to real producing actors. Raises if a
   provider is blocked by the abaki Anti-Monopoly policy (route-around)."
  ([rails alloc-id] (provision rails alloc-id (load-blocked-ids)))
  ([rails alloc-id blocked-ids]
   (mapv
    (fn [r]
      (let [kind (:kind r)
            [provider-did provider-kind _label] (provider-registry kind)]
        (when-let [blocked (some #(when (str/includes? (str provider-did) %) %) blocked-ids)]
          (throw (ex-info (str "Provider " provider-did " blocked by abaki Anti-Monopoly policy. "
                               "React mechanism triggered: Route Around " blocked ".") {:blocked blocked})))
        (make-provisioning-intent
         {:alloc-id alloc-id :rail-kind kind :provider-did provider-did :provider-kind provider-kind
          :imputed-usd-micros-yr (long (:imputed-usd-micros-yr r 0))
          :member-principal (boolean (:member-principal r))})))
    rails)))

(defn dispatch-live
  "Authorize LIVE provisioning dispatch to the producing actors (R2 autonomous gate). cash≡0 (G2)
   + no-server-key (G9) remain structural — the gate is an authorization membrane, never an override."
  [intents gate]
  (lg/require-gate gate)
  (mapv (fn [i]
          (when (not= 0 (:cash-usd-micros i 0))
            (throw (ex-info "cash≡0 INVARIANT (G2) holds in live mode too" {})))
          (when (:server-held-key i)
            (throw (ex-info "no-server-key INVARIANT (G9) holds in live mode too" {})))
          {:intent i :operator-did (:operator-did gate) :council-level (:council-level gate)
           :member-signature (:member-signature gate) :authorized-to-publish true})
        intents))
