;; etzhayyim.test-manimani — unit tests for the manimani CLI's pure helpers.
;;
;; Scope: only pure functions (no live network / Keychain / kotoba journal). The
;; Gmail OAuth2 flow (auth-gmail / ingest-gmail's live legs) needs a real Google
;; account + browser consent and is exercised manually, not here — this covers the
;; parts that ARE independently verifiable: PKCE generation, CLI flag parsing
;; (incl. the --flag-with-no-value → true fix), Gmail header extraction, and the
;; existing heuristic classifier.
(ns etzhayyim.test-manimani
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.manimani :as m]))

(deftest parse-flags-boolean-vs-value
  (testing "a --flag with no following value (or followed by another --flag) is boolean true"
    (is (= [[] {:backfill true}] (#'m/parse-flags ["--backfill"])))
    (is (= [[] {:since "3d" :backfill true}] (#'m/parse-flags ["--since" "3d" "--backfill"])))
    (is (= [[] {:backfill true :since "3d"}] (#'m/parse-flags ["--backfill" "--since" "3d"]))))
  (testing "a --key value pair still parses as before"
    (is (= [[] {:kind "memo"}] (#'m/parse-flags ["--kind" "memo"])))
    (is (= [["hello"] {:days "7"}] (#'m/parse-flags ["hello" "--days" "7"]))))
  (testing "positional args pass through untouched"
    (is (= [["a" "b"] {}] (#'m/parse-flags ["a" "b"])))))

(deftest pkce-verifier-and-challenge
  (testing "verifier: 43 chars, URL-safe (RFC 7636 base64url, no padding)"
    (let [v (#'m/pkce-verifier)]
      (is (= 43 (count v)))
      (is (not (re-find #"[+/=]" v)))))
  (testing "challenge is the S256 transform of ITS OWN verifier, and differs per verifier"
    (let [v1 (#'m/pkce-verifier) v2 (#'m/pkce-verifier)
          c1 (#'m/pkce-challenge v1) c1' (#'m/pkce-challenge v1) c2 (#'m/pkce-challenge v2)]
      (is (= 43 (count c1)))
      (is (not (re-find #"[+/=]" c1)))
      (is (= c1 c1') "challenge is a pure/deterministic function of the verifier")
      (is (not= c1 c2) "different verifiers (independently random) yield different challenges"))))

(deftest gmail-header-extraction
  (let [headers [{:name "From" :value "sender@example.com"}
                 {:name "Subject" :value "Re: quarterly filing"}]]
    (is (= "sender@example.com" (#'m/gmail-header headers "From")))
    (is (= "Re: quarterly filing" (#'m/gmail-header headers "Subject")))
    (is (nil? (#'m/gmail-header headers "Date")) "absent header → nil, not an exception")))

(deftest heuristic-classify-existing
  (testing "keyword overlap with an existing project slug routes there"
    (is (= "jk-tax" (:project (#'m/heuristic-classify "jk tax notice arrived" [{:slug "jk-tax"}])))))
  (testing "no overlap → :unsorted honest fallback, confidence < 0.5"
    (let [{:keys [project confidence]} (#'m/heuristic-classify "unrelated fragment" [{:slug "jk-tax"}])]
      (is (= "unsorted" project))
      (is (< confidence 0.5)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-manimani)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
