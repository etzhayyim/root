(ns etzhayyim.explorer.coverage11-test
  "Coverage for the live SSE frame decoder (transit+json → JSON → raw fallback),
   extracted from the EventSource onmessage handler so it is unit-testable."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [etzhayyim.explorer.live :as live]
            [etzhayyim.explorer.wire :as wire]))

(deftest decode-frame-transit
  (testing "a transit+json frame decodes with keyword/type fidelity"
    (let [frame (wire/encode {:datom ["e" :vitals.actor/cells 0] :seq 3})
          decoded (live/decode-frame frame)]
      (is (= {:datom ["e" :vitals.actor/cells 0] :seq 3} decoded))
      (is (keyword? (second (:datom decoded)))))))

(deftest decode-frame-scalar
  (testing "a transit scalar still decodes (transit reads ground types)"
    (is (= 42 (live/decode-frame "42")))))

(deftest decode-frame-raw-fallback
  (testing "an undecodable frame is wrapped as {:raw …} rather than throwing"
    (let [garbage "not transit not json {{{"
          decoded (live/decode-frame garbage)]
      (is (= {:raw garbage} decoded)))))
