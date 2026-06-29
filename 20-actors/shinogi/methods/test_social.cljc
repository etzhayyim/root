#!/usr/bin/env bb
;; shinogi 鎬 — social-protocol membrane tests (dry-run, no-server-key, live-gated).
(ns shinogi.methods.test-social
  (:require [shinogi.methods.social :as social]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def two-sources ["教育部 高校招生统一考试制度 (1952/1977–)" "MEXT 大学入学共通テスト (2021)"])

;; ── G5 — a post needs ≥2 disclosed public sources ────────────────────────────
(deftest needs-two-sources
  (is (thrown? clojure.lang.ExceptionInfo (social/enough-sources ["only one"]))
      "G5: <2 sources is refused")
  (is (thrown? clojure.lang.ExceptionInfo (social/enough-sources []))
      "G5: 0 sources is refused")
  (is (= two-sources (social/enough-sources two-sources)) "≥2 sources passes"))

;; ── drafts are dry-run + no-server-key + non-adjudicating + person-excluded ──
(deftest draft-is-dry-run-no-key
  (let [p (social/draft-loop-post {:id "R-involution-arms-race" :type :reinforcing
                                   :drive 0.296 :regime :vicious} two-sources)]
    (is (= :dry-run (:post/status p)) "status dry-run (never live)")
    (is (= false (:post/server-held-key p)) "no-server-key (ADR-2605231525)")
    (is (true? (:post/non-adjudicating p)) "non-adjudicating MIRROR (G7)")
    (is (true? (:post/person-excluded p)) "person-excluded (G6)")
    (is (str/includes? (:post/text p) "MIRROR") "carries the analysis-only disclaimer (G7)")
    (is (= 2 (count (:post/sources p))))))

;; ── the relief-cycle post routes to relief, never amplifies ──────────────────
(deftest cycle-post-routes-to-relief
  (let [p (social/draft-cycle-post "卒業後 頑張れない/躺平" ["kokoro" "shiori" "manabi"] 2.188 two-sources)]
    (is (str/includes? (:post/text p) "RELIEF"))
    (is (str/includes? (:post/text p) "kokoro"))
    (is (str/includes? (:post/text p) "怠惰") "explicitly frames it as NOT laziness (§1.4)")))

;; ── the energy-flow post is a candidate design ───────────────────────────────
(deftest energy-flow-post-is-candidate
  (let [p (social/draft-energy-flow-post
           {:current-wellbecoming 0.044 :designed-wellbecoming 0.421 :wellbecoming-gain 0.377}
           two-sources)]
    (is (str/includes? (:post/text p) "CANDIDATE") "framed as a candidate, not a directive (G11)")
    (is (= :dry-run (:post/status p)))))

;; ── G4/G13 — live broadcast is structurally refused ──────────────────────────
(deftest live-broadcast-refused
  (is (thrown? clojure.lang.ExceptionInfo (social/build-live))
      "G4/G13: shinogi never autonomously broadcasts; live is member-CACAO-leash + Council gated"))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'shinogi.methods.test-social)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))
