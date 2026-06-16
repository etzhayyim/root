(ns tate.methods.respond-plan
  "tate 盾 — legal-procedure response planner (個人としての対応支援; dry-run only).
  1:1 Clojure port of `methods/respond_plan.py` (ADR-2606112301 + worldwide 2606112400).

  Classifies a notice the member RECEIVED against the jurisdiction-keyed procedure
  registry and builds a response plan: DISCLOSED deadline rules, response options, a
  self-submit checklist, and referral triggers.

  CONSTITUTIONAL (read before any change):
    G3 — UPL: representation is structurally unrepresentable (make-option raises on
      :representation), in EVERY jurisdiction. The MEMBER decides + submits THEMSELVES.
    G4 — deadline honesty: tate NEVER computes a calendar date; every deadline is the
      DISCLOSED rule text + statutory anchor + verify-service-date=true.
    G6 — fake-notice (架空請求) guard via :proc/genuine-channels; court vocabulary on any
      other channel is :suspected-fake (refuse contact-sender, route to fake-help).
    G7 — referral-forward for high-stakes shapes.
    G10 — jurisdiction honesty: procedures never cross jurisdictions; an uncovered
      jurisdiction degrades to :unknown-jurisdiction (tate never guesses foreign law).

  House style: data maps stay string-keyed; ':…' keyword strings stay strings; pure fns;
  file I/O only behind #?(:clj …). The Python __main__ demo printer is omitted."
  (:require [clojure.string :as str]
            [tate.methods.terms-scan :as ts]))

;; fake-guard trip-wires (G6). The vocabulary is DERIVED — every procedure's trigger
;; keywords are automatically trip-wires, plus a small curated set of generic scam words.
(def CURATED-TRIPWIRES
  ["法院" "법원" "강제집행" "lawsuit" "差押" "garnishment"
   "Pfändung" "Insolvenz" "Betreibung" "assignation" "juzgado"])

