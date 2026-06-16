(ns meisai.methods.ingest
  "ingest.py — meisai 明細: member card-statement EDN → kotoba EAVT datoms. ADR-2606122400.
  1:1 Clojure port of `methods/ingest.py`.

  meisai does NO network I/O and holds NO credential: it reads a local intake EDN file,
  normalizes each statement row into append-only EAVT datoms, and persists via kotoba.
  Two gates are STRUCTURAL here:

    - G2 credential-unrepresentable: a credential-shaped key (password / secret / otp / cvv /
      pin / credential / token) or a PAN-shaped value (13-19 digit run) anywhere in the
      intake RAISES — a card number or secret cannot enter the Datom log.
    - G5 provenance: every statement tx carries the intake file's content CID; row entity ids
      are deterministic content hashes → re-ingest of the same intake is a no-op (dedup by CID).

  Keywords are kept as ':...' strings (not Clojure keywords) to mirror Python.
  SHA-256 via java.security.MessageDigest; file I/O behind #?(:clj ...)."
  (:require [clojure.string :as str]
            [meisai.methods.kotoba :as kotoba])
  #?(:clj (:import [java.security MessageDigest]
                   [java.io File])))

(def ^:private forbidden-key-tokens
  ["password" "secret" "otp" "cvv" "credential" "token" "pin"])

;; 13-19 consecutive digits, optionally space/dash-grouped → a primary account number shape.
;; Python: re.compile(r"(?:\d[ -]?){13,19}")
(def ^:private pan-re #"(?:\d[ -]?){13,19}")

(defn- sha256-hex
  "String → lowercase hex sha-256 digest (UTF-8)."
  [s]
  #?(:clj (let [md (MessageDigest/getInstance "SHA-256")
                ^bytes bs (.getBytes ^String s "UTF-8")]
            (.update md bs)
            (apply str (map #(format "%02x" (bit-and % 0xFF)) (.digest md))))
     :cljs (throw (ex-info "intake-cid requires SHA-256 on the JVM" {}))))

(defn intake-cid
  "Content address of the intake file string (G5 provenance + dedup key)."
  [raw]
  (str "b" (sha256-hex raw)))

(defn- walk
  "Mirror of Python `_walk`: yields [path leaf] pairs over a nested map/vector tree.
  For a map, the KEY is walked at the current path, the VALUE at `path/k`."
  [node path]
  (cond
    (map? node)
    (mapcat (fn [[k v]]
              (concat (walk k path)
                      (walk v (str path "/" k))))
            node)

    (sequential? node)
    (mapcat (fn [x] (walk x path)) node)

    :else
    [[path node]]))

(defn- py-str
  "Mirror of Python str(x) for the leaf values this code sees: nil → \"None\",
  true/false → \"True\"/\"False\", numbers/strings as printed."
  [x]
  (cond
    (nil? x) "None"
    (true? x) "True"
    (false? x) "False"
    :else (str x)))

(defn guard
  "G2 structural gate: refuse credential-shaped keys and PAN-shaped values anywhere."
  [doc]
  (doseq [[path leaf] (walk doc "")]
    (let [s (py-str leaf)
          low (str/lower-case s)]
      (when (and (some #(str/includes? low %) forbidden-key-tokens)
                 (str/starts-with? low ":"))
        (throw (ex-info (str "G2: credential-shaped key " (pr-str s)
                             " is unrepresentable in meisai")
                        {:gate "G2"})))
      (let [digits (re-find pan-re s)]
        (when (and digits
                   (>= (count (str/replace digits #"\D" "")) 13))
          (throw (ex-info (str "G2: PAN-shaped value at " (if (str/blank? path) "/" path)
                               " is unrepresentable in meisai")
                          {:gate "G2"})))))))

(defn- kw
  "':sumitclub' → 'sumitclub' (keyword → bare name for entity-id use).
  Mirror of Python str(v).lstrip(':') — strips ALL leading ':'."
  [v]
  (str/replace (py-str v) #"^:+" ""))

(defn- to-int
  "Mirror of Python int(x): coerce a long/double/numeric-string to a long (truncating)."
  [x]
  (cond
    (integer? x) (long x)
    (number? x) (long x)
    :else #?(:clj (long (Double/parseDouble (str x)))
             :cljs (long (js/parseInt (str x) 10)))))

(defn statement-datoms
  "Statement intake map (kotoba/parse-edn shape — keys like ':statement/month') →
  append-only EAVT datoms. E(statement) = meisai-stmt:<source>:<month>;
  E(row) = meisai-row:<sha256(stmt|idx|date|merchant|amount)[:16]> (deterministic)."
  [doc cid]
  (guard doc)
  (let [source (kw (get doc ":source" "unknown"))
        month (str (get doc ":statement/month" "?"))
        rows (or (get doc ":statement/rows") [])
        stmt-e (str "meisai-stmt:" source ":" month)
        base [(kotoba/add stmt-e ":meisai.stmt/source" (str ":" source))
              (kotoba/add stmt-e ":meisai.stmt/month" month)
              (kotoba/add stmt-e ":meisai.stmt/row-count" (count rows))
              (kotoba/add stmt-e ":meisai.stmt/intake-cid" cid)]
        base (if (some? (get doc ":statement/total-jpy"))
               (conj base (kotoba/add stmt-e ":meisai.stmt/total-jpy"
                                      (to-int (get doc ":statement/total-jpy"))))
               base)
        base (if (get doc ":source/url")
               (conj base (kotoba/add stmt-e ":meisai.stmt/source-url"
                                      (str (get doc ":source/url"))))
               base)]
    (reduce
     (fn [out [i r]]
       (let [date (str (get r ":date" "?"))
             merchant (str (get r ":merchant" "?"))
             amount (to-int (get r ":amount_jpy" 0))
             h (sha256-hex (str stmt-e "|" i "|" date "|" merchant "|" amount))
             row-e (str "meisai-row:" (subs h 0 16))
             rows-out (-> out
                          (conj (kotoba/add row-e ":meisai.row/stmt" stmt-e))
                          (conj (kotoba/add row-e ":meisai.row/index" i))
                          (conj (kotoba/add row-e ":meisai.row/date" date))
                          (conj (kotoba/add row-e ":meisai.row/merchant" merchant))
                          (conj (kotoba/add row-e ":meisai.row/amount-jpy" amount)))]
         (if (get r ":note")
           (conj rows-out (kotoba/add row-e ":meisai.row/note" (str (get r ":note"))))
           rows-out)))
     base
     (map-indexed vector rows))))

(defn load-statement
  "Read one intake EDN file → [doc content-cid]."
  [path]
  #?(:clj
     (let [raw (slurp (File. (str path)))]
       [(kotoba/parse-edn raw) (intake-cid raw)])
     :cljs
     (throw (ex-info "load-statement requires file I/O on the JVM" {}))))
