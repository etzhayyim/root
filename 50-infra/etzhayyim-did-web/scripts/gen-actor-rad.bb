#!/usr/bin/env bb
;; gen-actor-rad.bb — distill the kotoba-rad identity ledger
;; (80-data/kotoba-rad/<handle>.identity.journal.edn, the per-actor sovereign
;; identity per ADR-2606231200) into a same-origin JSON the /murakumo page joins
;; by handle to link each actor to its GitHub repo, RAD did:web identity, and the
;; kotoba-rad ledger file. Generated artifact: public/_shell/actor-rad.json
;; (committed; re-run after the ledger changes). Operational code = clj/bb over
;; the kotoba Datom log (etzhayyim/root repo convention).
(ns gen-actor-rad
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [babashka.fs :as fs]
            [cheshire.core :as json]))

(def ^:private script-dir (fs/parent (fs/absolutize *file*)))
(def ^:private ledger-dir (fs/path script-dir ".." ".." ".." "80-data" "kotoba-rad"))
(def ^:private out-file   (fs/path script-dir ".." "public" "_shell" "actor-rad.json"))

(defn- parse-ledger [f]
  (let [rows (->> (str/split-lines (slurp (str f)))
                  (remove str/blank?)
                  (keep #(try (edn/read-string %) (catch Exception _ nil))))
        find1 (fn [attr pred]
                (some (fn [[_e a v]] (when (and (= a attr) (or (nil? pred) (pred v))) v)) rows))
        nm      (find1 :rad/name nil)
        did-web (find1 :rad/did-web #(str/includes? (str %) "etzhayyim.github.io"))
        repo    (find1 :rad/repo nil)
        rid     (or (find1 :rad/rid nil)
                    (some (fn [[e a v]] (when (and (= a :rad/type) (= v :identity)) e)) rows))]
    (when nm
      [nm (cond-> {}
            repo    (assoc :repo repo)
            did-web (assoc :didWeb did-web)
            rid     (assoc :rid rid))])))

(let [result (into (sorted-map)
                   (keep parse-ledger (fs/glob ledger-dir "*.identity.journal.edn")))]
  (fs/create-dirs (fs/parent out-file))
  (spit (str out-file)
        (json/generate-string {:generatedFrom "80-data/kotoba-rad/*.identity.journal.edn"
                               :note "Per-actor kotoba-rad identity (ADR-2606231200). Keyed by handle. repo = :rad/repo, didWeb = github.io :rad/did-web, rid = :rad/rid."
                               :count (count result)
                               :actors result}
                              {:pretty true}))
  (println "wrote" (str (fs/canonicalize out-file)) "—" (count result) "actors"))
