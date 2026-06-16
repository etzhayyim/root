(ns noroshi.methods.test-isac-sim
  "Tests for the noroshi ISAC/JCAS simulator (ADR-2606051600).
  1:1 Clojure port of methods/test_isac_sim.py (pytest → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [clojure.set :as set]
            [noroshi.methods.isac-sim :as I]))

(def WF (I/isac-waveform))

(defn- approx?
  ([a b tol] (<= (Math/abs (- (double a) (double b))) tol)))
(defn- rel? [a b rel]
  (<= (Math/abs (- (double a) (double b))) (* rel (max (Math/abs (double a)) (Math/abs (double b)) 1e-300))))

(defn- bins [ests] (set (map (fn [e] [(get e "range_bin") (get e "doppler_bin")]) ests)))
(defn- bin-vec [ests] (mapv (fn [e] [(get e "range_bin") (get e "doppler_bin")]) ests))

;; ── waveform formulas ────────────────────────────────────────────────────────
(deftest test-range-resolution-formula
  (is (rel? (I/range-resolution-m WF) (/ I/C-LIGHT (* 2 (I/bandwidth-hz WF))) 1e-12)))

(deftest test-velocity-resolution-formula
  (is (rel? (I/velocity-resolution-mps WF) (/ (I/wavelength-m WF) (* 2 (get WF "n_sym") (get WF "symbol_s"))) 1e-12)))

;; ── sensing recovery ──────────────────────────────────────────────────────────
(deftest test-target-on-bin-is-recovered
  (doseq [[k l] [[4 3] [10 1] [1 7] [20 5]]]
    (let [tgt (I/target :range_m (* k (I/range-resolution-m WF)) :velocity_mps (* l (I/velocity-resolution-mps WF)))
          est (I/estimate-target WF tgt)]
      (is (= (get est "range_bin") k))
      (is (= (get est "doppler_bin") l))
      (is (rel? (get est "range_m") (get tgt "range_m") 1e-6))
      (is (rel? (get est "velocity_mps") (get tgt "velocity_mps") 1e-6)))))

(deftest test-off-bin-target-recovered-within-one-resolution-cell
  (let [tgt (I/target :range_m (* 4.4 (I/range-resolution-m WF)) :velocity_mps (* 2.6 (I/velocity-resolution-mps WF)))
        est (I/estimate-target WF tgt)]
    (is (<= (Math/abs (- (get est "range_m") (get tgt "range_m"))) (I/range-resolution-m WF)))
    (is (<= (Math/abs (- (get est "velocity_mps") (get tgt "velocity_mps"))) (I/velocity-resolution-mps WF)))))

;; ── JCAS power-split tradeoff ──────────────────────────────────────────────────
(deftest test-more-comms-power-raises-capacity
  (let [lo (I/jcas-operating-point WF 0.2) hi (I/jcas-operating-point WF 0.8)]
    (is (> (get hi "capacity_gbps") (get lo "capacity_gbps")))))

(deftest test-more-comms-power-worsens-sensing-precision
  (let [lo (I/jcas-operating-point WF 0.2) hi (I/jcas-operating-point WF 0.8)]
    (is (> (get hi "range_std_m") (get lo "range_std_m")))
    (is (> (get hi "velocity_std_mps") (get lo "velocity_std_mps")))))

