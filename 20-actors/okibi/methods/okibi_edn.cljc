#!/usr/bin/env bb
;; 燠 okibi — seed loader + classifier (clj-native, pure stdlib).
(ns okibi.methods.okibi-edn
  "燠 okibi — load + classify the thermal seed substrate into sources + sinks.
  Sibling of the mio/tawami *_edn loaders. Energy Order Protocol."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)] (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:sources [...] :sinks [...]}."
  [rows]
  {:sources (vec (filter #(= (:type %) :source) rows))
   :sinks   (vec (filter #(= (:type %) :sink) rows))})

(defn sources [path]
  #?(:clj (:sources (classify (load-edn path)))
     :default (throw (ex-info "sources: file load is :clj-only" {}))))

(defn sinks [path]
  #?(:clj (:sinks (classify (load-edn path)))
     :default (throw (ex-info "sinks: file load is :clj-only" {}))))
