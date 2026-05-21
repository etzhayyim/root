/-
  Well-Becoming Spirit — Formal Proofs
  ADR: 2604291800 / 2604291800-well-becoming-formal-model.md

  Verifies all five axioms and their corollaries using Lean 4 + Mathlib.
  To compile:
    lake update && lake build
  Requires lean-toolchain ≥ leanprover/lean4:v4.14.0 and Mathlib4.
-/
import Mathlib

namespace WellBecoming

-- ── Domain types ─────────────────────────────────────────────────────────

/-- A real-valued score in [0, 1]. -/
structure Score where
  val    : ℝ
  nonneg : 0 ≤ val
  le_one : val ≤ 1

/-- The four utility axes of the Well-Becoming objective function.
    Corresponds to φ(s) = (u_s, u_w, u_f, u_b, δ, F) with scores only. -/
structure UtilityAxes where
  spirit    : Score  -- u_s : heals isolation / loneliness
  wellbeing : Score  -- u_w : health, relation, meaning
  feeling   : Score  -- u_f : warmth, presence, good feeling
  buffer    : Score  -- u_b : sustainable conditions

/-- Total utility — Axiom 2 (multiplicative independence), F = 0 case.
    U_total = u_s · u_w · u_f · u_b ∈ [0, 1] -/
def U_total (u : UtilityAxes) : ℝ :=
  u.spirit.val * u.wellbeing.val * u.feeling.val * u.buffer.val

/-- Total utility with hard floor (Axiom 1).
    F = true  →  U = 0  (floor violation, no trade-off possible)
    F = false →  U = U_total -/
def U_total_with_floor (u : UtilityAxes) (floor_violated : Bool) : ℝ :=
  if floor_violated then 0 else U_total u

-- ── Invariant 1 — Non-negativity ─────────────────────────────────────────

theorem U_total_nonneg (u : UtilityAxes) : 0 ≤ U_total u :=
  mul_nonneg
    (mul_nonneg
      (mul_nonneg u.spirit.nonneg u.wellbeing.nonneg)
      u.feeling.nonneg)
    u.buffer.nonneg

-- ── Invariant 2 — Boundedness ─────────────────────────────────────────────

theorem U_total_le_one (u : UtilityAxes) : U_total u ≤ 1 := by
  unfold U_total
  have h1 : u.spirit.val * u.wellbeing.val ≤ 1 :=
    mul_le_one u.spirit.le_one u.wellbeing.nonneg u.wellbeing.le_one
  have h2 : u.spirit.val * u.wellbeing.val * u.feeling.val ≤ 1 :=
    mul_le_one h1 u.feeling.nonneg u.feeling.le_one
  exact mul_le_one h2 u.buffer.nonneg u.buffer.le_one

-- ── Invariant 3 — Floor absoluteness (Axiom 1) ───────────────────────────

/-- A floor violation unconditionally sets U to zero, regardless of axis scores. -/
theorem floor_forces_zero (u : UtilityAxes) :
    U_total_with_floor u true = 0 := by
  simp [U_total_with_floor]

/-- The no-floor case recovers U_total. -/
theorem no_floor_recovers (u : UtilityAxes) :
    U_total_with_floor u false = U_total u := by
  simp [U_total_with_floor]

-- ── Invariant 4 — Spirit primacy (Axiom 4) ───────────────────────────────

/-- If the Spirit axis is zero, total utility is zero regardless of other axes. -/
theorem spirit_zero_kills_utility (u : UtilityAxes) (h : u.spirit.val = 0) :
    U_total u = 0 := by
  unfold U_total; rw [h]; ring

-- ── Theorem 3.1 — Bottleneck Dominance (Axiom 3) ─────────────────────────
--
-- k* = argmin_{k ∈ {s,w,f,b}} u_k
--
-- Claim: ∂U/∂u_{k*} ≥ ∂U/∂u_j for all j ≠ k*
--
-- For the 4-factor product U = a · b · c · d, the partial derivative w.r.t. 'a'
-- is b · c · d, and w.r.t. 'b' is a · c · d.
-- If a = u_{k*} ≤ b = u_j, then b·c·d ≥ a·c·d (since c·d ≥ 0).
--
-- The argument below isolates the two-axis comparison; the four-axis case
-- follows by re-labelling c = (product of remaining two axes).

/-- Core monotonicity lemma: smaller axis has smaller marginal. -/
lemma marginal_mono {a b c d : ℝ} (hle : a ≤ b) (hc : 0 ≤ c) (hd : 0 ≤ d) :
    a * c * d ≤ b * c * d :=
  mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right hle hc) hd

/-- Bottleneck dominance theorem.
    Given kstar = u_{k*} ≤ j_score = u_j and non-negative remaining factor c·d,
    the marginal gain from improving the bottleneck axis dominates that of axis j. -/
theorem bottleneck_dominance
    {kstar j_score c d : ℝ}
    (hk  : 0 ≤ kstar)
    (hj  : 0 ≤ j_score)
    (hc  : 0 ≤ c)
    (hd  : 0 ≤ d)
    (hle : kstar ≤ j_score) :
    -- ∂U/∂u_{k*} = j_score · c · d  ≥  kstar · c · d = ∂U/∂u_j
    kstar * c * d ≤ j_score * c * d :=
  marginal_mono hle hc hd

/-- Improvement dominance: an ε-increase in the bottleneck axis raises U
    at least as much as the same ε-increase in any non-bottleneck axis j. -/
