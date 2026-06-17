(ns tatara.methods.test-crosscheck
  "tatara 鑪 — kabuto-linkage crosscheck tests (ADR-2606171800).

  Deterministic synthetic cases (no dependency on kabuto's evolving seed) + a real-seed coverage
  smoke that asserts structural invariants only (resolved + worklist == total; coverage =
  resolved/total; stable brand resolutions)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [tatara.methods.analyze :as az]
            [tatara.methods.crosscheck :as cc]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def plant-seed (io/file actor-dir "data" "seed-plant-graph.kotoba.edn"))
(def kab-seed (io/file (.getParentFile actor-dir) "kabuto" "data" "seed-public-companies.kotoba.edn"))

;; ── deterministic synthetic kabuto index ──
(def synth-companies
  [{:company/id "org.corp.tw.tsmc"      :company/name "Taiwan Semiconductor Manufacturing Co. (TSMC)"}
   {:company/id "org.corp.kr.sk-hynix"  :company/name "SK hynix"}
   {:company/id "org.corp.us.intel"     :company/name "Intel"}])

(deftest test-resolve-bridges-short-id-to-country-qualified-id
  (let [idx (cc/kabuto-index synth-companies)]
    (is (= "org.corp.tw.tsmc"     (cc/resolve-operator "org.corp.tsmc" idx)))
    (is (= "org.corp.kr.sk-hynix" (cc/resolve-operator "org.corp.skhynix" idx))) ;; hyphen-insensitive
    (is (= "org.corp.us.intel"    (cc/resolve-operator "org.corp.intel" idx)))
    (is (nil? (cc/resolve-operator "org.corp.nonexistentmaker" idx)))
    (is (nil? (cc/resolve-operator "org.corp.ab" idx)))))            ;; token < 3 chars → no match

(deftest test-crosscheck-structural-invariants
  (let [plants [{:plant/id "p1" :plant/operator "org.corp.tsmc"   :plant/name "Fab A"}
                {:plant/id "p2" :plant/operator "org.corp.tsmc"   :plant/name "Fab B"}
                {:plant/id "p3" :plant/operator "org.corp.ghostco" :plant/name "Ghost"}]
        r (cc/crosscheck plants synth-companies)]
    (is (= 2 (:total r)))                                  ;; 2 distinct operators
    (is (= 1 (:resolved r)))                               ;; only tsmc resolves
    (is (= 0.5 (:coverage r)))
    (is (= (:total r) (+ (:resolved r) (count (:worklist r)))))
    (is (= "org.corp.ghostco" (:operator (first (:worklist r)))))
    (is (= 2 (count (:plants (first (filter #(= "org.corp.tsmc" (:operator %)) (:rows r)))))))))

(deftest test-worklist-is-exactly-the-unresolved-rows
  (let [plants (filter :plant/id (az/load-edn plant-seed))
        companies (if (.exists kab-seed) (filter :company/id (az/load-edn kab-seed)) synth-companies)
        r (cc/crosscheck plants companies)]
    (is (= 25 (:total r)))                                 ;; 25 distinct operators in the seed
    (is (= (:total r) (+ (:resolved r) (count (:worklist r)))))
    (is (<= 0.0 (:coverage r) 1.0))
    ;; every worklist operator is genuinely unresolved in rows
    (let [unresolved (set (map :operator (remove :kabuto (:rows r))))]
      (is (= unresolved (set (map :operator (:worklist r))))))
    ;; stable high-confidence brand resolutions (robust to kabuto seed churn)
    (when (.exists kab-seed)
      (let [by-op (into {} (map (juxt :operator :kabuto) (:rows r)))]
        (is (str/includes? (str (get by-op "org.corp.tsmc")) "tsmc"))
        (is (str/includes? (str (get by-op "org.corp.intel")) "intel"))
        (is (str/includes? (str (get by-op "org.corp.boeing")) "boeing"))))))

(deftest test-report-renders
  (let [r (cc/crosscheck [{:plant/id "p1" :plant/operator "org.corp.tsmc" :plant/name "Fab A"}]
                         synth-companies)
        md (cc/render-report r)]
    (is (str/includes? md "kabuto-linkage crosscheck"))
    (is (str/includes? md "coverage"))))

#?(:clj
   (defn -main [& _]
     (let [{:keys [fail error]} (run-tests 'tatara.methods.test-crosscheck)]
       (System/exit (if (zero? (+ fail error)) 0 1)))))
