(ns kaiyaku.tests.test-handoff
  "kaiyaku 解約 — tate handoff ingest tests (wave 26). 1:1 Clojure port of tests/test_handoff.py.

  The compose loop closes: tate's make-kaiyaku-handoff output is parsed by kaiyaku's ingest
  and every :kaiyaku-routed clause flag becomes a notice-window candidate — round-trip across
  the two actors, no shared code beyond the EDN wire format."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [kaiyaku.methods.handoff-ingest :as handoff]
            [tate.methods.terms-scan :as terms-scan]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))

(defn- cands [] (handoff/ingest (handoff/live-handoff-from-tate)))

(deftest test-roundtrip-count-matches-tate
  ;; Every :kaiyaku-routed tate flag arrives as exactly one candidate.
  (let [[docs _] (terms-scan/load-docs)
        res (terms-scan/scan docs (terms-scan/load-patterns))
        expect (filter #(= ":kaiyaku" (get % "route")) (get res "flags"))
        cs (cands)]
    (is (and (= (count cs) (count expect)) (>= (count cs) 10)))
    (is (= (set (map #(get % "clause") cs)) (set (map #(get % "clause") expect))))))

(deftest test-candidates-are-calendar-actions
  (doseq [c (cands)]
    (is (= ":calendar-notice-window" (get c "action")) (str c))
    (is (seq (get c "anchor")) (str c))   ; 開示アンカーは handoff を越えて保持される
    (is (str/starts-with? (get c "jurisdiction") ":"))))

(deftest test-datoms-emitted
  (let [cs (cands)
        text (handoff/to-datoms cs 5)]
    (is (= (count cs)
           (count (re-seq #":kaiyaku\.handoff/clause" text))))
    (is (str/includes? text ":kaiyaku.handoff/action :calendar-notice-window"))))

;; (test-kaiyaku-claude-md-counts-in-sync removed in the ADR-2606160842 py→clj prune wave:
;; it counted `\ndef test_` across the now-pruned Python test files — a doc-sync guard for
;; Python that has no referent once the .py are gone. The cljc suites carry their own coverage.)
