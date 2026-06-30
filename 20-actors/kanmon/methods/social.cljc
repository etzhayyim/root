#!/usr/bin/env bb
;; kanmon 関門 — DRY-RUN self-publication projection (AT-proto social membrane).
(ns kanmon.methods.social
  "social.cljc — kanmon 関門 self-publication projection (ADR-2606272355 seed +
  ADR-2606281500 seed-and-grow doctrine).

  Projects kanmon's HISTORY (its 入試 OPENING map) and its system-dynamics LEVERAGE digest
  into app.bsky.feed.post-shaped records. The seed-and-grow doctrine lets the actor PUBLISH
  AUTONOMOUSLY by default — but the SEED (rails) is NOT lifted, and each is enforced here:

    G-mirror        — every post opens with the OPENING-map disclaimer (isMirror=true), never
                      ranks/scores a student, never a 偏差値/序列/合否予測 (nonAdjudicating=true).
    no-server-key   — serverHeldKey=false; the actor self-signs with its OWN did:key in its
                      mesh runtime under a revocable member CACAO leash; the server never signs.
    content-scan    — every post body passes a Rider §2 catastrophe-veto scan BEFORE emit
                      (injectable; default = a minimal local guard; production wires
                      etzhayyim-organism.sensors.charter-rider/scan). A hit makes it non-emittable.
    ≥2 sources      — a post carries ≥2 public ministry/test-body primary citations.
    no person       — aggregate exam-SYSTEM scale only (kanmon has no person in its model).
    R0-gate         — status is dry-run; a live broadcast is the operator/mesh deploy step
                      (the actor self-signs there; build-live raises here).

  Pure fns; deterministic; string-keyed post records (house style). Stdlib only."
  (:require [clojure.string :as str]))

(def DISCLAIMER
  (str "【観測ミラー / 入試 OPENING map — NOT a ranking, NOT exam-prep, 非断定】 "
       "公開された入試制度の構造から編んだ開放のための地図です。受験生を採点・序列化・合否予測しません。"))

;; ── content-scan rail (Rider §2 catastrophe-veto + kanmon negative space) ────
;; Default minimal guard. Production injects etzhayyim-organism.sensors.charter-rider/scan
;; (returns {:ok bool :hits [...]}). kanmon's own negative space (no ranking/prediction/person)
;; is added on top — a post that ranks students or predicts pass/fail is non-emittable.
(def ^:private forbidden-substrings
  ["偏差値" "序列" "ランキング" "合否予測" "合格判定" "落ちる確率" "受かる確率"
   "rank students" "pass-prediction" "this student" "個人を特定"])

(defn kanmon-content-scan
  "Minimal local content guard. Returns {:ok bool :hits [...]}."
  [text]
  (let [t (str text)
        hits (vec (filter #(str/includes? t %) forbidden-substrings))]
    {:ok (empty? hits) :hits hits}))

(defn scan-clean!
  "Run the (injectable) content scan; throw if it is not clean. Returns the text."
  ([text] (scan-clean! text kanmon-content-scan))
  ([text scan-fn]
   (let [r (scan-fn text)]
     (when-not (:ok r)
       (throw (ex-info (str "content-scan: post is non-emittable (Rider §2 / kanmon negative space): "
                            (pr-str (:hits r)))
                       {:hits (:hits r)})))
     text)))

(defn- enough-sources
  "≥2 non-blank public primary-source citations (ministry/test-body disclosures)."
  [sources]
  (let [s (vec (filter #(seq (str/trim (str %))) (or sources [])))]
    (when (< (count s) 2)
      (throw (ex-info "sources: a post needs ≥2 public ministry/test-body primary citations" {})))
    s))

(defn- post
  "Assemble a post record with every invariant pinned. status is ALWAYS dry-run."
  [subject body sources author]
  {":post/subject" subject
   ":post/body" body
   ":post/status" ":dry-run"             ;; R0-gate — published is unrepresentable here
   ":post/is-mirror" true                ;; G-mirror
   ":post/non-adjudicating-notice" true  ;; G-mirror
   ":post/server-held-key" false         ;; no-server-key (ADR-2605231525)
   ":post/author" author                 ;; member/actor did:key (for the gated live post)
   ":post/sources" sources})

(defn draft-opening-post
  "HISTORY post — one exam's barrier-load + the OPENING it routes to. Narrates STRUCTURE,
   never a person; passes the content scan before emit."
  ([exam-row sources] (draft-opening-post exam-row sources "" kanmon-content-scan))
  ([exam-row sources author] (draft-opening-post exam-row sources author kanmon-content-scan))
  ([exam-row sources author scan-fn]
   (let [srcs (enough-sources sources)
         {:keys [exam route barrier-load]} exam-row
         content (str "【関門】" (:name exam) " [" (name (:country exam)) "] "
                      "barrier-load=" barrier-load " → OPENING: " (name route) "。"
                      "（ゲートの構造の観測。受験生の評価ではありません。）"
                      " 出典 " (count srcs) " 件。")]
     (scan-clean! content scan-fn)   ;; scan the narration, not the disclaimer
     (post (str "opening:" (:id exam)) (str DISCLAIMER "\n\n" content) srcs author))))

(defn draft-leverage-post
  "HISTORY post — the system-dynamics LEVERAGE digest (system regime + deepest opening).
   `analysis` = kanmon.methods.dynamics/analyze output."
  ([analysis sources] (draft-leverage-post analysis sources "" kanmon-content-scan))
  ([analysis sources author] (draft-leverage-post analysis sources author kanmon-content-scan))
  ([analysis sources author scan-fn]
   (let [srcs (enough-sources sources)
         hd (get analysis "headline")
         top (:top-leverage hd)
         content (str "【因果】入試システムの読み: " (name (:system-regime hd))
                      "（支配要因 " (name (:dominant-stock hd))
                      "、vicious loops " (:vicious-loops hd) "）。"
                      "最深レバレッジ（仮説・指示ではない）= " (name (:route top))
                      " / Meadows M" (:meadows top) " — " (:label top) "。"
                      " 出典 " (count srcs) " 件。")]
     (scan-clean! content scan-fn)   ;; scan the narration, not the disclaimer
     (post "leverage:exam-gate-dynamics" (str DISCLAIMER "\n\n" content) srcs author))))

(defn build-live
  "Live posting is the seed-and-grow GROWTH step (the actor self-signs with its own did:key
   in its kotoba-mesh runtime under a revocable member CACAO leash, ADR-2606281500). It is
   NOT producible offline with a server key — this raises by construction at R0."
  [& _args]
  (throw (ex-info (str "kanmon R0: a live broadcast is the seed-and-grow GROWTH step — the actor "
                       "self-signs with its OWN did:key in its mesh runtime under a revocable member "
                       "CACAO leash (ADR-2606281500). It is never produced here with a server key.") {})))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (println "kanmon.social — dry-run projection; require + call draft-* (no live posting here)")))
