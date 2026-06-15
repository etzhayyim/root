#!/usr/bin/env bb
;; Working Clojure port of methods/kotoba.py — the local content-addressed Datom-log writer.
(ns kabuto.methods.kotoba
  "kotoba.clj — kabuto kotoba Datom-log writer (local, content-addressed).
  ADR-2606022000 + ADR-2605262130 + ADR-2605312345.

  Canonical state is the kotoba Datom log — content-addressed EAVT assertions, append-only. The
  local autonomous-loop write path (the shionome/watatsuna shape). Outputs are resilience +
  accountability (G2 — concentration / single-source / tier-depth / cross-bloc), never a
  raid/takeover/target framing; listed-company public-record facts only (G1); non-adjudicating (G4).

    graph-datoms   → EAVT for every entity (company/address/contact/supply-edge/process)
    derived-datoms → EAVT for derived :supply/* concentration signals (flagged :supply/derived)
    make-tx / append-tx / read-log / head-cid / verify-chain — content-addressed commit-DAG

  :db/add only (append-only). Deterministic: caller supplies tx-id + as-of; autorun sorts datoms
  into canonical order before hashing so the CID is reproducible regardless of set-iteration order."
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn log-default []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "kabuto.datoms.kotoba.edn")))

(def id-keys #{:company/id :company.address/id :company.contact/id :supply.edge/id :company.process/id})
(defn- add-datom [e a v] [:db/add e a v])

(defn graph-datoms [rows]
  (vec (mapcat
        (fn [r]
          (when (map? r)
            (when-let [e (some #(get r %) id-keys)]
              (for [[k v] r :when (not (id-keys k))
                    item (if (sequential? v) v [v])]
                (add-datom e k item)))))
        rows)))

(defn derived-datoms
  "Flatten the analyzer's derived :supply/* signals into EAVT assertions (flagged
  :supply/derived true). `a` is analyze/analyze. Mirrors analyze.render_datoms."
  [a]
  (let [r2 (fn [x] (/ (Math/round (* (double x) 100.0)) 100.0))
        cm (fn [c] (str/replace (str c) #"^:" ""))]
    (vec
     (concat
      (mapcat (fn [i [c commodity sup crit]]
                (let [e (str "supply-single-" i)]
                  [(add-datom e :supply/single-source-customer c)
                   (add-datom e :supply/commodity commodity)
                   (add-datom e :supply/sole-supplier sup)
                   (add-datom e :supply/criticality crit)
                   (add-datom e :supply/derived true)]))
              (range) (:single-source a))
      (mapcat (fn [[country load]]
                (let [e (str "supply-juris-" country)]
                  [(add-datom e :supply/jurisdiction country)
                   (add-datom e :supply/jurisdiction-load (r2 load))
                   (add-datom e :supply/derived true)]))
              (sort-by (comp - val) (:jurisdiction-load a)))
      (mapcat (fn [[sup load]]
                (let [e (str "supply-systemic-" sup)]
                  [(add-datom e :supply/systemic-supplier sup)
                   (add-datom e :supply/out-degree (get-in a [:out-deg sup] 0))
                   (add-datom e :supply/outward-criticality (r2 load))
                   (add-datom e :supply/derived true)]))
              (sort-by (comp - val) (:systemic a)))
      (mapcat (fn [[c secs load idx]]
                (let [e (str "supply-divers-" c)]
                  [(add-datom e :supply/diversification-customer c)
                   (add-datom e :supply/supplier-sectors secs)
                   (add-datom e :supply/inbound-criticality load)
                   (add-datom e :supply/diversification-index idx)
                   (add-datom e :supply/derived true)]))
              (:diversification a))
      (mapcat (fn [[n ind outd score]]
                (let [e (str "supply-inter-" n)]
                  [(add-datom e :supply/intermediary n)
                   (add-datom e :supply/in-degree ind)
                   (add-datom e :supply/out-degree outd)
                   (add-datom e :supply/betweenness score)
                   (add-datom e :supply/derived true)]))
              (:intermediaries a))
      (mapcat (fn [[n d]]
                (let [e (str "supply-tier-" n)]
                  [(add-datom e :supply/tier-depth-node n)
                   (add-datom e :supply/tier-depth d)
                   (add-datom e :supply/derived true)]))
              (:tier-depth a))
      (mapcat (fn [[bloc load]]
                (let [e (str "supply-bloc-" bloc)]
                  [(add-datom e :supply/region-bloc bloc)
                   (add-datom e :supply/bloc-load (r2 load))
                   (add-datom e :supply/derived true)]))
              (sort-by (comp - val) (:bloc-load a)))
      (mapcat (fn [[commodity nsup hhi]]
                (let [e (str "supply-commodity-" (cm commodity))]
                  [(add-datom e :supply/commodity (cm commodity))
                   (add-datom e :supply/commodity-suppliers nsup)
                   (add-datom e :supply/commodity-hhi hhi)
                   (add-datom e :supply/derived true)]))
              (:commodity-hhi a))
      (mapcat (fn [[corridor load]]
                (let [e (str "supply-corridor-" corridor)]
                  [(add-datom e :supply/cross-bloc-corridor corridor)
                   (add-datom e :supply/cross-bloc-load (r2 load))
                   (add-datom e :supply/derived true)]))
              (:cross-corridors a))
      (mapcat (fn [[c score ss _secs _load _cross]]
                (let [e (str "supply-resil-" c)]
                  [(add-datom e :supply/resilience-customer c)
                   (add-datom e :supply/resilience-score score)
                   (add-datom e :supply/single-source-count ss)
                   (add-datom e :supply/derived true)]))
              (:resilience a))))))

;; ── content-addressed commit-DAG ──────────────────────────────────────────────
(defn- sha256-hex [^String s]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")]
    (apply str (map #(format "%02x" (bit-and % 0xff)) (.digest md (.getBytes s "UTF-8"))))))
(defn- canonical [datoms prev] (str "{:datoms " (pr-str datoms) " :prev " (pr-str prev) "}"))
(defn tx-cid
  ([datoms] (tx-cid datoms ""))
  ([datoms prev] (str "b" (sha256-hex (canonical datoms prev)))))

(defn canonical-order
  "Sort datoms into a canonical (pr-str) order so the CID is reproducible regardless of
  analyze's set-iteration order. Idempotent."
  [datoms]
  (vec (sort-by pr-str datoms)))

(defn make-tx [datoms & {:keys [tx-id as-of prev-cid] :or {prev-cid ""}}]
  {:tx/id tx-id :tx/as-of as-of :tx/prev prev-cid
   :tx/cid (tx-cid datoms prev-cid) :tx/count (count datoms) :tx/datoms datoms})

(defn append-tx
  ([tx] (append-tx tx (log-default)))
  ([tx log-path]
   (let [f (io/file log-path)]
     (.mkdirs (.getParentFile (.getAbsoluteFile f)))
     (when-not (.exists f)
       (spit f (str ";; kabuto kotoba Datom log — append-only EAVT transactions (content-addressed "
                    "DAG). Resilience + accountability, never a target-list (G2/G4). DO NOT hand-edit. "
                    "ADR-2606022000.\n")))
     (spit f (str (pr-str tx) "\n") :append true)
     (:tx/cid tx))))

(defn read-log
  ([] (read-log (log-default)))
  ([log-path]
   (let [f (io/file log-path)]
     (if-not (.exists f) []
       (->> (str/split-lines (slurp f)) (map str/trim)
            (remove #(or (empty? %) (str/starts-with? % ";"))) (mapv edn/read-string))))))

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
         (let [tx (first xs) expect (tx-cid (:tx/datoms tx []) prev)]
           (if (or (not= (:tx/cid tx) expect) (not= (:tx/prev tx) prev))
             {:ok false :length (count txs) :broken-at i}
             (recur (inc i) (:tx/cid tx) (rest xs)))))))))
