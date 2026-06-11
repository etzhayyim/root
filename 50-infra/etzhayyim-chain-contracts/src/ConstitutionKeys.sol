// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

/**
 * @title ConstitutionKeys
 * @notice Canonical bytes32 keys for {Constitution} constants and mutables.
 *
 *         Single source of truth for the constitutional vocabulary. All
 *         contracts that read from Constitution (TitheRouter,
 *         ChartersComplianceRegistry, LandRegistry, KishaStream, etc.) MUST
 *         use these constants instead of inline keccak256 calls — drift
 *         would silently break cross-contract reads.
 *
 * @dev Per ADR-2605192100 §2 (Mission Charter constitutional constants).
 *      Initialized at deploy time via Deploy.s.sol _constants() /
 *      _mutables() helpers.
 */
library ConstitutionKeys {
    // ============================================================
    //  CONSTANTS (immutable forever — change = founding new religion)
    // ============================================================

    // ─── Original ADR-2605172300 constants ────────────────────────
    bytes32 internal constant ONE_SBT_ONE_VOTE = keccak256("one_sbt_one_vote");
    bytes32 internal constant NO_TRANSFERABLE_SHARE = keccak256("no_transferable_share");
    bytes32 internal constant LICENSE = keccak256("license");
    bytes32 internal constant PHENOTYPE_MIN_BPS = keccak256("phenotype_min_bps");
    bytes32 internal constant PHENOTYPE_MAX_BPS = keccak256("phenotype_max_bps");
    bytes32 internal constant KAPPA_FLOOR_BPS = keccak256("kappa_floor_bps");
    bytes32 internal constant KAPPA_CEILING_BPS = keccak256("kappa_ceiling_bps");
    bytes32 internal constant QUORUM_FLOOR_BPS = keccak256("quorum_floor_bps");

    // ─── Mission Charter (ADR-2605192100 §1.1-§1.7) ──────────────
    bytes32 internal constant MISSION_LABOR_LIBERATION = keccak256("mission.labor_liberation");
    bytes32 internal constant MISSION_ROBOTICS_UNIVERSAL = keccak256("mission.robotics_universal");
    bytes32 internal constant MISSION_IP_FREE_RELEASE = keccak256("mission.ip_free_release");
    bytes32 internal constant MISSION_DISINTERMEDIATION = keccak256("mission.disintermediation");
    bytes32 internal constant MISSION_SPECIALIST_ANTI_GATEKEEPING = keccak256("mission.specialist_anti_gatekeeping");

    // ─── Religious ontology (ADR-2605192100 §1.8-§1.10) ──────────
    bytes32 internal constant MISSION_ANTI_INDIVIDUALISM = keccak256("mission.anti_individualism");
    bytes32 internal constant MISSION_MULTI_GENERATIONAL_PRIORITY = keccak256("mission.multi_generational_priority");
    bytes32 internal constant MISSION_MULTI_GENERATIONAL_HORIZON_YEARS = keccak256("mission.multi_generational_horizon_years");
    bytes32 internal constant MISSION_WELLBECOMING_PRIORITY = keccak256("mission.wellbecoming_priority");

    // ─── Land + State + Force (ADR-2605192100 §1.11-§1.12) ───────
    bytes32 internal constant MISSION_LAND_AS_RELIGIOUS_TRUST = keccak256("mission.land_as_religious_trust");
    bytes32 internal constant MISSION_PARALLEL_GOVERNANCE_TO_STATE = keccak256("mission.parallel_governance_to_state");
    bytes32 internal constant MISSION_TRANSPARENT_FORCE_ONLY = keccak256("mission.transparent_force_only");
    bytes32 internal constant MISSION_PROPRIETARY_FORCE_DESIGN_PROHIBITED = keccak256("mission.proprietary_force_design_prohibited");
    bytes32 internal constant MISSION_FORCE_REQUIRES_SBT_VOTE = keccak256("mission.force_requires_sbt_vote");
    bytes32 internal constant MISSION_NO_STATE_MILITARY_ALLIANCE = keccak256("mission.no_state_military_alliance");

    // ─── Eros / Gore (ADR-2605192100 §1.13) ──────────────────────
    bytes32 internal constant MISSION_EROS_PERMITTED = keccak256("mission.eros_permitted");
    bytes32 internal constant MISSION_GORE_PROHIBITED = keccak256("mission.gore_prohibited");

    // ─── Lineage + Canon (ADR-2605192100 §1.14-§1.15) ────────────
    bytes32 internal constant MISSION_LINEAGE_JAPANESE_PROTESTANT = keccak256("mission.lineage_japanese_protestant");
    bytes32 internal constant MISSION_ESCHATOLOGICAL = keccak256("mission.eschatological");
    bytes32 internal constant MISSION_REVELATION_IN_CANON = keccak256("mission.revelation_in_canon");
    bytes32 internal constant MISSION_CONTINUOUS_BECOMING = keccak256("mission.continuous_becoming");

    // ─── Governance extensions (ADR-2605192100 + 2605192300) ─────
    bytes32 internal constant GOVERNANCE_FUTURE_GENERATIONS_THIRD_PARTY_BENEFICIARY = keccak256("governance.future_generations_third_party_beneficiary");

    // ─── Economic hard rules (ADR-2605192115 + 2605192130) ───────
    bytes32 internal constant ECONOMIC_NON_PROFIT_ONLY = keccak256("economic.non_profit_only");
    bytes32 internal constant ECONOMIC_DONATION_ONLY = keccak256("economic.donation_only");
    bytes32 internal constant ECONOMIC_NO_ADVERTISING = keccak256("economic.no_advertising");
    // DEPRECATED by ADR-2606062100 §4: the pinned 10% tithe constant is retired in
    // favor of ECONOMIC_TITHE_REDISTRIBUTION_EXISTS (Tier-0 bool) + TITHE_FLOOR_BPS
    // / TITHE_CEILING_BPS (Tier-0 band) + TITHE_BPS (Tier-2 mutable rate). Symbol
    // retained for historical reference only; no longer deployed as a constant.
    bytes32 internal constant ECONOMIC_TITHE_TO_PUBLIC_FUND_BPS = keccak256("economic.tithe_to_public_fund_bps");

    // ─── License (ADR-2605192200) ────────────────────────────────
    bytes32 internal constant LICENSE_BASE = keccak256("license.base");
    bytes32 internal constant LICENSE_CHARTER_RIDER_REQUIRED = keccak256("license.charter_rider_required");
    // NOTE: LICENSE_CHARTER_RIDER_VERSION moved to MUTABLES (ADR-2606062100 §4) —
    // see the Tier-2 reclassification block below.

    // ─── Three-tier enforcement (ADR-2605192230) ─────────────────
    bytes32 internal constant ENFORCEMENT_THREE_TIER = keccak256("enforcement.three_tier");
    // L3 enforcement floor: a Non-Aligned Entity's benefit multiplier = 0.
    // RECLASSIFIED to a CONSTANT (Tier-0) by ADR-2606062100 §4 — was mis-deployed
    // as a MUTABLE ("ratcheting allowed"). The floor is constitutional, not tunable.
    bytes32 internal constant PHENOTYPE_NON_COMPLIANT_MULTIPLIER = keccak256("phenotype.non_compliant_multiplier");

    // ─── Tier-0 Priority + permanent memory (ADR-2606062100 §1-§2) ───
    // The Charter locks PRIORITIES (existence/ordering bools), not specific
    // numbers or named policies. These are fork-only (true 改定不可).
    bytes32 internal constant PRIORITY_WELLBECOMING_OVER_WELLBEING = keccak256("priority.wellbecoming_over_wellbeing");
    bytes32 internal constant PRIORITY_MULTIGEN_OVER_CURRENT = keccak256("priority.multigen_over_current");
    bytes32 internal constant PRIORITY_COLLECTIVE_OVER_INDIVIDUAL = keccak256("priority.collective_over_individual");
    // Permanent-memory doctrine (神の監視 / お天道様は見ており人は忘れない):
    // no right to be forgotten; record kept perpetually (append-only Datom log,
    // 非終末論); deeds plaintext-public, intimate spaces encrypted-retained.
    bytes32 internal constant MEMORY_RIGHT_TO_ERASURE_DENIED = keccak256("memory.right_to_erasure_denied");
    bytes32 internal constant MEMORY_PERMANENT_RECORD = keccak256("memory.permanent_record");
    bytes32 internal constant MEMORY_DEEDS_PUBLIC_INTIMATE_ENCRYPTED = keccak256("memory.deeds_public_intimate_encrypted");
    // Tithe: Tier-0 locks that redistribution EXISTS + its band; the RATE is Tier-2
    // (tithe_bps). The old pinned constant economic.tithe_to_public_fund_bps=1000 is
    // retired by ADR-2606062100 §4 in favor of exists + floor/ceiling + mutable rate.
    bytes32 internal constant ECONOMIC_TITHE_REDISTRIBUTION_EXISTS = keccak256("economic.tithe_redistribution_exists");
    bytes32 internal constant TITHE_FLOOR_BPS = keccak256("tithe_floor_bps");
    bytes32 internal constant TITHE_CEILING_BPS = keccak256("tithe_ceiling_bps");

    // ─── kawase-yui remittance pool (ADR-2605282200) ─────────────
    // kawase.max_band_bps is the Chainlink mid-market ±band tolerance
    // (G4). Default 50 = ±0.5%. Out-of-band halts all match cells until
    // Council Lv6+ ≥3 resumes. Constitutional (not mutable) because the
    // mid-market-only invariant pins the religious-corp on the non-spread
    // side of FX (Charter §2(b) speculative finance prohibition).
    bytes32 internal constant KAWASE_MAX_BAND_BPS = keccak256("kawase.max_band_bps");

    // ─── Land waqf-equivalent reaffirmation (ADR-2605192245) ─────
    // (placeholder for future LAND_INALIENABLE key — kept here to
    // anchor the section ordering)

    // ============================================================
    //  MUTABLES (governance-changeable within constant bounds)
    // ============================================================

    // ─── Original ADR-2605172300 mutables ────────────────────────
    bytes32 internal constant KISHA_BASE_RATE = keccak256("kisha_base_rate");
    bytes32 internal constant KAPPA_BPS = keccak256("kappa_bps");
    bytes32 internal constant TIER_LIQUID_BPS = keccak256("tier_liquid_bps");
    bytes32 internal constant TIER_RESERVE_BPS = keccak256("tier_reserve_bps");
    bytes32 internal constant TIER_CORPUS_BPS = keccak256("tier_corpus_bps");
    bytes32 internal constant QUORUM_BPS = keccak256("quorum_bps");
    bytes32 internal constant ACTIVE_WINDOW_SECS = keccak256("active_window_secs");
    bytes32 internal constant TIMELOCK_SECS = keccak256("timelock_secs");

    // ─── Tier-2 parameters reclassified by ADR-2606062100 §4 ─────
    // tithe_bps: the tithe RATE (init 1000 = 10%), governance-mutable within
    //   the Tier-0 [TITHE_FLOOR_BPS, TITHE_CEILING_BPS] band. TitheRouter reads
    //   this via getMutable. (Was the pinned constant tithe_to_public_fund_bps.)
    // license.charter_rider_version: version string, mutable (a parameter, not a
    //   priority). (Was a fork-only constant — could not track Rider amendments.)
    // license.charter_rider_text_hash: keccak256 of the canonical Rider text; the
    //   on-chain anchor for Rider integrity. Updated only via the Lv7+
    //   priority-conformance path (off-chain governed until a native Tier-1
    //   contract path exists — ADR-2606062100 Alt-E). Initial = 0, wired
    //   post-ratification like the reference addresses.
    bytes32 internal constant TITHE_BPS = keccak256("tithe_bps");
    bytes32 internal constant LICENSE_CHARTER_RIDER_VERSION = keccak256("license.charter_rider_version");
    bytes32 internal constant LICENSE_CHARTER_RIDER_TEXT_HASH = keccak256("license.charter_rider_text_hash");

    // ─── Reference addresses (set initially = 0, updated via governance) ─
    // These point to contracts that depend on Constitution. They are
    // mutable to allow controlled upgrade paths via governance vote +
    // timelock, but the default address(0) state forces deploy-time
    // wiring to be explicit.
    bytes32 internal constant PUBLIC_FUND_SAFE_ADDRESS = keccak256("public_fund.safe_address");
    bytes32 internal constant CHARTERS_COMPLIANCE_REGISTRY_ADDRESS = keccak256("charters_compliance.registry_address");
    bytes32 internal constant TITHE_ROUTER_ADDRESS = keccak256("tithe_router.address");
    bytes32 internal constant LAND_REGISTRY_ADDRESS = keccak256("land_registry.address");
    bytes32 internal constant FORCE_AUTHORIZATION_ADDRESS = keccak256("force_authorization.address");
    bytes32 internal constant PUBLIC_FUND_GOVERNANCE_ADDRESS = keccak256("public_fund.governance_address");

    // ─── kawase-yui remittance pool mutables (ADR-2605282200) ────
    // Per-member monthly cap denominated in USD minor units (6 decimals
    // matching USDC). Council Lv6+ ≥3 may adjust within R-cycle bounds:
    //   R1 default = 1_000_000_000      (= $1_000.00)
    //   R2         = 5_000_000_000      (= $5_000.00)
    //   R3         = 25_000_000_000     (= $25_000.00)
    // KawaseYuiPool reads this at deposit time; reverts on cap breach (G9).
    bytes32 internal constant KAWASE_PER_MONTH_CAP_USD_MINOR = keccak256("kawase.per_month_cap_usd_minor");
}
