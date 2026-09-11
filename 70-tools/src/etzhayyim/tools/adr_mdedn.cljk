(ns etzhayyim.tools.adr-mdedn
  "`.md.edn` — markdown-as-commented-EDN for ADRs (option A, ADR-2606162200).

  A `.md.edn` file is ONE valid EDN map whose metadata are typed EDN keys and whose
  prose body is a `#md \"…\"` tagged string (markdown verbatim). Because it is plain
  EDN it supports `;;` line comments and `#_` form-discard, and is machine-readable
  without a YAML parser. The trade-off (no GitHub markdown rendering + `\"`/`\\`
  escaping in the body) is handled by tooling: `.md.edn` is canonical, the `.md` is a
  generated render. This namespace is the bidirectional bridge:

      .md  ──md->data──▶ {:meta… :body}  ──emit-mdedn──▶  .md.edn   (canonical)
      .md.edn ─read-mdedn─▶ {:meta… :body} ──mdedn->md──▶  .md       (GitHub render)

  Round-trip contract: the DATA (metadata map + body string) is preserved exactly
  across both directions; only incidental YAML/EDN whitespace is normalized.

  Pure clojure.core + clojure.edn + clojure.string (babashka-compatible)."
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as str]))

;; ── canonical front-matter key order (matches 90-docs/adr/template.md) ───────

(def key-order
  [:id :title :status :doc-type :topic :authoritative :last-verified
   :priority :axis :weight :priority-note
   :authoritative-for :depends-on :related :supersedes :superseded-by])

(defn- kw->yaml-key [k] (str/replace (name k) "-" "_"))
(defn- yaml-key->kw [s] (keyword (str/replace s "_" "-")))

;; ── .md (YAML front matter + body) → data ────────────────────────────────────

