#!/usr/bin/env bb
;; ugachi 穿ち — seed loader + classifier (clj-native, pure stdlib).
(ns ugachi.methods.ugachi-edn
  "ugachi 穿ち — load + classify the extraction-project seed substrate.
  Reads the actor's own EDN substrate (kotoba/seed.edn) into Clojure data and
  splits by :type. Dependency-free (clojure.edn stdlib; file I/O :clj-only).
  Sibling of the busshi/kakaku/kabuto *_edn loaders. ADR-2606161800."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)]
       (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:projects [...]}."
  [rows]
  {:projects (vec (filter #(= (:type %) :project) rows))})

(defn projects
  "Convenience: load a seed file and return just the project rows (:clj only)."
  [path]
  #?(:clj (:projects (classify (load-edn path)))
     :default (throw (ex-info "projects: file load is :clj-only" {}))))
