;; run_tests.clj — lg-chat clj-port test runner (repo rule: run_tests.clj, not .sh).
;; Usage: `bb run_tests.clj`  or  `bb test`  (from 60-apps/ai-gftd-chat-shell/lg/).
(require '[clojure.test :as t]
         'tests.test-smoke
         'tests.test-sodai-submit)

(let [{:keys [fail error] :as summary}
      (t/run-tests 'tests.test-smoke 'tests.test-sodai-submit)]
  (println "lg-chat clj-port:" (pr-str summary))
  (when (pos? (+ (or fail 0) (or error 0)))
    (System/exit 1)))
