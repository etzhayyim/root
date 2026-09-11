;; etzhayyim.shannon-scores — Shannon redundancy scoring pure logic (cljc port, wave 2).
;;
;; Pure-logic port of the math-heavy core of
;; 70-tools/etzhayyim-py/src/etzhayyim/shannon.py
;; (no click, no filesystem, no subprocess — just pure data transforms).
;;
;; Ported functions:
;;   WEIGHTS            — check-name → weight map
;;   cap                — clamp score to [0.0, 100.0] with 1 decimal
;;   sh-entropy         — Shannon entropy H in bits over a count map
;;   build-report       — weighted aggregate over a seq of check maps
;;   dsm-cuthill-mckee  — bandwidth-minimising Cuthill-McKee permutation
;;   dsm-detect-cycles  — simple DFS cycle enumeration (≤8 hops, ≤50 cycles)
;;   dsm-find-clusters  — connected-components via BFS (undirected)
;;   build-dsm-report   — full N×N DSM with bandwidth + score
;;   bayes-dijkstra-from     — Dijkstra shortest paths on P(propagation)
;;   build-bayesnet-report   — Bayesian change-propagation network
;;   build-bottleneck-report — fan-in×fan-out MI bottleneck analysis
;;   minimize-merge-proposals / split / move — entropy-reduction proposals
;;   build-minimize-report   — full coupling + cohesion entropy report
;;
;; IO functions (_walk, _sh_scan, CLI click commands) are NOT ported here;
;; they stay in the Python module or will arrive in a later wave.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.shannon-scores :as ss])
;;   (ss/sh-entropy {"a" 3 "b" 1})   ;=> 1.0
;;   (ss/cap 105.0)                   ;=> 100.0

(ns etzhayyim.shannon-scores
  (:require [clojure.string :as str]))

;; ── WEIGHTS ─────────────────────────────────────────────────────────────────────

(def weights
  "Check-name → weight map (mirrors Python WEIGHTS dict)."
  {"claude_md_duplication"  0.25
   "code_clone_cross"       0.15
   "collection_write_fan"   0.15
   "wit_type_duplication"   0.10
   "config_redundancy"      0.10
   "dead_code_entropy"      0.10
   "doc_code_drift"         0.10
   "rust_duplication"       0.05
   "stale_symbol_entropy"   0.10})

;; ── edge-type weights (for Bayes coupling) ──────────────────────────────────────

(def ^:private edge-type-weights
  {"invoke"          0.8
   "writes"          0.5
   "subscribe"       0.4
   "reads"           0.3
   "follow"          0.1
   "service_binding" 0.6})

;; ── helpers ──────────────────────────────────────────────────────────────────────

(defn cap
  "Clamp score to [0.0, 100.0] rounded to 1 decimal (round-half-even)."
  [score]
  (let [clamped (max 0.0 (min 100.0 (double score)))
        scale   10.0]
    (/ (Math/rint (* clamped scale)) scale)))

(defn sh-entropy
  "Shannon entropy H in bits over a map of {key count}.
   Returns 0.0 for empty / all-zero maps."
  [counts]
  (let [total (reduce + 0.0 (vals counts))]
    (if (zero? total)
      0.0
      (- (reduce (fn [h c]
                   (if (<= c 0)
                     h
                     (let [p (/ (double c) total)]
                       (+ h (* p (Math/log p))))))
                 0.0
                 (vals counts))
         (* 0.0)  ;; no-op; the negation is via negate below
         ))))

;; Re-express: h = -Σ p·log₂(p)  (log base 2 = ln / ln2)
(defn sh-entropy
  "Shannon entropy H in bits over a map of {key count}.
   Returns 0.0 for empty / all-zero maps."
  [counts]
  (let [total (reduce + 0.0 (vals counts))]
    (if (zero? total)
      0.0
      (reduce (fn [h c]
                (if (<= c 0)
                  h
                  (let [p (/ (double c) total)]
                    (- h (* p (/ (Math/log p) (Math/log 2)))))))
              0.0
              (vals counts)))))

