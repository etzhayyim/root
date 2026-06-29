#!/usr/bin/env bb
;; kanmon 関門 — seed loader + classifier (clj-native, pure stdlib).
(ns kanmon.methods.kanmon-edn
  "kanmon 関門 — load + classify the exam-system seed substrate.
  Reads the actor's own EDN substrate (kotoba/seed.edn) into Clojure data and
  splits by :type. Dependency-free (clojure.edn stdlib; file I/O :clj-only).
  Sibling of the kafun/busshi/ugachi *_edn loaders. ADR-2606291500."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn [text] (edn/read-string text))

#?(:clj
   (defn load-edn [path]
     (with-open [r (io/reader path)]
       (parse-edn (slurp r)))))

(defn classify
  "Split the flat seed vector by :type. Returns {:exams [...]}."
  [rows]
  {:exams (vec (filter #(= (:type %) :exam) rows))})

(defn exams
  "Convenience: load a seed file and return just the exam rows (:clj only)."
  [path]
  #?(:clj (:exams (classify (load-edn path)))
     :default (throw (ex-info "exams: file load is :clj-only" {}))))
