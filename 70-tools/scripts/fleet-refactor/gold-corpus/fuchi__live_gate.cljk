;; ported from 20-actors/fuchi/methods/live_gate.py (proper R1, git 1c29cbbc18) — gold reference (Fable)
;; 扶持 (fuchi) R1(live): すべての outward leg を既定で拒否する operator+Council ゲート。
;; ADR-2606052300 R1-live (G10 outward-gated)。
;;
;; live leg が admissible になるのは以下すべてが満たされるときのみ:
;;   1. operator process flag — env `FUCHI_ALLOW_LIVE_<LEG>` == "1"
;;   2. operator attestation — operator-did が非空
;;   3. Council ratification — council-level >= min-council (Lv6 通常 / Lv7 = couple)
;;   4. member signature (no-server-key) — member-signature が非空かつ server 署名でない
;;      (server は決して満たせない; ADR-2605231525)
;;
;; ゲートは構造的不変条件 (cash≡0 G2 / no-server-key G9 / in-kind-only G3) を緩めない。
;; require は authorization membrane であって invariant override ではない。
;; env は明示注入 (script clock/env は設計上不在 — env を渡す)。
(ns fuchi.methods.live-gate
  (:require [clojure.string :as str]))

;; leg → [env-flag minimum-council]。Lv6 = 通常 outward; Lv7 = invariant-adjacent。
(def leg-policy
  {"provision" ["FUCHI_ALLOW_LIVE_PROVISION" 6]
   "vote"      ["FUCHI_ALLOW_LIVE_VOTE" 6]
   "book"      ["FUCHI_ALLOW_LIVE_BOOK" 6]
   "couple"    ["FUCHI_ALLOW_LIVE_COUPLE" 7]}) ; displacement wave を束ねる — invariant-adjacent

(defn live-gate
  "live leg が運ぶ認可。既定構築 ⇒ 全条件で拒否される。"
  [leg & {:keys [operator-did council-level member-signature]
          :or {operator-did "" council-level 0 member-signature ""}}]
  (when-not (contains? leg-policy leg)
    (throw (ex-info (str "unknown live leg " (pr-str leg)) {:leg leg :known (keys leg-policy)})))
  {:leg leg
   :operator-did operator-did
   :council-level council-level
   :member-signature member-signature})

(defn- server-signer?
  "server 署名 (または空) かどうか — これらは member-signed を満たさない。"
  [sig]
  (let [s (str/lower-case (str/trim (or sig "")))]
    (or (empty? s)
        (some #(str/starts-with? s %) ["server" "did:server" ":server"])
        (contains? #{"server" "anon"} s))))

(defn gate-status
  "各ゲート条件を RAISE せず報告する (dry-run / analyze 用)。env は {flag value} map。"
  [gate env]
  (let [[flag min-council] (leg-policy (:leg gate))
        conds {:operator-flag (= (get env flag) "1")
               :operator-attested (not (str/blank? (:operator-did gate)))
               :council-ratified (>= (:council-level gate) min-council)
               :member-signed (not (server-signer? (:member-signature gate)))}]
    {:leg (:leg gate)
     :env-flag flag
     :min-council min-council
     :conditions conds
     :admissible (every? true? (vals conds))}))

(defn live-gate-require
  "live leg を認可する。満たされない最初の条件名で ex-info を投げる。
  成功時は gate-status を返す。cash≡0 / no-server-key / in-kind-only は緩めない。"
  [gate env]
  (let [st (gate-status gate env)
        c (:conditions st)
        [flag min-council] (leg-policy (:leg gate))]
    (cond
      (not (:operator-flag c))
      (throw (ex-info (str "G10: live '" (:leg gate) "' refused — operator flag " flag "=1 not set")
                      {:g :G10 :unmet :operator-flag}))
      (not (:operator-attested c))
      (throw (ex-info (str "G10: live '" (:leg gate) "' refused — no operator attestation")
                      {:g :G10 :unmet :operator-attested}))
      (not (:council-ratified c))
      (throw (ex-info (str "G10: live '" (:leg gate) "' refused — Council Lv" min-council
                           "+ required (have Lv" (:council-level gate) ")")
                      {:g :G10 :unmet :council-ratified}))
      (not (:member-signed c))
      (throw (ex-info (str "G9/no-server-key: live '" (:leg gate)
                           "' refused — a member signature is required (server can never sign)")
                      {:g :G9 :unmet :member-signed}))
      :else st)))
