(ns etzhayyim.registry.sync-node-test
  "Coverage for the kotoba sync node's pure helpers: cursor parsing, the
   transit+json frame round-trip, and the Datom stream materialiser."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.registry.sync-node :as sn]
            [cognitect.transit :as t])
  (:import [java.io ByteArrayInputStream]))

(def ^:private cursor-of #'sn/cursor-of)
(def ^:private transit-json #'sn/transit-json)
(def ^:private load-datoms #'sn/load-datoms)

(deftest cursor-parsing
  (testing "cursor is read from the query string, defaulting to 0"
    (is (= 7 (cursor-of "GET /xrpc/...sync.subscribe?cursor=7 HTTP/1.1")))
    (is (= 0 (cursor-of "GET /xrpc/...sync.subscribe HTTP/1.1")))
    (is (= 0 (cursor-of nil)))))

(deftest transit-frame-roundtrips
  (testing "a frame encodes to transit+json and decodes with keyword fidelity"
    (let [frame {:datom ["e1" :vitals.actor/cells 0] :seq 3 :as-of 4}
          json (transit-json frame)
          decoded (t/read (t/reader (ByteArrayInputStream. (.getBytes json "UTF-8")) :json))]
      (is (string? json))
      (is (= frame decoded))
      (is (keyword? (second (:datom decoded)))))))   ; attr survives as a keyword

(deftest datom-stream-materialises
  (testing "load-datoms yields [entity attr value] triples from the vitals EAVT"
    (let [datoms (load-datoms)]
      (is (pos? (count datoms)))
      (is (every? #(= 3 (count %)) datoms))
      (is (keyword? (second (first datoms)))))))
