(ns tate.methods.coverage-report
  "tate 盾 — honest jurisdiction-coverage report (G10, ADR-2606112400).
  1:1 Clojure port of `methods/coverage_report.py`.

  Makes the gap measurable: per-jurisdiction clause-pattern + procedure counts, the
  covered/uncovered ratio against the ~193 UN member states, and a NAMED gap list that
  doubles as the ingest worklist for the next wave.

  House style: data maps stay string-keyed; ':…' keyword strings stay strings; pure fns;
  file I/O only behind #?(:clj …). The Python __main__ demo printer is omitted.

  Float parity: Python `{x:.2%}` (x*100 .2f then '%') is mirrored HALF_EVEN over the exact
  double via BigDecimal, and `round(x, 4)` HALF_EVEN."
  (:require [clojure.string :as str]
            [tate.methods.terms-scan :as ts]
            [tate.methods.respond-plan :as rp]))

(def UN-MEMBER-STATES 193)

(def JURIS-WORKLIST
  [":it" ":es" ":nl" ":kr" ":fr" ":cn" ":tw" ":in"
   ":br" ":au" ":ca" ":sg" ":mx"
   ":dk" ":fi" ":ie" ":be" ":ch" ":no"
   ":ar" ":cl"])

(def STRUCTURAL-GAPS
  [":eu は越境 instruments のみ (加盟国国内法は各国エントリで個別収載)"
   "刑事手続は全管轄でスコープ外 (N6 — 即時弁護士照会のみ)"])

(def US-STATES-TOTAL 50)
(def SPECIALTY-TRACKS-PLANNED [])

