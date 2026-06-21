#!/usr/bin/env bb
;; 委 yudane — seed loader + classifier (clj-native, pure stdlib).
(ns yudane.methods.yudane-edn
  "委 yudane — load + classify the consented-intention seed substrate.
  Sibling of the mio/tawami *_edn loaders. Energy Order Protocol."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)] (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:offers [...]}."
  [rows]
  {:offers (vec (filter #(= (:type %) :offer) rows))})

(defn offers [path]
  #?(:clj (:offers (classify (load-edn path)))
     :default (throw (ex-info "offers: file load is :clj-only" {}))))
