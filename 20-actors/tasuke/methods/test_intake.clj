#!/usr/bin/env bb
;; test_intake.clj — Tests for 助 (tasuke) plain-language intake.
;; Babashka port of methods/test_intake.py.
;;
;; Run: bb --classpath 20-actors 20-actors/tasuke/methods/test_intake.clj
(ns tasuke.methods.test-intake
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [tasuke.methods.intake :as intake]
            [tasuke.methods.packet :as packet]))

;; ── helpers ───────────────────────────────────────────────────────────────────

(defn- answers
  "Build a base answers map, with optional overrides."
  [& {:as over}]
  (merge {"consent"    "はい"
          "narrative"  "口座から不正送金された"
          "occurred"   "2026-06-03"
          "loss"       "48万"
          "service"    "○○銀行"
          "account_id" "普通1234567"}
         over))

;; ── loss parser handles human input ──────────────────────────────────────────

(deftest test-parse-yen-forms
  (is (= 480000 (intake/parse-yen "480000")))
  (is (= 480000 (intake/parse-yen "48万")))
  (is (= 480000 (intake/parse-yen "48万円")))
  (is (= 480000 (intake/parse-yen "480,000円")))
  (is (= 15000  (intake/parse-yen "1万5000")))
  (is (= 0      (intake/parse-yen "なし")))
  (is (= 0      (intake/parse-yen ""))))

(deftest test-parse-yesno
  (is (= true  (intake/parse-yesno "はい")))
  (is (= true  (intake/parse-yesno "yes")))
  (is (= false (intake/parse-yesno "いいえ")))
  (is (= false (intake/parse-yesno ""))))

;; ── build_case bakes in G1/G7 ────────────────────────────────────────────────

(deftest test-build-case-sets-invariants
  (let [c (intake/build-case-from-answers (answers))]
    (is (= true    (get c ":case/consent")))
    (is (= 0       (get c ":case/support-cost-jpy")))
    (is (= false   (get c ":case/server-held-key")))
    (is (= 480000  (get c ":case/loss-jpy")))
    (is (= 480000  (get (first (get c ":case/loss-breakdown")) ":jpy")))))

(deftest test-build-case-refuses-without-consent
  (doseq [bad ["いいえ" "" "no"]]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"G7"
                          (intake/build-case-from-answers (answers "consent" bad))))))

(deftest test-case-id-is-deterministic
  (let [a (answers)
        b (answers)]
    (is (= (get (intake/build-case-from-answers a) ":case/id")
           (get (intake/build-case-from-answers b) ":case/id")))))

;; ── end-to-end: answers → packet, free, member-authored ──────────────────────

(deftest test-answers-to-packet-is-free-and-complete
  (let [case (intake/build-case-from-answers (answers))
        p    (packet/build-packet case)]
    (is (= 0 (get p "cost")))
    (let [kinds (map #(clojure.string/replace (get % ":doc/kind") #"^:+" "")
                     (get p "documents"))]
      (is (some #{"damage-report"} kinds))
      (is (some #{"bank-freeze-request"} kinds)))
    (doseq [d (get p "documents")]
      (is (= ":member" (get d ":doc/authored-by")))
      (is (= false (get d ":doc/published"))))))

;; ── interactive shell honors the injected asker + consent abort ──────────────

(deftest test-interactive-collects-with-injected-asker
  (let [answers-seq (atom ["はい" "乗っ取り被害" "2026-06-02" "なし" "LINE" "@me"])
        case (intake/interactive (fn [_prompt]
                                   (let [v (first @answers-seq)]
                                     (swap! answers-seq rest)
                                     v)))]
    (is (= true (get case ":case/consent")))
    (is (= 0    (get case ":case/loss-jpy")))))

(deftest test-interactive-aborts-on-no-consent
  (is (thrown? clojure.lang.ExceptionInfo
               (intake/interactive (fn [_prompt] "いいえ")))))

;; ── entry point ──────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'tasuke.methods.test-intake)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
