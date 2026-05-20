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
    bytes32 internal constant ECONOMIC_TITHE_TO_PUBLIC_FUND_BPS = keccak256("economic.tithe_to_public_fund_bps");

    // ─── License (ADR-2605192200) ────────────────────────────────
    bytes32 internal constant LICENSE_BASE = keccak256("license.base");
    bytes32 internal constant LICENSE_CHARTER_RIDER_REQUIRED = keccak256("license.charter_rider_required");
    bytes32 internal constant LICENSE_CHARTER_RIDER_VERSION = keccak256("license.charter_rider_version");

    // ─── Three-tier enforcement (ADR-2605192230) ─────────────────
    bytes32 internal constant ENFORCEMENT_THREE_TIER = keccak256("enforcement.three_tier");
    bytes32 internal constant PHENOTYPE_NON_COMPLIANT_MULTIPLIER = keccak256("phenotype.non_compliant_multiplier");

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
}