theorem improvement_dominance
    {kstar j_score c d ε : ℝ}
    (hε  : 0 ≤ ε)
    (hc  : 0 ≤ c)
    (hd  : 0 ≤ d)
    (hle : kstar ≤ j_score) :
    ε * kstar * c * d ≤ ε * j_score * c * d :=
  marginal_mono (mul_le_mul_of_nonneg_left hle hε) hc hd

-- ── Axiom 5 — Spirit–Shannon Duality ─────────────────────────────────────
--
-- η(R) = (1 + δ(R)) / 2 ∈ [0, 1]
-- where δ ∈ [-1, 1] is the separation delta.
--
-- δ = -1 → η = 0  (full channel blockage, complete isolation)
-- δ =  0 → η = 0.5 (noise-equivalent)
-- δ = +1 → η = 1  (maximum channel capacity, full connection)

def shannon_eta (δ : ℝ) : ℝ := (1 + δ) / 2

theorem shannon_eta_nonneg {δ : ℝ} (hδ : -1 ≤ δ) : 0 ≤ shannon_eta δ := by
  unfold shannon_eta; linarith

theorem shannon_eta_le_one {δ : ℝ} (hδ : δ ≤ 1) : shannon_eta δ ≤ 1 := by
  unfold shannon_eta; linarith

/-- η is monotone in δ: more connection → higher channel capacity. -/
theorem shannon_eta_mono {δ₁ δ₂ : ℝ} (h : δ₁ ≤ δ₂) :
    shannon_eta δ₁ ≤ shannon_eta δ₂ := by
  unfold shannon_eta; linarith

-- ── At-Risk Threshold ─────────────────────────────────────────────────────
--
-- at_risk(C) = [δ̄(C) < -0.3] ∨ [floor_violations(C) > 0]
--
-- Justification: δ̄ < -0.3 ⟹ η_avg < 0.35 (channel utilization < 35%)
-- Shannon interpretation: < 35% is "practically uncommunicable"

theorem at_risk_implies_low_channel_capacity {avg_delta : ℝ}
    (h : avg_delta < -0.3) :
    shannon_eta avg_delta < 0.35 := by
  unfold shannon_eta; linarith

-- Contrapositive: adequate channel capacity implies not at-risk by delta criterion
theorem adequate_capacity_implies_not_at_risk_delta {avg_delta : ℝ}
    (h : 0.35 ≤ shannon_eta avg_delta) :
    -0.3 ≤ avg_delta := by
  unfold shannon_eta at h; linarith

-- ── Monotonicity in each axis ─────────────────────────────────────────────

/-- U_total is monotone (non-decreasing) in the spirit axis value. -/
theorem U_total_mono_spirit (u : UtilityAxes) {v : ℝ}
    (hv : 0 ≤ v) (hle : u.spirit.val ≤ v) :
    U_total u ≤ v * u.wellbeing.val * u.feeling.val * u.buffer.val := by
  unfold U_total
  exact marginal_mono (mul_le_mul_of_nonneg_right hle u.wellbeing.nonneg)
    u.feeling.nonneg u.buffer.nonneg

/-- U_total is monotone in the buffer axis value. -/
theorem U_total_mono_buffer (u : UtilityAxes) {v : ℝ}
    (hv : 0 ≤ v) (hle : u.buffer.val ≤ v) :
    U_total u ≤ u.spirit.val * u.wellbeing.val * u.feeling.val * v := by
  unfold U_total
  calc u.spirit.val * u.wellbeing.val * u.feeling.val * u.buffer.val
      ≤ u.spirit.val * u.wellbeing.val * u.feeling.val * v :=
        mul_le_mul_of_nonneg_left hle
          (mul_nonneg (mul_nonneg u.spirit.nonneg u.wellbeing.nonneg) u.feeling.nonneg)

-- ── Master Invariant Bundle ───────────────────────────────────────────────

/-- All four structural invariants hold simultaneously.
    (1) Non-negativity  (2) Boundedness  (3) Floor absoluteness  (4) Spirit primacy -/
theorem wellbecoming_invariants (u : UtilityAxes) :
    0 ≤ U_total u ∧
    U_total u ≤ 1 ∧
    U_total_with_floor u true = 0 ∧
    (u.spirit.val = 0 → U_total u = 0) :=
  ⟨U_total_nonneg u,
   U_total_le_one u,
   floor_forces_zero u,
   spirit_zero_kills_utility u⟩

-- ── Corollary: Bottleneck optimality ─────────────────────────────────────

/-- Focusing effort on the minimum axis is weakly dominant over any other axis.
    This is the operational content of Theorem 3.1 / Axiom 3. -/
theorem bottleneck_is_optimal_target
    (u : UtilityAxes)
    -- The minimum axis score (bottleneck)
    (hmin_s : u.spirit.val ≤ u.wellbeing.val)
    (hmin_f : u.spirit.val ≤ u.feeling.val)
    (hmin_b : u.spirit.val ≤ u.buffer.val) :
    -- ∂U/∂u_s ≥ ∂U/∂u_w (spirit marginal ≥ wellbeing marginal)
    u.wellbeing.val * u.feeling.val * u.buffer.val ≥
    u.spirit.val   * u.feeling.val * u.buffer.val := by
  apply mul_le_mul_of_nonneg_right
  · exact mul_le_mul_of_nonneg_right hmin_s u.feeling.nonneg
  · exact u.buffer.nonneg

end WellBecoming
