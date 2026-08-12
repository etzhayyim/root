;; Regenerate 90-docs/_registry/graph.edn from 90-docs/_registry/docs.edn.
;;
;; graph.edn is the typed relation-graph projection of the docs registry —
;; the EDN successor to the former graph.jsonld (JSON-LD) projection
;; (retired per the "use EDN, not JSON-LD" directive, ADR-2606231808 lineage).
;; It carries the same schema.org / dc:terms / etzhayyim ontology predicates as
;; the :context block (so the linked-data semantics are preserved verbatim) and
;; a :graph vector of one node per registry entry with typed relations.
;;
;; clj-native per the repo's babashka direction (same as regen-registry.clj);
;; no Python dependency. Reads docs.edn (the EDN registry, kebab-case keyword
;; keys) so the chain is fully EDN end-to-end:
;;
;;   .md → docs.edn → graph.edn
;;
;; (docs.edn is itself regenerated from .md front-matter by regen-registry.clj
;; in lock-step with docs.json; the docs-registry-freshness gate guards it.)
;;
;; Idempotent. Nodes sorted by :id. Pure function of docs.edn (no timestamp),
;; so re-running on unchanged input is byte-identical.
;;
;; Usage:
;;   bb 70-tools/scripts/docs/regen-graph-edn.clj
;;   bb 70-tools/scripts/docs/regen-graph-edn.clj --check   ; exit 1 on drift
;;   bb 70-tools/scripts/docs/regen-graph-edn.clj --edn     ; plan-only EDN (stdout)

(ns regen-graph-edn
  (:require [babashka.fs :as fs]
            [clojure.edn :as edn]
            [clojure.string :as str]))

;; REPO = parents[3] of this script: docs -> scripts -> 70-tools -> REPO
(def repo
  (-> (or *file* "70-tools/scripts/docs/regen-graph-edn.clj")
      fs/absolutize fs/parent fs/parent fs/parent fs/parent
      str))

(def docs-edn (str (fs/path repo "90-docs" "_registry" "docs.edn")))
(def graph-edn (str (fs/path repo "90-docs" "_registry" "graph.edn")))

;; ── ontology (mirrors the former graph.jsonld @context, EDN keyword keys) ────
;; Typed relations carry {:id <predicate-IRI> :type "@id"} so a linked-data
;; consumer can resolve the reference within the :graph; scalar predicates map
;; the key straight to its IRI.
(def context
  {:id "@id"
   :type "@type"
   :title "http://purl.org/dc/terms/title"
   :status "https://schema.org/creativeWorkStatus"
   :topic "https://schema.org/about"
   :authoritative "https://schema.org/authoritativeLegalValue"
   :authoritative-for "https://etzhayyim.com/docs/authoritativeFor"
   :related {:id "https://schema.org/isRelatedTo" :type "@id"}
   :supersedes {:id "https://schema.org/supersedes" :type "@id"}
   :superseded-by {:id "https://schema.org/supersededBy" :type "@id"}
   :amends {:id "https://etzhayyim.com/docs/amends" :type "@id"}
   :amended-by {:id "https://etzhayyim.com/docs/amendedBy" :type "@id"}
   :last-verified "https://schema.org/dateModified"})

;; docs.edn :doc-type → schema.org type. Default = TechArticle.
(def doc-type->schema
  {"adr" "TechArticle"
   "explanation" "Article"
   "reference" "TechArticle"
   "how-to" "TechArticle"
   "tutorial" "Article"})

(defn- doc-iri [id] (str "doc:" id))

(defn project-entry
  "Convert one docs.edn entry to a graph node, or nil if it has no :id."
  [entry]
  (let [id (:id entry)]
    (when (and id (not (str/blank? (str id))))
      (cond-> {:id (doc-iri id)
               :type (get doc-type->schema (:doc-type entry) "TechArticle")}
        (not (str/blank? (str (:title entry))))  (assoc :title (:title entry))
        (not (str/blank? (str (:status entry)))) (assoc :status (:status entry))
        (not (str/blank? (str (:topic entry))))  (assoc :topic (:topic entry))
        (some? (:authoritative entry))           (assoc :authoritative (boolean (:authoritative entry)))
        (seq (:authoritative-for entry))         (assoc :authoritative-for (vec (:authoritative-for entry)))
        (seq (:related entry))                   (assoc :related (mapv doc-iri (:related entry)))
        (seq (:supersedes entry))                (assoc :supersedes (mapv doc-iri (:supersedes entry)))
        (seq (:superseded-by entry))             (assoc :superseded-by (mapv doc-iri (:superseded-by entry)))
        (seq (:amends entry))                    (assoc :amends (mapv doc-iri (:amends entry)))
        (seq (:amended-by entry))                (assoc :amended-by (mapv doc-iri (:amended-by entry)))
        (not (str/blank? (str (:last-verified entry)))) (assoc :last-verified (:last-verified entry))))))

