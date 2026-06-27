(ns tests.test-sodai-submit
  "Smoke tests for the sodai_submit clj port — no network, no browser.
  Verifies graph compiles, mode validation, field-map override, the
  browser-missing degradation, and the submit double-gate. clj port of
  tests/test_sodai_submit.py."
  (:require [clojure.test :refer [deftest is]]
            [clojure.string :as str]
            [clojure.set :as set]
            [lg-chat.graphs.sodai-submit :as ss]
            [lg-chat.sodai-fields :as sf]))

(def APP
  {"items" [{"name" "ソファー（2人以上用）" "qty" 1}]
   "name" "渋谷　太郎" "nameKana" "シブヤ　タロウ"
   "postal" "150-8010" "address" "渋谷区宇田川町１－１"
   "building" "" "phone" "0312345678" "email" "" "preferredDate" ""})

(deftest graph-compiles
  (let [graph ss/GRAPH
        node-names (-> graph :graph :nodes keys set)]
    (is (some? graph))
    (is (set/subset? #{:validate :drive} node-names))))

(deftest field-map-override
  ;; env override is read live; we test the merge logic on the parsed default.
  (let [fm sf/DEFAULT-FIELD-MAP]
    (is (contains? fm "name"))
    (is (contains? fm "phone"))
    ;; load-field-map returns the defaults when env is unset
    (is (= (sf/load-field-map) sf/DEFAULT-FIELD-MAP))))

(deftest validate-rejects-bad-mode
  (let [out (ss/node-validate {:mode "wreck-it" :application APP})]
    (is (= "error" (:status out)))))

(deftest validate-defaults-to-prefill
  (let [out (ss/node-validate {:application APP})]
    (is (= "prefill" (:mode out)))
    (is (false? (:submitted out)))))

(deftest drive-degrades-when-browser-missing
  ;; No clj browser driver under bb → drive must return a clear status, not crash.
  (let [out (ss/node-drive {:mode "prefill" :application APP})]
    (is (= "browser_missing" (:status out)))
    (is (str/includes? (str/lower-case (:error out)) "playwright"))))

(deftest submit-double-gate-refuses-without-approval
  ;; submit-click is the human-gated node; without approval it must not submit.
  (let [out (ss/node-submit-click {:mode "submit" :human-approved false})]
    (is (false? (:submitted out)))
    (is (str/includes? (:error out) "人間ゲート"))))

(deftest route-after-drive-to-end-unless-submit-approved
  (is (= :langgraph/end (ss/route-after-drive {:mode "prefill" :status "ok"})))
  (is (= :langgraph/end (ss/route-after-drive {:mode "submit" :human-approved false :status "ok"})))
  (is (= :submit-click
         (ss/route-after-drive {:mode "submit" :human-approved true :status "ok"}))))
