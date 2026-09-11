;; ported from 70-tools/e7m-sim/scenes/giemon_kabitori/sbom_gen.py — real 1:1 port
;; replacing the unit_refactor stage-0 "TODO: port-failed" stubs.
;; giemon kabitori — generate CycloneDX SBOM + kotoba ingest body from parts.edn.
;;
;; The EDN ledger (parts.edn) is the SSoT. This tool parses it (with a small,
;; self-contained EDN reader for the controlled subset used by that file) and
;; emits:
;;   - kabitori.cdx.json   — CycloneDX 1.5 SBOM
;;   - kabitori.ingest.json — kotoba kg.ingest_batch body
;;
;; House style: parsed EDN stays string-keyed maps, exactly the shapes the Python
;; reader produced; Python ':kw' tokens are kept AS strings (without the colon),
;; matching `_EdnReader._read_kw`. Pure fns; file I/O behind #?(:clj ...).
;; The Python `__main__` demo is provided as `-main` (file I/O on :clj only).
(ns e7m-sim.scenes.giemon-kabitori.sbom-gen
  (:require [clojure.string :as str]))

;; ── minimal EDN reader (controlled subset: maps, vectors, keywords, strings,
;;    ints, bool, nil; `;` line comments; `,` is whitespace) ──────────────────
;; 1:1 port of the Python `_EdnReader`. We thread an index through a mutable
;; volatile to keep the exact left-to-right semantics of the Python class.
;; Keywords return their NAME (sans colon) AS A STRING; ints become longs;
;; true/false/nil map to true/false/nil.

(defn- edn-err [i msg]
  (throw (ex-info (str "edn parse error at " i ": " msg) {:i i})))

(defn- alnum? [c]
  (or (and (>= (int c) (int \0)) (<= (int c) (int \9)))
      (and (>= (int c) (int \a)) (<= (int c) (int \z)))
      (and (>= (int c) (int \A)) (<= (int c) (int \Z)))))

(defn- skip-ws2
  "Skip whitespace (` \\t\\r\\n,`) and `;` line comments; return new index."
  [^String s n i]
  (loop [i i]
    (if (>= i n)
      i
      (let [c (.charAt s i)]
        (cond
          (= c \;) (let [j (loop [j i]
                             (if (and (< j n) (not= (.charAt s j) \newline))
                               (recur (inc j)) j))]
                     (recur j))
          (or (= c \space) (= c \tab) (= c \return) (= c \newline) (= c \,))
          (recur (inc i))
          :else i)))))

(declare read-form)

