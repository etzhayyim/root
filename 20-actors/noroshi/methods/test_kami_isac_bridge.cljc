(ns noroshi.methods.test-kami-isac-bridge
  "Tests for the noroshi×kami-autodrive ISAC sensor bridge (ADR-2606051600).
  1:1 Clojure port of methods/test_kami_isac_bridge.py (pytest → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [noroshi.methods.isac-sim :as isac]
            [noroshi.methods.kami-isac-bridge :as kib]))

(def WF (isac/isac-waveform))

(defn- approx? [a b rel]
  (<= (Math/abs (- (double a) (double b))) (* rel (max (Math/abs (double a)) (Math/abs (double b)) 1e-300))))

(deftest test-track-follows-closing-range
  (let [obj (kib/scenario-object "o1" (* 30 (isac/range-resolution-m WF)) (* 2 (isac/velocity-resolution-mps WF)))
        track (kib/track-object WF obj :frames 6 :frame_dt_s 0.002)
        ranges (mapv #(get % "range_m") track)]
    (is (= (count track) 6))
    (is (every? (fn [i] (>= (ranges i) (ranges (inc i)))) (range (dec (count ranges)))))))

(deftest test-velocity-recovered-each-frame
  (let [v (* 3 (isac/velocity-resolution-mps WF))
        obj (kib/scenario-object "o1" (* 30 (isac/range-resolution-m WF)) v)
        track (kib/track-object WF obj :frames 4)]
    (doseq [p track]
      (is (approx? (get p "velocity_mps") v 1e-6)))))

(deftest test-track-stops-when-object-passes-ego
  (let [obj (kib/scenario-object "fast" (* 2 (isac/range-resolution-m WF)) (* 50 (isac/velocity-resolution-mps WF)))
        track (kib/track-object WF obj :frames 20 :frame_dt_s 0.05)]
    (is (< (count track) 20))
    (is (every? #(> (get % "range_m") 0) track))))

(deftest test-run-scenario-returns-track-per-object
  (let [objs [(kib/scenario-object "a" (* 15 (isac/range-resolution-m WF)) (isac/velocity-resolution-mps WF))
              (kib/scenario-object "b" (* 18 (isac/range-resolution-m WF)) (* 2 (isac/velocity-resolution-mps WF)))]
        tracks (kib/run-scenario objs :wf WF :frames 3)]
    (is (= (set (keys tracks)) #{"a" "b"}))
    (is (every? #(= (count %) 3) (vals tracks)))))

(deftest test-object-starting-at-or-behind-ego-yields-empty-track
  (let [obj (kib/scenario-object "at-ego" 0.0 (isac/velocity-resolution-mps WF))]
    (is (= (kib/track-object WF obj :frames 5) []))))

(deftest test-zero-velocity-object-keeps-constant-range
  (let [obj (kib/scenario-object "static" (* 12 (isac/range-resolution-m WF)) 0.0)
        track (kib/track-object WF obj :frames 4)
        ranges (set (map (fn [p] (-> (get p "range_m") (* 1e6) Math/round (/ 1e6))) track))]
    (is (= (count ranges) 1))
    (is (every? #(= (get % "doppler_bin") 0) track))))

(deftest test-sense-frame-detects-all-objects-in-one-shot
  (let [objs [(kib/scenario-object "a" (* 4 (isac/range-resolution-m WF)) (* 2 (isac/velocity-resolution-mps WF)))
              (kib/scenario-object "b" (* 14 (isac/range-resolution-m WF)) (* 5 (isac/velocity-resolution-mps WF)))]
        dets (kib/sense-frame objs :wf WF)
        bins (set (map (fn [d] [(get d "range_bin") (get d "doppler_bin")]) dets))]
    (is (= bins #{[4 2] [14 5]}))))

(deftest test-sense-frame-drops-objects-at-or-behind-ego
  (let [objs [(kib/scenario-object "ahead" (* 6 (isac/range-resolution-m WF)) (isac/velocity-resolution-mps WF))
              (kib/scenario-object "at-ego" 0.0 (isac/velocity-resolution-mps WF))]]
    (is (= (count (kib/sense-frame objs :wf WF)) 1))))

(deftest test-report-renders-and-is-civilian
  (let [txt (kib/report)]
    (is (str/includes? txt "ISAC sensor"))
    (is (or (str/includes? txt "Civilian") (str/includes? txt "civilian")))))

#?(:clj (defn -main [& _] (run-tests 'noroshi.methods.test-kami-isac-bridge)))
