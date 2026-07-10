(ns akashi.adapters.edn-query
  "Small Datomic/DataScript-shaped query helper for akashi EDN tx-data.

  This intentionally operates over plain tx-data maps as emitted by
  adapters/edn_export.py. Production can transact the same maps into Datomic,
  DataScript, or kotoba; these helpers make the fixture artifact queryable
  without requiring a live DB."
  (:require [clojure.edn :as edn]))

(defn load-tx-data [path]
  (edn/read-string (slurp path)))

(defn entities
  "Return entity maps from a Datomic/DataScript tx-data vector. Vector ops are
  ignored because akashi's fixture exporter emits entity maps."
  [tx-data]
  (vec (filter map? tx-data)))

(defn by-family [db family]
  (filterv #(= family (:akashi.record/family %)) (entities db)))

(defn by-platform [db platform]
  (filterv #(= platform (:akashi.adDisclosureSnapshot/platform %))
           (by-family db "adDisclosureSnapshot")))

(defn advertiser-identities [db]
  (by-family db "advertiserIdentity"))

(defn advertiser-names [db]
  (->> (advertiser-identities db)
       (map :akashi.advertiserIdentity/display-name)
       (remove nil?)
       distinct
       sort
       vec))

(defn landing-domains [db]
  (->> (by-family db "landingEvidence")
       (map :akashi.landingEvidence/domain)
       (remove nil?)
       distinct
       sort
       vec))

(defn count-by-platform [db]
  (->> (by-family db "adDisclosureSnapshot")
       (map :akashi.adDisclosureSnapshot/platform)
       frequencies
       (into (sorted-map))))

(defn delivery-for-snapshot [db snapshot-cid]
  (filterv #(= snapshot-cid (:akashi.deliveryDisclosure/source-snapshot-cid %))
           (by-family db "deliveryDisclosure")))

(defn query
  "Tiny query facade for CLI/tests. Supported ops:
   {:op :platform :platform \"meta\"}
   {:op :advertisers}
   {:op :landing-domains}
   {:op :count-by-platform}"
  [db {:keys [op platform]}]
  (case op
    :platform (by-platform db platform)
    :advertisers (advertiser-names db)
    :landing-domains (landing-domains db)
    :count-by-platform (count-by-platform db)
    (throw (ex-info (str "unsupported akashi query op " op) {:op op}))))
