;; run_tests.clj — lg-chat clj test runner (repo rule: .clj, not .sh).
;; Usage: from 60-apps/etzhayyim-chat-shell/lg/clj/ run `bb run test`
;;        or `bb tests/run_tests.clj`.
(require '[clojure.test :as t]
         'lg-chat.test-smoke
         'lg-chat.graphs.test-sodai-submit)

(let [{:keys [fail error] :as summary}
      (t/run-tests 'lg-chat.test-smoke
                   'lg-chat.graphs.test-sodai-submit)]
  (println summary)
  (System/exit (if (zero? (+ (or fail 0) (or error 0))) 0 1)))
