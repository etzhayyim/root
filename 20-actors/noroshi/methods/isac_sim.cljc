(ns noroshi.methods.isac-sim
  "noroshi (烽) ISAC simulator — sensing-communication-fusion face (ADR-2606051600).
  1:1 Clojure port of methods/isac_sim.py.

  OFDM-radar reciprocal processing (Sturm & Wiesbeck): divide known data out of the
  echo → pure delay-Doppler grid → 2-D periodogram peak. CIVILIAN object sensing only.
  Deterministic + offline. The __main__ demo is omitted.

  Complex numbers are [re im] vectors. The CFAR noise path inlines CPython's MT19937
  + gauss (random.Random(seed).gauss) byte-for-byte so the seeded detection tests are
  reproducible (Python `random` parity)."
  (:require [clojure.string :as str]))

(def C-LIGHT 299792458.0)
(def TWO-PI (* 2.0 Math/PI))

;; ── complex helpers ([re im]) ───────────────────────────────────────────────────
(defn- cmul [[ar ai] [br bi]] [(- (* ar br) (* ai bi)) (+ (* ar bi) (* ai br))])
(defn- cadd [[ar ai] [br bi]] [(+ ar br) (+ ai bi)])
(defn- cdiv [[ar ai] [br bi]] (let [d (+ (* br br) (* bi bi))]
                                [(/ (+ (* ar br) (* ai bi)) d) (/ (- (* ai br) (* ar bi)) d)]))
(defn- cexp-i [theta] [(Math/cos theta) (Math/sin theta)])  ; e^{i·theta}
(defn- cabs [[r i]] (Math/sqrt (+ (* r r) (* i i))))
(defn- cscale [[r i] s] [(* r s) (* i s)])

;; ── IsacWaveform ────────────────────────────────────────────────────────────────
(defn isac-waveform
  [& {:keys [n_sub n_sym subcarrier_hz symbol_s carrier_hz]
      :or {n_sub 64 n_sym 16 subcarrier_hz 1.0e6 symbol_s 1.2e-6 carrier_hz 28.0e9}}]
  {"n_sub" n_sub "n_sym" n_sym "subcarrier_hz" subcarrier_hz
   "symbol_s" symbol_s "carrier_hz" carrier_hz})

(defn bandwidth-hz [wf] (* (get wf "n_sub") (get wf "subcarrier_hz")))
(defn wavelength-m [wf] (/ C-LIGHT (get wf "carrier_hz")))
(defn range-resolution-m [wf] (/ C-LIGHT (* 2.0 (bandwidth-hz wf))))
(defn velocity-resolution-mps [wf] (/ (wavelength-m wf) (* 2.0 (get wf "n_sym") (get wf "symbol_s"))))
(defn max-unambiguous-range-m [wf] (/ C-LIGHT (* 2.0 (get wf "subcarrier_hz"))))

(defn target
  [& {:keys [range_m velocity_mps rcs] :or {rcs 1.0}}]
  {"range_m" range_m "velocity_mps" velocity_mps "rcs" rcs})

(defn- sense-estimate [range-m velocity-mps range-bin doppler-bin peak-mag]
  {"range_m" range-m "velocity_mps" velocity-mps
   "range_bin" range-bin "doppler_bin" doppler-bin "peak_magnitude" peak-mag})

(defn qpsk-symbol
  "Deterministic unit-magnitude QPSK data symbol."
  [n m]
  (let [quadrant (mod (+ (* n 3) (* m 5)) 4)]
    (cexp-i (+ (/ Math/PI 4) (* quadrant (/ Math/PI 2))))))

(defn validate-waveform [wf]
  (when (or (< (get wf "n_sub") 1) (< (get wf "n_sym") 1))
    (throw (ex-info "waveform needs at least 1 subcarrier and 1 symbol" {})))
  (when (or (<= (get wf "subcarrier_hz") 0) (<= (get wf "symbol_s") 0) (<= (get wf "carrier_hz") 0))
    (throw (ex-info "subcarrier spacing, symbol duration, and carrier must be positive" {}))))

