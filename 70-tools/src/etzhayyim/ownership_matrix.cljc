;; etzhayyim.ownership-matrix — GENERATED projection joining actor manifests
;; (:substrate :datasets) with RAD identity journals (:rad/holds-dataset), per
;; ADR-2607010001 §D2 (manifest = source, matrix = projection, RAD = attestation).
;; Emits 80-data/kotoba-rad/ownership-matrix.edn. Never hand-edit; regenerate.
;; `bb rad:ownership-matrix` writes; `--check` is the freshness gate.
(ns etzhayyim.ownership-matrix
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.pprint :as pp]
            [clojure.string :as str]
            [cheshire.core :as json]
            [etzhayyim.data-provenance :as prov]))

(defn- read-manifest [f]
  (let [f (io/file f)]
    (when (.exists f)
      (if (str/ends-with? (.getName f) ".edn")
        (edn/read-string (slurp f))
        (json/parse-string (slurp f) true)))))

(defn- actor-manifests
  "Scan <actors-dir>/ for actor manifests; return seq of {:actor :datasets}
   for every actor that declares a :substrate :datasets block."
  [actors-dir]
  (keep (fn [d]
          (when (.isDirectory d)
            (let [name (.getName d)
                  f (or (io/file (str actors-dir "/" name "/manifest.edn"))
                        (io/file (str actors-dir "/" name "/manifest.jsonld"))
                        (io/file (str actors-dir "/" name "/actor-manifest.jsonld")))]
              (when-let [m (read-manifest f)]
                {:actor name :datasets (-> m :substrate :datasets)}))))
        (.listFiles (io/file actors-dir))))

(defn generate
  "Join declared (manifests) + attested (RAD journals) holdings into a matrix.
   {:generated-by :actors {<name> {:rid :datasets :declared?}} :datasets {<id> {:holders :layers}}}."
  [{:keys [actors-dir rad-dir]}]
  (let [declared (into {} (map (juxt :actor :datasets)
                               (filter #(seq (:datasets %))
                                       (actor-manifests actors-dir))))
        attested (prov/all-holdings rad-dir)
        actors (into {}
                     (for [{:keys [actor rid datasets]} attested]
                       [actor {:rid rid
                               :datasets datasets
                               :declared? (boolean (get declared actor))}]))
        dataset-index (->> attested
                           (mapcat (fn [{:keys [actor datasets]}]
                                     (map #(assoc % :holder actor) datasets)))
                           (group-by :dataset-id))]
    {:generated-by "etzhayyim.ownership-matrix"
     :actors actors
     :datasets (into {}
                     (for [[id holders] dataset-index]
                       [id {:holders (vec (sort (set (map :holder holders))))
                            :layers  (vec (sort (set (map :layer holders))))}]))}))

(defn- render [matrix]
  (str (with-out-str (pp/pprint matrix)) "\n"))

(defn -main
  "bb rad:ownership-matrix [--check]. Generates (or verifies freshness of)
   80-data/kotoba-rad/ownership-matrix.edn."
  [& args]
  (let [check?    (some #(= "--check" %) args)
        matrix    (generate {:actors-dir "20-actors" :rad-dir "80-data/kotoba-rad"})
        out       "80-data/kotoba-rad/ownership-matrix.edn"
        rendered  (render matrix)]
    (if check?
      (let [disk (when (.exists (io/file out)) (slurp out))]
        (if (= disk rendered)
          (do (println "✓ ownership-matrix.edn up to date")
              (System/exit 0))
          (do (println "STALE ownership-matrix.edn — run `bb rad:ownership-matrix` (no --check)")
              (System/exit 1))))
      (do (io/make-parents (io/file out))
          (spit out rendered)
          (println (format "→ %s (%d actors, %d datasets)"
                           out (count (:actors matrix)) (count (:datasets matrix))))))))
