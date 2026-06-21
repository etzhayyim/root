#!/usr/bin/env bb
;; tsuchifumi 土踏み — seed loader + classifier (clj-native, pure stdlib).
(ns tsuchifumi.methods.tsuchifumi-edn
  "tsuchifumi 土踏み — load + classify the seed substrate (kotoba/seed.edn).
  Reads the actor's own EDN substrate into Clojure data and splits by :type into
  {:regions … :evidence … :drivers …}. Dependency-free (clojure.edn stdlib; file
  I/O :clj-only). Sibling of the kafun/ugachi/busshi *_edn loaders. ADR-2606212000."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)]
       (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:regions [...] :evidence [...] :drivers [...]}."
  [rows]
  {:regions  (vec (filter #(= (:type %) :region) rows))
   :evidence (vec (filter #(= (:type %) :evidence) rows))
   :drivers  (vec (filter #(= (:type %) :driver) rows))})

(defn load-seed
  "Load a seed file and return the classified map (:clj only)."
  [path]
  #?(:clj (classify (load-edn path))
     :default (throw (ex-info "load-seed: file load is :clj-only" {}))))
