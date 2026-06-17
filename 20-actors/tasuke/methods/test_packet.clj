(ns tasuke.methods.test-packet
  "Tests for 助 (tasuke) packet generator — babashka port of methods/test_packet.py."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [tasuke.methods.edn :as e]
            [tasuke.methods.packet :as packet]))

(def ^:private actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def ^:private SEED (delay (e/load-edn (io/file actor-dir "data" "seed-cybercrime-cases.kotoba.edn"))))

(defn- cases []
  (get @SEED ":case/batch"))

(defn- lstrip-colon [s]
  (str/replace (str s) #"^:+" ""))

(defn- doc-kinds [packet]
  (mapv #(lstrip-colon (get % ":doc/kind")) (get packet "documents")))

;; ── the packet is free + complete for every seed case ────────────────────────
(deftest test-build-packet-every-case-free-and-documented
  (doseq [c (cases)]
    (let [p (packet/build-packet c)]
      (is (= 0 (get p "cost")))
      (is (seq (get p "documents")) (str (get p "caseId") " produced no documents"))
      (doseq [d (get p "documents")]
        (is (= ":member" (get d ":doc/authored-by")))
        (is (= 0 (get d ":doc/support-cost-jpy")))
        (is (= true (get d ":doc/needs-member-signature")))
        (is (= false (get d ":doc/published")))))))

(deftest test-document-selection-by-kind
  (let [cases (into {} (map (fn [c] [(get c ":case/id") c]) (cases)))
        fund (packet/build-packet (get cases "c-fund-1"))
        to (packet/build-packet (get cases "c-takeover-1"))]
    (is (some #{"bank-freeze-request"} (set (doc-kinds fund))))
    (let [tkinds (set (doc-kinds to))]
      (is (contains? tkinds "recovery-plan"))
      (is (contains? tkinds "platform-request")))))

(deftest test-police-core-always-present
  (let [core #{"damage-report" "incident-statement" "evidence-index" "damage-calculation"}]
    (doseq [c (cases)]
      (let [kinds (set (doc-kinds (packet/build-packet c)))]
        (is (= core (clojure.set/intersection core kinds)))))))

;; ── regression: the seed registry must be reachable (the stray-brace bug) ─────
(deftest test-windows-are-populated-from-registry
  (let [p (packet/build-packet (first (cases)))]
    (is (seq (get p "windows")))
    (doseq [w (get p "windows")]
      (is (and (get w "name") (not= (get w "name") (get w "code")))))))

;; ── the cover restates the charter promises ──────────────────────────────────
(deftest test-cover-states-free-and-member-submitted
  (let [cover-text (#'packet/cover (packet/build-packet (first (cases))))]
    (is (str/includes? cover-text "\u00A50"))
    (is (str/includes? cover-text "全て無料"))
    (is (str/includes? cover-text "本人が作成・署名・提出"))))

;; ── write-packet emits printable files ───────────────────────────────────────
(deftest test-write-packet-emits-cover-and-docs
  (let [p (packet/build-packet (first (cases)))
        tmp (io/file (System/getProperty "java.io.tmpdir")
                     (str "tasuke-test-packet-" (System/currentTimeMillis)))]
    (try
      (let [out (packet/write-packet p tmp)
            files (sort (map #(.getName %) (.listFiles out)))]
        (is (some #{"00-COVER.md"} files))
        (is (= (count (get p "documents"))
               (count (filter #(str/ends-with? % ".txt") files)))))
      (finally
        (doseq [f (file-seq tmp)]
          (.delete f))))))

;; ── G1/G7 gate still bites through the packet path ───────────────────────────
(deftest test-packet-refuses-non-consented-case
  (let [bad (assoc (first (cases)) ":case/consent" false)]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"G7"
          (packet/build-packet bad)))))

(deftest test-packet-refuses-priced-case
  (let [bad (assoc (first (cases)) ":case/support-cost-jpy" 1000)]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"G1"
          (packet/build-packet bad)))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests (quote tasuke.methods.test-packet))]
    (System/exit (if (zero? (+ fail error)) 0 1))))
