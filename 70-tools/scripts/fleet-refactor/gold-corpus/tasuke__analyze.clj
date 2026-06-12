;; ported from 20-actors/tasuke/methods/analyze.py — gold reference (Fable)
;; 助 (tasuke) — :representative victim case 上の end-to-end membrane。
;; 各 seed case を free support pipeline へ: intake → triage → member-authored 文書生成
;;   → 各文書が FREE / member-authored / signature-required / draft-only であることを assert。
;; offline scorecard を出す。live filing/submission/send は無し (全て G9 = Council Lv6+ + operator)。
;; これは全行程が ¥0 であることの dry-run demonstration。
;;
;; triage / doc generators (rg) / assert-member-authored は注入する (I/O 境界の外側)。
(ns tasuke.methods.analyze
  (:require [clojure.string :as str]))

;; 暗号化証拠の小さな stand-in (G6 — ref + hash のみ、plaintext は持たない)
(def demo-evidence
  [{:evidence/id "ev1" :evidence/kind :screenshot
    :evidence/envelope-ref "ipfs://bafyEVIDENCE1" :evidence/captured-at 1717500100}
   {:evidence/id "ev2" :evidence/kind :transaction-record
    :evidence/envelope-ref "ipfs://bafyEVIDENCE2" :evidence/captured-at 1717500200}])

(defn docs-for
  "scam KIND に合う文書セットを選ぶ — 常に police core + kind 固有の追加。
  rg = {:damage-report :incident-statement :evidence-index :damage-calculation
        :bank-freeze-request :platform-request :recovery-plan} の生成関数 map。"
  [rg case kind]
  (let [cid (:case/id case)
        ev (mapv #(assoc % :evidence/case cid) demo-evidence)
        core [((:damage-report rg) case)
              ((:incident-statement rg) case)
              ((:evidence-index rg) case ev)
              ((:damage-calculation rg) case)]
        extras (cond-> []
                 (= kind "unauthorized-transfer")
                 (conj ((:bank-freeze-request rg) case))
                 (contains? #{"account-takeover" "impersonation" "sns-fraud" "phishing"} kind)
                 (conj ((:platform-request rg) case "凍結・復旧"))
                 (contains? #{"account-takeover" "phishing"} kind)
                 (conj ((:recovery-plan rg) case "（対象サービス）")))]
    (into core extras)))

(defn- strip-colon [kw] (str/replace-first (str kw) #"^:" ""))

(defn run
  "全 case を pipeline に通し、{:rows :total-cost} を返す。
  triage は free/consented でなければ例外 (G1/G7)。各生成文書に assert-member-authored を適用。"
  [{:keys [triage rg assert-member-authored]} seed]
  (let [rows (for [case (:case/batch seed)
                   :let [tri (triage case)
                         kind (strip-colon (:triage/scam-kind tri))
                         docs (docs-for rg case kind)]]
               (do
                 (run! assert-member-authored docs)   ; G1/G2/G3/G9 guard on each doc
                 {:case (:case/id case)
                  :kind kind
                  :severity (strip-colon (:triage/severity tri))
                  :cost (:triage/support-cost-jpy tri)
                  :windows (mapv strip-colon (:triage/windows tri))
                  :docs (mapv #(strip-colon (:doc/kind %)) docs)
                  :actions (:triage/actions tri)
                  :deadlines (:triage/deadlines tri)
                  :paid-referral (:triage/paid-referral tri)}))]
    {:rows (vec rows)
     :total-cost (reduce + 0 (map :cost rows))}))
