;; test_lexicon.clj — the danjo revenue-ledger lexicons carry the constitutional anchors AND
;; stay in parity with the code that emits them. Run: bb test_lexicon.clj  (from methods/).
(ns root.danjo.methods.test-lexicon
  (:require [clojure.string :as str]
            [clojure.set :as set]))

(load-file "discrepancy.clj")
(load-file "ingest.clj")
(alias 'd  'root.danjo.methods.discrepancy)
(alias 'in 'root.danjo.methods.ingest)

(def lex-dir "../../../00-contracts/lexicons/com/etzhayyim/danjo/")
(defn lex [name] (in/parse-json (slurp (str lex-dir name ".json"))))
(defn props [doc] (get-in doc ["defs" "main" "record" "properties"]))

(def verdict-tokens ["crime" "criminal" "violat" "guilt" "illegal" "unlawful" "fraud" "犯罪" "違法" "有罪" "不正"])
(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))

;; ── reconciliationObservation: non-adjudication anchor + verdict-free enum (mirrors lint Check B) ──
(let [r (lex "reconciliationObservation")
      p (props r)
      cats (get-in p ["category" "knownValues"])]
  (check "reconciliationObservation lexicon id correct" (= "com.etzhayyim.danjo.reconciliationObservation" (get r "id")))
  (check "nonAdjudicatingNotice const:true" (= true (get-in p ["nonAdjudicatingNotice" "const"])))
  (check "category enum carries NO verdict token"
         (not-any? (fn [v] (some #(str/includes? (str/lower-case v) %) verdict-tokens)) cats))
  (check "sourceRecordCids minLength 2 (G5)" (= 2 (get-in p ["sourceRecordCids" "minLength"])))
  (check "methodNoteCid required (G6)" (some #{"methodNoteCid"} (get-in r ["defs" "main" "record" "required"])))
  ;; code ↔ lexicon parity: every category discrepancy.clj can emit is representable in the lexicon
  (let [emitted (set (map #(name (:category %))
                          (concat (d/reconcile {:appropriations [] :outlays [{:program-code "P" :fiscal-year 2024 :amount-jpy 9 :source-record-cids ["a" "b"]}]} 2024)
                                  (d/reconcile {:appropriations [{:program-code "Q" :fiscal-year 2024 :amount-jpy 1 :source-record-cids ["a" "b"]}]
                                                :outlays [{:program-code "Q" :fiscal-year 2024 :amount-jpy 5 :source-record-cids ["a" "b"]}]} 2024)
                                  (d/reconcile {:appropriations [{:program-code "R" :fiscal-year 2024 :amount-jpy 9 :source-record-cids ["a" "b"]}]
                                                :outlays [{:program-code "R" :fiscal-year 2024 :amount-jpy 1 :source-record-cids ["a" "b"]}]} 2024))))]
    (check "code↔lexicon parity: emitted categories ⊆ lexicon enum"
           (set/subset? emitted (set cats)))))

;; ── fiscalOrg: keyless / no-server-key anchors ──
(let [p (props (lex "fiscalOrg"))]
  (check "fiscalOrg keyless const:true" (= true (get-in p ["keyless" "const"])))
  (check "fiscalOrg verificationMethod maxLength 0 (no-server-key)" (= 0 (get-in p ["verificationMethod" "maxLength"]))))

;; ── taxClassification: honest 3-way enum + representative-only ──
(let [p (props (lex "taxClassification"))]
  (check "taxClassification earmarkKind = honest 3-way"
         (= #{"general" "statutory-purpose" "special-account"} (set (get-in p ["earmarkKind" "knownValues"]))))
  (check "taxClassification sourcing const:representative" (= "representative" (get-in p ["sourcing" "const"]))))

(println (format "── lexicon: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