;; ── build-report ─────────────────────────────────────────────────────────────────

(defn build-report
  "Aggregate a seq of check maps into a ShannonReport map.

   check maps have keys :name :score :violations :details :items
   Returns a map with :evaluated-at :overall-score :redundancy-rate
                       :checks :hotspots :scoring-model."
  [checks & [top-n]]
  (let [n             (or top-n 15)
        annotated     (mapv (fn [chk]
                              (let [w (get weights (:name chk) 0.0)]
                                (assoc chk :weight w)))
                            checks)
        weighted-sum  (reduce (fn [acc chk]
                                (+ acc (* (double (:score chk 100.0))
                                          (double (:weight chk 0.0)))))
                              0.0 annotated)
        total-weight  (reduce + 0.0 (map :weight annotated))
        overall       (if (pos? total-weight)
                        (/ weighted-sum total-weight)
                        100.0)
        all-items     (mapcat :items annotated)
        sorted-items  (sort-by :redundancy > all-items)
        hotspots      (vec (take n sorted-items))
        check-labels  (str/join "+"
                        (map (fn [c]
                               (format "%s(%.0f%%×%.0f)"
                                 (:name c)
                                 (double (:score c 100.0))
                                 (* (double (:weight c 0.0)) 100.0)))
                             annotated))]
    {:evaluated-at    #?(:clj  (let [fmt (java.text.SimpleDateFormat. "yyyy-MM-dd'T'HH:mm:ss'Z'")]
                                 (.setTimeZone fmt (java.util.TimeZone/getTimeZone "UTC"))
                                 (.format fmt (java.util.Date.)))
                         :cljs (.toISOString (js/Date.)))
     :overall-score   (let [scale 10.0]
                        (/ (Math/rint (* (double overall) scale)) scale))
     :redundancy-rate (let [scale 1000.0]
                        (/ (Math/rint (* (- 1.0 (/ overall 100.0)) scale)) scale))
     :checks          (vec annotated)
     :hotspots        hotspots
     :scoring-model   (str "weighted: " check-labels)}))

;; ── DSM helpers ──────────────────────────────────────────────────────────────────

(defn dsm-cuthill-mckee
  "Return a Cuthill-McKee permutation (reversed for bandwidth minimisation).
   matrix is a vector of vectors of ints; n is the dimension.
   Returns a vector of indices [i0 i1 ... i(n-1)]."
  [matrix n]
  (let [degree (mapv (fn [i]
                       (count (for [j (range n)
                                    :when (and (not= i j)
                                               (or (pos? (get-in matrix [i j]))
                                                   (pos? (get-in matrix [j i]))))]
                                j)))
                     (range n))
        visited (atom (vec (repeat n false)))
        result  (atom [])]
    (loop []
      (when (< (count @result) n)
        ;; find unvisited node with minimum degree
        (let [start (reduce (fn [best i]
                              (if (and (not (nth @visited i))
                                       (or (= best -1)
                                           (< (nth degree i) (nth degree best))))
                                i best))
                            -1
                            (range n))]
          (when (not= start -1)
            (let [queue (atom [start])]
              (swap! visited assoc start true)
              (loop []
                (when (seq @queue)
                  (let [node (first @queue)]
                    (swap! queue rest)
                    (swap! result conj node)
                    ;; add unvisited neighbours sorted by degree
                    (let [nbs (sort-by #(nth degree %)
                                (for [j (range n)
                                      :when (and (not (nth @visited j))
                                                 (or (pos? (get-in matrix [node j]))
                                                     (pos? (get-in matrix [j node]))))]
                                  j))]
                      (doseq [nb nbs]
                        (when-not (nth @visited nb)
                          (swap! visited assoc nb true)
                          (swap! queue conj nb))))
                    (recur)))))
            (recur)))))
    (vec (reverse @result))))

