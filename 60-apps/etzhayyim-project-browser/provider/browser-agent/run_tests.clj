;; run_tests.clj — repo rule: tests run via clj/bb, not .sh.
;;   bb run_tests.clj      (or: bb test)
(require '[clojure.test :as t]
         'etzhayyim.browser-agent.core-test)

(let [{:keys [fail error]} (t/run-tests 'etzhayyim.browser-agent.core-test)]
  (System/exit (if (pos? (+ (or fail 0) (or error 0))) 1 0)))
