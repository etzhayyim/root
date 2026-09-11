(ns scripts.lint.test-verify-no-modal-labs-calls
  "Tests for the Modal-Labs CI grep gate (ADR-2605282000 N1).

  Exercises the PURE scan fns on synthetic strings — a clean string (no
  violation), each violating string (modal.com / api.modal.com / modal import
  shapes), and an allow-listed line (excluded after the violation regex, per
  the Python's allow-list-matched-after semantics) — and asserts the
  violation regex + allow-list exclusion exactly as the Python.

  An OUTPUT-PARITY test (#?(:clj)) shells out to BOTH the Python and the
  Clojure `-main` over the SAME synthetic fixture tree via babashka.process
  and asserts identical violation lines + exit code."
  (:require [clojure.string :as str]
            [clojure.test :refer [deftest is testing]]
            [scripts.lint.verify-no-modal-labs-calls :as v]
            #?(:clj [clojure.java.io :as io])
            #?(:clj [babashka.process :as p])))

;; ── pure scan: clean strings carry no violation ──────────────────

(deftest clean-string-has-no-violation
  (testing "ordinary source never trips the gate"
    (is (= [] (v/violation-matches "import os\nprint('hello')\n")))
    (is (false? (v/scan-text "x = 1\ny = os.path.join('a', 'b')\n")))
    ;; word-boundary anchors keep look-alikes off (Python comment 1:1)
    (is (false? (v/scan-text "promodal = True\nmodal_count = 3\namodal.com\n")))))

;; ── pure scan: every violating shape, match-string + line 1:1 ────

(deftest violating-strings-are-detected
  (testing "modal.com / api.modal.com URL"
    (is (= [{:line 1 :match "https://api.modal.com"}]
           (v/violation-matches "r = get('https://api.modal.com/x')")))
    (is (= [{:line 1 :match "http://modal.com"}]
           (v/violation-matches "url = 'http://modal.com'"))))
  (testing "bare api.modal.com"
    (is (= [{:line 1 :match "api.modal.com"}]
           (v/violation-matches "host = api.modal.com"))))
  (testing "modal.com/<path>"
    (is (= [{:line 1 :match "modal.com/apps/x"}]
           (v/violation-matches "open('modal.com/apps/x')"))))
  (testing "from modal import"
    (is (= [{:line 1 :match "from modal import"}]
           (v/violation-matches "from modal import App"))))
  (testing "import modal  (line-anchored via (?m)$)"
    (is (= [{:line 2 :match "import modal"}]
           (v/violation-matches "x = 1\nimport modal\ny = 2"))))
  (testing "import modal as"
    (is (= [{:line 1 :match "import modal as"}]
           (v/violation-matches "import modal as m"))))
  (testing "line number is 1-based across multiple lines (Python count('\\n')+1)"
    (is (= [{:line 3 :match "from modal import"}]
           (v/violation-matches "a\nb\nfrom modal import App\nc")))))

;; ── allow-list: matched AFTER the violation regex, so excluded ───

(deftest allow-listed-line-is-excluded-after-the-violation-regex
  (testing "the line DOES hit the violation regex"
    ;; prove the regex itself still matches the trademark line — exclusion is
    ;; the allow-list's job, layered after (Python docstring semantics).
    ;; (A bare `modal.com ` does NOT match — the regex needs `api.` or `/path`
    ;; or `http` — so the trademark notice must carry api.modal.com to be a
    ;; meaningful allow-list demonstration; verified vs the Python regex.)
    (is (some? (re-find v/violation-re
                        "# api.modal.com is a trademark of Modal Labs, Inc.")))
    (is (some? (re-find v/violation-re
                        "# see https://modal.com/docs — trademark of Modal Labs"))))
  (testing "but a trademark / ADR mention is allow-listed out of the findings"
    (is (v/allow-listed? "# api.modal.com is a trademark of Modal Labs, Inc."))
    (is (v/allow-listed? "# see ADR-2605282000: api.modal.com is forbidden"))
    (is (= [] (v/violation-matches
               "# api.modal.com is a trademark of Modal Labs, Inc.")))
    (is (= [] (v/violation-matches
               "# ADR-2605282000 mentions api.modal.com as forbidden"))))
  (testing "a REAL call on a non-trademark line is NOT allow-listed"
    (is (false? (v/allow-listed? "client = connect('https://api.modal.com')")))
    (is (= [{:line 1 :match "https://api.modal.com"}]
           (v/violation-matches "client = connect('https://api.modal.com')"))))
  (testing "mixed file: violation kept, trademark line dropped"
    (is (= [{:line 1 :match "import modal"}]
           (v/violation-matches
            (str "import modal\n"
                 "# api.modal.com is a trademark of Modal Labs, Inc."))))))

;; ── OUTPUT-PARITY: Python vs Clojure -main over the SAME tree ────

#?(:clj
   (defn- write-fixture!
     "Materialize a synthetic repo root with the guarded package tree +
     `files` (path-under-package → content). Returns the root dir path."
     [files]
     (let [root (str (System/getProperty "java.io.tmpdir")
                     "/modal-gate-parity-" (System/currentTimeMillis))
           pkg (io/file root v/package-root)]
       (.mkdirs pkg)
       (doseq [[rel content] files]
         (let [f (io/file pkg rel)]
           (.mkdirs (.getParentFile f))
           (spit f content)))
       root)))

#?(:clj
   (defn- run-python [root]
     (let [r (p/sh {:dir "." :continue true}
                   "python3"
                   "70-tools/scripts/lint/verify_no_modal_labs_calls.py"
                   "--root" root)]
       {:exit (:exit r) :out (:out r) :err (:err r)})))

#?(:clj
   (defn- run-clojure [root]
     (let [r (p/sh {:dir "." :continue true}
                   "bb" "-cp" "70-tools"
                   "-e" (str "(require 'scripts.lint.verify-no-modal-labs-calls)"
                             "(System/exit"
                             " ((resolve 'scripts.lint.verify-no-modal-labs-calls/run)"
                             "  [\"--root\" \"" root "\"]))"))]
       {:exit (:exit r) :out (:out r) :err (:err r)})))

#?(:clj
   (defn- violation-lines
     "Extract the `  <path>:<line>: <match>` violation report lines (which the
     Python prints to stderr) — normalized to <basename>:<line> so the two
     impls' path rendering (pr-str vs repr quoting) and absolute-prefix
     differences don't defeat the comparison."
     [s]
     (->> (str/split-lines (or s ""))
          (keep (fn [ln]
                  (when-let [[_ path line] (re-find #"^\s+(\S+?):(\d+):" ln)]
                    (str (last (str/split path #"/")) ":" line))))
          sort
          vec)))

#?(:clj
   (deftest output-parity-python-vs-clojure
     (testing "clean tree → both exit 0, no violation lines"
       (let [root (write-fixture! {"ok.py" "import os\nprint('clean')\n"})
             py (run-python root)
             cj (run-clojure root)]
         (is (= 0 (:exit py)) (str "python err: " (:err py)))
         (is (= 0 (:exit cj)) (str "clojure err: " (:err cj)))
         (is (= [] (violation-lines (:err py))))
         (is (= [] (violation-lines (:err cj))))))
     (testing "violating tree → both exit 1, identical violation lines"
       (let [root (write-fixture!
                   {"a.py" "import os\nimport modal\n"
                    "sub/b.py" "from modal import App\nx = api.modal.com\n"
                    "c.py" "client = get('https://api.modal.com/run')\n"})
             py (run-python root)
             cj (run-clojure root)]
         (is (= 1 (:exit py)) (str "python err: " (:err py)))
         (is (= 1 (:exit cj)) (str "clojure err: " (:err cj)))
         (is (= (violation-lines (:err py))
                (violation-lines (:err cj)))
             (str "PY=" (violation-lines (:err py))
                  " CJ=" (violation-lines (:err cj))))))))
