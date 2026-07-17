#!/usr/bin/env nbb
;; --- nbb shims (auto, ADR-2607173000) ---------------------------------
(def ^:private __fs (js/require "node:fs"))
(def ^:private __path (js/require "node:path"))
(def ^:private __cp (js/require "node:child_process"))
(def ^:private __os (js/require "node:os"))
(def ^:private __crypto (js/require "node:crypto"))
(defn- __sh [& args]
  (let [opts (when (map? (last args)) (last args))
        cmd (if opts (butlast args) args)
        r (.spawnSync __cp (first cmd) (to-array (rest cmd))
                      (clj->js (merge {:encoding "utf8"} (when opts {:cwd (:dir opts)}))))]
    {:exit (or (.-status r) 1) :out (or (.-stdout r) "") :err (or (.-stderr r) "")}))
(defn- __shell [& args]
  (let [opts (when (map? (first args)) (first args))
        cmd (if opts (rest args) args)
        r (.spawnSync __cp (first cmd) (to-array (rest cmd))
                      (clj->js (merge {:stdio "inherit" :encoding "utf8"}
                                      (when opts {:cwd (:dir opts)}))))]
    (when-not (zero? (or (.-status r) 1))
      (throw (js/Error. (str "shell failed: " (pr-str cmd)))))
    {:exit (or (.-status r) 0) :out "" :err ""}))
;; -----------------------------------------------------------------------
;; junkan 循環 — bb-only test suite.
;; Shell runners are intentionally prohibited for this actor; invoke with:
;;   nbb 20-actors/junkan/run_tests.bb
(ns junkan.run-tests
  (:require [clojure.test :as t]))

(def namespaces
  '[junkan.methods.test-junkan-edn
    junkan.methods.test-analyze
    junkan.methods.test-kotoba
    junkan.methods.test-autorun
    junkan.methods.test-query
    junkan.methods.test-validate
    junkan.methods.test-scorecard
    junkan.methods.test-history
    junkan.methods.test-consumer-culture
    junkan.methods.test-waste-sanitation
    junkan.methods.test-country-region-actors
    junkan.methods.test-charter-gates])

(apply require namespaces)

(let [result (apply t/run-tests namespaces)]
  (.exit js/process (if (zero? (+ (:fail result) (:error result))) 0 1)))
