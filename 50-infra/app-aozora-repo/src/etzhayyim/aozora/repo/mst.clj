(ns etzhayyim.aozora.repo.mst
  "AT Protocol **Merkle Search Tree** over the kotoba blockstore.

  Maps repo keys `<collection>/<rkey>` → record CIDs into a deterministic tree
  whose root CID is the commit's `data` field. A key's layer is
  `leadingZerosOnHash(key)` counted in 2-bit units (atproto fanout); a node at
  layer L directly holds the layer-L keys, with subtree pointers spanning the
  lower-layer keys between them. Nodes serialize as dag-cbor
  `{l: <cid|null>, e: [{p, k, v, t}]}` and are stored as `:block/*` Datoms on the
  kotoba log — NEVER an @atproto/repo side store (ADR-2606242330 addendum).

  VERIFIED: the root CIDs this builder produces are byte-identical to the
  official `@atproto/repo` MST (mst_test.clj golden vectors from
  `MST.create(...).add(k, cid).getPointer()`)."
  (:require [etzhayyim.aozora.repo.cid :as cid]
            [etzhayyim.aozora.repo.dag-cbor :as dc]
            [etzhayyim.aozora.repo.blockstore :as bs])
  (:import [java.security MessageDigest]
           [java.util Arrays]))

(defn- utf8 ^bytes [^String s] (.getBytes s "UTF-8"))
(defn- sha256 ^bytes [^bytes b] (.digest (MessageDigest/getInstance "SHA-256") b))

(defn leading-zeros
  "atproto `leadingZerosOnHash`: leading zero bits of sha256(key) counted in
  2-bit units (matches @atproto/repo exactly)."
  [^String key]
  (let [h (sha256 (utf8 key)) n (alength h)]
    (loop [i 0 z 0]
      (if (>= i n)
        z
        (let [b (bit-and (aget h i) 0xff)]
          (if (>= b 64) z
              (let [z (inc z)]
                (if (>= b 16) z
                    (let [z (inc z)]
                      (if (>= b 4) z
                          (let [z (inc z)]
                            (if (zero? b) (recur (inc i) (inc z)) z))))))))))))

(defn- common-prefix-len
  "Number of shared leading UTF-8 bytes between two keys."
  [^String a ^String b]
  (let [ab (utf8 a) bb (utf8 b) n (min (alength ab) (alength bb))]
    (loop [i 0]
      (if (and (< i n) (= (aget ab i) (aget bb i))) (recur (inc i)) i))))

(defn- key-suffix ^bytes [^String k ^long plen]
  (let [kb (utf8 k)] (Arrays/copyOfRange kb (int plen) (alength kb))))

(defn- bytewise< [^String a ^String b]
  (let [ab (utf8 a) bb (utf8 b) n (min (alength ab) (alength bb))]
    (loop [i 0]
      (cond
        (= i n) (< (alength ab) (alength bb))
        :else (let [x (bit-and (aget ab i) 0xff) y (bit-and (aget bb i) 0xff)]
                (cond (< x y) true (> x y) false :else (recur (inc i))))))))

(defn- put-node! [store node-map]
  (let [{:keys [cid bytes]} (cid/block node-map)]
    (bs/put-block store cid bytes)
    cid))

(declare build-at!)

(defn- subtree-cid!
  "MST CID for a (possibly empty) sorted range, built at EXACTLY `layer`
  (= parent layer − 1). nil for an empty range. If the range has no key at
  `layer`, `build-at!` emits a pass-through node (e=[]) that points down — atproto
  represents layer skips with empty intermediate nodes, NOT by jumping layers."
  [store entries layer]
  (when (seq entries)
    (build-at! store entries layer)))

(defn- build-at!
  "Build (and store) the node AT `layer` covering `entries` (sorted, every
  :layer <= layer). Keys with :layer == layer are this node's direct entries; if
  none, it is a pass-through node (e=[]) whose left points to the layer−1 node.
  Subtree pointers are ALWAYS layer−1. Returns the node CID."
  [store entries layer]
  (let [v (vec entries)
        idx (vec (keep-indexed (fn [i e] (when (= layer (:layer e)) i)) v))]
    (if (empty? idx)
      ;; pass-through: no entry at this layer; whole range descends to layer−1
      (put-node! store {"l" (some-> (subtree-cid! store v (dec layer)) dc/cid-link)
                        "e" []})
      (let [first-d (first idx)
            l-cid (subtree-cid! store (subvec v 0 first-d) (dec layer))
            es (loop [js idx prev-key nil acc []]
                 (if (empty? js)
                   acc
                   (let [j (first js)
                         nextj (or (second js) (count v))
                         d (nth v j)
                         k (:key d)
                         plen (if prev-key (common-prefix-len prev-key k) 0)
                         t-cid (subtree-cid! store (subvec v (inc j) nextj) (dec layer))]
                     (recur (rest js) k
                            (conj acc {"p" plen
                                       "k" (key-suffix k plen)
                                       "v" (dc/cid-link (:val d))
                                       "t" (some-> t-cid dc/cid-link)})))))]
        (put-node! store {"l" (some-> l-cid dc/cid-link) "e" es})))))

(defn data-root!
  "Build the atproto MST over `kv-pairs` ({:key '<coll>/<rkey>' :val <record-cid>})
  into `store`; return the root CID (the commit `data` field). The empty repo's
  root is the canonical empty node."
  [store kv-pairs]
  (let [entries (->> kv-pairs
                     (map (fn [{:keys [key val]}]
                            {:key key :val val :layer (leading-zeros key)}))
                     (sort (fn [a b] (cond (bytewise< (:key a) (:key b)) -1
                                           (bytewise< (:key b) (:key a)) 1
                                           :else 0))))]
    (if (empty? entries)
      (put-node! store {"l" nil "e" []})
      (build-at! store (vec entries) (apply max (map :layer entries))))))
