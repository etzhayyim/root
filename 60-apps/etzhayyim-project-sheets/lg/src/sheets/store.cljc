(ns sheets.store
  "Sheets persistence stores (clj port of lg_sheets/store.py).

  `SheetStore` is the narrow interface the handlers use. Two implementations:
  - `KotobaSheetStore` — production, backed by kotoba datomic (graph sheets-v1).
  - `FakeSheetStore`   — in-memory atom, used by the deterministic unit tests.

  Both speak the same EDN tx-op vocabulary ([:db/add ...] / [:db/retract ...] /
  [:db.fn/retractEntity ...]), so the handlers are storage-agnostic. Methods are
  synchronous (babashka.http-client is blocking) — the Python `async` is dropped."
  (:require [clojure.string :as str]
            [sheets.ids :as ids]
            [sheets.edn-tx :as edn-tx]
            [sheets.kotoba-datomic :as kd]))

(defprotocol SheetStore
  (get-book-attrs [s slug])
  (all-book-attrs [s])
  (lookup-slug [s attr value])
  (write-ops [s ops]))

(defn- bare-attr [a]
  (let [s (str a)]
    (if (str/starts-with? s ":") (subs s 1) s)))

;; ── kotoba datomic implementation ─────────────────────────────────────────────

(defrecord KotobaSheetStore [dm]
  SheetStore
  (get-book-attrs [_ slug]
    (kd/pull dm (ids/eid-for-slug slug)))
  (all-book-attrs [this]
    (let [rows (kd/q dm "[:find ?slug :where [?e :sheet/type \"Spreadsheet\"] [?e :sheet/slug ?slug]]")]
      (vec (keep (fn [row]
                   (when (seq row)
                     (get-book-attrs this (str (first row)))))
                 rows))))
  (lookup-slug [_ attr value]
    ;; Inline the EDN-encoded value into the query (proven yatabase get_entity
    ;; pattern), rather than an `:in $ ?v` binding.
    (let [b (if (str/starts-with? attr ":") (subs attr 1) attr)
          query (str "[:find ?slug :where [?e :" b " " (edn-tx/encode value) "] [?e :sheet/slug ?slug]]")
          rows (kd/q dm query)]
      (when (and (seq rows) (seq (first rows)))
        (str (ffirst rows)))))
  (write-ops [_ ops]
    (when (seq ops)
      (kd/transact dm ops))))

(defn kotoba-sheet-store [dm] (->KotobaSheetStore dm))

;; ── in-memory fake (tests) ────────────────────────────────────────────────────

(defn- apply-op! [db op]
  (let [kind (str (first op))]
    (if (= kind ":db.fn/retractEntity")
      (swap! db dissoc (ids/slug-from-eid (str (second op))))
      (let [[_ eid attr value] op
            ba (bare-attr attr)
            slug (ids/slug-from-eid (str eid))]
        (case kind
          ":db/add" (swap! db update slug assoc ba value)
          ":db/retract" (swap! db update slug
                               (fn [row] (if (= (get row ba) value) (dissoc row ba) row)))
          nil)))))

(deftype FakeSheetStore [db]
  SheetStore
  (get-book-attrs [_ slug] (get @db slug))
  (all-book-attrs [_] (vec (vals @db)))
  (lookup-slug [_ attr value]
    (let [ba (if (str/starts-with? attr ":") (subs attr 1) attr)]
      (some (fn [[slug attrs]] (when (= (get attrs ba) value) slug)) @db)))
  (write-ops [_ ops] (doseq [op ops] (apply-op! db op))))

(defn fake-sheet-store [] (->FakeSheetStore (atom {})))
