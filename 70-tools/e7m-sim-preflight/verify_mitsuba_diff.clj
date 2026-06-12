;; ported from 70-tools/e7m-sim-preflight/verify_mitsuba_diff.py (unit_refactor stage 0)
;; Mitsuba 3 differentiable rendering (LLVM autodiff backend).
(ns e7m-sim-preflight.verify-mitsuba-diff
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare out make-scene main)

(def out (java.nio.file.Paths/get-path (java.lang.System "/tmp")))

;; TODO: port-failed unit make_scene (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpscoj8fa4/scratch.clj:2:32: e)
;; def make_scene(chassis_rgb=(0.2, 0.55, 0.2)):
;;     return mi.load_dict({
;;         "type": "scene",
;;         "integrator": {"type": "prb", "max_depth": 4},
;;         "sensor": {
;;             "type": "perspective", "fov": 45,
;;             "to_world": mi.ScalarTransform4f().look_at(
;;                 origin=[3.5, -3.0, 2.0], target=[0, 0, 0.3], up=[0, 0, 1]),
;;             "film": {"type": "hdrfilm", "width": 128, "height": 96, "pixel_format": "rgb"},
;;             "sampler": {"type": "independent", "sample_count": 8},
;;         },
;;         "light": {
;;             "type": "point",
;;             "position": [4.0, -1.0, 5.0],
;;             "intensity": {"type": "spectrum", "value": 80.0},
;;         },
;;         "ground": {
;;             "type": "rectangle",
;;             "to_world": mi.ScalarTransform4f().scale([10, 10, 1]),
;;             "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": [0.3, 0.45, 0.2]}},
;;         },
;;         "chassis": {
;;             "type": "cube",
;;             "to_world": (mi.ScalarTransform4f().translate([0, 0, 0.30])
;;                          @ mi.ScalarTransform4f().scale([0.70, 0.45, 0.10])),
;;             "bsdf": {"type": "diffuse",
;;                      "reflectance": {"type": "rgb", "value": list(chassis_rgb)}},
;;         },
;;     })
(defn make-scene [& _]
  (throw (ex-info "TODO: port-failed" {:from "make_scene"})))

;; TODO: port-failed unit main (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpn3j7g4zc/scratch.clj:2:1: er)
;; def main() -> int:
;;     print(f"Mitsuba {mi.MI_VERSION}, variant: {mi.variant()}")
;; 
;;     # Target: bright orange-ish chassis
;;     target = make_scene(chassis_rgb=(0.85, 0.40, 0.10))
;;     target_img = mi.render(target, spp=16)
;;     mi.util.write_bitmap(str(OUT / "diff_target.png"), target_img)
;;     print(f"Target rendered: mean = {dr.mean(dr.ravel(target_img))[0]:.4f}")
;; 
;;     # Scene starts green; we optimize chassis color to match target (orange).
;;     scene = make_scene(chassis_rgb=(0.2, 0.55, 0.2))
;;     params = mi.traverse(scene)
;;     all_keys = list(params.keys())
;;     key = next((k for k in all_keys if "chassis" in k and "reflectance" in k and "value" in k), None)
;;     if key is None:
;;         chassis_keys = [k for k in all_keys if "chassis" in k]
;;         print("could not find chassis reflectance; chassis keys:", chassis_keys)
;;         return 1
;;     print(f"Optimizing parameter: '{key}'  init = {params[key]}")
;; 
;;     opt = mi.ad.Adam(lr=0.05)
;;     opt[key] = mi.Color3f(params[key])
;; 
;;     for it in range(8):
;;         params[key] = dr.clip(opt[key], 0.001, 0.999)
;;         params.update()
;;         img = mi.render(scene, params, spp=8, seed=it)
;;         loss = dr.mean(dr.square(dr.ravel(img) - dr.ravel(target_img)))
;;         dr.backward(loss)
;;         opt.step()
;;         c = opt[key]
;;         print(f"  iter {it}: chassis_rgb=({c.x[0]:.3f}, {c.y[0]:.3f}, {c.z[0]:.3f})  loss={loss[0]:.5f}")
;; 
;;     final_img = mi.render(scene, params, spp=32)
;;     mi.util.write_bitmap(str(OUT / "diff_final.png"), final_img)
;;     final_color = opt[key]
;;     print(f"\nFinal chassis color: ({final_color.x[0]:.3f}, {final_color.y[0]:.3f}, {final_color.z[0]:.3f})")
;;     print(f"Target chassis color: (0.850, 0.400, 0.100)")
;;     print(f"Wrote: {OUT / 'diff_target.png'}  +  {OUT / 'diff_final.png'}")
;;     print("\nMitsuba 3 differentiable rendering (PRB): OK")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

