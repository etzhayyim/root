(ns maps.methods.analyze
  "analyze.py — static-feature substrate coverage analyzer (kotoba-native, R0).
  1:1 Clojure port of `methods/analyze.py` (ADR-2606064500).

  Reads a kotoba-EDN static-feature graph (:feature/* placed features, :feature.rel/* topology
  edges, :geo.alias/* multi-scheme region identity) and emits an AGGREGATE-FIRST coverage report.

  The minimal EDN reader, classify, _cell-r6 (h3 → degree-grid fallback — h3 is absent on this
  host, so the degree-grid stand-in is always used, mirroring the Python except-branch),
  _h3-cells-at-res, analyze, render-report, render-datoms are pure/portable. File I/O (load-edn,
  main) is host-only behind #?(:clj ...). The __main__ demo's stdout printing is omitted."
  (:require [clojure.string :as str]))

;; ── minimal EDN reader (subset: [] {} :kw \"str\" num bool nil) — ported from watari ──
(def ^:private end-marker ::end)

(defn- atom* [t]
  (cond
    (str/starts-with? t "\"") (-> (subs t 1 (dec (count t)))
                                  (str/replace "\\\"" "\"")
                                  (str/replace "\\\\" "\\"))
    (= t "true") true
    (= t "false") false
    (= t "nil") nil
    (str/starts-with? t ":") t  ;; keep keywords as ":ns/name" strings
    :else (try (Long/parseLong t)
               (catch #?(:clj Exception :cljs js/Error) _
                 (try (Double/parseDouble t)
                      (catch #?(:clj Exception :cljs js/Error) _ t))))))

(defn- tokens
  "Tokenize EDN text. Mirrors the Python regex
  [\\s,]+|;[^\\n]*|(\\[|\\]|\\{|\\}|\"(?:\\\\.|[^\"\\\\])*\"|[^\\s,\\[\\]{}]+) — yielding only group(1)."
  [s]
  (let [n (count s)]
    (loop [i 0, out []]
      (if (>= i n)
        out
        (let [c (nth s i)]
          (cond
            ;; whitespace / comma run
            (or (contains? #{\space \tab \newline \return \,} c))
            (recur (inc i) out)
            ;; comment to end of line
            (= c \;)
            (let [j (loop [j i] (if (and (< j n) (not= (nth s j) \newline)) (recur (inc j)) j))]
              (recur j out))
            ;; structural
            (contains? #{\[ \] \{ \}} c)
            (recur (inc i) (conj out (str c)))
            ;; string
            (= c \")
            (let [end (loop [j (inc i)]
                        (let [cj (nth s j)]
                          (cond (= cj \\) (recur (+ j 2))
                                (= cj \") (inc j)
                                :else (recur (inc j)))))]
              (recur end (conj out (subs s i end))))
            ;; bare token
            :else
            (let [end (loop [j i]
                        (if (and (< j n)
                                 (not (contains? #{\space \tab \newline \return \, \[ \] \{ \}} (nth s j))))
                          (recur (inc j)) j))]
              (recur end (conj out (subs s i end))))))))))

(defn- parse* [toks idx]
  (let [t (nth toks @idx)]
    (vswap! idx inc)
    (cond
      (= t "[")
      (loop [out []]
        (let [x (parse* toks idx)]
          (if (identical? x end-marker) out (recur (conj out x)))))
      (= t "{")
      (loop [out {}]
        (let [k (parse* toks idx)]
          (if (identical? k end-marker)
            out
            (let [v (parse* toks idx)]
              (recur (assoc out k v))))))
      (or (= t "]") (= t "}")) end-marker
      :else (atom* t))))

(defn parse-edn [text]
  (let [toks (tokens text)
        idx (volatile! 0)]
    (parse* toks idx)))

#?(:clj
   (defn load-edn [path]
     (parse-edn (slurp (str path)))))

;; ── classify the flat datom vector into entity buckets ──
(defn classify
  "rows → [features rels aliases] where features/aliases are id→map, rels is a vector."
  [rows]
  (reduce
   (fn [[features rels aliases] r]
     (if-not (map? r)
       [features rels aliases]
       (cond
         (contains? r ":feature/id")    [(assoc features (get r ":feature/id") r) rels aliases]
         (contains? r ":feature.rel/id") [features (conj rels r) aliases]
         (contains? r ":geo.alias/id")  [features rels (assoc aliases (get r ":geo.alias/id") r)]
         :else [features rels aliases])))
   [(array-map) [] (array-map)]
   rows))

(defn- num? [v] (and (number? v) (not (boolean? v))))

;; ── H3 res-6 cell id, real if `h3` is installed else a documented degree-grid stand-in ──
(defn- cell-r6 [lat lon]
  ;; h3 is unavailable on this host → the documented ~1° degree-grid stand-in (Python
  ;; except-branch). Conservative (UNDER-counts), flagged honestly in the report (G3).
  ["deg" (str "deg/" (long (Math/floor lat)) "/" (long (Math/floor lon)))])

;; ── res-r cells that tile the whole Earth (exact H3 count) — the coverage denominator ──
(defn h3-cells-at-res [r]
  (+ 2 (* 120 (long (Math/pow 7 r)))))

(defn analyze
  "Returns a result map (string-keyed) mirroring the Python dict."
  [features rels aliases]
  (let [result
        (reduce
         (fn [acc [_fid f]]
           (let [lab (get f ":feature/label" ":unknown")
                 acc (update-in acc [:label-count lab] (fnil inc 0))
                 lat (get f ":feature/lat")
                 lon (get f ":feature/lon")
                 acc (if (and (num? lat) (num? lon))
                       (let [[mode cid] (cell-r6 lat lon)]
                         (-> acc
                             (update :lats conj lat)
                             (update :lons conj lon)
                             (assoc :cell-mode mode)
                             (update :cells-r6 conj cid)
                             (update-in [:hot [(double (/ (Math/round (* lat 100.0)) 100.0))
                                               (double (/ (Math/round (* lon 100.0)) 100.0))]] (fnil inc 0))))
                       acc)
                 acc (if (= (get f ":feature/label") ":building")
                       (update acc :n-buildings inc) acc)
                 acc (update-in acc [:sourcing (get f ":feature/sourcing" ":unknown")] (fnil inc 0))]
             acc))
         {:label-count (array-map) :cells-r6 #{} :cell-mode nil
          :lats [] :lons [] :hot (array-map) :n-buildings 0 :sourcing (array-map)}
         features)
        {:keys [label-count cells-r6 cell-mode lats lons hot n-buildings sourcing]} result
        bbox (when (seq lats)
               {"south" (apply min lats) "north" (apply max lats)
                "west" (apply min lons) "east" (apply max lons)})
        densest (when (seq hot)
                  (apply max-key val hot))]
    {"n_features" (count features)
     "label_count" label-count
     "n_rels" (count rels)
     "n_aliases" (count aliases)
     "cells_r6" cells-r6
     "cell_mode" cell-mode
     "bbox" bbox
     "densest" densest
     "sourcing" sourcing
     "n_buildings" n-buildings}))

(defn- fmt-float
  "Mimic Python f-string float formatting like {:.3f}."
  [x decimals]
  #?(:clj (format (str "%." decimals "f") (double x))
     :default (.toFixed (double x) decimals)))

(defn- fmt-int-comma [n]
  ;; Python f\"{den:,}\" — thousands separators.
  (let [s (str (long n))
        neg (str/starts-with? s "-")
        digits (if neg (subs s 1) s)
        grouped (->> (reverse digits)
                     (partition-all 3)
                     (map #(apply str (reverse %)))
                     reverse
                     (str/join ","))]
    (str (when neg "-") grouped)))

(defn- fmt-sci
  "Mimic Python {x:.2e}."
  [x]
  #?(:clj (let [s (format "%.2e" (double x))]
            ;; Java uses e+NN (2-digit exp); Python uses e-NN too — both fine, but Python
            ;; pads exp to ≥2 digits which Java also does. Normalize Java 'e+05' vs Python 'e-05'.
            s)
     :default (str x)))

(defn render-report [_features a]
  (let [P (atom [])
        emit (fn [line] (swap! P conj line))]
    (emit "# maps — static-feature substrate coverage report (kotoba-native)")
    (emit "")
    (emit (str "> ADR-2606064500 · **aggregate-first** · the kotoba Datom log successor to the legacy "
               "RisingWave `vertex_spatial`. Answers *「いまどれぐらい coverage できているか」*: what the "
               "substrate holds and what slice of the Earth it covers. All sourcing `:representative` — "
               "a bounded anchor seed, NOT planet-scale coverage (G3: absence = not-yet-ingested)."))
    (emit "")
    (emit (str "- features: **" (get a "n_features") "**  ·  topology edges: **" (get a "n_rels") "**  ·  "
               "geo-aliases: **" (get a "n_aliases") "**  ·  buildings (3D-extrudable): **" (get a "n_buildings") "**"))
    (let [den (h3-cells-at-res 6)
          mode-note (if (= (get a "cell_mode") "h3")
                      "real H3"
                      (str "~1° degree-grid stand-in (h3 not installed — coarse, UNDER-counts; "
                           "install `h3` for true res-6)"))
          frac (/ (double (count (get a "cells_r6"))) den)]
      (emit (str "- Earth coverage @ res-6: **" (count (get a "cells_r6")) "** distinct cells touched "
                 "/ " (fmt-int-comma den) " total (" mode-note ") ≈ **" (fmt-sci frac) "** of the planet's res-6 tiling")))
    (when-let [b (get a "bbox")]
      (emit (str "- geographic footprint: lat [" (fmt-float (get b "south") 3) ", " (fmt-float (get b "north") 3) "] · "
                 "lon [" (fmt-float (get b "west") 3) ", " (fmt-float (get b "east") 3) "]")))
    (when-let [d (get a "densest")]
      (let [[[la lo] n] d]
        (emit (str "- densest hot spot: **" n "** features at ≈(" la ", " lo ") — the localized anchor"))))
    (emit "")
    (emit "## Features by label (what the substrate actually holds)")
    (emit "")
    (emit "| label | count |")
    (emit "|---|---:|")
    (doseq [lab (sort-by (fn [k] (- (get-in a ["label_count" k]))) (keys (get a "label_count")))]
      (emit (str "| `" lab "` | " (get-in a ["label_count" lab]) " |")))
    (emit "")
    (emit "## Sourcing (G3 honesty)")
    (emit "")
    (emit "| sourcing | count |")
    (emit "|---|---:|")
    (doseq [s (sort-by (fn [k] (- (get-in a ["sourcing" k]))) (keys (get a "sourcing")))]
      (emit (str "| `" s "` | " (get-in a ["sourcing" s]) " |")))
    (emit "")
    (emit "---")
    (emit (str "*Generated by `maps/methods/analyze.py` (stdlib; real H3 only if `h3` is installed). "
               "HONEST R0: bounded `:representative` anchor seed (Tokyo Station), NOT a live "
               "planet-scale ingest. The H3 res-6 fraction is literal-but-tiny by design — this seed "
               "demonstrates the kotoba `:feature/*` model + AVET cell index, it does NOT claim Earth "
               "coverage. Backfilling the real `vertex_spatial` export (ingest.py) grows this number; "
               "the 3D walker's loaded extent is unchanged by the substrate swap (ADR-2606064500 §"
               "Honest R0).*"))
    (str (str/join "\n" @P) "\n")))

(defn render-datoms [a]
  (let [P (atom [])
        emit (fn [line] (swap! P conj line))]
    (emit ";; maps — DERIVED coverage datoms (ADR-2606064500). :derived — NOT fact.")
    (emit ";; Recomputed from the seed graph; do not re-ingest as :authoritative.")
    (emit "[")
    (emit (str " {:coverage/feature-count " (get a "n_features") " :coverage/derived true}"))
    (emit (str " {:coverage/cell-count-r6 " (count (get a "cells_r6")) " :coverage/cell-mode \"" (get a "cell_mode") "\" "
               ":coverage/derived true}"))
    (when-let [b (get a "bbox")]
      (emit (str " {:coverage/bbox-south " (get b "south") " :coverage/bbox-north " (get b "north") " "
                 ":coverage/bbox-west " (get b "west") " :coverage/bbox-east " (get b "east") " :coverage/derived true}")))
    (when-let [d (get a "densest")]
      (let [[[la lo] n] d]
        (emit (str " {:coverage/anchor-density " n " :coverage/anchor-lat " la " :coverage/anchor-lon " lo " "
                   ":coverage/derived true}"))))
    (emit "]")
    (str (str/join "\n" @P) "\n")))
