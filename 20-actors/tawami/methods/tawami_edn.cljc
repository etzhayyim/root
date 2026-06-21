#!/usr/bin/env bb
;; 撓 tawami — seed loader + classifier (clj-native, pure stdlib).
(ns tawami.methods.tawami-edn
  "撓 tawami — load + classify the flexibility-asset seed substrate.
  Sibling of the mio/busshi *_edn loaders. Energy Order Protocol."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)] (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:assets [...]}."
  [rows]
  {:assets (vec (filter #(= (:type %) :asset) rows))})

(defn assets
  "Load a seed file and return just the asset rows (:clj only)."
  [path]
  #?(:clj (:assets (classify (load-edn path)))
     :default (throw (ex-info "assets: file load is :clj-only" {}))))
