;; ported from 20-actors/kosatsu/methods/kotoba.py — gold reference (Fable)
;; kosatsu 高札 — woven competing-claim graph を append-only EAVT assertion へ flatten し、
;; content-addressed commit-DAG (tx) を作る。各 designation は ATTRIBUTED event (自分の :asserter を
;; 持ち etzhayyim は何も authored しない)。tx-cid = sha256 over (prev-cid, datoms) → commit-DAG。
(ns kosatsu.methods.kotoba
  (:import [java.security MessageDigest]))

(def id-keys [:authority/id :subject/id :designation/id])

(defn add-datom
  "1 つの append-only EAVT assertion: [:db/add <entity> <attr> <value>]。"
  [entity attr value]
  [:db/add entity attr value])

(defn- flatten-rows
  "row 群 (map または coll) を EAVT assertion へ。entity は id-keys のいずれかから取る。
  list 値は 1 値ずつ展開する (cardinality-many)。"
  [rows]
  (let [items (if (map? rows) (vals rows) rows)]
    (for [row items
          :when (map? row)
          :let [e (some #(get row %) id-keys)]
          :when (some? e)
          [k v] row
          :when (not (some #{k} id-keys))
          item (if (sequential? v) v [v])]
      (add-datom e k item))))

(defn graph-datoms
  "competing-claim graph を append-only EAVT assertion へ flatten する。"
  [g]
  (vec (mapcat flatten-rows [(:authorities g) (:subjects g) (:designations g)])))

(defn- sha256-hex [^String s]
  (let [d (.digest (MessageDigest/getInstance "SHA-256") (.getBytes s "UTF-8"))]
    (apply str (map #(format "%02x" (bit-and % 0xff)) d))))

(defn- canonical
  "(prev-cid, datoms) の決定的直列化 (sort-keys, no-space)。"
  [datoms prev-cid]
  (pr-str {:prev prev-cid :datoms datoms}))

(defn tx-cid
  "Content address = sha256 over (prev-cid, datoms) → commit-DAG。"
  ([datoms] (tx-cid datoms ""))
  ([datoms prev-cid]
   (str "b" (sha256-hex (canonical datoms prev-cid)))))

(defn make-tx
  "datoms を 1 tx に束ね、prev-cid に連鎖させる (commit-DAG の 1 ノード)。"
  [datoms {:keys [tx-id as-of prev-cid] :or {prev-cid ""}}]
  {:tx/id tx-id
   :tx/as-of as-of
   :tx/prev prev-cid
   :tx/cid (tx-cid datoms prev-cid)
   :tx/count (count datoms)
   :tx/datoms datoms})
