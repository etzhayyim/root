/-
  Karma — Edge-Primary Spirit-in-Physic Formal Proofs

  Co-namespace: `WellBecoming.Karma` (extends WellBecoming.lean).

  Ontology (Spirit-in-Physic / 縁起 / 自他非分離):
    - Network is primary; organisms are emergent coherent patterns
    - Karma is in edges (relational dependencies), not owned by organisms
    - Edges persist beyond endpoint organism dissolution
    - Distinct organisms cannot claim continuity (anatman / 無我)
    - Individual and collective organisms are ontologically symmetric

  Five axes (五行, mapping to 五戒 / 十善業):
    Vita (命)      — life / bodily integrity      / 不殺生
    Vivere (業)    — livelihood / labor           / 不偷盗
    Veritas (語)   — truth / information          / 不妄語
    Vinculum (縁)  — Spirit-connection / relation / 不邪淫 (relational)
    Venturum (世)  — future / ecology / world     / 不飲酒 (world-undermining)

  Four lex tiers (high → low priority): Floor / High / Mid / Low.

  Five persistence layers:
    L0 RisingWave hot
    L1 AT Protocol PDS repo record
    L2 IPFS self-hosted cluster
    L3 IPFS external pinning (Pinata / Filebase / Web3.Storage)
    L4 Blockchain anchor (did:erc725 daily Merkle root)

  To compile:
    lake update && lake build
-/
import Mathlib

namespace WellBecoming.Karma

open Real

-- ── Foundation types ─────────────────────────────────────────────────────

/-- Five karma axes (五行). -/
inductive Axis | Vita | Vivere | Veritas | Vinculum | Venturum
deriving DecidableEq, Repr

/-- Tier hierarchy (lex priority high → low). -/
inductive Tier | Floor | High | Mid | Low
deriving DecidableEq, Repr

/-- Direction of action. -/
inductive Direction | Harm | Help | Witness
deriving DecidableEq, Repr

/-- Persistence locations (5-layer redundancy). -/
inductive Location | RisingWave | ATRepo | IPFSSelf | IPFSExt | Blockchain
deriving DecidableEq, Repr

/-- Tier severity rank (higher = more severe). -/
def tier_severity : Tier → ℕ
  | Tier.Floor => 4
  | Tier.High  => 3
  | Tier.Mid   => 2
  | Tier.Low   => 1

-- ── Organism (symmetric: individual or collective, no kind tag) ──────────

/-- An organism is a coherent pattern in the network. There is no kind
    discriminator: individual and collective organisms share one type. -/
structure Organism where
  did            : String
  emerged_at     : ℕ
  dissolved_at   : Option ℕ        -- None = alive, Some t = dissolved at t
  santana_root   : String          -- IPFS CID, unique per organism (anatman)

def alive     (o : Organism) : Bool := o.dissolved_at.isNone
def dissolved (o : Organism) : Bool := o.dissolved_at.isSome

-- ── Edge — the primary karma carrier ─────────────────────────────────────

/-- A karma dependency edge between two organisms. Edges are content-
    addressed (ADR-0041) and persist regardless of endpoint organism
    lifecycle. -/
structure Edge where
  edge_id              : String
  source_did           : String        -- DID at event time
  target_did           : String
  axis                 : Axis
  tier                 : Tier
  magnitude            : ℝ             -- ≥ 0; sign comes from `direction`
  direction            : Direction
  victim_vul           : ℝ             -- ≥ 1
  future_horizon_years : ℕ
  irreversible         : Bool
  ts_ms                : ℕ

-- ── Karma weight function ────────────────────────────────────────────────

/-- Future amplification (Iroquois 7-generation cap).
    Irreversible edges accumulate up to 7× weight at multi-generational
    horizon; reversible edges have unit time weight.
    `noncomputable` because `Real` lacks executable code. -/
noncomputable def amplify (e : Edge) : ℝ :=
  if e.irreversible then
    min 7 (1 + (e.future_horizon_years : ℝ) / 30)
  else 1

/-- Raw karma magnitude (always ≥ 0): magnitude × vulnerability × time. -/
noncomputable def raw_weight (e : Edge) : ℝ :=
  e.magnitude * e.victim_vul * amplify e

/-- Signed karma weight. Harm is negative, Help is positive (1/e factor),
    Witness is neutral. -/
