;; lg-hakken clj-port test runner (repo rule: run_tests.clj, NOT .sh).
;;
;;   bb run_tests.clj      (from 60-apps/etzhayyim-project-hakken/lg-clj/)
;;   bb test               (bb.edn task alias)
;;
;; Exits non-zero if any test fails or errors.
(require '[clojure.test :as t]
         'lg-hakken.edn-and-cid-test
         'lg-hakken.graph-test)

(let [{:keys [fail error]} (t/run-tests 'lg-hakken.edn-and-cid-test
                                        'lg-hakken.graph-test)]
  (when (pos? (+ (or fail 0) (or error 0)))
    (System/exit 1)))
