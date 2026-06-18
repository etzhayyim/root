(ns tsumugi.methods.autorun
  "autorun.cljc — 紡ぎ: the autonomous offline beat over the kotoba Datom log.
  Clojure port of methods/autorun.py (1:1, the offline beat). ADR-2606092000.

  Each beat is OFFLINE, deterministic, fail-open, and persists a content-addressed transaction
  to the LOCAL append-only kotoba Datom log:
    forage ─▶ publish ─▶ measure ─▶ append tx
  No live external I/O (the live WDQS/GLEIF ingest stays operator-gated). Deterministic: logical
  time only (beat index), so same seed + same cycle count → byte-identical head CID (within a
  runtime). Depends on the already-ported same-actor ingest-scale (forage-plan) + publish +
  coverage-scale. The argparse main is omitted. SHA-256 via java.security; file I/O at #?(:clj)."
  (:require [clojure.string :as str]
            [tsumugi.methods.ingest-scale :as ingest-scale]
            [tsumugi.methods.publish :as publish]
            [tsumugi.methods.coverage-scale :as coverage-scale]
            #?(:clj [clojure.java.io :as io]))
  #?(:clj (:import [java.security MessageDigest])))

(def SEED "20-actors/tsumugi/data/seed-scale-power.kotoba.edn")
(def OUT "20-actors/tsumugi/out")
(def LOG "20-actors/tsumugi/data/tsumugi-cycle.datoms.kotoba.edn")
(def AS-OF-BASE 2606110000)

(defn- sha256-hex [s]
  #?(:clj (let [md (MessageDigest/getInstance "SHA-256")]
            (.update md (.getBytes (str s) "UTF-8"))
            (apply str (map #(format "%02x" (bit-and % 0xFF)) (.digest md))))
     :cljs (throw (ex-info "sha256 requires the JVM" {}))))

(defn- cid* [body] (str "tx:sha256:" (subs (sha256-hex body) 0 16)))
(defn- pyround [x n] (let [f (Math/pow 10.0 n)] (/ (Math/rint (* (double x) f)) f)))

#?(:clj
   (defn read-head
     "Replay the local log → [head-cid beat-count] (durable across kills)."
     [log-path]
     (let [f (io/file (str log-path))]
       (if-not (.exists f)
         ["tx:genesis" 0]
         (let [txs (filter #(str/includes? % ":tx/id") (str/split-lines (slurp f)))]
           (if (empty? txs)
             ["tx:genesis" 0]
             (let [m (re-find #":tx/id \"([^\"]+)\"" (last txs))]
               [(if m (second m) "tx:genesis") (count txs)])))))))

#?(:clj
   (defn country-pct []
     (let [c (apply coverage-scale/compute (coverage-scale/load-data))
           cov (get-in c ["coverages" "Countries (~sovereign states)"])]
       (if cov (pyround (get cov "percent" 0.0) 4) 0.0))))

#?(:clj
   (defn beat
     "One offline cycle → the appended tx map (also written to the local log)."
     [log-path & {:keys [seed out-dir] :or {seed SEED out-dir OUT}}]
     (let [[head n] (read-head log-path)
           plan (ingest-scale/forage-plan seed)
           manifest (publish/publish out-dir seed)
           pct (country-pct)
           as-of (+ AS-OF-BASE n)
           forage (-> (get plan "recommendation") (str/split #" —") first (str/split #" \(") first)
           datoms [[":tsumugi.cycle/beat" n]
                   [":tsumugi.cycle/as-of" as-of]
                   [":tsumugi.cycle/seed-nodes" (get-in manifest ["counts" "nodes"])]
                   [":tsumugi.cycle/seed-edges" (get-in manifest ["counts" "edges"])]
                   [":tsumugi.cycle/forage" forage]
                   [":tsumugi.cycle/frontier-tips" (get plan "frontier_tips")]
                   [":tsumugi.cycle/harvested" (get plan "harvested_anchors")]
                   [":tsumugi.cycle/dataset-content-hash" (get manifest "contentHash")]
                   [":tsumugi.cycle/dataset-triples" (get-in manifest ["counts" "triples"])]
                   [":tsumugi.cycle/country-coverage-pct" pct]
                   [":tsumugi.cycle/published-by" publish/PUBLISHER-DID]]
           v (fn [x] (if (string? x) (str "\"" x "\"") (str x)))
           body-datoms (str/join " " (map (fn [[a x]] (str "[" a " " (v x) "]")) datoms))
           body (str "{:tx/prev \"" head "\" :tx/datoms [" body-datoms "]}")
           cid (cid* body)
           tx-line (str "{:tx/id \"" cid "\" :tx/prev \"" head "\" :tx/datoms [" body-datoms "]}")]
       (io/make-parents (str log-path))
       (spit (str log-path) (str tx-line "\n") :append true)
       {"cid" cid "prev" head "beat" n "datoms" (into {} datoms)})))
