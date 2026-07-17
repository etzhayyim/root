#!/usr/bin/env nbb
;; --- nbb shims (auto, ADR-2607173000) ---------------------------------
(def ^:private __fs (js/require "node:fs"))
(def ^:private __path (js/require "node:path"))
(def ^:private __cp (js/require "node:child_process"))
(def ^:private __os (js/require "node:os"))
(def ^:private __crypto (js/require "node:crypto"))
(defn- __sh [& args]
  (let [opts (when (map? (last args)) (last args))
        cmd (if opts (butlast args) args)
        r (.spawnSync __cp (first cmd) (to-array (rest cmd))
                      (clj->js (merge {:encoding "utf8"} (when opts {:cwd (:dir opts)}))))]
    {:exit (or (.-status r) 1) :out (or (.-stdout r) "") :err (or (.-stderr r) "")}))
(defn- __shell [& args]
  (let [opts (when (map? (first args)) (first args))
        cmd (if opts (rest args) args)
        r (.spawnSync __cp (first cmd) (to-array (rest cmd))
                      (clj->js (merge {:stdio "inherit" :encoding "utf8"}
                                      (when opts {:cwd (:dir opts)}))))]
    (when-not (zero? (or (.-status r) 1))
      (throw (js/Error. (str "shell failed: " (pr-str cmd)))))
    {:exit (or (.-status r) 0) :out "" :err ""}))
;; -----------------------------------------------------------------------
(defn- __json-parse [s & _] (js->clj (js/JSON.parse s) :keywordize-keys true))
(defn- __json-gen [x & _] (js/JSON.stringify (clj->js x)))
;; gen-actor-rad.nbb — distill the kotoba-rad identity ledger
;; (80-data/kotoba-rad/<handle>.identity.journal.edn, the per-actor sovereign
;; identity per ADR-2606231200) into a same-origin JSON the /murakumo page joins
;; by handle to link each actor to its GitHub repo, RAD did:web identity, and the
;; kotoba-rad ledger file. Generated artifact: public/_shell/actor-rad.json
;; (committed; re-run after the ledger changes). Operational code = clj/nbb over
;; the kotoba Datom log (etzhayyim/root repo convention).
(ns gen-actor-rad
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
                        ))

(def ^:private script-dir  (fs/parent (fs/absolutize *file*)))
(def ^:private ledger-dir  (fs/path script-dir ".." ".." ".." "80-data" "kotoba-rad"))
(def ^:private actors-dir  (fs/path script-dir ".." ".." ".." "20-actors"))
(def ^:private out-file    (fs/path script-dir ".." "public" "_shell" "actor-rad.json"))

(defn- monorepo-dirs []
  ;; handles that have a public source dir at etzhayyim/root/20-actors/<handle>
  ;; (so /murakumo can point `gh` at the always-public monorepo, not a private
  ;; child repo). The root repo is public; the per-actor child repos may not be.
  (when (fs/exists? actors-dir)
    (->> (fs/list-dir actors-dir)
         (filter fs/directory?)
         (map (comp str fs/file-name))
         (remove #(str/starts-with? % "."))
         sort vec)))

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
  (let [monorepo (monorepo-dirs)]
    (spit (str out-file)
          (__json-gen {:generatedFrom "80-data/kotoba-rad/*.identity.journal.edn + 20-actors/"
                                 :note "Per-actor kotoba-rad identity (ADR-2606231200). Keyed by handle. repo = :rad/repo, didWeb = github.io :rad/did-web, rid = :rad/rid. monorepoDirs = handles with a public 20-actors/<handle> source dir."
                                 :count (count result)
                                 :monorepoDirs monorepo
                                 :actors result}
                                {:pretty true}))
    (println "wrote" (str (fs/canonicalize out-file)) "—" (count result) "rad actors,"
             (count monorepo) "monorepo dirs")))
