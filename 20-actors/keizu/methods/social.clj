#!/usr/bin/env bb
;; Working Clojure port of methods/social.py.
(ns keizu.methods.social
  "social.clj — 系図 (keizu) DRY-RUN social-post projection. ADR-2606066001.

  Projects an AGGREGATE concentration finding into a social post (app.bsky.feed.post-shaped),
  enforcing the post invariants in their third home (mirror of the ontology :db/allowed +
  networkPost.edn :const):

    G5 — every post opens with the mirror / accountability-map disclaimer (isMirror=true),
         never speaks AS a government, never names a private individual.
    G2 — nonAdjudicatingNotice=true; the post narrates ties/shares, never a verdict.
    G7 — serverHeldKey=false; the member signs, the server never does (ADR-2605231525).
    G8 — status is 'dry-run' only at R0; 'published' is unrepresentable. A live post needs
         Council Lv6+ + operator + a member signature (build-live raises here).
    G3 — the post carries the same ≥2 public-source citations as the finding.

  Reuses weave.cljc public fn:
    w/source-denied — returns the offending denied token or \"\" if clean (§2(e)/N5 gate)

  Stdlib only. Deterministic.
  Run:  bb --classpath 20-actors 20-actors/keizu/methods/social.clj"
  (:require [keizu.methods.weave :as w]
            [clojure.string :as str]))

(def DISCLAIMER
  "【観測ミラー / accountability map — NOT the government, non-adjudicating】 公開情報から編んだ関係グラフの集計です。特定個人を名指しせず、不正の断定もしません。")

(defn- py-str-list
  "Render a Clojure vector as Python's str(list) output — single-quoted items, comma-space
  separated — so a body interpolating `finding['organs']` is byte-identical to social.py."
  [v]
  (str "[" (str/join ", " (map #(str "'" % "'") v)) "]"))

(defn- enough-sources
  "G3 + Rider §2(e)/N5 — filter to non-blank sources, require ≥2, reject commercial gov-intel terminals."
  [sources]
  (let [s (vec (filter #(seq (str/trim (str %))) (or sources [])))]
    (when (< (count s) 2)
      (throw (ex-info "G3: a post needs ≥2 public-source citations" {})))
    (let [d (w/source-denied s)]
      (when (seq d)
        (throw (ex-info (str "Rider §2(e)/N5: source " (pr-str d)
                             " is a commercial gov-intel terminal — a post may not cite it")
                        {}))))
    s))

(defn- post-
  "Assemble a networkPost record with every invariant pinned. status is ALWAYS dry-run."
  [subject body sources author]
  {":post/subject"                subject
   ":post/body"                   body
   ":post/status"                 ":dry-run"    ;; G8 — published is unrepresentable
   ":post/is-mirror"              true          ;; G5
   ":post/non-adjudicating-notice" true         ;; G2
   ":post/server-held-key"        false         ;; G7 / no-server-key
   ":post/author"                 author        ;; member DID (required only for a gated live post)
   ":post/sources"                sources})     ;; G3

(defn draft-committee-post
  "A dry-run post about a committee's cross-organ concentration (aggregate, no person)."
  ([finding sources] (draft-committee-post finding sources ""))
  ([finding sources author]
   (let [srcs (enough-sources sources)
         body (str DISCLAIMER "\n\n"
                   (get finding "label") ": " (get finding "member_count") " seats drawn from "
                   (get finding "distinct_organs") " organ(s) " (py-str-list (get finding "organs")) ". "
                   "出典 " (count srcs) " 件。")]
     (post- (str "committee:" (get finding "committee")) body srcs author))))

(defn draft-money-post
  "A dry-run post about per-payee money concentration (HHI), aggregate + factual."
  ([money-concentration sources] (draft-money-post money-concentration sources ""))
  ([money-concentration sources author]
   (let [srcs   (enough-sources sources)
         shares (get money-concentration "shares")
         top    (if (seq shares) (first shares) ["(none)" 0.0])
         top-name  (first top)
         top-share (double (second top))
         body (str DISCLAIMER "\n\n"
                   "公開された資金フローの集中度 HHI=" (get money-concentration "hhi") "。"
                   "最大受領 " top-name " = " (format "%.1f" (* top-share 100)) "%。"
                   "出典 " (count srcs) " 件。")]
     (post- "money:concentration" body srcs author))))

(defn build-live
  "G8 — live posting is outward-gated. Refuses by construction at R0."
  [& _args]
  (throw (ex-info
          (str "keizu R0: live social posting is Council Lv6+ + operator + member-signature gated (G8). "
               "Only dry-run posts are producible offline.")
          {})))

(defn -main [& _argv]
  (println "# 系図 (keizu) — DRY-RUN social post demo")
  (println "  (run social.py for a live seed demo; this stub prints the DISCLAIMER)")
  (println DISCLAIMER))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
