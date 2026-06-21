(ns hirameki.methods.hirameki-edn
  "hirameki 閃き — seed loader + classifier for the public-patent KG-mirror substrate.

  clj-native, dependency-free (clojure.edn). Each actor reads its own substrate; sibling
  of busshi/kabuto/kanjō/tokigusuri loaders. The seed mixes two node kinds — :field (the
  concentration unit) and :patent (exemplar corpus rows) — so the loader classifies them
  apart. ADR-2606212200."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn parse-edn
  "Parse an EDN string (a top-level vector of node maps)."
  [text]
  (edn/read-string text))

(defn load-edn
  "Read an EDN seed file into Clojure data. :clj file I/O only."
  [path]
  #?(:clj (with-open [r (java.io.PushbackReader. (io/reader path))]
            (edn/read r))
     :cljs (throw (ex-info "load-edn is :clj-only" {:path path}))))

(defn classify
  "Split seed rows by :type into {:fields [...] :patents [...]}."
  [rows]
  {:fields  (vec (filter #(= (:type %) :field) rows))
   :patents (vec (filter #(= (:type %) :patent) rows))})

(defn fields
  "Convenience: load + return only the :field rows. :clj-only."
  [path]
  (:fields (classify (load-edn path))))

(defn patents
  "Convenience: load + return only the :patent rows. :clj-only."
  [path]
  (:patents (classify (load-edn path))))
