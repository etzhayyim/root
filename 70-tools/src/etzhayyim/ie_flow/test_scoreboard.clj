;; ie-flow SoS scoreboard integration test. ADR-2606212200.
;; Run from repo root (needs the actor adapters on the classpath):
;;   bb -cp "20-actors:70-tools/src:orgs/kotoba-lang/kotodama/src" \
;;      70-tools/src/etzhayyim/ie_flow/test_scoreboard.clj
(require '[clojure.test :as t :refer [deftest is run-tests]]
         '[clojure.string :as str]
         '[clojure.set]
         '[etzhayyim.ie-flow.scoreboard :as sb])

;; a fixture snapshot (render-md is pure over this shape — no actor deps needed)
(def fixture
  {:scored [{:actor "alpha" :score 0.52 :throughput 100.0 :vetoed? false
             :components {:rectify 0.6 :eta 0.5 :phi 0.7 :efficiency 0.5 :surprise 0.0}}
            {:actor "beta" :score 0.0 :throughput 5.0 :vetoed? true
             :components {:rectify 0.0 :eta 0.1 :phi 0.2 :efficiency 0.3 :surprise 1.0}}]
   :colony {:colony-reward 5.2 :colony-order 5 :n 2 :scored-n 1 :vetoed-n 1 :mean-score 0.26}
   :organism {:intake-without-colony 14 :intake-with-colony 29 :delta 15
              :env-source {:colony-order 5}}})

(deftest render-md-is-human-readable
  (let [md (sb/render-md fixture)]
    (is (str/includes? md "# ie-flow SoS scoreboard"))
    (is (str/includes? md "| actor |") "has the ranked table")
    (is (str/includes? md "alpha"))
    (is (str/includes? md "beta ⚠") "a vetoed actor is flagged")
    (is (str/includes? md "14 → 29") "shows the organism-reward intake delta")
    (is (str/includes? md "colony-order **5**"))
    (is (not (str/includes? md "http")) "self-contained, no external links")))

(deftest build-produces-a-real-scoreboard
  (let [snap (sb/build)]
    (is (>= (count (:scored snap)) 3) "available local and external flow contracts score")
    (is (every? #(contains? % :score) (:scored snap)))
    (is (pos? (get-in snap [:colony :colony-reward])) "the colony returns positive order")
    (is (pos? (get-in snap [:organism :delta])) "the colony feeds the organism (intake rises)")
    (is (= (get-in snap [:organism :delta])
           (- (get-in snap [:organism :intake-with-colony])
              (get-in snap [:organism :intake-without-colony])))
        "delta = intake-with − intake-without (the reward integration)")))

(deftest render-md-on-the-live-build
  ;; the real report renders without error and reflects the live actor count
  (let [md (sb/render-md (sb/build))]
    (is (str/includes? md "actors with measured flow"))
    (is (str/includes? md "Organism reward"))))

(deftest pending-adopters-are-honest
  ;; adopted-but-unscored actors are surfaced (honest coverage), and they are DISJOINT
  ;; from the scored set (an actor is never both).
  (let [snap (sb/build)
        scored (set (map :actor (:scored snap)))
        pending (set (map :actor (:pending snap)))]
    (is (vector? (:pending snap)))
    (is (every? :actor (:pending snap)))
    (is (empty? (clojure.set/intersection scored pending))
        "no actor is both scored and pending")
    (is (every? #(contains? scored %) ["kafun" "kaname" "tsumugi"])
        "the live adapters score")
    ;; ibuki is the organism itself (recipient of colony-order), so it stays pending by design
    (is (contains? pending "ibuki") "the organism is not a colony member it scores (circular)")
    (let [md (sb/render-md snap)]
      (is (str/includes? md "pending an adapter") "report surfaces the pending adopters"))))

(let [{:keys [fail error]} (run-tests)]
  (when (pos? (+ (or fail 0) (or error 0))) (System/exit 1)))
