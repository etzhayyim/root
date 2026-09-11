;; etzhayyim.kotoba.prolly — probabilistic (prolly) tree over the Datom log.
;;
;; ADR-2606242400 (multi-level DAG extension). The flat manifest (root -> list of
;; ALL datom CIDs) is O(n) to fetch and rewrites wholesale on any change. A prolly
;; tree replaces it with a content-addressed, **history-independent** B-tree:
;;
;;   * datoms are sorted by their key [e a v tx];
;;   * chunk boundaries are CONTENT-DEFINED — a run ends when the low `bits` of
;;     sha2-256(key) are zero (avg chunk = 2^bits), so the SAME datoms always
;;     yield the SAME tree regardless of insertion order/history (the prolly
;;     property), and a change path-copies only the touched leaf + its spine;
;;   * leaves hold datom runs, internal nodes hold [first-key child-cid] runs,
;;     built level-by-level until a single ROOT remains.
;;
;; A point/range seek then descends ONE spine — O(log n) Range fetches against
;; the GitHubPagesBlockStore — instead of pulling the whole graph. Every node is
;; a CIDv1 block (raw/sha2-256, ipfs-parity), so the tree IS a Merkle DAG.

(ns etzhayyim.kotoba.prolly
  (:require [etzhayyim.kotoba.cid :as cid]))

(def ^:private default-bits
  "Average chunk size = 2^bits datoms. 6 ⇒ ~64/leaf in production; tests pass a
   smaller value to force a multi-level tree on a modest dataset."
  6)

(defn key-of
  "The sort/index key of a datom = its [e a v tx] (op excluded)."
  [dm] (subvec (vec dm) 0 4))

(defn- kstr [k] (pr-str k))                       ; total order via canonical pr-str
(defn key-str [dm] (kstr (key-of dm)))

(defn- boundary?
  "Content-defined chunk boundary: true when the low `bits` of sha2-256(s) are 0."
  [bits ^String s]
  (let [d (cid/sha2-256-digest (.getBytes s "UTF-8"))
        nbytes (quot (+ bits 7) 8)
        v (reduce (fn [acc i] (bit-or (bit-shift-left acc 8)
                                      (bit-and (aget d (- (alength d) 1 i)) 0xff)))
                  0 (range nbytes))]
    (zero? (bit-and v (dec (bit-shift-left 1 bits))))))

(defn- chunk-runs
  "Split `items` into runs; a run ends at the first item whose (key-fn item)
   triggers a boundary (boundary item is the run's last). The final partial run
   is always closed. Guarantees ≥1 run for non-empty input."
  [bits key-fn items]
  (loop [items items, cur [], runs []]
    (if-let [it (first items)]
      (let [cur (conj cur it)]
        (if (boundary? bits (key-fn it))
          (recur (rest items) [] (conj runs cur))
          (recur (rest items) cur runs)))
      (if (seq cur) (conj runs cur) runs))))

(defn- node->block [node]
  (let [b (.getBytes (pr-str node) "UTF-8")] [(cid/cid b) b]))

(defn build
  "Build a prolly tree over `datoms`. Returns
   {:root <cid> :blocks ([cid ^bytes]…) :levels <n> :nodes <n>}.
   Deterministic in the datom SET (history-independent)."
  [datoms & {:keys [bits] :or {bits default-bits}}]
  (let [sorted (vec (sort-by key-str datoms))]
    (if (empty? sorted)
      (let [[c b] (node->block {:kotoba/prolly :leaf :level 0 :items []})]
        {:root c :blocks [[c b]] :levels 1 :nodes 1})
      (let [;; level 0: leaves over datom runs
            leaf-runs (chunk-runs bits key-str sorted)
            leaves (mapv (fn [run]
                           (let [node {:kotoba/prolly :leaf :level 0
                                       :first (key-of (first run)) :items (vec run)}]
                             (assoc node :block (node->block node))))
                         leaf-runs)]
        (loop [level 0
               nodes leaves                       ; [{:first .. :block [cid b]}]
               all (mapv :block leaves)]
          (if (= 1 (count nodes))
            {:root (first (:block (first nodes)))
             :blocks all :levels (inc level) :nodes (count all)}
            (let [entries (mapv (fn [n] [(:first n) (first (:block n))]) nodes)
                  runs0 (chunk-runs bits (comp kstr first) entries)
                  ;; no-progress guard: if content-defined chunking didn't reduce
                  ;; the node count (e.g. every entry hit a boundary), collapse all
                  ;; entries into ONE parent so the tree always terminates.
                  runs (if (< (count runs0) (count nodes)) runs0 [entries])
                  parents (mapv (fn [run]
                                  (let [node {:kotoba/prolly :internal :level (inc level)
                                              :first (ffirst run) :children (vec run)}]
                                    (assoc node :block (node->block node))))
                                runs)]
              (recur (inc level) parents (into all (map :block parents))))))))))

;; ── read (over the GitHubPagesBlockStore get-block seam) ─────────────────────
;; `get-fn` = (fn [cid-str] -> ^bytes), CID-verified by the caller's store.

(defn- read-node [get-fn cid-str]
  (clojure.edn/read-string (String. ^bytes (get-fn cid-str) "UTF-8")))

(defn walk
  "Full in-order scan: descend every node, concat leaf items. Returns the sorted
   datom vector. `counter` (an atom) if given is incremented per node fetched."
  ([get-fn root] (walk get-fn root (atom 0)))
  ([get-fn root counter]
   (let [node (do (swap! counter inc) (read-node get-fn root))]
     (case (:kotoba/prolly node)
       :leaf (vec (:items node))
       :internal (vec (mapcat (fn [[_ cid]] (walk get-fn cid counter))
                              (:children node)))))))

(defn seek-datom
  "Point lookup: descend the ONE spine that can contain `target` (a datom).
   Returns {:found? bool :datom <or nil> :fetched <node-count>} — fetched ≈
   tree depth, NOT the whole tree (the O(log n) locality the flat manifest lacks)."
  [get-fn root target]
  (let [tkey (key-str target)
        counter (atom 0)]
    (loop [cid root]
      (let [node (do (swap! counter inc) (read-node get-fn cid))]
        (case (:kotoba/prolly node)
          :leaf (let [hit (some (fn [d] (when (= (key-str d) tkey) d)) (:items node))]
                  {:found? (some? hit) :datom hit :fetched @counter})
          :internal
          ;; choose the last child whose first-key <= target
          (let [child (->> (:children node)
                           (filter (fn [[fk _]] (<= (compare (kstr fk) tkey) 0)))
                           last)]
            (if child (recur (second child))
                {:found? false :datom nil :fetched @counter})))))))
