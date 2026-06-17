(ns ibuki.methods.test-heir
  "moyai heir-decay — Wellbecoming gradient → 子・孫 priority (ADR-2606172000)."
  (:require [clojure.test :refer [deftest is]]
            [ibuki.methods.heir :as heir]))

(deftest only-a-positive-becoming-mints
  ;; you cannot gift a gain you did not make
  (is (= [] (:heirs (heir/heir-shares 0))))
  (is (= [] (:heirs (heir/heir-shares -20))))
  (is (zero? (:minted (heir/heir-shares -20)))))

(deftest forward-flow-is-conserved-and-generational
  (let [{:keys [self heirs minted]} (heir/heir-shares 100)]
    ;; present keeps only the subsistence floor (子孫 priority — present is not the terminus)
    (is (= 20.0 self))
    (is (= 80.0 minted))
    ;; the heirs together receive EXACTLY the forward flow (nothing created/lost — circular)
    (is (< (Math/abs (- 80.0 (reduce + (map :share heirs)))) 1e-9))
    ;; three generations: 子 / 孫 / 曾孫, each decaying (child gets most)
    (is (= [1 2 3] (map :generation heirs)))
    (is (> (:share (nth heirs 0)) (:share (nth heirs 1)) (:share (nth heirs 2))))))

(deftest datoms-are-edge-primary-no-soul-score
  (let [dms (heir/heir-datoms "ibuki" 100 {:beat 7 :as-of 7})]
    ;; lineage edges carry generation + share, marked non-transferable; NEVER a balance/score
    (is (some #(= ":heir/generation" (nth % 2)) dms))
    (is (some #(= ":heir/non-transferable" (nth % 2)) dms))
    (is (not-any? #(re-find #"score|level|balance" (str (nth % 2))) dms))))
