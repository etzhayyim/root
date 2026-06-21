#!/usr/bin/env bb
;; 澪 mio — seed loader + classifier (clj-native, pure stdlib).
(ns mio.methods.mio-edn
  "澪 mio — load + classify the flow-improvement CLAIM seed substrate.

  Reads the actor's own EDN substrate (kotoba/seed.edn) into Clojure data with
  real keyword keys, and splits it by :type. Dependency-free (clojure.edn is
  stdlib; file I/O is :clj-only). Sibling of the busshi/kabuto *_edn loaders —
  each actor reads its own substrate. Energy Order Protocol backbone."
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
  "Split the flat seed vector by :type. Returns {:claims [...]}."
  [rows]
  {:claims (vec (filter #(= (:type %) :claim) rows))})

(defn claims
  "Convenience: load a seed file and return just the claim rows (:clj only)."
  [path]
  #?(:clj (:claims (classify (load-edn path)))
     :default (throw (ex-info "claims: file load is :clj-only" {}))))
