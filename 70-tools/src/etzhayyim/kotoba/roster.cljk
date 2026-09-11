;; etzhayyim.kotoba.roster — roster-wide kotoba maturity report.
;;
;; Auto-discovers every actor seed that names its :vocabulary, ingests each into
;; the kotoba engine (etzhayyim.kotoba.ingest), and emits a single maturity
;; matrix: entities · live datoms · schema conformance · content-address. One
;; command to see which 🟡 R0 actors are kotoba-substrate-ready. Read-only over
;; existing root data; nothing written to the kotoba subrepo.
;;
;; CLI:  bb kotoba:roster-report

(ns etzhayyim.kotoba.roster
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [etzhayyim.kotoba.ingest :as ingest]))

(defn- vocab-of [f]
  (second (re-find #"vocabulary[:\s]+([a-z0-9-]+-ontology)"
                   (apply str (take 600 (slurp f))))))

(defn discover
  "Seq of {:actor :schema :seed} for every actor seed that names a vocabulary
   present in 00-contracts/schemas/."
  []
  (->> (file-seq (io/file "20-actors"))
       (filter #(and (str/includes? (.getPath %) "/data/")
                     (str/ends-with? (.getName %) ".kotoba.edn")))
       (keep (fn [f]
               (when-let [vh (vocab-of f)]
                 (let [sp (str "00-contracts/schemas/" vh ".kotoba.edn")]
                   (when (.exists (io/file sp))
                     {:actor (-> f .getParentFile .getParentFile .getName)
                      :schema sp :seed (.getPath f)})))))
       (sort-by :actor)
       vec))

(defn report
  "Ingest every discovered actor and return a vector of row maps:
   {:actor :entities :datoms :undeclared :value-violations :head}."
  []
  (for [{:keys [actor schema seed]} (discover)]
    (let [j (str (System/getProperty "java.io.tmpdir") "/roster-" actor "-" (System/nanoTime) ".edn")]
      (try
        (let [r (ingest/ingest-actor {:schema schema :seed seed :journal j})]
          {:actor actor :entities (:entities r) :datoms (:datoms r)
           :undeclared (count (:undeclared r)) :value-violations (:value-violations r)
           :head (:head r)})
        (catch Exception e {:actor actor :error (.getMessage e)})
        (finally (io/delete-file j true))))))

(defn report->md [rows]
  (str "# kotoba roster maturity\n\n"
       "| actor | entities | datoms | undeclared | value-viol | head CID |\n"
       "|---|--:|--:|--:|--:|---|\n"
       (str/join "\n"
                 (for [r rows]
                   (if (:error r)
                     (format "| %s | ERROR: %s |" (:actor r) (:error r))
                     (format "| %s | %d | %d | %d | %s | `%s…` |"
                             (:actor r) (:entities r) (:datoms r) (:undeclared r)
                             (str (:value-violations r)) (subs (:head r) 0 16)))))
       "\n"))

(defn -main [& _]
  (let [rows (vec (report))
        clean (filter #(and (not (:error %)) (zero? (:undeclared %))) rows)]
    (println (report->md rows))
    (println (format "\n%d/%d actors ingested with zero undeclared-attr drift."
                     (count clean) (count rows)))
    (println (format "total: %d entities, %d live datoms across the roster."
                     (reduce + (keep :entities rows)) (reduce + (keep :datoms rows))))))
