#!/usr/bin/env bb
;; Regenerate the Status index from 90-docs/adr/status-registry.edn:
;;   * 90-docs/adr/status-index.md  — full human-readable one-line table (all subsections)
;;   * CLAUDE.md ## Status          — lean legend + pointer + per-subsection counts
;; Lossless prose stays in status-registry.edn; each ADR holds the detail.
(require '[clojure.string :as str]
         '[clojure.edn :as edn])

(def root ".")
(def clmd (str root "/CLAUDE.md"))
(def idx-md (str root "/90-docs/adr/status-index.md"))
(def rows (edn/read-string (slurp (str root "/90-docs/adr/status-registry.edn"))))

(def CAP 70)
(defn short-purpose [p]
  (let [s (str/replace (or p "") #"\*\*" "")]
    (if (<= (count s) CAP)
      s
      (let [cutters [" — " " – " "。 " "; " ". " " / " ": "]
            idxs (keep (fn [m] (let [i (str/index-of s m 24)] (when (and i (< i (+ CAP 20))) i))) cutters)
            cut (or (when (seq idxs) (apply min idxs))
                    (let [sp (str/last-index-of s " " CAP)] (or sp CAP)))]
        (str (str/trim (subs s 0 cut)) " …")))))

(def header-row "| Item | Purpose | Status | ADR | Date |")
(def sep-row    "|---|---|---|---|---|")
(defn md-row [r] (str "| " (:item r) " | " (short-purpose (:purpose r)) " | " (:status r) " | " (:adr r) " | " (:date r) " |"))
(defn emit-sub [title rs]
  (str "### " title "\n\n" header-row "\n" sep-row "\n" (str/join "\n" (map md-row rs)) "\n"))

(def subsections (vec (distinct (map :section rows))))

;; --- full human-readable index file ---
(def idx-text
  (str
   "# Status index\n\n"
   "> Generated from [`status-registry.edn`](status-registry.edn) by `scripts/regen-status.bb`. "
   "One-line index; full verbatim prose per row is in the registry, and each row's ADR holds the detail. "
   "Linked from `CLAUDE.md` ## Status.\n\n"
   "**Legend**: ✅ shipped · 🟢 landed (substrate, tests green) · 🟡 R0 / proposed scaffold · ⏳ blocked/pending.\n\n"
   (str/join "\n" (for [s subsections] (emit-sub s (filter #(= (:section %) s) rows))))))
(spit idx-md idx-text)

;; --- lean CLAUDE.md ## Status section ---
(def counts (for [s subsections] (str "- **" s "** — " (count (filter #(= (:section %) s) rows)) " rows")))
(def lean
  (str
   "## Status\n\n"
   "**Legend**: ✅ shipped · 🟢 landed (substrate, tests green) · 🟡 R0 / proposed scaffold · ⏳ blocked/pending.\n\n"
   "The full one-line index (191 rows across the 3 subsections below) lives in "
   "[`90-docs/adr/status-index.md`](90-docs/adr/status-index.md); lossless verbatim prose per row lives in "
   "[`90-docs/adr/status-registry.edn`](90-docs/adr/status-registry.edn); each row's ADR holds the detail — "
   "see [`90-docs/adr/README.md`](90-docs/adr/README.md). This section is a pointer, not a duplicate of the table.\n\n"
   (str/join "\n" counts) "\n"))

;; splice into CLAUDE.md
(def lines (str/split-lines (slurp clmd)))
(def start-idx (->> (map-indexed vector lines) (some (fn [[i l]] (when (str/starts-with? l "## Status") i)))))
(def end-idx (let [f (->> (map-indexed vector lines) (some (fn [[i l]] (when (and (> i start-idx) (re-find #"^## " l)) i))))] (or f (count lines))))
(def new-lines (concat (subvec lines 0 start-idx) (str/split-lines lean) [""] (subvec lines end-idx)))
(spit clmd (str (str/join "\n" new-lines) "\n"))
(printf "wrote %s + lean CLAUDE.md Status; rows=%d%n" idx-md (count rows))