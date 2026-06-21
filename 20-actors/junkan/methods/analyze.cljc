#!/usr/bin/env bb
;; junkan 循環 — governance-asymmetry system-dynamics read-off (clj-native, pure stdlib).
(ns junkan.methods.analyze
  "junkan 循環 — the ANALYSIS-ONLY system-dynamics read-off over the global
  governance-asymmetry instruments (ADR-2605290927).

  Each instrument feeds an asymmetry STOCK (information / participation / coercion
  / paradigm / economic) with a polarity (:widen / :narrow / :ambiguous) and a
  disclosed-hypothesis magnitude. junkan reads off:

    1. per-instrument signed contribution  = sign(polarity) · magnitude · confidence
    2. per-stock net pressure (mean of contributions) → REGIME
         :vicious (net widening) / :virtuous (net narrowing) / :neutral / :transitioning
    3. per-LOOP regime (from the loop's dominant stock; HYPOTHESIS only, G5)
    4. Meadows LEVERAGE candidates (the deepest-leverage narrowing instruments +
       the highest-pressure widening instruments whose reversibility is favorable)
       — CANDIDATES WITH UNCERTAINTY, never directives (G11 prescription? false)
    5. coverage (jurisdictions / kinds / stocks / sourcing) + an ingest worklist.

  DISCIPLINE (the analysis-only spine):
    G4  this namespace has NO outward channel — it returns data / writes a local
        ledger; there is no post/mention/email/tx path (enforced by absence).
    G5  every loop/regime is a HYPOTHESIS (`hypothesis? true`); correlation/sign
        only, never proven causation. `causal-proven` is unrepresentable.
    G6  aggregate-only — instruments + institutional enactors; no private individual.
    G7  sober, non-eschatological framing in the report; no doom/ranking-to-shame.
    G11 leverage points are candidates (`prescription? false`); no directive issued."
  (:require [clojure.string :as str]))

;; ── stock catalog (display order + labels) ───────────────────────────────────
(def stock-order
  [:information-asymmetry :participation-barrier :coercion-asymmetry
   :paradigm-subordination :economic-capture])

(def stock-label
  {:information-asymmetry  "A 情報・可視性の非対称 (information)"
   :participation-barrier  "B 参入・代表性の障壁 (participation)"
   :coercion-asymmetry     "C 強制力の非対称 (coercion)"
   :paradigm-subordination "D 思想・価値観の従属 (paradigm)"
   :economic-capture       "E 経済的レバレッジ集中 (economic)"})

;; ── canonical structural loops (HYPOTHESES; mirror ontology :loops) ──────────
(def loops
  [{:id "R-secrecy-spiral"        :type :reinforcing :dominant :information-asymmetry}
   {:id "R-coercion-paradigm-lock":type :reinforcing :dominant :paradigm-subordination}
   {:id "R-capture-barrier"       :type :reinforcing :dominant :economic-capture}
   {:id "B-transparency"          :type :balancing   :dominant :information-asymmetry}
   {:id "B-participation"         :type :balancing   :dominant :participation-barrier}])

;; ── pure read-off ────────────────────────────────────────────────────────────
(defn- round3 [x] (/ (Math/round (* (double x) 1000.0)) 1000.0))

(defn polarity-sign [p]
  (case p :widen 1.0 :narrow -1.0 :ambiguous 0.0 0.0))

(defn contribution
  "Signed contribution of an instrument to its stock ∈ [-1,1]:
   +ve = widens the citizen↔state asymmetry, -ve = narrows it (HYPOTHESIS, G5)."
  [i]
  (* (polarity-sign (:polarity i))
     (double (or (:magnitude i) 0))
     (double (or (:confidence i) 1.0))))

(defn regime-of
  "Read a regime off a net pressure + spread. `pos`/`neg` = magnitudes of widening
  vs narrowing present. Transitioning = both forces strong (the stock is contested)."
  [net pos neg]
  (cond
    (and (>= pos 0.3) (>= neg 0.3) (< (Math/abs (double net)) 0.2)) :transitioning
    (>  net 0.15) :vicious
    (< net -0.15) :virtuous
    :else :neutral))

(defn stock-pressure
  "For one stock: net pressure (mean signed contribution), pos/neg force totals,
  instrument count, and the read-off regime. HYPOTHESIS (G5)."
  [instrs]
  (let [cs (map contribution instrs)
        n (count cs)
        net (if (zero? n) 0.0 (/ (reduce + cs) n))
        pos (reduce + (filter pos? cs))
        neg (- (reduce + (filter neg? cs)))]
    {:count n
     :net (round3 net)
     :widen-force (round3 pos)
     :narrow-force (round3 neg)
     :regime (regime-of net pos neg)
     :hypothesis? true}))

(defn by-stock [instruments]
  (reduce (fn [m s] (assoc m s (stock-pressure (filter #(= s (:stock %)) instruments))))
          {} stock-order))

(defn loop-regimes
  "Read each canonical loop's regime off its dominant stock (HYPOTHESIS, G5).
  A reinforcing loop over a widening stock is :vicious; a balancing loop that is
  actually narrowing its stock is :virtuous (it is doing its job)."
  [stocks]
  (mapv
   (fn [{:keys [id type dominant] :as lp}]
     (let [sp (get stocks dominant)
           base (:regime sp)
           regime (cond
                    (= type :balancing)
                    (cond (= base :virtuous) :virtuous
                          (= base :vicious)  :vicious      ;; balancer is being overwhelmed
                          :else base)
                    :else base)]
       (assoc lp :dominant-net (:net sp) :regime regime :hypothesis? true)))
   loops))

(defn leverage-candidates
  "Meadows leverage CANDIDATES (G11 prescription? false): the deepest-leverage
  NARROWING instruments already pushing toward balance (amplify-worthy), and the
  highest-magnitude WIDENING instruments whose reversibility is most tractable
  (where a loop could flip). Candidates WITH uncertainty — never directives."
  [instruments]
  (let [narrowers (->> instruments
                       (filter #(= :narrow (:polarity %)))
                       (sort-by (fn [i] [(:meadows i) (- (double (or (:magnitude i) 0)))]))
                       (take 6)
                       (mapv (fn [i] {:id (:id i) :name (:name i) :jurisdiction (:jurisdiction i)
                                      :stock (:stock i) :meadows (:meadows i)
                                      :role :amplify-narrowing :prescription? false})))
        tractable {:statutory 3 :institutional 2 :constitutional 1 :cultural 1 :entrenched 0}
        wideners (->> instruments
                      (filter #(= :widen (:polarity %)))
                      (sort-by (fn [i] [(- (get tractable (:reversibility i) 0))
                                        (- (* (double (or (:magnitude i) 0))
                                              (double (or (:confidence i) 1.0))))]))
                      (take 6)
                      (mapv (fn [i] {:id (:id i) :name (:name i) :jurisdiction (:jurisdiction i)
                                     :stock (:stock i) :meadows (:meadows i)
                                     :reversibility (:reversibility i)
                                     :role :flip-widening :prescription? false})))]
    {:amplify narrowers :flip wideners :prescription? false}))

(defn coverage [instruments]
  (let [js (sort (distinct (map :jurisdiction instruments)))
        stocks-covered (set (map :stock instruments))
        missing-stocks (remove stocks-covered stock-order)
        ;; stocks with no narrowing (balancing) instrument yet = ingest worklist
        narrow-by-stock (set (map :stock (filter #(= :narrow (:polarity %)) instruments)))
        no-balancer (remove narrow-by-stock stock-order)]
    {:instruments (count instruments)
     :jurisdictions (count js)
     :jurisdiction-list (vec js)
     :kinds (frequencies (map :kind instruments))
     :stocks (frequencies (map :stock instruments))
     :polarity (frequencies (map :polarity instruments))
     :sourcing (frequencies (map :sourcing instruments))
     :stocks-without-data (vec missing-stocks)
     :stocks-without-balancer (vec no-balancer)
     :worklist (vec (concat
                     (map #(str "add data for stock " (name %)) missing-stocks)
                     (map #(str "add a narrowing/balancing instrument for stock " (name %)) no-balancer)
                     ["broaden jurisdiction coverage (Global South / small states under-represented)"]))}))

(defn analyze
  "Full read-off bundle. Pure; no I/O; no outward channel (G4)."
  [instruments]
  (let [stocks (by-stock instruments)]
    {"stocks" (into {} (map (fn [[k v]] [(name k) v]) stocks))
     "loops" (loop-regimes stocks)
     "leverage" (leverage-candidates instruments)
     "coverage" (coverage instruments)
     "hypothesis_only" true
     "actuation_taken" false}))

;; ── datom emission (append-only EAVT; flagged; HYPOTHESIS) ───────────────────
(defn- add [e a v] [":db/add" e a v])

(defn instrument-datoms
  "Append-only EAVT datom vectors for the disclosed instrument facts + the derived
  signed contribution. Person-free (G6): :enactor/:stakeholders are institutional
  strings. No :junkan/actuate or :junkan/dispatch attribute is ever emitted (G4)."
  [instruments]
  (vec
   (mapcat
    (fn [i]
      (let [e (str "junkan-instr:" (:id i))]
        [(add e ":junkan.gov.instr/name" (str (:name i)))
         (add e ":junkan.gov.instr/jurisdiction" (str (:jurisdiction i)))
         (add e ":junkan.gov.instr/kind" (str (:kind i)))
         (add e ":junkan.gov.instr/year" (long (or (:year i) 0)))
         (add e ":junkan.gov.instr/enactor" (str (:enactor i)))
         (add e ":junkan.gov.instr/origin" (str (:origin i)))
         (add e ":junkan.gov.instr/stock" (str (:stock i)))
         (add e ":junkan.gov.instr/polarity" (str (:polarity i)))
         (add e ":junkan.gov.instr/contribution" (round3 (contribution i)))
         (add e ":junkan.gov.instr/meadows" (long (or (:meadows i) 0)))
         (add e ":junkan.gov.instr/basis" (str (:basis i)))
         (add e ":junkan/sourcing" (str (:sourcing i)))
         (add e ":junkan/hypothesis" ":true")
         (add e ":junkan/derived" true)]))
    instruments)))

(defn stock-datoms [analysis]
  (vec
   (mapcat
    (fn [[s sp]]
      (let [e (str "junkan-stock:" s)]
        [(add e ":junkan.gov.stock/net" (:net sp))
         (add e ":junkan.gov.stock/widen-force" (:widen-force sp))
         (add e ":junkan.gov.stock/narrow-force" (:narrow-force sp))
         (add e ":junkan.gov.stock/regime" (str (:regime sp)))
         (add e ":junkan.gov.stock/count" (long (:count sp)))
         (add e ":junkan/hypothesis" ":true")
         (add e ":junkan/derived" true)]))
    (get analysis "stocks"))))

(defn loop-datoms [analysis]
  (vec
   (mapcat
    (fn [lp]
      (let [e (str "junkan-loop:" (:id lp))]
        [(add e ":junkan.gov.loop/type" (str (:type lp)))
         (add e ":junkan.gov.loop/dominant-stock" (str (:dominant lp)))
         (add e ":junkan.gov.loop/regime" (str (:regime lp)))
         (add e ":junkan/hypothesis" ":true")
         (add e ":junkan/derived" true)]))
    (get analysis "loops"))))

(defn datoms
  "All findings datoms for one analysis (instruments + stocks + loops)."
  [instruments analysis]
  (vec (concat (instrument-datoms instruments)
               (stock-datoms analysis)
               (loop-datoms analysis))))

(defn render-datoms [instruments analysis]
  (str "[\n " (str/join "\n " (map pr-str (datoms instruments analysis))) "\n]\n"))

;; ── markdown report (sober / non-eschatological / map-not-rank, G7) ──────────
(defn render-report [analysis]
  (let [stocks (get analysis "stocks")
        cov (get analysis "coverage")]
    (str
     "# junkan 循環 — 国民↔政府 非対称の system-dynamics read-off\n\n"
     "全世界の **具体的な法律・制度・思想・価値観** が citizen↔state の構造的非対称をどう"
     "広げる/狭めるかを、5 つの asymmetry STOCK と feedback LOOP で読み取る。"
     "**分析専用 (G4): junkan は観るだけで触れない。** 各 regime / leverage は **仮説 (G5)** であり"
     "因果の証明ではない。これは resilience/leverage の MAP であって、国家を晒す ranking ではない (G7)。\n\n"
     "_coverage_: " (:instruments cov) " instruments · " (:jurisdictions cov)
     " jurisdictions · sourcing " (pr-str (:sourcing cov)) "\n\n"
     "## Asymmetry stocks (regime = HYPOTHESIS)\n\n"
     "| stock | n | net pressure | widen | narrow | regime |\n"
     "|---|---|---|---|---|---|\n"
     (str/join "\n"
               (for [s stock-order
                     :let [sp (get stocks (name s))]
                     :when sp]
                 (str "| " (stock-label s)
                      " | " (:count sp)
                      " | " (:net sp)
                      " | " (:widen-force sp)
                      " | " (:narrow-force sp)
                      " | " (name (:regime sp)) " |")))
     "\n\n_net > 0 = 非対称が広がる方向に loop が回っている (悪循環傾向); net < 0 = 是正方向 (好循環)。_\n\n"
     "## Structural loops (HYPOTHESIS, G5)\n\n"
     "| loop | type | dominant stock | regime |\n"
     "|---|---|---|---|\n"
     (str/join "\n"
               (for [lp (get analysis "loops")]
                 (str "| " (:id lp) " | " (name (:type lp))
                      " | " (name (:dominant lp)) " | " (name (:regime lp)) " |")))
     "\n\n## Meadows leverage CANDIDATES (G11 — candidates, never directives)\n\n"
     "**増幅候補 (既に是正方向に働く深いレバレッジ instrument):**\n"
     (str/join "\n" (for [c (get-in analysis ["leverage" :amplify])]
                      (str "- L" (:meadows c) " · " (:name c) " (" (:jurisdiction c) ", "
                           (name (:stock c)) ")")))
     "\n\n**反転候補 (非対称を広げており、最も是正余地のある instrument):**\n"
     (str/join "\n" (for [c (get-in analysis ["leverage" :flip])]
                      (str "- L" (:meadows c) " · " (:name c) " (" (:jurisdiction c) ", "
                           (name (:stock c)) ", reversibility=" (name (or (:reversibility c) :-)) ")")))
     "\n\n## Coverage worklist (next /loop iterations)\n\n"
     (str/join "\n" (map #(str "- " %) (:worklist cov)))
     "\n\n_findings are append-only; surfacing beyond Council is performed by ossekai/kataribe on junkan's behalf, never by junkan (G13). actuation_taken=false throughout._\n")))

;; ── CLI (bb) ─────────────────────────────────────────────────────────────────
#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/junkan/kotoba/seed.governance-asymmetry.edn")
           rows (clojure.edn/read-string (slurp seed))
           is (vec (filter #(= (:type %) :instrument) rows))
           a (analyze is)]
       (println (render-report a))
       (println (str "-- " (count is) " instruments · "
                     (get-in a ["coverage" :jurisdictions]) " jurisdictions analysed --")))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
