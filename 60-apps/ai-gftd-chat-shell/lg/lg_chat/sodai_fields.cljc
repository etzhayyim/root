(ns lg-chat.sodai-fields
  "渋谷区 粗大ごみ 公式フォームの field-map / CAPTCHA マーカーの SSoT (clj port).

  Faithful port of lg_chat/sodai_fields.py (ADR-2606280030). The shibuya actor
  boundary values, the candidate-selector field-map, and the CAPTCHA markers are
  the SSoT shared by the sodai-submit graph. `load-field-map` overlays
  DEFAULT-FIELD-MAP with the env SODAI_FIELD_MAP (JSON) just like the Python.

  ⚠️ Selectors are guesses (real form unverified) — calibrate via mode=\"discover\"
  and override with env SODAI_FIELD_MAP."
  (:require [cheshire.core :as json]
            [clojure.string :as str]))

;; ── shibuya actor 境界 (lightweight separation) — フロント ward.ts と対の SSoT ──
(def WARD-CODE "13113")
(def WARD-NAME "渋谷区")
(def ACTOR-DID "did:web:gftd.ai:actor:shibuya")
(def NSID-PREFIX "ai.gftd.apps.shibuya")
(def RECEPTION-URL "https://sodai.tokyokankyo.or.jp/Sodai/V2Main/13113/0")

;; application キー → 候補 CSS セレクタ。最初に見つかった可視要素へ入力する。
(def DEFAULT-FIELD-MAP
  {"name"     ["input[name*='name' i]:not([name*='kana' i])" "#applicantName" "#name"]
   "nameKana" ["input[name*='kana' i]" "input[name*='furigana' i]" "#nameKana"]
   "postal"   ["input[name*='zip' i]" "input[name*='post' i]" "#zipCode" "#postalCode"]
   "address"  ["input[name*='addr' i]" "textarea[name*='addr' i]" "#address"]
   "building" ["input[name*='building' i]" "input[name*='tatemono' i]" "#building"]
   "phone"    ["input[name*='tel' i]" "input[name*='phone' i]" "#tel" "#phone"]
   "email"    ["input[type='email']" "input[name*='mail' i]" "#email"]})

;; CAPTCHA / bot 認証の検知マーカー。出たら自動操作は止め、人間に渡す (突破しない)。
(def CAPTCHA-MARKERS
  ["recaptcha" "g-recaptcha" "hcaptcha" "h-captcha" "cf-turnstile"
   "画像認証" "ロボットではありません" "認証コードを入力"])

(defn load-field-map
  "DEFAULT-FIELD-MAP を host supplied JSON で上書きしたものを返す。"
  ([] (load-field-map nil))
  ([raw]
   (let [raw (some-> raw str/trim)]
    (if (or (nil? raw) (empty? raw))
      DEFAULT-FIELD-MAP
      (try
        (let [override (json/parse-string raw)]
          (reduce-kv (fn [m k v]
                       (assoc m k (if (sequential? v) (vec v) [(str v)])))
                     DEFAULT-FIELD-MAP
                     override))
        (catch Exception _
          DEFAULT-FIELD-MAP))))))
