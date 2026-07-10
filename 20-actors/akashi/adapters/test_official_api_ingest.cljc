(ns akashi.adapters.test-official-api-ingest
  (:require [akashi.adapters.edn-export :as export]
            [akashi.adapters.official-api-ingest :as live]
            [akashi.adapters.edn-query :as q]
            [cheshire.core :as json]
            [clojure.test :refer [deftest is]]))

(def meta-response
  {"data" [{"id" "meta-live-1"
            "page_id" "12345"
            "page_name" "Example Public Page"
            "ad_snapshot_url" "https://www.facebook.com/ads/archive/render_ad/?id=meta-live-1"
            "ad_creative_bodies" ["Public transparency body"]
            "ad_delivery_start_time" "2026-07-01T00:00:00+0000"
            "publisher_platforms" ["facebook" "instagram"]
            "currency" "EUR"
            "spend" {"lower_bound" 100 "upper_bound" 499}
            "impressions" {"lower_bound" 1000 "upper_bound" 4999}
            "delivery_by_region" [{"region" "EU"}]}]})

(deftest meta-response-normalizes-to-akashi-records
  (let [records (live/parse-meta-response meta-response {:captured-at "2026-07-10T00:00:00Z"})
        tx (export/records-to-tx-data records)]
    (is (= 7 (count tx)))
    (is (= {"meta" 1} (q/count-by-platform tx)))
    (is (= ["Example Public Page"] (q/advertiser-names tx)))
    (is (= "official-api" (get-in records ["sourcePolicySnapshot" "accessMode"])))
    (is (= "allowed" (get-in records ["sourcePolicySnapshot" "collectionStatus"])))))

(deftest meta-fetch-requires-token
  (is (thrown-with-msg? clojure.lang.ExceptionInfo
                        #"META_AD_LIBRARY_ACCESS_TOKEN"
                        (live/fetch-meta-ads {:search-terms "example"
                                              :http-fn (fn [_ _] {:status 200 :body "{}"})}))))

(deftest x-csv-normalizes-to-akashi-records
  (let [csv "ad_id,advertiser,user_id,ad_url,ad_text,country,start_date,end_date\nx-1,Example X Advertiser,u1,https://ads.twitter.com/transparency/x-1,Body,DE,2026-07-01,2026-07-02\n"
        records (live/parse-x-csv csv {:captured-at "2026-07-10T00:00:00Z"})
        tx (export/records-to-tx-data records)]
    (is (= 7 (count tx)))
    (is (= {"x" 1} (q/count-by-platform tx)))
    (is (= ["Example X Advertiser"] (q/advertiser-names tx)))))

(deftest x-export-request-shape-is-official-api-only
  (let [calls (atom [])
        fake (fn [url opts]
               (swap! calls conj [url opts])
               {:status 200 :body (json/generate-string {"data" {"create" {"exportId" "e1"}}})})]
    (with-redefs [live/env! (fn [_] "token")]
      (is (= {"data" {"create" {"exportId" "e1"}}}
             (live/x-create-export-request {:user-id "123" :geo-location "DE"
                                            :start-date "2026-07-01" :end-date "2026-07-02"
                                            :http-fn fake}))))
    (is (= "https://api.twitter.com/graphql/e9OJa7fJKHtHftkNzcRkzw/CreateExportReportMutation"
           (ffirst @calls)))))
