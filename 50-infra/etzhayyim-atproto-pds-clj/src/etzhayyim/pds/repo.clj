(ns etzhayyim.pds.repo
  "Bridge: materialise an AT-Proto repo (MST → commit → CAR) from this PDS's
  first-party records via **app-aozora-repo**, on the kotoba blockstore — the
  `com.atproto.sync.*` federation egress (ADR-2606242330 P-wiring).

  no-server-key: the read endpoints REBUILD an UNSIGNED repo (the server holds no
  key). Signed commits are produced on member WRITE (app-aozora-repo
  `repo/commit-records!` with the member sign-fn), a separate flow."
  (:require [clojure.string :as str]
            [etzhayyim.pds.store :as pstore]
            [etzhayyim.aozora.repo.blockstore :as bs]
            [etzhayyim.aozora.repo.repo :as repo]
            [etzhayyim.aozora.repo.sync :as sync]))

(defn- all-records
  "Every record for `did` across its collections, as
  [{:collection :rkey :value}] for app-aozora-repo."
  [store did]
  (let [{:keys [collections]} (pstore/describe-repo store did)]
    (mapcat
     (fn [coll]
       (loop [cur nil acc []]
         (let [{:keys [records cursor]} (pstore/list-records store did coll 100 cur)
               acc (into acc (map (fn [r] {:collection coll
                                           :rkey (last (str/split (:uri r) #"/"))
                                           :value (:value r)})
                                  records))]
           (if cursor (recur cursor acc) acc))))
     collections)))

(defn build!
  "Build the repo (MST + UNSIGNED commit) for `did` from the PDS records into a
  fresh app-aozora-repo blockstore. Returns {:store :commit :rev}."
  [pds-store did]
  (let [recs (all-records pds-store did)
        bstore (bs/->mem-blockstore)
        rev (str "r" (count recs))   ;; deterministic read-snapshot rev (write rev = TID)
        res (repo/commit-records! bstore {:did did :rev rev :prev nil :sign-fn nil} recs)]
    {:store bstore :commit (:commit res) :rev rev}))

(defn get-repo-car
  "CARv1 of the whole repo for `did`."
  [pds-store did]
  (sync/get-repo (:store (build! pds-store did)) did))

(defn get-latest-commit
  "{:cid :rev} for the rebuilt repo head, or nil."
  [pds-store did]
  (let [{:keys [store]} (build! pds-store did)]
    (sync/get-latest-commit store did)))

(defn get-blocks-car
  "CARv1 of the requested `cids` from the rebuilt repo."
  [pds-store did cids]
  (sync/get-blocks (:store (build! pds-store did)) cids))
