(ns jinushi.methods.ingest
  "jinushi 地主 — REAL land-acquisition ingest from COMMITTED public-data snapshots (multi-source).

  Turns committed acquisition snapshots in the repo DATA LAYER (80-data/jinushi-land/*.kotoba.edn,
  landed via the datalad substrate ADR-2605241500) into the {:owners :parcels} shape that
  analyze/coverage consume — WITHOUT touching the network.

  MULTI-SOURCE + NO DOUBLE-COUNT (G2/G4 honesty): each snapshot declares
  `:counts-toward-world-coverage`. Only counting sources are merged into the world-coverage
  number; overlapping protected-area classes (e.g. nature reserves whose countries already
  carry national parks) are observed SEPARATELY and never summed — geometry de-dup is a future
  leg, so until then summing overlapping designations would inflate coverage dishonestly.

  WDQS / Wikimedia load discipline (operator directive 2026-06-16 「wdqs に負担をかけない」):
    - The committed snapshots are the loop's source of truth; each iteration re-ingests them with
      ZERO network I/O. A 30-min loop hitting WDQS would be abuse; it never does.
    - Live refresh is explicit/operator-only/polite (methods/fetch_wdqs.sh): one small LIMITed
      query, UA + contact, --max-time, courtesy sleep, no retry, refuses LIMIT>800.
    - Units are resolved + area normalized to m² at snapshot time (km²/hectare/decare/dunam/acre/
      m²); rows with an unresolved unit are dropped and the count disclosed, never guessed.
    - National parks / nature reserves are PUBLIC land → G1-safe (public owners, no persons, no
      coordinates; only country + area + a per-source per-country public-owner bucket)."
  (:require [clojure.string :as str]
            [jinushi.methods.analyze :as analyze]
            #?(:clj [clojure.java.io :as io])))

(defn source-slug
  "Short owner-namespace slug for a snapshot source-id (\"wikidata-national-parks\" → \"national-parks\")."
  [source-id]
  (if (str/starts-with? (or source-id "") "wikidata-")
    (subs source-id (count "wikidata-"))
    (or source-id "src")))

(defn owner-key [slug cc] (str "o.public." slug "." cc))

(defn snapshot->dataset
  "Pure: a parsed snapshot {:source-id :class :land-kind :records [{:cc :area-m2 …}]} →
  {:owners :parcels}. One PUBLIC owner bucket per (source, country); one parcel per record."
  [{:keys [source-id class land-kind records] :or {land-kind :public}}]
  (let [slug (source-slug source-id)
        kind (if (contains? analyze/owner-types land-kind) land-kind :public)
        ccs (sort (distinct (map :cc records)))
        owners (mapv (fn [cc]
                       {:owner/key (owner-key slug cc)
                        :owner/name (str (or class slug) " (" cc ")")
                        :owner/type kind})
                     ccs)
        parcels (->> records
                     (group-by :cc)
                     (sort-by key)
                     (mapcat (fn [[cc rs]]
                               (map-indexed
                                (fn [i r]
                                  {:parcel/id (format "WD-%s-%s-%04d" slug cc (inc i))
                                   :parcel/country cc
                                   :parcel/region ""
                                   :parcel/area-m2 (:area-m2 r)
                                   :parcel/owner (owner-key slug cc)
                                   :parcel/source :wikidata})
                                rs)))
                     vec)]
    {:owners owners :parcels parcels}))

(defn merge-datasets
  "Combine many {:owners :parcels} (owners deduped by :owner/key, parcels concatenated)."
  [& datasets]
  {:owners (->> (mapcat :owners datasets)
                (reduce (fn [m o] (assoc m (:owner/key o) o)) {})
                vals vec)
   :parcels (vec (mapcat :parcels datasets))})

(defn counting-dataset
  "Merge ONLY the snapshots flagged :counts-toward-world-coverage → the world-coverage dataset."
  [snaps]
  (apply merge-datasets (map snapshot->dataset (filter :counts-toward-world-coverage snaps))))

(defn source-summary
  "Per-source honesty row (counting + non-counting alike)."
  [{:keys [source-id class land-kind counts-toward-world-coverage records dropped-unknown-unit]}]
  {:source-id source-id
   :class class
   :land-kind land-kind
   :counts? (boolean counts-toward-world-coverage)
   :records (count records)
   :countries (count (distinct (map :cc records)))
   :area-km2 (/ (reduce + 0.0 (map :area-m2 records)) 1.0e6)
   :dropped dropped-unknown-unit})

#?(:clj
   (defn data-dir [root] (io/file root "80-data" "jinushi-land")))

#?(:clj
   (defn load-all-snapshots
     "Parse every *.kotoba.edn snapshot in the data dir (sorted by source-id)."
     [dir]
     (->> (.listFiles (io/file dir))
          (filter #(str/ends-with? (.getName %) ".kotoba.edn"))
          (map #(analyze/parse (slurp %)))
          (sort-by :source-id)
          vec)))

#?(:clj
   (defn -main [& argv]
     (let [here (or (some-> (when (and *file* (not= *file* "NO_SOURCE_PATH")) (io/file *file*))
                            .getParentFile .getParentFile)
                    (io/file "20-actors/jinushi"))
           root (or (some-> here .getParentFile .getParentFile) (io/file "."))
           dir (data-dir root)
           snaps (load-all-snapshots dir)
           ds (counting-dataset snaps)
           res (analyze/analyze ds)
           cov (:coverage res)]
       (require 'jinushi.methods.coverage)
       (println ((resolve 'jinushi.methods.coverage/render) res))
       (println)
       (println ";; ── sources (per-source honesty; only counting sources sum into world coverage) ──")
       (doseq [s (map source-summary snaps)]
         (println (format ";;  %-26s %-22s %5d recs / %2d cc / %,12.0f km²  counts=%s%s"
                          (:source-id s) (:class s) (:records s) (:countries s) (:area-km2 s)
                          (:counts? s)
                          (if (:counts? s) "" "  (observed-only; overlaps a counting source)"))))
       (println)
       (println (format ";; WORLD COVERAGE (counting sources only): %d countries, %,.0f km² = %.4g%% of world land"
                        (:countries-touched cov) (:acquired-area-km2 cov) (* 100.0 (:world-coverage-frac cov))))
       0)))