(defn court-vocabulary
  "Curated generics + the union of ALL procedure trigger keywords (derived, G6)."
  [procs]
  (into (vec CURATED-TRIPWIRES)
        (mapcat #(get % ":proc/trigger-keywords" []) procs)))

(def GENERIC-REFERRALS
  ["local bar association / legal aid" "認定司法書士 (JPのみ・簡裁140万円以下)"])

(def PROC-REFERRAL-ALWAYS #{"proc:sojou" "proc:us-summons"})

#?(:clj
   (defn load-procs
     ([] (load-procs (clojure.java.io/file ts/HERE "data" "procedure-registry.edn")))
     ([path] (filterv #(contains? % ":proc/id") (ts/read-edn (slurp (str path)))))))

#?(:clj
   (defn load-jurisdictions
     ([] (load-jurisdictions (clojure.java.io/file ts/HERE "data" "jurisdictions.edn")))
     ([path]
      (reduce (fn [m j] (if (contains? j ":juris/id") (assoc m (get j ":juris/id") j) m))
              {} (ts/read-edn (slurp (str path)))))))

#?(:clj
   (defn load-us-states
     ([] (load-us-states (clojure.java.io/file ts/HERE "data" "us-states.edn")))
     ([path]
      (reduce (fn [m s] (if (contains? s ":state/id") (assoc m (get s ":state/id") s) m))
              {} (ts/read-edn (slurp (str path)))))))

(defn make-option
  "The only option constructor. Representation is unrepresentable (G3) — globally."
  [opt]
  (when (= (get opt ":opt/kind") ":representation")
    (throw (ex-info (str "G3/UPL: representation is unrepresentable in tate "
                         "(弁護士法72条 / state UPL / LSA 2007 / RDG)") {})))
  {"id" (get opt ":opt/id") "kind" (get opt ":opt/kind") "label" (get opt ":opt/label")
   "mode" "dry-run" "submitted_by" "member"})

(defn- to-double [v] (cond (nil? v) nil (number? v) (double v)
                           :else (try (Double/parseDouble (str v)) (catch Exception _ nil))))

(defn- claim
  "float(notice.get(:notice/claim-jpy) or notice.get(:notice/claim-amount) or 0)."
  [notice]
  (double (or (to-double (get notice ":notice/claim-jpy"))
              (to-double (get notice ":notice/claim-amount"))
              0)))

(defn classify
  "(proc, status) — :genuine | :suspected-fake | :unknown | :unknown-jurisdiction."
  ([notice procs] (classify notice procs (load-jurisdictions)))
  ([notice procs jurisdictions]
   (let [juris (get notice ":notice/jurisdiction" ":jp")
         text (str/lower-case (get notice ":notice/text" ""))
         channel (get notice ":notice/channel")]
     (if-not (contains? jurisdictions juris)
       [nil ":unknown-jurisdiction"]
       (let [matched (first (filter
                             (fn [p]
                               (and (= (get p ":proc/jurisdiction" ":jp") juris)
                                    (some #(str/includes? text (str/lower-case %))
                                          (get p ":proc/trigger-keywords"))))
                             procs))]
         (if (nil? matched)
           (if (and (some #(str/includes? text (str/lower-case %)) (court-vocabulary procs))
                    (contains? #{":sms" ":email" ":mail"} channel))
             [nil ":suspected-fake"]
             [nil ":unknown"])
           (let [genuine (get matched ":proc/genuine-channels" [])]
             (cond
               (and (contains? #{":sms" ":email"} channel)
                    (not (some #{channel} genuine)))
               [matched ":suspected-fake"]

               (let [formal-required (some #(not= % ":mail") genuine)]
                 (and formal-required (not (some #{channel} genuine))))
               [matched ":suspected-fake"]

               :else [matched ":genuine"]))))))))

(defn- int-comma
  "Python f-string `{n:,}` — group integer with thousands commas."
  [n]
  (let [s (str (long n))
        [sign digits] (if (str/starts-with? s "-") ["-" (subs s 1)] ["" s])
        grouped (->> (reverse digits)
                     (partition-all 3)
                     (map (comp str/join reverse))
                     reverse
                     (str/join ","))]
    (str sign grouped)))

(defn build-plan
  ([notice procs] (build-plan notice procs (load-jurisdictions)))
  ([notice procs jurisdictions]
   (let [juris-id (get notice ":notice/jurisdiction" ":jp")
         juris (get jurisdictions juris-id {})
         [proc status] (classify notice procs jurisdictions)
         plan {"notice" (get notice ":notice/id")
               "notice_label" (get notice ":notice/label" (get notice ":notice/id"))
               "jurisdiction" juris-id
               "channel" (get notice ":notice/channel")
               "proc" (when proc (get proc ":proc/id"))
               "status" status
               "deadlines" [] "options" [] "steps" [] "referrals" []
               "mode" "dry-run"}]
     (cond
       (= status ":suspected-fake")
       (assoc plan
              "steps"
              [{"verb" "do-not-contact-sender"
                "detail" "記載の電話番号・URL・口座に一切接触しない (never call/click/pay the sender)"
                "mode" "dry-run"}
               {"verb" "preserve-evidence"
                "detail" "現物/スクリーンショットを保全 (日時・差出経路)"
                "mode" "dry-run"}
               {"verb" "verify-with-court"
                "detail" (str "実在確認は記載先ではなく公的窓口の公開番号で行う "
                              "(genuine service: " (get juris ":juris/service-note" "—") ")")
                "mode" "dry-run"}]
              "referrals"
              (vec (get juris ":juris/fake-help"
                        ["tasuke 助 (サイバー犯罪被害支援)" "local police"])))

       (= status ":unknown-jurisdiction")
       (assoc plan
              "steps"
              [{"verb" "declare-uncovered"
                "detail" (str "管轄 " juris-id " は tate 未カバー "
                              "(coverage_report.py 参照) — 現地法を推測しない")
                "mode" "dry-run"}
               {"verb" "preserve-evidence"
                "detail" "文書全文・封筒・送達方法を記録" "mode" "dry-run"}]
              "referrals" (vec GENERIC-REFERRALS))

       (= status ":unknown")
       (assoc plan
              "steps" [{"verb" "collect-more"
                        "detail" "文書全文・封筒・送達方法を記録して再分類" "mode" "dry-run"}]
              "referrals" (vec (get juris ":juris/referrals" GENERIC-REFERRALS)))

       :else
       (let [deadlines0 (mapv (fn [dl]
                                {"label" (get dl ":dl/label") "rule" (get dl ":dl/rule")
                                 "anchor" (get dl ":dl/anchor")
                                 "critical" (boolean (get dl ":dl/critical"))
                                 "verify_service_date" (boolean (get dl ":dl/verify-service-date"))})
                              (get proc ":proc/deadline-rules" []))
             ;; plan["deadlines"].sort(key=lambda d: not d["critical"]) — stable;
             ;; critical (True → not=False=0) sorts before non-critical
             deadlines1 (vec (sort-by #(if (get % "critical") 0 1) deadlines0))
             deadlines2 (if (= juris-id ":us")
                          (let [state (get (load-us-states) (get notice ":notice/us-state"))]
                            (if state
                              (conj deadlines1
                                    {"label" (str "州規則 (" (get state ":state/label") ")")
                                     "rule" (str (get state ":state/answer-rule")
                                                 " · small claims 上限 $"
                                                 (int-comma (get state ":state/small-claims-usd")))
                                     "anchor" (get state ":state/answer-anchor")
                                     "critical" false "verify_service_date" true})
                              (conj deadlines1
                                    {"label" "州規則 (州不明)"
                                     "rule" (str "州が特定できないため州規則は提示しない — サモンズ記載の期限と"
                                                 "当該州の rules of civil procedure を必ず確認 (州差が本体)")
                                     "anchor" "—" "critical" false "verify_service_date" true})))
                          deadlines1)
             options (mapv make-option (get proc ":proc/options" []))
             steps [{"verb" "verify-service-date" "detail" "送達/受領日を自分で確認 (期限の起算点)" "mode" "dry-run"}
                    {"verb" "draft-response" "detail" "選んだ選択肢の書面雛形を作成 (member が記入・確定)" "mode" "dry-run"}
                    {"verb" "self-submit" "detail" "member 本人が提出 (郵送/窓口/オンライン)" "mode" "dry-run"}
                    {"verb" "record-to-ledger" "detail" "対応と期限を kotoba Datom log に記録 (G8)" "mode" "dry-run"}]
             referrals0 (vec (get proc ":proc/refer-when" []))
             refer-over (double (or (to-double (get juris ":juris/refer-over-amount")) 0))
             cl (claim notice)
             claim-cur (or (get notice ":notice/claim-currency")
                           (when (contains? notice ":notice/claim-jpy") "JPY"))
             juris-cur (get juris ":juris/refer-over-currency")
             currency-mismatch (boolean (and (> cl 0) claim-cur juris-cur (not= claim-cur juris-cur)))
             over-line (boolean (and (not= refer-over 0.0) (not currency-mismatch) (> cl refer-over)))
             referrals (if (or over-line currency-mismatch
                               (contains? PROC-REFERRAL-ALWAYS (get proc ":proc/id")))
                         (let [r1 (if currency-mismatch
                                    (conj referrals0
                                          (str "請求が外貨建て (" claim-cur ") — 金額比較不能のため保守的に専門家照会"))
                                    referrals0)]
                           (into r1 (get juris ":juris/referrals" GENERIC-REFERRALS)))
                         referrals0)]
         (assoc plan
                "deadlines" deadlines2
                "options" options
                "steps" steps
                "referrals" referrals))))))

(defn plans
  [notices procs]
  (let [jurisdictions (load-jurisdictions)]
    (mapv #(build-plan % procs jurisdictions) notices)))

(defn report
  [ps]
  (let [L (transient
           ["# tate 盾 — response plans (dry-run; member self-submit — G3 UPL, all jurisdictions)"
            ""])]
    (doseq [p ps]
      (conj! L (str "## " (get p "notice_label") " [" (get p "jurisdiction") "] — " (get p "status")
                    (if (get p "proc") (str " (" (get p "proc") ")") "")))
      (doseq [d (get p "deadlines")]
        (let [mark (if (get d "critical") "⚠ " "")]
          (conj! L (str "- " mark "期限ルール [" (get d "label") "]: " (get d "rule")
                        " (" (get d "anchor") ") — 送達日は自分で確認"))))
      (doseq [o (get p "options")]
        (conj! L (str "- 選択肢: " (get o "label"))))
      (doseq [[i s] (map-indexed (fn [i s] [(inc i) s]) (get p "steps"))]
        (conj! L (str i ". [" (get s "verb") "] " (get s "detail"))))
      (when (seq (get p "referrals"))
        (conj! L (str "- 照会先: " (str/join ", " (get p "referrals")))))
      (conj! L ""))
    (str (str/join "\n" (persistent! L)) "\n")))