(defn build-graph
  "Read docs.edn, project every entry, return {:context ... :graph [...]}"
  [docs]
  {:context context
   :graph (->> (:entries docs)
               (keep project-entry)
               (sort-by :id)
               vec)})

;; ── deterministic EDN renderer (byte-stable, human-diffable) ────────────────

(defn- edn-string [s]
  (str \" (-> (str s)
              (str/replace "\\" "\\\\")
              (str/replace "\"" "\\\""))
       \"))

(defn- edn-scalar [v]
  (cond
    (string? v)  (edn-string v)
    (boolean? v) (str v)
    (keyword? v) (str v)
    :else (edn-string (str v))))

(defn- edn-vector [xs]
  (str "[" (str/join " " (map edn-scalar xs)) "]"))

;; Fixed key order for graph nodes (matches the projection order in
;; project-entry so the diff reads top-to-bottom by salience).
(def node-key-order
  [:id :type :title :status :topic :authoritative
   :authoritative-for :related :supersedes :superseded-by
   :amends :amended-by :last-verified])

(defn- edn-node [node]
  (->> node-key-order
       (keep (fn [k]
               (when (contains? node k)
                 (let [v (get node k)]
                   (str k " " (if (vector? v) (edn-vector v) (edn-scalar v)))))))
       (str/join " ")
       (#(str "{" % "}"))))

;; Context rendered with the same fixed predicate order as the `context` def.
(def context-key-order
  [:id :type :title :status :topic :authoritative :authoritative-for
   :related :supersedes :superseded-by :amends :amended-by :last-verified])

(defn- edn-context-val [v]
  (if (map? v)
    (str "{:id " (edn-string (:id v)) " :type " (edn-string (:type v)) "}")
    (edn-string v)))

(defn- render-context []
  (->> context-key-order
       (map (fn [k] (str " " k " " (edn-context-val (get context k)))))
       (str/join "\n ")
       (#(str "{" (str/triml %) "}"))))

(defn render-edn [g]
  (str "{:context\n " (render-context) "\n"
       " :graph\n"
       " [" (str/join "\n  " (map edn-node (:graph g))) "]}\n"))

;; ── main ────────────────────────────────────────────────────────────────────

(defn- load-docs []
  (when-not (fs/exists? docs-edn)
    (binding [*out* *err*]
      (println (str "regen-graph-edn: source not found at 90-docs/_registry/docs.edn; "
                     "run regen-registry.clj first")))
    (System/exit 2))
  (edn/read-string (slurp docs-edn)))

(defn -main [& args]
  (let [args (set args)
        g (build-graph (load-docs))
        rendered (render-edn g)
        n (count (:graph g))]
    (cond
      (contains? args "--edn")
      (do (print rendered) 0)

      (contains? args "--check")
      (let [on-disk (if (fs/exists? graph-edn) (slurp graph-edn) "")]
        (if (= on-disk rendered)
          (do (println (str "graph.edn in sync (" n " nodes)")) 0)
          (binding [*out* *err*]
            (let [old-n (try (count (:graph (edn/read-string on-disk))) (catch Exception _ 0))]
              (println (str "graph.edn drift detected: disk=" n " nodes, file=" old-n " nodes"))
              (println "run: nbb scripts/run-task.cljs docs:graph-edn")
              1))))

      :else
      (do (spit graph-edn rendered)
          (println (str "wrote 90-docs/_registry/graph.edn with " n " nodes"))
          0))))

;; Run main unless a LIBRARY CONSUMER says otherwise -- same inversion, and same reason, as
;; regen-registry.clj's guard: `(= *file* (System/getProperty "babashka.file"))` is false under
;; every runtime except babashka, so running this generator with `clojure` regenerated nothing and
;; exited 0. The default belongs on the side a silent no-op ruins.
(when-not (System/getProperty "regen-graph-edn.library-load")
  (System/exit (apply -main *command-line-args*)))
