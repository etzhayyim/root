(ns akashi.adapters.official-api-ingest
  "Production ingest boundary for official public ad-transparency APIs.
  No scraping, login automation, or anti-bot bypass. Live calls require an
  operator-provided token and explicit source-policy approval."
  (:require [akashi.adapters.dry-run-fixtures :as dry-run]
            [akashi.adapters.edn-export :as export]
            [akashi.adapters.platform-ad-library-fixture-parser :as parser]
            [akashi.adapters.regulator-bulk-fixture-parser :as canon]
            [cheshire.core :as json]
            [clojure.string :as str]
            [etzhayyim.kotoba.cid :as cid]
            [babashka.http-client :as http]))

(def meta-source-policy-cid "cid:akashi:source-policy:meta-official-api-r1")
(def meta-method-note-cid "cid:akashi:method-note:meta-official-api-r1")
(def x-source-policy-cid "cid:akashi:source-policy:x-dsa-repository-api-r1")
(def x-method-note-cid "cid:akashi:method-note:x-dsa-repository-api-r1")
(def attesting-did "did:web:akashi.etzhayyim.com")

(def meta-fields
  ["id" "page_id" "page_name" "ad_snapshot_url" "ad_creative_bodies"
   "ad_delivery_start_time" "ad_delivery_stop_time" "publisher_platforms"
   "spend" "impressions" "currency" "delivery_by_region"])

(defn now [] (str (java.time.Instant/now)))

(defn env! [k]
  (or (System/getenv k)
      (throw (ex-info (str "missing required environment variable " k) {:env k}))))

