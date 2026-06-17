(ns yabai.methods.ingest
  "ingest.py — yabai ACTIVE CTI / passive-DNS collector → kotoba EAVT.
  1:1 Clojure port of `methods/ingest.py` (ADR-2605301400 §T3).

  Defensive threat-intel collector. Pulls PUBLIC CTI surfaces and normalizes them into the
  passive-dns-cti kotoba vocabulary (:domain/* :pdns/* :tlscert/* :indicator/* …), dedup-merges
  with the curated seed (seed wins on id), and writes a merged EAVT graph analyze.py consumes.

  ACTIVE COLLECTION is operator-gated + offline-default. A live network pull (--live) is
  GATE-G7 (YABAI_OPERATOR_GATE).

  House style: ':…' keyword strings stay strings; pure fns (slug / ip-id / parse-crtsh /
  bridge-pdns / key-of) are portable; a minimal JSON reader is inlined (no cheshire/data.json);
  network + file I/O only behind #?(:clj …). The Python `__main__` CLI driver + live crt.sh fetch
  (urllib) are omitted (noted here): main wires source/in/domain/family/live flags to the
  bridges + the dedup-merge writer."
  (:require [clojure.string :as str]
            [yabai.methods.yabai-edn :as edn]))

(def crtsh "https://crt.sh/?q={q}&output=json")
(def vendor-families #{"securitytrails" "dnsdb" "recordedfuture"})

(defn slug
  "Port of _slug(s): re.sub(r'[^a-z0-9]+','-', str(s).lower()).strip('-')."
  [s]
  (-> (str/lower-case (str s))
      (str/replace #"[^a-z0-9]+" "-")
      (str/replace #"^-+" "")
      (str/replace #"-+$" "")))

(defn ip-id
  "Port of _ip_id(addr)."
  [addr]
  (str "ip." (if (str/includes? addr ":") "v6." "v4.")
       (-> addr (str/replace "." "-") (str/replace ":" "-"))))

;; ── minimal JSON reader (Python json.loads shapes: maps string-keyed, ints→long) ──
(declare json-value)

(defn- skip-ws [^String s i]
  (loop [i i]
    (if (and (< i (count s)) (contains? #{\space \tab \newline \return} (nth s i)))
      (recur (inc i)) i)))

(defn- json-string [^String s i]
  (loop [i (inc i), sb (StringBuilder.)]
    (let [c (nth s i)]
      (cond
        (= c \") [(.toString sb) (inc i)]
        (= c \\)
        (let [e (nth s (inc i))]
          (case e
            \" (do (.append sb \") (recur (+ i 2) sb))
            \\ (do (.append sb \\) (recur (+ i 2) sb))
            \/ (do (.append sb \/) (recur (+ i 2) sb))
            \b (do (.append sb \backspace) (recur (+ i 2) sb))
            \f (do (.append sb \formfeed) (recur (+ i 2) sb))
            \n (do (.append sb \newline) (recur (+ i 2) sb))
            \r (do (.append sb \return) (recur (+ i 2) sb))
            \t (do (.append sb \tab) (recur (+ i 2) sb))
            \u (let [cp (Integer/parseInt (subs s (+ i 2) (+ i 6)) 16)]
                 (.append sb (char cp)) (recur (+ i 6) sb))
            (do (.append sb e) (recur (+ i 2) sb))))
        :else (do (.append sb c) (recur (inc i) sb))))))

(defn- json-number [^String s i]
  (let [end (loop [j i]
              (if (and (< j (count s))
                       (contains? #{\0 \1 \2 \3 \4 \5 \6 \7 \8 \9 \+ \- \. \e \E} (nth s j)))
                (recur (inc j)) j))
        tok (subs s i end)]
    [(if (some #{\. \e \E} tok) (Double/parseDouble tok) (Long/parseLong tok)) end]))

(defn- json-array [^String s i]
  (loop [i (skip-ws s (inc i)), out []]
    (if (= (nth s i) \])
      [out (inc i)]
      (let [[v i] (json-value s i)
            i (skip-ws s i)]
        (if (= (nth s i) \,)
          (recur (skip-ws s (inc i)) (conj out v))
          [(conj out v) (inc i)])))))

(defn- json-object [^String s i]
  (loop [i (skip-ws s (inc i)), out {}]
    (if (= (nth s i) \})
      [out (inc i)]
      (let [[k i] (json-string s i)
            i (skip-ws s i)
            [v i] (json-value s (skip-ws s (inc i)))
            out (assoc out k v)
            i (skip-ws s i)]
        (if (= (nth s i) \,)
          (recur (skip-ws s (inc i)) out)
          [out (inc i)])))))

(defn- json-value [^String s i]
  (let [i (skip-ws s i), c (nth s i)]
    (cond
      (= c \{) (json-object s i)
      (= c \[) (json-array s i)
      (= c \") (json-string s i)
      (= c \t) [true (+ i 4)]
      (= c \f) [false (+ i 5)]
      (= c \n) [nil (+ i 4)]
      :else (json-number s i))))

(defn parse-json [text] (first (json-value text 0)))

(defn- strip-star-dot [s]
  ;; .strip().lstrip("*.")  — leading '*' and '.' chars removed
  (str/replace (str/trim s) #"^[*.]+" ""))

(defn parse-crtsh
  "Port of parse_crtsh(text, sourcing). crt.sh JSON → [domains certs]."
  ([text] (parse-crtsh text "authoritative"))
  ([text sourcing]
   (let [rows (parse-json text)]
     (reduce
      (fn [[domains certs seen] r]
        (let [cn (strip-star-dot (or (get r "common_name") ""))
              sans (->> (str/split-lines (or (get r "name_value") ""))
                        (map strip-star-dot)
                        (filter #(not= "" (str/trim %)))
                        vec)
              ;; {cn, *sans} dedup, cn first then sans in order (Python set order not testable)
              cand (distinct (cons cn sans))
              [domains seen]
              (reduce
               (fn [[domains seen] d]
                 (if (or (= "" d) (contains? seen d))
                   [domains seen]
                   (let [tld (if (str/includes? d ".") (last (str/split d #"\.")) d)]
                     [(assoc domains (str "domain." (slug d))
                             {":domain/id" (str "domain." (slug d)) ":domain/fqdn" d
                              ":domain/tld" tld ":domain/sourcing" (str ":" sourcing)})
                      (conj seen d)])))
               [domains seen]
               cand)
              sha (str (or (get r "serial_number") (get r "id") ""))
              cert {":tlscert/id" (str "cert." (slug cn) "." (if (= "" (subs sha 0 (min 8 (count sha)))) "x" (subs sha 0 (min 8 (count sha)))))
                    ":tlscert/sha256" sha
                    ":tlscert/issuer" (get r "issuer_name" "?")
                    ":tlscert/subject" cn
                    ":tlscert/san" (if (seq sans) sans [cn])
                    ":tlscert/not-before" (subs (or (get r "not_before") "") 0 (min 10 (count (or (get r "not_before") ""))))
                    ":tlscert/not-after" (subs (or (get r "not_after") "") 0 (min 10 (count (or (get r "not_after") ""))))
                    ":tlscert/ct-log" "crt.sh"
                    ":tlscert/anomaly" ":none"
                    ":tlscert/sourcing" (str ":" sourcing)}]
          [domains (conj certs cert) seen]))
      [{} [] #{}]
      rows)
     ;; final: [domains.values() certs]
     )))

(defn bridge-pdns
  "Port of bridge_pdns(records, sourcing). passive-DNS-shaped JSON → [domains pdns]."
  ([records] (bridge-pdns records "representative"))
  ([records sourcing]
   (let [[domains pdns]
         (reduce
          (fn [[domains pdns] r]
            (let [d (str/trim (str (get r "domain" "")))]
              (if (= "" d)
                [domains pdns]
                (let [did (str "domain." (slug d))
                      domains (assoc domains did
                                     {":domain/id" did ":domain/fqdn" d
                                      ":domain/tld" (if (str/includes? d ".") (last (str/split d #"\.")) d)
                                      ":domain/sourcing" (str ":" sourcing)})
                      rrtype (str/lower-case (str (get r "rrtype" "a")))
                      rrdata (or (get r "rrdata")
                                 (if (get r "value") [(get r "value")] []))
                      rec0 {":pdns/id" (str "pdns." (slug d) "." rrtype "." (slug (str (vec (take 1 rrdata)))))
                            ":pdns/domain" did ":pdns/rrtype" (str ":" rrtype)
                            ":pdns/rrdata" rrdata ":pdns/sourcing" (str ":" sourcing)}
                      rec1 (if (and (contains? #{"a" "aaaa"} rrtype) (seq rrdata))
                             (assoc rec0 ":pdns/ip" (ip-id (first rrdata)))
                             rec0)
                      rec2 (if (some? (get r "ttl"))
                             (assoc rec1 ":pdns/ttl" (long (get r "ttl")))
                             rec1)
                      rec3 (if (get r "first_seen")
                             (assoc rec2 ":pdns/first-seen-at" (get r "first_seen"))
                             rec2)
                      rec4 (if (get r "last_seen")
                             (assoc rec3 ":pdns/last-seen-at" (get r "last_seen"))
                             rec3)]
                  [domains (conj pdns rec4)]))))
          [{} []]
          records)]
     [(vec (vals domains)) pdns])))

;; NOTE: parse-crtsh above returns the raw reduce accumulator; expose a clean [domains certs].
(defn parse-crtsh-result
  "[domains-vec certs-vec] for parse-crtsh (Python returns list(domains.values()), certs)."
  ([text] (parse-crtsh-result text "authoritative"))
  ([text sourcing]
   (let [[domains certs _seen] (parse-crtsh text sourcing)]
     [(vec (vals domains)) certs])))

(def ^:private merge-id-keys
  [":domain/id" ":pdns/id" ":iphist/id" ":tlscert/id"
   ":indicator/id" ":access/id" ":btobs/id"])

(defn key-of
  "Port of _key(rec): first present id key's value, else nil."
  [rec]
  (some (fn [k] (when (contains? rec k) (get rec k))) merge-id-keys))

(defn merge-rows
  "Port of the seed+bridged dedup-merge: dedup by id, seed wins (first seen)."
  [seed-rows bridged]
  (first
   (reduce
    (fn [[merged seen] rec]
      (if-not (map? rec)
        [merged seen]
        (let [k (key-of rec)]
          (if (or (nil? k) (contains? seen k))
            [merged seen]
            [(conj merged rec) (conj seen k)]))))
    [[] #{}]
    (concat seed-rows bridged))))
