// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {DisplacementDividend} from "../src/DisplacementDividend.sol";

/// @dev First test coverage for DisplacementDividend.sol (ADR-2606032130). Unlike its
///      sibling R0 scaffolds (PublicLandRegistry / LandClassRegistry / StewardTenureRegistry,
///      which are 100% inert reverts pre-activation), this contract already has LIVE
///      pure-view weight math (tenureWeightInputs / floorDecayPermille) meant to be
///      auditable on-chain against the Python reference allocator — that math, and the
///      cash≡0 structural tripwire (payoutToSubject), had no test coverage at all.
contract DisplacementDividendTest is Test {
    DisplacementDividend dividend;
    address constant CHARTERS = address(0xC4A47E7);

    function setUp() public {
        dividend = new DisplacementDividend(CHARTERS);
    }

    function test_constructor_storesChartersAndStartsInactive() public view {
        assertEq(dividend.charters(), CHARTERS);
        assertFalse(dividend.activated());
        assertEq(dividend.publicFundGovernance(), address(0));
    }

    // ── tenureWeightInputs: hazard bounds ───────────────────────────────────

    function test_tenureWeightInputs_revertsBelowHazardMin() public {
        vm.expectRevert(abi.encodeWithSelector(DisplacementDividend.InvalidHazard.selector, 999));
        dividend.tenureWeightInputs(12, 999);
    }

    function test_tenureWeightInputs_revertsAboveHazardMax() public {
        vm.expectRevert(abi.encodeWithSelector(DisplacementDividend.InvalidHazard.selector, 2001));
        dividend.tenureWeightInputs(12, 2001);
    }

    function test_tenureWeightInputs_acceptsBoundaryHazardValues() public view {
        (, uint16 hazardAtMin) = dividend.tenureWeightInputs(12, 1000);
        assertEq(hazardAtMin, 1000);
        (, uint16 hazardAtMax) = dividend.tenureWeightInputs(12, 2000);
        assertEq(hazardAtMax, 2000);
    }

    // ── tenureWeightInputs: tenure capping ──────────────────────────────────

    function test_tenureWeightInputs_passesThroughTenureUnderCap() public view {
        (uint64 cappedMonths,) = dividend.tenureWeightInputs(120, 1500); // 10 years
        assertEq(cappedMonths, 120);
    }

    function test_tenureWeightInputs_capsAtTenureCapMonths() public view {
        (uint64 cappedMonths,) = dividend.tenureWeightInputs(1000, 1500); // 83y3m, way over 40y cap
        assertEq(cappedMonths, dividend.TENURE_CAP_MONTHS());
        assertEq(cappedMonths, 600);
    }

    function test_tenureWeightInputs_exactlyAtCapIsUnchanged() public view {
        (uint64 cappedMonths,) = dividend.tenureWeightInputs(600, 1500);
        assertEq(cappedMonths, 600);
    }

    // ── floorDecayPermille ──────────────────────────────────────────────────

    function test_floorDecayPermille_fullAtZeroElapsed() public view {
        assertEq(dividend.floorDecayPermille(0), 1000);
    }

    function test_floorDecayPermille_linearMidHorizon() public view {
        // 30 of 60 months elapsed -> 1000 - 30/60*1000 = 500
        assertEq(dividend.floorDecayPermille(30), 500);
    }

    function test_floorDecayPermille_zeroAtHorizon() public view {
        assertEq(dividend.floorDecayPermille(60), 0);
    }

    function test_floorDecayPermille_zeroPastHorizon() public view {
        assertEq(dividend.floorDecayPermille(120), 0);
    }

    // ── cash≡0 structural tripwire ───────────────────────────────────────────

    function test_payoutToSubject_alwaysRevertsRegardlessOfInputs() public {
        vm.expectRevert(DisplacementDividend.CashIsNeverPaidToSubject.selector);
        dividend.payoutToSubject(1, 1_000_000);

        vm.expectRevert(DisplacementDividend.CashIsNeverPaidToSubject.selector);
        dividend.payoutToSubject(0, 0);

        vm.expectRevert(DisplacementDividend.CashIsNeverPaidToSubject.selector);
        dividend.payoutToSubject(type(uint256).max, type(uint256).max);
    }

    // ── R0 activation gate (lifecycle writes all revert pre-activation) ─────

    function test_registerSubject_revertsNotYetActivated() public {
        vm.expectRevert(DisplacementDividend.NotYetActivated.selector);
        dividend.registerSubject(1, bytes32("cohort"), address(0xACC7), 2611, 60, 1500, bytes32("evidence"));
    }

    function test_earmarkCohortPool_revertsNotYetActivated() public {
        bytes[] memory sigs = new bytes[](0);
        address[] memory signers = new address[](0);
        vm.expectRevert(DisplacementDividend.NotYetActivated.selector);
        dividend.earmarkCohortPool(bytes32("cohort"), 1_000_000, bytes32("policy"), sigs, signers);
    }

    function test_advanceCovenant_revertsNotYetActivated() public {
        vm.expectRevert(DisplacementDividend.NotYetActivated.selector);
        dividend.advanceCovenant(1, DisplacementDividend.Covenant.Vowed);
    }
}
