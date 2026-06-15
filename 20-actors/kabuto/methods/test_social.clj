#!/usr/bin/env bb
;; Working Clojure port of methods/test_social.py.
(ns kabuto.methods.test-social
  "Tests for the kabuto 兜 social composer + Charter-Rider gate (methods/social.clj).

  Covers the Charter-Rider §2(a)-(h) deny-scan + the G2 framing invariant: every composed post
  is aggregate-first, public-facts-only, framed as resilience/accountability — never a target-list.

  Run:  bb --classpath 20-actors 20-actors/kabuto/methods/test_social.clj"
  (:require [kabuto.methods.kabuto-edn :as e]
            [kabuto.methods.social :as s]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- g []
  (e/classify (e/load-edn (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
                              (io/file "data" "seed-public-companies.kotoba.edn")))))

(deftest charter-rider-rejects-prohibited-content
  (is (false? (s/charter-rider-clean "where to cut the supply chain")))
  (is (false? (s/charter-rider-clean "weapon design for the foundry")))
  (is (false? (s/charter-rider-clean "buy adsense placement"))))

(deftest charter-rider-accepts-clean-resilience-text
  (is (true? (s/charter-rider-clean "Disclosed supply dependency — diversify to build resilience."))))

(deftest compose-posts-pass-the-rider-gate
  (let [gr (g)
        posts (s/compose (:companies gr) (:edges gr) "top jurisdictions US/JP/CN")]
    (is (seq posts) "expected composed posts")
    (doseq [[_ _ text] posts]
      (is (s/charter-rider-clean text) (str "composed post violates the Rider: " text)))))

(deftest compose-headline-is-not-a-target-list
  (let [gr (g)
        posts (s/compose (:companies gr) (:edges gr) "summary")
        headline (first (keep (fn [[_ kind t]] (when (= kind "intel-report") t)) posts))]
    (is (and headline (str/includes? headline "not a target-list")))))

(deftest compose-supply-edges-frame-diversification
  (let [gr (g)
        edge-posts (keep (fn [[_ kind t]] (when (= kind "supply-edge") t))
                         (s/compose (:companies gr) (:edges gr) ""))]
    (is (seq edge-posts))
    (doseq [t edge-posts]
      (is (or (str/includes? (str/lower-case t) "resilience")
              (str/includes? (str/lower-case t) "diversify"))))))

(deftest post-record-is-well-formed-atproto-post
  (let [rec (s/post-record "hello" ["en"])]
    (is (= (get rec "$type") "app.bsky.feed.post"))
    (is (<= (count (get rec "text")) 300))
    (is (str/ends-with? (get rec "createdAt") "Z"))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kabuto.methods.test-social)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
