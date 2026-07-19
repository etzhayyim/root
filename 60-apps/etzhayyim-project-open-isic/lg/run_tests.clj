#!/usr/bin/env bb
;; lg-open-isic — bb-native test runner (clojure.test; no shell). ADR-2606280030.
;;
;; Per the repo-wide rule (root CLAUDE.md §"Operational code = clj/bb"): new
;; first-party tooling is clj/bb, NOT shell. This is the .clj runner the repo
;; rule mandates for ported actors/apps (replaces run_tests.sh).
;;
;;   bb run_tests.clj          ; from 60-apps/etzhayyim-project-open-isic/lg/
;;   bb test                   ; via the scoped bb.edn task
(ns lg-open-isic.host
  (:require [babashka.http-client :as http]
            [clojure.test :as t]
            [lg-open-isic.graphs.classify-entity :as classify]))

(defn- env [name default] (or (System/getenv name) default))

(def config {:url (env "VLLM_URL" (:url classify/default-config))
             :model (env "VLLM_MODEL" (:model classify/default-config))})

(defn classifier [subject hint]
  (classify/classify-with http/post config subject hint))

(defn with-capabilities [f]
  (binding [classify/*classify* classifier] (f)))

(def suites
  '[lg-open-isic.test-graphs
    lg-open-isic.test-server])

(apply require suites)

(let [{:keys [fail error]} (apply t/run-tests suites)]
  (if (zero? (+ fail error))
    (println "── lg-open-isic: ALL suites green ──")
    (do (println "── lg-open-isic: FAILURES above ──")
        (System/exit 1))))