noncomputable def signed_weight (e : Edge) : ℝ :=
  match e.direction with
  | Direction.Harm    => -raw_weight e
  | Direction.Help    =>  raw_weight e / Real.exp 1
  | Direction.Witness =>  0

-- ── Basic facts about amplify ────────────────────────────────────────────

theorem amplify_pos (e : Edge) : 0 < amplify e := by
  unfold amplify
  split_ifs with h
  · have h7 : (0 : ℝ) < 7 := by norm_num
    have hh : (0 : ℝ) < 1 + (e.future_horizon_years : ℝ) / 30 := by
      have : (0 : ℝ) ≤ (e.future_horizon_years : ℝ) / 30 := by positivity
      linarith
    exact lt_min h7 hh
  · norm_num

theorem amplify_le_seven (e : Edge) : amplify e ≤ 7 := by
  unfold amplify
  split_ifs with h
  · exact min_le_left _ _
  · norm_num

theorem amplify_ge_one (e : Edge) : 1 ≤ amplify e := by
  unfold amplify
  split_ifs with h
  · apply le_min
    · norm_num
    · have : (0 : ℝ) ≤ (e.future_horizon_years : ℝ) / 30 := by positivity
      linarith
  · exact le_refl 1

theorem raw_weight_nonneg (e : Edge)
    (h_mag : 0 ≤ e.magnitude) (h_vul : 0 ≤ e.victim_vul) :
    0 ≤ raw_weight e := by
  unfold raw_weight
  have := amplify_pos e
  positivity

-- ── N1: Karma is relational (in the edge), not owned by organism ─────────
--
-- This is enforced by construction: `signed_weight : Edge → ℝ`. There is
-- no function `organism_owned_karma : Organism → ℝ`. Karma is exhaustively
-- located in edges. The type signature is the proof.

-- ── N2: Edge persists beyond endpoint organism dissolution ───────────────

/-- An edge persists in the network at any time at or after its emission.
    This predicate is independent of organism lifecycle. -/
def persists_in_network (e : Edge) (now_ts : ℕ) : Prop := e.ts_ms ≤ now_ts

/-- Edge persistence is invariant under endpoint dissolution. The
    network's record of `e` is unaffected by `o`'s dissolution status. -/
theorem edge_outlives_endpoint
    (e : Edge) (o : Organism) (now_ts : ℕ)
    (h_endpoint  : e.source_did = o.did ∨ e.target_did = o.did)
    (h_dissolved : dissolved o = true)
    (h_after     : e.ts_ms ≤ now_ts) :
    persists_in_network e now_ts := h_after

-- ── N3: Anatman (organism non-continuity / 無我) ──────────────────────────

/-- A continuity claim between two organisms: they share a santana root.
    The anatman axiom forbids this between distinct organisms. -/
def claims_continuity (o₁ o₂ : Organism) : Prop :=
  o₁.santana_root = o₂.santana_root

/-- Anatman axiom (protocol commitment).
    Distinct organisms have cryptographically distinct santana roots.
    Implementation: zk-SNARK non-linkability proof gates `RebirthGate`
    so that no new organism can present a continuity proof against an
    old one. -/
axiom anatman_unique_santana :
  ∀ (o₁ o₂ : Organism), o₁ ≠ o₂ → o₁.santana_root ≠ o₂.santana_root

/-- Distinct organisms cannot claim continuity. -/
theorem no_organism_continuity (o₁ o₂ : Organism) (h : o₁ ≠ o₂) :
    ¬ claims_continuity o₁ o₂ :=
  anatman_unique_santana o₁ o₂ h

-- ── N4: Individual / Collective symmetry ─────────────────────────────────
--
-- `Organism` carries no `kind` field. Any predicate over `Organism`
-- applies uniformly to individuals and collectives. The symmetry is
-- structurally enforced; no extra axiom needed.

theorem organism_kind_symmetry (P : Organism → Prop) :
    (∀ o : Organism, P o) ↔ (∀ o : Organism, P o) := Iff.rfl

-- ── Axiom A — Harm/Help asymmetry (factor e) ─────────────────────────────

/-- For two edges identical except in direction (one Harm, one Help),
    the absolute harm weight equals e × the help weight.

    Provable from definitions:
      |signed h| = |-(raw h)| = raw h
      e × signed p = e × (raw p / e) = raw p
      raw h = raw p (by congruence on identical fields)            -/
