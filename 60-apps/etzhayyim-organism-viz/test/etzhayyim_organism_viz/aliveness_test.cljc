(ns etzhayyim-organism-viz.aliveness-test
  "Port of tests/test_aliveness.py — drives the aliveness 5-tuple A(t) through
  tmp-repo fixtures (the same Shannon-entropy / Pearson / axis-Δ / tended-cell
  fixtures as the Python pytest suite). Pure fns + the #?(:clj) FS scanners."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [etzhayyim-organism-viz.aliveness :as av]))

(defn- approx
  ([a b] (approx a b 1e-9))
  ([a b eps] (< (Math/abs (- (double a) (double b))) eps)))

#?(:clj
   (do
     (defn- tmp-dir! []
       (str (java.nio.file.Files/createTempDirectory
             "alive" (make-array java.nio.file.attribute.FileAttribute 0))))

     (defn- mkdirs! [^String path] (.mkdirs (java.io.File. path)) path)

     (defn- spit! [^String path ^String body]
       (let [f (java.io.File. path)]
         (.mkdirs (.getParentFile f))
         (spit f body)
         path))

     (defn- write-cycle!
       "Mirror test_aliveness.write_cycle — an axis table matching _AXIS_ROW."
       [obs n axes]
       (let [rows (str/join "\n"
                            (map-indexed (fn [i [name score]]
                                           (format "| %d | %s | %d/10 | note |" (inc i) name score))
                                         axes))
             body (str "# observation cycle " n "\n\n| # | Axis | Score | Notes |\n|---|---|---|---|\n" rows "\n")]
         (spit! (str obs "/obs-cycle-" n ".md") body)))

     (defn- make-cell!
       "Mirror test_aliveness.make_cell — body=nil → no cell.py."
       [repo name body]
       (let [d (mkdirs! (str repo "/orgs/kotoba-lang/kotodama/cells/" name))]
         (when body (spit! (str d "/cell.py") body))
         d))

     (defn- rm-rf! [^String path]
       (doseq [f (reverse (file-seq (java.io.File. path)))] (.delete ^java.io.File f)))

     ;; ── _read_cycles + AliveTuple ────────────────────────────────────────────
     (deftest read-cycles-parses-axis-tables-in-order
       (let [tmp (tmp-dir!) obs (mkdirs! (str tmp "/_observations"))]
         (try
           (write-cycle! obs 2 [["Motion" 7] ["Diversity" 5]])
           (write-cycle! obs 1 [["Motion" 6]])
           (let [cycles (av/read-cycles obs)]
             (is (= [1 2] (mapv first cycles)) "sorted by filename")
             (is (= {"motion" 7 "diversity" 5} (second (nth cycles 1))) "names lowercased"))
           (finally (rm-rf! tmp)))))

     (deftest diversity-is-log-n-for-n-distinct-cells
       (let [tmp (tmp-dir!)]
         (try
           (doseq [nm ["a" "b" "c" "d"]] (make-cell! tmp nm "x"))
           (let [[h notes] (av/diversity tmp)]
             (is (approx h (Math/log 4)) "each count 1 → H = ln N")
             (is (str/includes? (first notes) "distinct cells")))
           (finally (rm-rf! tmp)))))

     (deftest diversity-zero-when-cells-dir-missing
       (let [tmp (tmp-dir!)]
         (try
           (let [[h notes] (av/diversity tmp)]
             (is (= 0.0 h))
             (is (str/includes? (first notes) "missing")))
           (finally (rm-rf! tmp)))))

     (deftest coupling-perfect-positive-correlation-is-one
       (let [tmp (tmp-dir!) obs (mkdirs! (str tmp "/_observations"))]
         (try
           (doseq [[n v] [[1 3] [2 6] [3 9]]] (write-cycle! obs n [["Alpha" v] ["Beta" v]]))
           (is (approx (first (av/coupling obs)) 1.0))
           (finally (rm-rf! tmp)))))

     (deftest coupling-perfect-negative-correlation-is-minus-one
       (let [tmp (tmp-dir!) obs (mkdirs! (str tmp "/_observations"))]
         (try
           (doseq [[n a b] [[1 1 9] [2 5 5] [3 9 1]]] (write-cycle! obs n [["Alpha" a] ["Beta" b]]))
           (is (approx (first (av/coupling obs)) -1.0))
           (finally (rm-rf! tmp)))))

     (deftest coupling-undefined-under-three-cycles
       (let [tmp (tmp-dir!) obs (mkdirs! (str tmp "/_observations"))]
         (try
           (write-cycle! obs 1 [["Alpha" 1] ["Beta" 2]])
           (write-cycle! obs 2 [["Alpha" 2] ["Beta" 3]])
           (let [[c notes] (av/coupling obs)]
             (is (= 0.0 c))
             (is (str/includes? (first notes) "<3 cycles")))
           (finally (rm-rf! tmp)))))

     (deftest motion-axis-delta-mean
       (let [tmp (tmp-dir!) obs (mkdirs! (str tmp "/_observations"))]
         (try
           (write-cycle! obs 1 [["Motion" 4]])
           (write-cycle! obs 2 [["Motion" 6]])
           (write-cycle! obs 3 [["Motion" 9]])
           (is (approx (first (av/motion obs nil)) 2.5) "deltas 2,3 → mean 2.5; repo=nil → no creation")
           (finally (rm-rf! tmp)))))

     (deftest pruning-ratio-counts-documented-nontrivial-cells
       (let [tmp (tmp-dir!)]
         (try
           (make-cell! tmp "tended1" (str "\"\"\"doc\"\"\"\n" (apply str (repeat 100 "x = 1\n"))))
           (make-cell! tmp "tended2" (str "\"\"\"doc\"\"\"\n" (apply str (repeat 100 "y = 2\n"))))
           (make-cell! tmp "stub" "x = 1\n")
           (make-cell! tmp "empty" nil)
           (let [[p notes] (av/pruning tmp)]
             (is (approx p (/ 2.0 4)))
             (is (str/includes? (first notes) "2/4")))
           (finally (rm-rf! tmp)))))

     (deftest generational-base-one-with-lands-present
       (let [tmp (tmp-dir!)]
         (try
           (spit! (str tmp "/LANDS.md") "inalienable")
           (is (approx (first (av/generational tmp)) 1.0))
           (finally (rm-rf! tmp)))))

     (deftest generational-lifts-005-per-ten-gen-marks
       (let [tmp (tmp-dir!) obs (mkdirs! (str tmp "/_observations"))]
         (try
           (spit! (str tmp "/LANDS.md") "x")
           (spit! (str obs "/marks-cycle-1.md") (apply str (repeat 20 "Gen 0 ")))
           (is (approx (first (av/generational tmp)) 1.10) "20 'Gen 0' → lift 0.05*(20//10)=0.10")
           (finally (rm-rf! tmp)))))

     (deftest generational-zero-when-lands-missing
       (let [tmp (tmp-dir!)]
         (try
           (let [[g notes] (av/generational tmp)]
             (is (= 0.0 g))
             (is (str/includes? (first notes) "missing")))
           (finally (rm-rf! tmp)))))

     (deftest compute-assembles-full-tuple
       (let [tmp (tmp-dir!) obs (mkdirs! (str tmp "/_observations"))]
         (try
           (spit! (str tmp "/LANDS.md") "x")
           (doseq [[n v] [[1 3] [2 6] [3 9]]] (write-cycle! obs n [["Alpha" v] ["Beta" v]]))
           (make-cell! tmp "c1" (str "\"\"\"d\"\"\"\n" (apply str (repeat 100 "x=1\n"))))
           (make-cell! tmp "c2" (str "\"\"\"d\"\"\"\n" (apply str (repeat 100 "x=1\n"))))
           (let [a (av/compute tmp)]
             (is (approx (:C a) 1.0) "coupling from the cycles")
             (is (approx (:D a) (Math/log 2)) "two cells")
             (is (approx (:G a) 1.0))
             (is (and (seq (:timestamp a)) (seq (:notes a))) "populated"))
           (finally (rm-rf! tmp)))))))