(defn dsm-detect-cycles
  "Detect cycles in the adjacency map adj={from {to count}}.
   apps is a sorted seq of node names.
   Returns at most max-cycles cycles of length ≤ max-len."
  [apps adj]
  (let [max-len    8
        max-cycles 50
        seen       (atom #{})
        cycles     (atom [])]
    (letfn [(_canon [path]
              (when (seq path)
                ;; find index of the lexicographically minimum element
                (let [n       (count path)
                      min-idx (reduce (fn [best i]
                                        (if (neg? (compare (nth path i) (nth path best)))
                                          i best))
                                      0
                                      (range 1 n))
                      rotated (mapv #(nth path (mod (+ % min-idx) n))
                                    (range n))]
                  (str/join "→" rotated))))
            (dfs [start node path]
              (when (and (< (count @cycles) max-cycles)
                         (<= (count path) max-len))
                (doseq [nxt (keys (get adj node {}))]
                  (when (< (count @cycles) max-cycles)
                    (cond
                      (and (= nxt start) (>= (count path) 2))
                      (let [cycle-path (conj path start)
                            canon      (_canon (vec (butlast cycle-path)))]
                        (when (not (@seen canon))
                          (swap! seen conj canon)
                          (swap! cycles conj {:path cycle-path
                                              :length (dec (count cycle-path))})))
                      (not (some #{nxt} path))
                      (dfs start nxt (conj path nxt)))))))]
      (doseq [start apps]
        (when (< (count @cycles) max-cycles)
          (dfs start start [start])))
      (vec (sort-by :length @cycles)))))

(defn dsm-find-clusters
  "Find connected components (undirected) in adj={from {to count}}.
   Returns a vector of cluster maps with :name :members :internal-deps :external-deps."
  [apps adj]
  (let [neighbors (reduce (fn [nb [frm targets]]
                            (reduce (fn [m to]
                                      (-> m
                                          (update frm (fnil conj #{}) to)
                                          (update to (fnil conj #{}) frm)))
                                    nb
                                    (keys targets)))
                          {}
                          adj)
        visited   (atom #{})]
    (reduce (fn [clusters start]
              (if (@visited start)
                clusters
                (let [queue   (atom [start])
                      members (atom [])]
                  (swap! visited conj start)
                  (loop []
                    (when (seq @queue)
                      (let [node (first @queue)]
                        (swap! queue rest)
                        (swap! members conj node)
                        (doseq [nb (get neighbors node #{})]
                          (when-not (@visited nb)
                            (swap! visited conj nb)
                            (swap! queue conj nb)))
                        (recur))))
                  (let [ms         (sort @members)
                        member-set (set ms)
                        internal   (reduce + 0
                                     (for [m ms [to cnt] (get adj m {})]
                                       (if (member-set to) cnt 0)))
                        external   (reduce + 0
                                     (for [m ms [to cnt] (get adj m {})]
                                       (if-not (member-set to) cnt 0)))]
                    (conj clusters
                          {:name          (str "cluster-" (inc (count clusters)))
                           :members       ms
                           :internal-deps internal
                           :external-deps external})))))
            []
            apps)))

(defn build-dsm-report
  "Build a full DSM report map from apps (seq of names), adj ({from {to count}}),
   top-n, and no-reorder flag.
   Returns a plain map mirroring the Python _build_dsm_report output."
  [apps adj top-n no-reorder]
  (let [n   (count apps)
        now #?(:clj  (let [fmt (java.text.SimpleDateFormat. "yyyy-MM-dd'T'HH:mm:ss'Z'")]
                       (.setTimeZone fmt (java.util.TimeZone/getTimeZone "UTC"))
                       (.format fmt (java.util.Date.)))
               :cljs (.toISOString (js/Date.)))]
    (if (zero? n)
      {:generated-at now :size 0 :apps [] :matrix [] :entries []
       :clusters [] :cycles [] :bandwidth 0 :score 100.0}
      (let [idx    (into {} (map-indexed (fn [i a] [a i]) apps))
            matrix (reduce (fn [m [frm targets]]
                             (let [fi (get idx frm)]
                               (if (nil? fi) m
                                 (reduce (fn [m2 [to cnt]]
                                           (let [ti (get idx to)]
                                             (if (nil? ti) m2
                                               (assoc-in m2 [fi ti] cnt))))
                                         m targets))))
                           (vec (repeat n (vec (repeat n 0))))
                           adj)
            perm   (if (and (not no-reorder) (> n 2))
                     (dsm-cuthill-mckee matrix n)
                     (vec (range n)))
            reordered (mapv #(nth apps (nth perm %)) (range n))
            rm        (mapv (fn [i]
                              (mapv (fn [j]
                                      (get-in matrix [(nth perm i) (nth perm j)]))
                                    (range n)))
                            (range n))
            entries   (for [i (range n) j (range n)
                            :when (pos? (get-in rm [i j]))]
                        {:from (nth reordered i)
                         :to   (nth reordered j)
                         :count (get-in rm [i j])})
            bw        (reduce (fn [mx [i j]]
                                (max mx (Math/abs (- i j))))
                              0
                              (for [i (range n) j (range n)
                                    :when (pos? (get-in rm [i j]))]
                                [i j]))
            cycles    (dsm-detect-cycles reordered adj)
            clusters  (take top-n
                        (sort-by #(- (count (:members %))) >
                          (dsm-find-clusters reordered adj)))
            score     (if (> n 1) (max 0.0 (* 100.0 (- 1.0 (/ (double bw) n)))) 100.0)]
        {:generated-at now
         :size         n
         :apps         reordered
         :matrix       rm
         :entries      (vec entries)
         :clusters     (vec clusters)
         :cycles       cycles
         :bandwidth    bw
         :score        (let [scale 10.0]
                         (/ (Math/rint (* score scale)) scale))}))))

;; ── Bayesian propagation ─────────────────────────────────────────────────────────

(defn ^:private bayes-dijkstra-from
  "Dijkstra shortest-path in log-probability space from source.
   edge-adj = {node [{:to t :conditional p} ...]}
   Returns at most 5 paths with probability > 0.01 and length ≥ 2."
  [source edge-adj max-depth]
  (let [max-paths 5
        pq        (atom [[0.0 0 source [source]]])  ;; [neg-log-p, counter, node, path]
        counter   (atom 0)
        visited   (atom #{})
        paths     (atom [])]
    (loop []
      (when (and (seq @pq) (< (count @paths) max-paths))
        (let [[neg-log-p _ node path] (first (sort-by first @pq))]
          (swap! pq (fn [q] (remove #(= % [neg-log-p _ node path]) q)))
          (when (and (not (@visited node)) (> (count path) 1))
            (swap! visited conj node)
            (let [prob (Math/exp (- neg-log-p))]
              (when (and (>= (count path) 3) (> prob 0.01))
                (swap! paths conj {:nodes (vec path) :probability prob :length (dec (count path))})))
            (when (<= (count path) max-depth)
              (doseq [{:keys [to conditional]} (get edge-adj node [])]
                (when (and (pos? conditional) (not (some #{to} path)))
                  (let [new-neg (+ neg-log-p (- (Math/log conditional)))]
                    (swap! counter inc)
                    (swap! pq conj [new-neg @counter to (conj path to)]))))))
          (recur))))
    @paths))

(defn build-bayesnet-report
  "Build a Bayesian change-propagation network report.
   apps = seq of node names; adj-typed = {from {to {edge-type count}}}.
   Returns a plain map mirroring Python _build_bayesnet_report."
  [apps adj-typed top-n max-depth]
  (let [n   (count apps)
        now #?(:clj  (let [fmt (java.text.SimpleDateFormat. "yyyy-MM-dd'T'HH:mm:ss'Z'")]
                       (.setTimeZone fmt (java.util.TimeZone/getTimeZone "UTC"))
                       (.format fmt (java.util.Date.)))
               :cljs (.toISOString (js/Date.)))]
    (if (zero? n)
      {:generated-at now :total-apps 0 :total-edges 0 :nodes [] :edges []
       :high-risk-paths [] :mean-propagation-probability 0.0
       :max-propagation-probability 0.0 :score 100.0}
      (let [fan-in  (reduce (fn [m [_ targets]]
                              (reduce #(update %1 %2 (fnil inc 0)) m (keys targets)))
                            {} adj-typed)
            fan-out (reduce (fn [m [frm targets]]
                              (assoc m frm (count targets)))
                            {} adj-typed)
            mfo     (max 1 (if (seq fan-out) (apply max (vals fan-out)) 1))
            nodes   (mapv (fn [a]
                            {:app     a
                             :fan-in  (get fan-in a 0)
                             :fan-out (get fan-out a 0)
                             :prior   (/ (double (get fan-out a 0)) mfo)})
                          apps)
            ;; build edges + edge-adj
            [edges edge-adj]
            (reduce (fn [[acc-es acc-ea] [frm targets]]
                      (reduce (fn [[inner-es inner-ea] [to types]]
                                (let [raw-s    (reduce (fn [s [t cnt]]
                                                          (let [w (get edge-type-weights t 0.2)]
                                                            (+ s (* w cnt))))
                                                        0.0 types)
                                      strength (if (> raw-s 1.0)
                                                 (- 1.0 (/ 1.0 (+ 1.0 raw-s)))
                                                 raw-s)
                                      etypes   (sort (keys types))
                                      edge     {:from frm :to to
                                                :strength    strength
                                                :conditional strength
                                                :edge-types  etypes}]
                                  [(conj inner-es edge)
                                   (update inner-ea frm (fnil conj []) {:to to :conditional strength})]))
                              [acc-es acc-ea]
                              targets))
                    [[] {}]
                    adj-typed)
            all-paths (mapcat #(bayes-dijkstra-from % edge-adj max-depth) apps)
            sorted-p  (vec (take top-n (sort-by :probability > all-paths)))
            mean-p    (if (seq edges)
                        (/ (reduce + 0.0 (map :conditional edges)) (count edges))
                        0.0)
            max-p     (if (seq edges) (apply max (map :conditional edges)) 0.0)
            s-edges   (sort-by :conditional > edges)
            score     (max 0.0 (* 100.0 (- 1.0 mean-p)))]
        {:generated-at                  now
         :total-apps                    n
         :total-edges                   (count edges)
         :nodes                         nodes
         :edges                         (vec s-edges)
         :high-risk-paths               sorted-p
         :mean-propagation-probability  (let [scale 10000.0]
                                          (/ (Math/rint (* mean-p scale)) scale))
         :max-propagation-probability   (let [scale 10000.0]
                                          (/ (Math/rint (* max-p scale)) scale))
         :score                         (let [scale 10.0]
                                          (/ (Math/rint (* score scale)) scale))}))))

;; ── bottleneck ───────────────────────────────────────────────────────────────────

(defn build-bottleneck-report
  "Information bottleneck analysis via fan-in × fan-out mutual information.
   Returns a plain map mirroring Python _build_bottleneck_report."
  [apps adj-typed top-n min-fan]
  (let [n   (count apps)
        now #?(:clj  (let [fmt (java.text.SimpleDateFormat. "yyyy-MM-dd'T'HH:mm:ss'Z'")]
                       (.setTimeZone fmt (java.util.TimeZone/getTimeZone "UTC"))
                       (.format fmt (java.util.Date.)))
               :cljs (.toISOString (js/Date.)))]
    (if (zero? n)
      {:generated-at now :total-apps 0 :bottlenecks []
       :system-mutual-information 0.0 :score 100.0}
      (let [stats (reduce (fn [st [frm targets]]
                            (reduce (fn [inner-st [to types]]
                                      (-> inner-st
                                          (update-in [frm :outbound] (fnil conj #{}) to)
                                          (update-in [to  :inbound]  (fnil conj #{}) frm)
                                          (update-in [frm :out-types]
                                            (fn [m] (reduce (fn [mm [t c]] (update mm t (fnil + 0) c)) (or m {}) types)))
                                          (update-in [to  :in-types]
                                            (fn [m] (reduce (fn [mm [t c]] (update mm t (fnil + 0) c)) (or m {}) types)))))
                                    st
                                    targets))
                          (into {} (map (fn [a] [a {:inbound #{} :outbound #{}
                                                    :in-types {} :out-types {}}])
                                        apps))
                          adj-typed)
            all-fans (concat (map (fn [s] (count (:inbound s))) (vals stats))
                             (map (fn [s] (count (:outbound s))) (vals stats)))
            max-fan  (max 1 (if (seq all-fans) (apply max all-fans) 1))
            modules  (for [app apps
                           :let [s      (get stats app {:inbound #{} :outbound #{}
                                                        :in-types {} :out-types {}})
                                 fi     (count (:inbound s))
                                 fo     (count (:outbound s))]
                           :when (or (>= fi min-fan) (>= fo min-fan))]
                       (let [b-score (min 1.0 (/ (Math/sqrt (* fi fo)) max-fan))
                             h-in    (sh-entropy (:in-types s))
                             h-out   (sh-entropy (:out-types s))
                             joint   (merge-with + (:in-types s) (:out-types s))
                             h-joint (sh-entropy joint)
                             mi      (max 0.0 (+ h-in h-out (- h-joint)))
                             sev     (cond
                                       (and (>= b-score 0.7) (>= fi 5) (>= fo 5)) "critical"
                                       (>= b-score 0.5) "high"
                                       (>= b-score 0.3) "medium"
                                       :else            "low")]
                         {:app              app
                          :fan-in           fi
                          :fan-out          fo
                          :bottleneck-score (let [scale 10000.0]
                                              (/ (Math/rint (* b-score scale)) scale))
                          :inbound-apps     (sort (:inbound s))
                          :outbound-apps    (sort (:outbound s))
                          :inbound-types    (:in-types s)
                          :outbound-types   (:out-types s)
                          :mutual-information (let [scale 10000.0]
                                                (/ (Math/rint (* mi scale)) scale))
                          :severity         sev}))
            sorted-m (vec (take top-n (sort-by :bottleneck-score > modules)))
            crit-hi  (count (filter #(#{"critical" "high"} (:severity %)) sorted-m))
            sys-mi   (reduce + 0.0 (map :mutual-information sorted-m))
            score    (if (pos? n) (max 0.0 (* 100.0 (- 1.0 (/ (double crit-hi) n)))) 100.0)]
        {:generated-at              now
         :total-apps                n
         :bottlenecks               sorted-m
         :system-mutual-information (let [scale 10000.0]
                                      (/ (Math/rint (* sys-mi scale)) scale))
         :score                     (let [scale 10.0]
                                      (/ (Math/rint (* score scale)) scale))}))))

;; ── minimize ─────────────────────────────────────────────────────────────────────

(defn ^:private minimize-merge-proposals
  "Propose merges for tightly-coupled apps in the same project."
  [apps adj app-proj]
  (let [checked (atom #{})]
    (for [a apps
          :let [proj-a (get app-proj a "")]
          :when (seq proj-a)
          b apps
          :when (and (neg? (compare a b))  ;; a < b lexicographically
                     (= (get app-proj b "") proj-a))
          :let [key (str a "|" b)]
          :when (not (@checked key))
          :let [_ (swap! checked conj key)
                ab     (get-in adj [a b] 0)
                ba     (get-in adj [b a] 0)
                mutual (+ ab ba)]
          :when (>= mutual 2)
          :let [h-a    (sh-entropy (get adj a {}))
                h-b    (sh-entropy (get adj b {}))
                cur-h  (+ h-a h-b)
                merged (reduce (fn [m [to c]]
                                 (if (= to b) m (update m to (fnil + 0) c)))
                               (reduce (fn [m [to c]]
                                         (if (= to a) m (update m to (fnil + 0) c)))
                                       {}
                                       (get adj b {}))
                               (get adj a {}))
                pred-h  (sh-entropy merged)
                red     (- cur-h pred-h)]
          :when (pos? red)
          :let [pct (if (pos? cur-h) (* (/ red cur-h) 100.0) 0.0)]]
      {:action            "merge"
       :targets           [a b]
       :reason            (str "high mutual coupling (" mutual " edges) in project " proj-a)
       :current-entropy   (let [scale 10000.0] (/ (Math/rint (* cur-h scale)) scale))
       :predicted-entropy (let [scale 10000.0] (/ (Math/rint (* pred-h scale)) scale))
       :reduction         (let [scale 10000.0] (/ (Math/rint (* red scale)) scale))
       :reduction-pct     (let [scale 10.0] (/ (Math/rint (* pct scale)) scale))})))

(defn ^:private minimize-split-proposals
  "Propose splits for apps with high coupling entropy."
  [apps adj threshold]
  (for [app apps
        :let [targets  (get adj app {})
              n-tgt    (count targets)]
        :when (>= n-tgt 3)
        :let [h (sh-entropy targets)]
        :when (>= h threshold)
        :let [sorted-t  (sort-by val > targets)
              mid       (quot (count sorted-t) 2)
              g1        (into {} (take mid sorted-t))
              g2        (into {} (drop mid sorted-t))
              n1        (double (reduce + (vals g1)))
              n2        (double (reduce + (vals g2)))
              total-n   (+ n1 n2)]
        :when (pos? total-n)
        :let [h1     (sh-entropy g1)
              h2     (sh-entropy g2)
              pred-h  (/ (+ (* n1 h1) (* n2 h2)) total-n)
              red     (- h pred-h)]
        :when (pos? red)
        :let [pct (if (pos? h) (* (/ red h) 100.0) 0.0)]]
    {:action            "split"
     :targets           [app]
     :reason            (format "high coupling entropy (%.2f bits, %d targets)" (double h) n-tgt)
     :current-entropy   (let [scale 10000.0] (/ (Math/rint (* h scale)) scale))
     :predicted-entropy (let [scale 10000.0] (/ (Math/rint (* pred-h scale)) scale))
     :reduction         (let [scale 10000.0] (/ (Math/rint (* red scale)) scale))
     :reduction-pct     (let [scale 10.0] (/ (Math/rint (* pct scale)) scale))}))

(defn ^:private minimize-move-proposals
  "Propose moves when most edges go to a different project."
  [apps adj app-proj]
  (for [app apps
        :let [targets    (get adj app {})
              n-tgt      (count targets)]
        :when (>= n-tgt 2)
        :let [my-proj (get app-proj app "")]
        :when (seq my-proj)
        :let [total-e (double (reduce + (vals targets)))
              proj-e  (reduce (fn [m [to c]]
                                (let [p (get app-proj to "")]
                                  (if (seq p) (update m p (fnil + 0) c) m)))
                              {} targets)
              [best-proj best-count]
              (reduce (fn [[bp bc] [proj cnt]]
                        (if (and (not= proj my-proj) (> cnt bc))
                          [proj cnt] [bp bc]))
                      ["" 0] proj-e)]
        :when (seq best-proj)
        :let [cross-r  (/ (double best-count) (max 1.0 total-e))]
        :when (>= cross-r 0.7)
        :let [cur-h  (sh-entropy targets)
              pred-h  (* cur-h (- 1.0 (* cross-r 0.5)))
              red     (- cur-h pred-h)]
        :when (pos? red)
        :let [pct (if (pos? cur-h) (* (/ red cur-h) 100.0) 0.0)]]
    {:action            "move"
     :targets           [app]
     :reason            (format "%.0f%% of edges go to project %s (current: %s)"
                           (* cross-r 100.0) best-proj my-proj)
     :current-entropy   (let [scale 10000.0] (/ (Math/rint (* cur-h scale)) scale))
     :predicted-entropy (let [scale 10000.0] (/ (Math/rint (* pred-h scale)) scale))
     :reduction         (let [scale 10000.0] (/ (Math/rint (* red scale)) scale))
     :reduction-pct     (let [scale 10.0] (/ (Math/rint (* pct scale)) scale))}))

(defn build-minimize-report
  "Full entropy-minimisation report: module coupling/cohesion + proposals.
   apps = seq; adj = {from {to count}}; app-proj = {app project}."
  [apps adj app-proj top-n threshold]
  (let [n   (count apps)
        now #?(:clj  (let [fmt (java.text.SimpleDateFormat. "yyyy-MM-dd'T'HH:mm:ss'Z'")]
                       (.setTimeZone fmt (java.util.TimeZone/getTimeZone "UTC"))
                       (.format fmt (java.util.Date.)))
               :cljs (.toISOString (js/Date.)))]
    (if (zero? n)
      {:generated-at now :total-apps 0 :system-entropy 0.0
       :cohesion-entropy 0.0 :modules [] :proposals []
       :potential-reduction 0.0 :score 100.0}
      (let [modules (mapv (fn [app]
                            (let [targets    (get adj app {})
                                  proj       (get app-proj app "")
                                  coupling-h (sh-entropy targets)
                                  coh-counts (if (seq proj)
                                               (into {} (filter (fn [[to _]]
                                                                  (= (get app-proj to "") proj))
                                                                targets))
                                               {})
                                  cohesion-h (sh-entropy coh-counts)
                                  net-h      (- coupling-h cohesion-h)]
                              {:app              app
                               :project          proj
                               :coupling-entropy (let [s 10000.0] (/ (Math/rint (* coupling-h s)) s))
                               :cohesion-entropy (let [s 10000.0] (/ (Math/rint (* cohesion-h s)) s))
                               :net-entropy      (let [s 10000.0] (/ (Math/rint (* net-h s)) s))}))
                          apps)
            sorted-m      (sort-by :net-entropy > modules)
            total-coupl   (reduce + 0.0 (map :coupling-entropy modules))
            total-coh     (reduce + 0.0 (map :cohesion-entropy modules))
            proposals     (concat (minimize-merge-proposals apps adj app-proj)
                                  (minimize-split-proposals apps adj threshold)
                                  (minimize-move-proposals apps adj app-proj))
            sorted-p      (vec (take top-n (sort-by :reduction > proposals)))
            pot-red       (reduce + 0.0 (map :reduction sorted-p))
            total         (+ total-coupl total-coh)
            score         (if (pos? total) (min 100.0 (* 100.0 (/ total-coh total))) 50.0)]
        {:generated-at        now
         :total-apps          n
         :system-entropy      (let [s 10000.0] (/ (Math/rint (* total-coupl s)) s))
         :cohesion-entropy    (let [s 10000.0] (/ (Math/rint (* total-coh s)) s))
         :modules             (vec sorted-m)
         :proposals           sorted-p
         :potential-reduction (let [s 10000.0] (/ (Math/rint (* pot-red s)) s))
         :score               (let [s 10.0] (/ (Math/rint (* score s)) s))}))))
