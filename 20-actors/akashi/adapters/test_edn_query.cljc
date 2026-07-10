(ns akashi.adapters.test-edn-query
  (:require [clojure.test :refer [deftest is]]
            [clojure.java.shell :as sh]
            [clojure.edn :as edn]
            [akashi.adapters.edn-query :as q]))

(defn- fixture-db []
  (let [{:keys [exit out err]} (sh/sh "python3" "20-actors/akashi/adapters/dry_run_fixtures.py" "--emit-edn")]
    (is (= 0 exit) err)
    (edn/read-string out)))

(defn- fixture-datomic-bundle []
  (let [{:keys [exit out err]} (sh/sh "python3" "20-actors/akashi/adapters/dry_run_fixtures.py" "--emit-datomic")]
    (is (= 0 exit) err)
    (edn/read-string out)))

(deftest test-query-platform-ad-library-edn
  (let [db (fixture-db)]
    (is (= 25 (count (q/entities db))))
    (is (= {"meta" 1 "multi-platform" 2 "x" 1} (q/count-by-platform db)))
    (is (= 1 (count (q/by-platform db "meta"))))
    (is (= 1 (count (q/by-platform db "x"))))
    (is (some #{"Example Public Interest Project"} (q/advertiser-names db)))
    (is (some #{"Example Launch Account"} (q/advertiser-names db)))
    (is (some #{"example.org"} (q/landing-domains db)))
    (is (some #{"launch.example"} (q/landing-domains db)))))

(deftest test-query-facade
  (let [db (fixture-db)]
    (is (= ["Example Civic Notice Sponsor" "Example Launch Account"
            "Example Public Interest Project" "Minimal Public Disclosure Sponsor"]
           (q/query db {:op :advertisers})))
    (is (= {"meta" 1 "multi-platform" 2 "x" 1}
           (q/query db {:op :count-by-platform})))
    (is (thrown? clojure.lang.ExceptionInfo
                 (q/query db {:op :unsupported})))))

(deftest test-datomic-bundle-import-shape-and-query
  (let [bundle (fixture-datomic-bundle)
        db (q/datomic-entities bundle)]
    (is (q/datomic-bundle-valid? bundle))
    (is (= 25 (count db)))
    (is (= {"meta" 1 "multi-platform" 2 "x" 1} (q/count-by-platform db)))
    (is (= 1 (count (q/by-platform db "meta"))))
    (is (some #{"Example Public Interest Project"} (q/advertiser-names db)))
    (is (some #{"launch.example"} (q/landing-domains db)))))