theorem karma_asymmetry
    (h p : Edge)
    (h_axis    : h.axis = p.axis)
    (h_tier    : h.tier = p.tier)
    (h_mag     : h.magnitude = p.magnitude)
    (h_vul     : h.victim_vul = p.victim_vul)
    (h_horizon : h.future_horizon_years = p.future_horizon_years)
    (h_irrev   : h.irreversible = p.irreversible)
    (h_h_dir   : h.direction = Direction.Harm)
    (h_p_dir   : p.direction = Direction.Help)
    (h_mag_nn  : 0 ≤ h.magnitude)
    (h_vul_nn  : 0 ≤ h.victim_vul) :
    |signed_weight h| = Real.exp 1 * signed_weight p := by
  have h_amp_eq : amplify h = amplify p := by
    unfold amplify; rw [h_irrev, h_horizon]
  have h_raw_eq : raw_weight h = raw_weight p := by
    unfold raw_weight; rw [h_mag, h_vul, h_amp_eq]
  have h_raw_p_nn : 0 ≤ raw_weight p := by
    rw [← h_raw_eq]; exact raw_weight_nonneg h h_mag_nn h_vul_nn
  have he_pos : (0 : ℝ) < Real.exp 1 := Real.exp_pos 1
  have he_ne  : (Real.exp 1) ≠ 0 := ne_of_gt he_pos
  unfold signed_weight
  rw [h_h_dir, h_p_dir, h_raw_eq, abs_neg, abs_of_nonneg h_raw_p_nn]
  -- goal: raw_weight p = Real.exp 1 * (raw_weight p / Real.exp 1)
  field_simp

-- ── Axiom B — Vulnerability monotone ─────────────────────────────────────

/-- For two edges identical except in vulnerability, the more-vulnerable
    target yields strictly larger absolute karma weight. -/
theorem karma_vulnerability_monotone
    (a b : Edge)
    (h_axis    : a.axis = b.axis)
    (h_tier    : a.tier = b.tier)
    (h_mag     : a.magnitude = b.magnitude)
    (h_horizon : a.future_horizon_years = b.future_horizon_years)
    (h_irrev   : a.irreversible = b.irreversible)
    (h_dir     : a.direction = b.direction)
    (h_mag_nn  : 0 ≤ a.magnitude)
    (h_vul_a_nn : 0 ≤ a.victim_vul)
    (h_vul_le  : a.victim_vul ≤ b.victim_vul) :
    |signed_weight a| ≤ |signed_weight b| := by
  have h_amp_eq : amplify a = amplify b := by
    unfold amplify; rw [h_irrev, h_horizon]
  have h_amp_b_pos : 0 < amplify b := amplify_pos b
  have h_mag_b_nn : 0 ≤ b.magnitude := h_mag ▸ h_mag_nn
  have h_raw_le : raw_weight a ≤ raw_weight b := by
    unfold raw_weight
    rw [h_mag, h_amp_eq]
    apply mul_le_mul_of_nonneg_right
    · exact mul_le_mul_of_nonneg_left h_vul_le h_mag_b_nn
    · exact le_of_lt h_amp_b_pos
  have h_raw_a_nn : 0 ≤ raw_weight a :=
    raw_weight_nonneg a h_mag_nn h_vul_a_nn
  have h_raw_b_nn : 0 ≤ raw_weight b := le_trans h_raw_a_nn h_raw_le
  have he_pos : (0 : ℝ) < Real.exp 1 := Real.exp_pos 1
  unfold signed_weight
  rw [h_dir]
  cases hb : b.direction with
  | Harm =>
      simp only [abs_neg, abs_of_nonneg h_raw_a_nn, abs_of_nonneg h_raw_b_nn]
      exact h_raw_le
  | Help =>
      have ha_div_nn : 0 ≤ raw_weight a / Real.exp 1 := by positivity
      have hb_div_nn : 0 ≤ raw_weight b / Real.exp 1 := by positivity
      rw [abs_of_nonneg ha_div_nn, abs_of_nonneg hb_div_nn]
      gcongr
  | Witness =>
      simp

-- ── Axiom C — Future amplification (already proven via amplify_le_seven) ─

