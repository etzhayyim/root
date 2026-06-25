;; etzhayyim.test-complex-stubs — complex_stubs pure-parser invariants (cljc port).
;; Run: bb test:complex-stubs
;; Covers the pure parsers (subprocess/httpx legs are IO-deferred):
;; parse-duration · date? · strip-jsonc-comments · parse-toml-array · parse-front-matter.
(ns etzhayyim.test-complex-stubs
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.complex-stubs :as cs]))

(deftest parse-duration-units-and-cap
  (is (= 30 (cs/parse-duration "30s")))
  (is (= 120 (cs/parse-duration "2m")))
  (is (= 45 (cs/parse-duration "45")))            ;; bare number = seconds
  (is (= 30 (cs/parse-duration "  30S  ")))       ;; trim + lower-case
  (testing "capped at 300 seconds"
    (is (= 300 (cs/parse-duration "1h")))
    (is (= 300 (cs/parse-duration "10m")))))

(deftest date?-strict-format
  (is (true? (cs/date? "2026-06-25")))
  (is (true? (cs/date? "2026-13-99")))            ;; format-only, not validity
  (is (false? (cs/date? "2026/06/25")))
  (is (false? (cs/date? "2026-6-25")))            ;; wrong length
  (is (false? (cs/date? "not-a-date!"))))

(deftest strip-jsonc-comments-respects-strings
  (testing "// line comments are removed"
    (is (= "{\"a\":1} " (cs/strip-jsonc-comments "{\"a\":1} // trailing"))))
  (testing "// inside a string literal is preserved"
    (is (= "{\"url\":\"http://x\"}" (cs/strip-jsonc-comments "{\"url\":\"http://x\"}"))))
  (testing "multi-line — only from // onward is removed (text before // is kept)"
    (is (= "{\n  \"a\":1 \n}" (cs/strip-jsonc-comments "{\n  \"a\":1 // c\n}")))))

(deftest parse-toml-array-simple
  (is (= ["a" "b" "c"] (cs/parse-toml-array "[\"a\", \"b\", \"c\"]")))
  (is (= ["x"] (cs/parse-toml-array "['x']")))
  (is (= [] (cs/parse-toml-array "[]")))
  (is (= [] (cs/parse-toml-array "not an array"))))

(deftest parse-front-matter-scalar-list-bool
  (testing "scalars (raw / quoted / bool) + list values"
    (let [{:keys [result error]}
          (cs/parse-front-matter "---\ntitle: \"Hello\"\nactive: true\ncount: 5\ntags:\n- a\n- b\n---\nbody")]
      (is (nil? error))
      (is (= "Hello" (get result "title")))
      (is (= true (get result "active")))
      (is (= "5" (get result "count")))
      (is (= ["a" "b"] (get result "tags")))))
  (testing "missing delimiters produce an error + empty result"
    (is (= "missing YAML front matter opening delimiter"
           (:error (cs/parse-front-matter "no front matter here"))))
    (is (re-find #"closing delimiter"
                 (:error (cs/parse-front-matter "---\ntitle: x\nbody (no close)"))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-complex-stubs)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
