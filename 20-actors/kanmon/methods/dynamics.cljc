#!/usr/bin/env bb
;; kanmon 関門 — system-dynamics (causal-loop) read of the exam-gate (clj-native, analysis-only).
(ns kanmon.methods.dynamics
  "dynamics.cljc — kanmon 関門 SYSTEM-DYNAMICS read of the exam-gate causality
  (ADR-2606291500 §SD; junkan 循環 pattern — Meadows leverage, analysis-only).

  Folds the per-exam disclosed factors into the accumulating STOCKS of the 受験 system,
  reads each causal LOOP's regime off its member stocks' joint pressure, and ranks the
  OPENING routes as Meadows LEVERAGE CANDIDATES (never directives — :prescription? false).

  This is a READ, not an actuation: there is no :kanmon/actuate / :kanmon/dispatch path,
  and a leverage candidate is a disclosed hypothesis (:hypothesis? true), never a
  prescription. The system is mirrored, never steered (the inputs are kanmon's own
  disclosed exam factors).

  STOCKS (accumulating pressures):
    :exam-pressure        felt pressure of the gate
    :single-shot-stakes   one-exam/one-day life-gating
    :access-inequality    concentration of who-can-pass (region/income)
    :credential-signaling 学歴 signal / degree inflation
    :cram-dependence       塾 / 사교육 dependence
  Each exam WIDENS these (the enacted gate) and NARROWS them via its enacted mitigations
  (existing alt-pathways / transparency / equity). net = Σwiden − Σnarrow → regime."
  (:require [clojure.string :as str]
            [kanmon.methods.analyze :as az]))

(defn- clamp [x] (max 0.0 (min 1.0 (double x))))
(defn- r3 [x] (/ (Math/round (* (double x) 1000.0)) 1000.0))

(def stocks
  [:exam-pressure :single-shot-stakes :access-inequality :credential-signaling :cram-dependence])

;; ── causal loops (reinforcing R / balancing B) over the stocks ───────────────
(def loops
  [{:id "R-jken-spiral" :type :reinforcing
    :name "受験スパイラル (pressure → cram → inequality → pressure)"
    :members [:exam-pressure :cram-dependence :access-inequality]}
   {:id "R-gakureki-inflation" :type :reinforcing
    :name "学歴インフレ (signaling ↔ pressure)"
    :members [:credential-signaling :exam-pressure]}
   {:id "R-ippatsu-lock" :type :reinforcing
    :name "一発勝負ロック (single-shot ↔ pressure ↔ cram)"
    :members [:single-shot-stakes :exam-pressure :cram-dependence]}
   {:id "B-diversify" :type :balancing
    :name "多様化 (alternative pathways relieve pressure)"
    :members [:exam-pressure]}
   {:id "B-transparency" :type :balancing
    :name "透明化 (disclosure relieves signaling/inequality)"
    :members [:access-inequality :credential-signaling]}
   {:id "B-destake" :type :balancing
    :name "脱・一発 (de-staking relieves single-shot)"
    :members [:single-shot-stakes]}])

;; ── per-exam contributions to each stock (widen − narrow), confidence-weighted ─
(def ^:private conf 0.6)  ;; :representative seed → modest confidence

(defn exam-contributions
  "Signed contributions of ONE exam to each stock: a vector of
   {:stock kw :widen n :narrow n} (each ∈ 0..1, confidence-folded into net later)."
  [{:keys [selectivity single-shot stakes alt-pathways transparency equity]}]
  (let [ss (double single-shot) st (double stakes) sel (double selectivity)
        ap (double alt-pathways) tr (double transparency) eq (double equity)]
    [{:stock :exam-pressure        :widen (clamp (+ (* 0.4 ss) (* 0.3 st) (* 0.3 (- 1 ap))))
                                    :narrow (clamp ap)}                       ;; existing alt-routes relieve
     {:stock :single-shot-stakes   :widen (clamp (+ (* 0.5 ss) (* 0.5 st)))
                                    :narrow 0.0}
     {:stock :access-inequality    :widen (clamp (- 1 eq))
                                    :narrow (clamp eq)}                       ;; existing equity relieves
     {:stock :credential-signaling :widen (clamp (+ (* 0.5 sel) (* 0.5 st)))
                                    :narrow (clamp tr)}                       ;; transparency relieves signaling
     {:stock :cram-dependence      :widen (clamp (+ (* 0.6 (- 1 eq)) (* 0.4 sel)))
                                    :narrow 0.0}]))

