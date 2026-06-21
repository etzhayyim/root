#!/usr/bin/env bb
;; kafun 花粉 — seed loader + classifier (clj-native, pure stdlib).
(ns kafun.methods.kafun-edn
  "kafun 花粉 — load + classify the forest-stand seed substrate.
  Reads the actor's own EDN substrate (kotoba/seed.edn) into Clojure data and
  splits by :type. Dependency-free (clojure.edn stdlib; file I/O :clj-only).
  Sibling of the ugachi/busshi/kakaku *_edn loaders. ADR-2606211712."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)]
       (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:stands [...]}."
  [rows]
  {:stands (vec (filter #(= (:type %) :stand) rows))})

(defn stands
  "Convenience: load a seed file and return just the stand rows (:clj only)."
  [path]
  #?(:clj (:stands (classify (load-edn path)))
     :default (throw (ex-info "stands: file load is :clj-only" {}))))
