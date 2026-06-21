#!/usr/bin/env bb
;; 樋 toi — seed loader + classifier (clj-native, pure stdlib).
(ns toi.methods.toi-edn
  "樋 toi — load + classify the compute seed substrate into jobs + sites.
  Sibling of the mio/okibi *_edn loaders. Energy Order Protocol."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)] (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:jobs [...] :sites [...]}."
  [rows]
  {:jobs  (vec (filter #(= (:type %) :job) rows))
   :sites (vec (filter #(= (:type %) :site) rows))})

(defn jobs [path]
  #?(:clj (:jobs (classify (load-edn path)))
     :default (throw (ex-info "jobs: file load is :clj-only" {}))))

(defn sites [path]
  #?(:clj (:sites (classify (load-edn path)))
     :default (throw (ex-info "sites: file load is :clj-only" {}))))