(defn- regime-of [net]
  (cond (> net 0.15) :vicious
        (< net -0.15) :virtuous
        (< (Math/abs net) 0.05) :neutral
        :else :transitioning))

(defn stock-pressures
  "Aggregate every exam's contributions into per-stock net pressure + regime.
   net = (Σwiden − Σnarrow)/n · confidence  → ∈ roughly [-1,1]."
  [exams]
  (let [n (max 1 (count exams))
        all (mapcat exam-contributions exams)
        by-stock (group-by :stock all)]
    (into {}
          (for [s stocks]
            (let [cs (get by-stock s [])
                  w (reduce + 0.0 (map :widen cs))
                  nr (reduce + 0.0 (map :narrow cs))
                  net (r3 (* conf (/ (- w nr) n)))]
              [s {:widen-force (r3 (/ w n)) :narrow-force (r3 (/ nr n))
                  :net net :regime (regime-of net) :hypothesis? true}])))))

(defn loop-regimes
  "Each loop's regime = the regime of its member stocks' MEAN net (junkan pattern:
   loop drive = joint pressure of members, not a single dominant stock)."
  [pressures]
  (mapv (fn [{:keys [members] :as lp}]
          (let [nets (map #(:net (get pressures %)) members)
                drive (r3 (/ (reduce + 0.0 nets) (max 1 (count nets))))]
            (assoc (select-keys lp [:id :type :name])
                   :drive drive :regime (regime-of drive))))
        loops))