(deftest test-power-split-out-of-range-rejected
  (is (thrown? #?(:clj Exception :cljs js/Error) (I/jcas-operating-point WF 1.5)))
  (is (thrown? #?(:clj Exception :cljs js/Error) (I/jcas-operating-point WF -0.1))))

(deftest test-report-renders
  (let [txt (I/report)]
    (is (str/includes? txt "ISAC"))
    (is (str/includes? txt "JCAS power-split tradeoff"))
    (is (str/includes? txt "never a person"))))

(deftest test-report-includes-pd-detection-curve
  (let [txt (I/report)]
    (is (str/includes? txt "CA-CFAR detection probability"))
    (is (str/includes? txt "| noise σ | Pd |"))))

;; ── coverage ────────────────────────────────────────────────────────────────
(deftest test-max-unambiguous-range-formula
  (is (rel? (I/max-unambiguous-range-m WF) (/ I/C-LIGHT (* 2 (get WF "subcarrier_hz"))) 1e-12)))

(deftest test-qpsk-symbols-are-unit-magnitude
  (doseq [n (range 8) m (range 8)]
    (let [[re im] (I/qpsk-symbol n m)]
      (is (approx? (Math/sqrt (+ (* re re) (* im im))) 1.0 1e-12)))))

(deftest test-jcas-capacity-matches-shannon-closed-form
  (let [op (I/jcas-operating-point WF 0.5 :tx_power_w 1.0 :channel_gain_db -90.0 :noise_psd_dbm_hz -174.0)
        b (I/bandwidth-hz WF)
        noise-w (* (Math/pow 10 (/ (- -174.0 30) 10)) b)
        snr (/ (* 0.5 1.0 (Math/pow 10 (/ -90.0 10))) noise-w)]
    (is (rel? (get op "capacity_gbps") (/ (* b (/ (Math/log (+ 1 snr)) (Math/log 2))) 1e9) 1e-9))))

(deftest test-degenerate-waveform-rejected
  (doseq [bad [(I/isac-waveform :n_sub 0) (I/isac-waveform :n_sym 0)
               (I/isac-waveform :subcarrier_hz 0.0) (I/isac-waveform :symbol_s -1.0)]]
    (is (thrown? #?(:clj Exception :cljs js/Error) (I/estimate-target bad (I/target :range_m 10.0 :velocity_mps 0.0))))
    (is (thrown? #?(:clj Exception :cljs js/Error) (I/jcas-operating-point bad 0.5)))))

(deftest test-zero-rcs-target-still-returns-an-estimate
  (let [est (I/estimate-target WF (I/target :range_m (* 4 (I/range-resolution-m WF)) :velocity_mps 0.0 :rcs 0.0))]
    (is (approx? (get est "peak_magnitude") 0.0 1e-6))))

(deftest test-stationary-target-lands-on-zero-doppler-bin
  (let [est (I/estimate-target WF (I/target :range_m (* 6 (I/range-resolution-m WF)) :velocity_mps 0.0))]
    (is (= (get est "doppler_bin") 0))
    (is (approx? (get est "velocity_mps") 0.0 1e-9))))

;; ── multi-target sensing ──────────────────────────────────────────────────────
(deftest test-estimate-targets-recovers-all-well-separated-targets
  (let [tg [(I/target :range_m (* 4 (I/range-resolution-m WF)) :velocity_mps (* 2 (I/velocity-resolution-mps WF)))
            (I/target :range_m (* 12 (I/range-resolution-m WF)) :velocity_mps (* 5 (I/velocity-resolution-mps WF)))
            (I/target :range_m (* 20 (I/range-resolution-m WF)) :velocity_mps (* 1 (I/velocity-resolution-mps WF)))]]
    (is (= (bins (I/estimate-targets WF tg)) #{[4 2] [12 5] [20 1]}))))

(deftest test-estimate-targets-single-matches-estimate-target
  (let [t (I/target :range_m (* 7 (I/range-resolution-m WF)) :velocity_mps (* 3 (I/velocity-resolution-mps WF)))
        multi (first (I/estimate-targets WF [t]))
        single (I/estimate-target WF t)]
    (is (= [(get multi "range_bin") (get multi "doppler_bin")]
           [(get single "range_bin") (get single "doppler_bin")]))))

(deftest test-estimate-targets-empty-list-returns-empty
  (is (= (I/estimate-targets WF []) [])))

(deftest test-estimate-targets-top-n-caps-results
  (let [tg (mapv (fn [i] (I/target :range_m (* (+ 4 (* 6 i)) (I/range-resolution-m WF))
                                   :velocity_mps (* 2 (I/velocity-resolution-mps WF)))) (range 3))]
    (is (= (count (I/estimate-targets WF tg :top_n 2)) 2))))

(deftest test-estimate-targets-guard-prevents-double-detection
  (let [t (I/target :range_m (* 10 (I/range-resolution-m WF)) :velocity_mps (* 4 (I/velocity-resolution-mps WF)))
        picks (I/estimate-targets WF [t] :top_n 2)]
    (is (= (count (bins picks)) 2))
    (is (thrown? #?(:clj Exception :cljs js/Error) (I/estimate-targets (I/isac-waveform :n_sub 0) [t])))))

;; ── CFAR detection ─────────────────────────────────────────────────────────────
(defn- two-targets []
  [(I/target :range_m (* 4 (I/range-resolution-m WF)) :velocity_mps (* 2 (I/velocity-resolution-mps WF)))
   (I/target :range_m (* 14 (I/range-resolution-m WF)) :velocity_mps (* 5 (I/velocity-resolution-mps WF)))])

(deftest test-cfar-noiseless-detects-exactly-the-true-targets
  (is (= (bins (I/detect-cfar WF (two-targets) :noise_sigma 0.0)) #{[4 2] [14 5]})))

(deftest test-cfar-detects-true-targets-under-noise
  (let [dets (I/detect-cfar WF (two-targets) :noise_sigma 0.3 :threshold_factor 4.0 :seed 1)]
    (is (set/subset? #{[4 2] [14 5]} (bins dets)))))

(deftest test-cfar-is-reproducible-for-a-given-seed
  (let [a (I/detect-cfar WF (two-targets) :noise_sigma 0.5 :threshold_factor 4.0 :seed 7)
        b (I/detect-cfar WF (two-targets) :noise_sigma 0.5 :threshold_factor 4.0 :seed 7)]
    (is (= (bin-vec a) (bin-vec b)))))

(deftest test-cfar-higher-threshold-controls-false-alarms
  (let [loose  (I/detect-cfar WF (two-targets) :noise_sigma 1.0 :threshold_factor 2.0 :seed 3)
        strict (I/detect-cfar WF (two-targets) :noise_sigma 1.0 :threshold_factor 10.0 :seed 3)]
    (is (<= (count strict) (count loose)))
    (is (<= (count strict) (+ 2 1)))))

(deftest test-cfar-empty-and-noiseless-returns-no-detections
  (is (= (I/detect-cfar WF [] :noise_sigma 0.0) [])))

(deftest test-cfar-rejects-bad-parameters
  (doseq [[sigma factor] [[-0.1 4.0] [0.3 0.0] [0.3 -1.0]]]
    (is (thrown? #?(:clj Exception :cljs js/Error) (I/detect-cfar WF (two-targets) :noise_sigma sigma :threshold_factor factor)))))

;; ── Pd vs SNR ───────────────────────────────────────────────────────────────────
(def SWF (I/isac-waveform :n_sub 16 :n_sym 8))
(def STGT (I/target :range_m (* 4 (I/range-resolution-m SWF)) :velocity_mps (* 2 (I/velocity-resolution-mps SWF))))

(deftest test-pd-is-one-at-low-noise
  (is (= (I/detection-probability SWF STGT 0.0 :trials 8) 1.0)))

(deftest test-pd-degrades-at-high-noise
  (is (< (I/detection-probability SWF STGT 6.0 :trials 8) 1.0)))

(deftest test-pd-vs-snr-is-monotone-non-increasing
  (let [curve (I/pd-vs-snr SWF STGT [0.0 1.0 3.0 6.0] :trials 8)
        pds (mapv second curve)]
    (is (every? (fn [i] (>= (pds i) (pds (inc i)))) (range (dec (count pds)))))
    (is (= (first pds) 1.0))
    (is (< (last pds) 1.0))))

(deftest test-pd-is-reproducible
  (is (= (I/detection-probability SWF STGT 2.0 :trials 8) (I/detection-probability SWF STGT 2.0 :trials 8))))

(deftest test-detection-probability-rejects-zero-trials
  (is (thrown? #?(:clj Exception :cljs js/Error) (I/detection-probability SWF STGT 1.0 :trials 0))))

#?(:clj (defn -main [& _] (run-tests 'noroshi.methods.test-isac-sim)))
