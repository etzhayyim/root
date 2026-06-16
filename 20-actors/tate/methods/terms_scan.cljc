(ns tate.methods.terms-scan
  "tate 盾 — disadvantageous-clause scanner over the member's OWN contracts / ToS.
  1:1 Clojure port of `methods/terms_scan.py` (ADR-2606112301 + worldwide 2606112400).

  Matches the member's contract texts (consumer ToS / credit-card member agreement /
  B2B 法人契約) against the coded clause-pattern registry and emits FLAGS: pattern +
  DISCLOSED statutory anchor + risk + route. 不利な契約をしていないか — surfaced, not
  adjudicated.

  CONSTITUTIONAL (read before any change):
    G1 — member-principal, own documents only (R0 = synthetic seed).
    G2 — non-adjudicating (UPL): a flag is {pattern, anchor, risk, route}, never a verdict.
    G5 — context honesty: consumer anchors NEVER fire on :b2b documents.
    G10 — jurisdiction honesty: anchors never cross jurisdictions.

  House style: this module also hosts the SHARED minimal EDN reader the sibling tate.*
  method modules require (read-edn / load-* / HERE). Python ':…' keyword strings stay
  strings; data maps stay string-keyed. File I/O only behind #?(:clj …). The Python
  __main__ demo printer (out/*.md, clause-flags.json) is intentionally omitted."
  (:require [clojure.string :as str]))

;; ── minimal EDN reader (subset: vectors [], maps {}, :keyword, "string", num, bool, nil)
;; Mirrors terms_scan.py's _TOK / _tokens / _atom / _parse faithfully. Keywords are kept
;; as ":ns/name" strings (NOT clojure keywords) so the whole pipeline stays string-keyed,
;; byte-for-byte the same shapes Python produced.

(def ^:private tok-re
  ;; _TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
  #"[\s,]+|;[^\n]*|(\[|\]|\{|\}|\"(?:\\.|[^\"\\])*\"|[^\s,\[\]{}]+)")

(defn tokens
  "Lazy seq of significant tokens (group 1 of each tok-re match that captured)."
  [s]
  (let [m (re-matcher tok-re s)]
    ((fn step []
       (lazy-seq
        (when (.find m)
          (let [t (.group m 1)]
            (if (nil? t)
              (step)
              (cons t (step))))))))))

(defn atom-of
  "Port of _atom: \"…\" → unescaped string; true/false/nil → bool/nil; \":…\" kept as
  string; int → long; else float; else raw string."
  [t]
  (cond
    (str/starts-with? t "\"")
    (-> (subs t 1 (dec (count t)))
        (str/replace "\\\"" "\"")
        (str/replace "\\\\" "\\"))
    (= t "true") true
    (= t "false") false
    (= t "nil") nil
    (str/starts-with? t ":") t
    :else
    (let [as-long (try (Long/parseLong t) (catch #?(:clj Exception :cljs :default) _ ::nan))]
      (if (not= as-long ::nan)
        as-long
        (let [as-dbl (try (Double/parseDouble t) (catch #?(:clj Exception :cljs :default) _ ::nan))]
          (if (not= as-dbl ::nan) as-dbl t))))))

(def ^:private end-marker ::end)

(defn- parse-step
  "Consume one form from the token vector at index i. Returns [value next-i] or
  [end-marker next-i] when a closing ] or } is hit (matching _parse's _END sentinel)."
  [toks i]
  (let [t (nth toks i)
        i (inc i)]
    (cond
      (= t "[")
      (loop [i i, out []]
        (let [[x i] (parse-step toks i)]
          (if (= x end-marker)
            [out i]
            (recur i (conj out x)))))

      (= t "{")
      (loop [i i, out {}]
        (let [[k i] (parse-step toks i)]
          (if (= k end-marker)
            [out i]
            (let [[v i] (parse-step toks i)]
              (recur i (assoc out k v))))))

      (or (= t "]") (= t "}"))
      [end-marker i]

      :else
      [(atom-of t) i])))

(defn read-edn
  "Parse the first top-level form from EDN text (matches read_edn → _parse(_tokens(text)))."
  [text]
  (let [toks (vec (tokens text))]
    (first (parse-step toks 0))))

;; ── host paths (ROOT/20-actors/tate via *file*: …/tate/methods/terms_scan.cljc → up 2)
#?(:clj
   (def HERE
     "tate actor dir (== Python HERE = pathlib(__file__).resolve().parent.parent)."
     (-> *file* clojure.java.io/file .getParentFile .getParentFile)))

(def risk-order {":high" 0 ":mid" 1 ":info" 2})

#?(:clj
   (defn- read-edn-file [path]
     (read-edn (slurp (str path)))))

#?(:clj
   (defn load-patterns
     "[f for f in read_edn(...) if \":clause/id\" in f]"
     ([] (load-patterns (clojure.java.io/file HERE "data" "clause-patterns.edn")))
     ([path] (filterv #(contains? % ":clause/id") (read-edn-file path)))))

#?(:clj
   (defn load-docs
     "Returns [docs notices]: forms with :doc/id and forms with :notice/id."
     ([] (load-docs (clojure.java.io/file HERE "data" "seed-member-docs.edn")))
     ([path]
      (let [forms (read-edn-file path)
            docs (filterv #(and (map? %) (contains? % ":doc/id")) forms)
            notices (filterv #(and (map? %) (contains? % ":notice/id")) forms)]
        [docs notices]))))

(defn scan-doc
  "Flags for one document. G5: pattern context must match the document context.
  G10: pattern jurisdiction must match the document jurisdiction (default :jp)."
  [doc patterns]
  (let [text (str/lower-case (get doc ":doc/text" ""))
        ctx (get doc ":doc/context")
        juris (get doc ":doc/jurisdiction" ":jp")
        flags (reduce
               (fn [flags p]
                 (cond
                   (not= (get p ":clause/context") ctx) flags
                   (not= (get p ":clause/jurisdiction" ":jp") juris) flags
                   :else
                   (if-let [hit (first (filter #(str/includes? text (str/lower-case %))
                                               (get p ":clause/keywords")))]
                     (conj flags
                           {"doc" (get doc ":doc/id")
                            "doc_label" (get doc ":doc/label" (get doc ":doc/id"))
                            "jurisdiction" juris
                            "clause" (get p ":clause/id")
                            "clause_label" (get p ":clause/label")
                            "matched" hit
                            "risk" (get p ":clause/risk")
                            "anchor" (get p ":clause/anchor")
                            "route" (get p ":clause/route")
                            "disclosed" true
                            "verify_current_law" true})
                     flags)))
               []
               patterns)]
    ;; flags.sort(key=lambda f: (RISK_ORDER.get(f["risk"], 9), f["clause"])) — stable
    (vec (sort-by (juxt #(get risk-order (get % "risk") 9) #(get % "clause")) flags))))

(defn scan
  [docs patterns]
  (let [flags (vec (mapcat #(scan-doc % patterns) docs))
        by-route (reduce (fn [m f] (update m (get f "route") (fnil inc 0))) {} flags)]
    {"flags" flags
     "docs_scanned" (count docs)
     ;; dict(sorted(by_route.items())) — sorted by route key
     "counts_by_route" (into (sorted-map) by-route)}))

(defn- edn-str
  "Python _edn_str: quote + escape backslash then double-quote."
  [s]
  (str "\"" (-> (str s) (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\""))

(defn make-kaiyaku-handoff
  "Machine-readable handoff to kaiyaku 解約: every :kaiyaku-routed flag as ingestable EDN."
  [res]
  (let [L (transient
           [";; tate 盾 → kaiyaku 解約 handoff — GENERATED (ADR-2606112301/2606112201). DO NOT hand-edit."
            ";; :kaiyaku-routed clause flags only — 自動更新/解約窓 candidates for the 縁-ledger."
            ""
            "["])]
    (doseq [f (get res "flags")]
      (when (= (get f "route") ":kaiyaku")
        (conj! L (str " {:handoff/doc " (edn-str (get f "doc"))))
        (conj! L (str "  :handoff/jurisdiction " (get f "jurisdiction")))
        (conj! L (str "  :handoff/clause " (edn-str (get f "clause"))))
        (conj! L (str "  :handoff/matched " (edn-str (get f "matched"))))
        (conj! L (str "  :handoff/anchor " (edn-str (get f "anchor"))))
        (conj! L "  :handoff/action :calendar-notice-window}")))
    (conj! L "]")
    (str (str/join "\n" (persistent! L)) "\n")))

(defn report
  [res]
  (let [L (transient
           ["# tate 盾 — 不利条項 readout (non-adjudicating, G2)"
            ""
            (str "- docs scanned: " (get res "docs_scanned") " · flags: " (count (get res "flags"))
                 " · routes: " (pr-str (get res "counts_by_route")))
            ""
            "| doc | juris | clause | risk | 開示アンカー | route |"
            "|---|---|---|---|---|---|"])]
    (doseq [f (get res "flags")]
      (conj! L (str "| " (get f "doc_label") " | " (get f "jurisdiction") " | "
                    (get f "clause_label") " | " (get f "risk") " | " (get f "anchor")
                    " | " (get f "route") " |")))
    (conj! L "")
    (conj! L (str "各フラグは「該当する **可能性** のある条項パターン + 開示済み法令アンカー」です。"
                  "有効/無効の判断はしません — 高リスクは法テラス・弁護士会の専門家確認へ (G2 UPL)。"))
    (str (str/join "\n" (persistent! L)) "\n")))