;; ── Meadows leverage candidates from the OPENING routes (never directives) ───
(def ^:private route->meadows
  ;; route → [meadows-level target-stock label]  (lower meadows # = deeper leverage)
  {:destake          [3 :single-shot-stakes   "Goals — replace one-shot selection (脱・一発勝負)"]
   :open-pathway     [4 :exam-pressure        "Add balancing feedback — alternative admission pathways"]
   :transparency-gap [6 :credential-signaling "Information flows — disclose opaque criteria"]
   :equity-watch     [5 :access-inequality    "Rules — access equity across region/income"]
   :monitor          [12 :exam-pressure       "Parameters — observe only"]})

(defn leverage-candidates
  "Rank the OPENING routes present in the assessment as Meadows leverage CANDIDATES.
   score = 0.6·depth + 0.4·mean-barrier-load, depth = (13 − meadows)/12.
   Each candidate is a disclosed hypothesis, NEVER a prescription (:prescription? false)."
  [exam-rows]
  (let [by-route (group-by :route exam-rows)]
    (->> (for [[route rows] by-route
               :let [[meadows stock label] (route->meadows route)]
               :when (and meadows (not= route :monitor))]
           (let [mbl (r3 (/ (reduce + 0.0 (map :barrier-load rows)) (count rows)))
                 depth (/ (- 13.0 meadows) 12.0)
                 score (r3 (+ (* 0.6 depth) (* 0.4 mbl)))]
             {:route route :meadows meadows :target-stock stock :label label
              :exemplar-count (count rows) :mean-barrier-load mbl
              :score score :prescription? false :hypothesis? true}))
         (sort-by (comp - :score))
         vec)))

(defn analyze
  "Full system-dynamics read. `exam-rows` = kanmon.analyze/assess output's \"exams\"
   (each {:exam … :route … :barrier-load …}). Returns
   {\"stocks\" {…} \"loops\" [...] \"leverage\" [...] \"headline\" {…}
    \"actuation-taken\" false}."
  [exam-rows]
  (let [exams (map :exam exam-rows)
        pressures (stock-pressures exams)
        lps (loop-regimes pressures)
        lev (leverage-candidates exam-rows)
        worst (apply max-key (comp :net val) pressures)
        vicious-loops (count (filter #(= :vicious (:regime %)) lps))]
    {"stocks" pressures
     "loops" lps
     "leverage" lev
     "headline" {:dominant-stock (key worst)
                 :dominant-net (:net (val worst))
                 :vicious-loops vicious-loops
                 :system-regime (regime-of (:net (val worst)))
                 :top-leverage (first lev)}
     "actuation-taken" false}))

;; ── EAVT datom emit (analysis-only — no :kanmon/actuate path exists) ─────────
(defn datoms [analysis]
  (let [sourcing ":representative"]
    (vec
     (concat
      (mapcat
       (fn [[stock {:keys [net widen-force narrow-force regime]}]]
         (let [e (str "stock:" (name stock))]
           [[":db/add" e ":kanmon.dyn.stock/net" net]
            [":db/add" e ":kanmon.dyn.stock/widen-force" widen-force]
            [":db/add" e ":kanmon.dyn.stock/narrow-force" narrow-force]
            [":db/add" e ":kanmon.dyn.stock/regime" (str regime)]
            [":db/add" e ":kanmon/derived" true]
            [":db/add" e ":kanmon/sourcing" sourcing]]))
       (get analysis "stocks"))
      (mapcat
       (fn [{:keys [id type regime drive]}]
         (let [e (str "loop:" id)]
           [[":db/add" e ":kanmon.dyn.loop/type" (str type)]
            [":db/add" e ":kanmon.dyn.loop/regime" (str regime)]
            [":db/add" e ":kanmon.dyn.loop/drive" drive]
            [":db/add" e ":kanmon/derived" true]]))
       (get analysis "loops"))
      (mapcat
       (fn [{:keys [route meadows target-stock score]}]
         (let [e (str "leverage:" (name route))]
           [[":db/add" e ":kanmon.dyn.lev/meadows" meadows]
            [":db/add" e ":kanmon.dyn.lev/target-stock" (str target-stock)]
            [":db/add" e ":kanmon.dyn.lev/score" score]
            [":db/add" e ":kanmon.dyn.lev/prescription" false]  ;; candidate, never a directive
            [":db/add" e ":kanmon/derived" true]]))
       (get analysis "leverage"))))))

(defn report [analysis]
  (let [hd (get analysis "headline")]
    (str/join
     "\n"
     (concat
      ["# kanmon 関門 — exam-gate SYSTEM DYNAMICS (analysis-only, ADR-2606291500)"
       (str "system-regime: " (name (:system-regime hd))
            "  dominant-stock: " (name (:dominant-stock hd)) " (net " (:dominant-net hd) ")"
            "  vicious-loops: " (:vicious-loops hd) "/" (count (get analysis "loops")))
       "(a causal READ — leverage points are disclosed hypotheses, never directives; no actuation)"
       ""
       "## stocks (net pressure: + widen / − narrow)"]
      (for [[s {:keys [net regime]}] (sort-by (comp - :net val) (get analysis "stocks"))]
        (str (format "%-22s" (name s)) " net=" (format "%+.3f" (double net)) "  " (name regime)))
      ["" "## causal loops"]
      (for [{:keys [id type regime drive]} (get analysis "loops")]
        (str (format "%-22s" id) " " (name type) " drive=" (format "%+.3f" (double drive)) "  " (name regime)))
      ["" "## Meadows leverage candidates (OPENING routes — hypotheses, NOT prescriptions)"]
      (for [{:keys [route meadows label score]} (get analysis "leverage")]
        (str "  M" meadows " score=" score "  " (name route) " — " label))))))

#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/kanmon/kotoba/seed.edn")
           exams (vec (filter #(= (:type %) :exam) (clojure.edn/read-string (slurp seed))))
           ;; build exam-rows via the analyze engine
           rows (get (az/assess exams) "exams")]
       (println (report (analyze rows))))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
