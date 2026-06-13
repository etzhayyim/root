(ns ake.methods.test-analyze
  "test_analyze.cljc — 朱 (ake) end-to-end membrane (propose → triage → route → revision).
  1:1 Clojure port of `methods/test_analyze.py` (clojure.test). Every Python assertion ported.
  `run` is pure over a parsed seed; the file edge (`load-edn`) is #?(:clj). The report is
  exercised via `report` (byte-identical to analyze.py's _report)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [ake.methods.analyze :as a]
            [ake.methods.contributor :as contrib]
            [ake.methods.revision :as rev]
            #?(:clj [ake.methods._edn :as edn])))

#?(:clj
   (def ^:private seed-path
     "20-actors/ake/data/seed-edit-graph.kotoba.edn"))

#?(:clj
   (defn- run* [] (a/run (edn/load-edn seed-path))))

#?(:clj
   (defn- by-id [res]
     (into {} (map (fn [r] [(get r "edit") r]) (get res "rows")))))

#?(:clj
   (deftest test-run-routes-every-seed-edit
     (let [m (by-id (run*))]
       (is (= #{"e1" "e2" "e3" "e4" "e5"} (set (keys m)))))))

#?(:clj
   (deftest test-optimistic-and-voted-edits-are-accepted
     (let [m (by-id (run*))]
       (is (and (= ":auto-accept" (get-in m ["e1" "route"])) (get-in m ["e1" "accepted"])))
       (is (and (= ":vote" (get-in m ["e2" "route"])) (get-in m ["e2" "accepted"])))   ;; 8-1
       (is (and (= ":vote" (get-in m ["e3" "route"])) (get-in m ["e3" "accepted"]))))))  ;; 5-0

#?(:clj
   (deftest test-invariant-and-rider-edits-are-not-accepted
     (let [m (by-id (run*))]
       (is (and (= ":council-lv7" (get-in m ["e4" "route"])) (not (get-in m ["e4" "accepted"]))))
       (is (and (= ":refused" (get-in m ["e5" "route"])) (not (get-in m ["e5" "accepted"])))))))

#?(:clj
   (deftest test-accepted-edits-landed-in-revision-history
     (let [res (run*)
           h (get res "history")]
       ;; e1 (tsmc hq-address) and e2 (example-listed status) accepted → present as current
       (is (some? (rev/current h "org.corp.tsmc" "hq-address")))
       (is (some? (rev/current h "org.corp.example-listed" "status")))
       ;; e4 (license, council-pending) and e5 (refused) did NOT land
       (is (nil? (rev/current h "org.corp.example-listed" "license"))))))

#?(:clj
   (deftest test-contributor-trajectory-recorded
     (let [res (run*)
           traj (get res "trajectory")]
       ;; the rider-violating author (esau) is recorded as refused, not accepted
       (let [esau "did:web:etzhayyim.com:member:esau"
             c (contrib/counts traj esau)]
         (is (and (= 0 (get c "accepted")) (>= (get c "refused") 1))))
       ;; the council-pending author (dan) has no decided event yet (pending ≠ refused)
       (let [dan "did:web:etzhayyim.com:member:dan"]
         (is (= {"accepted" 0 "refused" 0} (contrib/counts traj dan)))))))

#?(:clj
   (deftest test-report-renders
     (let [md (a/report (run*))]
       (is (str/includes? md "community-edit membrane dry-run"))
       (is (str/includes? md "Revision history")))))

#?(:clj (defn -main [& _] (run-tests 'ake.methods.test-analyze)))
