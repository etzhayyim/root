#!/usr/bin/env bb
;; shinan 指南 — seed loader + classifier + OPEN-LICENSE guard (clj-native, pure stdlib).
(ns shinan.methods.shinan-edn
  "shinan 指南 — load + classify the topic/resource seed substrate.
  Reads the actor's own EDN substrate (kotoba/seed.edn) into Clojure data and splits
  by :type. ENFORCES the open-license invariant on load: a resource whose :license is
  not an OPEN license is structurally inadmissible (学習解放 — open commons only). This
  is the loader-level half of the charter guarantee; analyze re-checks. Dependency-free
  (clojure.edn stdlib; file I/O :clj-only). Sibling of the kanmon/kafun *_edn loaders.
  ADR-2606291501."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

;; OPEN licenses ONLY (mirror kotoba/ontology.shinan.edn :license enum).
(def open-licenses
  #{:public-domain :cc0 :cc-by :cc-by-sa :open-courseware :gov-open :free-access})

(defn open-license? [lic] (contains? open-licenses lic))

(defn validate-open!
  "Throw if any resource carries a non-open (proprietary/paid) license. 学習解放: the
   commons holds only openly-licensed material — proprietary cram content is refused."
  [resources]
  (doseq [r resources]
    (when-not (open-license? (:license r))
      (throw (ex-info "shinan: non-open license is unrepresentable (学習解放 — open commons only)"
                      {:resource (:id r) :license (:license r)}))))
  resources)

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)]
       (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type and ENFORCE the open-license invariant.
   Returns {:topics [...] :resources [...]}."
  [rows]
  (let [resources (vec (filter #(= (:type %) :resource) rows))]
    (validate-open! resources)
    {:topics    (vec (filter #(= (:type %) :topic) rows))
     :resources resources}))

(defn topics [path]
  #?(:clj (:topics (classify (load-edn path)))
     :default (throw (ex-info "topics: file load is :clj-only" {}))))

(defn resources [path]
  #?(:clj (:resources (classify (load-edn path)))
     :default (throw (ex-info "resources: file load is :clj-only" {}))))
