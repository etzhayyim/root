(ns kanae.methods.project-yoro
  "project_yoro — project kanae fundFlowEdge records into yoro :yoro.fiscal/* datoms.
  Babashka port of project_yoro.py. Stdlib only. Deterministic.")

(require '[clojure.string :as str])
(require '[cheshire.core :as json])

;; ---------------------------------------------------------------------------
;; Endpoint label → (handle, stage) lookup table
;; ---------------------------------------------------------------------------

;; Each entry: [pattern-fn handle stage]
;; pattern-fn receives the label string and returns truthy if it matches.
(def ^:private LABEL-DID
  [[(fn [s] (or (str/includes? s "一般会計")
                (str/includes? s "National Treasury")
                (str/includes? s "General Account")))
    "kokko" "L7"]
   [(fn [s] (or (str/includes? s "文部科学省")
                (str/includes? s "Ministry of Education")))
    "gov-jp-mext" "L5"]
   [(fn [s] (str/includes? s "国立大学法人"))
    "gov-jp-mext-univ-grants" "L1"]
   [(fn [s] (str/includes? s "科学技術振興"))
    "gov-jp-mext-sci-tech" "L1"]])

(def ^:private ACTOR-PREFIX "did:web:etzhayyim.com:actor:")

(def ^:private PROFILES
  {"gov-jp-mext"
   {"handle"      "gov-jp-mext.etzhayyim.com"
    "displayName" "文部科学省 (MEXT) — gov mirror"
    "description" "Government mirror-actor (observational, ADR-2606042330). 文教及び科学振興費 fiscal flow assembled by kanae from danjo budget ledger (:representative)."}})

;; ---------------------------------------------------------------------------
;; Helpers (must appear before project)
;; ---------------------------------------------------------------------------

(defn slug-did
  "Map an endpoint label to a stable mirror-actor DID (or deterministic fallback)."
  [label]
  (if-let [[_ handle _stage] (first (filter (fn [[pat-fn & _]] (pat-fn label)) LABEL-DID))]
    (str ACTOR-PREFIX handle)
    ;; fallback: deterministic slug from the label
    (let [slug (-> (str/lower-case label)
                   (str/replace #"[^a-z0-9]+" "-")
                   (str/replace #"^-+|-+$" ""))]
      (str ACTOR-PREFIX "gov-jp-" (subs slug 0 (min 32 (count slug)))))))

(defn stage-for
  "Return the stage tier for an endpoint label."
  [label]
  (if-let [[_ _handle stage] (first (filter (fn [[pat-fn & _]] (pat-fn label)) LABEL-DID))]
    stage
    "L5"))

(defn- make-datom
  "Build a {e a v_edn added} datom map."
  [e a value]
  {"e" e "a" a "v_edn" (json/generate-string value) "added" true})

;; ---------------------------------------------------------------------------
;; project
;; ---------------------------------------------------------------------------

(defn project
  "fundFlowEdge list -> :yoro.fiscal/* (+ minimal :yoro.profile/*) datoms."
  [edges]
  (let [seen-profiles (atom #{})]
    (reduce
      (fn [datoms edge]
        (let [from-label (get-in edge ["fromEndpoint" "label"])
              to-label   (get-in edge ["toEndpoint" "label"])
              from-did   (slug-did from-label)
              to-did     (slug-did to-label)
              fy         (Long/parseLong (str/replace (get edge "period" "FY0") "FY" ""))
              stage      (stage-for from-label)
              e          (str "fiscal:" from-did ":" to-did ":" fy ":" (get edge "flowClass"))
              edge-datoms [(make-datom e ":yoro.fiscal/from"        from-did)
                           (make-datom e ":yoro.fiscal/to"          to-did)
                           (make-datom e ":yoro.fiscal/stage"       stage)
                           (make-datom e ":yoro.fiscal/fiscalYear"  fy)
                           (make-datom e ":yoro.fiscal/amountJpy"   (Long/parseLong (get edge "amount" "0")))
                           (make-datom e ":yoro.fiscal/basis"
                                       (str (get edge "flowClass") " · "
                                            (get edge "_programCode" "")
                                            " (kanae assembled, :representative)"))
                           (make-datom e ":yoro.fiscal/programCode" (get edge "_programCode" ""))
                           (make-datom e ":yoro.fiscal/sourceUrl"   (get edge "_sourceUrl" ""))
                           (make-datom e ":yoro.fiscal/observedAt"  (get edge "observedAt" ""))]
              ;; minimal profiles for endpoints that have one defined
              profile-datoms
              (reduce
                (fn [pds label]
                  (let [did    (slug-did label)
                        handle (subs did (count ACTOR-PREFIX))
                        prof   (get PROFILES handle)]
                    (if (and prof (not (contains? @seen-profiles did)))
                      (do
                        (swap! seen-profiles conj did)
                        (let [pe (str "profile:" did)]
                          (concat pds
                                  [(make-datom pe ":yoro.profile/did"         did)
                                   (make-datom pe ":yoro.profile/handle"      (get prof "handle"))
                                   (make-datom pe ":yoro.profile/displayName" (get prof "displayName"))
                                   (make-datom pe ":yoro.profile/description" (get prof "description"))])))
                      pds)))
                []
                [from-label to-label])]
          (concat datoms edge-datoms profile-datoms)))
      []
      edges)))

;; ---------------------------------------------------------------------------
;; merge-into-seed
;; ---------------------------------------------------------------------------

(defn merge-into-seed
  "Idempotently merge projected datoms into the yoro seed snapshot (JSON file).

  Removes any prior :yoro.fiscal/* entities owned by this projector before adding,
  so re-runs don't duplicate. The hand-authored ooyake demo seed is left untouched."
  [seed-path datoms]
  (let [seed       (json/parse-string (slurp seed-path))
        owned      (set (map #(get % "e") datoms))
        before     (count seed)
        remaining  (filterv #(not (contains? owned (get % "e"))) seed)
        removed    (- before (count remaining))
        merged     (concat remaining datoms)]
    (spit seed-path (json/generate-string merged))
    {"removed" removed "added" (count datoms) "total" (count merged)}))
