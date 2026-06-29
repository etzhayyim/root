#!/usr/bin/env bb
;; shinogi 鎬 — social-protocol activity membrane (AT-proto dry-run projection, no-server-key).
(ns shinogi.methods.social
  "social.cljc — shinogi 鎬 SOCIAL-PROTOCOL ACTIVITY (ADR-2606291200, on the actor
  self-publication seed ADR-2606272355 + the seed-and-grow doctrine ADR-2606281500).

  shinogi is ANALYSIS-ONLY (G4). This membrane is the ONE careful path onto the
  social protocol: it PROJECTS shinogi's disclosed-hypothesis findings — a vicious
  loop read-off, the 受験失敗 / 卒業後 relief cycles, and the wellbecoming
  ENERGY-FLOW DESIGN — into `app.bsky.feed.post`-shaped DRY-RUN MIRROR posts. It
  drafts; it does not broadcast.

  GUARDS (every draft):
    - ≥2 public-source citations or `enough-sources` raises (G5 disclosed basis).
    - non-adjudicating MIRROR + the analysis-only / wellbecoming disclaimer (G7).
    - `:post/server-held-key false` (no-server-key, ADR-2605231525): the post is
      signed by the issuing MEMBER/actor's OWN key in their runtime, never by a
      platform-held key here.
    - `:post/status :dry-run`; `build-live` RAISES — live broadcast is gated on a
      member CACAO leash (ADR-2606111400) + Council Lv6+ (G13). Per ADR-2606281500
      the seed (not the gate on this high-stakes youth-wellbeing topic) is what we
      plant; growth (live speech) is member/actor-signed, never an autonomous
      platform key.
    - person-excluded (G6) + never a student/school/country shame-rank (G8).

  G4 is preserved BY ABSENCE of any autonomous live-publish path: drafts are inert
  data until a member signs them. Pure; no I/O; no network. ADR-2606291200."
  (:require [clojure.string :as str]))

(def ^:private disclaimer
  "(shinogi 鎬 — 分析専用の MIRROR。仮説であり因果の証明でも予測でも指令でもない。relief/leverage の地図であって晒しランキングではない。)")

(defn enough-sources
  "Require ≥2 disclosed public-source citations (G5). Raises otherwise."
  [sources]
  (when (< (count (remove str/blank? (or sources []))) 2)
    (throw (ex-info "G5: a shinogi post needs ≥2 disclosed public-source citations" {:sources sources})))
  sources)

(defn- draft
  "Assemble a DRY-RUN post record. server-held-key false; status :dry-run."
  [text sources]
  (enough-sources sources)
  {:post/type "app.bsky.feed.post"
   :post/text (str text "\n\n" disclaimer)
   :post/sources (vec sources)
   :post/langs ["ja"]
   :post/status :dry-run
   :post/server-held-key false
   :post/non-adjudicating true
   :post/person-excluded true})

(defn draft-loop-post
  "Project one structural-loop read-off (a disclosed hypothesis) into a dry-run post."
  [loop-finding sources]
  (draft
   (str "【受験 involution 観測 / HYPOTHESIS】loop " (:id loop-finding)
        " (" (name (:type loop-finding)) ") の drive=" (:drive loop-finding)
        " → regime " (name (:regime loop-finding)) "。"
        (when (= :vicious (:regime loop-finding)) "悪循環の傾向(緩和のレバレッジは別途)。"))
   sources))

(defn draft-cycle-post
  "Project a relief cycle read-off (受験失敗 or 卒業後 頑張れない/躺平) — routed to relief, never amplified."
  [cycle-name route relief-gap sources]
  (draft
   (str "【" cycle-name " cycle / HYPOTHESIS】relief-gap=" relief-gap
        " (>0=圧力が緩和に勝る)。構造的に記述し、RELIEF (" (str/join " / " route)
        ") へ routing する — 絶望や怠惰の断定ではない(§1.4/§1.13)。")
   sources))

(defn draft-energy-flow-post
  "Project the wellbecoming ENERGY-FLOW DESIGN (a CANDIDATE, never a directive)."
  [energy-design sources]
  (draft
   (str "【wellbecoming エネルギー流の設計 / CANDIDATE】同じ努力エネルギーを零和の散逸チャネルから"
        "wellbecoming を生むチャネルへ再配線する設計案: wellbecoming " (:current-wellbecoming energy-design)
        " → " (:designed-wellbecoming energy-design) " (gain " (:wellbecoming-gain energy-design)
        ")。構造的な提案であって個人への指令ではない(G11)。")
   sources))

(defn build-live
  "Live broadcast is GATED — this raises. Live posting requires a member CACAO leash
  (ADR-2606111400) + Council Lv6+ (G13); the server never holds a signing key
  (ADR-2605231525). shinogi itself never autonomously broadcasts (G4 by absence)."
  [& _]
  (throw (ex-info "live broadcast is gated: member-CACAO-leash + Council Lv6+ + member/actor signature (G13/ADR-2606111400). shinogi holds no key and never auto-broadcasts (G4)." {:gate :live})))

#?(:clj
   (defn -main [& _]
     (let [post (draft-energy-flow-post
                 {:current-wellbecoming 0.044 :designed-wellbecoming 0.421 :wellbecoming-gain 0.377}
                 ["教育部 高校招生统一考试制度" "MEXT 大学入学共通テスト"])]
       (println "DRY-RUN post draft:")
       (println (:post/text post))
       (println (str "status=" (:post/status post)
                     " server-held-key=" (:post/server-held-key post)
                     " sources=" (count (:post/sources post))))
       (println "live? attempting build-live (should refuse):")
       (try (build-live) (catch clojure.lang.ExceptionInfo e (println " refused:" (ex-message e)))))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
