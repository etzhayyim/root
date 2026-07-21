(ns etzhayyim.murakumo-test
  "Tests for the shared Murakumo inference helper (ADR-2605215000; fail-open G6).
  No network is touched — the fail-open (nil node) + allowlist paths are pure."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.murakumo :as mk]))

(deftest fails-open-with-no-node
  (testing "infer-text with no reachable node returns nil (the caller uses its template)"
    (is (nil? (mk/infer-text [{:role "user" :content "x"}] nil)))))

(deftest murakumo-only-allowlist
  (testing "only the resolved fleet hosts are Murakumo (G6) — no other endpoint"
    (is (true? (mk/murakumo-host? "issachar")))
    (is (true? (mk/murakumo-host? "zebulun")))
    (is (false? (mk/murakumo-host? "api.openai.com")))
    (is (false? (mk/murakumo-host? "runpod.io")))))
