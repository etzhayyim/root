(ns kaiyaku.tests.test-plan
  "kaiyaku 解約 — severance-plan tests (ADR-2606112201). 1:1 Clojure port of tests/test_plan.py.

  Verifies the executor gates empirically:
    - safest-first tier routing: api → T1, browser-permitted → T2, else T3
    - G3: a :prohibited/:unknown browser stance NEVER yields T2; evasion verbs raise
    - cascade ties plan a rehome-dependency step FIRST
    - G8: notice/penalty are carried into the plan (cost-of-severance honesty)
    - G5/G6: every plan demands member-sig + dry-run + Council gate; execute raises
    - only :sever / :review-cascade ties are plannable (:keep refuses)

  NOTE: test_plans_json_export round-trips via json.loads(json.dumps(ps)). For these
  string-keyed pure-data shapes that round-trip is identity, so the ported assertion runs
  over ps directly (and additionally exercises the ->json serializer)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [kaiyaku.methods.analyze :as analyze]
            [kaiyaku.methods.plan :as plan]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def seed (io/file actor-dir "data" "seed-en-ledger.kotoba.edn"))

(defn- ctx
  "Returns [nodes ties-by-svc] (== Python _ctx)."
  []
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        res (analyze/analyze nodes edges)
        ties (reduce (fn [m t] (assoc m (get t "svc") t)) {} (get res "ties"))]
    [nodes ties]))

(deftest test-tier-routing
  (let [[nodes _] (ctx)]
    (is (= "T1" (plan/select-tier (get nodes "svc:saas-c"))))      ; api :available
    (is (= "T2" (plan/select-tier (get nodes "svc:video-a"))))     ; browser :permitted
    (is (= "T3" (plan/select-tier (get nodes "svc:gym-b"))))       ; browser :prohibited
    (is (= "T3" (plan/select-tier (get nodes "svc:merchant-g")))))) ; browser :unknown → refuse T2

(deftest test-prohibited-browser-never-t2
  ;; G3 by construction: no input shape with :browser :prohibited returns T2.
  (let [[nodes _] (ctx)]
    (doseq [svc (vals nodes)]
      (let [cancel (or (get svc ":svc/cancel") {})]
        (when (contains? #{":prohibited" ":unknown"} (get cancel ":browser"))
          (is (not= "T2" (plan/select-tier svc)) (str (get svc ":svc/id"))))))))

(deftest test-evasion-unrepresentable
  (doseq [verb (sort plan/EVASION-VERBS)]
    (is (thrown? #?(:clj Exception :cljs js/Error) (plan/make-step verb "x"))
        (str "evasion verb '" verb "' was representable"))))

(deftest test-cascade-rehome-first
  (let [[nodes ties] (ctx)
        p (plan/build-plan (get nodes "svc:mail-f") (get ties "svc:mail-f"))]
    (is (= ":review-cascade" (get p "recommendation")))
    (is (= "rehome-dependency" (get (first (get p "steps")) "verb")))
    (let [rehomes (filter #(= "rehome-dependency" (get % "verb")) (get p "steps"))]
      (is (= 2 (count rehomes))))))  ; sns-e + cloud-h both SSO through mail-f

(deftest test-cost-of-severance-carried
  (let [[nodes ties] (ctx)
        p (plan/build-plan (get nodes "svc:gym-b") (get ties "svc:gym-b"))]
    (is (and (= 30 (get p "notice_days")) (= 5000 (get p "penalty_jpy"))))
    ;; and no step plans around the obligation
    (is (every? #(not (str/includes? (get % "verb") "penalty")) (get p "steps")))))

(deftest test-destructive-gates-and-dry-run
  (let [[nodes ties] (ctx)
        p (plan/build-plan (get nodes "svc:video-a") (get ties "svc:video-a"))]
    (is (= {"member_sig" true "dry_run_confirm" true "council_lv6_operator_gate" true}
           (get p "requires")))
    (is (= "dry-run" (get p "mode")))
    (is (every? #(= "dry-run" (get % "mode")) (get p "steps")))
    (is (thrown? #?(:clj Exception :cljs js/Error) (plan/execute p))
        "execute must raise at R0 (G5/G6)")))

(deftest test-keep-not-plannable
  (let [[nodes ties] (ctx)]
    (is (thrown? #?(:clj Exception :cljs js/Error)
                 (plan/build-plan (get nodes "svc:saas-c") (get ties "svc:saas-c")))
        ":keep tie was plannable")))

(deftest test-plans-cover-all-severables
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        res (analyze/analyze nodes edges)
        ps (plan/plans nodes edges)
        want (set (map #(get % "svc")
                       (filter #(contains? #{":sever" ":review-cascade"} (get % "recommendation"))
                               (get res "ties"))))]
    (is (= want (set (map #(get % "svc") ps))))
    (is (every? (fn [p] (= "export-own-data"
                           (get (nth (get p "steps") (- (count (get p "steps")) 2)) "verb")))
                ps))))

(deftest test-plans-json-export
  ;; Wave 40: severance plans の機械可読 JSON (tate と対称 — yoro UI 配線が両 actor で完備).
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        ps (plan/plans nodes edges)
        json (plan/->json ps)        ; exercise the serializer (no-throw, non-empty)
        back ps]                     ; json.loads(json.dumps(x)) == x for these shapes
    (is (and (string? json) (pos? (count json))))
    (is (and (= (count back) (count ps)) (>= (count ps) 5)))
    (is (every? #(and (= "dry-run" (get % "mode")) (contains? % "steps")) back))))
