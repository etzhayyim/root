#!/usr/bin/env bb
;; One-shot migration: collapse the verbose CLAUDE.md Status tables into a
;; lossless 90-docs/adr/status-registry.edn + a one-line-index Status section.
;; Repo rule: "This table is a one-line index only. Full detail lives in ADR."
(require '[clojure.string :as str])
(set! *warn-on-reflection* false)

(def root ".")
(def clmd (str root "/CLAUDE.md"))
(def out-edn (str root "/90-docs/adr/status-registry.edn"))

(def lines (str/split-lines (slurp clmd)))

;; --- locate Status section (## Status .. next ## ) ---
(def start-idx (->> (map-indexed vector lines)
                    (some (fn [[i l]] (when (str/starts-with? l "## Status") i)))))
(def end-idx
  (let [found (->> (map-indexed vector lines)
                   (some (fn [[i l]] (when (and (> i start-idx)
                                                (re-find #"^## " l)) i))))]
    (or found (count lines))))
(def status-lines (subvec lines start-idx end-idx))

;; --- parse ---
(defn row-cells [line]
  (let [bare (-> line str/trim (str/replace #"^\|" "") (str/replace #"\|$" ""))]
    (mapv str/trim (str/split bare #"\|"))))

(defn separator? [line]
  (let [cs (row-cells line)]
    (and (seq cs) (every? #(re-matches #"^[ :-]+$" %) cs))))

(defn header? [line]
 (let [cs (row-cells line)]
   (and (seq cs) (some #{"Item" "Actor" "Purpose"} cs))))

(defn short-purpose [p]
  (let [s (str/replace p #"\*\*" "")]
    (if (<= (count s) 110)
      s
      (let [cutters [" — " " – " "。 " "; " ". " " / " ": "]
            idxs (keep (fn [m]
                         (let [i (str/index-of s m 40)]
                           (when (and i (< i 130)) i)))
                       cutters)
            cut (or (when (seq idxs) (apply min idxs))
                    (let [sp (str/last-index-of s " " 110)] (or sp 110)))]
        (str (str/trim (subs s 0 cut)) " …")))))

(defn parse [lines]
  (let [section (atom nil) rows (atom [])]
    (doseq [ln lines]
      (cond
        (str/starts-with? ln "### ") (reset! section (str/trim (subs ln 4)))
        (and (str/starts-with? ln "|") (not (separator? ln)) (not (header? ln)))
        (let [cs (row-cells ln)]
          (when (>= (count cs) 5)
            (swap! rows conj {:section @section
                              :item    (nth cs 0)
                              :purpose (nth cs 1)
                              :status  (nth cs 2)
                              :adr     (nth cs 3)
                              :date    (nth cs 4)})))))
    @rows))

(def rows (parse status-lines))

;; --- emit EDN (lossless) ---
(defn emit-row [r]
  (let [fields [[:section (:section r)] [:item (:item r)] [:purpose (:purpose r)]
                [:status (:status r)] [:adr (:adr r)] [:date (:date r)]]]
    (str " {" (str/join " " (map (fn [[k v]] (str ":" (name k) " " (pr-str (or v "")))) fields)) "}")))

(def edn-text
  (str
   "; status-registry.edn — lossless detail for the CLAUDE.md Status tables.\n"
   "; Generated from CLAUDE.md ## Status by scripts/extract-status-registry.bb.\n"
   "; One row per Status table entry; :purpose is the FULL verbatim prose.\n"
   "; CLAUDE.md keeps a one-line index; this + each ADR hold the detail.\n\n"
   "[\n" (str/join "\n" (map emit-row rows)) "\n]\n"))

(spit out-edn edn-text)

;; --- emit trimmed Status section markdown ---
(defn md-row [r]
  (str "| " (:item r) " | " (short-purpose (:purpose r)) " | " (:status r)
       " | " (:adr r) " | " (:date r) " |"))

(def header-row "| Item | Purpose | Status | ADR | Date |")
(def sep-row    "|---|---|---|---|---|")

(defn emit-subsection [title rows]
  (str "### " title "\n\n" header-row "\n" sep-row "\n"
       (str/join "\n" (map md-row rows)) "\n"))

;; preserve order + subsection grouping as encountered
(def subsections (vec (distinct (map :section rows))))
(def trimmed
  (str
   "## Status\n\n"
   "**Legend**: ✅ shipped · 🟢 landed (substrate, tests green) · 🟡 R0 / proposed scaffold · ⏳ blocked/pending. "
   "Full detail for every row lives in its ADR and in [`90-docs/adr/status-registry.edn`](90-docs/adr/status-registry.edn) "
   "(verbatim prose); this table is a one-line index only — see [`90-docs/adr/README.md`](90-docs/adr/README.md).\n\n"
   (str/join "\n" (for [s subsections]
                    (emit-subsection s (filter #(= (:section %) s) rows))))))

;; --- splice back into CLAUDE.md ---
(def new-lines
  (concat (subvec lines 0 start-idx)
          (str/split-lines trimmed)
          (subvec lines end-idx)))

(spit clmd (str (str/join "\n" new-lines) "\n"))

(printf "rows=%d  edn=%s  claudemd=%s%n" (count rows) out-edn clmd)
