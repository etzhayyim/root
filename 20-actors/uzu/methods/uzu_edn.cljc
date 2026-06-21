#!/usr/bin/env bb
;; uzu 渦 — seed loader + classifier (clj-native, pure stdlib).
(ns uzu.methods.uzu-edn
  "uzu 渦 — load + classify the seed substrate (ADR-2606211500).
  Reads the actor's own EDN substrate (kotoba/seed.edn) and splits by :type into the
  world tape, organism configs, measured flows, and circulation edges. Sibling of the
  ugachi/busshi *_edn loaders. Dependency-free (clojure.edn; file I/O :clj-only)."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)] (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type."
  [rows]
  {:tape (->> rows (filter #(= (:type %) :world-step)) (sort-by :step) vec)
   :organisms (vec (filter #(= (:type %) :organism) rows))
   :flows (vec (filter #(= (:type %) :flow) rows))
   :edges (vec (filter #(= (:type %) :circulation) rows))})

(defn tape
  "Convenience: load a seed file and return the ordered world tape (:clj only)."
  [path]
  #?(:clj (:tape (classify (load-edn path)))
     :default (throw (ex-info "tape: file load is :clj-only" {}))))

(defn organisms [path]
  #?(:clj (:organisms (classify (load-edn path)))
     :default (throw (ex-info "organisms: file load is :clj-only" {}))))

(defn flows [path]
  #?(:clj (:flows (classify (load-edn path)))
     :default (throw (ex-info "flows: file load is :clj-only" {}))))