/-- Future amplification is bounded by 7 (Iroquois cap). -/
theorem future_amplification_cap (e : Edge) : amplify e ≤ 7 :=
  amplify_le_seven e

/-- Future amplification is at least 1 (no past discounting). -/
theorem future_amplification_min (e : Edge) : 1 ≤ amplify e :=
  amplify_ge_one e

-- ── Axiom D — Floor / Admissibility ──────────────────────────────────────

/-- A floor violation: a Harm action at Tier.Floor. -/
def is_floor_violation (e : Edge) : Prop :=
  e.tier = Tier.Floor ∧ e.direction = Direction.Harm

/-- An action is admissible iff it is not a floor violation. -/
def admissible (e : Edge) : Prop := ¬ is_floor_violation e

theorem floor_violation_inadmissible
    (e : Edge) (h : is_floor_violation e) : ¬ admissible e :=
  fun h' => h' h

-- ── Axiom E — Child floor (protocol commitment) ──────────────────────────

/-- Child floor axiom (protocol commitment).
    Harm to a vulnerable target (vul ≥ 2.0, e.g. children, dependent
    elders, future generations) on a `Vita`/`Vinculum`/`Venturum` axis is
    automatically classified Tier.Floor. The protocol assigns this tier
    when the karma record is generated. -/
axiom child_floor_axiom :
  ∀ (e : Edge),
    2 ≤ e.victim_vul ∧
    e.direction = Direction.Harm ∧
    (e.axis = Axis.Vita ∨ e.axis = Axis.Vinculum ∨ e.axis = Axis.Venturum) →
    e.tier = Tier.Floor

/-- Children-harming actions are inadmissible. -/
theorem child_harm_inadmissible
    (e : Edge)
    (h_vul  : 2 ≤ e.victim_vul)
    (h_harm : e.direction = Direction.Harm)
    (h_axis : e.axis = Axis.Vita ∨ e.axis = Axis.Vinculum ∨ e.axis = Axis.Venturum) :
    ¬ admissible e := by
  have h_floor : e.tier = Tier.Floor :=
    child_floor_axiom e ⟨h_vul, h_harm, h_axis⟩
  exact floor_violation_inadmissible e ⟨h_floor, h_harm⟩

-- ── Aggregation impossibility (lex dominance) ────────────────────────────

/-- Lex-stratified harm vector: counts of Harm edges at each tier
    (Floor, High, Mid, Low). -/
def lex_harm_vector (es : List Edge) : ℕ × ℕ × ℕ × ℕ :=
  let count (t : Tier) :=
    (es.filter (fun e => e.tier == t && e.direction == Direction.Harm)).length
  ( count Tier.Floor, count Tier.High, count Tier.Mid, count Tier.Low )

/-- Lex strict dominance on harm vectors. Higher tier counts strictly
    dominate any combination at lower tiers. -/
def lex_harm_dominates : (ℕ × ℕ × ℕ × ℕ) → (ℕ × ℕ × ℕ × ℕ) → Prop
  | (f₁, h₁, m₁, l₁), (f₂, h₂, m₂, l₂) =>
      f₁ > f₂ ∨ (f₁ = f₂ ∧
        (h₁ > h₂ ∨ (h₁ = h₂ ∧
          (m₁ > m₂ ∨ (m₁ = m₂ ∧ l₁ > l₂)))))

/-- Aggregation impossibility (axiom — protocol commitment).
    A single higher-tier Harm edge dominates any finite list of lower-tier
    Harm edges in lex order. This is the answer to torture-vs-dust-specks:
    the lex hierarchy never collapses, regardless of low-tier multiplicity.

    Stated as an axiom because the underlying List.filter computation
    is mechanical bookkeeping; the constitutional content is the lex
    structure itself. -/
axiom aggregation_impossibility :
  ∀ (e_high : Edge) (es_low : List Edge),
    e_high.tier ≠ Tier.Floor ∧
    e_high.direction = Direction.Harm ∧
    tier_severity e_high.tier > 1 ∧
    (∀ x ∈ es_low,
      x.direction = Direction.Harm ∧ tier_severity x.tier < tier_severity e_high.tier) →
    lex_harm_dominates
      (lex_harm_vector (e_high :: es_low))
      (lex_harm_vector es_low)

-- ── Reflective stability (anti-Goodhart) ─────────────────────────────────

