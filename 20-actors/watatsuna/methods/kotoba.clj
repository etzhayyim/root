#!/usr/bin/env bb
;; Working Clojure port of methods/kotoba.py — the local content-addressed Datom-log writer.
(ns watatsuna.methods.kotoba
  "kotoba.clj — watatsuna kotoba Datom-log writer (local, content-addressed).
  ADR-2606012600 + ADR-2605262130 + ADR-2605312345.

  Canonical state is the kotoba Datom log — content-addressed EAVT assertions, append-only
  (非終末論). This is the local, autonomous-loop write path (the shionome/ipaddress/yabai/sukashi
  shape): a heartbeat appends content-addressed transactions to a local append-only EDN log with
  NO external I/O, so watatsuna runs its observe→analyze→persist cable-resilience cycle on the
  Murakumo fleet with no human/live-node in the loop.

  Constitutional posture holds by construction: every derived signal is a RESILIENCE map
  (chokepoint-load / station-degree / cable-diversity / redundancy-gap) — never a 'where to cut'
  interdiction framing (G2); public-record cable data only (G1); fault kinds carry only the
  public bulletin's own classification (G4).

    graph-datoms   → EAVT assertions for every entity (cable/station/link/segment/fault)
    derived-datoms → EAVT assertions for the analyzer's derived :resilience/* signals
    make-tx / append-tx / read-log / head-cid / verify-chain — content-addressed commit-DAG

  EAVT = [op entity attribute value]; op is :db/add only (append-only — no :db/retract).
  Deterministic: the caller supplies tx-id + as-of (no wall clock) → resume-safe. The CID is a
  clj-native content address (sha256 over the canonical pr-str of {:datoms :prev}); it is
  internally consistent + tamper-evident (it does not reproduce kotoba.py's JSON-based bytes,
  since the clj port carries real EDN keywords where the Python port carried strings)."
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn log-default []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "watatsuna.datoms.kotoba.edn")))

(def id-keys #{:cable/id :station/id :cable.link/id :cable.seg/id :cable.fault/id})

(defn- add-datom [e a v] [:db/add e a v])

(defn graph-datoms
  "Flatten the cable graph into append-only EAVT assertions. E = the entity's id; list values
  (e.g. :station/chokepoint, :cable.seg/traverses) fan out."
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
  "Flatten the analyzer's derived :resilience/* signals into EAVT assertions, each flagged
  :resilience/derived true (a RESILIENCE map recomputed on read, never re-ingested as fact,
  never an interdiction target-list — G2). `a` is analyze/analyze."
  [{:keys [cables stations]} a]
  (vec
   (concat
    (mapcat (fn [cp]
              (let [e (str "resilience-choke-" cp)]
                [(add-datom e :resilience/chokepoint cp)
                 (add-datom e :resilience/chokepoint-load (get-in a [:choke-load cp]))
                 (add-datom e :resilience/cable-count (get-in a [:choke-count cp]))
                 (add-datom e :resilience/derived true)]))
            (sort-by (juxt #(- (get-in a [:choke-load %])) str) (keys (:choke-load a))))
    (mapcat (fn [s]
              (let [e (str "resilience-station-" s)]
                [(add-datom e :resilience/station s)
                 (add-datom e :resilience/station-degree (get-in a [:station-degree s]))
                 (add-datom e :resilience/station-capacity-tbps (get-in a [:station-capacity s]))
                 (add-datom e :resilience/derived true)]))
            (filter #(pos? (get-in a [:station-degree %]))
                    (sort-by (juxt #(- (get-in a [:station-degree %])) str) (keys stations))))
    (mapcat (fn [c]
              (let [e (str "resilience-cable-" c)]
                [(add-datom e :resilience/cable c)
                 (add-datom e :resilience/cable-diversity (get-in a [:cable-diversity c]))
                 (add-datom e :resilience/derived true)]))
            (sort-by (juxt #(get-in a [:cable-diversity %]) str) (keys cables)))
    (mapcat (fn [s]
              (let [e (str "resilience-gap-" s)]
                [(add-datom e :resilience/redundancy-gap-station s)
                 (add-datom e :resilience/station-degree (get-in a [:station-degree s]))
                 (add-datom e :resilience/derived true)]))
            (:redundancy-gap a)))))

;; ── content-addressed commit-DAG ──────────────────────────────────────────────
(defn- sha256-hex [^String s]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")]
    (apply str (map #(format "%02x" (bit-and % 0xff)) (.digest md (.getBytes s "UTF-8"))))))

(defn- canonical [datoms prev]
  ;; deterministic canonical form (pr-str preserves vector order; map key order fixed here)
  (str "{:datoms " (pr-str datoms) " :prev " (pr-str prev) "}"))

(defn tx-cid
  "Content address = 'b' + sha256 over (prev, datoms) → a commit-DAG."
  ([datoms] (tx-cid datoms ""))
  ([datoms prev] (str "b" (sha256-hex (canonical datoms prev)))))

(defn make-tx [datoms & {:keys [tx-id as-of prev-cid] :or {prev-cid ""}}]
  {:tx/id tx-id :tx/as-of as-of :tx/prev prev-cid
   :tx/cid (tx-cid datoms prev-cid) :tx/count (count datoms) :tx/datoms datoms})

(defn append-tx
  "Append ONE transaction to the append-only log (never rewrites). Returns the tx CID."
  ([tx] (append-tx tx (log-default)))
  ([tx log-path]
   (let [f (io/file log-path)]
     (.mkdirs (.getParentFile (.getAbsoluteFile f)))
     (when-not (.exists f)
       (spit f (str ";; watatsuna kotoba Datom log — append-only EAVT transactions "
                    "(content-addressed DAG). Resilience map, never interdiction. "
                    "DO NOT hand-edit. ADR-2606012600.\n")))
     (spit f (str (pr-str tx) "\n") :append true)
     (:tx/cid tx))))

(defn read-log
  "Read the log back as a vector of transaction maps."
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
  "Recompute every CID from its datoms + prev; verify the DAG is intact. {:ok :length :broken-at}."
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
