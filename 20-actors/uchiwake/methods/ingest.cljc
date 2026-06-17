(ns uchiwake.methods.ingest
  "uchiwake 内訳 — product / GTIN / BOM ingestion bridge (offline default; live G7-gated).
  1:1 Clojure port of `methods/ingest.py` (ADR-2606081800).

  Bridges public product-data sources into the kotoba Datom log as
  :product/:part/:material/:bom.edge/:process.step/:logistics.leg/:design.ref/
  :company.ownership datoms, dedup-merged with the bounded real seed (seed wins on id).

  GATES (enforced here):
    G1  public trade items + public-record data only.
    G5  every emitted datom carries :*/sourcing; bridged data defaults :representative.
    G7  live full-universe fetch requires UCHIWAKE_OPERATOR_GATE=1 (Council + operator).
        Default is OFFLINE: bridge data/ingest/*.json if present, else just the seed.
    no-server-key: read-only.

  House style (lineage): ':…' keyword strings stay strings; string-keyed maps; pure fns;
  file/network I/O behind #?(:clj) edges (json.loads / file globbing / EDN text splicing)."
  (:require [clojure.string :as str]
            [uchiwake.methods.uchiwake-edn :as edn]
            [uchiwake.methods.adapters.openfoodfacts :as off]))

(def ^:private id-keys
  [":product/id" ":part/id" ":material/id" ":bom.edge/id"
   ":process.step/id" ":logistics.leg/id" ":design.ref/id" ":company.ownership/id"])

(defn seed-ids
  "Set of every entity id present across the seed rows (1:1 with _seed_ids)."
  [rows]
  (reduce
   (fn [ids r]
     (if-not (map? r)
       ids
       (reduce (fn [ids k] (if (contains? r k) (conj ids (get r k)) ids)) ids id-keys)))
   #{}
   rows))

(defn- first-id
  "next((r[k] for k in id-keys if k in r), None) — first present entity id, or nil."
  [r]
  (some (fn [k] (when (contains? r k) (get r k))) id-keys))

(defn admit-datom-doc-rows
  "Pure body of the non-OFF doc branch of bridge_offline: filter+default a list of datom rows
  against the seed ids (1:1 with the inner loop). Skips bad-GTIN product datoms (G5 honesty)
  and seed-owned ids (seed wins); defaults :product/sourcing to :representative on products."
  [rows seed-ids]
  (reduce
   (fn [bridged r]
     (cond
       (and (contains? r ":product/gtin")
            (not (edn/gtin-check-digit-ok (get r ":product/gtin"))))
       bridged                              ; skip — bad GTIN check digit

       :else
       (let [rid (first-id r)]
         (if (and rid (contains? seed-ids rid))
           bridged                          ; seed wins
           (let [r (if (contains? r ":product/id")
                     (if (contains? r ":product/sourcing") r
                         (assoc r ":product/sourcing" ":representative"))
                     r)]
             (conj bridged r))))))
   []
   rows))

(defn admit-off-datoms
  "Pure body of the OFF branch of bridge_offline: drop any normalized OFF datom whose product/
  material/bom id is already in the seed (seed wins). 1:1 with the off_datoms loop."
  [off-datoms seed-ids]
  (reduce
   (fn [bridged r]
     (let [rid (or (get r ":product/id") (get r ":material/id") (get r ":bom.edge/id"))]
       (if (and rid (contains? seed-ids rid)) bridged (conj bridged r))))
   []
   off-datoms))

(defn emit-bridged-edn
  "Serialize bridged datom maps to EDN map literals, one per line (1:1 with _emit_bridged_edn)."
  [datoms]
  (let [val (fn [v]
              (cond
                (boolean? v) (if v "true" "false")
                (string? v) (if (str/starts-with? v ":") v (edn/edn-str v))
                (and (number? v) (not (integer? v))) (str (double v))
                :else (str v)))
        lines (cons " ;; ── bridged datoms (offline adapters; :representative, G5) ──"
                    (map (fn [d]
                           (let [order (or (::order (meta d)) (keys d))]
                             (str " {" (str/join " " (map (fn [k] (str k " " (val (get d k)))) order)) "}")))
                         datoms))]
    (str/join "\n" lines)))

;; ── file/network-bound bridge + CLI (#?(:clj) edge; __main__ omitted) ────────
#?(:clj
   (defn -main
     "CLI entry (1:1 with main()): offline bridge of data/ingest/*.json (OFF adapter for
     openfoodfacts*, datom docs otherwise) + the seed, merged to products.merged.kotoba.edn
     (seed wins on id). Live ingest is G7-gated. File I/O only at this edge. The full --live
     path + the JSON reader are host-bound; this entry documents the offline behavior."
     [& _argv]
     (throw (ex-info (str "ingest -main is a host-IO entry; invoke seed-ids / "
                          "admit-datom-doc-rows / admit-off-datoms / emit-bridged-edn "
                          "directly over already-read rows") {}))))
