#!/usr/bin/env bb
;; shinogi 鎬 — exam-competition involution system-dynamics read-off (clj-native, pure stdlib).
(ns shinogi.methods.analyze
  "shinogi 鎬 — the ANALYSIS-ONLY system-dynamics read-off over the exam-competition
  involution drivers (ADR-2606291200, on the junkan 循環 method ADR-2605290927).

  Each driver feeds a pressure STOCK (positional-scarcity / effort-inflation /
  credential-signaling / wellbeing-erosion / family-capture / failure-penalty) with
  a polarity (:intensify / :relieve / :ambiguous) and a disclosed-hypothesis
  magnitude. shinogi reads off:

    1. per-driver signed contribution = sign(polarity) · magnitude · confidence
    2. per-stock net pressure (mean of contributions) → REGIME
         :vicious (net intensifying = 悪循環) / :virtuous (net relieving = 好循環)
         / :neutral / :transitioning
    3. per-LOOP regime (from the JOINT pressure of its member stocks; HYPOTHESIS, G5)
    4. the FAILURE CYCLE read-off (受験失敗 → stigma → wellbeing erosion → lost
       opportunity) + its relief gap, routed toward RELIEF (kokoro/shiori), G7
    5. Meadows LEVERAGE candidates — the deepest-leverage RELIEVING drivers to
       amplify, and the most tractable INTENSIFYING drivers where the spiral could
       ease — CANDIDATES WITH UNCERTAINTY, never directives (G11 prescription? false)
    6. coverage (jurisdictions / kinds / stocks / sourcing) + an ingest worklist.

  DISCIPLINE (the analysis-only spine):
    G4  this namespace has NO outward channel — it returns data / writes a local
        ledger; there is no post/mention/email/tx path (enforced by absence).
    G5  every loop/regime is a HYPOTHESIS (`hypothesis? true`); correlation/sign
        only, never proven causation.
    G6  aggregate-only — drivers + institutional enactors; no private individual,
        no per-student score/record.
    G7  sober, wellbecoming-positive framing; the failure cycle is routed toward
        RELIEF, never doom/despair-amplified, never a ranking-to-shame.
    G8  a relief/leverage MAP — never a student/school/country shame-ranking.
    G11 leverage points are candidates (`prescription? false`); no directive issued."
  (:require [clojure.string :as str]))

;; ── stock catalog (display order + labels) ───────────────────────────────────
(def stock-order
  [:positional-scarcity :effort-inflation :credential-signaling
   :wellbeing-erosion :family-capture :failure-penalty])

(def stock-label
  {:positional-scarcity  "A 選抜の希少性 (positional scarcity)"
   :effort-inflation     "B 努力の軍拡 (effort inflation = 内卷)"
   :credential-signaling "C 学歴シグナル依存 (credential signaling)"
   :wellbeing-erosion    "D 心身ウェルビーイングの侵食 (wellbeing erosion)"
   :family-capture       "E 家計資源の捕獲 (family capture)"
   :failure-penalty      "F 失敗ペナルティ (failure penalty)"})

;; ── canonical structural loops (HYPOTHESES; mirror ontology :loops) ──────────
;; :stocks = the member stocks the loop's edges connect; a loop's regime is read
;; off the JOINT pressure of ALL its member stocks (loop "drive").
(def loops
  [{:id "R-involution-arms-race"  :type :reinforcing :dominant :effort-inflation
    :stocks [:positional-scarcity :effort-inflation]}
   {:id "R-credential-inflation"  :type :reinforcing :dominant :credential-signaling
    :stocks [:credential-signaling :effort-inflation]}
   {:id "R-family-capture"        :type :reinforcing :dominant :family-capture
    :stocks [:family-capture :effort-inflation]}
   {:id "R-failure-despair"       :type :reinforcing :dominant :failure-penalty
    :stocks [:failure-penalty :wellbeing-erosion]}
   {:id "B-alternative-pathways"  :type :balancing   :dominant :positional-scarcity
    :stocks [:positional-scarcity]}
   {:id "B-wellbeing-protection"  :type :balancing   :dominant :wellbeing-erosion
    :stocks [:wellbeing-erosion]}])

