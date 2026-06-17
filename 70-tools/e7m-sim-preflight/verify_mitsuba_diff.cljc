;; ported from 70-tools/e7m-sim-preflight/verify_mitsuba_diff.py — real port replacing the
;; unit_refactor stage-0 "TODO: port-failed" stubs. NS fixed (root.* -> e7m-sim-preflight.*)
;; and the file is now .cljc.
;;
;; Mitsuba 3 differentiable rendering (LLVM autodiff backend).
;; Per ADR-2605261600 §3 non-symmetric advantages (b):
;;   > Mitsuba 3 differentiable rendering (inverse rendering for camera-attestation
;;   > consistency verification — not in Omniverse stack)
;;
;; FAITHFUL-PORT NOTE: the substance of `main` is a sequence of calls into the
;; Mitsuba 3 (C++) renderer + Dr.Jit autodiff + libLLVM — native libraries with NO
;; JVM/Clojure binding available in this environment. There is no pure-data algorithm
;; to reimplement: `mi.load_dict` / `mi.render` / `mi.traverse` / `mi.ad.Adam` /
;; `dr.backward` / `dr.clip` are all foreign-engine calls. So the render/optimize loop
;; stays behind a #?(:clj ...) host boundary that throws an HONEST "requires the mitsuba
;; + drjit native libs" error (strictly better than a generic "port-failed" stub).
;;
;; The genuinely pure part — `make-scene`, which builds the scene description as a
;; string-keyed data map exactly mirroring the Python dict (Python ':kw' keys kept as
;; strings) — IS ported faithfully and is the verifiable surface of this file.
;;
;; The Python "__main__" demo (sys.exit(main())) is intentionally omitted.
(ns e7m-sim-preflight.verify-mitsuba-diff
  "verify_mitsuba_diff.py — 1:1 Clojure port. Pure scene-description builder +
  native-render boundary. host file/render I/O behind #?(:clj ...)."
  (:require [clojure.string]))

;; OUT = Path(__file__).parent / "out" ; created at runtime under :clj.
(def ^:const out-dir "out")

;; default DRJIT_LIBLLVM_PATH the Python sets via os.environ.setdefault.
(def ^:const default-libllvm-path "/opt/homebrew/opt/llvm/lib/libLLVM.dylib")

;; ── pure: scene description ──────────────────────────────────────────────────
;; def make_scene(chassis_rgb=(0.2, 0.55, 0.2)):
;;     return mi.load_dict({ ... })
;; The dict is pure data; we return the same string-keyed map (the argument to
;; mi.load_dict). A "ScalarTransform4f" op is kept as a string-keyed op-descriptor
;; map (there is no native transform here to evaluate), faithfully recording the
;; same parameters the Python passed.
(defn- look-at [origin target up]
  {"op" "look_at" "origin" origin "target" target "up" up})

(defn- scale [v]
  {"op" "scale" "value" v})

(defn- translate [v]
  {"op" "translate" "value" v})

(defn- compose
  "mi.ScalarTransform4f() @ mi.ScalarTransform4f() — record the matmul chain."
  [a b]
  {"op" "matmul" "lhs" a "rhs" b})

(defn make-scene
  "Build the Mitsuba scene description dict (string-keyed, pure). Mirrors the Python
  `make_scene`; the returned map is exactly what `mi.load_dict` would receive."
  ([] (make-scene [0.2 0.55 0.2]))
  ([chassis-rgb]
   {"type" "scene"
    "integrator" {"type" "prb" "max_depth" 4}
    "sensor"
    {"type" "perspective" "fov" 45
     "to_world" (look-at [3.5 -3.0 2.0] [0 0 0.3] [0 0 1])
     "film" {"type" "hdrfilm" "width" 128 "height" 96 "pixel_format" "rgb"}
     "sampler" {"type" "independent" "sample_count" 8}}
    "light"
    {"type" "point"
     "position" [4.0 -1.0 5.0]
     "intensity" {"type" "spectrum" "value" 80.0}}
    "ground"
    {"type" "rectangle"
     "to_world" (scale [10 10 1])
     "bsdf" {"type" "diffuse" "reflectance" {"type" "rgb" "value" [0.3 0.45 0.2]}}}
    "chassis"
    {"type" "cube"
     "to_world" (compose (translate [0 0 0.30]) (scale [0.70 0.45 0.10]))
     "bsdf" {"type" "diffuse"
             "reflectance" {"type" "rgb" "value" (vec chassis-rgb)}}}}))

;; ── native boundary: differentiable render + optimize ────────────────────────
;; def main() -> int: ... renders the target, traverses params, runs the Adam
;; inverse-rendering loop, writes PNGs. Every line is a mitsuba/drjit native call.
;; No binding exists on this host → honest unsupported error, not a faked result.
(defn main
  "verify_mitsuba_diff main — runs the Mitsuba 3 PRB inverse-rendering optimization
  loop. Requires the native `mitsuba` + `drjit` libraries (+ libLLVM); these have no
  JVM/Clojure binding in this environment, so this entry point raises rather than
  return a fabricated result."
  [& _]
  #?(:clj
     (throw (ex-info
             (str "verify-mitsuba-diff/main requires the native mitsuba + drjit libraries "
                  "(libLLVM autodiff backend), which have no Clojure/JVM binding in this "
                  "environment. Run the Python reference (verify_mitsuba_diff.py) for the "
                  "differentiable-render loop. The pure scene description is available via "
                  "(make-scene) / (make-scene chassis-rgb).")
             {:from "main"
              :requires ["mitsuba" "drjit" "libLLVM"]
              :libllvm-path default-libllvm-path
              :out-dir out-dir
              :scene-builder `make-scene}))
     :default
     (throw (ex-info "verify-mitsuba-diff/main: native render unsupported on this host"
                     {:from "main" :requires ["mitsuba" "drjit" "libLLVM"]}))))
