(ns etzhayyim.pds.lexicon-test
  "Opt-in lexicon-shape validation (PDS_VALIDATE_RECORDS): unregistered collections
  always pass (permissive PDS), known app.bsky.* collections enforce required fields
  + string typing, and validation works on both string- and keyword-keyed records."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.pds.lexicon :as lex]))

(deftest unregistered-collections-always-pass
  (testing "an unknown collection is never validated (the PDS is permissive)"
    (is (nil? (lex/validate "com.example.custom.record" {"anything" 1})))
    (is (nil? (lex/validate "app.bsky.feed.unknownThing" {})))))

(deftest valid-records-pass-string-and-keyword-keyed
  (testing "a well-formed post passes (string keys)"
    (is (nil? (lex/validate "app.bsky.feed.post" {"text" "hi" "createdAt" "2026-06-26T00:00:00Z"}))))
  (testing "a well-formed post passes (keyword keys — the incoming-JSON path)"
    (is (nil? (lex/validate "app.bsky.feed.post" {:text "hi" :createdAt "2026-06-26T00:00:00Z"}))))
  (testing "actor.profile has NO required fields → an empty record passes"
    (is (nil? (lex/validate "app.bsky.actor.profile" {})))
    (is (nil? (lex/validate "app.bsky.actor.profile" {"displayName" "Alice"})))))

(deftest missing-required-fields-are-reported
  (testing "a post without createdAt is rejected, naming the missing field"
    (let [err (lex/validate "app.bsky.feed.post" {"text" "hi"})]
      (is (string? err))
      (is (str/includes? err "createdAt"))
      (is (str/includes? err "app.bsky.feed.post"))))
  (testing "a follow without its subject is rejected"
    (is (str/includes? (lex/validate "app.bsky.graph.follow" {"createdAt" "2026-06-26T00:00:00Z"})
                       "subject"))))

(deftest non-string-typed-fields-are-reported
  (testing "a post whose text is not a string is rejected as a type error"
    (let [err (lex/validate "app.bsky.feed.post" {"text" 42 "createdAt" "2026-06-26T00:00:00Z"})]
      (is (string? err))
      (is (str/includes? err "must be strings"))
      (is (str/includes? err "text"))))
  (testing "actor.profile with a non-string displayName is a type error"
    (is (str/includes? (lex/validate "app.bsky.actor.profile" {"displayName" 7}) "must be strings"))))

(deftest missing-takes-precedence-over-type-error
  (testing "a record both missing a required field AND mistyped reports the MISSING field first"
    ;; text present-but-mistyped + createdAt absent → the cond reports the missing required field
    (let [err (lex/validate "app.bsky.feed.post" {"text" 99})]
      (is (str/includes? err "requires"))
      (is (str/includes? err "createdAt"))
      (is (not (str/includes? err "must be strings"))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.lexicon-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
