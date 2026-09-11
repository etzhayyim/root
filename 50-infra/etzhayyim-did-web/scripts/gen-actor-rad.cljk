#!/usr/bin/env nbb
(ns gen-actor-rad
  (:require [clojure.edn :as edn]
            [clojure.string :as str]))

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
(defn- __json-gen [x & [opts]]
  (js/JSON.stringify (clj->js x) nil (when (:pretty opts) 2)))
;; gen-actor-rad.nbb — distill the kotoba-rad identity ledger
;; (80-data/kotoba-rad/<handle>.identity.journal.edn, the per-actor sovereign
;; identity per ADR-2606231200) into a same-origin JSON the /murakumo page joins
;; by handle to link each actor to its GitHub repo, RAD did:web identity, and the
;; kotoba-rad ledger file. Generated artifact: public/_shell/actor-rad.json
;; (committed; re-run after the ledger changes). Operational code = clj/nbb over
;; the kotoba Datom log (etzhayyim/root repo convention).

(defn- path [& xs] (.apply (.-resolve __path) __path (to-array xs)))
(defn- exists? [p] (.existsSync __fs p))
(defn- directory? [p] (and (exists? p) (.isDirectory (.statSync __fs p))))
(defn- list-dir [p]
  (map #(path p %) (js->clj (.readdirSync __fs p))))
(defn- file-name [p] (.basename __path p))
(defn- read-text [p] (.readFileSync __fs p "utf8"))
(defn- write-text [p content] (.writeFileSync __fs p content "utf8"))

(def ^:private script-dir  (.dirname __path (.resolve __path *file*)))
(def ^:private ledger-dir  (path script-dir ".." ".." ".." "80-data" "kotoba-rad"))
(def ^:private actors-dir
  (path (or (aget (.-env js/process) "ETZHAYYIM_WEST_ACTORS_DIR")
            (path script-dir ".." ".." ".." ".."))))
(def ^:private out-file    (path script-dir ".." "public" "_shell" "actor-rad.json"))

(defn- west-dirs []
  ;; Handles with a flat west checkout under orgs/etzhayyim.
  (when (exists? actors-dir)
    (->> (list-dir actors-dir)
         (filter directory?)
         (map file-name)
         (filter #(str/starts-with? % "com-etzhayyim-"))
         (map #(subs % (count "com-etzhayyim-")))
         sort vec)))

(defn- parse-ledger [f]
  (let [rows (->> (str/split-lines (read-text f))
                  (remove str/blank?)
                  (keep #(try (edn/read-string %) (catch :default _ nil))))
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

(let [ledgers (->> (list-dir ledger-dir)
                   (filter #(str/ends-with? % ".identity.journal.edn")))
      result (into (sorted-map) (keep parse-ledger ledgers))]
  (.mkdirSync __fs (.dirname __path out-file) #js {:recursive true})
  (let [west (west-dirs)]
    (write-text out-file
                (str (__json-gen {:generatedFrom "80-data/kotoba-rad/*.identity.journal.edn + flat west orgs/etzhayyim/"
                                  :note "Per-actor kotoba-rad identity (ADR-2606231200). Keyed by handle. repo = :rad/repo, didWeb = github.io :rad/did-web, rid = :rad/rid. monorepoDirs is a wire-compatible field containing flat west checkout handles."
                                  :count (count result)
                                  :monorepoDirs west
                                  :actors result}
                                 {:pretty true})
                     "\n"))
    (println "wrote" out-file "—" (count result) "rad actors,"
             (count west) "flat west dirs")))
