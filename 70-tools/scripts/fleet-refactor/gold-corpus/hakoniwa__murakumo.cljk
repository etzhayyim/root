;; ported from 20-actors/hakoniwa/methods/murakumo.py — gold reference (Fable)
;; hakoniwa 箱庭 LLM narration client (Murakumo-only). ADR-2605215000 + 2606111500.
;; G5 — 推論は必ず Murakumo fleet (LiteLLM loopback 127.0.0.1:4000) 経由。RunPod/OpenAI-direct/
;;   Vertex/Anthropic-direct/商用 GPU には決して接触しない。
;; GRACEFUL FALLBACK — gateway 不達なら deterministic TEMPLATE/scalar kernel へ落ちて :via を
;;   :template-fallback にする。fleet の有無に関わらず e2e で動き、外に出ず、ブロックしない。
;;
;; WASM premise: HTTP/JSON は host capability として注入する (http-fn / json-read / json-write)。
(ns hakoniwa.murakumo
  (:require [clojure.string :as str]))

(def gateway "http://127.0.0.1:4000/v1/chat/completions")
(def model "gemma3:4b")       ; per-node Ollama default (ADR-2605215000)

(def system-narrate
  (str "あなたは etzhayyim の箱庭 (hakoniwa) アクターのナレーターです。架空の latent ペルソナで"
       "構成されたシミュレーション結果を、防災・備えの計画材料として中立に要約します。厳守事項: "
       "(1) 単一の予測を断定しない — 結果は必ず『分布』として述べる(非終末論)。"
       "(2) 売買・投票・購入・支持などの行動を一切推奨しない(誘導禁止)。"
       "(3) 実在の個人には言及しない。日本語で1段落。"))

(defn fleet-available?
  "Murakumo gateway が loopback で応答すれば true。決して投げない。
  check-fn は host が渡す {url → status} プローブ。"
  [check-fn]
  (try (= 200 (check-fn "http://127.0.0.1:4000/v1/models"))
       (catch Exception _ false)))

(defn- chat
  "Murakumo chat completion 1 回。テキストか、不達なら nil。loopback gateway のみ接触 (G5)。
  caps = {:http-fn :json-write :json-read}。"
  [caps system user temperature]
  (let [{:keys [http-fn json-write json-read]} caps
        body (json-write {:model model
                          :messages [{:role "system" :content system}
                                     {:role "user" :content user}]
                          :temperature temperature
                          :max_tokens 220})]
    (try
      (let [resp (http-fn {:url gateway :method :post
                           :headers {"content-type" "application/json"} :body body})]
        (when (= 200 (:status resp))
          (-> (json-read (:body resp))
              (get-in [:choices 0 :message :content])
              str/trim)))
      (catch Exception _ nil))))

(defn- template-narration [scenario dist]
  (let [q (:quantiles dist)]
    (str "箱庭シミュレーション「" scenario "」の結果は、単一の予測ではなく可能性の分布です: "
         "町全体の採用スタンスは中央値 (p50) " (format "%.2f" (:p50 q)) "、"
         "下位10% (p10) " (format "%.2f" (:p10 q)) " 〜 "
         "上位90% (p90) " (format "%.2f" (:p90 q)) " の幅。"
         "これは架空ペルソナによるシナリオ探索であり、備えの計画材料です。"
         "特定の行動を推奨するものではありません。")))

(defn narrate
  "{:text :via} を返す。Murakumo を試し、不達なら deterministic template へ。
  text はまだ未ガード — 出力前に social の G2/G3 を通す。"
  [caps scenario dist]
  (if (fleet-available? (:check-fn caps))
    (let [q (:quantiles dist)
          user (str "シナリオ: " scenario "\n分布(町全体の採用スタンス): "
                    "p10=" (format "%.3f" (:p10 q)) " p50=" (format "%.3f" (:p50 q))
                    " p90=" (format "%.3f" (:p90 q))
                    " mean=" (format "%.3f" (:mean dist)) "\n"
                    "上記を1段落で中立に要約してください(分布として、行動推奨なし)。")
          text (chat caps system-narrate user 0.2)]
      (if text
        {:text text :via :murakumo}
        {:text (template-narration scenario dist) :via :template-fallback}))
    {:text (template-narration scenario dist) :via :template-fallback}))
