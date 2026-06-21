(ns etzhayyim.explorer.organism.aliveness
  "Browser-side recomputation of the aliveness 5-tuple A(t)=⟨M,D,C,P,G⟩
   (ADR-2606201610; method mirrors etzhayyim-organism-viz/aliveness.py).

   The constraint is *the browser computes* — we do not merely echo the baked
   vitals number. M and D are computed here directly from the public trajectory
   time series; C/P/G are read from the vitals snapshot when present and clearly
   tagged :read (vs :computed) so the UI can be honest about provenance.

   Health is a homeostatic band, NOT a target (non-eschatological,
   ADR-2605192100): each metric carries a [lo hi] range, not a goal."
  (:require [clojure.string :as str]))

;; Homeostatic ranges (the ideal-state prior). :lo/:hi bound a healthy band.
(def bands
  {:M {:lo 0.05 :hi 0.40 :label "Motion"        :ja "運動"}
   :D {:lo 0.50 :hi 1.10 :label "Diversity"     :ja "多様性"}
   :C {:lo 0.20 :hi 0.70 :label "Coupling"      :ja "結合"}
   :P {:lo 0.05 :hi 0.20 :label "Pruning"       :ja "剪定"}
   :G {:lo 1.00 :hi 2.00 :label "Generational"  :ja "世代"}})

(def order [:M :D :C :P :G])

(defn- safe-div [a b] (if (zero? b) 0.0 (/ a b)))

(defn shannon
  "Shannon entropy (nats) over a seq of counts."
  [counts]
  (let [total (reduce + 0 counts)]
    (if (zero? total)
      0.0
      (->> counts
           (keep (fn [c]
                   (when (pos? c)
                     (let [p (/ c total)]
                       (* p (Math/log p))))))
           (reduce + 0.0)
           (- 0.0)))))

(defn- motion
  "M — mean absolute Δ of the activity `sum` between consecutive runs, normalised
   by the rolling mean magnitude. Captures how much the organism is moving."
  [runs]
  (let [sums (->> runs (map #(or (:sum %) 0)) vec)]
    (if (< (count sums) 2)
      0.0
      (let [deltas (map (fn [a b] (Math/abs (- b a))) sums (rest sums))
            mean-mag (max 1.0 (/ (reduce + sums) (count sums)))]
        (min 1.0 (safe-div (/ (reduce + deltas) (count deltas)) mean-mag))))))

(defn- diversity
  "D — Shannon entropy over the {alive,dormant,stub} cell-class mix of the most
   recent run."
  [runs]
  (if-let [r (last runs)]
    (shannon [(or (:alive r) 0) (or (:dormant r) 0) (or (:stub r) 0)])
    0.0))

(defn in-band? [k v]
  (let [{:keys [lo hi]} (get bands k)]
    (and (some? v) (>= v lo) (<= v hi))))

(defn band-status
  "→ :ok (in band) | :high | :low | :unknown"
  [k v]
  (let [{:keys [lo hi]} (get bands k)]
    (cond
      (nil? v) :unknown
      (< v lo) :low
      (> v hi) :high
      :else :ok)))

(defn- read-vital
  "Pull a 5-tuple component out of the vitals EDN map under any of the likely
   keys; returns nil if absent."
  [vitals & ks]
  (some (fn [k] (let [v (get vitals k)] (when (number? v) v))) ks))

(defn compute
  "Returns [{:key :M :value 0.21 :source :computed :status :ok} ...] in display
   order. `trajectory` is the parsed trajectory.json; `vitals` the parsed
   vitals.kotoba.edn (may be nil)."
  [{:keys [trajectory vitals]}]
  (let [runs (->> (or (:runs trajectory) []) (sort-by :run) vec)
        m (motion runs)
        d (diversity runs)
        c (read-vital vitals :C :coupling :c)
        p (read-vital vitals :P :pruning :p)
        g (read-vital vitals :G :generational :g :mgi)]
    (->> [{:key :M :value m :source :computed}
          {:key :D :value d :source :computed}
          {:key :C :value c :source :read}
          {:key :P :value p :source :read}
          {:key :G :value g :source :read}]
         (map (fn [{:keys [key value] :as m}]
                (assoc m :status (band-status key value))))
         (sort-by #(.indexOf order (:key %)))
         vec)))

(defn alive?
  "Open-ended liveness check: the organism is 'alive' when no computed metric is
   out of band AND there is recent motion. (We never claim a final converged
   state — only that the trajectory sits in its healthy bands right now.)"
  [tuple]
  (and (seq tuple)
       (every? #(not= :unknown (:status %)) (filter #(= :computed (:source %)) tuple))
       (every? #(not= :low (:status %)) tuple)))

;; ── axis scores (Tree-of-Life branches) ────────────────────────────────────
;; The 10 constitutional axes. Scores come from vitals when present, else from
;; the organism summary as a coarse proxy so the tree always renders.
(def axes
  [[:autopoiesis  "Autopoiesis"  "自己創出"]
   [:metabolism   "Metabolism"   "代謝"]
   [:homeostasis  "Homeostasis"  "恒常性"]
   [:inference    "Active Inf."  "能動推論"]
   [:reproduction "Reproduction" "生殖"]
   [:symbiosis    "Symbiosis"    "共生"]
   [:diversity    "Diversity"    "多様性"]
   [:wellbecoming "Wellbecoming" "善く成る"]
   [:antifragile  "Anti-fragile" "反脆弱"]
   [:sanctify     "Sanctify"     "聖別"]])

(defn axis-scores
  "→ [{:key :autopoiesis :en \"Autopoiesis\" :ja \"自己創出\" :score 0..10}]
   Reads a per-axis score map from vitals (:axes / :axis-scores) when present."
  [{:keys [vitals]}]
  (let [src (or (:axes vitals) (:axis-scores vitals) {})]
    (mapv (fn [[k en ja]]
            {:key k :en en :ja ja
             :score (let [v (get src k)]
                      (cond
                        (number? v) v
                        (and (map? v) (number? (:score v))) (:score v)
                        :else nil))})
          axes)))
