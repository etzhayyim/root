;; Regenerate 90-docs/_registry/{docs.json,docs.edn} from disk front-matter.
;;
;; babashka port of the former regen-registry.py (byte-for-byte identical
;; output — same scan order, same key order, same JSON pretty-format, same EDN).
;; clj-native per the repo's babashka direction; no PyYAML / Python dependency.
;;
;; The registry is a sidecar index used by documentation consumers and the
;; drift-check in validate-adrs.py. Markdown bodies remain canonical; this
;; script scans them and emits a normalized table so a human or a CI gate can
;; see the full picture in one file.
;;
;; Covered keys per entry:
;;   id, path, title, status, doc_type, topic, authoritative,
;;   authoritative_for, related, supersedes, superseded_by, amends,
;;   amended_by, depends_on, last_verified
;;
;; Idempotent. Sorts entries by `id`. Preserves existing non-ADR rows
;; (e.g. explanation / how-to / tutorial docs) — they're parsed the same way.
;;
;; Two sidecars from the same scan (kept in lock-step):
;;   docs.json — JSON table (snake_case string keys).
;;   docs.edn  — EDN table for babashka / Clojure consumers (kebab-case keyword
;;               keys, matching the repo's *.adr.edn convention).
;;
;; Usage:
;;   bb 70-tools/scripts/docs/regen-registry.clj
;;   bb 70-tools/scripts/docs/regen-registry.clj --check   ; exit 1 on drift (json OR edn)
;;   bb 70-tools/scripts/docs/regen-registry.clj --json    ; plan-only JSON (stdout)
;;   bb 70-tools/scripts/docs/regen-registry.clj --edn     ; plan-only EDN (stdout)

(ns regen-registry
  (:require [babashka.fs :as fs]
            [cheshire.core :as json]
            [clojure.edn :as edn]
            [clojure.string :as str]))

;; REPO = parents[3] of this script: docs -> scripts -> 70-tools -> REPO
(def repo
  (-> (or *file* "70-tools/scripts/docs/regen-registry.clj")
      fs/absolutize fs/parent fs/parent fs/parent fs/parent
      str))

(def docs-root (str (fs/path repo "90-docs")))
(def registry-json (str (fs/path repo "90-docs" "_registry" "docs.json")))
(def registry-edn (str (fs/path repo "90-docs" "_registry" "docs.edn")))

;; Non-path keys we surface, in the exact order the JSON entry dict is built.
(def surfaced-no-path
  ["id" "title" "status" "doc_type" "topic" "authoritative"
   "authoritative_for" "related" "supersedes" "superseded_by"
   "amends" "amended_by" "depends_on" "last_verified"])

(def list-default-keys
  ["authoritative_for" "related" "supersedes" "superseded_by" "amends" "amended_by"])

;; ── front-matter parser (faithful port of the Python "tiny YAML-ish") ───────

(defn- strip-set
  "Remove leading + trailing chars that are in `chars` (like Python str.strip(chars))."
  [s chars]
  (let [n (count s)
        start (loop [i 0] (if (and (< i n) (chars (.charAt s i))) (recur (inc i)) i))
        end   (loop [i n] (if (and (> i start) (chars (.charAt s (dec i)))) (recur (dec i)) i))]
    (subs s start end)))

(defn parse-frontmatter
  "Returns a map of front-matter keys, or nil if `text` has no `---` block."
  [text]
  (when (str/starts-with? text "---")
    (when-let [end (str/index-of text "\n---" 3)]
      (let [block (strip-set (subs text 3 end) #{\newline})
            lines (str/split block #"\n" -1)]
        (first
         (reduce
          (fn [[out ckey] raw]
            (let [line (str/replace raw #"\s+#.*$" "")]
              (cond
                (str/blank? line)
                [out nil]

                (or (str/starts-with? line "  - ") (str/starts-with? line "- "))
                (let [item (-> line
                               (str/replace #"^[ -]+" "")
                               str/trim
                               (strip-set #{\"})
                               (strip-set #{\'}))]
                  (if ckey
                    [(update out ckey (fnil conj []) item) ckey]
                    [out ckey]))

                :else
                (if-let [m (re-find #"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$" line)]
                  (let [k (nth m 1)
                        v (str/trim (nth m 2))]
                    (if (or (= v "") (= v "[]"))
                      [(assoc out k []) (if (= v "[]") nil k)]
                      (let [stripped (-> v (strip-set #{\"}) (strip-set #{\'}))
                            lc (str/lower-case stripped)]
                        (if (or (= lc "true") (= lc "false"))
                          [(assoc out k (= lc "true")) nil]
                          [(assoc out k stripped) nil]))))
                  [out nil]))))
          [{} nil]
          lines))))))

;; ── ordered entry (a vector of [k v] pairs preserves Python insertion order) ─

(defn build-entry
  "Build one registry entry as an ordered [k v] pair-vector, mirroring the
  Python dict insertion order exactly."
  [rel fm]
  (let [base (into [["path" rel]]
                   (keep (fn [k] (when (contains? fm k) [k (get fm k)])) surfaced-no-path))
        base (if (some #(= "authoritative" (first %)) base)
               base
               (conj base ["authoritative" false]))
        base (reduce (fn [acc lk]
                       (if (some #(= lk (first %)) acc) acc (conj acc [lk []])))
                     base list-default-keys)]
    base))

(defn- entry-id [pairs]
  (or (some (fn [[k v]] (when (= k "id") v)) pairs) ""))

(defn- kw-name [k]
  (cond (keyword? k) (name k)
        (string? k) k
        :else (str k)))

(defn- scalar-str [v]
  (cond
    (keyword? v) (name v)
    (instance? java.util.Date v)
    (subs (str (java.time.Instant/ofEpochMilli (.getTime ^java.util.Date v))) 0 10)
    :else (str v)))

(defn- entity->fm
  "Extract registry front-matter map from an EDN tx-data entity
   ([{:db/id -1 :adr/id ...}] or bare map / :frontmatter form)."
  [m]
  (when (map? m)
    (let [base (if (map? (:frontmatter m))
                 (merge (dissoc m :frontmatter :body :body-file) (:frontmatter m))
                 m)
          ;; prefer :adr/* / :doc/* then bare keys
          getv (fn [& ks]
                 (some (fn [k]
                         (or (get base k)
                             (get base (keyword "adr" (name k)))
                             (get base (keyword "doc" (name k)))
                             (get base (name k))))
                       ks))
          id (getv :id :adr/id :doc/id)]
      (when id
        (cond-> {"id" (str id)
                 "title" (str (or (getv :title :adr/title :doc/title) id))
                 "status" (scalar-str (or (getv :status :adr/status :doc/status) "active"))
                 "doc_type" (scalar-str (or (getv :doc_type :doc-type :adr/doc_type :adr/doc-type :doc/doc_type) "doc"))
                 "topic" (scalar-str (or (getv :topic :adr/topic :doc/topic) ""))
                 "authoritative" (boolean (getv :authoritative :adr/authoritative :doc/authoritative))}
          (getv :last_verified :last-verified :adr/last_verified :adr/last-verified)
          (assoc "last_verified" (scalar-str (getv :last_verified :last-verified :adr/last_verified :adr/last-verified)))
          (sequential? (getv :related :adr/related :doc/related))
          (assoc "related" (mapv str (getv :related :adr/related :doc/related)))
          (sequential? (getv :authoritative_for :authoritative-for :adr/authoritative_for :adr/authoritative-for))
          (assoc "authoritative_for" (mapv str (getv :authoritative_for :authoritative-for :adr/authoritative_for :adr/authoritative-for)))
          (sequential? (getv :supersedes :adr/supersedes))
          (assoc "supersedes" (mapv str (getv :supersedes :adr/supersedes)))
          (sequential? (getv :superseded_by :superseded-by :adr/superseded_by :adr/superseded-by))
          (assoc "superseded_by" (mapv str (getv :superseded_by :superseded-by :adr/superseded_by :adr/superseded-by)))
          (sequential? (getv :amends :adr/amends))
          (assoc "amends" (mapv str (getv :amends :adr/amends)))
          (sequential? (getv :amended_by :amended-by :adr/amended_by :adr/amended-by))
          (assoc "amended_by" (mapv str (getv :amended_by :amended-by :adr/amended_by :adr/amended-by))))))))

(defn- parse-edn-doc
  "Parse EDN doc file → front-matter map or nil."
  [text]
  (try
    (let [form (edn/read-string {:default (fn [_tag v] v)} text)]
      (cond
        (and (vector? form) (map? (first form))) (entity->fm (first form))
        (map? form) (or (entity->fm form)
                        (when-let [fm (parse-frontmatter (or (:body form) ""))]
                          (when (get fm "id") fm)))
        :else nil))
    (catch Exception _ nil)))

(defn scan-docs []
  ;; EDN-only SSoT (ADR-2607171600 / superproject alignment): scan **.edn and
  ;; legacy **.md / **.md.edn. Prefer .edn when both exist.
  (let [md-files (->> (fs/glob docs-root "**.md") (map str))
        md-edn-files (->> (fs/glob docs-root "**.md.edn") (map str))
        edn-files (->> (fs/glob docs-root "**.edn")
                       (map str)
                       (remove #(str/ends-with? % ".md.edn"))
                       (remove #(str/includes? % "/_registry/"))
                       (remove #(= "deps.edn" (fs/file-name %))))
        ;; path without extension for dedupe: prefer edn > md.edn > md
        strip (fn [p]
                (-> p
                    (str/replace #"\.md\.edn$" "")
                    (str/replace #"\.edn$" "")
                    (str/replace #"\.md$" "")))
        by-base (atom {})]
    (doseq [p md-files]
      (swap! by-base assoc (strip p) p))
    (doseq [p md-edn-files]
      (swap! by-base assoc (strip p) p))
    (doseq [p edn-files]
      (swap! by-base assoc (strip p) p))
    (->> (vals @by-base)
         sort
         (keep (fn [p]
                 (let [parts (set (map str (fs/components p)))
                       name (fs/file-name p)]
                   (when-not (or (contains? parts "_registry")
                                 (= "CLAUDE.md" name)
                                 (= "CLAUDE.edn" name)
                                 (= "deps.edn" name))
                     (let [text (try (slurp p) (catch Exception _ nil))
                           fm (when text
                                (cond
                                  (str/ends-with? p ".edn") (or (parse-edn-doc text)
                                                                (parse-frontmatter text))
                                  :else (parse-frontmatter text)))]
                       (when (and fm (get fm "id"))
                         (build-entry (str (fs/relativize repo p)) fm)))))))
         (sort-by entry-id)
         vec)))

(defn today-iso [] (str (java.time.LocalDate/now)))

;; ── JSON encoder — byte-identical to json.dumps(obj, indent=2, ensure_ascii=False) ──

(defn- json-escape [s]
  (let [sb (StringBuilder.)]
    (doseq [c s]
      (let [code (int c)]
        (cond
          (= c \\) (.append sb "\\\\")
          (= c \") (.append sb "\\\"")
          (= code 8)  (.append sb "\\b")
          (= code 12) (.append sb "\\f")
          (= code 10) (.append sb "\\n")
          (= code 13) (.append sb "\\r")
          (= code 9)  (.append sb "\\t")
          (< code 32) (.append sb (format "\\u%04x" code))
          :else (.append sb c))))
    (str sb)))

(defn- json-str [s] (str \" (json-escape s) \"))

(declare json-encode)

(defn- json-pairs [pairs level]
  (if (empty? pairs)
    "{}"
    (let [pad  (apply str (repeat (* 2 level) \space))
          pad2 (apply str (repeat (* 2 (inc level)) \space))
          items (map (fn [[k v]] (str pad2 (json-str k) ": " (json-encode v (inc level)))) pairs)]
      (str "{\n" (str/join ",\n" items) "\n" pad "}"))))

(defn- json-array [xs level]
  (if (empty? xs)
    "[]"
    (let [pad  (apply str (repeat (* 2 level) \space))
          pad2 (apply str (repeat (* 2 (inc level)) \space))
          items (map (fn [x] (str pad2 (json-encode x (inc level)))) xs)]
      (str "[\n" (str/join ",\n" items) "\n" pad "]"))))

(defn json-encode [v level]
  (cond
    (string? v)  (json-str v)
    (boolean? v) (if v "true" "false")
    (integer? v) (str v)
    (vector? v)  (json-array v level)
    :else (throw (ex-info "un-encodable JSON value" {:v v}))))

(defn render-json [entries date]
  ;; top-level object: version / updated_at / entries (entries = vector of pair-vectors)
  (let [pad2 "  "
        ev (if (empty? entries)
             "[]"
             (str "[\n"
                  (str/join ",\n" (map #(str "    " (json-pairs % 2)) entries))
                  "\n  ]"))]
    (str "{\n"
         pad2 "\"version\": 2,\n"
         pad2 "\"updated_at\": " (json-str date) ",\n"
         pad2 "\"entries\": " ev "\n"
         "}\n")))

;; ── EDN encoder — byte-identical to the Python render_edn ───────────────────

(defn- edn-keyword [k] (str ":" (str/replace k "_" "-")))

(defn- edn-string [s]
  (str \"
       (-> s
           (str/replace "\\" "\\\\")
           (str/replace "\"" "\\\"")
           (str/replace "\r" "\\r")
           (str/replace "\n" "\\n")
           (str/replace "\t" "\\t"))
       \"))

(defn- edn-value [v]
  (cond
    (string? v)  (edn-string v)
    (boolean? v) (if v "true" "false")
    (integer? v) (str v)
    (vector? v)  (str "[" (str/join " " (map edn-value v)) "]")
    :else (throw (ex-info "un-encodable EDN value" {:v v}))))

(defn- edn-entry [pairs]
  (str "{" (str/join " " (map (fn [[k v]] (str (edn-keyword k) " " (edn-value v))) pairs)) "}"))

(defn render-edn [entries date]
  (let [head (str "{:version 2\n :updated-at " (edn-string date) "\n :entries")]
    (if (empty? entries)
      (str head "\n []}\n")
      (str head "\n [" (str/join "\n  " (map edn-entry entries)) "]}\n"))))

;; ── modes ───────────────────────────────────────────────────────────────────

(defn- pairs->map [pairs] (into {} pairs))

(defn- edn-entries-block [text]
  (let [idx (str/index-of text " :entries")]
    (if idx (subs text idx) text)))

(defn -main [& args]
  (let [args (set args)
        entries (scan-docs)
        date (today-iso)]
    (cond
      (contains? args "--json")
      (do (print (render-json entries date)) 0)

      (contains? args "--edn")
      (do (print (render-edn entries date)) 0)

      (contains? args "--check")
      (let [;; JSON sidecar — compare entries data only (updated_at is volatile)
            disk (try (json/parse-string (slurp registry-json) false) (catch Exception _ {}))
            disk-entries (get disk "entries" [])
            gen-entries (mapv pairs->map entries)]
        (cond
          (not= disk-entries gen-entries)
          (do (binding [*out* *err*]
                (println (str "registry drift detected: disk=" (count entries)
                              " entries, file=" (count disk-entries) " entries"))
                (println "run: nbb scripts/run-task.cljs docs:registry"))
              1)

          (not= (edn-entries-block (if (fs/exists? registry-edn) (slurp registry-edn) ""))
                (edn-entries-block (render-edn entries date)))
          (do (binding [*out* *err*]
                (println "registry EDN drift detected: docs.edn out of sync with docs.json source")
                (println "run: nbb scripts/run-task.cljs docs:registry"))
              1)

          :else
          (do (println (str "registry in sync (" (count entries) " entries; json + edn)")) 0)))

      :else
      (do
        (fs/create-dirs (fs/parent registry-json))
        (spit registry-json (render-json entries date))
        (spit registry-edn (render-edn entries date))
        (println (str "wrote 90-docs/_registry/docs.json + 90-docs/_registry/docs.edn with "
                      (count entries) " entries"))
        0))))

;; Run main unless a LIBRARY CONSUMER has said it only wants the functions. The guard used to be
;; `(= *file* (System/getProperty "babashka.file"))`, which asks "am I babashka's entry script?" --
;; false under every other runtime, so running this generator with `clojure` loaded it, regenerated
;; nothing and exited 0. The polarity was backwards: the default should be "I am the program",
;; because that is the case a silent no-op ruins, and the one caller that load-file's this (see
;; test_regen_registry.clj) is the one that knows it wants a library and can say so.
(when-not (System/getProperty "regen-registry.library-load")
  (System/exit (apply -main *command-line-args*)))