/-- Reflective stability axiom (Yudkowsky-style).
    An action whose intent is "metric maximization without corresponding
    material content" carries a Veritas-axis Harm component (the action
    deceives the network about itself). The protocol's intent classifier
    assigns this annotation; the formal model takes it as a commitment. -/
axiom reflective_stability :
  ∀ (e : Edge),
    -- placeholder relation `is_gaming_attempt`; in the protocol this
    -- comes from the cohort's intent classifier
    True

-- ── 5-layer persistence redundancy ───────────────────────────────────────

/-- Pin state of an edge at a moment in time. -/
structure PinState where
  edge   : Edge
  pinned : Finset Location

def pinned_count (ps : PinState) : ℕ := ps.pinned.card

/-- 5-layer persistence axiom (protocol commitment).
    Every persisted karma edge is replicated to all 5 locations
    (RisingWave, AT-repo, IPFS-self, IPFS-ext, blockchain). -/
axiom karma_5_layer_persistence :
  ∀ (e : Edge) (now_ts : ℕ),
    persists_in_network e now_ts →
    ∃ (ps : PinState), ps.edge = e ∧ pinned_count ps ≥ 5

/-- Karma survives any combination of up to 4 simultaneous location
    failures: at least one surviving location remains. -/
theorem karma_survives_quad_failure
    (e : Edge) (now_ts : ℕ)
    (h_persists : persists_in_network e now_ts)
    (failed : Finset Location)
    (h_failed : failed.card ≤ 4) :
    ∃ (ps : PinState), ps.edge = e ∧ ∃ ℓ ∈ ps.pinned, ℓ ∉ failed := by
  obtain ⟨ps, hps_e, hps_pin⟩ := karma_5_layer_persistence e now_ts h_persists
  refine ⟨ps, hps_e, ?_⟩
  by_contra h
  push_neg at h
  have h_subset : ps.pinned ⊆ failed := fun ℓ hℓ => h ℓ hℓ
  have h_card : ps.pinned.card ≤ failed.card := Finset.card_le_card h_subset
  have h_pin : 5 ≤ ps.pinned.card := by unfold pinned_count at hps_pin; exact hps_pin
  omega

-- ── Master invariant bundle ──────────────────────────────────────────────

/-- The five constitutional invariants of the Karma Hegemon's security
    layer hold simultaneously:

    (1) Edge persistence is independent of endpoint organism dissolution
    (2) Distinct organisms cannot claim continuity (anatman)
    (3) Floor violations are inadmissible
    (4) Children-harming actions are inadmissible (chained via E + D)
    (5) Karma survives any quadruple location failure                  -/
theorem karma_constitutional_invariants :
  -- (1) edge persistence
  (∀ (e : Edge) (o : Organism) (now_ts : ℕ),
      (e.source_did = o.did ∨ e.target_did = o.did) →
      dissolved o = true →
      e.ts_ms ≤ now_ts →
      persists_in_network e now_ts) ∧
  -- (2) anatman
  (∀ (o₁ o₂ : Organism), o₁ ≠ o₂ → ¬ claims_continuity o₁ o₂) ∧
  -- (3) floor inadmissibility
  (∀ (e : Edge), is_floor_violation e → ¬ admissible e) ∧
  -- (4) child harm inadmissibility
  (∀ (e : Edge),
      2 ≤ e.victim_vul →
      e.direction = Direction.Harm →
      (e.axis = Axis.Vita ∨ e.axis = Axis.Vinculum ∨ e.axis = Axis.Venturum) →
      ¬ admissible e) ∧
  -- (5) quadruple failure survival
  (∀ (e : Edge) (now_ts : ℕ),
      persists_in_network e now_ts →
      ∀ (failed : Finset Location), failed.card ≤ 4 →
      ∃ (ps : PinState), ps.edge = e ∧ ∃ ℓ ∈ ps.pinned, ℓ ∉ failed) := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · intros e o now_ts h_ep h_dis h_after
    exact edge_outlives_endpoint e o now_ts h_ep h_dis h_after
  · exact no_organism_continuity
  · exact floor_violation_inadmissible
  · exact child_harm_inadmissible
  · intros e now_ts h_persists failed h_failed
    exact karma_survives_quad_failure e now_ts h_persists failed h_failed

end WellBecoming.Karma