;; ── pure read-off ────────────────────────────────────────────────────────────
(defn- round3 [x] (/ (Math/round (* (double x) 1000.0)) 1000.0))

(defn polarity-sign [p]
  (case p :intensify 1.0 :relieve -1.0 :ambiguous 0.0 0.0))

(defn contribution
  "Signed contribution of a driver to its stock ∈ [-1,1]:
   +ve = intensifies the involution/pressure, -ve = relieves it (HYPOTHESIS, G5)."
  [d]
  (* (polarity-sign (:polarity d))
     (double (or (:magnitude d) 0))
     (double (or (:confidence d) 1.0))))

(defn regime-of
  "Read a regime off a net pressure + spread. `pos`/`neg` = magnitudes of
  intensifying vs relieving present. Transitioning = both forces strong (contested)."
  [net pos neg]
  (cond
    (and (>= pos 0.3) (>= neg 0.3) (< (Math/abs (double net)) 0.2)) :transitioning
    (>  net 0.15) :vicious
    (< net -0.15) :virtuous
    :else :neutral))

(defn stock-pressure
  "For one stock: net pressure (mean signed contribution), intensify/relieve force
  totals, driver count, and the read-off regime. HYPOTHESIS (G5)."
  [drivers]
  (let [cs (map contribution drivers)
        n (count cs)
        net (if (zero? n) 0.0 (/ (reduce + cs) n))
        pos (reduce + (filter pos? cs))
        neg (- (reduce + (filter neg? cs)))]
    {:count n
     :net (round3 net)
     :intensify-force (round3 pos)
     :relieve-force (round3 neg)
     :regime (regime-of net pos neg)
     :hypothesis? true}))

