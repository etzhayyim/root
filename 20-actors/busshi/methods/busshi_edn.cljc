#!/usr/bin/env bb
;; busshi 物資 — seed loader + classifier (clj-native, pure stdlib).
(ns busshi.methods.busshi-edn
  "busshi 物資 — load + classify the commodity/materials seed substrate.

  Reads the actor's own EDN substrate (kotoba/seed.edn) into Clojure data with
  real keyword keys, and splits it by :type. Dependency-free (clojure.edn is
  stdlib; file I/O is :clj-only). Sibling of the kabuto/kanjō/kasa/kakaku *_edn
  loaders — each actor reads its own substrate. ADR-2606161730."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn
  "Parse an EDN string (top-level vector of maps) into Clojure data."
  [text]
  (edn/read-string text))

#?(:clj
   (defn load-edn
     "Load + parse an EDN file from disk (:clj only)."
     [path]
     (with-open [r (io/reader path)]
       (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:commodities [...]}."
  [rows]
  {:commodities (vec (filter #(= (:type %) :commodity) rows))})

(defn commodities
  "Convenience: load a seed file and return just the commodity rows (:clj only)."
  [path]
  #?(:clj (:commodities (classify (load-edn path)))
     :default (throw (ex-info "commodities: file load is :clj-only" {}))))