;; ── pure fns (host-independent — also exercise the cljs-shared code paths) ───
(deftest alive-tuple-as-dict-rounds-to-4dp
  (let [a (av/alive-tuple 1.234567 2.0 0.5 0.75 1.1 "t" ["x"])
        d (av/as-dict a)]
    (is (= 1.2346 (get d "M_motion")))
    (is (= 1.1 (get d "G_generational")))
    (is (= ["x"] (get d "notes")))))

(deftest in-healthy-band-thresholds
  (let [healthy (av/alive-tuple 0.6 1.6 0.5 0.7 1.1)]
    (is (= {"M" true "D" true "C" true "P" true "G" true} (av/in-healthy-band healthy))))
  (let [edge (av/alive-tuple 0.5 1.5 0.71 0.49 1.0)]
    (is (= {"M" false "D" false "C" false "P" false "G" false} (av/in-healthy-band edge))
        "boundary failures: M not >0.5, C >0.7, P <0.5, G not >1.0")))

(deftest shannon-and-pearson-pure
  (testing "Shannon entropy of N equal counts = ln N"
    (is (approx (av/shannon-entropy [1 1 1 1]) (Math/log 4))))
  (testing "Pearson is ±1 for perfectly (anti)correlated series, nil when flat"
    (is (approx (av/pearson [3 6 9] [3 6 9]) 1.0))
    (is (approx (av/pearson [1 5 9] [9 5 1]) -1.0))
    (is (nil? (av/pearson [2 2 2] [1 2 3])))))
