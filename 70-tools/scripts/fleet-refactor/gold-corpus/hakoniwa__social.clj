;; ported from 20-actors/hakoniwa/methods/social.py — gold reference (Fable)
;; hakoniwa 箱庭 social-emission cell の charter ガード。ADR-2606111500。
;; distribution finding を social post へ射影し EMIT する。authorization は charter 不変条件を
;; 緩めない — ここ (emission home) で強制する:
;;   G2 — DISTRIBUTION-ONLY (非終末論)。本文は分布 (p10/p50/p90) を述べ点予測を述べない。
;;        guard-no-point が断定/予言トークン (必ず/確実に/will definitely/…) を走査し REFUSE。
;;   G3 — NON-STEERING。guard-no-steer が行動誘導トークン (買え/売れ/投票/…) を走査し REFUSE。
(ns hakoniwa.social
  (:require [clojure.string :as str]))

(def disclaimer
  (str "【箱庭シミュレーション / 架空ペルソナによる可能性分布 — 予測の断定ではありません。"
       "備えの計画材料であり、特定の行動を推奨しません。実在の個人は登場しません。】"))

;; G2 — 断定 / 単一予言の未来トークン。本文は分布で語り点に collapse しない。
(def point-tokens
  ["必ず" "確実に" "間違いなく" "絶対に" "確定" "断言" "100%"
   "will definitely" "is guaranteed" "for certain" "the future is" "we predict that"
   "確実な予測" "必ず起こる"])

;; G3 — 行動誘導 / 説得トークン。post は知らせるが行動を指示しない。
(def steer-tokens
  ["買え" "売れ" "買うべき" "売るべき" "購入し" "投票し" "投票しよう" "投票せよ"
   "支持しよう" "支持せよ" "ボイコット" "反対しよう" "賛成しよう" "今すぐ行動"
   "you should" "you must" "vote for" "vote against" "buy " "sell " "boycott"
   "sign up now" "act now" "purchase"])

(defn- scan
  "本文 (disclaimer は除外) に tokens のいずれかが含まれれば、その token を返す。"
  [body tokens]
  (let [low (str/lower-case (str/replace body disclaimer ""))]
    (some #(when (str/includes? low (str/lower-case %)) %) tokens)))

(defn guard-no-point
  "G2: 点/断定の未来を表す token があれば例外。"
  [body]
  (when-let [t (scan body point-tokens)]
    (throw (ex-info (str "G2: post body asserts a point/certain future via " (pr-str t)
                         " — refused (非終末論)")
                    {:g :G2 :token t})))
  body)

(defn guard-no-steer
  "G3: 行動誘導 token があれば例外。"
  [body]
  (when-let [t (scan body steer-tokens)]
    (throw (ex-info (str "G3: post body steers behaviour via " (pr-str t) " — refused")
                    {:g :G3 :token t})))
  body)

(defn guard-post
  "G2 + G3 を両方適用する。両方通れば body を返す。"
  [body]
  (-> body guard-no-point guard-no-steer))