;; ── float parity ────────────────────────────────────────────────────────────
(defn- round-n
  "Python round(x, n) — HALF_EVEN over the exact double; returns a double."
  [x n]
  (-> (java.math.BigDecimal. (double x))
      (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
      (.doubleValue)))

(defn- fmt-pct2
  "Python `{x:.2%}` — x*100 then .2f (HALF_EVEN over the exact double), then '%'."
  [x]
  (str (-> (java.math.BigDecimal. (* 100.0 (double x)))
           (.setScale 2 java.math.RoundingMode/HALF_EVEN)
           (.toPlainString))
       "%"))

(defn- count-by
  "defaultdict(int) over (key-fn x) → string-keyed sorted-map."
  [coll key-fn]
  (reduce (fn [m x] (update m (key-fn x) (fnil inc 0))) {} coll))

(defn coverage []
  (let [patterns (ts/load-patterns)
          procs (rp/load-procs)
          juris (rp/load-jurisdictions)
          pat-by-j (count-by patterns #(get % ":clause/jurisdiction" ":jp"))
          proc-by-j (count-by procs #(get % ":proc/jurisdiction" ":jp"))
          covered (sort (keys juris))
          remaining (filterv #(not (contains? juris %)) JURIS-WORKLIST)
          states (rp/load-us-states)
          us-state-gap (if (>= (count states) US-STATES-TOTAL)
                         (str ":us 州レベル: 全" US-STATES-TOTAL "州収載 — 次の課題は改正追跡 "
                              "(:verify-current-law) と DC/準州")
                         (str ":us 州レベル: " (count states) "/" US-STATES-TOTAL " 州を収載 — "
                              "残り" (- US-STATES-TOTAL (count states)) "州は『州不明』honest degrade"))
          tracks (count-by procs #(get % ":proc/track" ":civil"))
          ;; matrix: juris → track → count
          matrix (reduce (fn [m p]
                           (update-in m [(get p ":proc/jurisdiction" ":jp")
                                         (get p ":proc/track" ":civil")]
                                      (fnil inc 0)))
                         {} procs)
          track-counts (str ":labor " (get tracks ":labor" 0) " / :housing " (get tracks ":housing" 0)
                            " / :enforcement " (get tracks ":enforcement" 0)
                            " / :insolvency " (get tracks ":insolvency" 0)
                            " / :family " (get tracks ":family" 0))
          track-gap (if (seq SPECIALTY-TRACKS-PLANNED)
                      (str "専門トラック: " track-counts " 件収載 — "
                           (str/join " / " SPECIALTY-TRACKS-PLANNED) " 未収載")
                      (str "専門トラック: " track-counts " 件 — 計画トラックは全て開削済み; "
                           "次の深化は各トラックの管轄横展開 (多くは jp/us/de の3管轄のみ)"))
          civil-only (sort (for [[j ts*] matrix
                                 :when (and (= (set (keys ts*)) #{":civil"}) (not= j ":eu"))]
                             j))
          civil-only-gap (if (seq civil-only)
                           (str "専門トラック未開削の管轄 (civil のみ): " (str/join " " civil-only))
                           "全管轄に専門トラックあり (:eu は越境 instruments のみで対象外)")
          named-gaps (-> (mapv #(str % " — 未収載 (worklist)") remaining)
                         (conj us-state-gap track-gap civil-only-gap)
                         (into STRUCTURAL-GAPS))]
      {"us_states_covered" (count states)
       "us_states_total" US-STATES-TOTAL
       "procedure_tracks" (into (sorted-map) tracks)
       "track_matrix" (into (sorted-map)
                            (map (fn [[j ts*]] [j (into (sorted-map) ts*)]) matrix))
       "civil_only_jurisdictions" (vec civil-only)
       "_procs" procs
       "critical_deadlines" (vec (for [p procs
                                       dl (get p ":proc/deadline-rules" [])
                                       :when (get dl ":dl/critical")]
                                   {"proc" (get p ":proc/id")
                                    "juris" (get p ":proc/jurisdiction" ":jp")
                                    "label" (get dl ":dl/label")
                                    "anchor" (get dl ":dl/anchor")}))
       "jurisdictions" (vec covered)
       "patterns_by_jurisdiction" (into (sorted-map) pat-by-j)
       "procedures_by_jurisdiction" (into (sorted-map) proc-by-j)
       "covered_count" (count covered)
       "un_member_states" UN-MEMBER-STATES
       "coverage_ratio" (round-n (/ (count covered) (double UN-MEMBER-STATES)) 4)
       "worklist_remaining" remaining
       "named_gaps" named-gaps}))

(defn report [cov]
  (let [all-tracks [":civil" ":labor" ":housing" ":enforcement" ":insolvency" ":family"]
        L (transient
           ["# tate 盾 — jurisdiction coverage (honest — G10)"
            ""
            (str "- covered: " (get cov "covered_count") " legal systems "
                 "(" (str/join ", " (get cov "jurisdictions")) ") of ~" (get cov "un_member_states")
                 " UN states → ratio ≈ " (fmt-pct2 (get cov "coverage_ratio"))
                 " (低いのは仕様 — 推測より空白)")
            (str "- :us 州レベル: " (get cov "us_states_covered") "/" (get cov "us_states_total")
                 " 州 (州不明の通知は honest degrade)")
            ""
            "| juris | clause patterns | procedures |"
            "|---|---|---|"])]
    (doseq [j (get cov "jurisdictions")]
      (conj! L (str "| " j " | " (get-in cov ["patterns_by_jurisdiction" j] 0)
                    " | " (get-in cov ["procedures_by_jurisdiction" j] 0) " |")))
    (conj! L "")
    (conj! L "## Track × jurisdiction matrix (横展開ギャップの可視化)")
    (conj! L "")
    (conj! L (str "| juris | " (str/join " | " (map #(subs % 1) all-tracks)) " |"))
    (conj! L (str "|---|" (apply str (repeat (count all-tracks) "---|"))))
    (doseq [[j ts*] (get cov "track_matrix")]
      (conj! L (str "| " j " | "
                    (str/join " | " (map #(let [v (get ts* %)] (if v (str v) "·")) all-tracks))
                    " |")))
    (let [n-juris (max 1 (count (get cov "track_matrix")))
          depth (str/join " · "
                          (map (fn [t]
                                 (str (subs t 1) " "
                                      (count (filter #(pos? (get % t 0))
                                                     (vals (get cov "track_matrix"))))
                                      "/" n-juris))
                               [":labor" ":housing" ":enforcement" ":insolvency" ":family"]))]
      (conj! L "")
      (conj! L (str "track depth (管轄横展開率): " depth)))
    (let [n-protective (count (for [p (get cov "_procs" [])
                                    o (get p ":proc/options" [])
                                    :when (= (get o ":opt/protective") true)]
                                o))]
      (conj! L (str "protective options (member を守る一手): " n-protective)))
    (conj! L "")
    (conj! L "## Critical deadlines (徒過で権利が消える期限 — 全管轄一覧)")
    (conj! L "")
    (doseq [cd (get cov "critical_deadlines")]
      (conj! L (str "- [" (get cd "juris") "] " (get cd "proc") " — " (get cd "label")
                    " (" (get cd "anchor") ")")))
    (conj! L "")
    (conj! L "## Named gaps (next-wave worklist)")
    (doseq [g (get cov "named_gaps")]
      (conj! L (str "- " g)))
    (conj! L "")
    (conj! L (str "未カバー管轄の通知は :unknown-jurisdiction に honest degrade し、"
                  "現地法を推測せず証拠保全 + 専門家照会のみを案内する (respond_plan G10)。"))
    (str (str/join "\n" (persistent! L)) "\n")))
