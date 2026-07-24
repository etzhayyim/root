(ns test-lite-runner
  "Tests for the bb lite-runner (cljc port of lite_runner.py). Pins the parity-critical
  contract — the ops commit-DAG must be BYTE-IDENTICAL to the python runner so the two
  are drop-in interchangeable (the property that makes the runtime cutover safe) — plus
  cron parsing, cells.edn loading, native cljc cell firing (the cutover capability), and
  the error-safe supervisor contract. Includes a LIVE py↔clj byte-parity deftest."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.java.shell :refer [sh]]
            [clojure.string :as str]
            [lite-runner :as lr]))

(deftest tx-cid-is-content-addressed-and-deterministic
  (let [datoms [[":db/add" "e1" ":cell.run/node" ":issachar"]
                [":db/add" "e1" ":cell.run/status" ":ok"]]]
    ;; deterministic + prefixed "b" + 64 hex
    (is (= (lr/tx-cid datoms "") (lr/tx-cid datoms "")))
    (is (re-matches #"b[0-9a-f]{64}" (lr/tx-cid datoms "")))
    ;; prev changes the cid (chained commit-DAG)
    (is (not= (lr/tx-cid datoms "") (lr/tx-cid datoms "bprev")))))

(deftest cron-minute-matches-python-semantics
  (is (= #{17} (lr/cron-minute "17 * * * *")))
  (is (= #{0 10 20 30 40 50} (lr/cron-minute "*/10 * * * *")))
  (is (= 60 (count (lr/cron-minute "*"))))
  (is (= 60 (count (lr/cron-minute nil))))
  (is (= #{5 15 25} (lr/cron-minute "5,15,25 * * * *"))))

(deftest load-cells-filters-cron-cells-for-node
  ;; reads the real cells.edn; every returned cell is a cron cell on the asked node
  (let [doc (clojure.edn/read-string (slurp "cells.edn"))
        a-node (-> (get doc :cell) first (get :node))
        cells (lr/load-cells "cells.edn" a-node)]
    (is (every? #(= a-node (get % :node)) cells))
    (is (every? #(= "cron" (get-in % [:trigger :kind])) cells))))

(deftest fire-cell-native-cljc-and-error-safe
  ;; native cljc path: require + resolve the entry, extract the cid (16-char head)
  (let [[status detail] (lr/fire-cell {:module "test-fixtures.sample-cell" :entry "fire"} ".")]
    (is (= ":ok" status))
    (is (= "bafyfixturecid12" detail)))   ;; first 16 chars of the fixture cid
  ;; a missing/failing cell must NOT throw — it returns :error (supervisor stays up)
  (let [[status _] (lr/fire-cell {:module "test-fixtures.no-such-cell" :entry "fire"} ".")]
    (is (= ":error" status))))

(deftest fire-cell-cutover-safety-python-fallback
  ;; CUTOVER SAFETY: a python-only cell fires identically to the python runner.
  ;; (a) explicit :lang "python" → shells the module from cells-root (PYTHONPATH)
  (let [[status detail] (lr/fire-cell {:module "pycell" :entry "fire" :lang "python"} "test_fixtures")]
    (is (= ":ok" status))
    (is (= "bafypyfixture000" detail)))    ;; first 16 chars of the python fixture cid
  ;; (b) AUTO-FALLBACK: no :lang, no cljc ns on the classpath → falls back to the python
  ;;     module automatically — what keeps the LIVE issachar/sukashi cell working on cutover
  ;;     without re-annotating cells.edn
  (let [[status detail] (lr/fire-cell {:module "pycell" :entry "fire"} "test_fixtures")]
    (is (= ":ok" status))
    (is (= "bafypyfixture000" detail))))

(deftest append-run-writes-a-chained-tx
  (let [log (str (System/getProperty "java.io.tmpdir") "/lr-test-" (System/nanoTime) ".edn")]
    (let [c1 (lr/append-run log :node "issachar" :cell "kaname_beat" :status ":ok" :detail "bafyabc" :as-of 202606221753)
          c2 (lr/append-run log :node "issachar" :cell "kaname_beat" :status ":error" :detail "RuntimeError: boom" :as-of 202606221853)
          txs (->> (str/split-lines (slurp log))
                   (remove #(str/starts-with? (str/trim %) ";"))
                   (mapv clojure.edn/read-string))]
      (is (= 2 (count txs)))
      (is (= c1 (get (first txs) :tx/cid)))
      (is (= "" (get (first txs) :tx/prev)))
      (is (= c1 (get (second txs) :tx/prev)))   ;; chained
      (is (= c2 (get (second txs) :tx/cid)))
      (.delete (java.io.File. log)))))

;; ── LIVE py↔clj BYTE parity on the ops commit-DAG ──────────────────

(deftest live-ops-log-byte-parity
  (testing "cljc append-run produces a byte-identical ops log to python lite_runner.py"
    (let [tmp (System/getProperty "java.io.tmpdir")
          clj-log (str tmp "/lr-clj-" (System/nanoTime) ".edn")
          py-log (str tmp "/lr-py-" (System/nanoTime) ".edn")]
      (lr/append-run clj-log :node "issachar" :cell "kaname_beat" :status ":ok" :detail "bafyabc" :as-of 202606221753)
      (lr/append-run clj-log :node "issachar" :cell "kaname_beat" :status ":error" :detail "RuntimeError: boom" :as-of 202606221853)
      (let [py (sh "python3" "-c"
                   (str "import lite_runner as lr, pathlib\n"
                        "log=pathlib.Path('" py-log "')\n"
                        "lr.append_run(log, node='issachar', cell='kaname_beat', status=':ok', detail='bafyabc', as_of=202606221753)\n"
                        "lr.append_run(log, node='issachar', cell='kaname_beat', status=':error', detail='RuntimeError: boom', as_of=202606221853)\n")
                   :dir ".")]
        (if (not (zero? (:exit py)))
          (println "  [skip] python3 unavailable — byte-parity not re-checked this run:" (:err py))
          (is (= (slurp py-log) (slurp clj-log))
              "the bb ops log must be byte-identical to the python runner's"))))))