(defn split-front-matter
  "Split a markdown string into [yaml-text body-text]. yaml-text is nil when the
  document has no `---` front matter."
  [text]
  (let [lines (str/split-lines text)]
    (if (= "---" (str/trim (or (first lines) "")))
      (let [[fm after] (split-with #(not= "---" (str/trim %)) (rest lines))]
        [(str/join "\n" fm)
         (str/triml (str/join "\n" (drop 1 after)))])    ; drop closing ---, ltrim
      [nil text])))

(defn- parse-scalar [s]
  (let [s (str/trim s)]
    (cond
      (= s "[]") []
      (= s "true") true
      (= s "false") false
      (re-matches #"-?\d+" s) (parse-long s)
      (re-matches #"-?\d+\.\d+" s) (parse-double s)
      (and (>= (count s) 2) (str/starts-with? s "\"") (str/ends-with? s "\""))
      (-> (subs s 1 (dec (count s)))
          (str/replace "\\\"" "\"")
          (str/replace "\\\\" "\\"))
      :else s)))

(defn parse-front-matter
  "Parse our flat ADR YAML front matter into an EDN metadata map. Supports scalar
  `key: value`, inline `[]`, and block lists (`key:` then `  - item` lines)."
  [yaml]
  (loop [lines (str/split-lines (or yaml ""))
         acc {} cur-key nil cur-list nil]
    (if (empty? lines)
      (cond-> acc cur-key (assoc cur-key (or cur-list [])))
      (let [line (first lines)]
        (cond
          (str/blank? line)
          (recur (rest lines) acc cur-key cur-list)

          (re-matches #"\s+-\s+.*" line)                 ; block-list item
          (recur (rest lines) acc cur-key
                 (conj (or cur-list [])
                       (parse-scalar (str/replace-first line #"^\s+-\s+" ""))))

          :else
          (let [acc (if cur-key (assoc acc cur-key (or cur-list [])) acc)
                m (re-matches #"([A-Za-z0-9_]+):\s*(.*)$" line)]
            (if m
              (let [k (yaml-key->kw (nth m 1)) v (str/trim (nth m 2))]
                (if (str/blank? v)
                  (recur (rest lines) acc k nil)          ; a block list follows
                  (recur (rest lines) (assoc acc k (parse-scalar v)) nil nil)))
              (recur (rest lines) acc cur-key cur-list))))))))

(defn md->data
  "Parse a `.md` document into {:body <markdown> + metadata keys}."
  [text]
  (let [[yaml body] (split-front-matter text)]
    (assoc (parse-front-matter yaml) :body (str/trimr body))))

;; ── data → .md.edn (canonical commented EDN) ─────────────────────────────────

(defn- edn-scalar [v]
  (cond
    (vector? v) (if (empty? v) "[]" (str "[" (str/join " " (map pr-str v)) "]"))
    :else (pr-str v)))                                   ; strings/bools/numbers

(defn- escape-md [s]
  (-> s (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")))

(def ^:private header-tmpl
  (str ";; ─────────────────────────────────────────────────────────────────────\n"
       ";; %s\n"
       ";; .md.edn — canonical commented-EDN ADR (ADR-2606162200). Metadata are\n"
       ";; typed EDN; :body is a #md tagged markdown string. Edit THIS file; run\n"
       ";; `bb adr:render %s` to regenerate the GitHub-rendered .md.\n"
       ";; ─────────────────────────────────────────────────────────────────────\n"))

(defn emit-mdedn
  "Render a data map to the canonical `.md.edn` text. `out-name` (optional) is the
  basename shown in the header's render hint."
  ([m] (emit-mdedn m "<file>.md"))
  ([m out-name]
   (let [meta- (dissoc m :body)
         present (filter #(contains? meta- %) key-order)
         extras (sort (remove (set key-order) (keys meta-)))
         ks (concat present extras)
         pad (apply max 0 (map #(count (str %)) ks))
         kv (fn [k] (str (format (str "%-" pad "s") (str k)) " " (edn-scalar (get meta- k))))
         kvs (map kv ks)
         head (str "{" (first kvs))
         mid (apply str (map #(str "\n " %) (rest kvs)))]
     (str (format header-tmpl (or (:id m) "ADR") out-name)
          head mid
          "\n\n ;; ── body (markdown — #md verbatim) ──────────────────────────────────\n"
          " :body\n"
          " #md \"" (escape-md (:body m)) "\"}\n"))))

;; ── .md.edn → data ───────────────────────────────────────────────────────────

(defn read-mdedn
  "Parse a `.md.edn` string back into a data map (the #md body becomes a string)."
  [text]
  (edn/read-string {:readers {'md identity} :default (fn [_ v] v)} text))

;; ── data → .md (GitHub-rendered) ─────────────────────────────────────────────

(defn- yaml-scalar-out [v]
  (cond
    (boolean? v) (str v)
    (number? v) (str v)
    (string? v)
    (if (and (seq v)
             (re-matches #"[A-Za-z0-9][\w./-]*" v)
             (not (#{"true" "false" "null" "yes" "no"} v)))
      v                                                  ; safe bareword
      (str "\"" (-> v (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\""))
    :else (pr-str v)))

(defn mdedn->md
  "Render a data map (from read-mdedn or md->data) to a `.md` document."
  [m]
  (let [meta- (dissoc m :body)
        present (filter #(contains? meta- %) key-order)
        extras (sort (remove (set key-order) (keys meta-)))
        ks (concat present extras)
        fm (for [k ks]
             (let [v (get meta- k) yk (kw->yaml-key k)]
               (if (vector? v)
                 (if (empty? v)
                   (str yk ": []")
                   (str yk ":\n" (str/join "\n" (map #(str "  - " (yaml-scalar-out %)) v))))
                 (str yk ": " (yaml-scalar-out v)))))]
    (str "---\n" (str/join "\n" fm) "\n---\n\n" (str/trimr (:body m)) "\n")))

;; ── file helpers / CLI ───────────────────────────────────────────────────────

(defn md-file->mdedn!
  "Convert <path>.md → <path>.md.edn. Returns the output path."
  [md-path]
  (let [text (slurp md-path)
        out (str md-path ".edn")
        base (last (str/split out #"/"))]
    (spit out (emit-mdedn (md->data text) base))
    out))

(defn mdedn-file->md!
  "Render <path>.md.edn → <path>.md (overwriting). Returns the output path."
  [mdedn-path]
  (let [out (str/replace mdedn-path #"\.md\.edn$" ".md")
        out (if (= out mdedn-path) (str mdedn-path ".md") out)]
    (spit out (mdedn->md (read-mdedn (slurp mdedn-path))))
    out))

;; ── index generation (adr-index.edn ← front matter, the SSoT) ────────────────
;;
;; The machine index is GENERATED from each ADR's front matter, never hand-edited.
;; This replaces the 2.8 MB single-line adr-index.edn (un-parseable + drift-prone,
;; the deps.edn failure class of ADR-2606121143) with a canonical, one-entry-per-line,
;; clojure.edn-parseable file. Per ADR-2606162200.

(defn- first-h1 [body]
  (some #(when (str/starts-with? % "# ") (str/triml (subs % 1)))
        (str/split-lines (or body ""))))

(defn- tx-entity->data
  "Normalize tx-data entity (or bare map) to flat metadata map with :body."
  [e]
  (when (map? e)
    (let [getv (fn [k]
                 (or (get e k)
                     (get e (keyword "adr" (name k)))
                     (get e (keyword "doc" (name k)))))]
      (cond-> {:id (str (or (getv :id) ""))
               :title (str (or (getv :title) ""))
               :status (str (or (getv :status) "unknown"))
               :doc-type (str (or (getv :doc-type) (getv :doc_type) "adr"))
               :body (str (or (getv :body) ""))}
        (seq (str (or (getv :topic) ""))) (assoc :topic (str (getv :topic)))
        (some? (getv :authoritative)) (assoc :authoritative (boolean (getv :authoritative)))
        (seq (str (or (getv :last-verified) (getv :last_verified) "")))
        (assoc :last-verified (str (or (getv :last-verified) (getv :last_verified))))))))

(defn list-adr-files
  "Canonical ADR source files in `dir`: every `*.edn` / `*.md.edn` / `*.md`,
  preferring plain `.edn` then `.md.edn` then `.md`. Excludes README / template /
  MDEDN / adr-index."
  [dir]
  (let [names (->> (.listFiles (io/file dir))
                   (map #(.getName %))
                   (filter #(or (re-matches #".*\.md(\.edn)?$" %)
                                (and (str/ends-with? % ".edn")
                                     (not (str/ends-with? % ".md.edn")))))
                   (remove #(re-find #"README|template|MDEDN-FORMAT|adr-index" %)))
        strip (fn [n]
                (-> n
                    (str/replace #"\.md\.edn$" "")
                    (str/replace #"\.edn$" "")
                    (str/replace #"\.md$" "")))
        by-base (atom {})]
    (doseq [n names]
      (let [b (strip n)
            rank (cond (and (str/ends-with? n ".edn") (not (str/ends-with? n ".md.edn"))) 3
                       (str/ends-with? n ".md.edn") 2
                       :else 1)
            prev (get @by-base b)]
        (when (or (nil? prev) (> rank (second prev)))
          (swap! by-base assoc b [n rank]))))
    (->> @by-base vals (map first) sort)))

(defn file->entry
  "Build one index entry (metadata, no body) from an ADR file path. Falls back to a
  filename-derived id and the first H1 as title when front matter is absent."
  [path]
  (let [text (slurp path)
        data (cond
               (str/ends-with? path ".md.edn") (read-mdedn text)
               (and (str/ends-with? path ".edn") (not (str/ends-with? path ".md.edn")))
               (try
                 (let [form (edn/read-string {:default (fn [_tag v] v)} text)]
                   (cond
                     (and (vector? form) (map? (first form))) (tx-entity->data (first form))
                     (map? form) (or (tx-entity->data form) (md->data (or (:body form) "")))
                     :else (md->data text)))
                 (catch #?(:clj Exception :cljs :default) _ (md->data text)))
               :else (md->data text))
        base (-> path
                 (str/replace #".*/" "")
                 (str/replace #"\.md\.edn$" "")
                 (str/replace #"\.edn$" "")
                 (str/replace #"\.md$" ""))
        m (dissoc data :body)]
    (-> m
        ;; coerce id/title to strings: some ADR front matter has a bare-numeric
        ;; id/title that parse-scalar reads as a Long, which breaks the id sort.
        (assoc :id (str (or (:id m) (str "adr-" base)))
               :title (str (or (:title m) (first-h1 (:body data)) base))
               :status (str (or (:status m) "unknown"))
               :doc-type (str (or (:doc-type m) "adr"))
               :file (str base ".edn")))))

(defn gen-index
  "Scan `dir` and return the index as a vector of entry maps, newest id first."
  [dir]
  (->> (list-adr-files dir)
       (map #(file->entry (str dir "/" %)))
       (sort-by :id #(compare %2 %1))
       vec))

(def ^:private index-key-order (concat key-order [:file]))

(defn- entry->line [m]
  (let [present (filter #(contains? m %) index-key-order)
        extras (sort (remove (set index-key-order) (keys m)))
        ks (concat present extras)]
    (str "{" (str/join " " (map #(str % " " (edn-scalar (get m %))) ks)) "}")))

(defn emit-index
  "Canonical, one-entry-per-line, clojure.edn-parseable adr-index.edn text."
  [entries]
  (str ";; adr-index.edn — GENERATED by `bb adr:index` from ADR front matter (the SSoT).\n"
       ";; DO NOT hand-edit. Edit the ADR .md / .md.edn front matter and regenerate.\n"
       ";; One entry per line → diff/merge-friendly + clojure.edn-parseable.\n"
       ";; Per ADR-2606162200 (.md.edn) + ADR-2606121143 (single-line-EDN failure class).\n"
       "[\n"
       (str/join "\n" (map entry->line entries))
       "\n]\n"))

(defn write-index!
  "Generate and write `out` (default 90-docs/adr/adr-index.edn) from `dir`'s ADRs.
  Returns {:count n :path out}."
  ([dir] (write-index! dir (str dir "/adr-index.edn")))
  ([dir out]
   (let [entries (gen-index dir)]
     (spit out (emit-index entries))
     {:count (count entries) :path out})))

(defn check-index
  "Regenerate the index in-memory and compare to the committed `out` file.
  Returns {:ok bool :reason …}. Drives a lefthook drift gate."
  ([dir] (check-index dir (str dir "/adr-index.edn")))
  ([dir out]
   (let [want (emit-index (gen-index dir))
         have (if (.exists (io/file out)) (slurp out) "")]
     (if (= want have)
       {:ok true :count (count (gen-index dir))}
       {:ok false :reason (str out " is stale — run `bb adr:index` and commit")}))))

(defn -main
  "CLI: `to <*.md>…` | `render <*.md.edn>…` | `index [dir] [out]` | `index-check [dir] [out]`."
  [& args]
  (let [[cmd & files] args]
    (case cmd
      "to"     (doseq [f files] (println "→" (md-file->mdedn! f)))
      "render" (doseq [f files] (println "→" (mdedn-file->md! f)))
      "index"  (let [dir (or (first files) "90-docs/adr")
                     out (or (second files) (str dir "/adr-index.edn"))
                     r (write-index! dir out)]
                 (println "→" (:path r) (str "(" (:count r) " entries)")))
      "index-check" (let [dir (or (first files) "90-docs/adr")
                          out (or (second files) (str dir "/adr-index.edn"))
                          r (check-index dir out)]
                      (if (:ok r)
                        (println "✓ adr-index.edn up to date" (str "(" (:count r) " entries)"))
                        (do (println "✗" (:reason r)) (System/exit 1))))
      (do (println "usage: adr-mdedn (to <*.md>… | render <*.md.edn>… | index [dir] [out] | index-check)")
          (System/exit 2)))))
