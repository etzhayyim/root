#!/usr/bin/env bb
;; Working Clojure port of methods/kotoba.py — the local content-addressed Datom-log writer.
(ns watari.methods.kotoba
  "kotoba.clj — watari kotoba Datom-log writer (local, content-addressed).
  ADR-2606041827 + ADR-2605262130 + ADR-2605312345.

  Canonical state is the kotoba Datom log — content-addressed EAVT assertions, append-only
  (非終末論; the fix stream IS the trajectory, the latest fix IS the current position). This is
  the local, autonomous-loop write path (the shionome/ipaddress/yabai/sukashi/watatsuna shape).

  Constitutional posture holds by construction: outputs are situational-awareness, not
  surveillance / not targeting (G2 — aggregate lane/chokepoint/approach density); a craft is a
  craft, NEVER a person (G4 — no position track linked to an individual, operator is a company
  only). The loop persists exactly what analyze.clj computes, derived signals flagged
  :movement/derived.

    graph-datoms   → EAVT assertions for every entity (craft/fix/leg/lane)
    derived-datoms → EAVT assertions for derived :movement/* signals
    make-tx / append-tx / read-log / head-cid / verify-chain — content-addressed commit-DAG

  EAVT = [op entity attribute value]; op is :db/add only (append-only — no :db/retract).
  Deterministic: caller supplies tx-id + as-of (no wall clock) → resume-safe. The CID is a
  clj-native content address (sha256 over the canonical pr-str of {:datoms :prev}); internally
  consistent + tamper-evident (it does not reproduce kotoba.py's JSON bytes, since the clj port
  carries real EDN keywords where the Python port carried strings)."
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn log-default []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "watari.datoms.kotoba.edn")))

(def id-keys #{:craft/id :craft.fix/id :craft.leg/id :lane/id})

(defn- add-datom [e a v] [:db/add e a v])

(defn graph-datoms
  "Flatten the moving-craft graph into append-only EAVT assertions. E = the entity's id; list
  values fan out. Persists craft identity / fixes / legs / lanes as-is — operator-as-company
  only, never a person (G4)."
  [rows]
  (vec (mapcat
        (fn [r]
          (when (map? r)
            (when-let [e (some #(get r %) id-keys)]
              (for [[k v] r :when (not (id-keys k))
                    item (if (sequential? v) v [v])]
                (add-datom e k item)))))
        rows)))

(defn derived-datoms
  "Flatten the analyzer's derived :movement/* signals into EAVT assertions, each flagged
  :movement/derived true (aggregate situational-awareness, never a per-craft follow/targeting
  feed — G2/G4). `a` is analyze/analyze."
  [{:keys [craft lanes]} a]
  (vec
   (concat
    (mapcat (fn [cp]
              (let [e (str "movement-choke-" cp)]
                [(add-datom e :movement/chokepoint cp)
                 (add-datom e :movement/chokepoint-transit (get-in a [:choke-transit cp]))
                 (add-datom e :movement/derived true)]))
            (sort-by (juxt #(- (get-in a [:choke-transit %])) str) (keys (:choke-transit a))))
    (mapcat (fn [ln]
              (let [e (str "movement-lane-" ln)]
                [(add-datom e :movement/lane ln)
                 (add-datom e :movement/lane-load (get-in a [:lane-load ln]))
                 (add-datom e :movement/vessels (count (get-in a [:lane-kind ln :vessel] #{})))
                 (add-datom e :movement/aircraft (count (get-in a [:lane-kind ln :aircraft] #{})))
                 (add-datom e :movement/derived true)]))
            (sort-by (juxt #(- (get-in a [:lane-load %])) str) (keys (:lane-load a))))
    (mapcat (fn [c]
              (let [fx (get-in a [:latest c])
                    e (str "movement-stale-" c)]
                [(add-datom e :movement/craft c)
                 (add-datom e :movement/stale true)
                 (add-datom e :movement/last-seen (or (:craft.fix/observed-at fx) ""))
                 (add-datom e :movement/derived true)]))
            (sort (:stale a))))))

;; ── content-addressed commit-DAG ──────────────────────────────────────────────
(defn- sha256-hex [^String s]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")]
    (apply str (map #(format "%02x" (bit-and % 0xff)) (.digest md (.getBytes s "UTF-8"))))))

(defn- canonical [datoms prev] (str "{:datoms " (pr-str datoms) " :prev " (pr-str prev) "}"))

(defn tx-cid
  ([datoms] (tx-cid datoms ""))
  ([datoms prev] (str "b" (sha256-hex (canonical datoms prev)))))

(defn make-tx [datoms & {:keys [tx-id as-of prev-cid] :or {prev-cid ""}}]
  {:tx/id tx-id :tx/as-of as-of :tx/prev prev-cid
   :tx/cid (tx-cid datoms prev-cid) :tx/count (count datoms) :tx/datoms datoms})

(defn append-tx
  ([tx] (append-tx tx (log-default)))
  ([tx log-path]
   (let [f (io/file log-path)]
     (.mkdirs (.getParentFile (.getAbsoluteFile f)))
     (when-not (.exists f)
       (spit f (str ";; watari kotoba Datom log — append-only EAVT transactions (content-addressed "
                    "DAG). Situational-awareness, never surveillance / no person-tracking (G2/G4). "
                    "DO NOT hand-edit. ADR-2606041827.\n")))
     (spit f (str (pr-str tx) "\n") :append true)
     (:tx/cid tx))))

(defn read-log
  ([] (read-log (log-default)))
  ([log-path]
   (let [f (io/file log-path)]
     (if-not (.exists f)
       []
       (->> (str/split-lines (slurp f))
            (map str/trim)
            (remove #(or (empty? %) (str/starts-with? % ";")))
            (mapv edn/read-string))))))

(defn head-cid
  ([] (head-cid (log-default)))
  ([log-path] (let [txs (read-log log-path)] (if (seq txs) (:tx/cid (last txs)) ""))))

(defn verify-chain
  ([] (verify-chain (log-default)))
  ([log-path]
   (let [txs (read-log log-path)]
     (loop [i 0 prev "" xs txs]
       (if (empty? xs)
         {:ok true :length (count txs) :broken-at -1}
         (let [tx (first xs)
               expect (tx-cid (:tx/datoms tx []) prev)]
           (if (or (not= (:tx/cid tx) expect) (not= (:tx/prev tx) prev))
             {:ok false :length (count txs) :broken-at i}
             (recur (inc i) (:tx/cid tx) (rest xs)))))))))
