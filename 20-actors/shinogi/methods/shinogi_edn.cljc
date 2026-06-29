#!/usr/bin/env bb
;; shinogi 鎬 — exam-involution seed loader + classifier (clj-native, pure stdlib).
(ns shinogi.methods.shinogi-edn
  "shinogi 鎬 — load + classify the exam-competition involution driver substrate.
  Reads the actor's own EDN substrate (kotoba/seed.exam-involution.edn) into
  Clojure data and splits by :type. Dependency-free (clojure.edn stdlib; file I/O
  :clj-only). Sibling of the junkan/ugachi/busshi *_edn loaders. ADR-2606291200."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)]
       (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:drivers [...]}."
  [rows]
  {:drivers (vec (filter #(= (:type %) :driver) rows))})

(defn drivers
  "Convenience: load a seed file and return just the driver rows (:clj only)."
  [path]
  #?(:clj (:drivers (classify (load-edn path)))
     :default (throw (ex-info "drivers: file load is :clj-only" {}))))
