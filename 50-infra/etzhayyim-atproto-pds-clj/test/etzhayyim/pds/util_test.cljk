(ns etzhayyim.pds.util-test
  "Pure invariants for atproto identifier primitives: TID rkeys + content CIDs."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.pds.util :as u]))

(def ^:private b32-alphabet "234567abcdefghijklmnopqrstuvwxyz")

(deftest content-cid-deterministic-and-stable
  (testing "same value → same CID, prefixed 'b' (multibase base32)"
    (is (= (u/content-cid {"a" 1}) (u/content-cid {"a" 1})))
    (is (str/starts-with? (u/content-cid {"a" 1}) "b")))
  (testing "different value → different CID"
    (is (not= (u/content-cid {"a" 1}) (u/content-cid {"a" 2}))))
  (testing "an equal map literal hashes identically regardless of how it is written"
    ;; Clojure map equality is order-independent, so two *equal* maps share a CID.
    (is (= (u/content-cid {"a" 1 "b" 2}) (u/content-cid {"a" 1 "b" 2}))))
  ;; LATENT CANONICALISATION GAP (surfaced by this test): content-cid passes
  ;; `{:sort-keys true}` to cheshire, but that is NOT a real cheshire option — it
  ;; is silently ignored, so the JSON follows map *iteration* order rather than a
  ;; canonical sorted order. For small array-maps the iteration order tracks the
  ;; literal write order, so the SAME logical record built with different key
  ;; insertion order currently yields DIFFERENT CIDs. The util.clj docstring
  ;; already flags a spec-exact CIDv1 dag-cbor multihash as the follow-up; true
  ;; canonical addressing should sort keys (sorted-map or :key-fn) before hashing.
  ;; Documented here, not fixed (coverage-only): pin the current behaviour so a
  ;; future canonicalisation fix is a deliberate, visible change.
  (testing "current behaviour: differing key insertion order changes the CID"
    (is (not= (u/content-cid (array-map "a" 1 "b" 2))
              (u/content-cid (array-map "b" 2 "a" 1)))))
  (testing "CID body uses only the atproto base32 alphabet"
    (is (every? #(str/index-of b32-alphabet (str %))
                (subs (u/content-cid {"x" "y"}) 1)))))

(deftest tid-shape-and-monotonicity
  (testing "13-char rkey from the base32 alphabet"
    (let [t (u/tid)]
      (is (= 13 (count t)))
      (is (every? #(str/index-of b32-alphabet (str %)) t))))
  (testing "successive TIDs are strictly increasing + sortable + unique"
    (let [ts (vec (repeatedly 8 u/tid))]
      (is (apply distinct? ts))
      (is (= ts (vec (sort ts))))            ;; generation order == lexical order
      (is (neg? (compare (first ts) (last ts)))))))

(deftest now-iso-parseable
  (let [s (u/now-iso)]
    (is (string? s))
    (is (some? (java.time.Instant/parse s)))))   ;; throws if not ISO-8601

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.util-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
