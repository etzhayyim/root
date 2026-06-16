(ns jinushi.methods.ingest
  "jinushi 地主 — REAL land-acquisition ingest from a COMMITTED public-data snapshot.

  Turns a committed acquisition snapshot (data/acquired/*.kotoba.edn) into the
  {:owners :parcels} shape that analyze/coverage consume — WITHOUT touching the network.

  WDQS / Wikimedia load discipline (G4 + good-citizen, per operator directive 2026-06-16):
    - The snapshot is the loop's source of truth. Each loop iteration re-ingests the COMMITTED
      snapshot; it NEVER re-queries WDQS. A 30-min loop hitting WDQS would be abuse.
    - A live refresh is an EXPLICIT, rare, polite operation only (methods/fetch_wdqs.sh):
      one small LIMITed query, descriptive UA + contact, --max-time, a courtesy sleep, and at
      most one query per refresh. Never a tight retry loop.
    - National parks (P31=Q46169) are PUBLIC land; the owner is the state. G1-safe: public
      entities, no persons, no coordinates — only country + area + public-owner bucket.

  Source attribution stays on every record (:parcel/source :wikidata); area is honest (rows
  whose unit could not be resolved were dropped at snapshot time, never guessed)."
  (:require [clojure.string :as str]
            [jinushi.methods.analyze :as analyze]
            #?(:clj [clojure.java.io :as io])))

(defn public-owner-key [cc] (str "o.public.np." cc))

(defn snapshot->dataset
  "Pure: a parsed snapshot map {:records [{:cc :area-m2 …} …]} → {:owners :parcels}.
  One PUBLIC owner bucket per country (national-park system); one parcel per record."
  [{:keys [records]}]
  (let [ccs (sort (distinct (map :cc records)))
        owners (mapv (fn [cc]
                       {:owner/key (public-owner-key cc)
                        :owner/name (str "National park system (" cc ")")
                        :owner/type :public})
                     ccs)
        ;; deterministic ids: per-country running index over snapshot order
        parcels (->> records
                     (group-by :cc)
                     (sort-by key)
                     (mapcat (fn [[cc rs]]
                               (map-indexed
                                (fn [i r]
                                  {:parcel/id (format "WD-NP-%s-%04d" cc (inc i))
                                   :parcel/country cc
                                   :parcel/region ""
                                   :parcel/area-m2 (:area-m2 r)
                                   :parcel/owner (public-owner-key cc)
                                   :parcel/source :wikidata})
                                rs)))
                     vec)]
    {:owners owners :parcels parcels}))

(defn merge-datasets
  "Combine many {:owners :parcels} into one (owners deduped by :owner/key, parcels concatenated).
  Lets a real snapshot and the synthetic seed be analyzed as one acquisition view."
  [& datasets]
  {:owners (->> (mapcat :owners datasets)
                (reduce (fn [m o] (assoc m (:owner/key o) o)) {})
                vals vec)
   :parcels (vec (mapcat :parcels datasets))})

#?(:clj
   (defn load-snapshot [f] (analyze/parse (slurp (io/file f)))))

#?(:clj
   (defn -main [& argv]
     (let [here (or (some-> (when (and *file* (not= *file* "NO_SOURCE_PATH")) (io/file *file*))
                            .getParentFile .getParentFile)
                    (io/file "20-actors/jinushi"))
           snap-f (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                    (io/file (first argv))
                    (io/file here "data" "acquired" "wikidata-national-parks.kotoba.edn"))
           snap (load-snapshot snap-f)
           ds (snapshot->dataset snap)
           res (analyze/analyze ds)
           cov (:coverage res)]
       (require 'jinushi.methods.coverage)
       (println ((resolve 'jinushi.methods.coverage/render) res))
       (println)
       (println (format ";; REAL ingest: %d parks → %d countries, %,.0f km² public land = %.4g%% of world land (snapshot %s, %d dropped-unknown-unit)"
                        (count (:parcels ds))
                        (:countries-touched cov)
                        (:acquired-area-km2 cov)
                        (* 100.0 (:world-coverage-frac cov))
                        (:retrieved snap)
                        (:dropped-unknown-unit snap)))
       0)))
