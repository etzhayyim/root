;; etzhayyim.data-provenance — validator for the actor data-ownership model
;; (ADR-2607010001). Cross-checks RAD :rad/holds-dataset / dataset:<id>
;; sub-entities against the CIDs recorded in 80-data/* provenance, pin, and
;; coverage-manifest files. Offline (no IPFS daemon); reuses the kotoba Datom
;; log reader. clj/bb per the repo "Operational code = clj/bb" rule.
;; `bb lint:provenance` — exits non-zero on any holding that is missing a
;; required field or whose :rad/cidv1 is not recorded anywhere in 80-data.
(ns etzhayyim.data-provenance
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.log :as log]
            [etzhayyim.kotoba.cid :as cid]))

;; ── collect holdings from RAD journals ──────────────────────────────────────

(defn journal-holdings
  "Read one actor's RAD identity journal → {:actor :rid :datasets [...]}.
   Each dataset map carries the dataset:<id> sub-entity fields
   (:rad/dataset-id :layer :source :cidv1 :freshness-days :retrieved
   :counts-toward-world-coverage)."
  [journal-path]
  (when (.exists (io/file journal-path))
    (let [logv   (log/read-log journal-path)
          rid    (some #(when (and (= :rad/type (d/d-a %)) (= :identity (d/d-v %)))
                          (d/d-e %)) logv)
          actor  (some #(when (= :rad/name (d/d-a %)) (d/d-v %)) logv)
          ids    (set (map d/d-v (filter #(= :rad/holds-dataset (d/d-a %)) logv)))]
      {:actor actor :rid rid
       :datasets (for [id ids
                       :let [kv (into {}
                                      (map (juxt d/d-a d/d-v))
                                      (filter #(= (str "dataset:" id) (d/d-e %)) logv))]]
                   {:dataset-id                  (:rad/dataset-id kv)
                    :layer                       (:rad/layer kv)
                    :source                      (:rad/source kv)
                    :cidv1                       (:rad/cidv1 kv)
                    :freshness-days              (:rad/freshness-days kv)
                    :retrieved                   (:rad/retrieved kv)
                    :counts-toward-world-coverage (:rad/counts-toward-world-coverage kv)})})))

(defn all-holdings
  "Sweep <rad-dir>/*.identity.journal.edn → seq of {:actor :rid :datasets}."
  [rad-dir]
  (->> (file-seq (io/file rad-dir))
       (filter #(and (.isFile %)
                     (str/ends-with? (.getName %) ".identity.journal.edn")))
       (keep journal-holdings)))

;; ── cidv1 reference integrity ───────────────────────────────────────────────

(def ^:private provenance-suffixes
  "Files that record dataset CIDs we cross-check against :rad/cidv1."
  ["ingest-provenance.json" "-manifest.json" "ipfs-pins.kotoba.edn"])

(defn known-cids-in
  "Walk <data-dir> (80-data); collect every CIDv1 string (baf…) mentioned in
   ingest-provenance.json / *-manifest.json / ipfs-pins.kotoba.edn files."
  [data-dir]
  (into #{}
        (comp (filter #(.isFile %))
              (filter #(some (fn [sfx] (str/ends-with? (.getName %) sfx))
                             provenance-suffixes))
              (mapcat #(re-seq #"baf[a-z0-9]{30,}" (slurp %))))
        (file-seq (io/file data-dir))))

(defn actor-dataset-cids
  "Content-CIDs of actor-level dataset files (registry/*.seed.json + data/*.kotoba.edn),
   computed via cid-of-file so :rad/cidv1 can point at a dataset file directly — not just
   at a CID recorded inside a provenance/pin manifest. ADR-2607010001."
  [actors-dir]
  (into #{}
        (comp (filter #(.isFile %))
              (filter #(let [n (.getName %) p (.getPath %)]
                         (or (and (str/ends-with? n ".seed.json")
                                  (str/includes? p "/registry/"))
                             (and (str/ends-with? n ".kotoba.edn")
                                  (str/includes? p "/data/")))))
              (keep #(try (cid/cid-of-file (.getPath %))
                          (catch Exception _ nil))))
        (file-seq (io/file actors-dir))))

(defn data-dataset-cids
  "Content-CIDs of 80-data dataset projection files (*.kotoba.edn), computed via
   cid-of-file so :rad/cidv1 can point at a dataset projection file directly
   (complements known-cids-in, which only collects CID strings mentioned INSIDE
   provenance/pin/manifest files). ADR-2607010001."
  [data-dir]
  (into #{}
        (comp (filter #(.isFile %))
              (filter #(str/ends-with? (.getName %) ".kotoba.edn"))
              (keep #(try (cid/cid-of-file (.getPath %))
                          (catch Exception _ nil))))
        (file-seq (io/file data-dir))))

(defn validate-holding
  "Required fields present? cidv1 resolves to a CID recorded in 80-data?
   Returns {:dataset-id :ok? :missing-required :cid-resolves?}."
  [known-cids holding]
  (let [missing   (remove #(some? (get holding %)) [:dataset-id :layer :cidv1])
        resolves? (or (nil? (:cidv1 holding))
                      (contains? known-cids (:cidv1 holding)))]
    {:dataset-id       (:dataset-id holding)
     :ok?              (and (empty? missing) resolves?)
     :missing-required (seq missing)
     :cid-resolves?    resolves?}))

(defn validate
  "Sweep RAD journals, cross-check holdings against 80-data CIDs.
   Returns {:actors :holdings :ok :problems}."
  [{:keys [rad-dir data-dir actors-dir]}]
  (let [known   (-> (known-cids-in data-dir)
                    (into (when actors-dir (actor-dataset-cids actors-dir)))
                    (into (data-dataset-cids data-dir)))
        hs      (all-holdings rad-dir)
        results (for [{:keys [actor datasets]} hs
                      h datasets
                      :let [v (validate-holding known h)]]
                  (assoc v :actor actor))]
    {:actors   (count hs)
     :holdings (count results)
     :ok       (count (filter :ok? results))
     :problems (remove :ok? results)}))

(defn -main
  "bb lint:provenance — validate RAD holdings cross-reference 80-data."
  [& _]
  (let [res     (validate {:rad-dir "80-data/kotoba-rad" :data-dir "80-data" :actors-dir "20-actors"})
        problems (:problems res)]
    (println (format "actors=%d holdings=%d ok=%d problems=%d"
                     (:actors res) (:holdings res) (:ok res) (count problems)))
    (doseq [p problems]
      (println "  PROBLEM" (:actor p) (:dataset-id p)
               (or (seq (:missing-required p))
                   (when-not (:cid-resolves? p) "cid-not-found-in-80-data"))))
    (System/exit (if (seq problems) 1 0))))
