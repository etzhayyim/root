;; test_analyze.clj — danjo discrepancy analyzer + byte-identical parity with analyze.py.
;; Run: bb test_analyze.clj   (or: clojure -M test_analyze.clj)   from methods/.
(ns root.danjo.methods.test-analyze
  (:require [clojure.string :as str]))

(load-file "analyze.clj")
(alias 'an 'root.danjo.methods.analyze)

(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))

;; ── canonical-json-ascii: ensure_ascii=True (distinct from budget_ledger's encoder) ──
(check "canonical-json-ascii sorts keys, no whitespace"
       (= "{\"a\":1,\"b\":\"x\"}" (an/canonical-json-ascii {"b" "x" "a" 1})))
(check "canonical-json-ascii escapes non-ASCII as \\uXXXX (教 = U+6559)"
       (= "{\"k\":\"\\u6559\"}" (an/canonical-json-ascii {"k" "教"})))
(check "canonical-json-ascii bool/nil → true/false/null"
       (= "[true,false,null]" (an/canonical-json-ascii [true false nil])))

;; ── method-cid byte parity (golden from analyze.py) ──
(let [methods (an/load-json "v1-jp-seed.json")
      m       (->> (get methods "methods") (filter #(= "single-bidder-streak" (get % "methodId"))) first)]
  (check "method-cid(single-bidder-streak) == Python golden"
         (= "method:single-bidder-streak:955ade7944f2" (an/method-cid m))))

;; ── build-observation discipline (G5 ≥2 cids, G4 no verdict field) ──
(check "build-observation RAISES on <2 source cids (G5)"
       (try (an/build-observation {:cids ["only-one"] :count 1 :authority "a" :awardee "b"}
                                  {"methodId" "single-bidder-streak"}) false
            (catch Exception _ true)))
(let [o (an/build-observation {:cids ["c1" "c2"] :count 2 :authority "auth:x" :awardee "lei:y"}
                              {"methodId" "single-bidder-streak"})
      ks (set (map name (keys o)))]
  (check "observation is non-adjudicating (G4)" (true? (:nonAdjudicatingNotice o)))
  (check "G4 — no verdict/crime/guilt key on an observation"
         (empty? (filter #(some (fn [t] (str/includes? (str/lower-case %) t))
                                ["verdict" "guilt" "wrongdoing" "crime" "illegal" "sanction"])
                         ks)))
  (check "observation carries a methodNoteCid (G6)" (str/starts-with? (:methodNoteCid o) "method:")))

;; ── end-to-end on the seed corpus (parity with analyze.py run_all) ──
(let [corpus  (an/load-json "../data/corpus.seed.json")
      methods (an/load-json "v1-jp-seed.json")
      obs     (an/run-all corpus methods)]
  (check "seed → exactly 1 discrepancy observation" (= 1 (count obs)))
  (let [o (first obs)]
    (check "observation category == single-bidder-streak" (= "single-bidder-streak" (:category o)))
    (check "observation has 6 source cids (≥2, G5)" (= 6 (count (:sourceRecordCids o))))
    (check "observed pattern matches Python golden"
           (= "6 consecutive single-bid awards from auth:jp:mlit to lei:5493ACME000000000001 within the method window"
              (:observedPattern o))))

  ;; ── render-edn byte-identical with analyze.py render_edn ──
  (let [golden (str ";; danjo-observations.kotoba.edn — danjo.discrepancyObservation records.\n"
                    ";; G4 nonAdjudicatingNotice=true (FACT, never a verdict) · G5 ≥2 sourceRecordCids\n"
                    ";; · G6 methodNoteCid. The censor's EYE, never the SWORD. Named-party publication\n"
                    ";; G10 + 1 SBT=1 vote gated. DERIVED :representative. ADR-2605301600.\n"
                    "\n[\n"
                    " {:danjo.obs/category :single-bidder-streak :danjo.obs/non-adjudicating true "
                    ":danjo.obs/pattern \"6 consecutive single-bid awards from auth:jp:mlit to lei:5493ACME000000000001 within the method window\" "
                    ":danjo.obs/source-record-cids [\"bafy-proc-001\" \"bafy-proc-002\" \"bafy-proc-003\" \"bafy-proc-004\" \"bafy-proc-005\" \"bafy-proc-006\"] "
                    ":danjo.obs/method-note-cid \"method:single-bidder-streak:955ade7944f2\" "
                    ":danjo.obs/sourcing :representative}\n"
                    "]\n")]
    (check "render-edn is byte-identical with analyze.py render_edn" (= golden (an/render-edn obs)))))

(println (format "── test_analyze: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