(defn- echo-grid
  "Reciprocal delay-Doppler grid D[n][m]. Returns a vector of n_sub rows of n_sym complex."
  [wf tgt]
  (let [tau (/ (* 2.0 (get tgt "range_m")) C-LIGHT)
        f-d (/ (* 2.0 (get tgt "velocity_mps")) (wavelength-m wf))
        alpha (Math/sqrt (max (get tgt "rcs") 0.0))
        n-sub (get wf "n_sub") n-sym (get wf "n_sym")
        scar (get wf "subcarrier_hz") sym-s (get wf "symbol_s")]
    (mapv (fn [n]
            (mapv (fn [m]
                    (let [x (qpsk-symbol n m)
                          echo (-> x
                                   (cscale alpha)
                                   (cmul (cexp-i (* (- TWO-PI) n scar tau)))
                                   (cmul (cexp-i (* TWO-PI m sym-s f-d))))]
                      (cdiv echo x)))
                  (range n-sym)))
          (range n-sub))))

(defn- periodogram
  "2-D range-Doppler periodogram magnitude P[k][l]."
  [wf grid]
  (let [n-sub (get wf "n_sub") n-sym (get wf "n_sym")]
    (mapv (fn [k]
            (mapv (fn [l]
                    (let [acc (loop [n 0 acc [0.0 0.0]]
                                (if (>= n n-sub)
                                  acc
                                  (let [rk (cexp-i (/ (* TWO-PI n k) n-sub))
                                        acc2 (loop [m 0 acc acc]
                                               (if (>= m n-sym)
                                                 acc
                                                 (recur (inc m)
                                                        (cadd acc (-> (get-in grid [n m])
                                                                      (cmul rk)
                                                                      (cmul (cexp-i (/ (* (- TWO-PI) m l) n-sym))))))))]
                                    (recur (inc n) acc2))))]
                      (cabs acc)))
                  (range n-sym)))
          (range n-sub))))

(defn- bin->estimate [wf k l mag]
  (let [tau (/ k (* (get wf "n_sub") (get wf "subcarrier_hz")))
        f-d (/ l (* (get wf "n_sym") (get wf "symbol_s")))]
    (sense-estimate (/ (* C-LIGHT tau) 2.0) (/ (* (wavelength-m wf) f-d) 2.0) k l mag)))

(defn- argmax-bin
  "Return [k l] of the maximum value in the 2-D mags (n_sub × n_sym), Python max() order:
  first by k then l, ties keep the first-seen max (Python max keeps first on ties)."
  [wf mags]
  (let [n-sub (get wf "n_sub") n-sym (get wf "n_sym")]
    (loop [k 0 l 0 bk 0 bl 0 bv (get-in mags [0 0])]
      (cond
        (>= k n-sub) [bk bl]
        (>= l n-sym) (recur (inc k) 0 bk bl bv)
        :else (let [v (get-in mags [k l])]
                (if (> v bv)
                  (recur k (inc l) k l v)
                  (recur k (inc l) bk bl bv)))))))

(defn estimate-target
  "Recover (range, velocity) from one target via the 2-D OFDM-radar periodogram."
  [wf tgt]
  (validate-waveform wf)
  (let [mags (periodogram wf (echo-grid wf tgt))
        [k l] (argmax-bin wf mags)]
    (bin->estimate wf k l (get-in mags [k l]))))

