#!/usr/bin/env bb
;; Working Clojure port of methods/social.py.
(ns shionome.methods.social
  "social.clj — 潮目 (shionome) DRY-RUN social-post projection. ADR-2606072200.

  Projects an AGGREGATE capital-flow finding into a social post (app.bsky.feed.post-shaped),
  enforcing the post invariants in their third home (mirror of the ontology :db/allowed +
  networkPost.edn :const):

    G2 — THE DEFINING INVARIANT (トレードはしない): noTradeNotice=true; the body is SCANNED for
         trade/advisory tokens (buy / sell / target / 推奨 / 買い / 売り …) and REFUSED if any
         appear. A post narrates where money MOVED, never what anyone should do.
    G5 — every post opens with the observational-mirror disclaimer (isMirror=true), never a
         trade signal, never financial advice.
    G7 — serverHeldKey=false; the member signs, the server never does (ADR-2605231525).
    G8 — status is 'dry-run' only at R0; 'published' is unrepresentable. A live post needs
         Council Lv6+ + operator + a member signature (build-live raises here).
    G3 — the post carries the same ≥2 public-source citations as the finding.

  Reuses weave.cljc public fns:
    w/source-denied  — returns the offending denied token or \"\" if clean (§2(e)/N5 gate)
    w/trade-token-in — returns the first trade/advisory token in text or \"\" if clean (G2 gate)

  Stdlib only. Deterministic.
  Run:  bb --classpath 20-actors 20-actors/shionome/methods/social.clj"
  (:require [shionome.methods.weave :as w]
            [clojure.string :as str]))

(def DISCLAIMER
  "【観測ミラー / capital-flow observation — NOT financial advice, トレードはしない】 公開市場データから観測した資金フローの集計です。売買の推奨・目標価格・ポジション提案は一切しません。")

(defn- guard-sources
  "G3 + Rider §2(e)/N5 — filter to non-blank sources, require ≥2, reject commercial terminals."
  [sources]
  (let [s (vec (filter #(seq (str/trim (str %))) (or sources [])))]
    (when (< (count s) 2)
      (throw (ex-info "G3: a post needs ≥2 public-source citations" {})))
    (let [d (w/source-denied s)]
      (when (seq d)
        (throw (ex-info (str "Rider §2(e)/N5: source " (pr-str d)
                             " is a commercial market-data terminal — a post may not cite it")
                        {}))))
    s))

(defn- guard-no-trade
  "G2 core (トレードはしない) — refuse to emit a post whose body contains a trade/advisory
  token. The disclaimer text is exempt (it NAMES the prohibited acts to disclaim them)."
  [body]
  (let [scanned (str/replace body DISCLAIMER "")
        t (w/trade-token-in scanned)]
    (when (seq t)
      (throw (ex-info
              (str "G2: post body contains the trade/advisory token " (pr-str t)
                   " — refused (shionome never recommends a trade; it only observes flows). トレードはしない.")
              {})))))

(defn- fmt1
  "Format a double to 1 decimal place (Python's f\"{x:.1f}\")."
  [x]
  (format "%.1f" (double x)))

(defn- post-
  "Assemble a networkPost record with every invariant pinned. status is ALWAYS dry-run."
  [subject body sources author]
  {":post/subject"        subject
   ":post/body"           body
   ":post/status"         ":dry-run"    ;; G8 — published is unrepresentable
   ":post/is-mirror"      true          ;; G5
   ":post/no-trade-notice" true          ;; G2 — トレードはしない
   ":post/server-held-key" false         ;; G7 / no-server-key
   ":post/author"         author        ;; member DID (required only for a gated live post)
   ":post/sources"        sources})     ;; G3

(defn draft-netflow-post
  "A dry-run post about where money is going / leaving (top inflow + top outflow bucket).
  Aggregate, factual, non-advisory."
  ([net-rows sources] (draft-netflow-post net-rows sources ""))
  ([net-rows sources author]
   (let [srcs (guard-sources sources)
         inflows  (filter #(> (get % "net") 0) net-rows)
         outflows (filter #(< (get % "net") 0) net-rows)
         top-in  (first inflows)
         top-out (when (seq outflows) (apply min-key #(get % "net") outflows))
         ;; parts mirrors Python: [DISCLAIMER "" <optional inflow> <optional outflow> <src-count>]
         middle (cond-> []
                  top-in  (conj (str "資金流入トップ: " (get top-in "label")
                                     " (net +" (fmt1 (get top-in "net")) "bn)。"))
                  top-out (conj (str "資金流出トップ: " (get top-out "label")
                                     " (net " (fmt1 (get top-out "net")) "bn)。"))
                  true    (conj (str "出典 " (count srcs) " 件。")))
         ;; body = "\n\n".join([DISCLAIMER, " ".join(parts[2:])]) when len(parts) > 2
         ;; (always true since parts has at least the source-count item)
         body (str DISCLAIMER "\n\n" (str/join " " middle))]
     (guard-no-trade body)
     (post- "netflow" body srcs author))))

(defn draft-rotation-post
  "A dry-run post about the largest observed rotation pair (どこからどこへ)."
  ([rotation-rows sources] (draft-rotation-post rotation-rows sources ""))
  ([rotation-rows sources author]
   (let [srcs (guard-sources sources)
         top  (first rotation-rows)
         body (if top
                (str DISCLAIMER "\n\n"
                     "最大の資金回転: " (get top "from_label") " → " (get top "to_label")
                     " (" (fmt1 (get top "magnitude")) "bn 相当)。"
                     "出典 " (count srcs) " 件。")
                (str DISCLAIMER "\n\n観測された資金回転はありません。出典 " (count srcs) " 件。"))]
     (guard-no-trade body)
     (post- "rotation" body srcs author))))

(defn draft-regime-post
  "A dry-run post stating the FACTUAL cross-asset regime descriptor (risk-on/off/mixed).
  Descriptive only — explicitly carries the no-trade notice (G2)."
  ([regime sources] (draft-regime-post regime sources ""))
  ([regime sources author]
   (let [srcs (guard-sources sources)
         jp   (get {"risk-on" "リスクオン" "risk-off" "リスクオフ"
                    "mixed" "まちまち" "indeterminate" "判定不能"}
                   (get regime "regime") (get regime "regime"))
         risk-net (double (get regime "risk_net"))
         safe-net (double (get regime "safe_net"))
         ;; Python f-string: f"{risk_net:+.1f}bn" → e.g. "+27.3bn"
         sign-fmt (fn [x] (if (>= x 0) (str "+" (fmt1 x)) (fmt1 x)))
         body (str DISCLAIMER "\n\n"
                   "クロスアセット観測: " jp " (" (get regime "regime") ") — "
                   "リスク資産 net " (sign-fmt risk-net) "bn / "
                   "安全資産 net " (sign-fmt safe-net) "bn。"
                   "記述であり助言ではありません。出典 " (count srcs) " 件。")]
     (guard-no-trade body)
     (post- "regime" body srcs author))))

(defn build-live
  "G8 — live posting is outward-gated. Refuses by construction at R0."
  [& _args]
  (throw (ex-info
          (str "shionome R0: live social posting is Council Lv6+ + operator + member-signature gated (G8). "
               "Only dry-run posts are producible offline.")
          {})))

(defn -main [& _argv]
  (println "# 潮目 (shionome) — DRY-RUN social post demo")
  (println "  (run social.py for a live seed demo; this stub prints the DISCLAIMER)")
  (println DISCLAIMER))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
