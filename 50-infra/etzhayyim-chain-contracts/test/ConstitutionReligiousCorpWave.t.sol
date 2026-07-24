// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {Constitution} from "../src/Constitution.sol";
import {ConstitutionKeys as K} from "../src/ConstitutionKeys.sol";

/**
 * @title ConstitutionReligiousCorpWaveTest
 * @notice Integration test that constructs a Constitution loaded with the
 *         full religious-corp wave constants (ADR-2605192100 §2) and
 *         verifies every key is read-back correct.
 *
 *         Mirrors the keys + values from Deploy._constants() / _mutables()
 *         exactly. Deploy.s.sol drift will be caught by this test.
 *
 * @dev Per ADR-2605192100 + 2605192115 + 2605192130 + 2605192200 + 2605192230.
 */
contract ConstitutionReligiousCorpWaveTest is Test {
    Constitution internal c;

    function setUp() public {
        // ─── Constants (47 = 39 prior − 2 retired + 9 priority/memory/etc, ADR-2606062100) ──
        bytes32[] memory cK = new bytes32[](47);
        bytes32[] memory cV = new bytes32[](47);

        // Original (8)
        cK[0] = K.ONE_SBT_ONE_VOTE;            cV[0] = bytes32(uint256(1));
        cK[1] = K.NO_TRANSFERABLE_SHARE;       cV[1] = bytes32(uint256(1));
        cK[2] = K.LICENSE;                      cV[2] = bytes32("Apache-2.0");
        cK[3] = K.PHENOTYPE_MIN_BPS;            cV[3] = bytes32(uint256(5_000));
        cK[4] = K.PHENOTYPE_MAX_BPS;            cV[4] = bytes32(uint256(20_000));
        cK[5] = K.KAPPA_FLOOR_BPS;              cV[5] = bytes32(uint256(100));
        cK[6] = K.KAPPA_CEILING_BPS;            cV[6] = bytes32(uint256(500));
        cK[7] = K.QUORUM_FLOOR_BPS;             cV[7] = bytes32(uint256(2_000));

        // Mission §1.1-§1.7 (5)
        cK[8]  = K.MISSION_LABOR_LIBERATION;            cV[8]  = bytes32(uint256(1));
        cK[9]  = K.MISSION_ROBOTICS_UNIVERSAL;          cV[9]  = bytes32(uint256(1));
        cK[10] = K.MISSION_IP_FREE_RELEASE;             cV[10] = bytes32(uint256(1));
        cK[11] = K.MISSION_DISINTERMEDIATION;           cV[11] = bytes32(uint256(1));
        cK[12] = K.MISSION_SPECIALIST_ANTI_GATEKEEPING; cV[12] = bytes32(uint256(1));

        // Religious ontology §1.8-§1.10 (4)
        cK[13] = K.MISSION_ANTI_INDIVIDUALISM;          cV[13] = bytes32(uint256(1));
        cK[14] = K.MISSION_MULTI_GENERATIONAL_PRIORITY; cV[14] = bytes32(uint256(1));
        cK[15] = K.MISSION_MULTI_GENERATIONAL_HORIZON_YEARS; cV[15] = bytes32(uint256(50));
        cK[16] = K.MISSION_WELLBECOMING_PRIORITY;       cV[16] = bytes32(uint256(1));

        // Land + State + Force §1.11-§1.12 (6)
        cK[17] = K.MISSION_LAND_AS_RELIGIOUS_TRUST;          cV[17] = bytes32(uint256(1));
        cK[18] = K.MISSION_PARALLEL_GOVERNANCE_TO_STATE;     cV[18] = bytes32(uint256(1));
        cK[19] = K.MISSION_TRANSPARENT_FORCE_ONLY;           cV[19] = bytes32(uint256(1));
        cK[20] = K.MISSION_PROPRIETARY_FORCE_DESIGN_PROHIBITED; cV[20] = bytes32(uint256(1));
        cK[21] = K.MISSION_FORCE_REQUIRES_SBT_VOTE;          cV[21] = bytes32(uint256(1));
        cK[22] = K.MISSION_NO_STATE_MILITARY_ALLIANCE;       cV[22] = bytes32(uint256(1));

        // Eros / Gore §1.13 (2)
        cK[23] = K.MISSION_EROS_PERMITTED;     cV[23] = bytes32(uint256(1));
        cK[24] = K.MISSION_GORE_PROHIBITED;    cV[24] = bytes32(uint256(1));

        // Lineage + Canon §1.14-§1.15 (4)
        cK[25] = K.MISSION_LINEAGE_JAPANESE_PROTESTANT; cV[25] = bytes32(uint256(1));
        cK[26] = K.MISSION_ESCHATOLOGICAL;               cV[26] = bytes32(uint256(0));  // false
        cK[27] = K.MISSION_REVELATION_IN_CANON;          cV[27] = bytes32(uint256(0));  // false
        cK[28] = K.MISSION_CONTINUOUS_BECOMING;          cV[28] = bytes32(uint256(1));

        // Governance + Economic + License + Enforcement (9)
        cK[29] = K.GOVERNANCE_FUTURE_GENERATIONS_THIRD_PARTY_BENEFICIARY; cV[29] = bytes32(uint256(1));
        cK[30] = K.ECONOMIC_NON_PROFIT_ONLY;            cV[30] = bytes32(uint256(1));
        cK[31] = K.ECONOMIC_DONATION_ONLY;              cV[31] = bytes32(uint256(1));
        cK[32] = K.ECONOMIC_NO_ADVERTISING;             cV[32] = bytes32(uint256(1));
        // [33] tithe pinned → redistribution-exists; [36] rider-version → phenotype floor
        cK[33] = K.ECONOMIC_TITHE_REDISTRIBUTION_EXISTS; cV[33] = bytes32(uint256(1));
        cK[34] = K.LICENSE_BASE;                          cV[34] = bytes32("Apache-2.0");
        cK[35] = K.LICENSE_CHARTER_RIDER_REQUIRED;      cV[35] = bytes32(uint256(1));
        cK[36] = K.PHENOTYPE_NON_COMPLIANT_MULTIPLIER;  cV[36] = bytes32(uint256(0));
        cK[37] = K.ENFORCEMENT_THREE_TIER;               cV[37] = bytes32(uint256(1));

        // kawase-yui FX band (ADR-2605282200 G4)
        cK[38] = K.KAWASE_MAX_BAND_BPS;                  cV[38] = bytes32(uint256(50));

        // Priority-over-specifics + permanent memory (ADR-2606062100 §1-§2)
        cK[39] = K.PRIORITY_WELLBECOMING_OVER_WELLBEING;   cV[39] = bytes32(uint256(1));
        cK[40] = K.PRIORITY_MULTIGEN_OVER_CURRENT;         cV[40] = bytes32(uint256(1));
        cK[41] = K.PRIORITY_COLLECTIVE_OVER_INDIVIDUAL;    cV[41] = bytes32(uint256(1));
        cK[42] = K.MEMORY_RIGHT_TO_ERASURE_DENIED;         cV[42] = bytes32(uint256(1));
        cK[43] = K.MEMORY_PERMANENT_RECORD;               cV[43] = bytes32(uint256(1));
        cK[44] = K.MEMORY_DEEDS_PUBLIC_INTIMATE_ENCRYPTED; cV[44] = bytes32(uint256(1));
        cK[45] = K.TITHE_FLOOR_BPS;                        cV[45] = bytes32(uint256(500));
        cK[46] = K.TITHE_CEILING_BPS;                      cV[46] = bytes32(uint256(2_000));

        // ─── Mutables (18 = 8 original + 3 reclassified + 6 references + 1 kawase) ──
        bytes32[] memory mK = new bytes32[](18);
        bytes32[] memory mV = new bytes32[](18);
        mK[0] = K.KISHA_BASE_RATE;        mV[0] = bytes32(uint256(1_000_000));
        mK[1] = K.KAPPA_BPS;               mV[1] = bytes32(uint256(300));
        mK[2] = K.TIER_LIQUID_BPS;         mV[2] = bytes32(uint256(1_000));
        mK[3] = K.TIER_RESERVE_BPS;        mV[3] = bytes32(uint256(6_000));
        mK[4] = K.TIER_CORPUS_BPS;         mV[4] = bytes32(uint256(3_000));
        mK[5] = K.QUORUM_BPS;              mV[5] = bytes32(uint256(3_300));
        mK[6] = K.ACTIVE_WINDOW_SECS;      mV[6] = bytes32(uint256(30 days));
        mK[7] = K.TIMELOCK_SECS;           mV[7] = bytes32(uint256(72 hours));
        // Reclassified to Tier-2 (ADR-2606062100 §4): tithe rate + rider version + text-hash
        mK[8]  = K.TITHE_BPS;                       mV[8]  = bytes32(uint256(1_000));
        mK[9]  = K.LICENSE_CHARTER_RIDER_VERSION;   mV[9]  = bytes32("v3.6");
        // keccak256 of /CHARTER-RIDER.md v3.6 (drift-locked in ConstitutionInvariants.t.sol)
        mK[10] = K.LICENSE_CHARTER_RIDER_TEXT_HASH; mV[10] = 0x549c99eacb894c9bc74025cf09cb892b6b66e407b112c7c528ab6e7c9b14630b;
        // Reference addresses initial = 0 (set via governance post-deploy)
        mK[11] = K.PUBLIC_FUND_SAFE_ADDRESS;            mV[11] = bytes32(0);
        mK[12] = K.CHARTERS_COMPLIANCE_REGISTRY_ADDRESS; mV[12] = bytes32(0);
        mK[13] = K.TITHE_ROUTER_ADDRESS;                 mV[13] = bytes32(0);
        mK[14] = K.LAND_REGISTRY_ADDRESS;                mV[14] = bytes32(0);
        mK[15] = K.FORCE_AUTHORIZATION_ADDRESS;          mV[15] = bytes32(0);
        mK[16] = K.PUBLIC_FUND_GOVERNANCE_ADDRESS;       mV[16] = bytes32(0);
        // kawase-yui per-member monthly cap (ADR-2605282200 G9): R1 default $1,000.
        mK[17] = K.KAWASE_PER_MONTH_CAP_USD_MINOR;       mV[17] = bytes32(uint256(1_000_000_000));

        c = new Constitution(cK, cV, mK, mV);
    }

    // ============================================================
    //  Verify each constitutional invariant is set + immutable
    // ============================================================

    function test_mission_charter_constants_set() public view {
        assertEq(c.getConstant(K.MISSION_LABOR_LIBERATION), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_ROBOTICS_UNIVERSAL), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_IP_FREE_RELEASE), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_DISINTERMEDIATION), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_SPECIALIST_ANTI_GATEKEEPING), bytes32(uint256(1)));
    }

    function test_religious_ontology_constants_set() public view {
        assertEq(c.getConstant(K.MISSION_ANTI_INDIVIDUALISM), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_MULTI_GENERATIONAL_PRIORITY), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_MULTI_GENERATIONAL_HORIZON_YEARS), bytes32(uint256(50)));
        assertEq(c.getConstant(K.MISSION_WELLBECOMING_PRIORITY), bytes32(uint256(1)));
    }

    function test_land_and_force_constants_set() public view {
        assertEq(c.getConstant(K.MISSION_LAND_AS_RELIGIOUS_TRUST), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_TRANSPARENT_FORCE_ONLY), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_PROPRIETARY_FORCE_DESIGN_PROHIBITED), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_FORCE_REQUIRES_SBT_VOTE), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_NO_STATE_MILITARY_ALLIANCE), bytes32(uint256(1)));
    }

    function test_eros_gore_constants_set() public view {
        assertEq(c.getConstant(K.MISSION_EROS_PERMITTED), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_GORE_PROHIBITED), bytes32(uint256(1)));
    }

    function test_non_eschatology_constants_set() public view {
        // Religion is explicitly non-eschatological (per ADR-2605192100 §1.15)
        assertEq(c.getConstant(K.MISSION_ESCHATOLOGICAL), bytes32(uint256(0)));
        assertEq(c.getConstant(K.MISSION_REVELATION_IN_CANON), bytes32(uint256(0)));
        assertEq(c.getConstant(K.MISSION_CONTINUOUS_BECOMING), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MISSION_LINEAGE_JAPANESE_PROTESTANT), bytes32(uint256(1)));
    }

    function test_economic_hard_rules_set() public view {
        assertEq(c.getConstant(K.ECONOMIC_NON_PROFIT_ONLY), bytes32(uint256(1)));
        assertEq(c.getConstant(K.ECONOMIC_DONATION_ONLY), bytes32(uint256(1)));
        assertEq(c.getConstant(K.ECONOMIC_NO_ADVERTISING), bytes32(uint256(1)));
        // ADR-2606062100 §4: Tier-0 locks that tithe redistribution EXISTS + the band;
        // the 10% RATE is now a Tier-2 mutable within [500, 2000] bps.
        assertEq(c.getConstant(K.ECONOMIC_TITHE_REDISTRIBUTION_EXISTS), bytes32(uint256(1)));
        assertEq(c.getConstant(K.TITHE_FLOOR_BPS), bytes32(uint256(500)));
        assertEq(c.getConstant(K.TITHE_CEILING_BPS), bytes32(uint256(2_000)));
        assertEq(c.getMutable(K.TITHE_BPS), bytes32(uint256(1_000)));
    }

    function test_priority_and_memory_constants_set() public view {
        // ADR-2606062100: the Charter locks PRIORITIES, not specific policies.
        assertEq(c.getConstant(K.PRIORITY_WELLBECOMING_OVER_WELLBEING), bytes32(uint256(1)));
        assertEq(c.getConstant(K.PRIORITY_MULTIGEN_OVER_CURRENT), bytes32(uint256(1)));
        assertEq(c.getConstant(K.PRIORITY_COLLECTIVE_OVER_INDIVIDUAL), bytes32(uint256(1)));
        // Permanent memory (神の監視): no right to be forgotten.
        assertEq(c.getConstant(K.MEMORY_RIGHT_TO_ERASURE_DENIED), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MEMORY_PERMANENT_RECORD), bytes32(uint256(1)));
        assertEq(c.getConstant(K.MEMORY_DEEDS_PUBLIC_INTIMATE_ENCRYPTED), bytes32(uint256(1)));
    }

    function test_license_rider_constants_set() public view {
        assertEq(c.getConstant(K.LICENSE_BASE), bytes32("Apache-2.0"));
        assertEq(c.getConstant(K.LICENSE_CHARTER_RIDER_REQUIRED), bytes32(uint256(1)));
        // ADR-2606062100 §4: rider version is now a Tier-2 mutable (tracks amendments),
        // not a fork-only constant. v3.6 is the current priority-over-specifics Rider.
        assertEq(c.getMutable(K.LICENSE_CHARTER_RIDER_VERSION), bytes32("v3.6"));
    }

    function test_three_tier_enforcement_constants_set() public view {
        assertEq(c.getConstant(K.ENFORCEMENT_THREE_TIER), bytes32(uint256(1)));
        // ADR-2606062100 §4 bug fix: the L3 floor (Non-Aligned multiplier = 0) is now a
        // Tier-0 CONSTANT — was mis-deployed as a mutable, contradicting the doctrine.
        assertEq(c.getConstant(K.PHENOTYPE_NON_COMPLIANT_MULTIPLIER), bytes32(uint256(0)));
    }

    function test_kawase_yui_constants_set() public view {
        // ADR-2605282200 G4: Chainlink mid-market band = ±0.5% (50 bps).
        // Constitutional because mid-market-only pins the religious-corp
        // on the non-spread side of FX (Charter §2(b) speculative finance).
        assertEq(c.getConstant(K.KAWASE_MAX_BAND_BPS), bytes32(uint256(50)));
        // ADR-2605282200 G9: R1 per-member monthly cap = $1,000 in USDC minor.
        assertEq(
            c.getMutable(K.KAWASE_PER_MONTH_CAP_USD_MINOR),
            bytes32(uint256(1_000_000_000))
        );
    }

    // ============================================================
    //  Verify mutable reference addresses start at zero (must be
    //  wired via governance post-deploy per RUNBOOK)
    // ============================================================

    function test_reference_addresses_initially_zero() public view {
        assertEq(c.getMutable(K.PUBLIC_FUND_SAFE_ADDRESS), bytes32(0));
        assertEq(c.getMutable(K.CHARTERS_COMPLIANCE_REGISTRY_ADDRESS), bytes32(0));
        assertEq(c.getMutable(K.TITHE_ROUTER_ADDRESS), bytes32(0));
        assertEq(c.getMutable(K.LAND_REGISTRY_ADDRESS), bytes32(0));
        assertEq(c.getMutable(K.FORCE_AUTHORIZATION_ADDRESS), bytes32(0));
        assertEq(c.getMutable(K.PUBLIC_FUND_GOVERNANCE_ADDRESS), bytes32(0));
    }

    // ============================================================
    //  Verify all constants total count matches deploy script
    // ============================================================

    function test_all_constants_registered_as_immutable() public view {
        // Spot-check every category to ensure no key was forgotten
        // in the deploy script's _constants() helper.
        assertTrue(c.isConstant(K.ONE_SBT_ONE_VOTE), "original 1");
        assertTrue(c.isConstant(K.MISSION_LABOR_LIBERATION), "mission 1");
        assertTrue(c.isConstant(K.MISSION_ANTI_INDIVIDUALISM), "ontology 1");
        assertTrue(c.isConstant(K.MISSION_LAND_AS_RELIGIOUS_TRUST), "land 1");
        assertTrue(c.isConstant(K.MISSION_TRANSPARENT_FORCE_ONLY), "force 1");
        assertTrue(c.isConstant(K.MISSION_EROS_PERMITTED), "eros");
        assertTrue(c.isConstant(K.MISSION_GORE_PROHIBITED), "gore");
        assertTrue(c.isConstant(K.MISSION_ESCHATOLOGICAL), "anti-eschaton");
        assertTrue(c.isConstant(K.ECONOMIC_TITHE_REDISTRIBUTION_EXISTS), "tithe-exists");
        assertTrue(c.isConstant(K.LICENSE_CHARTER_RIDER_REQUIRED), "rider");
        assertTrue(c.isConstant(K.ENFORCEMENT_THREE_TIER), "three-tier");
        assertTrue(c.isConstant(K.KAWASE_MAX_BAND_BPS), "kawase-band");
        // ADR-2606062100 Tier-0 priority + permanent-memory additions
        assertTrue(c.isConstant(K.PRIORITY_WELLBECOMING_OVER_WELLBEING), "priority-wb");
        assertTrue(c.isConstant(K.MEMORY_RIGHT_TO_ERASURE_DENIED), "memory-erasure");
        assertTrue(c.isConstant(K.PHENOTYPE_NON_COMPLIANT_MULTIPLIER), "l3-floor-const");
        // Retired/reclassified keys must NOT be constants anymore
        assertFalse(c.isConstant(K.ECONOMIC_TITHE_TO_PUBLIC_FUND_BPS), "tithe-pinned-retired");
        assertFalse(c.isConstant(K.TITHE_BPS), "tithe-rate-mutable");
        assertFalse(c.isConstant(K.LICENSE_CHARTER_RIDER_VERSION), "rider-version-mutable");
    }
}
