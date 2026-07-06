// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v3.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {Constitution} from "../src/Constitution.sol";
import {ConstitutionKeys as K} from "../src/ConstitutionKeys.sol";
import {Deploy} from "../script/Deploy.s.sol";

/// @dev Exposes Deploy's internal genesis helpers so the invariant test exercises
///      the ACTUAL deploy script (not a hand-mirrored copy). Any drift in
///      Deploy._constants() / _mutables() is caught here.
contract DeployHarness is Deploy {
    function constantsPublic() public pure returns (bytes32[] memory, bytes32[] memory) {
        return _constants();
    }

    function mutablesPublic() public pure returns (bytes32[] memory, bytes32[] memory) {
        return _mutables();
    }
}

/**
 * @title ConstitutionInvariantsTest
 * @notice Structural invariants over the REAL deploy genesis (ADR-2606062100
 *         3-Tier model). Unlike ConstitutionReligiousCorpWaveTest (which
 *         hand-mirrors the arrays to verify values), this suite builds the
 *         Constitution directly from Deploy._constants()/_mutables() and asserts
 *         the constitutional invariants hold — so a future edit to the deploy
 *         script that violates the tier model fails CI.
 */
contract ConstitutionInvariantsTest is Test {
    DeployHarness internal h;
    Constitution internal c;

    bytes32[] internal cK;
    bytes32[] internal cV;
    bytes32[] internal mK;
    bytes32[] internal mV;

    function setUp() public {
        h = new DeployHarness();
        (cK, cV) = h.constantsPublic();
        (mK, mV) = h.mutablesPublic();
        c = new Constitution(cK, cV, mK, mV);
    }

    // ── Counts (lock the documented genesis size) ───────────────────────────

    function test_genesis_counts() public view {
        assertEq(cK.length, 47, "constant count");
        assertEq(cV.length, 47, "constant value count");
        assertEq(mK.length, 18, "mutable count");
        assertEq(mV.length, 18, "mutable value count");
    }

    // ── Constant / mutable sets are disjoint (Tier-0 vs Tier-2 separation) ──

    function test_constant_and_mutable_sets_are_disjoint() public view {
        for (uint256 i = 0; i < cK.length; ++i) {
            assertTrue(c.isConstant(cK[i]), "constant key not registered");
            for (uint256 j = 0; j < mK.length; ++j) {
                assertTrue(cK[i] != mK[j], "key in BOTH constant and mutable sets");
            }
        }
        // No mutable key is registered as a constant.
        for (uint256 j = 0; j < mK.length; ++j) {
            assertFalse(c.isConstant(mK[j]), "mutable key registered as constant");
        }
    }

    // ── No accidental duplicate keys within a set ───────────────────────────

    function test_no_duplicate_keys() public view {
        for (uint256 i = 0; i < cK.length; ++i) {
            for (uint256 j = i + 1; j < cK.length; ++j) {
                assertTrue(cK[i] != cK[j], "duplicate constant key");
            }
        }
        for (uint256 i = 0; i < mK.length; ++i) {
            for (uint256 j = i + 1; j < mK.length; ++j) {
                assertTrue(mK[i] != mK[j], "duplicate mutable key");
            }
        }
    }

    // ── Tithe: Tier-0 locks exists + band; Tier-2 holds the rate, in band ───

    function test_tithe_band_invariant() public view {
        assertEq(c.getConstant(K.ECONOMIC_TITHE_REDISTRIBUTION_EXISTS), bytes32(uint256(1)), "tithe must exist");
        uint256 floor_ = uint256(c.getConstant(K.TITHE_FLOOR_BPS));
        uint256 ceil_ = uint256(c.getConstant(K.TITHE_CEILING_BPS));
        uint256 rate = uint256(c.getMutable(K.TITHE_BPS));
        assertLt(floor_, ceil_, "tithe floor < ceiling");
        assertGe(rate, floor_, "tithe rate >= floor");
        assertLe(rate, ceil_, "tithe rate <= ceiling");
        // The retired pinned-10% constant must NOT be a constant anymore.
        assertFalse(c.isConstant(K.ECONOMIC_TITHE_TO_PUBLIC_FUND_BPS), "pinned tithe const retired");
        // The rate is a mutable, not a constant.
        assertFalse(c.isConstant(K.TITHE_BPS), "tithe rate must be mutable");
    }

    // ── κ and quorum mutables sit within their constant floor/ceiling ───────

    function test_kappa_and_quorum_within_bounds() public view {
        uint256 kappa = uint256(c.getMutable(K.KAPPA_BPS));
        assertGe(kappa, uint256(c.getConstant(K.KAPPA_FLOOR_BPS)), "kappa >= floor");
        assertLe(kappa, uint256(c.getConstant(K.KAPPA_CEILING_BPS)), "kappa <= ceiling");
        assertGe(uint256(c.getMutable(K.QUORUM_BPS)), uint256(c.getConstant(K.QUORUM_FLOOR_BPS)), "quorum >= floor");
    }

    // ── Asset-tier ratios sum to 100% ───────────────────────────────────────

    function test_tier_ratios_sum_to_10000() public view {
        uint256 sum = uint256(c.getMutable(K.TIER_LIQUID_BPS)) + uint256(c.getMutable(K.TIER_RESERVE_BPS))
            + uint256(c.getMutable(K.TIER_CORPUS_BPS));
        assertEq(sum, 10_000, "tier ratios must sum to 10000 bps");
    }

    // ── Bug-fix lock: the L3 enforcement floor is a Tier-0 CONSTANT == 0 ────

    function test_l3_enforcement_floor_is_constant_zero() public view {
        assertTrue(c.isConstant(K.PHENOTYPE_NON_COMPLIANT_MULTIPLIER), "L3 floor must be a CONSTANT (not mutable)");
        assertEq(c.getConstant(K.PHENOTYPE_NON_COMPLIANT_MULTIPLIER), bytes32(uint256(0)), "L3 floor == 0");
    }

    // ── Tier-0 priority + permanent-memory doctrine present and locked ─────

    function test_tier0_priority_and_memory_locked() public view {
        bytes32[7] memory tier0 = [
            K.PRIORITY_WELLBECOMING_OVER_WELLBEING,
            K.PRIORITY_MULTIGEN_OVER_CURRENT,
            K.PRIORITY_COLLECTIVE_OVER_INDIVIDUAL,
            K.MEMORY_RIGHT_TO_ERASURE_DENIED,
            K.MEMORY_PERMANENT_RECORD,
            K.MEMORY_DEEDS_PUBLIC_INTIMATE_ENCRYPTED,
            K.ECONOMIC_TITHE_REDISTRIBUTION_EXISTS
        ];
        for (uint256 i = 0; i < tier0.length; ++i) {
            assertTrue(c.isConstant(tier0[i]), "Tier-0 key must be a fork-only constant");
            assertEq(c.getConstant(tier0[i]), bytes32(uint256(1)), "Tier-0 priority bool == 1");
        }
    }

    // ── Rider: required is Tier-0; version + text-hash are Tier-2 ───────────

    function test_rider_required_constant_version_mutable() public view {
        assertEq(c.getConstant(K.LICENSE_CHARTER_RIDER_REQUIRED), bytes32(uint256(1)), "rider required");
        assertEq(c.getConstant(K.LICENSE_BASE), bytes32("Apache-2.0"), "license base Apache-2.0");
        assertFalse(c.isConstant(K.LICENSE_CHARTER_RIDER_VERSION), "rider version is mutable");
        assertFalse(c.isConstant(K.LICENSE_CHARTER_RIDER_TEXT_HASH), "rider text-hash is mutable");
        assertEq(c.getMutable(K.LICENSE_CHARTER_RIDER_VERSION), bytes32("v3.6"), "rider v3.6");
    }

    // ── Rider-integrity anchor: the on-chain text-hash == keccak256 of the
    //    actual /CHARTER-RIDER.md bytes (drift-lock; ADR-2606062100 §4). ─────

    function test_rider_text_hash_matches_file() public view {
        bytes32 stored = c.getMutable(K.LICENSE_CHARTER_RIDER_TEXT_HASH);
        assertTrue(stored != bytes32(0), "rider text-hash must be wired (not the 0 placeholder)");
        bytes32 actual = keccak256(bytes(vm.readFile("../../CHARTER-RIDER.md")));
        assertEq(stored, actual, "genesis rider_text_hash must equal keccak256 of /CHARTER-RIDER.md");
    }

    // ── Cross-artifact drift-lock: every priorityConformanceAttestation
    //    `servesPriority` enum value is a real Tier-0 constant key, and the enum
    //    covers EXACTLY the 7 Tier-0 priority/memory/tithe-exists keys. So the
    //    lexicon (JSON) and the genesis (Solidity) cannot drift apart. ──────────

    function test_lexicon_servesPriority_matches_tier0_constants() public view {
        string memory json = vm.readFile(
            "../../00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/priorityConformanceAttestation.json"
        );
        string[] memory enumVals = abi.decode(
            vm.parseJson(json, ".defs.main.record.properties.servesPriority.enum"),
            (string[])
        );

        // The enum must cover exactly the 7 Tier-0 priority/memory/tithe-exists keys.
        assertEq(enumVals.length, 7, "servesPriority enum must list all 7 Tier-0 priorities");

        // Forward: every enum value is a registered Tier-0 CONSTANT (not mutable).
        for (uint256 i = 0; i < enumVals.length; ++i) {
            bytes32 key = keccak256(bytes(enumVals[i]));
            assertTrue(c.isConstant(key), string.concat("enum value not a Tier-0 constant: ", enumVals[i]));
        }

        // Reverse: each of the 7 Tier-0 keys appears in the enum (no priority omitted).
        bytes32[7] memory tier0 = [
            K.PRIORITY_WELLBECOMING_OVER_WELLBEING,
            K.PRIORITY_MULTIGEN_OVER_CURRENT,
            K.PRIORITY_COLLECTIVE_OVER_INDIVIDUAL,
            K.MEMORY_RIGHT_TO_ERASURE_DENIED,
            K.MEMORY_PERMANENT_RECORD,
            K.MEMORY_DEEDS_PUBLIC_INTIMATE_ENCRYPTED,
            K.ECONOMIC_TITHE_REDISTRIBUTION_EXISTS
        ];
        for (uint256 t = 0; t < tier0.length; ++t) {
            bool found = false;
            for (uint256 i = 0; i < enumVals.length; ++i) {
                if (keccak256(bytes(enumVals[i])) == tier0[t]) {
                    found = true;
                    break;
                }
            }
            assertTrue(found, "a Tier-0 priority key is missing from the lexicon enum");
        }
    }
}