(defn- sha256 [s]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")
        bs (.digest md (.getBytes ^String (str s) "UTF-8"))]
    (apply str (map #(format "%02x" (bit-and % 0xff)) bs))))

(defn- range-value [m]
  (when (map? m)
    (let [lower (or (get m "lower_bound") (get m "lower") (get m "min"))
          upper (or (get m "upper_bound") (get m "upper") (get m "max"))]
      (into {} (remove (comp nil? val)
                       {"min" lower
                        "max" upper
                        "currency" (get m "currency")
                        "sourceLabel" (or (get m "sourceLabel") (get m "source_label"))})))))

(defn- join-text [xs]
  (cond
    (string? xs) xs
    (sequential? xs) (str/join "\n\n" (remove str/blank? xs))
    :else nil))

(defn- status [ad]
  (if (str/blank? (str (get ad "ad_delivery_stop_time"))) "active" "inactive"))

(defn- domain [url]
  (try
    (str/lower-case (or (.getAuthority (java.net.URI. url)) ""))
    (catch Throwable _ "")))

(defn meta-response->platform-payload
  [response {:keys [captured-at source-url jurisdiction]
             :or {captured-at (now)
                  source-url "https://www.facebook.com/ads/library/api/"
                  jurisdiction "global"}}]
  (let [ads (or (get response "data") [])]
    {"capturedAt" captured-at
     "source" {"platform" "meta"
               "sourceFamily" "social-ad-library"
               "sourceUrl" source-url
               "jurisdiction" jurisdiction
               "accessMode" "official-api"
               "collectionStatus" "allowed"}
     "records" (mapv
                (fn [ad]
                  (let [snapshot-url (or (get ad "ad_snapshot_url")
                                         (str "https://www.facebook.com/ads/library/?id=" (get ad "id")))
                        creative-text (join-text (get ad "ad_creative_bodies"))
                        platforms (get ad "publisher_platforms")
                        region-summary (->> (get ad "delivery_by_region")
                                            (keep #(or (get % "region") (get % "country")))
                                            distinct
                                            vec)]
                    (into {}
                          (remove (comp nil? val)
                                  {"sourceRecordId" (get ad "id")
                                   "sourceUrl" snapshot-url
                                   "advertiser" (into {}
                                                      (remove (comp nil? val)
                                                              {"displayName" (get ad "page_name")
                                                               "platformAdvertiserId" (get ad "page_id")
                                                               "pageUrl" (when-let [page-id (get ad "page_id")]
                                                                           (str "https://www.facebook.com/" page-id))
                                                               "websiteDomain" (domain snapshot-url)
                                                               "jurisdiction" jurisdiction
                                                               "verifiedStatus" "not-disclosed"}))
                                   "landingUrl" snapshot-url
                                   "creativeText" creative-text
                                   "language" nil
                                   "disclosedCategory" "source-disclosed-ad-library"
                                   "sourceIssuePoliticalFlag" "source-not-disclosed"
                                   "startedAt" (get ad "ad_delivery_start_time")
                                   "endedAt" (get ad "ad_delivery_stop_time")
                                   "status" (status ad)
                                   "spendRange" (some-> (range-value (get ad "spend"))
                                                        (assoc "currency" (get ad "currency")))
                                   "impressionRange" (range-value (get ad "impressions"))
                                   "regionSummary" (if (seq region-summary) region-summary platforms)
                                   "targetingSummary" (when (seq platforms)
                                                        {"publisherPlatforms" platforms})}))))
                ads)}))

(defn parse-meta-response [response opts]
  (parser/parse-platform-ad-library-fixture
   (meta-response->platform-payload response opts)
   {:attesting-did attesting-did
    :source-policy-cid meta-source-policy-cid
    :method-note-cid meta-method-note-cid}))

(defn fetch-meta-ads
  "Fetch one official Meta Ad Library API page. Requires META_AD_LIBRARY_ACCESS_TOKEN."
  [{:keys [search-terms countries ad-type api-version limit http-fn]
    :or {countries ["US"]
         ad-type "POLITICAL_AND_ISSUE_ADS"
         api-version "v23.0"
         limit 25
         http-fn http/get}}]
  (let [token (env! "META_AD_LIBRARY_ACCESS_TOKEN")
        resp (http-fn (str "https://graph.facebook.com/" api-version "/ads_archive")
                      {:throw false
                       :as :string
                       :query-params {"access_token" token
                                      "search_terms" search-terms
                                      "ad_reached_countries" (json/generate-string countries)
                                      "ad_type" ad-type
                                      "fields" (str/join "," meta-fields)
                                      "limit" limit}})]
    (when-not (<= 200 (:status resp) 299)
      (throw (ex-info "Meta Ad Library API request failed"
                      {:status (:status resp) :body (:body resp)})))
    (json/parse-string (:body resp))))

(defn ingest-meta
  [opts]
  (let [records (parse-meta-response (fetch-meta-ads opts) opts)]
    (dry-run/validate-output records)
    records))

(defn x-create-export-request
  "Create an X DSA Ads Repository export request. Requires X_ADS_REPOSITORY_BEARER_TOKEN."
  [{:keys [user-id geo-location start-date end-date http-fn]
    :or {http-fn http/post}}]
  (let [token (env! "X_ADS_REPOSITORY_BEARER_TOKEN")
        body {"variables" {"user" user-id
                           "geoLocation" geo-location
                           "deliveryRange" {"start_date" start-date
                                            "end_date" end-date}}}
        resp (http-fn "https://api.twitter.com/graphql/e9OJa7fJKHtHftkNzcRkzw/CreateExportReportMutation"
                      {:throw false
                       :as :string
                       :headers {"authorization" (str "Bearer " token)
                                 "content-type" "application/json"}
                       :body (json/generate-string body)})]
    (when-not (<= 200 (:status resp) 299)
      (throw (ex-info "X Ads Repository export request failed"
                      {:status (:status resp) :body (:body resp)})))
    (json/parse-string (:body resp))))

(defn x-export-status
  "Check an X DSA Ads Repository export status. Requires X_ADS_REPOSITORY_BEARER_TOKEN."
  [{:keys [export-id http-fn]
    :or {http-fn http/get}}]
  (let [token (env! "X_ADS_REPOSITORY_BEARER_TOKEN")
        body {"query" "e9OJa7fJKHtHftkNzcRkzw"
              "variables" {"exportId" export-id}}
        resp (http-fn "https://api.twitter.com/graphql/0RTLTx4DunPS6rVj-1cLCg/GetExportReportStatusQuery"
                      {:throw false
                       :as :string
                       :headers {"authorization" (str "Bearer " token)
                                 "content-type" "application/json"}
                       :body (json/generate-string body)})]
    (when-not (<= 200 (:status resp) 299)
      (throw (ex-info "X Ads Repository export status failed"
                      {:status (:status resp) :body (:body resp)})))
    (json/parse-string (:body resp))))

(defn- csv-lines [s]
  (->> (str/split-lines s)
       (remove str/blank?)))

(defn- split-csv-line [line]
  (mapv #(str/replace % #"^\"|\"$" "")
        (str/split line #",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)" -1)))

(defn csv->maps [s]
  (let [[header & rows] (csv-lines s)
        cols (mapv #(str/replace (str/lower-case %) #"\s+" "_") (split-csv-line header))]
    (mapv #(zipmap cols (split-csv-line %)) rows)))

(defn x-csv->platform-payload
  [csv-text {:keys [captured-at source-url jurisdiction]
             :or {captured-at (now)
                  source-url "https://business.x.com/en/help/ads-policies/product-policies/ads-transparency"
                  jurisdiction "EU"}}]
  {"capturedAt" captured-at
   "source" {"platform" "x"
             "sourceFamily" "social-ad-library"
             "sourceUrl" source-url
             "jurisdiction" jurisdiction
             "accessMode" "official-api"
             "collectionStatus" "allowed"}
   "records" (mapv
              (fn [row]
                (let [id (or (get row "ad_id") (get row "id") (get row "tweet_id") (canon/sha256-json row))
                      source-url (or (get row "ad_url") (get row "url") source-url)
                      advertiser (or (get row "advertiser") (get row "advertiser_name") (get row "account"))]
                  {"sourceRecordId" id
                   "sourceUrl" source-url
                   "advertiser" {"displayName" advertiser
                                 "platformAdvertiserId" (or (get row "user_id") (get row "account_id"))
                                 "jurisdiction" jurisdiction
                                 "verifiedStatus" "not-disclosed"}
                   "landingUrl" source-url
                   "creativeText" (or (get row "ad_text") (get row "creative_text") (get row "text") "")
                   "disclosedCategory" "dsa-ad-repository"
                   "sourceIssuePoliticalFlag" "not-applicable"
                   "startedAt" (or (get row "start_date") (get row "delivery_start"))
                   "endedAt" (or (get row "end_date") (get row "delivery_end"))
                   "status" "unknown"
                   "regionSummary" [(or (get row "country") jurisdiction)]
                   "targetingSummary" row}))
              (csv->maps csv-text))})

(defn parse-x-csv [csv-text opts]
  (parser/parse-platform-ad-library-fixture
   (x-csv->platform-payload csv-text opts)
   {:attesting-did attesting-did
    :source-policy-cid x-source-policy-cid
    :method-note-cid x-method-note-cid}))

(defn- storage-manifest [artifact datomic records edn datomic-edn]
  {:akashi.storage/artifact artifact
   :akashi.storage/cidv1 (cid/cid edn)
   :akashi.storage/sha256 (sha256 edn)
   :akashi.storage/format "datomic-datascript-tx-edn"
   :akashi.storage/datomic {:path datomic
                            :cidv1 (cid/cid datomic-edn)
                            :sha256 (sha256 datomic-edn)
                            :format "datomic-schema-and-scalar-tx-edn"}
   :akashi.storage/records (reduce + 0 (map #(if (sequential? %) (count %) 1) (vals records)))
   :akashi.storage/git {:path artifact :status "materialized"}
   :akashi.storage/datalad {:path artifact :next "bb kotoba:annex save 20-actors/akashi/data/live"}
   :akashi.storage/kotoba-rad {:path artifact
                               :cidv1 (cid/cid edn)
                               :akashi.storage/identity-journal "80-data/kotoba-rad/akashi.identity.journal.edn"
                               :next "bb rad:add-holding akashi --apply"}})

(defn materialize-live!
  [records {:keys [out datomic manifest]
            :or {out "20-actors/akashi/data/live/akashi-platform-ad-library.live.tx.kotoba.edn"
                 datomic "20-actors/akashi/data/live/akashi-platform-ad-library.live.datomic.edn"
                 manifest "20-actors/akashi/data/live/akashi-platform-ad-library.live.storage-manifest.edn"}}]
  (let [edn (export/records-to-edn records)
        datomic-edn (export/records-to-datomic-edn records)
        payload (storage-manifest out datomic records edn datomic-edn)]
    (doseq [p [out datomic manifest]]
      (when-let [parent (.getParentFile (java.io.File. ^String p))]
        (.mkdirs parent)))
    (spit out edn)
    (spit datomic datomic-edn)
    (spit manifest (str (pr-str payload) "\n"))
    payload))

(defn- parse-args [args]
  (loop [xs args opts {}]
    (if-let [x (first xs)]
      (case x
        "--search-terms" (recur (nnext xs) (assoc opts :search-terms (second xs)))
        "--countries" (recur (nnext xs) (assoc opts :countries (str/split (second xs) #",")))
        "--ad-type" (recur (nnext xs) (assoc opts :ad-type (second xs)))
        "--limit" (recur (nnext xs) (assoc opts :limit (parse-long (second xs))))
        "--api-version" (recur (nnext xs) (assoc opts :api-version (second xs)))
        "--csv" (recur (nnext xs) (assoc opts :csv (second xs)))
        "--user-id" (recur (nnext xs) (assoc opts :user-id (second xs)))
        "--geo-location" (recur (nnext xs) (assoc opts :geo-location (second xs)))
        "--start-date" (recur (nnext xs) (assoc opts :start-date (second xs)))
        "--end-date" (recur (nnext xs) (assoc opts :end-date (second xs)))
        "--export-id" (recur (nnext xs) (assoc opts :export-id (second xs)))
        "--out" (recur (nnext xs) (assoc opts :out (second xs)))
        "--datomic" (recur (nnext xs) (assoc opts :datomic (second xs)))
        "--manifest" (recur (nnext xs) (assoc opts :manifest (second xs)))
        "--emit-edn" (recur (rest xs) (assoc opts :emit-edn true))
        "--emit-datomic" (recur (rest xs) (assoc opts :emit-datomic true))
        "--materialize" (recur (rest xs) (assoc opts :materialize true))
        (if (:op opts)
          (throw (ex-info (str "unknown argument " x) {:arg x}))
          (recur (rest xs) (assoc opts :op x))))
      opts)))

(defn -main [& args]
  (let [{:keys [op emit-edn emit-datomic materialize] :as opts} (parse-args args)
        result (case op
                 "meta" (ingest-meta opts)
                 "x-create-export" (x-create-export-request opts)
                 "x-status" (x-export-status opts)
                 "x-csv" (do
                           (when-not (:csv opts)
                             (throw (ex-info "--csv is required for x-csv" {})))
                           (let [records (parse-x-csv (slurp (:csv opts)) opts)]
                             (dry-run/validate-output records)
                             records))
                 (throw (ex-info "op required: meta | x-create-export | x-status | x-csv" {:op op})))]
    (cond
      (and (map? result) materialize) (println (pr-str (materialize-live! result opts)))
      (and (map? result) emit-datomic) (print (export/records-to-datomic-edn result))
      (and (map? result) emit-edn) (print (export/records-to-edn result))
      :else (println (if (map? result) (pr-str result) (json/generate-string result))))))