(defn by-stock [drivers]
  (reduce (fn [m s] (assoc m s (stock-pressure (filter #(= s (:stock %)) drivers))))
          {} stock-order))

(defn loop-drive
  "JOINT pressure of a loop's member stocks: mean net, summed intensify/relieve
  forces. The loop's 'drive' — read from ALL connected stocks (HYPOTHESIS, G5)."
  [stocks member-stocks]
  (let [sps (keep #(get stocks %) member-stocks)
        n (count sps)
        net (if (zero? n) 0.0 (/ (reduce + (map :net sps)) n))
        pos (reduce + (map :intensify-force sps))
        neg (reduce + (map :relieve-force sps))]
    {:drive (round3 net) :intensify-force (round3 pos) :relieve-force (round3 neg)}))

(defn loop-regimes
  "Read each canonical loop's regime off the JOINT pressure of its member stocks
  (HYPOTHESIS, G5). A reinforcing loop whose coupled stocks are jointly intensifying
  is :vicious; a balancing loop actually relieving its stock is :virtuous (doing its
  job)."
  [stocks]
  (mapv
   (fn [{:keys [type dominant] :as lp0}]
     (let [lp (dissoc lp0 :stocks)
           member (or (:stocks lp0) [dominant])
           {:keys [drive intensify-force relieve-force]} (loop-drive stocks member)
           base (regime-of drive intensify-force relieve-force)
           regime (if (= type :balancing)
                    (cond (= base :virtuous) :virtuous
                          (= base :vicious)  :vicious   ;; balancer is being overwhelmed
                          :else base)
                    base)]
       (assoc lp :member-stocks (vec member)
                 :dominant-net (:net (get stocks dominant))
                 :drive drive :regime regime :hypothesis? true)))
   loops))

;; ── the FAILURE CYCLE (the user-asked-for read-off; routed toward relief, G7) ──
(defn failure-cycle
  "A focused read of the 受験失敗 cycle: the R-failure-despair loop's drive
  (failure-penalty ⇄ wellbeing-erosion), the relief present on those two stocks,
  and the RELIEF GAP. Stated soberly and routed toward RELIEF (kokoro 心 mental-
  health support / shiori 栞 detractor-relief), never amplified (G7). HYPOTHESIS (G5)."
  [stocks loops*]
  (let [fp (get stocks :failure-penalty)
        we (get stocks :wellbeing-erosion)
        lp (first (filter #(= "R-failure-despair" (:id %)) loops*))
        relief (round3 (+ (:relieve-force fp) (:relieve-force we)))
        pressure (round3 (+ (:intensify-force fp) (:intensify-force we)))
        gap (round3 (- pressure relief))]
    {:loop "R-failure-despair"
     :drive (:drive lp)
     :regime (some-> (:regime lp) name)
     :failure-penalty-net (:net fp)
     :wellbeing-erosion-net (:net we)
     :pressure pressure
     :relief relief
     :relief-gap gap                         ;; >0 ⇒ more pressure than relief on the failure cycle
     :route-to ["kokoro" "shiori"]           ;; G7 — relief routing, never amplification
     :note "受験失敗 cycle: a sober relief MAP routed to kokoro/shiori; never a despair amplifier or a roster of failing students (G7+G8)."
     :hypothesis? true}))

;; DISCLOSED leverage-scoring weights (public + auditable; G11 transparency).
(def leverage-weights
  {:amplify {:depth 0.6 :magnitude 0.4}            ;; deeper Meadows level + bigger relieving pull
   :flip    {:tractability 0.5 :effective 0.5}})   ;; easier to flip + bigger intensifying pull
(def tractability-score {:policy 3 :institutional 2 :market 2 :cultural 1 :entrenched 0})

(defn amplify-score
  "Disclosed score for a RELIEVING candidate worth amplifying. {:score :components}."
  [d]
  (let [depth (/ (- 13 (double (:meadows d))) 12.0)     ;; 0..1, deeper level → higher
        mag (double (or (:magnitude d) 0))
        w (:amplify leverage-weights)
        score (+ (* (:depth w) depth) (* (:magnitude w) mag))]
    {:score (round3 score)
     :components {:depth (round3 depth) :magnitude (round3 mag) :weights w}}))

(defn flip-score
  "Disclosed score for an INTENSIFYING candidate where the spiral could ease.
  {:score :components}."
  [d]
  (let [tract (/ (double (get tractability-score (:reversibility d) 0)) 3.0)  ;; 0..1
        eff (* (double (or (:magnitude d) 0)) (double (or (:confidence d) 1.0)))
        w (:flip leverage-weights)
        score (+ (* (:tractability w) tract) (* (:effective w) eff))]
    {:score (round3 score)
     :components {:tractability (round3 tract) :effective (round3 eff) :weights w}}))

(defn leverage-candidates
  "Meadows leverage CANDIDATES (G11 prescription? false): the deepest-leverage
  RELIEVING drivers already easing the spiral (amplify-worthy), and the highest-
  magnitude INTENSIFYING drivers whose reversibility is most tractable (where the
  spiral could ease). Each candidate carries a DISCLOSED :score + :components so the
  rank is auditable. Candidates WITH uncertainty — never directives."
  [drivers]
  (let [relievers (->> drivers
                       (filter #(= :relieve (:polarity %)))
                       (map (fn [d] (merge {:id (:id d) :name (:name d) :jurisdiction (:jurisdiction d)
                                            :stock (:stock d) :meadows (:meadows d)
                                            :role :amplify-relieving :prescription? false}
                                           (amplify-score d))))
                       (sort-by #(- (:score %)))
                       (take 6) vec)
        intensifiers (->> drivers
                          (filter #(= :intensify (:polarity %)))
                          (map (fn [d] (merge {:id (:id d) :name (:name d) :jurisdiction (:jurisdiction d)
                                               :stock (:stock d) :meadows (:meadows d)
                                               :reversibility (:reversibility d)
                                               :role :flip-intensifying :prescription? false}
                                              (flip-score d))))
                          (sort-by #(- (:score %)))
                          (take 6) vec)]
    {:amplify relievers :flip intensifiers :weights leverage-weights :prescription? false}))

;; ── region map (continental grouping for coverage balance; coarse) ───────────
(def jurisdiction-region
  {"CN" :asia "KR" :asia "JP" :asia "IN" :asia "SG" :asia "TW" :asia "HK" :asia
   "VN" :asia "TH" :asia "ID" :asia "PH" :asia "MY" :asia
   "FI" :europe "DE" :europe "GB" :europe "FR" :europe "SE" :europe "NO" :europe
   "US" :americas "BR" :americas "MX" :americas "CA" :americas
   "NG" :africa "ZA" :africa "KE" :africa "EG" :africa
   "AU" :oceania "NZ" :oceania})

(defn region-of [jurisdiction] (get jurisdiction-region jurisdiction :other))

(defn coverage [drivers]
  (let [js (sort (distinct (map :jurisdiction drivers)))
        stocks-covered (set (map :stock drivers))
        missing-stocks (remove stocks-covered stock-order)
        ;; stocks with no relieving driver yet = ingest worklist
        relieve-by-stock (set (map :stock (filter #(= :relieve (:polarity %)) drivers)))
        no-relief (remove relieve-by-stock stock-order)
        region-juris (reduce (fn [m j] (update m (region-of j) (fnil conj #{}) j)) {} js)
        regions (into {} (map (fn [[r s]] [r (count s)]) region-juris))
        unmapped (vec (sort (get region-juris :other #{})))
        stock-counts (into {} (map (fn [s] [s (count (filter #(= s (:stock %)) drivers))]) stock-order))
        thinnest (when (seq stock-counts) (key (apply min-key val stock-counts)))]
    {:drivers (count drivers)
     :jurisdictions (count js)
     :jurisdiction-list (vec js)
     :kinds (frequencies (map :kind drivers))
     :stocks (frequencies (map :stock drivers))
     :polarity (frequencies (map :polarity drivers))
     :sourcing (frequencies (map :sourcing drivers))
     :regions regions
     :unmapped-jurisdictions unmapped
     :stocks-without-data (vec missing-stocks)
     :stocks-without-relief (vec no-relief)
     :thinnest-stock (some-> thinnest name)
     :worklist (vec (concat
                     (map #(str "add data for stock " (name %)) missing-stocks)
                     (map #(str "add a relieving driver for stock " (name %)) no-relief)
                     (when thinnest [(str "deepen thinnest stock: " (name thinnest)
                                          " (n=" (get stock-counts thinnest) ")")])
                     (when (seq unmapped) [(str "map region for jurisdictions: " (str/join " " unmapped))])
                     ["broaden jurisdiction coverage (more Asian + Global-South exam systems)"]))}))

;; ── temporal era trajectory (system-dynamics over time; structural, not a rank) ──
(def era-order
  ["pre-1960" "1960–1979" "1980–1999" "2000–2009" "2010–2019" "2020–"])

(defn era-of
  "Map an enactment/onset year to a coarse era bucket. Undated (year 0/nil) → nil."
  [year]
  (let [y (long (or year 0))]
    (cond
      (<= y 0)   nil
      (< y 1960) "pre-1960"
      (< y 1980) "1960–1979"
      (< y 2000) "1980–1999"
      (< y 2010) "2000–2009"
      (< y 2020) "2010–2019"
      :else      "2020–")))

(defn era-trajectory
  "Fold dated drivers by era → intensify/relieve force + net pressure per era. Reads
  the long-run TRAJECTORY of the involution (whether drivers of each era lean toward
  intensifying or relieving). Structural over time — NOT a country ranking (G7).
  HYPOTHESIS (G5)."
  [drivers]
  (let [dated (filter #(era-of (:year %)) drivers)
        by-era (group-by #(era-of (:year %)) dated)]
    (vec
     (for [era era-order
           :let [ds (get by-era era)]
           :when (seq ds)
           :let [cs (map contribution ds)
                 pos (reduce + (filter pos? cs))
                 neg (- (reduce + (filter neg? cs)))]]
       {:era era :count (count ds)
        :intensify-force (round3 pos) :relieve-force (round3 neg)
        :net (round3 (/ (reduce + cs) (count cs)))
        :hypothesis? true}))))

(def kind-order [:policy :institution :practice :norm])

(defn kind-polarity-matrix
  "For each driver KIND, the net pressure (mean signed contribution) + count +
  polarity mix. Do policies vs institutions vs practices vs norms systematically
  intensify or relieve the involution? Fully aggregate; HYPOTHESIS (G5)."
  [drivers]
  (into {}
        (for [k kind-order
              :let [in-k (filter #(= k (:kind %)) drivers)
                    cs (map contribution in-k)]
              :when (seq in-k)]
          [k {:count (count in-k)
              :net (round3 (/ (reduce + cs) (count cs)))
              :polarity (frequencies (map :polarity in-k))}])))

(defn extreme-drivers
  "The strongest concrete signals: top-n drivers by signed contribution at each pole
  — the most intensifying and the most relieving named policies/institutions.
  Concrete examples behind the aggregates (HYPOTHESIS, G5)."
  [drivers n]
  (let [scored (map (fn [d] {:id (:id d) :name (:name d) :jurisdiction (:jurisdiction d)
                             :stock (:stock d) :contribution (round3 (contribution d))})
                    drivers)
        sorted (sort-by :contribution scored)]
    {:most-intensifying (vec (reverse (take-last n sorted)))
     :most-relieving (vec (take n sorted))}))

(defn headline
  "A compact, structured digest of the most salient read-off (HYPOTHESIS, G5):
  the most-pressured stock, the latest-era net trend, and the strongest intensifying
  driver. Aggregate + sober (G7); a summary, never a directive (G11)."
  [drivers stocks-map kind-mat traj]
  (let [most-pressured (->> stocks-map
                            (map (fn [[k v]] [k (:net v)]))
                            (sort-by (comp - second))
                            first)
        latest-era (last traj)
        relieving-kind (->> kind-mat
                            (map (fn [[k v]] [k (:net v)]))
                            (sort-by second)
                            first)
        top-intensify (->> drivers (sort-by #(- (contribution %))) first)]
    {:most-pressured-stock (some-> most-pressured first name)
     :most-pressured-net (some-> most-pressured second)
     :latest-era (:era latest-era)
     :latest-era-net (:net latest-era)
     :most-relieving-kind (some-> relieving-kind first name)
     :most-relieving-kind-net (some-> relieving-kind second)
     :strongest-intensifying-driver (:name top-intensify)
     :strongest-intensifying-jurisdiction (:jurisdiction top-intensify)
     :hypothesis? true}))

(defn analyze
  "Full read-off bundle. Pure; no I/O; no outward channel (G4)."
  [drivers]
  (let [stocks (by-stock drivers)
        loops* (loop-regimes stocks)
        kind-mat (kind-polarity-matrix drivers)
        traj (era-trajectory drivers)]
    {"stocks" (into {} (map (fn [[k v]] [(name k) v]) stocks))
     "headline" (headline drivers stocks kind-mat traj)
     "extremes" (extreme-drivers drivers 5)
     "loops" loops*
     "failure_cycle" (failure-cycle stocks loops*)
     "leverage" (leverage-candidates drivers)
     "trajectory" traj
     "kind_polarity" (into {} (map (fn [[k v]] [(name k) v]) kind-mat))
     "coverage" (coverage drivers)
     "hypothesis_only" true
     "actuation_taken" false}))

;; ── datom emission (append-only EAVT; flagged; HYPOTHESIS) ───────────────────
(defn- add [e a v] [":db/add" e a v])

(defn driver-datoms
  "Append-only EAVT datom vectors for the disclosed driver facts + the derived
  signed contribution. Person-free (G6): :enactor/:stakeholders are institutional
  strings. No :shinogi/actuate, :shinogi/dispatch, or per-student attribute is ever
  emitted (G4/G6/G8)."
  [drivers]
  (vec
   (mapcat
    (fn [d]
      (let [e (str "shinogi-driver:" (:id d))]
        [(add e ":shinogi.exam.driver/name" (str (:name d)))
         (add e ":shinogi.exam.driver/jurisdiction" (str (:jurisdiction d)))
         (add e ":shinogi.exam.driver/kind" (str (:kind d)))
         (add e ":shinogi.exam.driver/year" (long (or (:year d) 0)))
         (add e ":shinogi.exam.driver/enactor" (str (:enactor d)))
         (add e ":shinogi.exam.driver/origin" (str (:origin d)))
         (add e ":shinogi.exam.driver/stock" (str (:stock d)))
         (add e ":shinogi.exam.driver/polarity" (str (:polarity d)))
         (add e ":shinogi.exam.driver/contribution" (round3 (contribution d)))
         (add e ":shinogi.exam.driver/meadows" (long (or (:meadows d) 0)))
         (add e ":shinogi.exam.driver/basis" (str (:basis d)))
         (add e ":shinogi/sourcing" (str (:sourcing d)))
         (add e ":shinogi/hypothesis" ":true")
         (add e ":shinogi/derived" true)]))
    drivers)))

(defn stock-datoms [analysis]
  (vec
   (mapcat
    (fn [[s sp]]
      (let [e (str "shinogi-stock:" s)]
        [(add e ":shinogi.exam.stock/net" (:net sp))
         (add e ":shinogi.exam.stock/intensify-force" (:intensify-force sp))
         (add e ":shinogi.exam.stock/relieve-force" (:relieve-force sp))
         (add e ":shinogi.exam.stock/regime" (str (:regime sp)))
         (add e ":shinogi.exam.stock/count" (long (:count sp)))
         (add e ":shinogi/hypothesis" ":true")
         (add e ":shinogi/derived" true)]))
    (get analysis "stocks"))))

(defn loop-datoms [analysis]
  (vec
   (mapcat
    (fn [lp]
      (let [e (str "shinogi-loop:" (:id lp))]
        [(add e ":shinogi.exam.loop/type" (str (:type lp)))
         (add e ":shinogi.exam.loop/dominant-stock" (str (:dominant lp)))
         (add e ":shinogi.exam.loop/drive" (:drive lp))
         (add e ":shinogi.exam.loop/regime" (str (:regime lp)))
         (add e ":shinogi/hypothesis" ":true")
         (add e ":shinogi/derived" true)]))
    (get analysis "loops"))))

(defn failure-cycle-datoms [analysis]
  (let [fc (get analysis "failure_cycle")
        e "shinogi-failure-cycle:R-failure-despair"]
    [(add e ":shinogi.exam.failure/drive" (:drive fc))
     (add e ":shinogi.exam.failure/regime" (str (:regime fc)))
     (add e ":shinogi.exam.failure/pressure" (:pressure fc))
     (add e ":shinogi.exam.failure/relief" (:relief fc))
     (add e ":shinogi.exam.failure/relief-gap" (:relief-gap fc))
     (add e ":shinogi/hypothesis" ":true")
     (add e ":shinogi/derived" true)]))

(defn era-datoms [analysis]
  (vec
   (mapcat
    (fn [e]
      (let [ent (str "shinogi-era:" (:era e))]
        [(add ent ":shinogi.exam.era/net" (:net e))
         (add ent ":shinogi.exam.era/intensify-force" (:intensify-force e))
         (add ent ":shinogi.exam.era/relieve-force" (:relieve-force e))
         (add ent ":shinogi.exam.era/count" (long (:count e)))
         (add ent ":shinogi/hypothesis" ":true")
         (add ent ":shinogi/derived" true)]))
    (get analysis "trajectory"))))

(defn datoms
  "All findings datoms for one analysis (drivers + stocks + loops + failure-cycle + era)."
  [drivers analysis]
  (vec (concat (driver-datoms drivers)
               (stock-datoms analysis)
               (loop-datoms analysis)
               (failure-cycle-datoms analysis)
               (era-datoms analysis))))

(defn render-datoms [drivers analysis]
  (str "[\n " (str/join "\n " (map pr-str (datoms drivers analysis))) "\n]\n"))

;; ── markdown report (sober / wellbecoming-positive / map-not-rank, G7+G8) ────
(defn render-report [analysis]
  (let [stocks (get analysis "stocks")
        cov (get analysis "coverage")
        fc (get analysis "failure_cycle")]
    (str
     "# shinogi 鎬 — 受験競争 involution (内卷) の system-dynamics read-off\n\n"
     "高考 / 수능 / 受験 / JEE-NEET といった高stakes受験システムの **具体的な政策・制度・"
     "慣行・規範** が involution (内卷=努力の軍拡) と **受験失敗の cycle** をどう強める/緩める"
     "かを、6 つの pressure STOCK と feedback LOOP で読み取る。"
     "**分析専用 (G4): shinogi は観るだけで触れない。** 各 regime / leverage は **仮説 (G5)** であり"
     "因果の証明ではない。これは relief/leverage の MAP であって、学生・学校・国家を晒す ranking ではない (G7+G8)。\n\n"
     "_coverage_: " (:drivers cov) " drivers · " (:jurisdictions cov)
     " jurisdictions · sourcing " (pr-str (:sourcing cov)) "\n\n"
     (let [h (get analysis "headline")]
       (str "**要点 (HYPOTHESIS, G5):** いま最も圧力がかかる stock は **" (:most-pressured-stock h)
            "** (net " (:most-pressured-net h) ")。直近 era **" (:latest-era h) "** の net は "
            (:latest-era-net h) "。最も involution を強める driver は **"
            (:strongest-intensifying-driver h) "** (" (:strongest-intensifying-jurisdiction h) ")。\n\n"))
     ;; ── the failure cycle (foregrounded; routed to relief, G7) ──
     "## 受験失敗の system cycle (R-failure-despair, HYPOTHESIS, G5)\n\n"
     "_失敗 → 烙印 → 心身ウェルビーイングの侵食 → 次の機会の喪失 → 烙印 の強化ループ。"
     "**素面に記述し、RELIEF (kokoro 心 / shiori 栞) へ routing する** — 絶望を増幅せず、"
     "「落ちた学生」の名簿でもない (G7+G8)。_\n\n"
     "- loop drive: **" (:drive fc) "** (regime " (:regime fc) ")\n"
     "- failure-penalty net " (:failure-penalty-net fc)
     " · wellbeing-erosion net " (:wellbeing-erosion-net fc) "\n"
     "- pressure " (:pressure fc) " vs relief " (:relief fc)
     " → **relief-gap " (:relief-gap fc) "** (>0 = 緩和より圧力が勝る)\n"
     "- route-to: " (str/join " / " (:route-to fc)) "\n\n"
     "## Strongest concrete signals (HYPOTHESIS, G5)\n\n"
     "**最も involution を強める driver:**\n"
     (str/join "\n" (for [c (get-in analysis ["extremes" :most-intensifying])]
                      (str "- [" (:contribution c) "] " (:name c) " (" (:jurisdiction c)
                           ", " (name (:stock c)) ")")))
     "\n\n**最も緩和する driver:**\n"
     (str/join "\n" (for [c (get-in analysis ["extremes" :most-relieving])]
                      (str "- [" (:contribution c) "] " (:name c) " (" (:jurisdiction c)
                           ", " (name (:stock c)) ")")))
     "\n\n## Pressure stocks (regime = HYPOTHESIS)\n\n"
     "| stock | n | net pressure | intensify | relieve | regime |\n"
     "|---|---|---|---|---|---|\n"
     (str/join "\n"
               (for [s stock-order
                     :let [sp (get stocks (name s))]
                     :when sp]
                 (str "| " (stock-label s)
                      " | " (:count sp)
                      " | " (:net sp)
                      " | " (:intensify-force sp)
                      " | " (:relieve-force sp)
                      " | " (name (:regime sp)) " |")))
     "\n\n_net > 0 = involution が強まる方向に loop が回っている (悪循環); net < 0 = 緩和方向 (好循環)。_\n\n"
     "## Structural loops (HYPOTHESIS, G5 — drive = joint pressure of member stocks)\n\n"
     "| loop | type | member stocks | drive | regime |\n"
     "|---|---|---|---|---|\n"
     (str/join "\n"
               (for [lp (get analysis "loops")]
                 (str "| " (:id lp) " | " (name (:type lp))
                      " | " (str/join ", " (map name (:member-stocks lp)))
                      " | " (:drive lp)
                      " | " (name (:regime lp)) " |")))
     "\n\n## Driver kind × net pressure (do policies/institutions/practices/norms intensify or relieve?)\n\n"
     "| kind | n | net | polarity mix |\n|---|---|---|---|\n"
     (str/join "\n" (for [k kind-order
                          :let [m (get (get analysis "kind_polarity") (name k))]
                          :when m]
                      (str "| " (name k) " | " (:count m) " | " (:net m)
                           " | " (pr-str (:polarity m)) " |")))
     "\n\n## Era trajectory (system-dynamics over time, HYPOTHESIS, G5)\n\n"
     "_各時代の driver が involution を強める/緩める方向にどれだけ傾くか。構造の時系列であって国家 ranking ではない (G7)。_\n\n"
     "| era | n | intensify | relieve | net |\n"
     "|---|---|---|---|---|\n"
     (str/join "\n"
               (for [e (get analysis "trajectory")]
                 (str "| " (:era e) " | " (:count e)
                      " | " (:intensify-force e) " | " (:relieve-force e)
                      " | " (:net e) " |")))
     "\n\n## Meadows leverage CANDIDATES (G11 — candidates, never directives)\n\n"
     "_scores are DISCLOSED + weighted (amplify = 0.6·depth + 0.4·magnitude; flip = "
     "0.5·tractability + 0.5·magnitude·confidence) — the rank is auditable, not a directive._\n\n"
     "**増幅候補 (既に involution を緩める深いレバレッジ driver):**\n"
     (str/join "\n" (for [c (get-in analysis ["leverage" :amplify])]
                      (str "- [" (:score c) "] L" (:meadows c) " · " (:name c) " ("
                           (:jurisdiction c) ", " (name (:stock c)) ")")))
     "\n\n**緩和余地候補 (involution を強めており、最も是正余地のある driver):**\n"
     (str/join "\n" (for [c (get-in analysis ["leverage" :flip])]
                      (str "- [" (:score c) "] L" (:meadows c) " · " (:name c) " ("
                           (:jurisdiction c) ", " (name (:stock c))
                           ", reversibility=" (name (or (:reversibility c) :-)) ")")))
     "\n\n## Coverage worklist (next /loop iterations)\n\n"
     (str/join "\n" (map #(str "- " %) (:worklist cov)))
     "\n\n_findings are append-only; surfacing beyond Council is performed by ossekai/kataribe on shinogi's behalf, never by shinogi (G13). actuation_taken=false throughout._\n")))

;; ── CLI (bb) ─────────────────────────────────────────────────────────────────
#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/shinogi/kotoba/seed.exam-involution.edn")
           rows (clojure.edn/read-string (slurp seed))
           ds (vec (filter #(= (:type %) :driver) rows))
           a (analyze ds)]
       (println (render-report a))
       (println (str "-- " (count ds) " drivers · "
                     (get-in a ["coverage" :jurisdictions]) " jurisdictions analysed --")))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
