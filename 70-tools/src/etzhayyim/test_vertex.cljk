;; etzhayyim.test-vertex — vertex tier-registry pure invariants (cljc port; IO-free).
;; Run via the aggregate: bb test:helpers
;; Covers parse-tier-registry (TOML content → tier map) · lookup-tier ·
;; tier-tables · tier-stats.
(ns etzhayyim.test-vertex
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.vertex :as v]))

;; A representative deps.toml fragment: 3 vertex_tier sections + an interleaved
;; unrelated section (must reset tier context) + a stray table outside any tier.
(def toml
  (str "[vertex_tier.tier_a]\n"
       "tables = [\n"
       "  \"vertex_beta\",\n"     ;; out of order on purpose — parser sorts
       "  \"vertex_alpha\",\n"
       "]\n"
       "\n"
       "[other.section]\n"        ;; non-vertex section → exits tier context
       "x = 1\n"
       "\"vertex_orphan\"\n"      ;; not inside a tier → never classified
       "\n"
       "[vertex_tier.tier_b]\n"
       "tables = [\n"
       "  \"vertex_gamma\",\n"
       "]\n"
       "\n"
       "[vertex_tier.tier_c]\n"
       "tables = [\n"
       "  \"vertex_delta\",\n"
       "]\n"))

(def reg (v/parse-tier-registry toml))

(deftest parse-tier-registry-sections
  (testing "each tier collects its tables, sorted"
    (is (= ["vertex_alpha" "vertex_beta"] (vec (:a reg))))
    (is (= ["vertex_gamma"] (vec (:b reg))))
    (is (= ["vertex_delta"] (vec (:c reg)))))
  (testing "index maps each table to its tier keyword"
    (is (= {"vertex_alpha" :A "vertex_beta" :A "vertex_gamma" :B "vertex_delta" :C}
           (:index reg))))
  (testing "a table outside any vertex_tier section is not classified"
    (is (nil? (get (:index reg) "vertex_orphan")))))

(deftest lookup-tier-by-name
  (is (= :A (v/lookup-tier reg "vertex_alpha")))
  (is (= :C (v/lookup-tier reg "vertex_delta")))
  (is (nil? (v/lookup-tier reg "vertex_nonexistent"))))

(deftest tier-tables-by-keyword
  (is (= ["vertex_alpha" "vertex_beta"] (vec (v/tier-tables reg :A))))
  (is (= ["vertex_gamma"] (vec (v/tier-tables reg :B))))
  (is (nil? (v/tier-tables reg :Z))))

(deftest tier-stats-counts
  (is (= {:tier-a 2 :tier-b 1 :tier-c 1 :total 4} (v/tier-stats reg))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-vertex)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