(defn- combined-grid
  "Sum the per-target reciprocal grids."
  [wf targets]
  (let [grids (mapv #(echo-grid wf %) targets)
        n-sub (get wf "n_sub") n-sym (get wf "n_sym")]
    (mapv (fn [n]
            (mapv (fn [m]
                    (reduce (fn [acc g] (cadd acc (get-in g [n m]))) [0.0 0.0] grids))
                  (range n-sym)))
          (range n-sub))))

(defn- extract-peaks
  "CLEAN peak extraction: pick the global max, suppress a ±guard cell, repeat."
  [wf mags & {:keys [top_n guard threshold] :or {guard 1}}]
  (let [n-sub (get wf "n_sub") n-sym (get wf "n_sym")
        cap (if (nil? top_n) (* n-sub n-sym) (min top_n (* n-sub n-sym)))]
    (loop [work (mapv vec mags) picks [] i 0]
      (if (>= i cap)
        picks
        (let [[k l] (argmax-bin wf work)]
          (if (and (some? threshold) (< (get-in mags [k l]) threshold))
            picks
            (let [picks2 (conj picks (bin->estimate wf k l (get-in mags [k l])))
                  work2 (reduce (fn [w [dk dl]]
                                  (assoc-in w [(mod (+ k dk) n-sub) (mod (+ l dl) n-sym)] -1.0))
                                work
                                (for [dk (range (- guard) (inc guard))
                                      dl (range (- guard) (inc guard))] [dk dl]))]
              (recur work2 picks2 (inc i)))))))))

(defn estimate-targets
  "Multi-target sensing: ONE combined echo → CLEAN top-N peak extraction."
  [wf targets & {:keys [top_n guard] :or {guard 1}}]
  (validate-waveform wf)
  (if (empty? targets)
    []
    (let [tn (if (nil? top_n) (count targets) top_n)
          mags (periodogram wf (combined-grid wf targets))]
      (extract-peaks wf mags :top_n tn :guard guard))))

;; ── CPython MT19937 + gauss (random.Random parity) ──────────────────────────────
(def ^:private MT-N 624)
(def ^:private MT-M 397)
(def ^:private MATRIX-A 0x9908b0df)
(def ^:private UPPER 0x80000000)
(def ^:private LOWER 0x7fffffff)

(defn- mt-init-genrand [^longs mt s]
  (aset mt 0 (bit-and (long s) 0xffffffff))
  (dotimes [ii (dec MT-N)]
    (let [i (inc ii) prev (aget mt (dec i))]
      (aset mt i (bit-and (+ (* 1812433253 (bit-xor prev (unsigned-bit-shift-right prev 30))) i) 0xffffffff))))
  mt)

(defn- mt-init-by-array [init-key]
  (let [mt (long-array MT-N) klen (count init-key)
        i (volatile! 1) j (volatile! 0)]
    (mt-init-genrand mt 19650218)
    (dotimes [_ (max MT-N klen)]
      (let [prev (aget mt (dec @i))]
        (aset mt @i (bit-and (+ (bit-xor (aget mt @i)
                                         (* (bit-xor prev (unsigned-bit-shift-right prev 30)) 1664525))
                                (long (nth init-key @j)) @j) 0xffffffff)))
      (vswap! i inc) (vswap! j inc)
      (when (>= @i MT-N) (aset mt 0 (aget mt (dec MT-N))) (vreset! i 1))
      (when (>= @j klen) (vreset! j 0)))
    (dotimes [_ (dec MT-N)]
      (let [prev (aget mt (dec @i))]
        (aset mt @i (bit-and (- (bit-xor (aget mt @i)
                                         (* (bit-xor prev (unsigned-bit-shift-right prev 30)) 1566083941))
                                @i) 0xffffffff)))
      (vswap! i inc)
      (when (>= @i MT-N) (aset mt 0 (aget mt (dec MT-N))) (vreset! i 1)))
    (aset mt 0 0x80000000)
    mt))

(defn- key-from-seed [s]
  (if (zero? s) [0]
      (loop [n (long s) acc []]
        (if (zero? n) acc (recur (unsigned-bit-shift-right n 32) (conj acc (bit-and n 0xffffffff)))))))

(defn- new-rng [s] (atom {:mt (mt-init-by-array (key-from-seed s)) :mti MT-N :gauss-next nil}))

(defn- mt-genrand! [st]
  (let [mt (:mt @st) mti (:mti @st)]
    (when (>= mti MT-N)
      (dotimes [kk (- MT-N MT-M)]
        (let [y (bit-or (bit-and (aget mt kk) UPPER) (bit-and (aget mt (inc kk)) LOWER))]
          (aset mt kk (bit-and (bit-xor (aget mt (+ kk MT-M)) (unsigned-bit-shift-right y 1)
                                        (if (odd? y) MATRIX-A 0)) 0xffffffff))))
      (dotimes [kk2 (dec MT-M)]
        (let [kk (+ (- MT-N MT-M) kk2)
              y (bit-or (bit-and (aget mt kk) UPPER) (bit-and (aget mt (inc kk)) LOWER))]
          (aset mt kk (bit-and (bit-xor (aget mt (+ kk (- MT-M MT-N))) (unsigned-bit-shift-right y 1)
                                        (if (odd? y) MATRIX-A 0)) 0xffffffff))))
      (let [y (bit-or (bit-and (aget mt (dec MT-N)) UPPER) (bit-and (aget mt 0) LOWER))]
        (aset mt (dec MT-N) (bit-and (bit-xor (aget mt (dec MT-M)) (unsigned-bit-shift-right y 1)
                                              (if (odd? y) MATRIX-A 0)) 0xffffffff)))
      (swap! st assoc :mti 0))
    (let [mti (:mti @st) y0 (aget mt mti)]
      (swap! st assoc :mti (inc mti))
      (let [y1 (bit-xor y0 (unsigned-bit-shift-right y0 11))
            y2 (bit-xor y1 (bit-and (bit-shift-left y1 7) 0x9d2c5680))
            y3 (bit-xor y2 (bit-and (bit-shift-left y2 15) 0xefc60000))
            y4 (bit-xor y3 (unsigned-bit-shift-right y3 18))]
        (bit-and y4 0xffffffff)))))

(defn- rng-random [st]
  (let [a (unsigned-bit-shift-right (mt-genrand! st) 5)
        b (unsigned-bit-shift-right (mt-genrand! st) 6)]
    (/ (+ (* a 67108864.0) b) 9007199254740992.0)))

(defn- rng-gauss [st mu sigma]
  (let [z (:gauss-next @st)]
    (if (some? z)
      (do (swap! st assoc :gauss-next nil) (+ mu (* z sigma)))
      (let [x2pi (* (rng-random st) TWO-PI)
            g2rad (Math/sqrt (* -2.0 (Math/log (- 1.0 (rng-random st)))))
            z (* (Math/cos x2pi) g2rad)]
        (swap! st assoc :gauss-next (* (Math/sin x2pi) g2rad))
        (+ mu (* z sigma))))))

(defn- add-noise
  "Add deterministic complex-Gaussian noise (seeded → reproducible)."
  [wf grid sigma seed]
  (let [st (new-rng seed) n-sub (get wf "n_sub") n-sym (get wf "n_sym")]
    ;; Python iterates n outer, m inner; complex(gauss, gauss) computes real then imag.
    (mapv (fn [n]
            (mapv (fn [m]
                    (let [re (rng-gauss st 0.0 sigma)
                          im (rng-gauss st 0.0 sigma)]
                      (cadd (get-in grid [n m]) [re im])))
                  (range n-sym)))
          (range n-sub))))

(defn detect-cfar
  "Detect targets in noise with a constant-false-alarm threshold (simplified CA-CFAR)."
  [wf targets & {:keys [noise_sigma threshold_factor seed guard]
                 :or {noise_sigma 0.0 threshold_factor 4.0 seed 0 guard 1}}]
  (validate-waveform wf)
  (when (< noise_sigma 0) (throw (ex-info "noise_sigma must be ≥ 0" {})))
  (when (<= threshold_factor 0) (throw (ex-info "threshold_factor must be positive" {})))
  (if (and (empty? targets) (== noise_sigma 0))
    []
    (let [n-sub (get wf "n_sub") n-sym (get wf "n_sym")
          grid0 (if (seq targets) (combined-grid wf targets)
                    (vec (repeat n-sub (vec (repeat n-sym [0.0 0.0])))))
          grid (if (> noise_sigma 0) (add-noise wf grid0 noise_sigma seed) grid0)
          mags (periodogram wf grid)
          n-cells (* n-sub n-sym)
          mean-floor (/ (reduce + (mapcat identity mags)) n-cells)
          threshold (* threshold_factor mean-floor)]
      (extract-peaks wf mags :top_n nil :guard guard :threshold threshold))))

(defn detection-probability
  "Monte-Carlo Pd: fraction of `trials` seeds in which CFAR detects the target's true bin."
  [wf tgt noise_sigma & {:keys [threshold_factor trials] :or {threshold_factor 4.0 trials 16}}]
  (when (< trials 1) (throw (ex-info "trials must be ≥ 1" {})))
  (let [truth (estimate-target wf tgt)
        true-bin [(get truth "range_bin") (get truth "doppler_bin")]
        hits (reduce
              (fn [hits seed]
                (let [dets (detect-cfar wf [tgt] :noise_sigma noise_sigma :threshold_factor threshold_factor :seed seed)
                      bins (set (map (fn [d] [(get d "range_bin") (get d "doppler_bin")]) dets))]
                  (if (contains? bins true-bin) (inc hits) hits)))
              0 (range trials))]
    (/ (double hits) trials)))

(defn pd-vs-snr
  "Sweep the noise level → [[σ Pd] …]."
  [wf tgt sigmas & {:keys [threshold_factor trials] :or {threshold_factor 4.0 trials 16}}]
  (mapv (fn [s] [s (detection-probability wf tgt s :threshold_factor threshold_factor :trials trials)]) sigmas))

;; ── communication ↔ sensing power-split ─────────────────────────────────────────
(defn jcas-operating-point
  "One point on the JCAS tradeoff: split total power ρ:(1-ρ) between comms and sensing."
  [wf power-split & {:keys [tx_power_w channel_gain_db noise_psd_dbm_hz]
                     :or {tx_power_w 1.0 channel_gain_db -90.0 noise_psd_dbm_hz -174.0}}]
  (when-not (<= 0.0 power-split 1.0)
    (throw (ex-info "power_split ρ must lie in [0,1]" {})))
  (validate-waveform wf)
  (let [b (bandwidth-hz wf)
        noise-w (* (Math/pow 10 (/ (- noise_psd_dbm_hz 30) 10)) b)
        gain (Math/pow 10 (/ channel_gain_db 10))
        snr-comm (/ (* (max power-split 1e-12) tx_power_w gain) noise-w)
        capacity-bps (* b (/ (Math/log (+ 1.0 snr-comm)) (Math/log 2)))
        n-mn (* (get wf "n_sub") (get wf "n_sym"))
        snr-sense (* (/ (* (max (- 1.0 power-split) 1e-12) tx_power_w gain) noise-w) n-mn)
        crlb-scale (/ 1.0 (Math/sqrt (* 2.0 (max snr-sense 1e-12))))]
    {"power_split" power-split
     "capacity_gbps" (/ capacity-bps 1e9)
     "range_std_m" (* (range-resolution-m wf) crlb-scale)
     "velocity_std_mps" (* (velocity-resolution-mps wf) crlb-scale)}))

;; ── report ──────────────────────────────────────────────────────────────────────
(defn- fmt [fmt-str x] (#?(:clj format :default (fn [_ v] (str v))) fmt-str (double x)))

(defn report
  ([] (report (isac-waveform)))
  ([wf]
   (let [wf (or wf (isac-waveform))
         tgt (target :range_m (* 4 (range-resolution-m wf)) :velocity_mps (* 3 (velocity-resolution-mps wf)))
         est (estimate-target wf tgt)
         lines (atom ["# noroshi 烽 — ISAC (JCAS) sensing + communication"
                      ""
                      "## waveform"
                      (str "- bandwidth        : " (fmt "%.1f" (/ (bandwidth-hz wf) 1e6)) " MHz  (" (get wf "n_sub") " subcarriers × " (fmt "%.0f" (/ (get wf "subcarrier_hz") 1e3)) " kHz)")
                      (str "- range resolution : " (fmt "%.3f" (range-resolution-m wf)) " m   (R_max " (fmt "%.2f" (/ (max-unambiguous-range-m wf) 1e3)) " km)")
                      (str "- velocity res.    : " (fmt "%.3f" (velocity-resolution-mps wf)) " m/s")
                      ""
                      "## sensing recovery (civilian object — never a person, N1/G4)"
                      (str "- true   : R = " (fmt "%.3f" (get tgt "range_m")) " m, v = " (fmt "%.3f" (get tgt "velocity_mps")) " m/s")
                      (str "- est.   : R = " (fmt "%.3f" (get est "range_m")) " m, v = " (fmt "%.3f" (get est "velocity_mps")) " m/s  (bins k=" (get est "range_bin") ", l=" (get est "doppler_bin") ")")
                      ""
                      "## JCAS power-split tradeoff (ρ = fraction to COMMS)"
                      "| ρ | capacity (Gb/s) | range σ (m) | velocity σ (m/s) |"
                      "|---|---|---|---|"])]
     (doseq [rho [0.1 0.3 0.5 0.7 0.9]]
       (let [op (jcas-operating-point wf rho)]
         (swap! lines conj (str "| " (fmt "%.1f" rho) " | " (fmt "%.3f" (get op "capacity_gbps")) " | "
                                (fmt "%.4f" (get op "range_std_m")) " | " (fmt "%.4f" (get op "velocity_std_mps")) " |"))))
     (let [swf (isac-waveform :n_sub 16 :n_sym 8)
           stgt (target :range_m (* 4 (range-resolution-m swf)) :velocity_mps (* 2 (velocity-resolution-mps swf)))]
       (swap! lines into ["" "## CA-CFAR detection probability vs noise (Pd, seeded Monte-Carlo)"
                          "| noise σ | Pd |" "|---|---|"])
       (doseq [[sigma pd] (pd-vs-snr swf stgt [0.0 1.0 2.0 4.0 8.0] :trials 8)]
         (swap! lines conj (str "| " (fmt "%.1f" sigma) " | " (fmt "%.2f" pd) " |"))))
     (swap! lines into ["" (str "> One waveform, two functions: more comms power ⇒ higher data rate but coarser sensing; "
                                "Pd degrades as noise rises (constant-false-alarm threshold).")
                        (str "> R0 simulation only — no live emission, no hardware (G7). Sensing is civilian "
                             "collision-avoidance/presence; fire-control / targeting is structurally absent (N1).")])
     (str/join "\n" @lines))))
