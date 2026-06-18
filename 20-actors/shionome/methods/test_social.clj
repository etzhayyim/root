#!/usr/bin/env bb
;; test_social.clj — 潮目 (shionome) dry-run social post + no-trade body scan. ADR-2606072200.
(ns shionome.methods.test-social
  (:require [shionome.methods.social :as social]
            [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]))

(def ^:private _SRC ["https://fred.stlouisfed.org/" "https://www.ici.org/research"])

(def ^:private _NET
  [{"bucket" "us-equities"   "label" "US equities"   "net"  13.1 "inflow" 23.2 "outflow" 10.1}
   {"bucket" "us-govt-bonds" "label" "US Treasuries" "net" -21.7 "inflow"  0.0 "outflow" 21.7}])

(def ^:private _ROT
  [{"from" "us-govt-bonds" "from_label" "US Treasuries"
    "to"   "us-equities"  "to_label"   "US equities"
    "magnitude" 12.4}])

(def ^:private _REGIME
  {"regime" "risk-on" "risk_net" 27.3 "safe_net" -26.6 "no_trade_notice" true})

;; ── helpers ──────────────────────────────────────────────────────────────────

(defmacro expect-raises
  "Assert that body throws an exception whose message contains `contains-str`."
  [contains-str & body]
  `(let [caught# (try ~@body nil (catch Exception e# e#))]
     (is (some? caught#) "expected an exception, none raised")
     (when (seq ~contains-str)
       (is (str/includes? (ex-message caught#) ~contains-str)
           (str "raised but missing " (pr-str ~contains-str) ": " (ex-message caught#))))))

;; ── tests ────────────────────────────────────────────────────────────────────

(deftest test-netflow-post-pins-invariants
  (let [p (social/draft-netflow-post _NET _SRC)]
    (is (= ":dry-run" (get p ":post/status")))
    (is (true?  (get p ":post/is-mirror")))
    (is (true?  (get p ":post/no-trade-notice")))
    (is (false? (get p ":post/server-held-key")))))

(deftest test-netflow-post-body-has-disclaimer
  (let [p (social/draft-netflow-post _NET _SRC)]
    (is (str/includes? (get p ":post/body") "トレードはしない"))))

(deftest test-rotation-post-ok
  (let [p (social/draft-rotation-post _ROT _SRC)]
    (is (str/includes? (get p ":post/body") "US Treasuries"))
    (is (= ":dry-run" (get p ":post/status")))))

(deftest test-regime-post-states-descriptor
  (let [p (social/draft-regime-post _REGIME _SRC)]
    (is (str/includes? (get p ":post/body") "risk-on"))
    (is (str/includes? (get p ":post/body") "助言ではありません"))))

(deftest test-post-requires-two-sources-g3
  (expect-raises "G3"
    (social/draft-netflow-post _NET ["only-one"])))

(deftest test-post-refuses-denied-source
  (expect-raises "Rider"
    (social/draft-netflow-post _NET ["bloomberg terminal" "x"])))

(deftest test-no-trade-guard-blocks-buy
  (expect-raises "G2"
    (#'shionome.methods.social/guard-no-trade "you should buy equities")))

(deftest test-no-trade-guard-blocks-japanese
  (expect-raises "G2"
    (#'shionome.methods.social/guard-no-trade "目標株価は5000円")))

(deftest test-no-trade-guard-allows-disclaimer
  ;; the disclaimer NAMES the prohibited acts; it must not trip the guard
  (is (nil? (#'shionome.methods.social/guard-no-trade social/DISCLAIMER))))

(deftest test-build-live-refuses-g8
  (expect-raises "G8"
    (social/build-live)))

(deftest test-empty-rotation-post-safe
  (let [p (social/draft-rotation-post [] _SRC)]
    (is (= ":dry-run" (get p ":post/status")))))

;; ── runner ───────────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'shionome.methods.test-social)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
