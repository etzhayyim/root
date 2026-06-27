(ns sheets.mapping
  "Canonical spreadsheet <-> :sheet/* datom mapping (clj port of lg_sheets/mapping.py,
  ADR-2606010500 D6).

  One spreadsheet = one datomic entity \"sheet:book:{slug}\". Worksheet metadata is a
  JSON list (:sheet/sheetsJson); cell values are a JSON object keyed by worksheet
  title (:sheet/gridJson = {title: [[stringified cells]]}). All map keys are strings
  to match the JSON wire shape used by the handlers."
  (:require [cheshire.core :as json]
            [sheets.ids :as ids]
            [sheets.edn-tx :refer [tx-add tx-retract]]))

;; field (book/input key, string) -> bare datom attr (string)
(def scalar-fields
  [["googleSpreadsheetId" "sheet/googleSpreadsheetId"]
   ["msDriveItemId" "sheet/msDriveItemId"]
   ["title" "sheet/title"]
   ["ownerDid" "sheet/ownerDid"]
   ["createdAtMs" "sheet/createdAtMs"]
   ["updatedAtMs" "sheet/updatedAtMs"]
   ["revision" "sheet/revision"]])

(def json-fields [["sheets" "sheet/sheetsJson"] ["grid" "sheet/gridJson"]])

(def defaults {"revision" 0})

(defn- dumps [v] (json/generate-string v))

(defn create-ops [slug book]
  (let [eid (ids/eid-for-slug slug)
        base [(tx-add eid "sheet/type" "Spreadsheet")
              (tx-add eid "sheet/id" eid)
              (tx-add eid "sheet/slug" slug)]
        scalars (for [[field attr] scalar-fields
                      :let [v (get book field (get defaults field))]
                      :when (some? v)]
                  (tx-add eid attr v))
        jsons (for [[field attr] json-fields
                    :when (some? (get book field))]
                (tx-add eid attr (dumps (get book field))))]
    (vec (concat base scalars jsons))))

(defn update-ops [slug current-attrs patch]
  (let [eid (ids/eid-for-slug slug)
        scalar-ops
        (mapcat (fn [[field attr]]
                  (if-not (contains? patch field)
                    []
                    (let [new-v (get patch field)
                          old-v (get current-attrs attr)]
                      (if (= old-v new-v)
                        []
                        (cond-> []
                          (some? old-v) (conj (tx-retract eid attr old-v))
                          (some? new-v) (conj (tx-add eid attr new-v)))))))
                scalar-fields)
        json-ops
        (mapcat (fn [[field attr]]
                  (if-not (contains? patch field)
                    []
                    (let [new-json (dumps (get patch field))
                          old-json (get current-attrs attr)]
                      (if (= old-json new-json)
                        []
                        (cond-> []
                          (some? old-json) (conj (tx-retract eid attr old-json))
                          true (conj (tx-add eid attr new-json)))))))
                json-fields)]
    (vec (concat scalar-ops json-ops))))

(defn- loads [raw default]
  (cond
    (nil? raw) default
    (not (string? raw)) raw
    :else (try (json/parse-string raw) (catch Exception _ default))))

(defn attrs->book
  "Spreadsheet metadata (no grid) — for spreadsheetsGet/Create responses."
  [attrs]
  (let [slug (or (get attrs "sheet/slug")
                 (ids/slug-from-eid (get attrs "sheet/id" "sheet:book:unknown")))
        scalars (into {} (for [[field attr] scalar-fields
                               :when (and (contains? attrs attr)
                                          (some? (get attrs attr)))]
                           [field (get attrs attr)]))
        book (merge {"spreadsheetId" slug}
                    scalars
                    {"sheets" (loads (get attrs "sheet/sheetsJson") [])})]
    (if (contains? book "revision")
      book
      (assoc book "revision" (get defaults "revision")))))

(defn attrs->grid [attrs]
  (loads (get attrs "sheet/gridJson") {}))
