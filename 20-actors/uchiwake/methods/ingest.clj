(ns uchiwake.methods.ingest
  "uchiwake 内訳 — product / GTIN / BOM ingestion bridge (offline default; live G7-gated).
  Clojure port of `methods/ingest.py` (ADR-2606081800), Wave-2 clj-native migration
  (ADR-2606142300). A clj-side data/network tool (reads disk seeds, optional live fetch), so it is
  `.clj` rather than `.cljc` — alongside crosscheck.clj / adapters/openfoodfacts.clj.

  Bridges public product-data sources into the kotoba Datom log as :product/:part/:material/
  :bom.edge/… datoms, dedup-merged with the bounded real seed (seed wins on id). Default is
  OFFLINE (bridge data/ingest/*.json if present, else just the seed). The LIVE Open Food Facts
  fetch leg requires UCHIWAKE_OPERATOR_GATE=1 + an explicit --gtin (G7); the GS1 mod-10 check
  digit is validated BEFORE any network call (G5). no-server-key + read-only (G12)."
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [cheshire.core :as json]
            [uchiwake.methods.uchiwake-edn :as edn]
            [uchiwake.methods.adapters.openfoodfacts :as off]))

(def ^:private id-keys
  [":product/id" ":part/id" ":material/id" ":bom.edge/id"
   ":process.step/id" ":logistics.leg/id" ":design.ref/id" ":company.ownership/id"])

(defn seed-ids
  "Collect every entity id present in the seed rows (1:1 with _seed_ids)."
  [rows]
  (reduce (fn [s r]
            (if-not (map? r) s
                    (reduce (fn [s k] (if (contains? r k) (conj s (get r k)) s)) s id-keys)))
          #{} rows))

(defn- val-str
  "_emit_bridged_edn val(): bool→true/false; ':…' kept; other string → escaped EDN string; number."
  [v]
  (cond
    (boolean? v) (if v "true" "false")
    (integer? v) (str v)
    (float? v) (edn/py-float-str v)
    (and (string? v) (str/starts-with? v ":")) v
    (string? v) (edn/edn-str v)
    :else (str v)))

(defn emit-bridged-edn
  "Serialize bridged datom maps to EDN map literals, one per line (1:1 with _emit_bridged_edn)."
  [datoms]
  (->> (cons " ;; ── bridged datoms (offline adapters; :representative, G5) ──"
             (map (fn [d]
                    (str " {" (str/join " " (map (fn [k] (str k " " (val-str (get d k))))
                                                 (edn/keys-in-order d))) "}"))
                  datoms))
       (str/join "\n")))

;; ── live OFF fetch leg (G7-gated; mirrors ingest.py fetch_off) ────────────────
(def off-api "https://world.openfoodfacts.org/api/v2/product/%s.json")
(def off-fields "code,product_name,brands,countries_tags,ingredients")
(def off-ua "etzhayyim-uchiwake research (jun@etzhayyim.group)")

(def ^:private here (-> (io/file *file*) .getParentFile .getParentFile))
(def ^:private seed-file (io/file here "data" "seed-products.kotoba.edn"))
(def ^:private ingest-dir (io/file here "data" "ingest"))
(def ^:private merged-file (io/file here "data" "products.merged.kotoba.edn"))
(def ^:private live-file (io/file ingest-dir "openfoodfacts.live.json"))

;; The existing adapters/openfoodfacts.clj normalize-dataset returns Clojure-keyword stats
;; ({:products-ok …}); we only use its datom vector here, so the stat keys don't matter.
(defn bridge-offline
  "Merge any data/ingest/*.json bridged datoms with the seed (seed wins on id).
  OFF-shaped files route through the adapter; datom-shaped files are GTIN-validated."
  []
  (let [seed-rows (edn/load-edn (str seed-file))
        sids (seed-ids seed-rows)
        files (when (.isDirectory ingest-dir)
                (sort-by #(.getName %)
                         (filter #(str/ends-with? (.getName %) ".json") (.listFiles ingest-dir))))]
    [seed-rows
     (vec
      (mapcat
       (fn [f]
         (let [doc (json/parse-string (slurp f))]
           (if (str/starts-with? (.getName f) "openfoodfacts")
             (let [recs (if (map? doc) (get doc "products" []) doc)
                   [off-datoms _] (off/normalize-dataset recs)]
               (filter (fn [r]
                         (let [rid (or (get r ":product/id") (get r ":material/id")
                                       (get r ":bom.edge/id"))]
                           (not (and rid (contains? sids rid)))))
                       off-datoms))
             (let [rows (if (map? doc) (get doc "datoms" []) doc)]
               (keep (fn [r]
                       (cond
                         (and (contains? r ":product/gtin")
                              (not (edn/gtin-check-digit-ok (get r ":product/gtin")))) nil
                         :else
                         (let [rid (some #(get r %) id-keys)]
                           (when-not (and rid (contains? sids rid))
                             (if (and (contains? r ":product/id")
                                      (not (contains? r ":product/sourcing")))
                               (assoc r ":product/sourcing" ":representative")
                               r)))))
                     rows)))))
       files))]))

(defn fetch-off
  "LIVE Open Food Facts product fetch — G7-gated, single polite request. Validates the GS1 check
  digit BEFORE any network call (G5). Returns the OFF product map."
  [gtin]
  (when (not= (System/getenv "UCHIWAKE_OPERATOR_GATE") "1")
    (throw (ex-info "REFUSED (G7): live OFF fetch requires UCHIWAKE_OPERATOR_GATE=1 + Council."
                    {:gate :G7})))
  (let [digits (apply str (filter #(Character/isDigit ^char %) (str gtin)))]
    (when-not (edn/gtin-check-digit-ok digits)
      (throw (ex-info (str "REFUSED (G5): " gtin " fails the GS1 mod-10 check digit.") {:gate :G5})))
    (let [url (str (format off-api digits) "?fields=" off-fields)
          conn (doto ^java.net.HttpURLConnection (.openConnection (java.net.URL. url))
                 (.setRequestProperty "User-Agent" off-ua)
                 (.setConnectTimeout 30000) (.setReadTimeout 30000))
          obj (with-open [r (io/reader (.getInputStream conn))] (json/parse-string (slurp r)))]
      (when (or (not= (get obj "status") 1) (not (map? (get obj "product"))))
        (throw (ex-info (str "OFF has no product record for GTIN " digits) {})))
      (let [prod (get obj "product")]
        (if (contains? prod "code") prod (assoc prod "code" digits))))))

(defn save-live-record
  "Append one fetched OFF record into data/ingest/openfoodfacts.live.json (dedup by code)."
  [prod]
  (.mkdirs ingest-dir)
  (let [existing (if (.exists live-file)
                   (let [doc (json/parse-string (slurp live-file))]
                     (if (map? doc) (get doc "products" doc) doc))
                   [])
        by-code (reduce (fn [m r] (assoc m (str (get r "code")) r)) {} (filter map? existing))
        by-code (assoc by-code (str (get prod "code")) prod)
        records (vec (vals by-code))]
    (spit live-file (json/generate-string {"products" records} {:pretty true}))
    (count records)))

(defn -main [& argv]
  (let [argv (vec argv)
        live (boolean (some #{"--live"} argv))
        gtin (when-let [i (let [j (.indexOf argv "--gtin")] (when (>= j 0) j))] (nth argv (inc i)))
        gated (= (System/getenv "UCHIWAKE_OPERATOR_GATE") "1")
        live (if (and live (not gated))
               (do (binding [*out* *err*]
                     (println (str "REFUSED (G7): live GS1/GLEIF/OFF ingest requires "
                                   "UCHIWAKE_OPERATOR_GATE=1 + Council. Running offline instead.")))
                   false)
               live)]
    (when (and live gtin)
      (let [prod (fetch-off gtin) n (save-live-record prod)]
        (binding [*out* *err*]
          (println (str "G7 gate satisfied — fetched OFF GTIN " gtin ": \""
                        (or (get prod "product_name") "(unnamed)") "\" → " (.getName live-file)
                        " (" n " live record" (if (= n 1) "" "s") ")")))))
    (let [[seed-rows bridged] (bridge-offline)
          g (edn/classify seed-rows)
          text (slurp (str seed-file))]
      (println (str "seed: " (count (:products g)) " products, " (count (:parts g)) " parts, "
                    (count (:materials g)) " materials, " (count (:bom g)) " BOM edges, "
                    (count (:ownership g)) " ownership edges"))
      (println (str "bridged (offline data/ingest/*.json): " (count bridged) " new datoms"))
      (if (seq bridged)
        (let [block (emit-bridged-edn bridged)
              cut (str/last-index-of (str/trimr text) "]")
              merged (str (subs text 0 cut) "\n" block "\n]\n")]
          (spit merged-file merged)
          (println (str "→ " merged-file " (seed + " (count bridged) " bridged datoms)")))
        (do (spit merged-file text)
            (println (str "→ " merged-file " (== seed; no external ingest)")))))))