(defn- read-str [^String s n i]
  ;; i points at opening quote
  (loop [i (inc i), buf (StringBuilder.)]
    (when (>= i n) (edn-err i "unterminated string"))
    (let [c (.charAt s i)]
      (cond
        (= c \\) (let [esc (.charAt s (inc i))
                       ch (case esc
                            \n \newline
                            \t \tab
                            \r \return
                            esc)]
                   (recur (+ i 2) (.append buf ch)))
        (= c \") [(.toString buf) (inc i)]
        :else (recur (inc i) (.append buf c))))))

(defn- read-kw [^String s n i]
  ;; i points at leading colon
  (let [start (inc i)
        end (loop [j start]
              (if (and (< j n)
                       (let [c (.charAt s j)]
                         (or (alnum? c) (contains? #{\/ \- \. \* \_} c))))
                (recur (inc j)) j))]
    [(subs s start end) end]))

(defn- read-atom [^String s n i]
  (let [end (loop [j i]
              (if (and (< j n)
                       (let [c (.charAt s j)]
                         (or (alnum? c) (contains? #{\- \. \+} c))))
                (recur (inc j)) j))
        tok (subs s i end)]
    [(cond
       (= tok "true") true
       (= tok "false") false
       (= tok "nil") nil
       :else (try (Long/parseLong tok)
                  (catch #?(:clj Exception :default :default) _ tok)))
     end]))

(defn- read-map [^String s n i]
  ;; i points at `{`
  (loop [i (inc i), d {}]
    (let [i (skip-ws2 s n i)]
      (when (>= i n) (edn-err i "unterminated map"))
      (if (= (.charAt s i) \})
        [d (inc i)]
        (let [[k i] (read-form s n i)
              [v i] (read-form s n i)]
          (recur i (assoc d k v)))))))

(defn- read-vec [^String s n i]
  ;; i points at `[`
  (loop [i (inc i), out []]
    (let [i (skip-ws2 s n i)]
      (when (>= i n) (edn-err i "unterminated vector"))
      (if (= (.charAt s i) \])
        [out (inc i)]
        (let [[el i] (read-form s n i)]
          (recur i (conj out el)))))))

(defn- read-form [^String s n i]
  (let [i (skip-ws2 s n i)]
    (when (>= i n) (edn-err i "unexpected EOF"))
    (let [c (.charAt s i)]
      (cond
        (= c \{) (read-map s n i)
        (= c \[) (read-vec s n i)
        (= c \") (read-str s n i)
        (= c \:) (read-kw s n i)
        :else (read-atom s n i)))))

(defn parse-edn
  "Parse the first EDN form in `text` → Clojure data (maps string-keyed,
  keyword tokens kept AS strings)."
  [^String text]
  (first (read-form text (count text) 0)))

;; ── claim mapping: a part map's keys → kg claims (string values) ─────────────
(def ^:private claim-keys
  ["part/group" "part/procurement" "part/manufacturer" "part/product"
   "part/mpn" "part/purl" "part/qty" "part/mass-g" "part/unit-jpy"
   "part/supplier" "part/sim-feature" "part/fab-process" "part/sourcing"
   "part/note"])

(defn- capitalize-word [^String w]
  (if (empty? w)
    w
    (str (str/upper-case (subs w 0 1)) (subs w 1))))

(defn claim-pred
  "part/mass-g -> part/massG ; part/sim-feature -> part/simFeature ;
  part/fab-process -> part/fabProcess (camel-ish tail, keep slash)."
  [^String k]
  (let [[head tail] (str/split k #"/" 2)
        parts (str/split tail #"-")
        camel (apply str (first parts) (map capitalize-word (rest parts)))]
    (str head "/" camel)))

;; Python `str(x)` rendering for claim/property values. Numbers must NOT print
;; with a Clojure-specific suffix; longs print bare which matches Python int.
(defn- py-str [v]
  (cond
    (string? v) v
    (true? v) "True"
    (false? v) "False"
    (nil? v) "None"
    :else (str v)))

(defn to-kotoba-entities [meta parts]
  (let [bom-of (get meta "bom/of" "giemon-kabitori")]
    {"entities"
     (vec
      (for [p parts]
        (let [claims (into [{"pred" "part/bom" "value" bom-of}]
                           (for [k claim-keys
                                 :when (and (contains? p k) (some? (get p k)))]
                             {"pred" (claim-pred k) "value" (py-str (get p k))}))]
          {"id" (get p "part/id")
           "type" "GiemonKabitoriPart"
           "labelEn" (get p "part/name" (get p "part/id"))
           "claims" claims})))}))

(defn to-cyclonedx [meta parts]
  {"bomFormat" "CycloneDX"
   "specVersion" "1.5"
   "version" 1
   "metadata"
   {"component" {"type" "device"
                 "name" (get meta "bom/title" "Giemon Kabitori probe")
                 "version" (get meta "bom/revision" "v1")}
    "properties"
    [{"name" "giemon:bomOf" "value" (get meta "bom/of" "giemon-kabitori")}
     {"name" "giemon:sourcing" "value" (get meta "bom/sourcing" "representative")}
     {"name" "giemon:note" "value" (get meta "bom/note" "")}]}
   "components"
   (vec
    (for [p parts]
      (let [props (vec
                   (for [k claim-keys
                         :when (and (contains? p k) (some? (get p k)))]
                     {"name" (str "giemon:" (str/replace (claim-pred k) "part/" ""))
                      "value" (py-str (get p k))}))
            comp (cond-> {"type" "device"
                          "bom-ref" (get p "part/id")
                          "name" (get p "part/name" (get p "part/id"))
                          "properties" props}
                   (get p "part/manufacturer")
                   (assoc "publisher" (get p "part/manufacturer")
                          "supplier" {"name" (get p "part/manufacturer")})
                   (get p "part/product")
                   (assoc "version" (py-str (get p "part/product")))
                   (get p "part/purl")
                   (assoc "purl" (get p "part/purl")))]
        comp)))})

;; ── canonical JSON writer (json.dumps shapes) — for the file-I/O edge only ──
#?(:clj
   (do
     (defn- json-escape ^String [^String s]
       (str/escape s {\" "\\\"" \\ "\\\\"
                      \backspace "\\b" \tab "\\t" \newline "\\n"
                      \formfeed "\\f" \return "\\r"}))

     (defn- json-str
       "Render `v` as JSON. `indent` nil = compact; integer = pretty (json.dumps
       indent=N with `, ` / `: ` separators, ensure_ascii=False)."
       [v indent level]
       (let [nl (if indent (str "\n" (apply str (repeat (* indent (inc level)) \space))) "")
             nl-close (if indent (str "\n" (apply str (repeat (* indent level) \space))) "")
             kv-sep (if indent ": " ": ")
             item-sep (if indent "," ", ")]
         (cond
           (string? v) (str "\"" (json-escape v) "\"")
           (true? v) "true"
           (false? v) "false"
           (nil? v) "null"
           (integer? v) (str v)
           (number? v) (str v)
           (map? v) (if (empty? v)
                      "{}"
                      (str "{" nl
                           (str/join (str item-sep nl)
                                     (map (fn [[k val]]
                                            (str "\"" (json-escape (str k)) "\""
                                                 kv-sep (json-str val indent (inc level))))
                                          v))
                           nl-close "}"))
           (sequential? v) (if (empty? v)
                             "[]"
                             (str "[" nl
                                  (str/join (str item-sep nl)
                                            (map #(json-str % indent (inc level)) v))
                                  nl-close "]"))
           :else (throw (ex-info "json-str: unsupported value" {:value v})))))

     (defn -main
       "Faithful port of the Python __main__/main: read parts.edn, write the two
       JSON artifacts next to it (or under out-dir), print a summary."
       [& args]
       (let [here (str (.getParent (java.io.File. (str *file*))))
             edn-path (if (>= (count args) 1) (first args) (str here "/parts.edn"))
             out-dir (if (>= (count args) 2) (second args) here)
             doc (parse-edn (slurp edn-path))
             meta (get doc "bom/meta")
             parts (get doc "bom/parts")]
         (assert (and (sequential? parts) (pos? (count parts))) "no parts parsed")
         (doseq [p parts, req ["part/id" "part/name" "part/group" "part/procurement"]]
           (assert (contains? p req)
                   (str (get p "part/id" "?") " missing " req)))
         (let [n-cots (count (filter #(= (get % "part/procurement") "cots") parts))
               n-fab (count (filter #(= (get % "part/procurement") "custom-fab") parts))
               cdx (to-cyclonedx meta parts)
               ing (to-kotoba-entities meta parts)
               slug (let [of (py-str (get meta "bom/of" "robot"))]
                      (if (str/starts-with? of "giemon-") (subs of (count "giemon-")) of))
               cdx-path (str out-dir "/" slug ".cdx.json")
               ing-path (str out-dir "/" slug ".ingest.json")]
           (spit cdx-path (str (json-str cdx 2 0) "\n"))
           (spit ing-path (str (json-str ing nil 0) "\n"))
           (println (str slug ": parts=" (count parts)
                         "  cots=" n-cots "  custom-fab=" n-fab))
           (println (str "wrote " cdx-path " (" (count (get cdx "components")) " components)"))
           (println (str "wrote " ing-path " (" (count (get ing "entities")) " entities)")))))))
