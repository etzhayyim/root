(ns sheets.gitoffice-normalize
  "GitOffice edge adapter — :sheet/gridJson blob <-> sparse :cell/* datoms
  (clj port of lg_sheets/gitoffice_normalize.py, doc e §13 option 1).

  Converts the workbook blob (:sheet/gridJson = {title: [[cell]]}) to sparse
  [:db/add e a v] ops (each non-empty cell its own datom, keyed by absolute A1
  ref \"<sheet>!<A1>\") and rows -> blob trimmed to the non-empty bounding box."
  (:require [clojure.string :as str]
            [sheets.edn-tx :refer [tx-add]]))

;; --- A1 notation ------------------------------------------------------------

(defn col->a1 [c]
  (loop [n (inc c) s ""]
    (if (pos? n)
      (let [q (quot (dec n) 26)
            r (mod (dec n) 26)]
        (recur q (str (char (+ 65 r)) s)))
      s)))

(defn a1->col [letters]
  (dec (reduce (fn [acc ch] (+ (* acc 26) (- (int ch) 64))) 0 letters)))

(defn cell-id [sheet row col]
  (str sheet "!" (col->a1 col) (inc row)))

(defn- nonempty? [v] (not (or (nil? v) (= v ""))))

(defn bare [a]
  (let [s (str a)]
    (if (str/starts-with? s ":") (subs s 1) s)))

;; --- blob -> datom ops ------------------------------------------------------

(defn grid->cell-ops
  ":sheet/gridJson -> [:db/add e a v] ops (sparse: only non-empty cells)."
  [book-id grid-json]
  (vec
   (for [[sheet grid] grid-json
         [r rowvals] (map-indexed vector grid)
         [c val] (map-indexed vector rowvals)
         :when (nonempty? val)
         :let [cid (cell-id sheet r c)]
         op [(tx-add cid "cell/book" book-id)
             (tx-add cid "cell/sheet" sheet)
             (tx-add cid "cell/ref" (str (col->a1 c) (inc r)))
             (tx-add cid "cell/row" r)
             (tx-add cid "cell/col" c)
             (tx-add cid "cell/value" val)]]
     op)))

;; --- datom rows -> blob -----------------------------------------------------

(defn cells->grid
  "Decoded (e a v) rows -> :sheet/gridJson (each sheet trimmed to bbox)."
  [rows book-id]
  (let [cells (reduce (fn [acc [e a v]]
                        (let [attr (bare a)]
                          (if (str/starts-with? attr "cell/")
                            (assoc-in acc [e attr] v)
                            acc)))
                      {} rows)
        cells (into {} (filter (fn [[_ at]] (= (get at "cell/book") book-id)) cells))
        by-sheet (reduce (fn [acc at]
                           (update acc (get at "cell/sheet") (fnil conj [])
                                   [(get at "cell/row") (get at "cell/col") (get at "cell/value")]))
                         {} (vals cells))]
    (into {}
          (for [[sheet items] by-sheet]
            (let [rows-n (inc (apply max (map first items)))
                  cols-n (inc (apply max (map second items)))
                  empty-grid (vec (repeat rows-n (vec (repeat cols-n ""))))
                  grid (reduce (fn [g [r c val]] (assoc-in g [r c] val))
                               empty-grid items)]
              [sheet grid])))))

(defn trim-grid
  "One grid -> non-empty bounding rectangle (the sparse round-trip fixed point)."
  [grid]
  (let [coords (for [r (range (count grid))
                     c (range (count (nth grid r)))
                     :when (nonempty? (get-in grid [r c]))]
                 [r c])]
    (if (empty? coords)
      []
      (let [rows-n (inc (apply max (map first coords)))
            cols-n (inc (apply max (map second coords)))]
        (vec (for [r (range rows-n)]
               (vec (for [c (range cols-n)]
                      (let [row (nth grid r)]
                        (if (and (< c (count row)) (some? (nth row c)))
                          (nth row c)
                          ""))))))))))

(defn ops->rows [ops]
  (vec (for [op ops :when (= 4 (count op))] [(nth op 1) (nth op 2) (nth op 3)])))
