;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hakoniwa/methods/murakumo.py (unit_refactor stage 0)
;; murakumo.py — hakoniwa 箱庭 LLM narration client (Murakumo-only). ADR-2605215000 + 2606111500.
(ns root.hakoniwa.methods.murakumo
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare gateway fleet-available chat system-narrate template-narration narrate persona-step)

(def gateway "http://127.0.0.1:4000/v1/chat/completions")
(def model "gemma3:4b")
(def timeout 8)

;; TODO: port-failed unit fleet_available (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpww9stowl/scratch.clj:2:28: e)
;; def fleet_available(url: str = "http://127.0.0.1:4000/v1/models", timeout: int = 3) -> bool:
;;     """True iff the Murakumo LiteLLM gateway answers on loopback. Never raises."""
;;     try:
;;         with urllib.request.urlopen(url, timeout=timeout) as r:
;;             return r.status == 200
;;     except Exception:
;;         return False
(defn fleet-available [& _]
  (throw (ex-info "TODO: port-failed" {:from "fleet_available"})))

;; TODO: port-failed unit _chat (assembled-lint error)
;; def _chat(system: str, user: str, *, temperature: float = 0.2) -> str | None:
;;     """One Murakumo chat completion. Returns the text, or None if the fleet is unreachable.
;;     ONLY ever contacts the loopback gateway (G5)."""
;;     body = json.dumps({
;;         "model": MODEL,
;;         "messages": [{"role": "system", "content": system},
;;                      {"role": "user", "content": user}],
;;         "temperature": temperature,
;;         "max_tokens": 220,
;;     }).encode("utf-8")
;;     req = urllib.request.Request(GATEWAY, data=body,
;;                                  headers={"Content-Type": "application/json"})
;;     try:
;;         with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
;;             out = json.loads(r.read().decode("utf-8"))
;;         return out["choices"][0]["message"]["content"].strip()
;;     except (urllib.error.URLError, KeyError, ValueError, TimeoutError, OSError):
;;         return None
(defn chat [& _]
  (throw (ex-info "TODO: port-failed" {:from "_chat"})))

(def system-narrate
  "あなたは etzhayyim の箱庭 (hakoniwa) アクターのナレーターです。架空の latent ペルソナで構成されたシミュレーション結果を、防災・備えの計画材料として中立に要約します。厳守事項: (1) 単一の予測を断定しない — 結果は必ず『分布』として述べる(非終末論)。(2) 売買・投票・購入・支持などの行動を一切推奨しない(誘導禁止)。(3) 実在の個人には言及しない。日本語で1段落。"
  "あなたは etzhayyim の箱庭 (hakoniwa) アクターのナレーターです。架空の latent ペルソナで構成されたシミュレーション結果を、防災・備えの計画材料として中立に要約します。厳守事項: (1) 単一の予測を断定しない — 結果は必ず『分布』として述べる(非終末論)。(2) 売買・投票・購入・支持などの行動を一切推奨しない(誘導禁止)。(3) 実在の個人には言及しない。日本語で1段落。")

(defn _template-narration [scenario dist]
  (let [q (:quantiles dist)]
    (str "箱庭シミュレーション「" scenario "」の結果は、単一の予測ではなく可能性の分布です: 町全体の採用スタンス中央値 (p50) "
         (format "%.2f" (:p50 q)) ", 下位10% (p10) "
         (format "%.2f" (:p10 q)) " 〜 上位90% (p90) "
         (format "%.2f" (:p90 q)) " の幅。これは架空ペルソナによるシナリオ探索であり、備えの計画材料です。特定の行動を推奨するものではありません。")))

;; TODO: port-failed unit narrate (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp_9fkrpji/scratch.clj:4:28: w)
;; def narrate(scenario: str, dist: dict, *, prefer_fleet: bool = True) -> dict:
;;     """Return {text, via}. Tries Murakumo; falls back to a deterministic template. The text is
;;     NOT yet guarded — social.draft_distribution_post applies G2/G3 before emission."""
;;     if prefer_fleet and fleet_available():
;;         q = dist["quantiles"]
;;         user = (f"シナリオ: {scenario}\n"
;;                 f"分布(町全体の採用スタンス): p10={q[':p10']:.3f} p25={q[':p25']:.3f} "
;;                 f"p50={q[':p50']:.3f} p75={q[':p75']:.3f} p90={q[':p90']:.3f} "
;;                 f"mean={dist['mean']:.3f} stdev={dist['stdev']:.3f}\n"
;;                 f"上記を1段落で中立に要約してください(分布として、行動推奨なし)。")
;;         text = _chat(SYSTEM_NARRATE, user)
;;         if text:
;;             return {"text": text, "via": ":murakumo"}
;;     return {"text": _template_narration(scenario, dist), "via": ":template-fallback"}
(defn narrate [& _]
  (throw (ex-info "TODO: port-failed" {:from "narrate"})))

;; TODO: port-failed unit persona_step (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp_91gf0tr/scratch.clj:15:75: )
;; def persona_step(stance: float, neighbour_mean: float, susceptibility: float, anchor: float,
;;                  *, prefer_fleet: bool = False) -> dict:
;;     """LLM-persona swarm variant (gated). Asks the fleet for a synthetic persona's next stance;
;;     falls back to the deterministic Friedkin-Johnsen scalar update. Returns {stance, via}.
;; 
;;     prefer_fleet defaults False — the swarm variant is opt-in (G8) and the deterministic kernel
;;     is the default + test path. Even when on, it stays Murakumo-only (loopback) and clamps."""
;;     if prefer_fleet and fleet_available():
;;         user = (f"架空ペルソナ(susceptibility={susceptibility:.2f}, anchor={anchor:.2f})の"
;;                 f"現在スタンス={stance:.2f}、近傍平均={neighbour_mean:.2f}。"
;;                 f"次ステップのスタンスを 0〜1 の数値のみで答えてください。")
;;         text = _chat("0〜1の数値のみを返す。説明不要。", user, temperature=0.0)
;;         if text:
;;             try:
;;                 v = float(text.split()[0])
;;                 return {"stance": min(1.0, max(0.0, v)), "via": ":murakumo"}
;;             except (ValueError, IndexError):
;;                 pass
;;     nx = susceptibility * neighbour_mean + (1.0 - susceptibility) * anchor
;;     return {"stance": min(1.0, max(0.0, nx)), "via": ":kernel-fallback"}
(defn persona-step [& _]
  (throw (ex-info "TODO: port-failed" {:from "persona_step"})))

